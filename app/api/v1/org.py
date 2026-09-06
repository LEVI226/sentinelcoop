"""Module COOPÉRATIVES & CAISSES — CDC §9 (+ profils de risque local §28)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.org import Branch, BranchRiskProfile, Cooperative
from app.schemas.operations import BranchCreate, BranchRiskProfileUpdate
from app.services.audit_service import audit

router = APIRouter(tags=["org"])


class CoopCreate(BaseModel):
    name: str
    code: str
    country: str = ""


class CoopUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    is_active: bool | None = None


# ------------------------- Cooperatives -------------------------
@router.get("/cooperatives")
async def list_cooperatives(user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Cooperative).order_by(Cooperative.name))
    rows = res.scalars().all()
    return {"success": True, "data": [{
        "id": c.id, "name": c.name, "code": c.code, "country": c.country,
        "is_active": c.is_active,
    } for c in rows], "meta": {"requestId": "list"}}


@router.post("/cooperatives")
async def create_cooperative(body: CoopCreate, request: Request,
                             user: CurrentUser = Depends(require("manage:cooperatives")),
                             db: AsyncSession = Depends(get_db)):
    c = Cooperative(name=body.name, code=body.code, country=body.country)
    db.add(c)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="COOP_CREATED",
                entity_type="COOPERATIVE", entity_id=c.id,
                new_value={"code": c.code}, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(c)
    return {"success": True, "data": {"id": c.id, "name": c.name, "code": c.code},
            "meta": {"requestId": request.state.request_id}}


@router.get("/cooperatives/{coop_id}")
async def get_cooperative(coop_id: int, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Cooperative).where(Cooperative.id == coop_id))
    c = res.scalar_one_or_none()
    if c is None:
        raise AppError("COOP_NOT_FOUND", "Coopérative introuvable", status=404)
    branches = (await db.execute(
        select(Branch).where(Branch.cooperative_id == coop_id))).scalars().all()
    return {"success": True, "data": {
        "id": c.id, "name": c.name, "code": c.code, "country": c.country,
        "branches": [{"id": b.id, "code": b.code, "name": b.name, "city": b.city,
                      "sync_status": b.sync_status} for b in branches],
    }, "meta": {"requestId": "get"}}


@router.patch("/cooperatives/{coop_id}")
async def update_cooperative(coop_id: int, body: CoopUpdate, request: Request,
                             user: CurrentUser = Depends(require("manage:cooperatives")),
                             db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Cooperative).where(Cooperative.id == coop_id))
    c = res.scalar_one_or_none()
    if c is None:
        raise AppError("COOP_NOT_FOUND", "Coopérative introuvable", status=404)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(c, f, v)
    await audit(db, actor_id=user.id, actor_role=user.role, action="COOP_UPDATED",
                entity_type="COOPERATIVE", entity_id=coop_id,
                new_value=body.model_dump(exclude_none=True),
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(c)
    return {"success": True, "data": {"id": c.id, "name": c.name, "code": c.code},
            "meta": {"requestId": request.state.request_id}}


# ------------------------- Branches -------------------------
@router.get("/branches")
async def list_branches(user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Branch).order_by(Branch.code))
    rows = res.scalars().all()
    return {"success": True, "data": [{
        "id": b.id, "cooperative_id": b.cooperative_id, "code": b.code, "name": b.name,
        "city": b.city, "country": b.country, "is_active": b.is_active,
        "manager_name": b.manager_name, "sync_status": b.sync_status,
    } for b in rows], "meta": {"requestId": "list"}}


@router.post("/branches")
async def create_branch(body: BranchCreate, request: Request,
                        user: CurrentUser = Depends(require("manage:branches")),
                        db: AsyncSession = Depends(get_db)):
    dup = (await db.execute(select(Branch).where(Branch.code == body.code))).scalar_one_or_none()
    if dup:
        raise AppError("DUPLICATE_BRANCH", "Code caisse existant", status=409)
    b = Branch(code=body.code, name=body.name, cooperative_id=body.cooperative_id,
               city=body.city, country=body.country, manager_name=body.manager_name)
    db.add(b)
    await db.flush()
    db.add(BranchRiskProfile(branch_id=b.id, version=1))
    await audit(db, actor_id=user.id, actor_role=user.role, action="BRANCH_CREATED",
                entity_type="BRANCH", entity_id=b.id,
                new_value={"code": b.code, "name": b.name},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(b)
    return {"success": True, "data": {"id": b.id, "code": b.code, "name": b.name},
            "meta": {"requestId": request.state.request_id}}


@router.get("/branches/{branch_id}")
async def get_branch(branch_id: int, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Branch).where(Branch.id == branch_id))
    b = res.scalar_one_or_none()
    if b is None:
        raise AppError("BRANCH_NOT_FOUND", "Caisse introuvable", status=404)
    profile = (await db.execute(
        select(BranchRiskProfile).where(BranchRiskProfile.branch_id == branch_id)
        .order_by(BranchRiskProfile.version.desc()).limit(1))).scalar_one_or_none()
    return {"success": True, "data": {
        "id": b.id, "code": b.code, "name": b.name, "city": b.city,
        "cooperative_id": b.cooperative_id, "sync_status": b.sync_status,
        "risk_profile": {
            "overall_risk": profile.overall_risk if profile else 0,
            "cash_exposure": profile.cash_exposure if profile else 0,
            "geographical_exposure": profile.geographical_exposure if profile else 0,
            "economic_activity_exposure": profile.economic_activity_exposure if profile else 0,
        } if profile else None,
    }, "meta": {"requestId": "get"}}


@router.patch("/branches/{branch_id}")
async def update_branch(branch_id: int, request: Request,
                        user: CurrentUser = Depends(require("manage:branches")),
                        db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Branch).where(Branch.id == branch_id))
    b = res.scalar_one_or_none()
    if b is None:
        raise AppError("BRANCH_NOT_FOUND", "Caisse introuvable", status=404)
    body = await request.json()
    for f in ("name", "city", "country", "manager_name", "is_active"):
        if f in body:
            setattr(b, f, body[f])
    await audit(db, actor_id=user.id, actor_role=user.role, action="BRANCH_UPDATED",
                entity_type="BRANCH", entity_id=branch_id,
                new_value=body, request_id=request.state.request_id)
    await db.commit()
    await db.refresh(b)
    return {"success": True, "data": {"id": b.id, "code": b.code, "name": b.name},
            "meta": {"requestId": request.state.request_id}}


@router.post("/branches/{branch_id}/risk-profile")
async def update_risk_profile(branch_id: int, body: BranchRiskProfileUpdate, request: Request,
                              user: CurrentUser = Depends(require("manage:riskprofiles")),
                              db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(BranchRiskProfile).where(BranchRiskProfile.branch_id == branch_id)
        .order_by(BranchRiskProfile.version.desc()).limit(1)
    )
    profile = res.scalar_one_or_none()
    nv = (profile.version if profile else 0) + 1
    new_profile = BranchRiskProfile(
        branch_id=branch_id, version=nv,
        cash_exposure=body.cash_exposure,
        geographical_exposure=body.geographical_exposure,
        economic_activity_exposure=body.economic_activity_exposure,
        overall_risk=(body.cash_exposure + body.geographical_exposure
                      + body.economic_activity_exposure) // 3,
    )
    db.add(new_profile)
    await audit(db, actor_id=user.id, actor_role=user.role, action="RISK_PROFILE_UPDATED",
                entity_type="BRANCH", entity_id=branch_id,
                new_value={"version": nv}, request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"branch_id": branch_id, "version": nv},
            "meta": {"requestId": request.state.request_id}}