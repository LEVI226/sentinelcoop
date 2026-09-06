# Architecture — CIF Guard Backend

## Présentation

Backend **FastAPI** (Python 3.14) servant l'API de conformité LBC/FT/FP du réseau
CIF Guard, ainsi que la console d'administration statique sur `/admin`.

Stack :
- **FastAPI 0.141** — framework HTTP
- **SQLAlchemy 2.0 async + psycopg3** — accès PostgreSQL
- **PostgreSQL 16** — persistance (base dédiée `cifguard`)
- **Alembic 1.19** — migrations (disponible)
- **Argon2id, AES-256-GCM, HKDF-SHA256, PyJWT** — sécurité

## Arborescence

```
app/
  main.py                 # Point d'entrée, assemblage des routers, static /admin
  config.py               # Paramètres (.env)
  database.py             # Engine async + session + Base
  core/
    security.py           # Argon2id, AES-GCM, HKDF, blind index, JWT
    errors.py             # Format d'erreur commun (§45-46) + handlers + middleware request_id
    rbac.py               # PERMISSIONS + SYSTEM_ROLES
    abac.py               # Périmètre caisse + sensibilité des données
    dependencies.py        # CurrentUser, get_current_user, require()
    async_utils.py        # Fix event loop Windows (psycopg)
  models/                 # 54 modèles SQLAlchemy
  schemas/                # Schémas Pydantic (auth, customer, transaction, operations, common)
  services/               # Moteurs métier (risque, règle, screening, crypto, transaction, audit)
  api/v1/                 # Routers REST (préfixe /api/v1)
    auth, customers, transactions, accounts, alerts, cases,
    rules, screening, declarations, dashboard, org, users, audit,
    network, misc
  scripts/                # init_db, seed, sync_rbac, migrate_class_diagram, genkeys
  static/admin/           # Console admin (index.html, dashboard.html)
run.py                    # Launcher : fix event loop puis uvicorn
```

## Flux de requête

1. Middleware `request_id_middleware` : injecte `request.state.request_id` (uuid ou
   `x-request-id` entrant) — traçabilité.
2. Routage `/api/v1/**` → contrôleur → `Depends(get_db)` (session async).
3. Authentification : `get_current_user` (token Bearer, check session, charge rôles +
   permissions).
4. `require("perm")` : contrôle RBAC ; ABAC appliqué dans les contrôleurs
   (`can_access_branch`, `can_read_sensitive`).
5. Réponses standard `{success, data, meta{requestId}}` ; erreurs
   `{success, error{code,message,details}, requestId}`.
6. Registre d'audit **append-only** (`AuditLog`) sur les actions sensibles ;
   aucune route ne permet leur suppression. La rétention est pilotée par le
   paramètre système `audit_log_retention_days` (défaut 365 j) et appliquée par
   une tâche de fond qui purge quotidiennement les entrées dépassées (~24 h).

## Postes de travail & rétention des logs

- **`PosteDeTravail`** (`postes_de_travail`) : poste de travail rattaché à une
  caisse (`branch_id`) et facultativement à un compte utilisateur
  (`user_id`, unique). `code` unique et durable d'un poste.
- Création/suppression réservées au superadmin (`manage:postes`) ; suppression
  **logique** (`is_active=false`) : historique conservé, code réservé.
- **Réinitialisation de mot de passe** (`POST /users/{id}/reset-password`,
  `update:users`) : impose une politique de force, force le changement au
  prochain login et révoque sessions + refresh tokens.
- **Rétention de l'audit** : `audit_service.purge_obsolete_audit_logs()` purge
  les `AuditLog.timestamp` plus vieux que le délai configuré (lecture du
  paramètre `audit_log_retention_days`, min 1). La régularité est assurée par
  la tâche `start_audit_log_purge_task` lancée au démarrage de l'application.

## Moteurs métier

| Service | Rôle | CDC |
|---|---|---|
| `risk_engine` | Scores 0-100 explicables (client/transaction/réseau/caisse) | §18-20 |
| `rule_engine` | Évaluation des règles (structuring 48h, forte valeur, …) | §15 |
| `screening_engine` | Normalisation, clé phonétique, similarité | §16-17 |
| `transaction_analysis` | Règle → risque → alerte (mode différé) | §31 |
| `customer_crypto` | Chiffrement PII + blind index | §44 |

## Sécurité des données clients

- Champs PII **chiffrés AES-256-GCM** (nonce aléatoire, payload `v1:...`).
- **HKDF-SHA256** dérive une sous-clé par domaine (isolation par entité).
- **Blind index HMAC** pour la recherche sans déchiffrer (nom/email/téléphone).
- Mots de passe **Argon2id**.
- **JWT HS256** access (30 min) + refresh (30 j) avec rotation et `jti`.

## Frontend admin

Frontend statique (HTML/JS vanilla) servi par FastAPI sur `/admin` :
- `index.html` : connexion → `/api/v1/auth/login` + `/auth/me`
- `dashboard.html` : KPIs, distribution de risque, alertes, dossiers, clients,
  filtrage, audit, caisses — alimentés par l'API `/api/v1/dashboard/**`.

## Démarrage (Windows)

```powershell
cd C:\Users\PREDATOR\Documents\Back-end_filtrage
.\.venv\Scripts\python.exe run.py            # ou --port 8001
# API : http://127.0.0.1:8000/api/docs     (Swagger)
# Admin : http://127.0.0.1:8000/admin
```

Le launcher `run.py` configure `SelectorEventLoop` avant uvicorn (requis par psycopg
async sur Windows — sinon `ProactorEventLoop` + erreur).
