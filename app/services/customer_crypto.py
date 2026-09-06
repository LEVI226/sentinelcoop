"""Chiffrement des champs PII d'un client.

Chaque champ sensible est chiffré avec AES-256-GCM sur un domaine de clé dérivé
(HKDF) pour séparer la confidentialité par type de donnée. Les champs de
recherche disposent d'un blind index HMAC.
"""
from __future__ import annotations

from typing import Optional

from app.core import security
from app.models.customer import Customer

# Domaine de dérivation par champ (séparation de clés)
DOMAINS = {
    "first_name": "customer.first_name",
    "last_name": "customer.last_name",
    "date_of_birth": "customer.dob",
    "place_of_birth": "customer.pob",
    "nationality": "customer.nationality",
    "gender": "customer.gender",
    "phone": "customer.phone",
    "email": "customer.email",
    "address": "customer.address",
    "occupation": "customer.occupation",
    "employer": "customer.employer",
    "declared_income": "customer.income",
}


def _enc(name: str, value) -> Optional[str]:
    if value is None or value == "":
        return None
    return security.encrypt_field(str(value), DOMAINS[name])


def apply_encryption(cust: Customer, data: dict) -> None:
    """Chiffre les champs PII dans `data` et écrit les colonnes chiffrées + blind index."""
    for field, domain in DOMAINS.items():
        col = f"{field}_enc"
        if field in data:
            setattr(cust, col, _enc(field, data.get(field)))
    # Blind index pour recherche
    fn = data.get("first_name")
    ln = data.get("last_name")
    email = data.get("email")
    phone = data.get("phone")
    if ln:
        cust.blind_last_name = security.blind_index(str(ln))
    if fn:
        cust.blind_first_name = security.blind_index(str(fn))
    if email:
        cust.blind_email = security.blind_index(str(email))
    if phone:
        cust.blind_phone = security.blind_index(str(phone))


def decrypt_dict(cust: Customer) -> dict:
    """Déchiffre tous les champs PII du client pour la réponse API."""
    out = {
        "id": cust.id,
        "branch_id": cust.branch_id,
        "cooperative_id": cust.cooperative_id,
        "local_customer_id": cust.local_customer_id,
        "network_customer_id": cust.network_customer_id,
        "customer_type": cust.customer_type,
        "kyc_status": cust.kyc_status,
        "risk_level": cust.risk_level,
        "risk_score": cust.risk_score,
        "is_pep": cust.is_pep,
        "is_active": cust.is_active,
        "created_at": cust.created_at.isoformat() if cust.created_at else None,
        "updated_at": cust.updated_at.isoformat() if cust.updated_at else None,
    }
    for field, col in DOMAINS.items():
        token = getattr(cust, f"{field}_enc")
        out[field] = security.decrypt_field(token, DOMAINS[field]) if token else None
    return out
