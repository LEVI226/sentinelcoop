"""Dépendances FastAPI : authentification, RBAC/ABAC."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import security
from app.core.errors import AppError
from app.database import get_db
from app.models.auth import RefreshToken, User, UserSession


@dataclass
class CurrentUser:
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    branch_id: Optional[int]
    cooperative_id: Optional[int]
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)
    session_id: str = ""

    @property
    def role(self) -> str:
        return self.roles[0] if self.roles else "user"

    def has(self, permission: str) -> bool:
        return permission in self.permissions

    def is_network_role(self) -> bool:
        return any(r in {"superadmin", "conformite_reseau"} for r in self.roles)

    def is_read_only(self) -> bool:
        return "auditeur" in self.roles

    def can_access_branch(self, target_branch_id: Optional[int]) -> bool:
        if self.is_network_role():
            return True
        if self.branch_id is None or target_branch_id is None:
            return False
        return self.branch_id == target_branch_id


async def _load_user(db: AsyncSession, user_id: int) -> Optional[User]:
    res = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    return res.scalar_one_or_none()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Extrait le token Bearer, vérifie la session, charge l'utilisateur et ses droits."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise AppError("UNAUTHORIZED", "Authentification requise", status=401)
    token = auth[7:]

    try:
        payload = security.decode_token(token, expected_type="access")
    except Exception:
        raise AppError("INVALID_TOKEN", "Token invalide ou expiré", status=401)

    session_id = payload.get("sid", "")
    user_id = payload.get("uid")

    if session_id:
        sess_res = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        sess = sess_res.scalar_one_or_none()
        if sess is None or sess.revoked_at is not None:
            raise AppError("SESSION_REVOKED", "Session révoquée", status=401)

    user = await _load_user(db, user_id)
    if user is None or not user.is_active:
        raise AppError("USER_INACTIVE", "Utilisateur inactif", status=401)

    roles = [r.code for r in user.roles]
    permissions: set[str] = set()
    for role in user.roles:
        for p in role.permissions:
            permissions.add(p.code)

    return CurrentUser(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        branch_id=user.branch_id,
        cooperative_id=user.cooperative_id,
        roles=roles,
        permissions=permissions,
        session_id=session_id,
    )


def require(*permissions: str):
    """Décorateur de permission RBAC."""
    def dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        for p in permissions:
            if not user.has(p):
                raise AppError("FORBIDDEN", f"Permission requise : {p}", status=403)
        return user
    return dep
