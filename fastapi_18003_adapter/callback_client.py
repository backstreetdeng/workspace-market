# -*- coding: utf-8 -*-
"""Reliable callback client for web-visible OpenClaw Agent events.

Agents should use this helper instead of shell-specific curl commands. It sends
the canonical payload expected by fastapi_18003_adapter.main:/callback:

    {"session_id": "...", "event": {...}}

A3 修复（2026-07-01 老大 P0 拍板）：
  1. post_callback 重试 3 次（指数退避 1s / 2s / 4s）
  2. 检查 18003 返回值 ok=true，否则视失败并重试
  3. 全部失败抛 CallbackDeliveryError，不静默吞掉
  4. main() 新增 --max-retries / --backoff-base 参数

行为变化（向后兼容）：
  - 默认 max_retries=3（之前是 1 次）
  - 默认 backoff_base=1.0（1s / 2s / 4s）
  - 想用旧行为可显式传 max_retries=1

2026-07-01 之前的 elif 修复保留：
  - --phase 非空且 --event-type 未指定时，默认 event="task_progress"
  - 避免 main.py _event_kind 识别不出事件类型、默认归类为 "react"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


DEFAULT_CALLBACK_URL = os.environ.get(
    "MARKET_WEB_CALLBACK_URL",
    "http://127.0.0.1:18003/callback",
)


class CallbackDeliveryError(RuntimeError):
    """callback 投递失败（重试 max_retries 次后仍失败）。

    可能成因：
      - 18003 不可达（DNS / 连接拒绝 / 超时）
      - 持续返回 5xx
      - 持续返回 {"ok": false, ...}
    """


def _attempt_callback(
    *,
    session_id: str,
    event: Dict[str, Any],
    callback_url: str,
    timeout: float,
) -> Dict[str, Any]:
    """单次 HTTP POST 尝试。返回 18003 的响应 dict。

    Raises:
        urllib.error.HTTPError: 4xx / 5xx
        urllib.error.URLError: 网络层错误
        TimeoutError: 超时
        json.JSONDecodeError: 响应不是合法 JSON
    """
    event.setdefault("timestamp", time.time())
    payload = {"session_id": session_id, "event": event}
    request = urllib.request.Request(
        callback_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {"ok": True}


def post_callback(
    *,
    session_id: str,
    event: Dict[str, Any],
    callback_url: str = DEFAULT_CALLBACK_URL,
    timeout: float = 10.0,
    max_retries: int = 3,
    backoff_base: float = 1.0,
) -> Dict[str, Any]:
    """POST callback to 18003 /callback with retry + ok check.

    Args:
        session_id: 会话 ID（18003 用来路由到正确的 chat.html SSE 连接）
        event: 事件 dict
        callback_url: 18003 /callback 端点
        timeout: 单次请求超时（秒）
        max_retries: 最大尝试次数（含首次）。默认 3 → 失败重试 2 次
        backoff_base: 退避基数（秒）。第 N 次失败后等待 backoff_base * 2^(N-1)。
                      默认 1.0 → 退避 1s / 2s / 4s / 8s ...

    Returns:
        18003 的响应 dict（通常含 ok: true）

    Raises:
        ValueError: 参数错误（session_id 空）
        TypeError: event 不是 dict
        CallbackDeliveryError: 重试 max_retries 次后仍失败
    """
    if not session_id:
        raise ValueError("session_id is required")
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = _attempt_callback(
                session_id=session_id,
                event=event,
                callback_url=callback_url,
                timeout=timeout,
            )
            # 检查 ok 字段：dict 且 ok != True 视为失败
            if isinstance(resp, dict) and resp.get("ok") is not True:
                last_error = CallbackDeliveryError(
                    f"18003 returned ok!=true on attempt {attempt}/{max_retries}: {resp}"
                )
            else:
                # 成功
                if attempt > 1:
                    print(
                        f"[retry-success] callback ok=true on attempt {attempt}/{max_retries}",
                        file=sys.stderr,
                    )
                return resp
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc

        # 不是最后一次则退避
        if attempt < max_retries:
            backoff = backoff_base * (2 ** (attempt - 1))
            print(
                f"[retry] attempt {attempt}/{max_retries} failed ({type(last_error).__name__}: {last_error}); "
                f"sleeping {backoff:.1f}s before retry",
                file=sys.stderr,
            )
            time.sleep(backoff)

    # 所有重试都失败
    raise CallbackDeliveryError(
        f"callback delivery failed after {max_retries} attempts to {callback_url}: {last_error}"
    ) from last_error


def _parse_json_object(raw, label):
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def _build_event(args):
    event = _parse_json_object(args.event_json, "--event-json")
    if args.event_type:
        event["event"] = args.event_type
    # A3 修复 (2026-07-01 老大发现): 编排专家 callback 默认只传 --phase, 不传 --event-type
    # 导致 main.py _event_kind 识别不出事件类型, 默认归类为"react"
    # 此处: 如果 --phase 非空且 event_type 未指定，默认 event="task_progress"
    elif args.phase and "event" not in event:
        event["event"] = "task_progress"
    if args.node_id:
        event["node_id"] = args.node_id
    if args.parent_id:
        event["parent_id"] = args.parent_id
    if args.display_name:
        event["display_name"] = args.display_name
    if args.phase:
        event["phase"] = args.phase
    if args.stage:
        event["stage"] = args.stage
    if args.status:
        event["status"] = args.status
    if args.summary:
        event["summary"] = args.summary
    if args.agent:
        event["agent"] = args.agent
    if args.task_id:
        event["task_id"] = args.task_id

    details = _parse_json_object(args.details_json, "--details-json")
    if details:
        event["details"] = details

    if not event:
        raise ValueError("provide at least --phase, --summary, or --event-json")
    return event


def main(argv=None):
    parser = argparse.ArgumentParser(description="POST a market web callback event.")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--callback-url", default=DEFAULT_CALLBACK_URL)
    parser.add_argument("--phase")
    parser.add_argument("--stage")
    parser.add_argument("--status", default="running")
    parser.add_argument("--event-type", choices=["task_progress", "substep_created", "substep_updated", "complete", "error"])
    parser.add_argument("--node-id")
    parser.add_argument("--parent-id")
    parser.add_argument("--display-name")
    parser.add_argument("--summary")
    parser.add_argument("--agent")
    parser.add_argument("--task-id")
    parser.add_argument("--event-json", help="JSON object merged into event")
    parser.add_argument("--details-json", help="JSON object stored under event.details")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-retries", type=int, default=3, help="max attempts incl. first (default 3)")
    parser.add_argument("--backoff-base", type=float, default=1.0, help="backoff base seconds (default 1.0 -> 1s/2s/4s)")
    args = parser.parse_args(argv)

    try:
        result = post_callback(
            session_id=args.session_id,
            event=_build_event(args),
            callback_url=args.callback_url,
            timeout=args.timeout,
            max_retries=args.max_retries,
            backoff_base=args.backoff_base,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, urllib.error.URLError) as exc:
        # OSError 包含 TimeoutError / ConnectionRefusedError 等
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except CallbackDeliveryError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "attempts": args.max_retries}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
