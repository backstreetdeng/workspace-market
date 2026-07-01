# -*- coding: utf-8 -*-
"""FastAPI adapter that connects chat.html to OpenClaw Gateway sessions.

This adapter is intentionally thin:
- /chat accepts browser messages and sends them to the market_strategy Agent.
- /sse streams callback/progress events to the browser.
- /callback receives ReAct events from independent Agents.

It must not implement market-analysis orchestration in Python.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .gateway_client import MARKET_AGENT_ID, post_chat_completion
from .models import DEPRECATED_ANALYSIS_TYPES, CallbackPayload, ChatRequest
from .session_manager import session_manager



async def _db_snapshot() -> Dict[str, Any]:
    """Query the rag-engine database for document/chunk counts."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(
            host="192.168.3.146",
            port=5432,
            database="vectordb",
            user="vectordb",
            password="vectordb123",
            connect_timeout=3,
            cursor_factory=RealDictCursor,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM documents")
        documents = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM chunks")
        chunks = cur.fetchone()["cnt"]
        cur.close()
        conn.close()
        return {"connected": True, "documents": documents, "chunks": chunks}
    except Exception as exc:
        return {"connected": False, "error": str(exc), "documents": 0, "chunks": 0}


ADAPTER_BASE_URL = os.environ.get("MARKET_WEB_ADAPTER_BASE_URL", "http://127.0.0.1:18003").rstrip("/")
CALLBACK_HELPER_PATH = Path(__file__).with_name("callback_client.py")
HEARTBEAT_SECONDS = 15
TREE_EVENT_KINDS = {"task_progress", "substep_created", "substep_updated"}
TERMINAL_TIMEOUT_HINTS = ("timed out", "timeout", "operation was aborted", "aborted")
# B2 (2026-07-01 老大确认): chat_ingress.jsonl 落盘日志
# 位置: <workspace-market>/logs/chat_ingress.jsonl (绝对路径, 不依赖 cwd)
# 写入点: /chat 端点 (gate-in), 必落; 后续 agent_decision 由 callback 路径补齐
_CHAT_INGRESS_LOG = Path(__file__).resolve().parent.parent / "logs" / "chat_ingress.jsonl"
_CHAT_INGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)


def _log_chat_ingress(req: ChatRequest, *, agent_decision: str = "pending", deprecated: bool = False) -> None:
    """Append a JSONL line to logs/chat_ingress.jsonl.

    不靠 agent 自觉, adapter 强制落盘. 字段:
      ts (ISO8601) / session_id / question (前 200 字) / analysis_type / agent_decision / deprecated
    agent_decision 可取值:
      pending               - /chat 已接, 还未确认
      forwarded_to_orchestrator - 小市场已 sessions_send 给 strategy-orchestrator
      self_answered         - 小市场自答, 未走编排专家 (警告)
      skipped               - 其他
    """
    try:
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
            "session_id": req.session_id,
            "question": (req.question or "")[:200],
            "analysis_type": req.analysis_type or "auto",
            "agent_decision": agent_decision,
            "deprecated": deprecated,
        }
        with _CHAT_INGRESS_LOG.open("a", encoding="utf-8", newline="") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # 落盘失败不能影响 /chat 主流程
        print(f"[chat_ingress] log write failed: {exc}", flush=True)

