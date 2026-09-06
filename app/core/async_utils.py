"""Configuration de la boucle d'événements compatible psycopg sur Windows.

Sur Windows, l'event loop par défaut (ProactorEventLoop) n'est pas compatible
avec psycopg en mode async. On force SelectorEventLoop (AsyncIO + selectors).
"""
from __future__ import annotations

import asyncio
import selectors
import sys


def ensure_selector_loop():
    """Configure la politique d'event loop pour utiliser SelectorEventLoop sur Windows."""
    if sys.platform == "win32":
        class SelectorPolicy(asyncio.DefaultEventLoopPolicy):
            def new_event_loop(self):
                return asyncio.SelectorEventLoop(selectors.SelectSelector())

        asyncio.set_event_loop_policy(SelectorPolicy())


def run_async(coro) -> None:
    """Exécute une coroutine dans un event loop compatible psycopg."""
    ensure_selector_loop()
    asyncio.run(coro)