# CIF Guard Backend — Plateforme de conformité LBC/FT/FP

Backend **FastAPI + PostgreSQL** de la plateforme **CIF Guard** : filtrage et supervision
de la conformité **LBC/FT/FP** (Lutte contre le Blanchiment de Capitaux, le Financement
du Terrorisme et de la Prolifération) pour un réseau de caisses / coopératives
financières.

Construit sur le **cahier des charges fonctionnel et technique CIF Guard v1.0**.
Projet indépendant ; les deux scripts d'évaluation (`validate_cdc.py`,
`validate_criteria.py`) documentent le niveau de conformité mesuré.

---

## Sommaire

1. [Fonctionnalités](#1-fonctionnalités)
2. [Stack technique](#2-stack-technique)
3. [Structure du projet](#3-structure-du-projet)
4. [Prérequis](#4-prérequis)
5. [Installation](#5-installation)
6. [Configuration (`.env`)](#6-configuration-env)
7. [Initialisation de la base](#7-initialisation-de-la-base)
8. [Lancement (HTTP / HTTPS)](#8-lancement-http--https)
9. [Console admin & comptes](#9-console-admin--comptes)
10. [Sécurité & chiffrement](#10-sécurité--chiffrement)
11. [API](#11-api)
12. [Tests & validation](#12-tests--validation)
13. [Critères d'acceptation (§58)](#13-critères-dacceptation-58)
14. [Dépannage](#14-dépannage)
15. [Documentation](#15-documentation)

---

## 1. Fonctionnalités

### Filtrage & surveillance
- **Screening** de sanctions / listes (ONU, restreintes, watchlists) : moteur
  probabiliste (exact, fuzzy, alias, phonétique), importer une liste
  (checksum **SHA-256**, versionnage), fraîcheur des listes.
- **Moteur de règles** versionnées et configurables : seuil (THRESHOLD),
  fractionnement (STRUCTURING 48h), fréquence, vélocité — déclenchement
  automatique d'**alertes**.
- **Moteur de risque** explicable : score 0-100 décomposé en facteurs pondérés
  (client, transaction, réseau, caisse) + phrase d'explication.

### Gestion opérationnelle
- **Alertes** : workflow complet avec SLA (assignation, escalade, commentaire,
  demande d'information, confirmation, rejet, clôture) — retards calculés selon
  la priorité.
- **Dossiers (case management)** : notes, tâches, décisions, rattachement
  alertes/transactions, clôture.
- **Déclarations de soupçon** + **résultats de filtrage** (diagramme de classes).
- **Réseau multi-caisses** : relations, identités pseudonymisées, recherche
  d'un client à travers plusieurs caisses.
- **Audit** horodaté de toutes les actions critiques, avec filtres.

### Conformité technique
- **KYC** des clients (gestion des statuts PENDING/VERIFIED/UNDER_REVIEW), PEP.
- **ABAC/RBAC** : l'agent de caisse est strictement limité à son périmètre.
- **Chiffrement des données personnelles** : AES-256-GCM + dérivation HKDF,
  blind index HMAC pour recherche sans déchiffrement.
- **Journalisation** de toute action critique (login, transactions, alertes,
  déclarations, rapports…).
- **Mode connectivité dégradée** : files d'événements de synchronisation
  idempotentes (`event_id`).
- **Rapports** : génération (modèle `READY` + `storage_key`), agrégats
  dashboard alimentés par le backend.

---

## 2. Stack technique

| Couche | Technologie |
|---|---|
| Langage | **Python 3.14** |
| Framework | **FastAPI** (Starlette + Pydantic v2) |
| ORM | **SQLAlchemy 2.0** (asynchrone, psycopg 3) |
| Base de données | **PostgreSQL 16** |
| Sécurité | **Argon2id** · **AES-256-GCM** · **HKDF-SHA256** · **JWT** (access + refresh à rotation) |
| Frontend admin | HTML/CSS/JS statiques servis par FastAPI (`/admin`) |
| Docs API | Swagger UI (auto) |
| Tests | **pytest** (unitaires + intégration HTTP) |

---

## 3. Structure du projet

```
Back-end_filtrage/
├── run.py                      # Launcher Windows (fix SelectorEventLoop) + --https
├── requirements.txt
├── .env.example                # Modèle de configuration
├── app/
│   ├── main.py                 # Entrée FastAPI (routers /api/v1, /admin, /health)
│   ├── config.py               # Configuration centralisée (.env)
│   ├── database.py             # Engine + sessions SQLAlchemy async
│   ├── models/                 # Modèles SQLAlchemy
│   │   ├── auth.py             #   User, Role, Permission, Sesssion
│   │   ├── org.py              #   Cooperative, Branch, BranchRiskProfile
│   │   ├── customer.py         #   Customer, CustomerRiskScore, NetworkIdentity, IdentityMatch
│   │   ├── finance.py          #   Account, AccountHolder, Transaction
│   │   ├── rule.py             #   Rule, RuleVersion, RuleAction, RuleExecution
│   │   ├── screening.py        #   ScreeningSource/List/ListVersion/Entity/Alias, Run, Match
│   │   ├── alert.py            #   Alert, AlertEvent, Case, CaseNote, CaseDecision...
│   │   ├── declaration.py      #   DeclarationSoupcon, ResultatFiltrage
│   │   └── extra.py            #   AuditLog, InformationRequest, Document, Report,
│   │                           #   Notification, SyncEvent, SyncJob, NetworkRelationship...
│   ├── schemas/                # Schémas Pydantic (transaction, common/OKResponse...)
│   ├── api/v1/                 # Routers (préfixe /api/v1)
│   │   ├── auth.py  users.py  org.py
│   │   ├── customers.py  accounts.py  transactions.py
│   │   ├── screening.py  rules.py  alerts.py  cases.py
│   │   ├── declarations.py  network.py  dashboard.py
│   │   ├── audit.py  misc.py      # rapports, notifications, sync, settings, KYC...
│   ├── core/
│   │   ├── security.py         # Argon2id, AES-256-GCM, HKDF, JWT (access/refresh)
│   │   ├── rbac.py             # Registre des permissions + rôles système
│   │   ├── abac.py             # Contrôle de périmètre (branche / réseau)
│   │   ├── dependencies.py     # Deps FastAPI (get_current_user, require)
│   │   ├── errors.py           # Enveloppe d'erreur + middleware requestId
│   │   └── async_utils.py      # run_async / ensure_selector_loop
│   ├── services/
│   │   ├── risk_engine.py      # Scores explicables 0-100
│   │   ├── rule_engine.py      # Évaluateurs THRESHOLD/STRUCTURING/FREQUENCY/VELOCITY
│   │   ├── screening_engine.py # Matching probabiliste
│   │   ├── transaction_analysis.py  # Orchestration règle → risque → screening → alerte
│   │   ├── customer_crypto.py  # Chiffrement de domaine des PII
│   │   └── audit_service.py
│   ├── static/admin/           # Console admin (login + dashboard)
│   └── scripts/
│       ├── genkeys.py          # Génère JWT_SECRET + ENCRYPTION_MASTER_KEY
│       ├── init_db.py          # Crée toutes les tables (create_all)
│       └── seed.py             # Données de démonstration (idempotent)
├── tests/                      # test_core.py (28 unit) + test_api.py (16 E2E)
├── certs/                      # Certificat auto-signé Windows (run.py --https)
├── validate_cdc.py             # Conformité dérivée du CDC → 22/22
├── validate_criteria.py        # Critères d'acceptation §58 → 12/12
├── docs/                       # architecture, api, security, class-diagram-mapping
├── CHANGELOG.md                # Historique des évolutions
├── WORKFLOW.md                 # Méthode de travail
└── PROMPTS.md                  # Archive des demandes
```

---

## 4. Prérequis

| Logiciel | Version | Vérification |
|---|---|---|
| Python | **3.14+** | `python --version` |
| PostgreSQL | **16.x** | service `postgresql16` sur `127.0.0.1:5432` |

---

## 5. Installation

```powershell
# 1. Environnement virtuel
python -m venv .venv

# 2. Activer (PowerShell)
.\.venv\Scripts\Activate.ps1

# 3. Dépendances
pip install -r requirements.txt

# 4. Générer les clés de sécurité (JWT + chiffrement) → complète .env
python -m app.scripts.genkeys

# 5. Configuration
copy .env.example .env        # puis adaptez DATABASE_URL
```

---

## 6. Configuration (`.env`)

```ini
# ---- Serveur ----
APP_NAME=Back-end_filtrage
ENVIRONMENT=development
API_PREFIX=/api/v1
DEBUG=true
HOST=0.0.0.0
PORT=8000

# ---- Base de données PostgreSQL ----
DATABASE_URL=postgresql+psycopg://<user>:<mdp>@127.0.0.1:5432/cifguard

# ---- Sécurité / Chiffrement (générés par genkeys) ----
JWT_SECRET=<64 hex>
JWT_EXPIRES_MINUTES=30
REFRESH_EXPIRES_DAYS=7
ENCRYPTION_MASTER_KEY=<64 hex>        # clé maîtresse AES-256-GCM des PII

# ---- Stockage (documents) ----
STORAGE_BACKEND=local
STORAGE_LOCAL_DIR=./storage

# ---- CORS ----
CORS_ORIGINS=*
```

> **Secrets** : jamais commité (`.env` dans `.gitignore`). Régénérez avec
> `python -m app.scripts.genkeys` (idempotent : n'écrase pas les clés déjà présentes).

---

## 7. Initialisation de la base

```powershell
# 1. Créer les tables (create_all — toutes les migrations incluses)
python -m app.scripts.init_db

# 2. Données de démonstration (rôles, permissions, caisses, clients, alertes...)
python -m app.scripts.seed
```

> `seed.py` est **idempotent** : il s'arrête si l'utilisateur `admin` existe déjà.
> Pour repartir de zéro : droppez les tables de la base `cifguard`, puis relancez
> `init_db` + `seed`.

Aperçu du jeu de données seed : **7 utilisateurs**, **5 caisses**, **1 coopérative**,
**20 clients** (dont « Client A » multi-caisses avec identité réseau), **~40 comptes**,
**200 transactions**, **15 alertes**, **5 dossiers**, **listes de screening**,
**2 règles actives** (`STRUCTURING_48H`, `HIGH_VALUE_TRANSFER`).

---

## 8. Lancement (HTTP / HTTPS)

> **Windows** : il faut un `SelectorEventLoop` pour psycopg asynchrone. Utilisez le
> launcher `run.py` (qui applique le correctif automatiquement) plutôt qu'un appel
> direct à uvicorn.

```powershell
# HTTP — port 8000
python run.py

# Autre port
python run.py --port 8001

# Rechargement automatique (développement)
python run.py --reload

# HTTPS — port 8443 (certificat auto-signé Windows, voir §14)
python run.py --https

# HTTPS sur un autre port
python run.py --https --port 9443
```

| Page | URL |
|---|---|
| Dashboard admin | http://localhost:8000/admin |
| Swagger UI | http://localhost:8000/api/docs |
| OpenAPI (JSON) | http://localhost:8000/api/openapi.json |
| Health | http://localhost:8000/health |
| Health BD | http://localhost:8000/health/database |
| Racine (info service) | http://localhost:8000/ |

En HTTPS : mêmes chemins sur `https://127.0.0.1:8443/...`.

---

## 9. Console admin & comptes

Console web statique (**login + dashboard** : KPIs, répartition de risque,
alertes prioritaires, dossiers, clients, screening, audit, caisses).
Tous les comptes seed partagent le mot de passe **`CIFGuard@2026`** :

| Email | Rôle | Périmètre / permissions |
|---|---|---|
| `admin@cifguard.net` | **superadmin** | toutes les permissions (36) |
| `reseau@cifguard.net` | **conformite_reseau** | screening, réseau, cas (18) |
| `analyste@cifguard.net` | **analyste_conformite** | alertes, dossiers, cas |
| `auditeur@cifguard.net` | **auditeur** | audit, rapports |
| `caisse1@cifguard.net` | **responsable_caisse** | périmètre caisses |
| `agent1@cifguard.net` | **agent_caisse** | **uniquement sa caisse** (ABAC) |
| `agent2@cifguard.net` | **agent_caisse** | **uniquement sa caisse** (ABAC) |

> **Test ABAC** : connectez-vous en `agent1` → le dashboard et les API non exposées
> à son périmètre renvoient `403` (`FORBIDDEN_OBJECT`) pour les ressources d'autres
> caisses.

---

## 10. Sécurité & chiffrement

- **Mots de passe** : Argon2id.
- **Données personnelles chiffrées** (AES-256-GCM, clé maîtresse `ENCRYPTION_MASTER_KEY`,
  nonces dérivés par **HKDF-SHA256** pour la séparation de domaine) : nom, email,
  téléphone, date de naissance, adresse, etc.
- **Recherche sans déchiffrement** : *blind index* HMAC (nom, email, téléphone).
- **Sessions JWT** : access token court (30 min) + refresh à **rotation** avec
  révocation par `jti` / gestion de sessions.
- **RBAC** : registre central des permissions (`rbac.py`), rôles système.
- **ABAC** : contrôle de périmètre caisse (`branch_id`) et réseau — masquage des
  données hors périmètre, pas seulement au niveau de l'UI.
- **Audit** : chaque action critique est horodatée (`actor_id`, `actor_role`,
  `action`, `entity`, `reason`).

Détails : `docs/security.md`.

---

## 11. API

- Préfixe : **`/api/v1`**
- Documentation interactive : **Swagger** sur `/api/docs`
- Authentification : `Authorization: Bearer <access_token>`

### Format commun (§45-47 du CDC)

Succès :
```json
{
  "success": true,
  "data": { "id": 123, "reference": "TX-0001" },
  "meta": { "requestId": "req_9f2c" }
}
```

Liste :
```json
{
  "success": true,
  "data": [ ],
  "meta": { "page": 1, "limit": 20, "total": 157, "requestId": "req_9f2c" }
}
```

Erreur :
```json
{
  "success": false,
  "error": { "code": "CUSTOMER_NOT_FOUND", "message": "Client introuvable", "details": {} },
  "requestId": "req_9f2c"
}
```

### Aperçu des modules

| Module | Routes principales |
|---|---|
| `auth` | `POST /auth/login`, `/refresh`, `/logout`, `GET /auth/me`, `/sessions` |
| `customers` | `GET/POST /customers`, `GET /customers/{id}/risk`, `POST /customers/{id}/screen`, `/review` |
| `transactions` | `POST /transactions` (analyse async), `GET /transactions[/{id}]` |
| `accounts` | `GET/POST /accounts`, `GET /accounts/{id}/transactions` |
| `alerts` | `GET/POST /alerts`, `POST /alerts/{id}/assign\|escalate\|comment\|confirm\|dismiss\|close` |
| `cases` | `GET/POST /cases`, `POST /cases/{id}/alerts\|notes\|tasks\|decision\|close` |
| `rules` | `GET/POST /rules`, `POST /rules/{id}/activate\|deactivate`, `GET /rules/{id}/versions` |
| `screening` | `GET /screening/matches`, `/runs`, `/list-versions`, `POST /screening/lists/import`, `GET /screening/lists/status` |
| `declarations` | `POST/GET/PATCH /declarations`, `GET /filtering-results`, `POST /filtering-results/{id}/decision` |
| `network` | `GET/POST /network/relationships`, `GET /network/customers/{id}`, `GET /network/identities`, `POST /network/identities/match` |
| `dashboard` | `GET /dashboard/summary`, `/risk-distribution`, `/alerts-trend`, `/priority-alerts`, `/transaction-summary`, `/compliance-summary` |
| `org` | `GET/POST/PATCH /cooperatives`, `/branches`, `POST /branches/{id}/risk-profile` |
| `users` | `GET/POST/PATCH /users`, `GET /roles` |
| `audit` | `GET /audit`, `GET /audit/summary` |
| `misc` | `PATCH /customers/{id}/kyc`, `GET/POST /reports`, `GET /notifications`, `POST /sync/events`, `GET /sync/status`, `GET/PUT /settings` |

Référence complète : `docs/api.md`.

### Exemple — connexion

```powershell
$body = '{"email":"admin@cifguard.net","password":"CIFGuard@2026"}'
$r = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -ContentType "application/json" -Body $body
$token = $r.data.access_token

# Appel authentifié
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard/summary" -Headers @{Authorization="Bearer $token"}
```

---

## 12. Tests & validation

Le serveur doit être **lancé** pour les tests d'intégration (E2E).

```powershell
# Suite complète : 28 unitaires + 16 intégration → 44
python -m pytest tests -q

# Conformité dérivée du CDC (22 assertions) → 22/22
python validate_cdc.py

# Critères d'acceptation §58 (12 critères, API réelle) → 12/12
python validate_criteria.py
```

Résultats de référence :

| Vérification | Command | Résultat |
|---|---|---|
| Suite pytest | `pytest tests -q` | **44 passed** (28 unit + 16 E2E) |
| Conformité CDC | `python validate_cdc.py` | **22/22** |
| Critères d'acceptation | `python validate_criteria.py` | **12/12** |

---

## 13. Critères d'acceptation (§58)

État mesuré par `validate_criteria.py` (12/12) :

1. Un utilisateur peut se connecter **selon son rôle**.
2. Un agent ne peut pas consulter les données **hors de son périmètre** (403).
3. Une transaction est **enregistrée et analysée** (score de risque).
4. Une règle peut générer **automatiquement une alerte**.
5. Une alerte peut être **affectée, escaladée et clôturée**.
6. Toutes les **actions critiques apparaissent dans l'audit**.
7. Un client peut être recherché **à travers plusieurs caisses** via son identité
   réseau autorisée.
8. Le système peut produire un **score de risque explicable**.
9. Un screening **conserve la version de la liste** utilisée.
10. Le système peut **continuer temporairement en connectivité dégradée**
    (files sync idempotentes).
11. Le **dashboard** du frontend reçoit ses indicateurs **depuis le backend**.
12. Les **rapports** peuvent être générés depuis les données réelles du système.

---

## 14. Dépannage

| Problème | Solution |
|---|---|
| `Psycopg cannot use ProactorEventLoop` | Lancer via `python run.py` (jamais uvicorn direct sous Windows) |
| `Address already in use` | Changer de port : `python run.py --port 8001` |
| Erreur `JWT_SECRET manquant` | `python -m app.scripts.genkeys` puis relancer |
| Base vide / « no such table » | `python -m app.scripts.init_db` puis `python -m app.scripts.seed` |
| Aucune alerte après une transaction | Vérifier que `run.py` a été relancé après modification de `transaction_analysis.py` (analyse async) |
| Certificat HTTPS refusé dans le navigateur | Les exports reposent sur `certs/` ; régénérer via le script PowerShell (SAN `localhost`+`127.0.0.1`, installé dans `Cert:\CurrentUser\Root`) |
| Dashboard renvoie 401 après relance | À nouveau login (secret JWT changé → anciens tokens invalidés) |

---

## 15. Documentation

| Document | Rôle |
|---|---|
| `README.md` | Ce document |
| `CHANGELOG.md` | Historique des évolutions ([0.1.0] → [0.1.2]) |
| `WORKFLOW.md` | Méthode de travail et procédures techniques |
| `PROMPTS.md` | Archive des demandes utilisateur |
| `docs/architecture.md` | Architecture technique |
| `docs/security.md` | Sécurité, chiffrement, JWT |
| `docs/api.md` | Référence API complète |
| `docs/class-diagram-mapping.md` | Mapping du diagramme de classes du CDC |