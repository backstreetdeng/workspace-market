# -*- coding: utf-8 -*-
"""Launcher in workspace-market root - adds self to path so package imports work."""
import sys
from pathlib import Path

ws_root = Path(__file__).resolve().parent
if str(ws_root) not in sys.path:
    sys.path.insert(0, str(ws_root))

import uvicorn
from fastapi_18003_adapter.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18003)
