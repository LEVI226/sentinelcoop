"""ABAC : contrôle d'accès par attributs (CDC §8).

Règles de base :
- Un utilisateur voit uniquement les données de SA caisse (branch_id),
  sauf rôles réseau (conformité_reseau) et audit.
- Data classification : certaines données (PEP, notes d'investigation) sont
  réservées aux rôles conformité.
"""
from __future__ import annotations

from app.core.errors import AppError

# Rôles disposant d'une vision réseau étendue
NETWORK_ROLES = {"superadmin", "conformite_reseau"}
# Rôles à lecture seule
READ_ONLY_ROLES = {"auditeur"}
# Niveaux de sensibilité des types de données (CDC §43)
SENSITIVITY = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
}


def _role_set(user) -> set[str]:
    roles = getattr(user, "roles", [])
    out: set[str] = set()
    for r in roles:
        out.add(r.code if hasattr(r, "code") else str(r))
    return out


def can_access_branch(user, target_branch_id: int | None) -> bool:
    """Un utilisateur ne voit que les données de sa caisse, sauf rôles réseau."""
    roles = _role_set(user)
    if NETWORK_ROLES & roles:
        return True
    if user.branch_id is None or target_branch_id is None:
        return False
    return user.branch_id == target_branch_id


def require_branch_access(user, target_branch_id: int | None, single: bool = True) -> None:
    if single and not can_access_branch(user, target_branch_id):
        raise AppError("FORBIDDEN", "Données hors de votre périmètre d'accès", status=403)


def can_read_sensitive(user, sensitivity: str) -> bool:
    """Contrôle par niveau de sensibilité de la donnée."""
    roles = _role_set(user)
    need = SENSITIVITY.get(sensitivity, 0)
    if need <= 1:
        return True
    if need == 2 and ({"auditeur", "conformite_reseau", "superadmin", "analyste_conformite"} & roles):
        return True
    if need == 3 and ({"superadmin", "conformite_reseau"} & roles):
        return True
    return False


def is_read_only(user) -> bool:
    return bool(_role_set(user) & READ_ONLY_ROLES)
