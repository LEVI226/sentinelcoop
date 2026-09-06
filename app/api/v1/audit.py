"""Module AUDIT — CDC §24-25 (journal horodaté, recherche/filtres)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.database import get_db
from app.models.extra import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit(user: CurrentUser = Depends(require("read:audit")),
                     db: AsyncSession = Depends(get_db),
                     page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                     entity_type: str | None = None, entity_id: int | None = None,
                     action: str | None = None, actor_id: int | None = None):
    q = select(AuditLog)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.where(AuditLog.entity_id == entity_id)
    if action:
        q = q.where(AuditLog.action == action)
    if actor_id:
        q = q.where(AuditLog.actor_id == actor_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(AuditLog.timestamp.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [{
        "id": a.id, "ts": a.timestamp.isoformat(), "actor_id": a.actor_id,
        "actor_role": a.actor_role,
        "action": a.action, "entity_type": a.entity_type, "entity_id": a.entity_id,
        "reason": a.reason,
    } for a in rows], "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.get("/summary")
async def audit_summary(user: CurrentUser = Depends(require("read:audit")),
                        db: AsyncSession = Depends(get_db)):
    """Agrégats d'audit pour le dashboard."""
    by_action = dict((await db.execute(
        select(AuditLog.action, func.count()).group_by(AuditLog.action))).all())
    total = sum(by_action.values())
    return {"success": True, "data": {
        "total_events": total,
        "by_action": [{"action": a, "count": n} for a, n in by_action.items()],
    }, "meta": {"requestId": "summary"}}