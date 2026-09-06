"""Module ALERTES — CDC §21-22 (SLA, escalade, workflow complet)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.alert import Alert, AlertAssignment, AlertComment, AlertEvent
from app.models.auth import User
from app.schemas.operations import (
    AlertAssign,
    AlertCommentBody,
    AlertCreate,
    AlertInfoRequest,
    AlertUpdate,
)
from app.services.audit_service import audit

router = APIRouter(prefix="/alerts", tags=["alerts"])
settings = get_settings()


def _due_for(priority: str) -> datetime:
    minutes = settings.ALERT_SLA_MINUTES.get(priority.strip().lower(), 12 * 60)
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


async def _get_alert(db: AsyncSession, alert_id: int):
    res = await db.execute(select(Alert).where(Alert.id == alert_id))
    a = res.scalar_one_or_none()
    if a is None:
        raise AppError("ALERT_NOT_FOUND", "Alerte introuvable", status=404)
    return a


def _serialize(a: Alert) -> dict:
    now = datetime.now(timezone.utc)
    overdue = a.due_at is not None and a.due_at < now and a.status not in ("CLOSED", "DISMISSED", "CONFIRMED")
    return {
        "id": a.id, "code": a.code, "title": a.title, "description": a.description,
        "severity": a.severity, "priority": a.priority, "alert_type": a.alert_type,
        "status": a.status, "customer_id": a.customer_id, "transaction_id": a.transaction_id,
        "branch_id": a.branch_id, "source": a.source, "rule_id": a.rule_id,
        "assigned_to": a.assigned_to, "created_by": a.created_by,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "due_at": a.due_at.isoformat() if a.due_at else None,
        "is_overdue": overdue,
        "remaining_minutes": round((a.due_at - now).total_seconds() / 60) if a.due_at else None,
    }


@router.get("")
async def list_alerts(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    severity: str | None = None,
    assigned_to: int | None = None,
    overdue: bool | None = None,
):
    q = select(Alert)
    # ABAC : un agent/responsable ne voit que les alertes de sa caisse
    if not user.can_access_branch(None):
        q = q.where(Alert.branch_id == user.branch_id)
    if status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    if assigned_to:
        q = q.where(Alert.assigned_to == assigned_to)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(Alert.created_at.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    data = [_serialize(a) for a in rows]
    if overdue is True:
        data = [d for d in data if d["is_overdue"]]
    return {"success": True, "data": data,
            "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.post("")
async def create_alert(body: AlertCreate, request: Request,
                       user: CurrentUser = Depends(require("manage:alerts")),
                       db: AsyncSession = Depends(get_db)):
    code = f"AL-{datetime.now().strftime('%Y%m%d')}-{await _next_code(db)}"
    a = Alert(
        code=code, title=body.title, description=body.description,
        severity=body.severity, priority=body.priority,
        status="NEW", source=body.source,
        customer_id=body.customer_id, transaction_id=body.transaction_id,
        branch_id=body.branch_id or user.branch_id,
        created_by=user.id,
        due_at=_due_for(body.priority),
    )
    db.add(a)
    await db.flush()
    db.add(AlertEvent(alert_id=a.id, event_type="CREATED", user_id=user.id,
                      payload=json.dumps({"source": body.source})))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_CREATED",
                entity_type="ALERT", entity_id=a.id,
                new_value={"code": code, "severity": a.severity},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}


async def _next_code(db: AsyncSession) -> str:
    res = await db.execute(select(func.count()).select_from(Alert))
    return f"{res.scalar() + 1:04d}"


@router.get("/{alert_id}")
async def get_alert(alert_id: int, user: CurrentUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    if not user.can_access_branch(a.branch_id):
        raise AppError("FORBIDDEN", "Alerte hors périmètre", status=403)
    ev_res = await db.execute(
        select(AlertEvent).where(AlertEvent.alert_id == alert_id).order_by(AlertEvent.created_at)
    )
    comments = (await db.execute(
        select(AlertComment).where(AlertComment.alert_id == alert_id).order_by(AlertComment.created_at)
    )).scalars().all()
    return {"success": True, "data": {
        ** _serialize(a),
        "events": [{"type": e.event_type, "at": e.created_at.isoformat(), "user_id": e.user_id}
                   for e in ev_res.scalars().all()],
        "comments": [{"id": c.id, "user_id": c.user_id, "body": c.body,
                      "at": c.created_at.isoformat()} for c in comments],
    }, "meta": {"requestId": "get"}}


@router.patch("/{alert_id}")
async def update_alert(alert_id: int, body: AlertUpdate, request: Request,
                       user: CurrentUser = Depends(require("manage:alerts")),
                       db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    if body.status:
        a.status = body.status
    if body.priority:
        a.priority = body.priority
        a.due_at = _due_for(body.priority)
    if body.severity:
        a.severity = body.severity
    if body.status == "CLOSED" and a.resolved_at is None:
        a.resolved_at = datetime.now()
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_UPDATED",
                entity_type="ALERT", entity_id=alert_id,
                new_value=body.model_dump(exclude_none=True),
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/assign")
async def assign_alert(alert_id: int, body: AlertAssign, request: Request,
                       user: CurrentUser = Depends(require("manage:alerts")),
                       db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    target = (await db.execute(select(User).where(User.id == body.user_id))).scalar_one_or_none()
    if target is None:
        raise AppError("USER_NOT_FOUND", "Utilisateur inexistant", status=404)
    prev = a.assigned_to
    a.assigned_to = body.user_id
    a.status = "IN_PROGRESS"
    db.add(AlertAssignment(alert_id=alert_id, user_id=body.user_id,
                           assigned_by=user.id, previous_user_id=prev))
    db.add(AlertEvent(alert_id=alert_id, event_type="ASSIGNED", user_id=user.id,
                      payload=json.dumps({"from": prev, "to": body.user_id})))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_ASSIGNED",
                entity_type="ALERT", entity_id=alert_id,
                old_value={"assigned_to": prev}, new_value={"assigned_to": body.user_id},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/escalate")
async def escalate_alert(alert_id: int, request: Request,
                         user: CurrentUser = Depends(require("manage:alerts")),
                         db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    a.status = "ESCALATED"
    db.add(AlertEvent(alert_id=alert_id, event_type="ESCALATED", user_id=user.id,
                      payload=json.dumps({"by": user.id})))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_ESCALATED",
                entity_type="ALERT", entity_id=alert_id,
                new_value={"status": "ESCALATED"},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/comment")
async def comment_alert(alert_id: int, body: AlertCommentBody, request: Request,
                        user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    await _get_alert(db, alert_id)
    db.add(AlertComment(alert_id=alert_id, user_id=user.id, body=body.body))
    db.add(AlertEvent(alert_id=alert_id, event_type="COMMENTED", user_id=user.id,
                      payload=json.dumps({"preview": body.body[:80]})))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_COMMENTED",
                entity_type="ALERT", entity_id=alert_id,
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"message": "Commentaire ajouté"},
            "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/request-information")
async def request_information(alert_id: int, body: AlertInfoRequest, request: Request,
                              user: CurrentUser = Depends(require("manage:alerts")),
                              db: AsyncSession = Depends(get_db)):
    from app.models.extra import InformationRequest
    a = await _get_alert(db, alert_id)
    req = InformationRequest(
        code=f"IR-{datetime.now().strftime('%Y%m%d')}-{alert_id:04d}",
        request_type=body.request_type, status="REQUESTED",
        customer_id=a.customer_id, alert_id=alert_id,
        requested_by=user.id, details=body.details,
    )
    db.add(req)
    a.status = "PENDING"
    db.add(AlertEvent(alert_id=alert_id, event_type="INFO_REQUESTED", user_id=user.id,
                      payload=json.dumps({"type": body.request_type})))
    await audit(db, actor_id=user.id, actor_role=user.role, action="INFORMATION_REQUESTED",
                entity_type="ALERT", entity_id=alert_id,
                new_value={"type": body.request_type},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"req_id": req.id, "status": a.status},
            "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/confirm")
async def confirm_alert(alert_id: int, request: Request,
                        user: CurrentUser = Depends(require("manage:alerts")),
                        db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    a.status = "CONFIRMED"
    db.add(AlertEvent(alert_id=alert_id, event_type="CONFIRMED", user_id=user.id))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_CONFIRMED",
                entity_type="ALERT", entity_id=alert_id,
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int, request: Request,
                        user: CurrentUser = Depends(require("manage:alerts")),
                        db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    a.status = "DISMISSED"
    a.resolved_at = datetime.now()
    db.add(AlertEvent(alert_id=alert_id, event_type="DISMISSED", user_id=user.id))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_DISMISSED",
                entity_type="ALERT", entity_id=alert_id,
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}


@router.post("/{alert_id}/close")
async def close_alert(alert_id: int, request: Request,
                      user: CurrentUser = Depends(require("manage:alerts")),
                      db: AsyncSession = Depends(get_db)):
    a = await _get_alert(db, alert_id)
    a.status = "CLOSED"
    a.resolved_at = datetime.now()
    db.add(AlertEvent(alert_id=alert_id, event_type="CLOSED", user_id=user.id))
    await audit(db, actor_id=user.id, actor_role=user.role, action="ALERT_CLOSED",
                entity_type="ALERT", entity_id=alert_id,
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": _serialize(a), "meta": {"requestId": request.state.request_id}}