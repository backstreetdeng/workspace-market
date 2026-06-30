# -*- coding: utf-8 -*-
"""Reliable callback client for web-visible OpenClaw Agent events.

Agents should use this helper instead of shell-specific curl commands. It sends
the canonical payload expected by fastapi_18003_adapter.main:/callback:

    {"session_id": "...", "event": {...}}
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


def post_callback(
    *,
    session_id: str,
    event: Dict[str, Any],
    callback_url: str = DEFAULT_CALLBACK_URL,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    if not session_id:
        raise ValueError("session_id is required")
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")

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


def _parse_json_object(raw: Optional[str], label: str) -> Dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def _build_event(args: argparse.Namespace) -> Dict[str, Any]:
    event = _parse_json_object(args.event_json, "--event-json")
    if args.event_type:
        event["event"] = args.event_type
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


def main(argv: Optional[list[str]] = None) -> int:
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
    args = parser.parse_args(argv)

    try:
        result = post_callback(
            session_id=args.session_id,
            event=_build_event(args),
            callback_url=args.callback_url,
            timeout=args.timeout,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
