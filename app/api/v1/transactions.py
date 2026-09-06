"""Module TRANSACTIONS — CDC §14.

POST   /api/v1/transactions      (enregistrement + analyse async)
GET    /api/v1/transactions      (liste paginée)
GET    /api/v1/transactions/:id
GET    /api/v1/transactions/:id   (détail)
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.customer import Customer
from app.models.finance import Transaction
from app.schemas.transaction import TransactionCreate
from app.services.audit_service import audit
from app.services.transaction_analysis import analyze_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def _check_customer(db: AsyncSession, customer_id: int, user: CurrentUser):
    res = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = res.scalar_one_or_none()
    if c is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client inexistant", status=404)
    if not user.can_access_branch(c.branch_id):
        raise AppError("FORBIDDEN", "Client hors périmètre", status=403)


@router.post("")
async def create_transaction(body: TransactionCreate, request: Request,
                             user: CurrentUser = Depends(require("create:transactions")),
                             db: AsyncSession = Depends(get_db)):
    await _check_customer(db, body.customer_id, user)
    # Unicité de référence
    dup = (await db.execute(select(Transaction).where(Transaction.reference == body.reference))).scalar_one_or_none()
    if dup:
        raise AppError("DUPLICATE_TRANSACTION", "Référence déjà utilisée", status=409)

    txn = Transaction(
        reference=body.reference,
        customer_id=body.customer_id,
        account_id=body.account_id,
        branch_id=body.branch_id,
        counterparty_id=body.counterparty_id,
        type=body.type,
        amount=body.amount,
        currency=body.currency,
        transaction_date=body.transaction_date,
        channel=body.channel,
        purpose=body.purpose,
        source_of_funds=body.source_of_funds,
        destination=body.destination,
        status="COMPLETED",
        monitoring_status="NOT_REVIEWED",
    )
    db.add(txn)
    await db.flush()

    await audit(db, actor_id=user.id, actor_role=user.role, action="TRANSACTION_CREATED",
                entity_type="TRANSACTION", entity_id=txn.id,
                new_value={"reference": txn.reference, "amount": txn.amount, "type": txn.type},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(txn)

    # Analyse asynchrone (CDC §41) — non bloquante
    task = asyncio.create_task(_run_analysis(txn.id))
    return {"success": True, "data": {
        "id": txn.id, "reference": txn.reference, "status": txn.status,
        "analysis_pending": True,
    }, "meta": {"requestId": request.state.request_id}}


async def _run_analysis(txn_id: int):
    """Lance l'analyse dans une session dédiée (après réponse HTTP)."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Transaction).where(Transaction.id == txn_id))
        txn = res.scalar_one_or_none()
        if txn is None:
            return
        try:
            await analyze_transaction(db, txn)
            await db.commit()
        except Exception:
            logger.exception("Analyse transaction %s échouée", txn_id)
            await db.rollback()


@router.get("")
async def list_transactions(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    customer_id: int | None = None,
    status: str | None = None,
    monitoring: str | None = None,
):
    q = select(Transaction)
    if not user.can_access_branch(None):
        q = q.where(Transaction.branch_id == user.branch_id)
    if customer_id:
        q = q.where(Transaction.customer_id == customer_id)
    if status:
        q = q.where(Transaction.status == status)
    if monitoring:
        q = q.where(Transaction.monitoring_status == monitoring)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(Transaction.transaction_date.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    data = [{
        "id": t.id, "reference": t.reference, "customer_id": t.customer_id,
        "account_id": t.account_id, "branch_id": t.branch_id,
        "type": t.type, "amount": t.amount, "currency": t.currency,
        "transaction_date": t.transaction_date.isoformat(), "channel": t.channel,
        "status": t.status, "monitoring_status": t.monitoring_status, "risk_score": t.risk_score,
    } for t in rows]
    return {"success": True, "data": data,
            "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    t = res.scalar_one_or_none()
    if t is None:
        raise AppError("TRANSACTION_NOT_FOUND", "Transaction introuvable", status=404)
    if not user.can_access_branch(t.branch_id):
        raise AppError("FORBIDDEN", "Transaction hors périmètre", status=403)
    return {"success": True, "data": {
        "id": t.id, "reference": t.reference, "customer_id": t.customer_id,
        "account_id": t.account_id, "branch_id": t.branch_id, "counterparty_id": t.counterparty_id,
        "type": t.type, "amount": t.amount, "currency": t.currency,
        "transaction_date": t.transaction_date.isoformat(), "channel": t.channel,
        "purpose": t.purpose, "source_of_funds": t.source_of_funds, "destination": t.destination,
        "status": t.status, "monitoring_status": t.monitoring_status, "risk_score": t.risk_score,
    }, "meta": {"requestId": "get"}}