"""Module CLIENTS — CDC §10.

GET    /api/v1/customers                 (paginé, filtres)
POST   /api/v1/customers                 (création + chiffrement PII)
GET    /api/v1/customers/:id
PATCH  /api/v1/customers/:id
GET    /api/v1/customers/:id/risk
GET    /api/v1/customers/:id/accounts
GET    /api/v1/customers/:id/transactions
GET    /api/v1/customers/:id/alerts
GET    /api/v1/customers/:id/cases
GET    /api/v1/customers/:id/history
POST   /api/v1/customers/:id/screen
POST   /api/v1/customers/:id/review
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.abac import can_access_branch, can_read_sensitive
from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.alert import Alert, Case, CaseAlert
from app.models.customer import Customer, CustomerRiskScore
from app.models.finance import Account, Transaction
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerReview
from app.schemas.transaction import TransactionCreate
from app.services import customer_crypto
from app.services.audit_service import audit
from app.services.risk_engine import risk_engine
from app.services.screening_engine import ScreeningEngine

router = APIRouter(prefix="/customers", tags=["customers"])


async def _get_customer(db: AsyncSession, customer_id: int, user: CurrentUser) -> Customer:
    res = await db.execute(select(Customer).where(Customer.id == customer_id))
    cust = res.scalar_one_or_none()
    if cust is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client introuvable", status=404)
    if not user.can_access_branch(cust.branch_id):
        raise AppError("FORBIDDEN", "Client hors de votre périmètre", status=403)
    return cust


@router.get("")
async def list_customers(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    risk_level: str | None = None,
):
    q = select(Customer)
    if not user.can_access_branch(None):
        q = q.where(Customer.branch_id == user.branch_id)
    if search:
        idx = security.blind_index(search)
        q = q.where(or_(Customer.blind_last_name == idx,
                        Customer.blind_first_name == idx,
                        Customer.blind_email == idx,
                        Customer.blind_phone == idx,
                        Customer.local_customer_id.ilike(f"%{search}%"),
                        Customer.network_customer_id.ilike(f"%{search}%")))
    if risk_level:
        q = q.where(Customer.risk_level == risk_level)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    q = q.order_by(Customer.id).offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    data = [customer_crypto.decrypt_dict(c) for c in rows]
    return {
        "success": True,
        "data": data,
        "meta": {"page": page, "limit": limit, "total": total,
                 "requestId": "list" if hasattr(user, "session_id") else "list"},
    }


@router.post("")
async def create_customer(body: CustomerCreate, request: Request,
                          user: CurrentUser = Depends(require("create:customers")),
                          db: AsyncSession = Depends(get_db)):
    if not user.can_access_branch(body.branch_id):
        raise AppError("FORBIDDEN", "Caisse hors de votre périmètre", status=403)

    # Vérifier unicité par blind index (email/phone)
    if body.email:
        idx = security.blind_index(body.email)
        dup = (await db.execute(select(Customer).where(Customer.blind_email == idx))).scalar_one_or_none()
        if dup:
            raise AppError("DUPLICATE_EMAIL", "Un client avec cet email existe déjà", status=409)

    cust = Customer(
        branch_id=body.branch_id,
        cooperative_id=user.cooperative_id,
        local_customer_id=f"LOC-{body.branch_id}-{await _next_local(db, body.branch_id)}",
        customer_type=body.customer_type,
        kyc_status="PENDING",
        is_active=True,
    )
    data = body.model_dump()
    customer_crypto.apply_encryption(cust, data)
    db.add(cust)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="CUSTOMER_CREATED",
                entity_type="CUSTOMER", entity_id=cust.id,
                new_value={"local_customer_id": cust.local_customer_id},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(cust)
    return {"success": True, "data": customer_crypto.decrypt_dict(cust),
            "meta": {"requestId": request.state.request_id}}


async def _next_local(db: AsyncSession, branch_id: int) -> int:
    res = await db.execute(
        select(func.count()).select_from(Customer).where(Customer.branch_id == branch_id)
    )
    return res.scalar() + 1


@router.get("/{customer_id}")
async def get_customer(customer_id: int, user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    cust = await _get_customer(db, customer_id, user)
    data = customer_crypto.decrypt_dict(cust)
    # masquer les données sensibles pour certains rôles
    if not can_read_sensitive(user, "confidential"):
        for k in ["email", "phone", "address"]:
            data.pop(k, None)
    return {"success": True, "data": data, "meta": {"requestId": "get"}}


@router.patch("/{customer_id}")
async def update_customer(customer_id: int, body: CustomerUpdate, request: Request,
                          user: CurrentUser = Depends(require("update:customers")),
                          db: AsyncSession = Depends(get_db)):
    cust = await _get_customer(db, customer_id, user)
    data = body.model_dump(exclude_unset=True)
    # Mise à jour des champs chiffrés uniquement
    sensitive = ["first_name", "last_name", "phone", "email", "address", "occupation", "employer", "declared_income"]
    upd = {k: v for k, v in data.items() if k in sensitive and v is not None}
    if upd:
        customer_crypto.apply_encryption(cust, upd)
    if "is_active" in data:
        cust.is_active = bool(data["is_active"])
    await audit(db, actor_id=user.id, actor_role=user.role, action="CUSTOMER_UPDATED",
                entity_type="CUSTOMER", entity_id=cust.id,
                old_value={}, new_value={"fields": list(upd.keys())},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(cust)
    return {"success": True, "data": customer_crypto.decrypt_dict(cust),
            "meta": {"requestId": request.state.request_id}}


@router.get("/{customer_id}/risk")
async def customer_risk(customer_id: int, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    cust = await _get_customer(db, customer_id, user)
    res = await db.execute(
        select(CustomerRiskScore).where(CustomerRiskScore.customer_id == customer_id)
        .order_by(CustomerRiskScore.computed_at.desc())
    )
    scores = res.scalars().all()
    if not scores:
        raise AppError("NO_RISK_SCORE", "Aucun score calculé", status=404)
    latest = scores[0]
    return {
        "success": True,
        "data": {
            "customer_id": customer_id,
            "score": cust.risk_score,
            "level": cust.risk_level,
            "factors": latest.factors_json if latest.factors_json else "[]",
            "history": [{"score": s.score, "level": s.level, "at": s.computed_at.isoformat()} for s in scores],
            "explanation": risk_engine.explain({"factors": __import__("json").loads(latest.factors_json or "[]"),
                                                "score": cust.risk_score, "level": cust.risk_level}),
        },
        "meta": {"requestId": "risk"},
    }


@router.get("/{customer_id}/accounts")
async def customer_accounts(customer_id: int, user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    cust = await _get_customer(db, customer_id, user)
    res = await db.execute(select(Account).where(Account.customer_id == customer_id))
    accounts = res.scalars().all()
    return {"success": True, "data": [{
        "id": a.id, "account_number": a.account_number, "account_type": a.account_type,
        "currency": a.currency, "status": a.status, "balance": a.balance,
        "branch_id": a.branch_id, "opened_at": a.opened_at.isoformat() if a.opened_at else None,
    } for a in accounts], "meta": {"requestId": "accounts"}}


@router.get("/{customer_id}/transactions")
async def customer_transactions(customer_id: int, user: CurrentUser = Depends(get_current_user),
                                db: AsyncSession = Depends(get_db),
                                page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    cust = await _get_customer(db, customer_id, user)
    q = select(Transaction).where(
        or_(Transaction.customer_id == customer_id, Transaction.counterparty_id == customer_id)
    ).order_by(Transaction.transaction_date.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page-1)*limit).limit(limit))).scalars().all()
    data = [{
        "id": t.id, "reference": t.reference, "type": t.type, "amount": t.amount,
        "currency": t.currency, "transaction_date": t.transaction_date.isoformat(),
        "channel": t.channel, "status": t.status, "monitoring_status": t.monitoring_status,
        "risk_score": t.risk_score, "branch_id": t.branch_id, "source_of_funds": t.source_of_funds,
    } for t in rows]
    return {"success": True, "data": data, "meta": {"page": page, "limit": limit, "total": total,
                                                    "requestId": "txns"}}


@router.get("/{customer_id}/alerts")
async def customer_alerts(customer_id: int, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    await _get_customer(db, customer_id, user)
    res = await db.execute(select(Alert).where(Alert.customer_id == customer_id).order_by(Alert.created_at.desc()))
    alerts = res.scalars().all()
    return {"success": True, "data": [{
        "id": a.id, "code": a.code, "title": a.title, "severity": a.severity,
        "priority": a.priority, "status": a.status, "source": a.source,
        "created_at": a.created_at.isoformat(), "due_at": a.due_at.isoformat() if a.due_at else None,
    } for a in alerts], "meta": {"requestId": "alerts"}}


@router.get("/{customer_id}/cases")
async def customer_cases(customer_id: int, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    await _get_customer(db, customer_id, user)
    res = await db.execute(select(Case).where(Case.customer_id == customer_id).order_by(Case.created_at.desc()))
    cases = res.scalars().all()
    return {"success": True, "data": [{
        "id": c.id, "code": c.code, "title": c.title, "status": c.status,
        "risk_level": c.risk_level, "created_at": c.created_at.isoformat(),
    } for c in cases], "meta": {"requestId": "cases"}}


@router.get("/{customer_id}/history")
async def customer_history(customer_id: int, user: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    await _get_customer(db, customer_id, user)
    from app.models.extra import AuditLog
    res = await db.execute(
        select(AuditLog).where(AuditLog.entity_type == "CUSTOMER", AuditLog.entity_id == customer_id)
        .order_by(AuditLog.timestamp.desc())
    )
    events = res.scalars().all()
    return {"success": True, "data": [{
        "action": e.action, "actor_id": e.actor_id, "at": e.timestamp.isoformat(),
        "reason": e.reason, "new_value": e.new_value,
    } for e in events], "meta": {"requestId": "history"}}


@router.post("/{customer_id}/screen")
async def screen_customer(customer_id: int, request: Request,
                          user: CurrentUser = Depends(require("read:screening")),
                          db: AsyncSession = Depends(get_db)):
    cust = await _get_customer(db, customer_id, user)
    engine = ScreeningEngine(db)
    name = security.decrypt_field(cust.last_name_enc, "customer.last_name") if cust.last_name_enc else ""
    first = security.decrypt_field(cust.first_name_enc, "customer.first_name") if cust.first_name_enc else ""
    full_name = f"{first} {name}".strip()
    run = await engine.run_customer(subject_id=customer_id, full_name=full_name, executed_by=user.id)
    # Récupérer les matchs
    from app.models.screening import ScreeningMatch
    res = await db.execute(
        select(ScreeningMatch).where(ScreeningMatch.run_id == run.id).order_by(ScreeningMatch.score.desc())
    )
    matches = res.scalars().all()
    await audit(db, actor_id=user.id, actor_role=user.role, action="SCREENING_EXECUTED",
                entity_type="CUSTOMER", entity_id=customer_id,
                new_value={"run_id": run.id, "matches": len(matches)},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {
        "run_id": run.id,
        "matches": [{
            "id": m.id, "entity_id": m.entity_id, "list_version_id": m.list_version_id,
            "score": m.score, "match_type": m.match_type, "status": m.status,
        } for m in matches],
    }, "meta": {"requestId": request.state.request_id}}


@router.post("/{customer_id}/review")
async def review_customer(customer_id: int, body: CustomerReview, request: Request,
                          user: CurrentUser = Depends(require("manage:kyc")),
                          db: AsyncSession = Depends(get_db)):
    cust = await _get_customer(db, customer_id, user)
    old = cust.kyc_status
    cust.kyc_status = body.status
    await audit(db, actor_id=user.id, actor_role=user.role, action="KYC_REVIEWED",
                entity_type="CUSTOMER", entity_id=customer_id,
                old_value={"kyc_status": old}, new_value={"kyc_status": body.status, "comment": body.comment},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(cust)
    return {"success": True, "data": {"id": cust.id, "kyc_status": cust.kyc_status},
            "meta": {"requestId": request.state.request_id}}