# -*- coding: utf-8 -*-
"""OpenClaw Gateway client for the 18003 adapter."""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


OPENCLAW_GATEWAY_BASE_URL = os.environ.get("OPENCLAW_GATEWAY_BASE_URL", "http://127.0.0.1:18789").rstrip("/")
OPENCLAW_GATEWAY_TOKEN = os.environ.get(
    "OPENCLAW_GATEWAY_TOKEN",
    os.environ.get("OPENCLAW_TOKEN", "2ec777c61f588861712e0d7d9da2cf909fb2b4f45c954be9"),
)
MARKET_AGENT_ID = os.environ.get("MARKET_AGENT_ID", "market_strategy")
GATEWAY_TIMEOUT_SECONDS = float(os.environ.get("OPENCLAW_GATEWAY_TIMEOUT_SECONDS", "120"))


def openclaw_session_key(agent_id: str, session_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "_.:-" else "-" for ch in session_id).strip("-")
    return f"agent:{agent_id}:web:chat:{safe or int(time.time() * 1000)}"


def post_chat_completion(
    *,
    agent_id: str,
    session_id: str,
    message: str,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    if not OPENCLAW_GATEWAY_TOKEN:
        return {"ok": False, "error": "missing OPENCLAW_GATEWAY_TOKEN"}

    session_key = openclaw_session_key(agent_id, session_id)
    payload = {
        "model": f"openclaw/{agent_id}",
        "messages": [{"role": "user", "content": message}],
        "user": f"market-web:{session_id}",
        "stream": False,
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        f"{OPENCLAW_GATEWAY_BASE_URL}/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENCLAW_GATEWAY_TOKEN}",
            "Content-Type": "application/json",
            "x-openclaw-session-key": session_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout or GATEWAY_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {
            "ok": bool(text),
            "text": text,
            "agent_id": agent_id,
            "session_key": session_key,
            "raw": data,
        }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {
            "ok": False,
            "error": f"HTTP {exc.code}: {body or exc.reason}",
            "agent_id": agent_id,
            "session_key": session_key,
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, ValueError, KeyError) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "agent_id": agent_id,
            "session_key": session_key,
        }
