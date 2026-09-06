"""Module DASHBOARD — CDC §30 (agrégats pour le frontend)."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.customer import Customer, CustomerRiskScore
from app.models.finance import Account, Transaction

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _branch_filter(user: CurrentUser, column):
    """Applique le filtre ABAC selon la caisse de l'utilisateur."""
    if not user.can_access_branch(None):
        return column == user.branch_id
    return None


async def _count(db, stmt):
    return (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()


@router.get("/summary")
async def summary(user: CurrentUser = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    cq = select(Customer).where(Customer.is_active.is_(True))
    aq = select(Alert)
    tq = select(Transaction)
    if not user.can_access_branch(None):
        cq = cq.where(Customer.branch_id == user.branch_id)
        aq = aq.where(Alert.branch_id == user.branch_id)
        tq = tq.where(Transaction.branch_id == user.branch_id)

    total_clients = await _count(db, cq)
    high_risk = await _count(db, cq.where(Customer.risk_level.in_(["HIGH", "CRITICAL"])))
    critical_open = await _count(db, aq.where(Alert.status.in_(
        ["NEW", "TO_REVIEW", "IN_PROGRESS", "PENDING"]), Alert.severity == "CRITICAL"))
    now = datetime.now()
    overdue = await _count(db, aq.where(Alert.status.in_(
        ["NEW", "TO_REVIEW", "IN_PROGRESS", "PENDING", "ESCALATED"]),
        Alert.due_at < now))
    to_review = await _count(db, aq.where(Alert.status == "NEW"))
    tx_pending = await _count(db, tq.where(Transaction.monitoring_status == "NOT_REVIEWED"))

    return {"success": True, "data": {
        "clientsControlled": total_clients,
        "highRiskClients": high_risk,
        "criticalOpenAlerts": critical_open,
        "overdueAlerts": overdue,
        "transactionsToReview": tx_pending,
    }, "meta": {"requestId": "summary"}}


@router.get("/risk-distribution")
async def risk_distribution(user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    q = select(Customer.risk_level, func.count()).group_by(Customer.risk_level)
    if not user.can_access_branch(None):
        q = q.where(Customer.branch_id == user.branch_id)
    rows = (await db.execute(q)).all()
    return {"success": True, "data": [{"level": lv, "count": n} for lv, n in rows],
            "meta": {"requestId": "risk-distribution"}}


@router.get("/alerts-trend")
async def alerts_trend(user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db),
                       days: int = 14):
    since = datetime.now() - timedelta(days=days)
    q = select(
        func.date(Alert.created_at).label("day"),
        func.count().label("n"),
    ).where(Alert.created_at >= since).group_by(func.date(Alert.created_at)).order_by("day")
    if not user.can_access_branch(None):
        q = q.where(Alert.branch_id == user.branch_id)
    rows = (await db.execute(q)).all()
    return {"success": True, "data": [{"date": str(day), "count": n} for day, n in rows],
            "meta": {"requestId": "alerts-trend"}}


@router.get("/priority-alerts")
async def priority_alerts(user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db),
                          limit: int = 10):
    q = select(Alert).where(Alert.status.in_(
        ["NEW", "TO_REVIEW", "IN_PROGRESS", "PENDING", "ESCALATED"]),
        Alert.severity == "CRITICAL").order_by(Alert.created_at.desc()).limit(limit)
    if not user.can_access_branch(None):
        q = q.where(Alert.branch_id == user.branch_id)
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": [{
        "id": a.id, "code": a.code, "title": a.title, "severity": a.severity,
        "status": a.status, "created_at": a.created_at.isoformat(),
        "due_at": a.due_at.isoformat() if a.due_at else None,
    } for a in rows], "meta": {"requestId": "priority-alerts"}}


@router.get("/transaction-summary")
async def transaction_summary(user: CurrentUser = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    q = select(Transaction.type, func.count(), func.sum(Transaction.amount)).group_by(Transaction.type)
    if not user.can_access_branch(None):
        q = q.where(Transaction.branch_id == user.branch_id)
    rows = (await db.execute(q)).all()
    total = sum(n for _, n, _ in rows)
    return {"success": True, "data": [{
        "type": t, "count": n, "sum": float(s or 0)
    } for t, n, s in rows], "meta": {"requestId": "transaction-summary", "total": total}}


@router.get("/compliance-summary")
async def compliance_summary(user: CurrentUser = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    """Synthèse conformité : KYC, screening, cas, déclarations."""
    from app.models.declaration import DeclarationSoupcon
    from app.models.alert import Case
    from app.models.screening import ScreeningMatch

    kyc_q = select(Customer.kyc_status, func.count()).group_by(Customer.kyc_status)
    match_q = select(ScreeningMatch.status, func.count()).group_by(ScreeningMatch.status)
    case_q = select(Case.status, func.count()).group_by(Case.status)
    decl_q = select(DeclarationSoupcon.statut, func.count()).group_by(DeclarationSoupcon.statut)

    if not user.can_access_branch(None):
        kyc_q = kyc_q.where(Customer.branch_id == user.branch_id)

    kyc = dict((await db.execute(kyc_q)).all())
    matches = dict((await db.execute(match_q)).all())
    cases = dict((await db.execute(case_q)).all())
    decls = dict((await db.execute(decl_q)).all())

    return {"success": True, "data": {
        "kyc": [{"status": k, "count": v} for k, v in kyc.items()],
        "screening_matches": [{"status": k, "count": v} for k, v in matches.items()],
        "cases": [{"status": k, "count": v} for k, v in cases.items()],
        "declarations": [{"status": k, "count": v} for k, v in decls.items()],
    }, "meta": {"requestId": "compliance-summary"}}