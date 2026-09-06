"""Point d'entrée CIF Guard API (FastAPI).

Lancement (Windows) :
    python -m uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.async_utils import ensure_selector_loop
from app.core.errors import register_exception_handlers, request_id_middleware
from app.database import get_db
from app.api.v1 import (  # noqa: F401
    accounts, alerts, audit, auth, cases, customers, dashboard, declarations,
    misc, network, org, postes, rules, screening, transactions, users,
)
from app.services.audit_service import purge_obsolete_audit_logs

# Windows : psycopg (asyncpg protocol layer) exige un SelectorEventLoop.
ensure_selector_loop()

app = FastAPI(
    title="CIF Guard — API de conformité LBC/FT/FP",
    version="0.1.0",
    description=(
        "Backend de filtrage et supervision de conformité pour le réseau de "
        "coopératives financières : screening listes de sanctions, surveillance "
        "des opérations, KYC, gestion des alertes et des dossiers, déclarations "
        "de soupçon, audit et reporting."
    ),
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.middleware("http")(request_id_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Routers (préfixe /api/v1)
for router in (
    auth.router, customers.router, transactions.router, accounts.router,
    alerts.router, cases.router, rules.router, screening.router,
    declarations.router, dashboard.router, org.router, users.router,
    audit.router, network.router, misc.router, postes.router,
):
    app.include_router(router, prefix="/api/v1")


# ------------------------- Purge périodique des logs d'audit -------------------------
@app.on_event("startup")
async def start_audit_log_purge_task():
    """Tache de fond : purge automatique periodique des journaux d'audit obsoletes.

    Aucun endpoint ne permet de supprimer manuellement les logs (meme le
    superadmin) : seule cette tache retire les entrees depassant la duree de
    conservation configuree via `audit_log_retention_days`.
    """
    async def _purge_loop():
        while True:
            try:
                async for db in get_db():
                    count = await purge_obsolete_audit_logs(db)
                    if count:
                        print(f"[log-purge] {count} entree(s) d'audit obsoletes purges")
                    break
            except Exception as exc:  # pragma: no cover
                print(f"[log-purge] erreur: {type(exc).__name__}: {exc}")
            await asyncio.sleep(86400)  # cycle quotidien

    asyncio.create_task(_purge_loop())


# ------------------------- Health / status -------------------------
@app.get("/health", tags=["system"])
async def health(request: Request):
    return {"success": True, "data": {"status": "ok", "app": "CIF Guard API"},
            "meta": {"requestId": request.state.request_id}}


@app.get("/health/database", tags=["system"])
async def health_database(request: Request):
    async for db in get_db():
        try:
            await db.execute(text("SELECT 1"))
            ok, detail = True, "ok"
        except Exception as exc:  # pragma: no cover
            ok, detail = False, str(exc).split("\n")[0]
        break
    return {"success": True, "data": {"database": detail if ok else "error"},
            "meta": {"requestId": request.state.request_id}}


# ------------------------- Admin frontend (statique) -------------------------
app.mount("/admin", StaticFiles(directory="app/static/admin", html=True), name="admin")


@app.get("/", tags=["system"], include_in_schema=False)
async def root():
    return {"success": True, "data": {
        "name": "CIF Guard API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "admin": "/admin",
    }, "meta": {"requestId": "root"}}