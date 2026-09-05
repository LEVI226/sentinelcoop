# Schéma MVP hackathon

## Objectif

Livrer en 72 heures une version démontrable, pas une plateforme bancaire complète.

## Périmètre MVP

Le MVP doit couvrir:

- création client;
- contrôle CNIB;
- filtrage sanctions/PPE;
- création compte;
- saisie dépôt/retrait/retrait par procuration;
- seuils par caisse;
- Dori zone rouge et Banfora zone verte;
- alertes informatives et bloquantes;
- RBAC simple;
- journal d'audit;
- vue conformité réseau.

## Architecture MVP

```text
React/Vite
  pages:
    Login
    Dashboard caisse
    Client KYC
    Comptes
    Opération
    Alertes
    Vue réseau
    Audit

FastAPI
  services:
    auth_demo
    kyc_service
    screening_service
    transaction_rules
    alert_service
    audit_service
    sync_service

SQLite
  tables:
    caisses
    clients
    pieces_identite
    beneficiaires_effectifs
    comptes
    mandats_procurations
    watchlists
    operations
    alertes
    audit_log
    roles_permissions
```

## Structure projet recommandée

```text
sentinellecoop-app/
  backend/
    app/
      main.py
      db.py
      models.py
      schemas.py
      services/
        screening.py
        rules.py
        risk.py
        rbac.py
        audit.py
        sync.py
      routers/
        clients.py
        comptes.py
        operations.py
        alertes.py
        audit.py
    data/
      dataset_demo/
    requirements.txt
  frontend/
    src/
      pages/
      components/
      api/
      state/
      styles/
    package.json
  README.md
```

## API MVP

| Méthode | Route | Usage |
| --- | --- | --- |
| `POST` | `/auth/login` | Choix rôle démo |
| `GET` | `/caisses` | Liste caisses et seuils |
| `GET` | `/clients` | Clients visibles selon rôle |
| `POST` | `/clients` | Création client |
| `POST` | `/clients/{id}/screen` | Filtrage sanctions/PPE |
| `GET` | `/clients/{id}/risk-summary` | Vue consolidée client |
| `POST` | `/comptes` | Création compte |
| `POST` | `/operations` | Saisie opération et génération alertes |
| `GET` | `/alertes` | File alertes selon rôle |
| `POST` | `/alertes/{id}/decision` | Décision conformité |
| `GET` | `/audit-log` | Journal d'audit |
| `POST` | `/watchlists/import` | Import liste locale |

## Règles MVP minimales

| Code | Règle | Niveau |
| --- | --- | --- |
| R001 | Match sanction fort | Bloquant |
| R002 | Homonymie sanction moyenne | Informatif |
| R003 | PPE | Informatif |
| R004 | CNIB expirée | Bloquant |
| R005 | Dépôt au-dessus seuil local | Informatif |
| R007 | Fractionnement sous seuil | Informatif |
| R008 | Solde global multi-comptes élevé | Informatif |
| R009 | Opération zone rouge | Informatif |
| R010 | Procuration expirée | Bloquant |
| R014 | Liste obsolète | Bloquant ou admin |

## Démo de référence

### Cas 1 - Multi-caisses

- `GCLI_001` possède un compte à Dori et Banfora.
- L'agent de Dori ne voit pas les détails Banfora.
- La conformité réseau voit le risque consolidé.

### Cas 2 - Fractionnement

- Trois dépôts sous seuil à Dori.
- Le cumul déclenche une alerte informative.

### Cas 3 - Procuration

- Retrait par procuration avec mandat expiré.
- Le système bloque l'opération.

### Cas 4 - PPE/personne morale

- `SOCIETE SAHEL TRADING` possède un bénéficiaire effectif PPE.
- La revue renforcée se déclenche.

## Critères de réussite technique

- L'application démarre en moins de 30 secondes.
- La recherche sanctions/PPE répond en moins de 1 seconde sur le dataset de démo.
- La saisie opération génère les alertes attendues.
- Le mode hors ligne est crédible grâce au cache local.
- Le README explique comment lancer et tester.
