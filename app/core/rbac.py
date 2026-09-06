"""Registre central des permissions et aide RBAC (CDC §8)."""
from __future__ import annotations

# permission conventionnelle : <action>:<module> ex: "read:customers"
PERMISSIONS: dict[str, str] = {
    # Auth / users
    "read:users": "Consulter les utilisateurs",
    "create:users": "Créer un utilisateur",
    "update:users": "Modifier un utilisateur",
    "delete:users": "Supprimer un utilisateur",
    "manage:roles": "Gérer les rôles et permissions",
    # Coopératives / caisses
    "read:cooperatives": "Consulter les coopératives",
    "manage:cooperatives": "Gérer les coopératives",
    "read:branches": "Consulter les caisses",
    "manage:branches": "Gérer les caisses",
    "manage:riskprofiles": "Gérer les profils de risque de caisse",
    # Clients / KYC
    "read:customers": "Consulter les clients",
    "create:customers": "Créer un client",
    "update:customers": "Modifier un client",
    "manage:kyc": "Gérer le KYC",
    # Comptes / transactions
    "read:accounts": "Consulter les comptes",
    "create:accounts": "Créer un compte",
    "update:accounts": "Modifier un compte",
    "read:transactions": "Consulter les transactions",
    "create:transactions": "Enregistrer une transaction",
    "manage:transactions": "Gérer les transactions",
    # Conformité
    "read:alerts": "Consulter les alertes",
    "manage:alerts": "Gérer les alertes",
    "read:cases": "Consulter les dossiers",
    "manage:cases": "Gérer les dossiers",
    "manage:rules": "Gérer les règles",
    "manage:screening": "Gérer le screening",
    "read:screening": "Consulter le screening",
    "manage:risk": "Gérer le moteur de risque",
    "read:risk": "Consulter les scores de risque",
    "read:network": "Consulter le risque réseau",
    "read:reports": "Consulter les rapports",
    "generate:reports": "Générer les rapports",
    "read:audit": "Consulter les journaux d'audit",
    "read:notifications": "Consulter les notifications",
    "manage:sync": "Gérer la synchronisation",
    "manage:settings": "Gérer les paramètres système",
}

# Rôles système (CDC §5)
SYSTEM_ROLES: dict[str, list[str]] = {
    "superadmin": list(PERMISSIONS.keys()),
    "admin": [
        "read:users", "create:users", "update:users",
        "manage:roles", "read:cooperatives", "manage:cooperatives",
        "read:branches", "manage:branches", "manage:riskprofiles",
        "read:customers", "read:alerts", "read:cases", "read:reports",
        "generate:reports", "read:audit", "manage:settings", "manage:sync",
        "read:transactions", "read:accounts", "read:risk",
    ],
    "conformite_reseau": [
        "read:customers", "read:accounts", "read:transactions",
        "read:alerts", "manage:alerts", "read:cases", "manage:cases",
        "manage:rules", "manage:screening", "read:screening",
        "manage:risk", "read:risk", "read:network",
        "read:reports", "generate:reports", "read:audit",
        "read:cooperatives", "read:branches",
    ],
    "analyste_conformite": [
        "read:customers", "read:accounts", "read:transactions",
        "read:alerts", "manage:alerts", "read:cases", "manage:cases",
        "read:screening", "read:risk", "read:network",
    ],
    "responsable_caisse": [
        "read:customers", "create:customers", "update:customers",
        "read:accounts", "read:transactions", "create:transactions",
        "read:alerts", "manage:alerts",
    ],
    "agent_caisse": [
        "read:customers", "create:customers",
        "read:accounts", "read:transactions", "create:transactions",
        "read:alerts",
    ],
    "auditeur": [
        "read:customers", "read:accounts", "read:transactions",
        "read:alerts", "read:cases", "read:audit", "read:reports",
    ],
}
