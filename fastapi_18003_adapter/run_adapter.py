# -*- coding: utf-8 -*-
"""Launcher for fastapi_18003_adapter - avoids relative-import issues."""
import sys
from pathlib import Path

# Ensure workspace-market is in path
ws = Path(__file__).resolve().parent.parent
if str(ws) not in sys.path:
    sys.path.insert(0, str(ws))

import uvicorn
from fastapi_18003_adapter.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18003)
