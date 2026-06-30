# -*- coding: utf-8 -*-
"""In-memory SSE session management for the 18003 adapter."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


SESSION_TTL_SECONDS = 60 * 60


@dataclass
class SessionState:
    session_id: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    status: str = "idle"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    final_sent: bool = False


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
        state.updated_at = time.time()
        return state

    async def push(self, session_id: str, event: str, data: Dict[str, Any]) -> None:
        state = await self.get_or_create(session_id)
        state.updated_at = time.time()
        if event in {"complete", "error"}:
            state.status = "done" if event == "complete" else "error"
            state.final_sent = True
        await state.queue.put({"event": event, "data": data})

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
                        "age_seconds": round(time.time() - state.created_at, 1),
                    }
                    for state in self._sessions.values()
                ],
            }


session_manager = SessionManager()
