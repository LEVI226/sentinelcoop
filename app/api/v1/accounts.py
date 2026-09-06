"""Module COMPTES — CDC §13."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.customer import Customer
from app.models.finance import Account, Transaction
from app.services.audit_service import audit

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountCreate(BaseModel):
    account_number: str = Field(min_length=3, max_length=50)
    customer_id: int
    branch_id: int
    account_type: str = "SAVINGS"
    currency: str = "XOF"


@router.get("")
async def list_accounts(user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db),
                        page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                        customer_id: int | None = None,
                        status: str | None = None):
    q = select(Account)
    if not user.can_access_branch(None):
        q = q.where(Account.branch_id == user.branch_id)
    if customer_id:
        q = q.where(Account.customer_id == customer_id)
    if status:
        q = q.where(Account.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(Account.id).offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [{
        "id": a.id, "account_number": a.account_number, "customer_id": a.customer_id,
        "branch_id": a.branch_id, "account_type": a.account_type, "currency": a.currency,
        "status": a.status, "balance": a.balance,
        "opened_at": a.opened_at.isoformat() if a.opened_at else None,
    } for a in rows], "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.post("")
async def create_account(body: AccountCreate, request: Request,
                         user: CurrentUser = Depends(require("create:accounts")),
                         db: AsyncSession = Depends(get_db)):
    cust = (await db.execute(select(Customer).where(Customer.id == body.customer_id))).scalar_one_or_none()
    if cust is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client inexistant", status=404)
    if not user.can_access_branch(cust.branch_id):
        raise AppError("FORBIDDEN", "Client hors périmètre", status=403)
    a = Account(
        account_number=body.account_number, customer_id=body.customer_id,
        branch_id=body.branch_id, account_type=body.account_type, currency=body.currency,
    )
    db.add(a)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="ACCOUNT_CREATED",
                entity_type="ACCOUNT", entity_id=a.id,
                new_value={"account_number": a.account_number},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(a)
    return {"success": True, "data": {"id": a.id, "account_number": a.account_number},
            "meta": {"requestId": request.state.request_id}}


@router.get("/{account_id}")
async def get_account(account_id: int, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Account).where(Account.id == account_id))
    a = res.scalar_one_or_none()
    if a is None:
        raise AppError("ACCOUNT_NOT_FOUND", "Compte introuvable", status=404)
    if not user.can_access_branch(a.branch_id):
        raise AppError("FORBIDDEN", "Compte hors périmètre", status=403)
    txns = (await db.execute(
        select(Transaction).where(Transaction.account_id == account_id)
        .order_by(Transaction.transaction_date.desc()).limit(20))).scalars().all()
    return {"success": True, "data": {
        "id": a.id, "account_number": a.account_number, "customer_id": a.customer_id,
        "branch_id": a.branch_id, "account_type": a.account_type, "currency": a.currency,
        "status": a.status, "balance": a.balance,
        "recent_transactions": [{"id": t.id, "reference": t.reference, "type": t.type,
                                 "amount": t.amount, "date": t.transaction_date.isoformat()}
                                for t in txns],
    }, "meta": {"requestId": "get"}}


@router.patch("/{account_id}")
async def update_account(account_id: int, request: Request,
                         user: CurrentUser = Depends(require("update:accounts")),
                         db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Account).where(Account.id == account_id))
    a = res.scalar_one_or_none()
    if a is None:
        raise AppError("ACCOUNT_NOT_FOUND", "Compte introuvable", status=404)
    body = await request.json()
    if "status" in body:
        a.status = body["status"]
        if body["status"] == "CLOSED":
            a.closed_at = datetime.now()
    if "balance" in body:
        a.balance = float(body["balance"])
    await audit(db, actor_id=user.id, actor_role=user.role, action="ACCOUNT_UPDATED",
                entity_type="ACCOUNT", entity_id=account_id,
                new_value=body, request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": a.id, "status": a.status},
            "meta": {"requestId": request.state.request_id}}


@router.get("/{account_id}/transactions")
async def account_transactions(account_id: int, user: CurrentUser = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db),
                               page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    res = await db.execute(select(Account).where(Account.id == account_id))
    a = res.scalar_one_or_none()
    if a is None:
        raise AppError("ACCOUNT_NOT_FOUND", "Compte introuvable", status=404)
    if not user.can_access_branch(a.branch_id):
        raise AppError("FORBIDDEN", "Compte hors périmètre", status=403)
    q = select(Transaction).where(Transaction.account_id == account_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(Transaction.transaction_date.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [{
        "id": t.id, "reference": t.reference, "type": t.type, "amount": t.amount,
        "transaction_date": t.transaction_date.isoformat(), "status": t.status,
        "risk_score": t.risk_score,
    } for t in rows], "meta": {"page": page, "limit": limit, "total": total, "requestId": "txns"}}