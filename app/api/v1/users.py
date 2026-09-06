"""Module USERS / ROLES & PERMISSIONS — CDC §8."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import security
from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.auth import Role, User, user_roles
from app.services.audit_service import audit

router = APIRouter(tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3)
    first_name: str = ""
    last_name: str = ""
    role: str
    branch_id: int | None = None
    cooperative_id: int | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    branch_id: int | None = None


@router.get("/users")
async def list_users(user: CurrentUser = Depends(require("read:users")),
                     db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(User).options(selectinload(User.roles)).order_by(User.id)
    )
    rows = res.scalars().all()
    return {"success": True, "data": [{
        "id": u.id, "email": u.email, "username": u.username,
        "first_name": u.first_name, "last_name": u.last_name,
        "branch_id": u.branch_id, "cooperative_id": u.cooperative_id,
        "is_active": u.is_active,
        "roles": [r.code for r in u.roles],
    } for u in rows], "meta": {"requestId": "list"}}


@router.post("/users")
async def create_user(body: UserCreate, request: Request,
                      user: CurrentUser = Depends(require("create:users")),
                      db: AsyncSession = Depends(get_db)):
    dup = (await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )).scalar_one_or_none()
    if dup:
        raise AppError("DUPLICATE_USER", "Email ou nom d'utilisateur déjà utilisé", status=409)
    role = (await db.execute(select(Role).where(Role.code == body.role))).scalar_one_or_none()
    if role is None:
        raise AppError("ROLE_NOT_FOUND", f"Rôle inconnu : {body.role}", status=404)
    u = User(
        email=body.email, username=body.username,
        first_name=body.first_name, last_name=body.last_name,
        branch_id=body.branch_id, cooperative_id=body.cooperative_id,
        password_hash=security.hash_password("CIFGuard@2026"),
        must_change_password=True,
    )
    db.add(u)
    await db.flush()
    await db.execute(user_roles.insert().values(user_id=u.id, role_id=role.id))
    await audit(db, actor_id=user.id, actor_role=user.role, action="USER_CREATED",
                entity_type="USER", entity_id=u.id,
                new_value={"email": body.email, "role": body.role},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": u.id, "email": u.email, "roles": [body.role]},
            "meta": {"requestId": request.state.request_id}}


@router.patch("/users/{user_id}")
async def update_user(user_id: int, body: UserUpdate, request: Request,
                      user: CurrentUser = Depends(require("update:users")),
                      db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if u is None:
        raise AppError("USER_NOT_FOUND", "Utilisateur introuvable", status=404)
    old = {"is_active": u.is_active}
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(u, f, v)
    await audit(db, actor_id=user.id, actor_role=user.role, action="USER_UPDATED",
                entity_type="USER", entity_id=user_id,
                old_value=old, new_value=body.model_dump(exclude_none=True),
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": u.id, "updated": True},
            "meta": {"requestId": request.state.request_id}}


@router.get("/roles")
async def list_roles(user: CurrentUser = Depends(require("read:users")),
                     db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Role).order_by(Role.code))
    rows = res.scalars().all()
    return {"success": True, "data": [{
        "id": r.id, "code": r.code, "name": r.name, "is_system": r.is_system,
        "permissions": [p.code for p in r.permissions],
    } for r in rows], "meta": {"requestId": "roles"}}