"""Module AUTH — CDC §7.

POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
POST   /api/v1/auth/change-password
POST   /api/v1/auth/recover
GET    /api/v1/auth/sessions
DELETE /api/v1/auth/sessions/:id
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core import security
from app.core.dependencies import CurrentUser, get_current_user
from app.core.errors import AppError
from app.database import get_db
from app.models.auth import User, UserSession, RefreshToken, user_roles
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RecoverRequest,
    RefreshRequest,
    SessionInfo,
)
from app.schemas.common import OKResponse
from app.services.audit_service import audit

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _client_info(request: Request) -> tuple[str, str, str]:
    ip = request.client.host if request.client else ""
    device = request.headers.get("x-device-id", "")
    ua = request.headers.get("user-agent", "")[:400]
    return ip, device, ua


async def _create_session(db: AsyncSession, user: User, ip: str, device: str, ua: str) -> UserSession:
    sid = uuid.uuid4().hex
    sess = UserSession(
        id=sid,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_EXPIRES_DAYS),
        ip_address=ip,
        device_id=device,
        user_agent=ua,
    )
    db.add(sess)
    await db.flush()
    return sess


@router.post("/login", response_model=OKResponse[LoginResponse])
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.email == body.email)
    )
    user = res.scalar_one_or_none()
    if user is None or not security.verify_password(body.password, user.password_hash):
        await audit(db, action="LOGIN_FAILED", actor_role="", entity_type="AUTH",
                    reason="Identifiants invalides", request_id=request.state.request_id)
        raise AppError("INVALID_CREDENTIALS", "Email ou mot de passe incorrect", status=401)
    if not user.is_active:
        raise AppError("USER_INACTIVE", "Compte désactivé", status=403)

    ip, device, ua = _client_info(request)
    session = await _create_session(db, user, ip, device, ua)

    role = user.roles[0].code if user.roles else "user"
    access = security.create_access_token(
        subject=user.email, user_id=user.id, role=role,
        branch_id=user.branch_id, coop_id=user.cooperative_id, session_id=session.id,
    )

    rt = RefreshToken(
        id=uuid.uuid4().hex, user_id=user.id, session_id=session.id,
        expires_at=session.expires_at,
    )
    db.add(rt)
    await db.flush()
    refresh = security.create_refresh_token(user.email, user.id, session.id, jti=rt.id)

    await audit(db, actor_id=user.id, actor_role=role, action="LOGIN",
                entity_type="AUTH", ip_address=ip,
                request_id=request.state.request_id, reason="Connexion réussie")
    await db.commit()

    return OKResponse(
        data=LoginResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.JWT_EXPIRES_MINUTES * 60,
        ),
        meta={"requestId": request.state.request_id},
    )


@router.post("/refresh", response_model=OKResponse[LoginResponse])
async def refresh(body: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = security.decode_token(body.refresh_token, expected_type="refresh")
    except Exception:
        raise AppError("INVALID_TOKEN", "Refresh token invalide", status=401)

    rt_res = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == payload.get("jti"),
            RefreshToken.session_id == payload.get("sid"),
        )
    )
    rt = rt_res.scalar_one_or_none()
    if rt is None or rt.revoked_at is not None or rt.expires_at < datetime.now(timezone.utc):
        raise AppError("INVALID_TOKEN", "Refresh token expiré ou révoqué", status=401)

    res = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == rt.user_id)
    )
    user = res.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AppError("USER_INACTIVE", "Utilisateur inactif", status=401)

    # Rotate refresh token
    rt.revoked_at = datetime.now(timezone.utc)
    new_rt = RefreshToken(
        id=uuid.uuid4().hex, user_id=user.id, session_id=rt.session_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_EXPIRES_DAYS),
    )
    db.add(new_rt)
    await db.flush()

    role = user.roles[0].code if user.roles else "user"
    access = security.create_access_token(
        subject=user.email, user_id=user.id, role=role,
        branch_id=user.branch_id, coop_id=user.cooperative_id,
        session_id=rt.session_id,
    )
    refresh = security.create_refresh_token(user.email, user.id, rt.session_id, jti=new_rt.id)
    await db.commit()
    return OKResponse(
        data=LoginResponse(
            access_token=access, refresh_token=refresh,
            expires_in=settings.JWT_EXPIRES_MINUTES * 60,
        ),
        meta={"requestId": request.state.request_id},
    )


@router.post("/logout")
async def logout(request: Request, user: CurrentUser = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    sess_res = await db.execute(
        select(UserSession).where(UserSession.id == user.session_id)
    )
    sess = sess_res.scalar_one_or_none()
    if sess:
        sess.revoked_at = datetime.now(timezone.utc)
    await audit(db, actor_id=user.id, actor_role=user.role, action="LOGOUT",
                entity_type="AUTH", entity_id=user.session_id,
                ip_address=request.client.host if request.client else "",
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"message": "Déconnecté"}, "meta": {"requestId": request.state.request_id}}


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "branch_id": user.branch_id,
            "cooperative_id": user.cooperative_id,
            "roles": user.roles,
            "permissions": sorted(user.permissions),
        },
        "meta": {"requestId": "me"},
    }


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, request: Request,
                          user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.id == user.id))
    u = res.scalar_one()
    if not security.verify_password(body.current_password, u.password_hash):
        raise AppError("WRONG_PASSWORD", "Mot de passe actuel incorrect", status=400)
    u.password_hash = security.hash_password(body.new_password)
    u.must_change_password = False
    await audit(db, actor_id=user.id, actor_role=user.role, action="PASSWORD_CHANGED",
                entity_type="AUTH", entity_id=user.id,
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"message": "Mot de passe mis à jour"}, "meta": {"requestId": request.state.request_id}}


@router.post("/recover")
async def recover(body: RecoverRequest, db: AsyncSession = Depends(get_db)):
    """Récupération sécurisée : en production, génère un lien/OTP. MVP : vérifie l'existence."""
    res = await db.execute(select(User).where(User.email == body.email))
    user = res.scalar_one_or_none()
    if user is None:
        # Ne pas révéler l'existence d'un compte
        return {"success": True, "data": {"message": "Si le compte existe, un courriel a été envoyé"}, "meta": {}}
    await audit(db, actor_id=user.id, actor_role="", action="RECOVERY_REQUESTED",
                entity_type="AUTH", entity_id=user.id)
    await db.commit()
    return {"success": True, "data": {"message": "Si le compte existe, un courriel a été envoyé"}, "meta": {}}


@router.get("/sessions")
async def list_sessions(user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(UserSession).where(UserSession.user_id == user.id).order_by(UserSession.created_at.desc())
    )
    sessions = res.scalars().all()
    data = [
        SessionInfo(
            id=s.id,
            created_at=s.created_at.isoformat(),
            expires_at=s.expires_at.isoformat(),
            revoked=s.revoked_at is not None,
            ip_address=s.ip_address,
            device_id=s.device_id,
            user_agent=s.user_agent,
        )
        for s in sessions
    ]
    return {"success": True, "data": data, "meta": {"requestId": "sessions"}}


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user.id)
    )
    sess = res.scalar_one_or_none()
    if sess is None:
        raise AppError("SESSION_NOT_FOUND", "Session introuvable", status=404)
    sess.revoked_at = datetime.now(timezone.utc)
    await audit(db, actor_id=user.id, actor_role=user.role, action="SESSION_REVOKED",
                entity_type="AUTH", entity_id=user.id,
                reason=f"Session {session_id} révoquée")
    await db.commit()
    return {"success": True, "data": {"message": "Session révoquée"}, "meta": {"requestId": "revoke"}}
