"""Sécurité "dernière génération" :

- Argon2id          : hachage des mots de passe (recommandation OWASP).
- AES-256-GCM       : chiffrement authentifié des champs sensibles (dossiers clients).
- HKDF-SHA256       : dérivation de sous-clés depuis la clé maîtresse (séparation de domaine).
- JWT (HS256)       : signature des tokens access + refresh, avec rotation.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import get_settings

settings = get_settings()

_ph = PasswordHasher()

# ---------------------------------------------------------------------------
# Clé maîtresse & dérivation HKDF (séparation de domaine)
# ---------------------------------------------------------------------------
_MASTER = bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)


def derive_key(domain: str, length: int = 32) -> bytes:
    """Dérive une sous-clé dédiée (ex: 'customer.pii', 'customer.phone') depuis la
    clé maîtresse via HKDF-SHA256. Un compromis sur une entité ne compromet pas les autres."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=domain.encode("utf-8"),
    )
    return hkdf.derive(_MASTER)


# ---------------------------------------------------------------------------
# Cipher AES-256-GCM
# ---------------------------------------------------------------------------
def _encrypt_gcm(plaintext: bytes, domain: str) -> str:
    key = derive_key(domain)
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    payload = nonce + ct
    return "v1:" + base64.urlsafe_b64encode(payload).decode("ascii")


def _decrypt_gcm(token: str, domain: str) -> bytes:
    if not token.startswith("v1:"):
        raise ValueError("Mauvais format de chiffrement")
    key = derive_key(domain)
    raw = base64.urlsafe_b64decode(token[3:])
    nonce, ct = raw[:12], raw[12:]
    return AESGCM(key).decrypt(nonce, ct, None)


def encrypt_field(value: str, domain: str) -> str:
    """Chiffre une valeur sensible (stockée en base)."""
    return _encrypt_gcm(value.encode("utf-8"), domain)


def decrypt_field(token: str, domain: str) -> str:
    return _decrypt_gcm(token, domain).decode("utf-8")


def encrypt_int(value: int, domain: str) -> str:
    return _encrypt_gcm(str(value).encode("utf-8"), domain)


def decrypt_int(token: str, domain: str) -> int:
    return int(_decrypt_gcm(token, domain).decode("utf-8"))


# ---------------------------------------------------------------------------
# Empreinte déterministe (HMAC) pour recherche sur champs chiffrés
# Permet de retrouver un client par son nom/email/phone sans déchiffrer toutes les lignes.
# ---------------------------------------------------------------------------
def blind_index(value: str, domain: str = "search") -> str:
    key = derive_key(domain + ".blind")
    return hmac.new(key, value.strip().lower().encode("utf-8"), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Mots de passe : Argon2id
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except (VerifyMismatchError, Exception):
        return False


# ---------------------------------------------------------------------------
# Tokens JWT (access + refresh)
# ---------------------------------------------------------------------------
import jwt as pyjwt  # noqa: E402


def _jwt_secret() -> bytes:
    return settings.JWT_SECRET.encode("utf-8")


def create_access_token(subject: str, user_id: int, role: str, branch_id: int | None,
                        coop_id: int | None, session_id: str, **kw) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "uid": user_id,
        "role": role,
        "branch_id": branch_id,
        "coop_id": coop_id,
        "sid": session_id,
        "type": "access",
        "iat": now,
        "exp": now + settings.JWT_EXPIRES_MINUTES * 60,
    }
    payload.update(kw)
    return pyjwt.encode(payload, _jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, user_id: int, session_id: str, jti: str | None = None) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "uid": user_id,
        "sid": session_id,
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": now + settings.REFRESH_EXPIRES_DAYS * 86400,
    }
    return pyjwt.encode(payload, _jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Décode et vérifie un JWT. Lève jwt.PyJWTError si invalide."""
    payload = pyjwt.decode(token, _jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise ValueError("Type de token invalide")
    return payload
