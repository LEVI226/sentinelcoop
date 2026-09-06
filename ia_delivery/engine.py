"""Pure analysis: no network, database, posting or regulatory decisions."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinellecoop.matcher import similarite_nom
from sentinellecoop.phonetics import deplier, jaro_winkler

VERSION = "cif-ia-demo-1"
FEATURES = ["name_wape", "name_jaro", "dob_equal", "dob_conflict", "dob_missing"]


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)


def features(left, right):
    a, b = left.get("name", "").strip(), right.get("name", "").strip()
    if not a or not b or len(a) > 200 or len(b) > 200:
        raise ValueError("Names must contain 1..200 characters")
    da, db = left.get("birth_date"), right.get("birth_date")
    for d in (da, db):
        if d:
            datetime.strptime(d, "%Y-%m-%d")
    known = bool(da and db)
    return [similarite_nom(a, b), jaro_winkler(deplier(a), deplier(b)),
            float(known and da == db), float(known and da != db), float(not known)]


def load_model(path=None):
    path = Path(path) if path else Path(__file__).parent / "artifacts/model.json"
    model = json.loads(path.read_text(encoding="utf-8"))
    if model["feature_names"] != FEATURES or len(model["weights"]) != len(FEATURES):
        raise ValueError("Incompatible model schema")
    if not all(math.isfinite(float(v)) for v in [*model["weights"], model["bias"]]):
        raise ValueError("Invalid model coefficients")
    return model


def predict(x, model):
    z = model["bias"] + sum(a * b for a, b in zip(x, model["weights"]))
    return 1 / (1 + math.exp(-max(-40, min(40, z))))


def screen_customer(customer, snapshot, *, as_of, model=None):
    now = timestamp(as_of)
    if snapshot.get("synthetic") is not True:
        raise ValueError("Competition engine accepts synthetic snapshots only")
    entries = snapshot["entities"]
    if len(entries) > 5000:
        raise ValueError("Demo reference limit exceeded")
    if timestamp(snapshot["issued_at"]) > now or now >= timestamp(snapshot["expires_at"]):
        return {"status": "INCOMPLETE", "reason_codes": ["REFERENCE_NOT_CURRENT"],
                "reference_version": snapshot["version"], "candidates": []}
    features(customer, customer)  # validate even if the reference is empty
    model = model or load_model()
    candidates = []
    for entry in entries:
        if entry["category"] not in ("PEP", "SANCTION"):
            raise ValueError("Unknown reference category")
        names = [entry["name"], *entry.get("aliases", [])]
        if len(names) > 30:
            raise ValueError("Too many aliases")
        compared = [(name, features(customer, {**entry, "name": name})) for name in names]
        alias, x = max(compared, key=lambda item: predict(item[1], model))
        # Broad name-based retrieval remains visible even if ML downranks a pair.
        if max(x[:2]) < 0.65:
            continue
        score = predict(x, model)
        reasons = ["NAME_CANDIDATE"]
        if x[2]: reasons.append("BIRTH_DATE_AGREEMENT")
        if x[3]: reasons.append("BIRTH_DATE_CONFLICT")
        if x[4]: reasons.append("BIRTH_DATE_MISSING")
        candidates.append({"entity_id": entry["entity_id"], "category": entry["category"],
                           "matched_alias": alias, "match_score": round(score * 100, 2),
                           "score_kind": "UNCALIBRATED_SYNTHETIC_MODEL_SCORE",
                           "reason_codes": reasons, "identity_resolution": "UNCONFIRMED",
                           "recommended_action": "IDENTITY_REVIEW",
                           "above_model_threshold": score >= model["threshold"]})
    candidates.sort(key=lambda c: (-c["match_score"], c["entity_id"]))
    return {"status": "COMPLETE", "customer_id": customer["customer_id"],
            "reference_version": snapshot["version"], "model_version": model["version"],
            "engine_version": VERSION, "as_of": as_of, "candidates": candidates,
            "operational_decision": "NOT_TAKEN_BY_ENGINE"}


def analyze_transaction(transaction, history, *, as_of, history_complete, policy):
    """History is the effective canonical view: reversals resolved upstream.

    Current transaction is counted once. Inputs are scoped to one customer,
    institution and currency. Returned findings do not post or block payments.
    """
    now = timestamp(as_of)
    threshold = policy["aggregate_threshold_minor"]
    if type(threshold) is not int or threshold <= 0:
        raise ValueError("Positive integer threshold required")
    duration = policy.get("window_hours", 48)
    if type(duration) is not int or not 1 <= duration <= 720:
        raise ValueError("Window must be 1..720 hours")
    rows = {}
    for tx in [*history, transaction]:
        for field in ("institution_id", "customer_id", "currency"):
            if tx[field] != transaction[field]:
                raise ValueError("Mixed scope or currency")
        if type(tx["amount_minor"]) is not int or tx["amount_minor"] <= 0:
            raise ValueError("Positive integer amount required")
        if tx["direction"] not in ("IN", "OUT"):
            raise ValueError("Direction must be IN or OUT")
        if not tx["transaction_id"]:
            raise ValueError("Missing transaction ID")
        timestamp(tx["occurred_at"])
        timestamp(tx["received_at"])
        old = rows.get(tx["transaction_id"])
        if old is not None and old != tx:
            raise ValueError("Conflicting duplicate transaction")
        rows[tx["transaction_id"]] = tx
    if timestamp(transaction["occurred_at"]) > now or timestamp(transaction["received_at"]) > now:
        raise ValueError("Current transaction is not available at as_of")
    recent = sorted((t for t in rows.values()
                     if now - timedelta(hours=duration) < timestamp(t["occurred_at"]) <= now
                     and timestamp(t["received_at"]) <= now),
                    key=lambda t: (t["occurred_at"], t["transaction_id"]))
    findings = []

    def finding(rule, evidence, score, explanation):
        ids = sorted(t["transaction_id"] for t in evidence)
        key = json.dumps([transaction["institution_id"], transaction["customer_id"], rule,
                          policy["version"], ids], separators=(",", ":"))
        return {"finding_id": hashlib.sha256(key.encode()).hexdigest()[:24],
                "customer_id": transaction["customer_id"], "rule_id": rule,
                "priority_score": score, "match_score": None,
                "score_kind": "HEURISTIC_TRIAGE", "proposed_risk": "HIGH",
                "explanation": explanation, "evidence_transaction_ids": ids,
                "transactions": evidence, "policy_version": policy["version"],
                "recommended_action": "ANALYST_REVIEW", "synthetic_demo": True}

    for direction in ("IN", "OUT"):
        fragments = [t for t in recent if t["direction"] == direction and t["amount_minor"] < threshold]
        if len(fragments) >= 3 and sum(t["amount_minor"] for t in fragments) >= threshold:
            findings.append(finding("FRAGMENTATION_" + direction, fragments, 70,
                                    "Au moins trois mouvements de même sens sous le seuil illustratif dépassent ensemble ce seuil."))
    # Pairwise rapid movement indicator, not fungible-money tracing or a U-turn.
    pairs = [(a, b) for a in recent for b in recent
             if a["direction"] == "IN" and b["direction"] == "OUT"
             and timedelta(0) < timestamp(b["occurred_at"]) - timestamp(a["occurred_at"]) <= timedelta(hours=1)
             and a["amount_minor"] * 0.8 <= b["amount_minor"] <= a["amount_minor"] * 1.2]
    if pairs:
        a, b = pairs[0]
        findings.append(finding("RAPID_IN_OUT", [a, b], 65,
                                "Entrée et sortie de montants proches en moins d'une heure ; contexte économique à examiner."))
    return {"status": "COMPLETE" if history_complete else "PARTIAL",
            "coverage": "CUSTOMER_LOCAL", "engine_version": VERSION,
            "as_of": as_of, "findings": findings,
            "reason_codes": [] if history_complete else ["HISTORY_INCOMPLETE"],
            "operational_decision": "NOT_TAKEN_BY_ENGINE"}