app = FastAPI(title="Market WebChat OpenClaw Adapter", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _event_kind(event: Dict[str, Any]) -> str:
    explicit = str(event.get("event") or event.get("type") or "").strip().lower()
    if explicit in {"progress", "react", "complete", "error", *TREE_EVENT_KINDS}:
        return explicit
    phase = str(event.get("phase") or "").strip().lower()
    if phase == "complete" or "report" in event or "answer" in event:
        return "complete"
    if phase == "error" or event.get("error"):
        return "error"
    return "react"


def _is_gateway_watch_error(result: Dict[str, Any]) -> bool:
    error = str(result.get("error") or "").lower()
    return any(hint in error for hint in TERMINAL_TIMEOUT_HINTS)


def _payload_to_dict(payload: Any) -> Dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    if hasattr(payload, "dict"):
        return payload.dict()
    return dict(payload or {})


def _normalize_callback_event(payload: Any) -> tuple[str, Dict[str, Any]]:
    data = _payload_to_dict(payload)
    session_id = str(data.get("session_id") or "").strip()
    raw_event = data.get("event") or {}

    if isinstance(raw_event, str):
        event: Dict[str, Any] = {"phase": raw_event}
    elif isinstance(raw_event, dict):
        event = dict(raw_event)
    else:
        event = {"raw_event": raw_event}

    flat_event = {k: v for k, v in data.items() if k not in {"session_id", "event"}}
    event = {**flat_event, **event}
    event.setdefault("timestamp", time.time())
    return session_id, event


def _normalize_task_event(event: Dict[str, Any]) -> Dict[str, Any]:
    event = dict(event)
    status_aliases = {
        "doing": "running",
        "in_progress": "running",
        "success": "done",
        "finished": "done",
        "failed": "error",
    }
    status = str(event.get("status") or "").strip().lower()
    if status:
        event["status"] = status_aliases.get(status, status)

    if "node_id" not in event and event.get("id"):
        event["node_id"] = str(event["id"])
    if "summary" not in event and event.get("name"):
        event["summary"] = str(event["name"])
    if "display_name" not in event and event.get("summary"):
        event["display_name"] = str(event["summary"])

    kind = str(event.get("event") or event.get("type") or "").strip().lower()
    if kind == "substep_created":
        event["is_new_substep"] = True
    if kind in TREE_EVENT_KINDS and "node_id" not in event:
        agent = str(event.get("agent") or "agent").strip().lower().replace(" ", "_")
        phase = str(event.get("phase") or event.get("stage") or kind).strip().lower().replace(" ", "_")
        task_id = str(event.get("task_id") or "").strip().lower().replace(" ", "_")
        event["node_id"] = ":".join(part for part in [agent, phase, task_id] if part)
    return event


async def _complete_payload(req: ChatRequest, gateway_result: Dict[str, Any], started_at: float, session_id: str = "") -> Dict[str, Any]:
    # Try to extract confidence from various possible locations
    confidence = (
        gateway_result.get("confidence")
        or gateway_result.get("result", {}).get("confidence")
        or gateway_result.get("quality_check", {}).get("confidence")
        or 0
    )
    
    # Try to extract report from various possible locations (report-agent returns output_path, markdown, etc.)
    report = (
        gateway_result.get("report")
        or gateway_result.get("markdown")
        or gateway_result.get("output_path")
        or gateway_result.get("result", {}).get("markdown")
        or gateway_result.get("text")
        or ""
    )
    text = str(report)
    if _looks_like_metadata_only_report(text) and session_id:
        aggregated = await _aggregate_report_from_callbacks(session_id)
        if aggregated and len(aggregated) > len(text):
            text = aggregated
            report = aggregated
    return {
        "success": bool(gateway_result.get("ok")),
        "question": req.question,
        "analysis_type": req.analysis_type or "",
        "time_range": req.time_range or "",
        "confidence": confidence,
        "quality_passed": bool(gateway_result.get("ok")),
        "evidence_count": 0,
        "execution_time": round(time.time() - started_at, 2),
        "sources": [f"openclaw:{MARKET_AGENT_ID}"],
        "missing_or_uncertain": [] if gateway_result.get("ok") else [gateway_result.get("error") or "Gateway call failed"],
        "report": text,
        "answer": text,
        "raw": {
            "gateway": {k: v for k, v in gateway_result.items() if k != "raw"},
            "session_id": req.session_id,
        },
    }


def _looks_like_metadata_only_report(text: str) -> bool:
    """Heuristic: detect when the gateway reply text is metadata-only.

    The market_strategy agent sometimes replies with a short summary
    (e.g. `confidence=0.85, quality_passed=true`) instead of embedding the
    full Markdown report from strategy-orchestrator. When that happens,
    chat.html shows "\u672a\u8fd4\u56de\u62a5\u544a\u5185\u5bb9" because the report
    field is empty.

    A real Markdown report is usually hundreds of lines, contains headers,
    lists, and structured analysis. A metadata-only reply is short and
    lacks Markdown structure.
    """
    if not text:
        return True
    stripped = text.strip()
    if len(stripped) < 600:
        return True
    if stripped.startswith(chr(96)) and stripped.endswith(chr(96)) and len(stripped) < 1200:
        return True
    has_markdown_header = any(
        line.lstrip().startswith("#") for line in stripped.splitlines()[:40]
    )
    if not has_markdown_header:
        return True
    return False


async def _aggregate_report_from_callbacks(session_id: str, min_length: int = 200) -> str:
    """Scan session events for the longest report/answer/markdown field.

    This is a defensive fallback. The primary path is that the
    market_strategy agent embeds the full Markdown report in its gateway
    reply. If it does not, we still want chat.html to render the
    strategy-orchestrator's full report, which is normally delivered as a
    `phase=Complete` callback.
    """
    if not session_id:
        return ""
    try:
        history = await session_manager.history(session_id, after_seq=0)
    except Exception:
        return ""
    candidates = []
    seen = set()
    for item in history.get("events", []) or []:
        data = item.get("data") or {}
        for key in ("report", "answer", "markdown"):
            value = data.get(key)
            if not isinstance(value, str):
                continue
            value = value.strip()
            if len(value) < min_length:
                continue
            if value in seen:
                continue
            seen.add(value)
            candidates.append(value)
    if not candidates:
        return ""
    return max(candidates, key=len)


def build_market_agent_message(req: ChatRequest) -> str:
    callback_url = f"{ADAPTER_BASE_URL}/callback"
    callback_command = (
        f'python "{CALLBACK_HELPER_PATH}" '
        f'--callback-url "{callback_url}" '
        f'--session-id "{req.session_id}" '
        '--phase "Plan" --status "running" '
        '--agent "strategy-orchestrator" '
        '--summary "Planning task and selecting execution agents."'
    )
    payload = {
        "source": "chat.html",
        "session_id": req.session_id,
        "callback_url": callback_url,
        "callback_helper": {
            "path": str(CALLBACK_HELPER_PATH),
            "command_template": callback_command,
            "event_schema": {
                "event": "task_progress | substep_created | substep_updated | complete | error",
                "node_id": "stable unique node id for this step, reused when updating the same step",
                "parent_id": "optional parent node_id for tree nesting",
                "phase": "Plan | Dispatch | DataRunning | DataDone | AnalysisRunning | AnalysisDone | ReportRunning | QualityGate | Complete | Error",
                "status": "running | done | warning | error",
                "display_name": "short node label shown in the task tree",
                "summary": "short user-visible execution update",
                "agent": "agent currently doing the work",
                "task_id": "optional subtask identifier",
                "details": "optional JSON object with source/tool/gap counts",
            },
            "rule": "Use this Python helper for every callback. Do not use curl aliases or shell-specific HTTP snippets.",
        },
        "user_message": req.question,
        "analysis_type": req.analysis_type,
        "time_range": req.time_range,
        "max_cycles": req.max_cycles,
        "routing_contract": {
            "ordinary_chat": (
                "非市场分析问题 (闲聊 / 状态查询 / 文件说明) -> 在当前 market_strategy 会话直接答。"
            ),
            "complex_market_task": (
                "【必先 sessions_send, 禁止自答】 (2026-07-01 老大精细化纠错): "
                "当 analysis_type 命中以下任一市场战略枚举时, "
                "你 (market_strategy agent) 必须先用 sessions_send(agentId='strategy-orchestrator', ...) "
                "把任务包 (含 session_id / callback_url / require_callback=True / parent_id) 转发给编排专家, "
                "等待 phase=Plan 阶段事件回到 callback, 不要在没有 Plan 事件时声称'已分析完'。\n"
                "硬规则:\n"
                "  ① analysis_type 命中以下枚举 -> 必先转: business_analysis / opportunity_assessment / "
                "comprehensive_research / policy_impact / competitor_analysis / market_overview\n"
                "  ② analysis_type='auto' (chat.html 默认) -> 不要凭字段缺失就甩锅, "
                "先用 LLM 能力对 user_message 做语义判断, 若属于市场战略类 -> 转; 若属于闲聊类 -> 自答\n"
                "  ③ 字段缺失 / 字面不匹配 / 不确定时 -> LLM 语义判断优先, 不要'不确定就转'\n"
                "  ④ 触发转发的明确边界: 问题语义包含 '竞争格局 / 战略 / 政策 / 机会 / 综合研究 / 商业模式 / "
                "市场趋势 / 销量分析 / 品牌对比' 任一关键词 -> 转; 否则 -> 自答"
            ),
            "callback_requirement": (
                "The downstream strategy-orchestrator must emit each ReAct event with callback_helper. "
                "Do not use curl -X POST. PowerShell treats curl as Invoke-WebRequest and can break headers. "
                "For every delegated Agent, send a substep_created event when it starts, then substep_updated "
                "events as it runs, using stable node_id and parent_id so chat.html can render a nested task tree. "
                "The final callback should include phase='Complete' and report or answer. "
                "【必先 ping】market_strategy 在转交任务后, 必须先观察至少一个 phase=Plan 事件回到 callback, "
                "才能宣告任务已启动; 没有 Plan 事件 = 自答 (P0 违规)。"
            ),
            "fallback_visibility": (
                "【兜底可见性】如果 market_strategy 在 60s 内没有让 strategy-orchestrator 上报 phase=Plan, "
                "adapter 会自动向 SSE 推 'self_answered' warning 事件, 前端 chat.html 会显示 "
                "'小市场直接答了, 未走 strategy-orchestrator' 警告横幅。这是 P0 违规, "
                "小市场必须在收到 chat.html / 飞书任务后, 第一时间执行 sessions_send 转发, "
                "不要等 user 催、不要凭印象自答。"
            ),
        },
    }
    return (
        "You are receiving a web chat turn from chat.html through the OpenClaw Gateway.\n"
        "Follow the routing contract exactly. Do not let the FastAPI adapter perform orchestration.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


async def _run_gateway_turn(req: ChatRequest) -> None:
    started_at = time.time()
    await session_manager.push(
        req.session_id,
        "progress",
        {
            "event": "task_progress",
            "node_id": "gateway_send",
            "phase": "Gateway",
            "stage": "stage1",
            "status": "running",
            "agent": "fastapi_18003_adapter",
            "display_name": "Gateway relay",
            "summary": f"Sending turn to OpenClaw agent={MARKET_AGENT_ID}; session_id={req.session_id}",
        },
    )
    message = build_market_agent_message(req)
    result = await asyncio.to_thread(
        post_chat_completion,
        agent_id=MARKET_AGENT_ID,
        session_id=req.session_id,
        message=message,
    )
    if result.get("ok"):
        await session_manager.push(
            req.session_id,
            "complete",
            await _complete_payload(req, result, started_at, session_id=req.session_id),
        )
    elif _is_gateway_watch_error(result):
        await session_manager.push(
            req.session_id,
            "task_progress",
            {
                "event": "task_progress",
                "node_id": "gateway_watch",
                "parent_id": "gateway_send",
                "phase": "GatewayWatch",
                "stage": "gateway_watch",
                "status": "warning",
                "agent": "fastapi_18003_adapter",
                "display_name": "Gateway synchronous wait ended",
                "summary": (
                    "Gateway 同步等待已结束，后台智能体可能仍在运行；"
                    "页面继续监听 callback/SSE，不把这次等待结束判定为任务失败。"
                ),
                "details": {
                    "execution_time": round(time.time() - started_at, 2),
                    "raw_error": result.get("error") or "",
                },
            },
        )
    else:
        await session_manager.push(
            req.session_id,
            "error",
            {
                "success": False,
                "error": result.get("error") or "OpenClaw Gateway call failed",
                "execution_time": round(time.time() - started_at, 2),
                "raw": result,
            },
        )


# B4 兜底 (2026-07-01 老大授权): 启动后台 periodic safety check
_safety_task: Optional[asyncio.Task] = None


@app.on_event("startup")
async def _b4_safety_startup() -> None:
    global _safety_task
    _safety_task = asyncio.create_task(session_manager.periodic_safety_check())


@app.on_event("shutdown")
async def _b4_safety_shutdown() -> None:
    global _safety_task
    if _safety_task is not None and not _safety_task.done():
        _safety_task.cancel()


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "mode": "openclaw_gateway_event_adapter",
        "timestamp": time.time(),
        "sessions": await session_manager.snapshot(),
        "db": await _db_snapshot(),
    }


@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> Dict[str, Any]:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")
    # B2: 在 Pydantic 验证前拿 raw analysis_type, 用于 chat_ingress.jsonl 准确标 deprecated
    # (Pydantic validator 会把旧值改写为新值, 之后看 req.analysis_type 就丢了原始信息)
    raw_analysis_type = None
    try:
        raw_body = await request.json()
        raw_analysis_type = raw_body.get("analysis_type") if isinstance(raw_body, dict) else None
    except Exception:
        pass
    is_deprecated = raw_analysis_type in DEPRECATED_ANALYSIS_TYPES
    # B3 补充: 如果 raw 值是未知 (Pydantic 会 ValidationError -> 422), 这里提前转 400
    if (
        raw_analysis_type is not None
        and raw_analysis_type != ""
        and raw_analysis_type not in DEPRECATED_ANALYSIS_TYPES
        and raw_analysis_type not in {
            "auto",
            "business_analysis",
            "opportunity_assessment",
            "comprehensive_research",
            "policy_impact",
            "competitor_analysis",
            "market_overview",
        }
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "deprecated_analysis_type",
                "received": raw_analysis_type,
                "allowed": [
                    "auto",
                    "business_analysis",
                    "opportunity_assessment",
                    "comprehensive_research",
                    "policy_impact",
                    "competitor_analysis",
                    "market_overview",
                ],
                "hint": "前端 chat.html 需升级到最新版本 (分析类型下拉枚举已对齐 TOOLS.md)",
            },
        )
    # B3: Literal 收紧 analysis_type (2026-07-01 老大确认)
    # chat.html 历史客户端可能传旧枚举值 (competitor / market / comprehensive / 等), 此处:
    # - 若值是 None / "auto" / 已是新枚举 -> 接受
    # - 若值是旧枚举 -> 改写为新枚举 (过渡期兼容) + 在 chat_ingress.jsonl 标 deprecated=true
    # - 若值是完全未知 -> 返 400 + {"error": "deprecated_analysis_type", "hint": [...新枚举值]}
    # 注意: Pydantic Literal 在 Optional 模式下空字符串会触发 ValidationError, 这里需要 pre-validation
    if req.analysis_type is not None and req.analysis_type not in {
        "auto",
        "business_analysis",
        "opportunity_assessment",
        "comprehensive_research",
        "policy_impact",
        "competitor_analysis",
        "market_overview",
    }:
        if req.analysis_type == "":
            req.analysis_type = "auto"
        elif req.analysis_type in DEPRECATED_ANALYSIS_TYPES:
            req.analysis_type = DEPRECATED_ANALYSIS_TYPES[req.analysis_type]
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "deprecated_analysis_type",
                    "received": req.analysis_type,
                    "allowed": [
                        "auto",
                        "business_analysis",
                        "opportunity_assessment",
                        "comprehensive_research",
                        "policy_impact",
                        "competitor_analysis",
                        "market_overview",
                    ],
                    "hint": "前端 chat.html 需升级到最新版本 (分析类型下拉枚举已对齐 TOOLS.md)",
                },
            )
    await session_manager.mark_running(req.session_id)
    # B2: /chat 接到的每一题都落 JSONL (不靠 agent 自觉), agent_decision 初值 pending
    _log_chat_ingress(req, agent_decision="pending", deprecated=is_deprecated)
    await session_manager.push(
        req.session_id,
        "react",
        {
            "event": "task_progress",
            "node_id": "accept",
            "phase": "Accept",
            "stage": "stage0",
            "status": "done",
            "agent": "fastapi_18003_adapter",
            "display_name": "Request accepted",
            "summary": "Accepted browser message; adapter will relay to OpenClaw Gateway.",
        },
    )
    asyncio.create_task(_run_gateway_turn(req))
    return {"accepted": True, "session_id": req.session_id}


