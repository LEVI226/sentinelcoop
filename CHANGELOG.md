# Changelog — CIF Guard Backend

Format inspiré de [Keep a Changelog](https://keepachangelog.com/).
Versioning **0.1.0** (état de développement/démo).

## [0.1.2] — 2026-09-06
### Ajouté
- **Validation des critères d'acceptation `validate_criteria.py`** : les **12 critères
  §58** du CDC évalués un à un contre l'API réelle —
  `python validate_criteria.py` → **12/12 OK** :
  connexion selon le rôle, périmètre ABAC de l'agent, transaction enregistrée +
  analysée, règle → alerte automatique, cycle alerte (affectation/escalade/clôture),
  actions critiques dans l'audit, recherche multi-caisses via identité réseau,
  score de risque explicable, screening conservant la version de la liste,
  connectivité dégradée (files sync idempotentes), dashboard alimenté par le backend,
  rapports générés depuis les données réelles.

### Corrigé
- **Génération d'alertes par règles** (`transaction_analysis.py`) : le code d'alerte
  `AL-{date}-{txn_id}` était identique pour toutes les règles déclenchées sur la même
  transaction → collision sur l'index unique `alerts.code` → `IntegrityError` → analyse
  entièrement annulée (rollback silencieux, risque resté à 0, aucune alerte).
  Le code inclut désormais le code règle : `AL-{date}-{txn_id}-{rule.code}`.
- Visibilité des erreurs : l'échec d'une analyse asynchrone est désormais journalisé
  (`logger.exception`) au lieu d'un rollback silencieux.

### Notes
- `python validate_criteria.py` → 12/12 ; `pytest tests -q` → 44/44.

## [0.1.1] — 2026-09-06
### Ajouté
- **Certificat auto-signé Windows** (`certs/`) : `New-SelfSignedCertificate` pour
  `localhost`/`127.0.0.1` (RSA 2048, SHA256, 2 ans), installé dans
  `Cert:\CurrentUser\Root` (navigateur sans avertissement), exporté en `.pfx`
  (mot de passe `cifguard@2026`), `.cer`, et `.crt`/`.key` PEM pour uvicorn.
- `run.py --https` : sert l'API + la console admin en HTTPS sur `127.0.0.1:8443`
  (certif `certs/cifguard.crt` + `certs/cifguard.key`). `.pfx`/`.key` ignorés par git.

## [0.1.0] — 2026-09-06
### Ajouté
- **Tests automatisés** (`tests/`) : 28 tests unitaires (security/crypto, risk_engine,
  rule_engine, screening_utils, ABAC) + 16 tests d'intégration E2E contre le serveur
  (`tests/test_api.py`) — **44 passants**.
- **Validation CDC `validate_cdc.py`** : 22 assertions de conformité dérivées des
  sections référencées (§45-47 format réponse, §49-50 seed, §15 règles, §16-17
  screening, chiffrement/JWT, diagramme de classes) — **22/22 OK**.
- Documentation finale : `CHANGELOG.md`, `PROMPTS.md`, `docs/api.md`.
- **API FastAPI** complète (préfixe `/api/v1`) :
  - Auth (login, refresh avec rotation + `jti`, logout, me, change-password,
    recover, sessions)
  - Customers / KYC / risk (scores explicables) / screen
  - Transactions (+ analyse asynchronous), comptes
  - Alertes (workflow SLA : assign/escalade/commentaire/demande d'info/confirmation/rejet/fermeture)
  - Dossiers (notes, tâches, décisions, rattachement alertes/transactions)
  - Règles (versionnées, activate/deactivate), Screening (listes versionnées, import, fraîcheur)
  - Déclarations de soupçon + résultats de filtrage (diagramme de classes)
  - Dashboard (summary, risk-distribution, alerts-trend, priority-alerts,
    transaction-summary, compliance-summary)
  - Coopératives / caisses / profils de risque, utilisateurs / rôles / permissions
  - Réseau (relations, identités pseudonymisées, multi-caisses), audit, rapports,
    notifications, synchronisation hors-ligne, paramètres système
- **Sécurité** : Argon2id, AES-256-GCM (PII), HKDF-SHA256 (sous-clés), blind index
  HMAC, JWT access/refresh à rotation.
- **Console admin statique** servie par FastAPI (`/admin`) : connexion + tableau de
  bord (KPIs, distribution de risque, alertes, dossiers, clients, filtrage, audit, caisses).
- **Launcher Windows** `run.py` : configure `SelectorEventLoop` avant uvicorn
  (compatibilité psycopg async).
- **Documentation** : `docs/architecture.md`, `docs/security.md`, `docs/api.md`,
  `docs/class-diagram-mapping.md`.

### Corrigé
- Conformité §45-47 : `auth/login` et `auth/refresh` retournent désormais
  l'enveloppe standard `{success, data{access_token,refresh_token,...},
  meta{requestId}}` (au lieu du payload OAuth plat). Consommateurs mis à jour
  (frontend `/admin`, `tests/test_api.py`, smoke_test.py).
- Route `auth/refresh` : ajout du claim `jti` au refresh token et retour d'un vrai
  JWT (au lieu du `RefreshToken.id`).
- Appel `create_access_token(..., coop_id=...)` (correspondance de paramètre).
- Comparaisons temporelles aware/naive (alertes `due_at`, refresh).
- `AuditLog` : sérialisation alignée sur le modèle (`timestamp`, `reason`).
- Permissions des routes reports (`generate:reports`) et sync (`manage:sync`)
  alignées sur le registre RBAC.
- ABAC `_role_set` : tolère les rôles en chaînes (`CurrentUser.roles`).

### Notes
- Étape validation d'acceptation terminée : `python validate_cdc.py` → 22/22 ;
  `pytest tests -q` → 44/44 ; smoke_test 29/29.
- Données seed : 7 users, 5 branches, 20 clients, 40 comptes, 200 transactions,
  15 alertes, 5 dossiers, listes de screening, règles de démo.
