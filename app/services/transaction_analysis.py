"""Analyse async d'une transaction : règles → risque → screening → alerte.

Simule la file de traitements (CDC §41). En production remplacer par une vraie
file (Celery/RQ/Redis) sans changer la logique d'orchestration.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertEvent
from app.models.finance import Transaction
from app.models.rule import Rule, RuleVersion, RuleAction, RuleExecution
from app.models.screening import ScreeningMatch, ScreeningRun
from app.services import rule_engine, screening_engine
from app.services.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


async def _run_rules(db: AsyncSession, txn: Transaction) -> list[dict]:
    """Exécute les règles actives sur la transaction et ses cousines récentes."""
    # Transactions récentes du même client (pour STRUCTURING/VELOCITY/FREQUENCY)
    res = await db.execute(
        select(Transaction).where(Transaction.customer_id == txn.customer_id)
        .order_by(Transaction.transaction_date.desc()).limit(50)
    )
    recent = res.scalars().all()
    txns_payload = [
        {"amount": t.amount, "transaction_date": t.transaction_date.isoformat()}
        for t in recent
    ]

    rules_res = await db.execute(select(Rule).where(Rule.is_active.is_(True)))
    rules = rules_res.scalars().all()
    hits = []
    for rule in rules:
        # version courante
        if not rule.current_version_id:
            continue
        ver = (await db.execute(select(RuleVersion).where(RuleVersion.id == rule.current_version_id))).scalar_one_or_none()
        if ver is None:
            continue
        outcome = rule_engine.run_rule(rule.rule_type, ver.config_json, txns_payload)
        exec_rec = RuleExecution(
            rule_version_id=ver.id, target_type="TRANSACTION", target_id=txn.id,
            matched=outcome["matched"],
            details_json=json.dumps(outcome, default=str),
        )
        db.add(exec_rec)
        if outcome["matched"]:
            actions = (await db.execute(
                select(RuleAction).where(RuleAction.rule_version_id == ver.id)
            )).scalars().all()
            hits.append({
                "rule": rule,
                "severity": actions[0].severity if actions else "MEDIUM",
                "priority": actions[0].priority if actions else "MEDIUM",
            })
    return hits


async def _screening(db: AsyncSession, txn: Transaction, counterparty_name: str | None):
    engine = screening_engine.ScreeningEngine(db)
    if counterparty_name:
        run = await engine.run_customer(subject_id=txn.id, full_name=counterparty_name,
                                        executed_by=None)
        run.subject_type = "TRANSACTION"
    return None


async def analyze_transaction(db: AsyncSession, txn: Transaction) -> None:
    """Analyse complète (mode différé). Appelé après la réponse HTTP."""
    hits = await _run_rules(db, txn)
    # Risque transaction
    re = RiskEngine()
    risk = re.transaction_score(
        amount_risk=min(100, int(txn.amount / 100000)),  # proportionnel au montant
        profile_deviation=60 if hits else 10,
        rule_hits=len(hits),
        customer_risk=30,
    )
    txn.risk_score = risk["score"]

    # Génération d'alertes pour chaque règle déclenchée
    for hit in hits:
        rule = hit["rule"]
        existing = await db.execute(
            select(Alert).where(Alert.rule_id == rule.id, Alert.transaction_id == txn.id,
                                Alert.customer_id == txn.customer_id)
        )
        if existing.scalar_one_or_none():
            continue
        alert = Alert(
            code=f"AL-{datetime.now().strftime('%Y%m%d')}-{txn.id:04d}-{rule.code}",
            title=f"{rule.name} — {txn.reference}",
            description=f"Règle {rule.code} déclenchée pour la transaction {txn.reference}",
            severity=hit["severity"],
            priority=hit["priority"],
            status="NEW",
            customer_id=txn.customer_id,
            transaction_id=txn.id,
            branch_id=txn.branch_id,
            source="RULE",
            rule_id=rule.id,
            due_at=datetime.now(),
        )
        db.add(alert)
        await db.flush()
        db.add(AlertEvent(alert_id=alert.id, event_type="CREATED",
                          payload=json.dumps({"rule": rule.code})))
    await db.flush()