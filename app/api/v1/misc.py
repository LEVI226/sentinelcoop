"""Modules complémentaires : KYC, demandes d'info, documents, rapports,
notifications, synchronisation, paramètres système (CDC §14, §19, §22, §23, §31-34)."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.customer import Customer, CustomerDocument, CustomerRiskScore, NetworkIdentity
from app.models.extra import (
    Attachment, InformationRequest, Notification, Report, SyncEvent, SyncJob, SystemSetting,
)
from app.services.audit_service import audit
from app.services.risk_engine import recompute_customer_risk

router = APIRouter(tags=["misc"])


# ------------------------- KYC -------------------------
@router.patch("/customers/{customer_id}/kyc")
async def update_kyc(customer_id: int, request: Request,
                     user: CurrentUser = Depends(require("manage:kyc")),
                     db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = res.scalar_one_or_none()
    if c is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client introuvable", status=404)
    body = await request.json()
    old = {"status": c.kyc_status}
    if "kyc_status" in body:
        c.kyc_status = body["kyc_status"]
    if "is_pep" in body:
        c.is_pep = bool(body["is_pep"])
    await recompute_customer_risk(db, c.id)
    await audit(db, actor_id=user.id, actor_role=user.role, action="KYC_UPDATED",
                entity_type="CUSTOMER", entity_id=customer_id,
                old_value=old, new_value=body, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(c)
    return {"success": True, "data": {"kyc_status": c.kyc_status, "risk_level": c.risk_level},
            "meta": {"requestId": request.state.request_id}}


# ------------------------- Demandes d'information -------------------------
class InfoRequestCreate(BaseModel):
    customer_id: int
    request_type: str = "SOURCE_OF_FUNDS"
    details: str = ""
    alert_id: int | None = None
    case_id: int | None = None


class InfoRequestRespond(BaseModel):
    status: str  # SENT|PARTIALLY_RECEIVED|RECEIVED|EXPIRED|CLOSED


@router.get("/information-requests")
async def list_information_requests(user: CurrentUser = Depends(get_current_user),
                                    db: AsyncSession = Depends(get_db),
                                    status: str | None = None):
    q = select(InformationRequest)
    if status:
        q = q.where(InformationRequest.status == status)
    rows = (await db.execute(q.order_by(InformationRequest.created_at.desc()))).scalars().all()
    return {"success": True, "data": [{
        "id": r.id, "code": r.code, "request_type": r.request_type,
        "status": r.status, "customer_id": r.customer_id,
        "alert_id": r.alert_id, "case_id": r.case_id, "details": r.details,
        "created_at": r.created_at.isoformat(),
    } for r in rows], "meta": {"requestId": "list"}}


@router.post("/information-requests")
async def create_information_request(body: InfoRequestCreate, request: Request,
                                     user: CurrentUser = Depends(require("manage:cases")),
                                     db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(InformationRequest))).scalar()
    ir = InformationRequest(
        code=f"IRQ-{datetime.now().strftime('%Y')}-{total+1:03d}",
        customer_id=body.customer_id, request_type=body.request_type,
        details=body.details, alert_id=body.alert_id, case_id=body.case_id,
        requested_by=user.id,
    )
    db.add(ir)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="INFO_REQUEST_CREATED",
                entity_type="INFORMATION_REQUEST", entity_id=ir.id,
                new_value={"code": ir.code, "type": body.request_type},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": ir.id, "code": ir.code, "status": ir.status},
            "meta": {"requestId": request.state.request_id}}


@router.patch("/information-requests/{req_id}")
async def update_information_request(req_id: int, body: InfoRequestRespond, request: Request,
                                     user: CurrentUser = Depends(require("manage:cases")),
                                     db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(InformationRequest).where(InformationRequest.id == req_id))
    ir = res.scalar_one_or_none()
    if ir is None:
        raise AppError("IRQ_NOT_FOUND", "Demande introuvable", status=404)
    ir.status = body.status
    await db.commit()
    return {"success": True, "data": {"id": ir.id, "status": ir.status},
            "meta": {"requestId": request.state.request_id}}


# ------------------------- Documents / Pièces jointes -------------------------
@router.get("/documents")
async def list_documents(user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db),
                         customer_id: int | None = None):
    q = select(CustomerDocument)
    if customer_id:
        q = q.where(CustomerDocument.customer_id == customer_id)
    rows = (await db.execute(q.order_by(CustomerDocument.created_at.desc()))).scalars().all()
    return {"success": True, "data": [{
        "id": d.id, "customer_id": d.customer_id, "doc_type": d.doc_type,
        "status": d.status, "expires_at": d.expires_at.isoformat() if d.expires_at else None,
    } for d in rows], "meta": {"requestId": "list"}}


@router.get("/attachments")
async def list_attachments(user: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db),
                           object_type: str | None = None, object_id: int | None = None):
    q = select(Attachment)
    if object_type:
        q = q.where(Attachment.object_type == object_type)
    if object_id:
        q = q.where(Attachment.object_id == object_id)
    rows = (await db.execute(q.order_by(Attachment.created_at.desc()))).scalars().all()
    return {"success": True, "data": [{
        "id": a.id, "object_type": a.object_type, "object_id": a.object_id,
        "filename": a.filename, "content_type": a.content_type, "size_bytes": a.size_bytes,
    } for a in rows], "meta": {"requestId": "list"}}


# ------------------------- Rapports -------------------------
class ReportRequest(BaseModel):
    report_type: str
    format: str = "PDF"


@router.post("/reports")
async def request_report(body: ReportRequest, request: Request,
                         user: CurrentUser = Depends(require("generate:reports")),
                         db: AsyncSession = Depends(get_db)):
    """Génération asynchrone simulée : rapport créé, statut READY immédiatement
    (la génération PDF/XLSX de production serait un worker dédié)."""
    total = (await db.execute(select(func.count()).select_from(Report))).scalar()
    r = Report(report_type=body.report_type, format=body.format, status="READY",
               storage_key=f"reports/{datetime.now():%Y/%m}/{total+1}.{body.format.lower()}",
               requested_by=user.id)
    db.add(r)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="REPORT_REQUESTED",
                entity_type="REPORT", entity_id=r.id,
                new_value={"type": body.report_type, "format": body.format},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": r.id, "status": "READY",
                                      "report_type": r.report_type, "format": r.format},
            "meta": {"requestId": request.state.request_id}}


@router.get("/reports")
async def list_reports(user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Report).order_by(Report.created_at.desc()).limit(50))).scalars().all()
    return {"success": True, "data": [{
        "id": r.id, "report_type": r.report_type, "format": r.format,
        "status": r.status, "storage_key": r.storage_key,
        "created_at": r.created_at.isoformat(),
    } for r in rows], "meta": {"requestId": "list"}}


# ------------------------- Notifications -------------------------
@router.get("/notifications")
async def list_notifications(user: CurrentUser = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db),
                             unread_only: bool = False):
    q = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        q = q.where(Notification.is_read.is_(False))
    rows = (await db.execute(q.order_by(Notification.created_at.desc()).limit(50))).scalars().all()
    unread = (await db.execute(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )).scalar()
    return {"success": True, "data": [{
        "id": n.id, "event": n.event, "title": n.title, "body": n.body,
        "is_read": n.is_read, "created_at": n.created_at.isoformat(),
    } for n in rows], "meta": {"requestId": "list", "unread": unread}}


@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int, user: CurrentUser = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Notification).where(
        Notification.id == notif_id, Notification.user_id == user.id))
    n = res.scalar_one_or_none()
    if n is None:
        raise AppError("NOTIF_NOT_FOUND", "Notification introuvable", status=404)
    n.is_read = True
    await db.commit()
    return {"success": True, "data": {"id": n.id, "is_read": True}, "meta": {}}


# ------------------------- Synchronisation hors-ligne -------------------------
class SyncEventCreate(BaseModel):
    device_id: str
    sequence_number: int
    entity_type: str
    entity_id: int | None = None
    payload: str = "{}"


@router.post("/sync/events")
async def push_sync_events(body: SyncEventCreate, request: Request,
                           user: CurrentUser = Depends(require("manage:sync")),
                           db: AsyncSession = Depends(get_db)):
    event_id = f"{body.device_id}:{body.sequence_number}"
    dup = (await db.execute(select(SyncEvent).where(SyncEvent.event_id == event_id))).scalar_one_or_none()
    if dup:
        return {"success": True, "data": {"event_id": event_id, "status": "DUPLICATE"},
                "meta": {"requestId": request.state.request_id}}
    ev = SyncEvent(event_id=event_id, device_id=body.device_id,
                   sequence_number=body.sequence_number, entity_type=body.entity_type,
                   entity_id=body.entity_id, payload=body.payload, status="SYNCED",
                   server_received_at=datetime.now())
    db.add(ev)
    await db.commit()
    return {"success": True, "data": {"event_id": event_id, "status": "SYNCED"},
            "meta": {"requestId": request.state.request_id}}


@router.get("/sync/status")
async def sync_status(user: CurrentUser = Depends(require("manage:sync")),
                      db: AsyncSession = Depends(get_db)):
    jobs = (await db.execute(
        select(SyncJob).order_by(SyncJob.id.desc()).limit(10))).scalars().all()
    events = (await db.execute(
        select(SyncEvent.status, func.count()).group_by(SyncEvent.status))).all()
    return {"success": True, "data": {
        "recent_jobs": [{"id": j.id, "branch_id": j.branch_id, "status": j.status,
                         "direction": j.direction,
                         "started_at": j.started_at.isoformat() if j.started_at else None}
                        for j in jobs],
        "events_by_status": [{"status": s, "count": n} for s, n in events],
    }, "meta": {"requestId": "sync-status"}}


# ------------------------- Paramètres système -------------------------
@router.get("/settings")
async def list_settings(user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(SystemSetting).order_by(SystemSetting.key))).scalars().all()
    return {"success": True, "data": {s.key: s.value for s in rows},
            "meta": {"requestId": "settings"}}


@router.put("/settings")
async def update_settings(request: Request,
                          user: CurrentUser = Depends(require("manage:settings")),
                          db: AsyncSession = Depends(get_db)):
    body = await request.json()
    for key, value in body.items():
        row = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
        if row:
            row.value = str(value)
            row.updated_by = user.id
        else:
            db.add(SystemSetting(key=key, value=str(value), updated_by=user.id))
    await audit(db, actor_id=user.id, actor_role=user.role, action="SETTINGS_UPDATED",
                entity_type="SYSTEM", new_value=body, request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": body, "meta": {"requestId": request.state.request_id}}