@app.get("/sse")
async def sse(session_id: str, after_seq: int = 0) -> StreamingResponse:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    await session_manager.get_or_create(session_id)

    async def stream() -> AsyncIterator[str]:
        last_sent_seq = after_seq
        if after_seq >= 0:
            history = await session_manager.history(session_id, after_seq=after_seq)
            for item in history["events"]:
                last_sent_seq = max(last_sent_seq, int(item["data"].get("seq") or 0))
                yield _sse(str(item["event"]), item["data"])
        while True:
            item = await session_manager.pop(session_id, timeout=HEARTBEAT_SECONDS)
            if item is None:
                yield _sse(
                    "progress",
                    {
                        "is_heartbeat": True,
                        "phase": "Heartbeat",
                        "stage": "heartbeat",
                        "status": "running",
                        "summary": "Waiting for OpenClaw Agent callback or final response.",
                    },
                )
                continue
            item_seq = int(item["data"].get("seq") or 0)
            if item_seq and item_seq <= last_sent_seq:
                continue
            last_sent_seq = max(last_sent_seq, item_seq)
            yield _sse(str(item["event"]), item["data"])
            if item["event"] in {"complete", "error"}:
                break

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.get("/events")
async def events(session_id: str, after_seq: int = 0) -> Dict[str, Any]:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return await session_manager.history(session_id, after_seq=after_seq)


@app.post("/callback")
async def callback(payload: CallbackPayload) -> Dict[str, Any]:
    session_id, event = _normalize_callback_event(payload)
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    event = _normalize_task_event(event)
    event_kind = _event_kind(event)
    if event_kind == "complete":
        event.setdefault("success", True)
        event.setdefault("quality_passed", True)
        event.setdefault("confidence", 0)
        if "report" not in event and "answer" in event:
            event["report"] = event["answer"]
    await session_manager.push(session_id, event_kind, event)
    return {"ok": True, "session_id": session_id, "event": event_kind}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_18003_adapter.main:app", host="127.0.0.1", port=18003, reload=False)
