# -*- coding: utf-8 -*-
"""Tests for the OpenClaw Gateway web chat adapter on port 18003."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi_18003_adapter.gateway_client import openclaw_session_key  # noqa: E402
from fastapi_18003_adapter.main import (  # noqa: E402
    _aggregate_report_from_callbacks,
    _complete_payload,
    _looks_like_metadata_only_report,
    build_market_agent_message,
    callback,
)
from fastapi_18003_adapter.models import CallbackPayload, ChatRequest  # noqa: E402
from fastapi_18003_adapter.session_manager import session_manager  # noqa: E402


class FastApi18003AdapterTest(unittest.IsolatedAsyncioTestCase):
    def test_market_agent_message_carries_callback_contract(self) -> None:
        message = build_market_agent_message(
            ChatRequest(
                question="分析零跑商业模式",
                analysis_type="business_analysis",
                time_range="最近6个月",
                session_id="web-test-1",
            )
        )

        self.assertIn('"source": "chat.html"', message)
        self.assertIn('"session_id": "web-test-1"', message)
        self.assertIn('"callback_url": "http://127.0.0.1:18003/callback"', message)
        self.assertIn('"callback_helper"', message)
        self.assertIn("callback_client.py", message)
        self.assertIn("Do not use curl", message)
        self.assertIn('"node_id"', message)
        self.assertIn('"parent_id"', message)
        self.assertIn("substep_created", message)
        self.assertIn("sessions_send", message)
        self.assertIn("strategy-orchestrator", message)

    def test_openclaw_session_key_is_stable(self) -> None:
        self.assertEqual(
            openclaw_session_key("market_strategy", "web session 1"),
            "agent:market_strategy:web:chat:web-session-1",
        )

    async def test_callback_pushes_complete_event_with_defaults(self) -> None:
        session_id = "unit-callback-complete"
        await session_manager.get_or_create(session_id)

        result = await callback(
            CallbackPayload(
                session_id=session_id,
                event={"phase": "Complete", "answer": "最终报告"},
            )
        )
        item = await session_manager.pop(session_id, timeout=0.1)

        self.assertEqual(result["ok"], True)
        self.assertEqual(item["event"], "complete")
        self.assertEqual(item["data"]["success"], True)
        self.assertEqual(item["data"]["quality_passed"], True)
        self.assertEqual(item["data"]["report"], "最终报告")

    async def test_callback_accepts_flat_legacy_event_shape(self) -> None:
        session_id = "unit-callback-flat"
        await session_manager.get_or_create(session_id)

        result = await callback(
            CallbackPayload(
                session_id=session_id,
                event="Plan",
                summary="Planning started",
                status="running",
            )
        )
        item = await session_manager.pop(session_id, timeout=0.1)

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["event"], "react")
        self.assertEqual(item["event"], "react")
        self.assertEqual(item["data"]["phase"], "Plan")
        self.assertEqual(item["data"]["summary"], "Planning started")

    async def test_callback_accepts_tree_substep_event(self) -> None:
        session_id = "unit-callback-tree"
        await session_manager.mark_running(session_id)

        result = await callback(
            CallbackPayload(
                session_id=session_id,
                event={
                    "event": "substep_created",
                    "id": "sql_001",
                    "parent_id": "data_001",
                    "name": "Connecting PostgreSQL sales database",
                    "status": "doing",
                    "agent": "data-agent",
                },
            )
        )
        item = await session_manager.pop(session_id, timeout=0.1)
        history = await session_manager.history(session_id)

        self.assertEqual(result["event"], "substep_created")
        self.assertEqual(item["event"], "substep_created")
        self.assertEqual(item["data"]["node_id"], "sql_001")
        self.assertEqual(item["data"]["parent_id"], "data_001")
        self.assertEqual(item["data"]["summary"], "Connecting PostgreSQL sales database")
        self.assertEqual(item["data"]["status"], "running")
        self.assertEqual(item["data"]["seq"], 1)
        self.assertEqual(history["last_seq"], 1)
        self.assertEqual(history["events"][0]["data"]["node_id"], "sql_001")

    async def test_session_history_can_replay_after_seq(self) -> None:
        session_id = "unit-session-history"
        await session_manager.mark_running(session_id)
        await session_manager.push(session_id, "task_progress", {"node_id": "a", "phase": "Plan"})
        await session_manager.push(session_id, "task_progress", {"node_id": "b", "phase": "Data"})

        history = await session_manager.history(session_id, after_seq=1)

        self.assertEqual(history["last_seq"], 2)
        self.assertEqual(len(history["events"]), 1)
        self.assertEqual(history["events"][0]["data"]["node_id"], "b")



class CompletePayloadReportAggregationTest(unittest.IsolatedAsyncioTestCase):
    """P0 regression: chat.html must always render a usable report."""

    async def test_metadata_only_gateway_text_triggers_callback_aggregation(self) -> None:
        session_id = "unit-complete-meta-aggregation"
        await session_manager.mark_running(session_id)

        full_report = (
            "# 比亚迪 Q1 市场策略分析\n\n"
            "## 市场现状\n- 销量：12.3 万辆\n- 份额：13.5%\n\n"
            "## 竞品分析\n- 特斯拉 Model Y\n- 小米 SU7\n\n"
            "## 战略建议\n1. 强化 15-20 万价格带\n2. 加快智驾平权\n"
        ) * 4  # ensure long enough to bypass metadata heuristic

        await session_manager.push(
            session_id,
            "react",
            {"phase": "Complete", "status": "done", "report": full_report, "answer": full_report},
        )

        req = ChatRequest(
            question="分析比亚迪 Q1 策略",
            analysis_type="business_analysis",
            time_range="最近3个月",
            session_id=session_id,
        )
        gateway_result = {
            "ok": True,
            "text": "已完成。confidence=0.85, quality_passed=true, cycles=2",
        }

        payload = await _complete_payload(req, gateway_result, started_at=time.time(), session_id=session_id)

        self.assertGreaterEqual(len(payload["report"]), 400)
        self.assertIn("比亚迪", payload["report"])
        self.assertIn("市场现状", payload["report"])
        self.assertTrue(payload["report"].rstrip().startswith("# 比亚迪"))
        self.assertGreaterEqual(len(payload["report"]), len(full_report) - 1)
        self.assertIn("## 市场现状", payload["report"])

    async def test_full_report_in_gateway_text_skips_aggregation(self) -> None:
        session_id = "unit-complete-skip-aggregation"
        await session_manager.mark_running(session_id)

        full_report = (
            "# 标题\n\n## 子节\n"
            + ("这是一段正式的 Markdown 正文，" * 80)
        )

        await session_manager.push(
            session_id,
            "react",
            {"phase": "Complete", "status": "done", "report": "# OLDER REPORT\nOLDER"},
        )

        req = ChatRequest(
            question="问题",
            analysis_type="business_analysis",
            time_range="最近3个月",
            session_id=session_id,
        )
        gateway_result = {"ok": True, "text": full_report}

        payload = await _complete_payload(req, gateway_result, started_at=time.time(), session_id=session_id)

        self.assertEqual(payload["report"], full_report)
        self.assertIn("正式", payload["report"])

    async def test_no_session_id_keeps_gateway_text(self) -> None:
        req = ChatRequest(
            question="问题",
            analysis_type="business_analysis",
            time_range="最近3个月",
            session_id="orphan",
        )
        gateway_result = {"ok": True, "text": "short"}

        payload = await _complete_payload(req, gateway_result, started_at=time.time(), session_id="")

        self.assertEqual(payload["report"], "short")
        self.assertEqual(payload["answer"], "short")


class MetadataHeuristicTest(unittest.TestCase):
    """Unit tests for _looks_like_metadata_only_report."""

    def test_empty_string_is_metadata(self) -> None:
        self.assertTrue(_looks_like_metadata_only_report(""))

    def test_short_text_is_metadata(self) -> None:
        self.assertTrue(_looks_like_metadata_only_report("已完成，confidence=0.85"))

    def test_short_quoted_text_is_metadata(self) -> None:
        self.assertTrue(_looks_like_metadata_only_report("`confidence=0.85`"))

    def test_long_text_without_headers_is_metadata(self) -> None:
        plain = "这是一段没有 Markdown 标题的纯文本。" * 30
        self.assertTrue(_looks_like_metadata_only_report(plain))

    def test_full_markdown_report_is_not_metadata(self) -> None:
        report = (
            "# 报告标题\n\n"
            + ("## 子节\n正文内容 " * 80)
        )
        self.assertFalse(_looks_like_metadata_only_report(report))


if __name__ == "__main__":
    unittest.main()
