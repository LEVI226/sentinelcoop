"""Launcher CIF Guard — résout le problème d'event loop psycopg/Windows.

Utilisation :
    python run.py
    python run.py --port 8001
    python run.py --https          # HTTPS:8443 avec certs/cifguard.crt/.key
    python run.py --https --port 9443
"""
from __future__ import annotations

import asyncio
import selectors
import sys
from pathlib import Path

# Fix psycopg async + Windows : forcer SelectorEventLoop AVANT tout import asyncio app
if sys.platform == "win32":
    _policy = type("_P", (asyncio.DefaultEventLoopPolicy,), {
        "new_event_loop": lambda self: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    })
    asyncio.set_event_loop_policy(_policy())  # type: ignore[misc]

import uvicorn  # noqa: E402

from app.main import app  # noqa: E402  — app.main already calls ensure_selector_loop

port = 8000
if "--port" in sys.argv:
    idx = sys.argv.index("--port")
    if idx + 1 < len(sys.argv):
        port = int(sys.argv[idx + 1])

reload = "--reload" in sys.argv
use_https = "--https" in sys.argv

if use_https and "--port" not in sys.argv:
    port = 8443

_base = Path(__file__).resolve().parent / "certs"
ssl = None
if use_https:
    ssl = {
        "ssl_certfile": str(_base / "cifguard.crt"),
        "ssl_keyfile": str(_base / "cifguard.key"),
    }

uvicorn.run(app, host="127.0.0.1", port=port, reload=reload, **ssl if ssl else {})