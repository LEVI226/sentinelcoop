"""
Upsert idempotent par UUID : chaque fonction crée l'enregistrement s'il
n'existe pas, ou le met à jour sinon. C'est ce mécanisme qui garantit
qu'un lot de synchronisation rejoué (après une coupure réseau en plein
envoi) ne produit jamais de doublon côté central.
"""
import datetime as dt
from sqlalchemy.orm import Session
from . import models


def upsert_client(db: Session, uuid: str, agency_id: str, payload: dict):
    obj = db.get(models.Client, uuid)
    if obj is None:
        obj = models.Client(id=uuid, agency_id=agency_id)
        db.add(obj)
    obj.full_name = payload.get("full_name", obj.full_name or "")
    obj.birth_date = payload.get("birth_date")
    obj.id_document = payload.get("id_document")
    obj.updated_at = dt.datetime.utcnow()
    return obj


def upsert_transaction(db: Session, uuid: str, agency_id: str, payload: dict):
    obj = db.get(models.Transaction, uuid)
    if obj is None:
        obj = models.Transaction(id=uuid, agency_id=agency_id)
        db.add(obj)
    obj.client_id = payload.get("client_id")
    obj.amount = payload.get("amount", 0.0)
    obj.currency = payload.get("currency", "XOF")
    obj.tx_type = payload.get("tx_type", "deposit")
    return obj


def upsert_alert(db: Session, uuid: str, agency_id: str, payload: dict):
    obj = db.get(models.Alert, uuid)
    if obj is None:
        obj = models.Alert(id=uuid, agency_id=agency_id)
        db.add(obj)
    obj.client_id = payload.get("client_id")
    obj.transaction_id = payload.get("transaction_id")
    obj.matched_name = payload.get("matched_name")
    obj.match_score = payload.get("match_score", 0.0)
    obj.severity = payload.get("severity", "informative")
    obj.decision = payload.get("decision", obj.decision or "pending")
    return obj


UPSERTERS = {
    "client": upsert_client,
    "transaction": upsert_transaction,
    "alert": upsert_alert,
}
