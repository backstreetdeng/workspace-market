# -*- coding: utf-8 -*-
"""Callback client for strategy-orchestrator to push ReAct events to 18003 adapter.

Usage:
    python callback_client.py <session_id> <event_json>

Example:
    python callback_client.py "chat_123" "{\"phase\":\"Plan\",\"status\":\"done\",\"summary\":\"...\"}"

This replaces raw PowerShell JSON POSTs which fail due to $ variable expansion.
"""

import json
import sys
import urllib.error
import urllib.request


def post_callback(session_id: str, event: dict) -> dict:
    url = "http://127.0.0.1:18003/callback"
    payload = {"session_id": session_id, "event": event}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"ok": True, "status": resp.status, "body": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"ok": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "Usage: python callback_client.py <session_id> <event_json>"}))
        sys.exit(1)
    session_id = sys.argv[1]
    try:
        event = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)
    result = post_callback(session_id, event)
    print(json.dumps(result, ensure_ascii=False))
