"""Module SCREENING — CDC §16-17, §36 (listes versionnées, matcher, import/sync)."""
from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.screening import (
    ScreeningListVersion, ScreeningMatch, ScreeningRun, ScreeningSource,
    ScreeningList, ScreeningEntity,
)
from app.services.audit_service import audit

router = APIRouter(prefix="/screening", tags=["screening"])


@router.get("/matches")
async def list_matches(user: CurrentUser = Depends(require("read:screening")),
                       db: AsyncSession = Depends(get_db),
                       page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                       status: str | None = None):
    q = select(ScreeningMatch)
    if status:
        q = q.where(ScreeningMatch.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(ScreeningMatch.score.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    data = []
    for m in rows:
        ent = (await db.execute(select(ScreeningEntity).where(ScreeningEntity.id == m.entity_id))).scalar_one_or_none()
        lv = (await db.execute(select(ScreeningListVersion).where(ScreeningListVersion.id == m.list_version_id))).scalar_one_or_none()
        data.append({
            "id": m.id, "run_id": m.run_id, "entity": ent.full_name if ent else None,
            "match_type": m.match_type, "score": m.score, "status": m.status,
            "list_version": f"{lv.version}" if lv else None,
        })
    return {"success": True, "data": data,
            "meta": {"page": page, "limit": limit, "total": total, "requestId": "matches"}}


@router.get("/runs")
async def list_runs(user: CurrentUser = Depends(require("read:screening")),
                    db: AsyncSession = Depends(get_db),
                    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    q = select(ScreeningRun)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(ScreeningRun.executed_at.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [{
        "id": r.id, "subject_type": r.subject_type, "subject_id": r.subject_id,
        "executed_at": r.executed_at.isoformat(), "status": r.status,
    } for r in rows], "meta": {"page": page, "limit": limit, "total": total, "requestId": "runs"}}


@router.get("/list-versions")
async def list_versions(user: CurrentUser = Depends(require("read:screening")),
                        db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ScreeningList, ScreeningListVersion)
        .join(ScreeningListVersion, ScreeningListVersion.list_id == ScreeningList.id)
        .order_by(ScreeningListVersion.published_at.desc())
    )
    rows = res.all()
    return {"success": True, "data": [{
        "list_id": l.id, "list_name": l.name, "version": v.version,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "downloaded_at": v.downloaded_at.isoformat() if v.downloaded_at else None,
        "checksum": v.checksum, "is_current": v.is_current,
    } for l, v in rows], "meta": {"requestId": "versions"}}


@router.get("/list-versions/{version_id}")
async def get_version(version_id: int, user: CurrentUser = Depends(require("read:screening")),
                      db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ScreeningListVersion).where(ScreeningListVersion.id == version_id))
    v = res.scalar_one_or_none()
    if v is None:
        raise AppError("VERSION_NOT_FOUND", "Version introuvable", status=404)
    entities = (await db.execute(
        select(ScreeningEntity).where(ScreeningEntity.list_version_id == version_id).limit(50)
    )).scalars().all()
    return {"success": True, "data": {
        "id": v.id, "list_id": v.list_id, "version": v.version,
        "published_at": v.published_at, "downloaded_at": v.downloaded_at,
        "checksum": v.checksum, "is_current": v.is_current,
        "entities_preview": [{"id": e.id, "full_name": e.full_name, "type": e.entity_type}
                             for e in entities],
    }, "meta": {"requestId": "version"}}


class ImportListItem(BaseModel):
    full_name: str
    entity_type: str = "INDIVIDUAL"
    country: str = ""
    reason: str = ""


class ListImportBody(BaseModel):
    list_name: str
    source_code: str = "SANCTIONS"
    version: str = "MANUAL"
    items: list[ImportListItem]


@router.post("/lists/import")
async def import_list(body: ListImportBody, request: Request,
                      user: CurrentUser = Depends(require("manage:screening")),
                      db: AsyncSession = Depends(get_db)):
    src_res = await db.execute(select(ScreeningSource).where(ScreeningSource.code == body.source_code))
    src = src_res.scalar_one_or_none()
    if src is None:
        src = ScreeningSource(code=body.source_code, name=body.source_code)
        db.add(src)
        await db.flush()
    sl = ScreeningList(source_id=src.id, name=body.list_name, is_active=True)
    db.add(sl)
    await db.flush()

    payload = "|".join(f"{i.full_name}{i.country}" for i in body.items)
    checksum = hashlib.sha256(payload.encode()).hexdigest()
    version = ScreeningListVersion(
        list_id=sl.id, version=body.version, published_at=datetime.now(),
        downloaded_at=datetime.now(), checksum=checksum, is_current=True,
    )
    db.add(version)
    await db.flush()

    # Invalidate les anciennes versions actuelles de la même liste
    await db.execute(
        ScreeningListVersion.__table__.update()
        .where(ScreeningListVersion.list_id == sl.id)
        .values(is_current=False)
    )
    version.is_current = True

    for item in body.items:
        db.add(ScreeningEntity(list_version_id=version.id, full_name=item.full_name,
                               entity_type=item.entity_type, country=item.country,
                               reason=item.reason))
    await audit(db, actor_id=user.id, actor_role=user.role, action="LIST_IMPORTED",
                entity_type="SCREENING_LIST", entity_id=sl.id,
                new_value={"name": body.list_name, "version": body.version,
                           "items": len(body.items), "checksum": checksum[:16]},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"list_id": sl.id, "version_id": version.id,
                                      "checksum": checksum, "items": len(body.items)},
            "meta": {"requestId": request.state.request_id}}


@router.get("/lists/status")
async def lists_status(user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """Fraîcheur des listes (CDC §35)."""
    res = await db.execute(
        select(ScreeningList, ScreeningListVersion)
        .join(ScreeningListVersion, ScreeningListVersion.list_id == ScreeningList.id)
        .where(ScreeningListVersion.is_current.is_(True))
    )
    rows = res.all()
    return {"success": True, "data": [{
        "list_id": l.id, "list_name": l.name, "version": v.version,
        "downloaded_at": v.downloaded_at, "is_current": v.is_current,
        "expires_at": v.effective_from,
    } for l, v in rows], "meta": {"requestId": "status"}}