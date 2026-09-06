"""Module POSTES DE TRAVAIL — CDC §5 postes d'agent."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.auth import User
from app.models.org import Branch
from app.models.poste import PosteDeTravail
from app.services.audit_service import audit

router = APIRouter(tags=["postes"])


class PosteCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    branch_id: int
    user_id: int | None = None
    device_id: str = ""
    location: str = ""


class PosteUpdate(BaseModel):
    name: str | None = None
    branch_id: int | None = None
    user_id: int | None = None
    device_id: str | None = None
    location: str | None = None
    is_active: bool | None = None


@router.get("/postes")
async def list_postes(user: CurrentUser = Depends(require("read:postes")),
                      db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(PosteDeTravail)
        .options(selectinload(PosteDeTravail.branch), selectinload(PosteDeTravail.user))
        .order_by(PosteDeTravail.code)
    )
    rows = res.scalars().all()
    return {"success": True, "data": [_serialize(p) for p in rows], "meta": {"requestId": "list"}}


@router.post("/postes")
async def create_poste(body: PosteCreate, request: Request,
                      user: CurrentUser = Depends(require("manage:postes")),
                      db: AsyncSession = Depends(get_db)):
    dup = (await db.execute(
        select(PosteDeTravail).where(PosteDeTravail.code == body.code)
    )).scalar_one_or_none()
    if dup:
        raise AppError("DUPLICATE_POSTE", "Code de poste déjà utilisé", status=409)
    branch = (await db.execute(
        select(Branch).where(Branch.id == body.branch_id)
    )).scalar_one_or_none()
    if branch is None:
        raise AppError("BRANCH_NOT_FOUND", "Caisse introuvable", status=404)
    if body.user_id is not None:
        agent = (await db.execute(
            select(User).where(User.id == body.user_id)
        )).scalar_one_or_none()
        if agent is None:
            raise AppError("USER_NOT_FOUND", "Utilisateur introuvable", status=404)
    p = PosteDeTravail(
        code=body.code, name=body.name, branch_id=body.branch_id,
        user_id=body.user_id, device_id=body.device_id, location=body.location,
    )
    db.add(p)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="POSTE_CREATED",
                entity_type="POSTE", entity_id=p.id,
                new_value={"code": body.code, "name": body.name, "branch_id": body.branch_id},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(p)
    return {"success": True, "data": {"id": p.id, "code": p.code, "name": p.name},
            "meta": {"requestId": request.state.request_id}}


@router.get("/postes/{poste_id}")
async def get_poste(poste_id: int, user: CurrentUser = Depends(require("read:postes")),
                    db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(PosteDeTravail)
        .options(selectinload(PosteDeTravail.branch), selectinload(PosteDeTravail.user))
        .where(PosteDeTravail.id == poste_id)
    )
    p = res.scalar_one_or_none()
    if p is None:
        raise AppError("POSTE_NOT_FOUND", "Poste introuvable", status=404)
    return {"success": True, "data": _serialize(p), "meta": {"requestId": "get"}}


@router.patch("/postes/{poste_id}")
async def update_poste(poste_id: int, body: PosteUpdate, request: Request,
                      user: CurrentUser = Depends(require("manage:postes")),
                      db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(PosteDeTravail).where(PosteDeTravail.id == poste_id))
    p = res.scalar_one_or_none()
    if p is None:
        raise AppError("POSTE_NOT_FOUND", "Poste introuvable", status=404)
    old = {"is_active": p.is_active, "name": p.name, "branch_id": p.branch_id}
    if body.branch_id is not None:
        branch = (await db.execute(
            select(Branch).where(Branch.id == body.branch_id)
        )).scalar_one_or_none()
        if branch is None:
            raise AppError("BRANCH_NOT_FOUND", "Caisse introuvable", status=404)
    if body.user_id is not None:
        agent = (await db.execute(
            select(User).where(User.id == body.user_id)
        )).scalar_one_or_none()
        if agent is None:
            raise AppError("USER_NOT_FOUND", "Utilisateur introuvable", status=404)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    await audit(db, actor_id=user.id, actor_role=user.role, action="POSTE_UPDATED",
                entity_type="POSTE", entity_id=poste_id,
                old_value=old, new_value=body.model_dump(exclude_none=True),
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(p)
    return {"success": True, "data": {"id": p.id, "code": p.code, "name": p.name},
            "meta": {"requestId": request.state.request_id}}


@router.delete("/postes/{poste_id}")
async def delete_poste(poste_id: int, request: Request,
                      user: CurrentUser = Depends(require("manage:postes")),
                      db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(PosteDeTravail).where(PosteDeTravail.id == poste_id))
    p = res.scalar_one_or_none()
    if p is None:
        raise AppError("POSTE_NOT_FOUND", "Poste introuvable", status=404)
    if not p.is_active:
        raise AppError("POSTE_ALREADY_DISABLED", "Poste déjà désactivé", status=409)
    p.is_active = False
    await audit(db, actor_id=user.id, actor_role=user.role, action="POSTE_DELETED",
                entity_type="POSTE", entity_id=poste_id,
                old_value={"is_active": True}, new_value={"is_active": False},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": p.id, "is_active": False},
            "meta": {"requestId": request.state.request_id}}


def _serialize(p: PosteDeTravail) -> dict:
    return {
        "id": p.id, "code": p.code, "name": p.name,
        "branch_id": p.branch_id, "user_id": p.user_id,
        "device_id": p.device_id, "location": p.location,
        "is_active": p.is_active,
        "branch_name": p.branch.name if p.branch else None,
        "user_email": p.user.email if p.user else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
