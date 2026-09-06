"""Moteur de risque — scores explicables (CDC §18-20).

Le score est un entier 0-100 décomposé en facteurs pondérés. Chaque facteur
(code + weight) est conservé pour permettre l'explicabilité.
"""
from __future__ import annotations

import json

from app.config import get_settings

settings = get_settings()


def assign_level(score: int) -> tuple[str, list]:
    """Retourne (level, bands). Bands = [(name, lo, hi)]. CDC §19."""
    bands = settings.risk_bands
    level = "LOW"
    for name, lo, hi in bands:
        if lo <= score <= hi:
            level = name
            break
    if score > 100:
        level = "CRITICAL"
    return level, bands


def _clamp(score: int) -> int:
    return max(0, min(100, score))


class RiskEngine:
    """Calcule les 4 niveaux de score (client, transaction, réseau, caisse)."""

    def customer_score(self, *, kyc_risk: int = 0, pep_risk: int = 0,
                       profile_risk: int = 0, behavior_risk: int = 0,
                       network_risk: int = 0, local_risk: int = 0) -> dict:
        # Pondérations (représentatives, explicables)
        components = {
            "KYC_RISK": (kyc_risk, 0.20),
            "PEP_RISK": (pep_risk, 0.15),
            "PROFILE_DEVIATION": (profile_risk, 0.20),
            "BEHAVIOR": (behavior_risk, 0.20),
            "NETWORK_ACTIVITY": (network_risk, 0.15),
            "HIGH_RISK_BRANCH": (local_risk, 0.10),
        }
        return self._aggregate("CUSTOMER", components)

    def transaction_score(self, *, amount_risk: int = 0, frequency_risk: int = 0,
                          velocity_risk: int = 0, destination_risk: int = 0,
                          counterparty_risk: int = 0, profile_deviation: int = 0,
                          rule_hits: int = 0, customer_risk: int = 0) -> dict:
        components = {
            "AMOUNT": (amount_risk, 0.20),
            "FREQUENCY_VELOCITY": (max(frequency_risk, velocity_risk), 0.20),
            "DESTINATION": (destination_risk, 0.10),
            "COUNTERPARTY": (counterparty_risk, 0.15),
            "PROFILE_DEVIATION": (profile_deviation, 0.20),
            "RULE_HITS": (min(100, rule_hits * 40), 0.15),
        }
        return self._aggregate("TRANSACTION", components)

    def network_score(self, *, linked_accounts: int = 0, branch_count: int = 0,
                      alerts: int = 0, concentration: int = 0) -> dict:
        components = {
            "LINKED_ACCOUNTS": (min(100, linked_accounts * 15), 0.30),
            "MULTI_BRANCH": (min(100, branch_count * 30), 0.25),
            "ALERT_PRESSURE": (min(100, alerts * 20), 0.25),
            "CONCENTRATION": (concentration, 0.20),
        }
        return self._aggregate("NETWORK", components)

    def branch_score(self, *, cash_exposure: int = 0, volume: int = 0,
                     historical_alerts: int = 0, connectivity: int = 0,
                     local_context: int = 0) -> dict:
        components = {
            "CASH_EXPOSURE": (cash_exposure, 0.25),
            "TRANSACTION_VOLUME": (min(100, volume), 0.20),
            "HISTORICAL_ALERTS": (min(100, historical_alerts * 15), 0.20),
            "CONNECTIVITY": (connectivity, 0.15),
            "LOCAL_CONTEXT": (local_context, 0.20),
        }
        return self._aggregate("BRANCH", components)

    def _aggregate(self, subject: str, components: dict) -> dict:
        total = 0.0
        factors = []
        # Le facteur poids doit refléter la contribution du composant au score final
        for code, (value, weight) in components.items():
            contribution = _clamp(value) * weight
            total += contribution
            factors.append({"code": code, "weight": round(contribution)})
        # Normalisation pour atteindre l'échelle 0-100
        weights_sum = sum(w for _, w in components.values())
        if weights_sum:
            total = total / weights_sum
        score = _clamp(int(round(total)))
        level, bands = assign_level(score)
        # Trier les facteurs par contribution décroissante (explicabilité)
        factors.sort(key=lambda f: f["weight"], reverse=True)
        return {
            "subject": subject,
            "score": score,
            "level": level,
            "factors": factors,
            "bands": bands,
        }

    def explain(self, result: dict) -> str:
        """Phrase d'explication pour le frontend (CDC §20)."""
        top = result["factors"][0] if result["factors"] else None
        if top:
            return (f"Le score {result['level']} ({result['score']}/100) est principalement "
                    f"attribuable au facteur {top['code']} (contribution {top['weight']}).")
        return "Score neutre, aucun facteur significatif."


risk_engine = RiskEngine()


async def recompute_customer_risk(db, customer_id: int) -> dict:
    """Re-calcule le score de risque d'un client et le persiste (nouvelle entrée d'historique).

    Utilisé lors des mises à jour KYC / screening pour maintenir l'explicabilité.
    """
    from app.models.customer import Customer, CustomerRiskScore

    res = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    cust = res.scalar_one_or_none()
    if cust is None:
        raise ValueError(f"client {customer_id} introuvable")

    kyc_risk = 0 if cust.kyc_status == "VERIFIED" else (60 if cust.kyc_status == "UNDER_REVIEW" else 35)
    pep_risk = 80 if cust.is_pep else 0
    profile_risk = 40 if cust.declared_income_enc else 0

    result = risk_engine.customer_score(
        kyc_risk=kyc_risk, pep_risk=pep_risk, profile_risk=profile_risk,
    )
    db.add(CustomerRiskScore(
        customer_id=customer_id, score=result["score"], level=result["level"],
        factors_json=json.dumps(result["factors"]),
    ))
    cust.risk_score = result["score"]
    cust.risk_level = result["level"]
    await db.flush()
    return result


from sqlalchemy import select  # noqa: E402
