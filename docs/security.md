# Sécurité — CIF Guard Backend

## Chiffrement, hachage et jetons

Toute la cryptographie repose sur une **clé maîtresse** (64 octets hex) dans `.env`
(`ENCRYPTION_MASTER_KEY`), dérivée en sous-clés par domaine via **HKDF-SHA256**
(`app/core/security.py`).

| Usage | Mécanisme |
|---|---|
| Mots de passe | **Argon2id** (`hash_password` / `verify_password`) |
| PII clients | **AES-256-GCM** (`encrypt_field`, nonce 12 o, AAD nul, payload `v1:<nonce+ct>`) |
| Déterminisme recherche | **HMAC-SHA256** blind index (`blind_last_name`, `_first_name`, `_email`, `_phone`) |
| Tokens access | **JWT HS256**, 30 min (`JWT_EXPIRES_MINUTES`) |
| Tokens refresh | **JWT HS256**, 30 j, rotation + `jti` (référence `RefreshToken` en base) |

`create_access_token` : `sub, uid, role, branch_id, coop_id, sid, type=access`.
`create_refresh_token` : `sub, uid, sid, jti, type=refresh`.

## Authentification & sessions

- `POST /api/v1/auth/login` : vérifie Argon2id, crée `UserSession` (id uuid),
  émet access + refresh.
- `POST /api/v1/auth/refresh` : vérifie le JWT refresh, retrouve le `RefreshToken`
  par `jti`+`sid`, vérifie non-révoqué/non-expiré, **révoque** l'ancien et **roule**
  vers un nouveau (rotation).
- `POST /api/v1/auth/logout` : révoque la session courante.
- `GET /api/v1/auth/me`, `POST /api/v1/auth/change-password`,
  `GET|DELETE /api/v1/auth/sessions`.

Toute requête protégée passe par `get_current_user` qui :
1. valide le JWT access,
2. si claim `sid` présent, vérifie la session non révoquée,
3. charge l'utilisateur (actif) + rôles + permissions.

## RBAC / ABAC

- `PERMISSIONS` + `SYSTEM_ROLES` (`app/core/rbac.py`) : rôles système
  (superadmin, admin, conformite_reseau, analyste_conformite, responsable_caisse,
  agent_caisse, auditeur).
- `require("perm")` (`core/dependencies.py`) : contrôle de permission simple.
- `abac.py` :
  - `can_access_branch` : un utilisateur ne voit que sa caisse, sauf rôles réseau
    (`superadmin`, `conformite_reseau`).
  - `can_read_sensitive` : niveaux de sensibilité `public/internal/confidential/restricted`
    pour restreindre p. ex. les notes d'investigation.

## Piste d'audit

`AuditLog` append-only : `timestamp, actor_id, actor_role, action, entity_type,
entity_id, old_value, new_value, request_id, ip_address, device_id`.
Écrit via `audit(...)` sur connexions, créations/mises à jour sensibles, workflows
d'alertes/dossiers, screening, règles, réglages.

## Recommandations production

- Forcer **HTTPS** derrière un reverse proxy (Nginx/Caddy) ; gérer `X-Forwarded-*`.
- Router sur des **clés maîtresses dédiées** (`customer.pii`, `customer.phone`, …)
  déjà séparées par domaine HKDF.
- Remplacer le secret JWT et la clé maîtresse au premier déploiement.
- Limiter les origines CORS (aujourd'hui `*` pour la démo).
- Génération de rapports/exports via un worker dédié.
- Journaux d'audit : purge/archivage selon la réglementation locale.
