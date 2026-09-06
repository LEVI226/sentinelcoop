"""Module RULES ENGINE — CDC §15 (règles versionnées, activate/deactivate)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.rule import Rule, RuleVersion, RuleAction
from app.schemas.operations import RuleCreate
from app.services.audit_service import audit

router = APIRouter(prefix="/rules", tags=["rules"])


async def _get_rule(db: AsyncSession, rule_id: int) -> Rule:
    res = await db.execute(select(Rule).where(Rule.id == rule_id))
    r = res.scalar_one_or_none()
    if r is None:
        raise AppError("RULE_NOT_FOUND", "Règle introuvable", status=404)
    return r


def _serialize_rule(r: Rule, config: str = "") -> dict:
    return {
        "id": r.id, "code": r.code, "name": r.name, "rule_type": r.rule_type,
        "description": r.description, "is_active": r.is_active,
        "current_version_id": r.current_version_id, "config": config,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("")
async def list_rules(user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Rule).order_by(Rule.code))
    rules = res.scalars().all()
    data = []
    for r in rules:
        config = ""
        if r.current_version_id:
            ver = (await db.execute(
                select(RuleVersion).where(RuleVersion.id == r.current_version_id)
            )).scalar_one_or_none()
            config = ver.config_json if ver else ""
        data.append(_serialize_rule(r, config))
    return {"success": True, "data": data, "meta": {"requestId": "list"}}


@router.post("")
async def create_rule(body: RuleCreate, request: Request,
                      user: CurrentUser = Depends(require("manage:rules")),
                      db: AsyncSession = Depends(get_db)):
    dup = (await db.execute(select(Rule).where(Rule.code == body.code))).scalar_one_or_none()
    if dup:
        raise AppError("DUPLICATE_RULE", "Code de règle existant", status=409)
    rule = Rule(
        code=body.code, name=body.name, rule_type=body.rule_type,
        description=body.description, is_active=False,
    )
    db.add(rule)
    await db.flush()
    ver = RuleVersion(rule_id=rule.id, version=1, is_current=True,
                      config_json=body.config_json)
    db.add(ver)
    await db.flush()
    rule.current_version_id = ver.id
    await audit(db, actor_id=user.id, actor_role=user.role, action="RULE_CREATED",
                entity_type="RULE", entity_id=rule.id,
                new_value={"code": body.code, "type": body.rule_type},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(rule)
    return {"success": True, "data": _serialize_rule(rule, body.config_json),
            "meta": {"requestId": request.state.request_id}}


@router.get("/{rule_id}")
async def get_rule(rule_id: int, user: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    r = await _get_rule(db, rule_id)
    versions = (await db.execute(
        select(RuleVersion).where(RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc())
    )).scalars().all()
    return {"success": True, "data": {
        ** _serialize_rule(r),
        "versions": [{"id": v.id, "version": v.version, "is_current": v.is_current,
                      "config": v.config_json} for v in versions],
    }, "meta": {"requestId": "get"}}


@router.patch("/{rule_id}")
async def update_rule(rule_id: int, request: Request,
                      user: CurrentUser = Depends(require("manage:rules")),
                      db: AsyncSession = Depends(get_db)):
    r = await _get_rule(db, rule_id)
    body = await request.json()
    if "name" in body:
        r.name = body["name"]
    if "description" in body:
        r.description = body["description"]
    if "config_json" in body and r.current_version_id:
        ver = (await db.execute(
            select(RuleVersion).where(RuleVersion.id == r.current_version_id)
        )).scalar_one_or_none()
        if ver:
            ver.config_json = body["config_json"]
    await audit(db, actor_id=user.id, actor_role=user.role, action="RULE_UPDATED",
                entity_type="RULE", entity_id=rule_id,
                old_value={}, new_value=body,
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(r)
    return {"success": True, "data": _serialize_rule(r), "meta": {"requestId": request.state.request_id}}


@router.post("/{rule_id}/activate")
async def activate_rule(rule_id: int, request: Request,
                        user: CurrentUser = Depends(require("manage:rules")),
                        db: AsyncSession = Depends(get_db)):
    r = await _get_rule(db, rule_id)
    r.is_active = True
    await audit(db, actor_id=user.id, actor_role=user.role, action="RULE_ACTIVATED",
                entity_type="RULE", entity_id=rule_id,
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": r.id, "is_active": True},
            "meta": {"requestId": request.state.request_id}}


@router.post("/{rule_id}/deactivate")
async def deactivate_rule(rule_id: int, request: Request,
                          user: CurrentUser = Depends(require("manage:rules")),
                          db: AsyncSession = Depends(get_db)):
    r = await _get_rule(db, rule_id)
    r.is_active = False
    await audit(db, actor_id=user.id, actor_role=user.role, action="RULE_DEACTIVATED",
                entity_type="RULE", entity_id=rule_id,
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": r.id, "is_active": False},
            "meta": {"requestId": request.state.request_id}}


@router.get("/{rule_id}/versions")
async def rule_versions(rule_id: int, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    await _get_rule(db, rule_id)
    res = await db.execute(
        select(RuleVersion).where(RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc())
    )
    versions = res.scalars().all()
    return {"success": True, "data": [{
        "id": v.id, "version": v.version, "is_current": v.is_current,
        "config": v.config_json, "created_at": v.created_at.isoformat(),
    } for v in versions], "meta": {"requestId": "versions"}}