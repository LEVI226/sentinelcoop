# PROMPTS — Historique et guide de poursuite

Ce fichier documente le périmètre, les décisions et les invites types pour poursuivre
le développement de CIF Guard Backend.

## Objectif

Construire le back-end de la plateforme **CIF Guard** pour un réseau de caisses /
coopératives financières : conformité **LBC/FT/FP** (filtrage des opérations,
KYC, scoring de risque, alertes, dossiers, déclarations, audit, reporting),
avec chiffrement « dernière génération » des dossiers clients.

## Décisions clés (validées utilisateur)

- **FastAPI** (même si le CDC évoquait NestJS).
- Périmètre : **tout le cahier des charges**.
- Chiffrement : **JWE + HKDF + clés** (implémentation AES-256-GCM via
  `cryptography` + HKDF-SHA256 + Argon2id).
- Dashboard : **frontend statique servi par FastAPI** (`/admin`) avec design pro.
- Intégration du **diagramme de classes** fourni (`DeclarationSoupcon`,
  `ResultatFiltrage`, colonne `alert_type`). Mapping dans
  `docs/class-diagram-mapping.md`.

## État

- Noyau sécurité/moteurs/modèles/seed : **fait**.
- Routes API : **toutes créées et smoke-testées (29 endpoints E2E OK)**.
- Console admin : **login + dashboard fonctionnels**.
- Tests : **44/44 pytest (28 unit + 16 intégration)** ; validation CDC **22/22** ;
  **critères d'acceptation §58 : 12/12** (`python validate_criteria.py`).
- Correctif de session : alertes générées par règles avec codes uniques
  `AL-{date}-{txn}-{règle}` (avant : collision sur `alerts.code`).
- Tickets ouverts : génération réelle des rapports PDF/XLSX, sync hors-ligne complète.

## Invites utiles pour continuer

- *« Lance le serveur et vérifie le parcours login → dashboard → alerte → dossier →
  déclaration de soupçon »*.
- *« Ajoute des tests unitaires pour risk_engine, rule_engine, screening_engine,
  security (Argon2id/AES-GCM/JWT) et les routes Auth »*.
- *« Valide les 12 critères d'acceptation du cahier des charges »*.
- *« Ajoute la génération de rapports PDF/XLSX réelle (worker) »*.
- *« Implémente la synchronisation hors-ligne complète (queue + résolution de conflit) »*.
- *« Restreins le CORS et prépare la config production (HTTPS, reverse proxy) »*.

## Comptes seed

Tous avec le mot de passe `CIFGuard@2026` :
- `admin@cifguard.net` — superadmin
- `reseau@cifguard.net` — conformite_reseau
- `analyste@cifguard.net` — analyste_conformite
- `auditeur@cifguard.net` — auditeur
- `caisse1@cifguard.net` — responsable_caisse
- `agent1@cifguard.net`, `agent2@cifguard.net` — agent_caisse
