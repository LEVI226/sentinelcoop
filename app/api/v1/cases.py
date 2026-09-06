"""Module CASE MANAGEMENT — CDC §23."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.alert import (
    Alert, Case, CaseAlert, CaseDecision, CaseNote, CaseTask, CaseTransaction,
)
from app.schemas.operations import (
    CaseCreate, CaseDecisionBody, CaseNoteBody, CaseTaskBody,
)
from app.services.audit_service import audit

router = APIRouter(prefix="/cases", tags=["cases"])


async def _next_code(db: AsyncSession) -> str:
    res = await db.execute(select(func.count()).select_from(Case))
    return f"{res.scalar() + 1:03d}"


async def _get_case(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    c = res.scalar_one_or_none()
    if c is None:
        raise AppError("CASE_NOT_FOUND", "Dossier introuvable", status=404)
    return c


@router.post("")
async def create_case(body: CaseCreate, request: Request,
                      user: CurrentUser = Depends(require("manage:cases")),
                      db: AsyncSession = Depends(get_db)):
    case = Case(
        code=f"CASE-{datetime.now().strftime('%Y')}-{await _next_code(db)}",
        title=body.title, description=body.description,
        status="OPEN", risk_level="MEDIUM",
        customer_id=body.customer_id, created_by=user.id, assigned_to=user.id,
    )
    db.add(case)
    await db.flush()
    for alert_id in body.alert_ids:
        db.add(CaseAlert(case_id=case.id, alert_id=alert_id))
    await audit(db, actor_id=user.id, actor_role=user.role, action="CASE_CREATED",
                entity_type="CASE", entity_id=case.id,
                new_value={"code": case.code, "title": case.title},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(case)
    return {"success": True, "data": _serialize(case),
            "meta": {"requestId": request.state.request_id}}


def _serialize(c: Case) -> dict:
    return {
        "id": c.id, "code": c.code, "title": c.title, "description": c.description,
        "status": c.status, "risk_level": c.risk_level, "customer_id": c.customer_id,
        "assigned_to": c.assigned_to, "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "closed_at": c.closed_at.isoformat() if c.closed_at else None,
    }


@router.get("")
async def list_cases(user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db),
                     page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                     status: str | None = None):
    q = select(Case)
    if status:
        q = q.where(Case.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(Case.created_at.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [_serialize(c) for c in rows],
            "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.get("/{case_id}")
async def get_case(case_id: int, user: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    c = await _get_case(db, case_id)
    alerts = (await db.execute(
        select(Alert).join(CaseAlert, CaseAlert.alert_id == Alert.id)
        .where(CaseAlert.case_id == case_id))).scalars().all()
    txns = (await db.execute(
        select(CaseTransaction).where(CaseTransaction.case_id == case_id))).scalars().all()
    notes = (await db.execute(
        select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.created_at))).scalars().all()
    tasks = (await db.execute(
        select(CaseTask).where(CaseTask.case_id == case_id))).scalars().all()
    decisions = (await db.execute(
        select(CaseDecision).where(CaseDecision.case_id == case_id)
        .order_by(CaseDecision.decided_at.desc()))).scalars().all()
    return {"success": True, "data": {
        ** _serialize(c),
        "alerts": [{"id": a.id, "code": a.code, "title": a.title, "status": a.status} for a in alerts],
        "transactions": [{"id": t.transaction_id} for t in txns],
        "notes": [{"id": n.id, "user_id": n.user_id, "body": n.body,
                   "at": n.created_at.isoformat()} for n in notes],
        "tasks": [{"id": t.id, "title": t.title, "done": t.done} for t in tasks],
        "decisions": [{"id": d.id, "decision": d.decision, "reason": d.reason,
                       "by": d.decided_by, "at": d.decided_at.isoformat()} for d in decisions],
    }, "meta": {"requestId": "get"}}


@router.patch("/{case_id}")
async def update_case(case_id: int, request: Request,
                      user: CurrentUser = Depends(require("manage:cases")),
                      db: AsyncSession = Depends(get_db)):
    c = await _get_case(db, case_id)
    body = await request.json()
    for field in ("title", "description", "status", "risk_level", "assigned_to"):
        if field in body:
            setattr(c, field, body[field])
    await audit(db, actor_id=user.id, actor_role=user.role, action="CASE_UPDATED",
                entity_type="CASE", entity_id=case_id,
                new_value=body, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(c)
    return {"success": True, "data": _serialize(c), "meta": {"requestId": request.state.request_id}}


@router.post("/{case_id}/alerts")
async def add_alert(case_id: int, request: Request,
                    user: CurrentUser = Depends(require("manage:cases")),
                    db: AsyncSession = Depends(get_db)):
    await _get_case(db, case_id)
    body = await request.json()
    db.add(CaseAlert(case_id=case_id, alert_id=int(body["alert_id"])))
    await db.commit()
    return {"success": True, "data": {"message": "Alerte rattachée"}, "meta": {}}


@router.post("/{case_id}/transactions")
async def add_transaction(case_id: int, request: Request,
                          user: CurrentUser = Depends(require("manage:cases")),
                          db: AsyncSession = Depends(get_db)):
    await _get_case(db, case_id)
    body = await request.json()
    db.add(CaseTransaction(case_id=case_id, transaction_id=int(body["transaction_id"])))
    await db.commit()
    return {"success": True, "data": {"message": "Transaction rattachée"}, "meta": {}}


@router.post("/{case_id}/notes")
async def add_note(case_id: int, body: CaseNoteBody, request: Request,
                   user: CurrentUser = Depends(require("manage:cases")),
                   db: AsyncSession = Depends(get_db)):
    await _get_case(db, case_id)
    note = CaseNote(case_id=case_id, user_id=user.id, body=body.body)
    db.add(note)
    await audit(db, actor_id=user.id, actor_role=user.role, action="CASE_NOTE_ADDED",
                entity_type="CASE", entity_id=case_id,
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": note.id}, "meta": {"requestId": request.state.request_id}}


@router.post("/{case_id}/tasks")
async def add_task(case_id: int, body: CaseTaskBody, request: Request,
                   user: CurrentUser = Depends(require("manage:cases")),
                   db: AsyncSession = Depends(get_db)):
    await _get_case(db, case_id)
    task = CaseTask(case_id=case_id, title=body.title, assigned_to=body.assigned_to)
    db.add(task)
    await db.commit()
    return {"success": True, "data": {"id": task.id}, "meta": {"requestId": request.state.request_id}}


@router.post("/{case_id}/decision")
async def make_decision(case_id: int, body: CaseDecisionBody, request: Request,
                        user: CurrentUser = Depends(require("manage:cases")),
                        db: AsyncSession = Depends(get_db)):
    c = await _get_case(db, case_id)
    decision = CaseDecision(case_id=case_id, decision=body.decision,
                            reason=body.reason, decided_by=user.id)
    db.add(decision)
    if body.decision in ("CONFIRMED", "ESCALATE_TO_AUTHORITY"):
        c.status = "IN_PROGRESS"
    if body.decision == "CLOSE":
        c.status = "CLOSED"
        c.closed_at = datetime.now()
    await audit(db, actor_id=user.id, actor_role=user.role, action="CASE_DECIDED",
                entity_type="CASE", entity_id=case_id,
                new_value={"decision": body.decision, "reason": body.reason},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": decision.id, "decision": decision.decision},
            "meta": {"requestId": request.state.request_id}}


@router.post("/{case_id}/close")
async def close_case(case_id: int, request: Request,
                     user: CurrentUser = Depends(require("manage:cases")),
                     db: AsyncSession = Depends(get_db)):
    c = await _get_case(db, case_id)
    c.status = "CLOSED"
    c.closed_at = datetime.now()
    await audit(db, actor_id=user.id, actor_role=user.role, action="CASE_CLOSED",
                entity_type="CASE", entity_id=case_id,
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(c)
    return {"success": True, "data": _serialize(c), "meta": {"requestId": request.state.request_id}}