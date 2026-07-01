# -*- coding: utf-8 -*-
"""In-memory SSE session management for the 18003 adapter."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


SESSION_TTL_SECONDS = 60 * 60

# B4 兜底 (2026-07-01 老大授权): 编排专家 60s 内必须推 phase=Plan callback, 否则推 self_answered warning
ORCHESTRATOR_PING_TIMEOUT = 60.0
PERIODIC_SAFETY_CHECK_INTERVAL = 15.0


@dataclass
class SessionState:
    session_id: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    status: str = "idle"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    final_sent: bool = False
    seq: int = 0
    events: list[Dict[str, Any]] = field(default_factory=list)
    task_nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_event: Optional[Dict[str, Any]] = None
    # B4 兜底 (2026-07-01 老大授权): 记录 phase=Plan 首次到达时间 + enforce_task 句柄
    first_plan_at: Optional[float] = None
    last_warning_at: Optional[float] = None
    enforce_task: Optional[asyncio.Task] = None


class SessionManager:
    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: str) -> SessionState:
        await self.cleanup()
        async with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                state = SessionState(session_id=session_id)
                self._sessions[session_id] = state
            state.updated_at = time.time()
            return state

    async def mark_running(self, session_id: str) -> SessionState:
        state = await self.get_or_create(session_id)
        state.status = "running"
        state.final_sent = False
        state.seq = 0
        state.events.clear()
        state.task_nodes.clear()
        state.last_event = None
        # B4 兜底: 重置 plan 状态 + 取消旧的 enforce_task + 启动新的 60s 倒计时
        state.first_plan_at = None
        state.last_warning_at = None
        if state.enforce_task is not None and not state.enforce_task.done():
            state.enforce_task.cancel()
        state.enforce_task = asyncio.create_task(
            self._enforce_orchestrator_ping(session_id, ORCHESTRATOR_PING_TIMEOUT)
        )
        while not state.queue.empty():
            try:
                state.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        state.updated_at = time.time()
        return state

    async def _enforce_orchestrator_ping(
        self, session_id: str, timeout: float = ORCHESTRATOR_PING_TIMEOUT
    ) -> None:
        """B4 兜底: 60s 内未收到编排专家 phase=Plan callback, 推 self_answered warning
        编排专家发送 phase=Plan 时会在 push() 内自动 cancel 本 task
        """
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return
        state = self._sessions.get(session_id)
        if state is None:
            return  # session 已清理
        if state.first_plan_at is not None:
            return  # 编排专家已响应, 无需 warning
        if state.status not in {"idle", "running"}:
            return  # session 已终态
        # 推 self_answered warning
        await self.push(
            session_id,
            "task_progress",
            {
                "phase": "GatewayWatch",
                "stage": "self_answered_warning",
                "status": "warning",
                "agent": "fastapi_18003_adapter",
                "summary": (
                    f"{int(timeout)}s 内未收到编排专家 phase=Plan callback。"
                    f"可能编排专家 main session 失败 / callback 链路异常 / 编排专家侧未修复。"
                    f"B4 兜底逻辑自动触发，请人工排查编排专家 session 状态。"
                ),
            },
        )
        state.last_warning_at = time.time()

    async def periodic_safety_check(self) -> None:
        """B4 兜底: 后台周期检查所有 running session, 60s 无 Plan 强制 warning
        防止 mark_running 漏启动 / session 被 cleanup 后重启 等边界情况
        在 main.py startup 启动本方法, shutdown 时 cancel
        """
        try:
            while True:
                await asyncio.sleep(PERIODIC_SAFETY_CHECK_INTERVAL)
                await self._safety_check_once()
        except asyncio.CancelledError:
            return

    async def _safety_check_once(self) -> None:
        now = time.time()
        async with self._lock:
            sessions_snapshot = list(self._sessions.values())
        for state in sessions_snapshot:
            if state.status != "running":
                continue
            if state.first_plan_at is not None:
                continue
            if state.final_sent:
                continue
            age = now - state.updated_at
            # 60s 无 Plan + 上次 warning 在 60s 之前 (避免重复刷屏)
            if age >= ORCHESTRATOR_PING_TIMEOUT and (
                state.last_warning_at is None
                or now - state.last_warning_at >= ORCHESTRATOR_PING_TIMEOUT
            ):
                await self.push(
                    state.session_id,
                    "task_progress",
                    {
                        "phase": "GatewayWatch",
                        "stage": "self_answered_warning",
                        "status": "warning",
                        "agent": "fastapi_18003_adapter",
                        "summary": (
                            f"safety check: {int(age)}s 内未收到 phase=Plan (兜底自动触发)"
                        ),
                    },
                )
                state.last_warning_at = now

    async def push(self, session_id: str, event: str, data: Dict[str, Any]) -> None:
        state = await self.get_or_create(session_id)
        state.updated_at = time.time()
        payload = dict(data or {})
        state.seq += 1
        payload.setdefault("seq", state.seq)
        payload.setdefault("timestamp", time.time())
        # B4 兜底: 收到 phase=Plan callback 时记录首次到达时间 + cancel enforce_task
        phase = str(payload.get("phase") or "").strip()
        if phase == "Plan" and state.first_plan_at is None:
            state.first_plan_at = time.time()
            if state.enforce_task is not None and not state.enforce_task.done():
                state.enforce_task.cancel()
                state.enforce_task = None
        if event in {"complete", "error"}:
            state.status = "done" if event == "complete" else "error"
            state.final_sent = True
            # 终态时清理 enforce_task (避免悬挂)
            if state.enforce_task is not None and not state.enforce_task.done():
                state.enforce_task.cancel()
                state.enforce_task = None
        elif payload.get("status") == "warning":
            state.status = "warning"
        else:
            state.status = "running"

        item = {"event": event, "data": payload}
        state.events.append(item)
        if len(state.events) > 500:
            state.events = state.events[-500:]

        node_id = str(payload.get("node_id") or payload.get("id") or "").strip()
        if node_id:
            current = state.task_nodes.get(node_id, {})
            state.task_nodes[node_id] = {**current, **payload, "event": event}
        state.last_event = item
        await state.queue.put(item)

    async def history(self, session_id: str, after_seq: int = 0) -> Dict[str, Any]:
        state = await self.get_or_create(session_id)
        async with self._lock:
            events = [
                {"event": item["event"], "data": dict(item["data"])}
                for item in state.events
                if int(item["data"].get("seq") or 0) > after_seq
            ]
            return {
                "session_id": state.session_id,
                "status": state.status,
                "final_sent": state.final_sent,
                "last_seq": state.seq,
                "events": events,
                "task_nodes": dict(state.task_nodes),
                "last_event": state.last_event,
            }

    async def pop(self, session_id: str, timeout: float) -> Optional[Dict[str, Any]]:
        state = await self.get_or_create(session_id)
        try:
            return await asyncio.wait_for(state.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def cleanup(self) -> None:
        now = time.time()
        async with self._lock:
            expired = [
                key
                for key, state in self._sessions.items()
                if now - state.updated_at > self.ttl_seconds
            ]
            for key in expired:
                state = self._sessions.get(key)
                if state is not None and state.enforce_task is not None and not state.enforce_task.done():
                    state.enforce_task.cancel()
                self._sessions.pop(key, None)

    async def snapshot(self) -> Dict[str, Any]:
        await self.cleanup()
        async with self._lock:
            return {
                "count": len(self._sessions),
                "sessions": [
                    {
                        "session_id": state.session_id,
                        "status": state.status,
                        "final_sent": state.final_sent,
                        "last_seq": state.seq,
                        "event_count": len(state.events),
                        "last_event": state.last_event,
                        "first_plan_at": state.first_plan_at,
                        "last_warning_at": state.last_warning_at,
                        "age_seconds": round(time.time() - state.created_at, 1),
                    }
                    for state in self._sessions.values()
                ],
            }


session_manager = SessionManager()
