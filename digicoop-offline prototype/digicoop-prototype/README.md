# DigiCoop Terminal — Filtrage LBC/FT/FP (prototype offline-first)

Prototype fonctionnel pour le Hackathon National d'Innovation CIF — DigiCoop-WA+, Thématique 01.
Implémente l'architecture offline-first discutée : terminal PWA (React + SQLite en WebAssembly)
qui filtre en temps réel, et un central (FastAPI + PostgreSQL) qui consolide et distribue les
listes de sanctions/PPE via une file de synchronisation asynchrone.

**Données** : uniquement synthétiques (`backend/app/seed_watchlist.py`), conformément à la règle
« aucune donnée réelle » du briefing hackathon.

## Le parcours implémenté

```
Client → Comptes et solde global → Filtrage PPE/sanctions → Opération contrôlée
       → Alerte persistante → Décision humaine et audit
```

Les 4 premières étapes tournent entièrement en local (`frontend/src/engine/`), en moins d'une
seconde, sans dépendre du réseau. Les 2 dernières basculent vers l'asynchrone via la file de
synchronisation (`frontend/src/sync/`), sans jamais bloquer l'agent au guichet.

## Structure et répartition par axe (4 personnes, 4 dossiers disjoints)

```
backend/                       Backend + sécurité — FastAPI, PostgreSQL, endpoints /sync/*, /alerts
frontend/src/engine/           Moteur IA — fuzzy matching, règles transactionnelles, orchestration du filtrage
frontend/src/offline/          Mode offline — sentinelle réseau, file de synchronisation, backoff, dead-letter
frontend/src/components/       Frontend — écrans React, formulaires, tableau de bord local
frontend/src/db/               Partagé (infra) — SQLite-WASM local, générique, ne dépend d'aucun axe
docker-compose.yml             Postgres + API, pour un central prêt en une commande
```

Chaque axe a son propre contrat d'interface, documenté dans son dossier
(`frontend/src/offline/README.md` pour l'axe mode offline). Le seul point où
les axes se rencontrent est `App.jsx`, qui les assemble sans qu'aucun des
trois ne dépende du code interne d'un autre — voir la note d'intégration
dans ce fichier.

## Démarrer le central

```bash
# Option rapide (SQLite, zéro dépendance) :
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m app.seed_watchlist        # charge les listes synthétiques
uvicorn app.main:app --reload --port 8000

# Option réelle (PostgreSQL, via Docker) :
docker compose up --build
docker compose exec api python -m app.seed_watchlist
```

## Démarrer le terminal

```bash
cd frontend
npm install        # copie aussi sql-wasm.wasm dans public/ (postinstall)
cp .env.example .env
npm run dev
```

Ouvrir l'URL affichée (par défaut `http://localhost:5173`). Le terminal fonctionne même si le
central n'est pas démarré — c'est le point central de l'architecture.

## Scénario de démo (celui attendu par le jury — démonstration live obligatoire)

1. Démarrer le central, puis le terminal. À la première ouverture, choisir un code pour
   chiffrer la base locale (voir `frontend/src/offline/README.md`, section 12) ; aux ouvertures
   suivantes, entrer ce même code. Laisser une synchronisation se faire (le point de statut
   passe à « synchronisé »).
2. Couper le réseau (mode avion, ou simplement arrêter le central).
3. Créer un client avec un montant élevé (≥ 2 000 000 XOF) → l'alerte apparaît instantanément
   dans « Alertes locales », le point de statut passe à « hors-ligne — file en attente ».
4. Reconnecter / relancer le central → dans les secondes qui suivent, l'alerte apparaît sur
   `GET /alerts` côté central, sans aucune action de l'agent.
5. (Optionnel, pour montrer la résilience) Rouvrir le terminal dans un second onglet : un
   bandeau avertit que ce terminal est déjà ouvert ailleurs. Fermer un des deux onglets.

## Tests

```bash
pip install --break-system-packages playwright && playwright install chromium
cd frontend && npm run build && npx vite preview --port 4173 &
python3 tests/test_offline_only.py             # le terminal fonctionne sans central du tout
python3 tests/test_end_to_end_sync.py          # une alerte créée localement arrive bien côté central
python3 tests/test_backoff_dead_letter.py      # backoff, dead-letter et renvoi manuel réellement exercés
python3 tests/test_encryption_roundtrip.py     # chiffrement au repos sur un vrai cycle fermeture/réouverture
```

Les quatre scripts ont été exécutés pendant le développement de ce prototype : filtrage flou
validé (95 % de similarité sur une variante orthographique, non-régression vérifiée après
optimisation — voir `frontend/src/engine/BENCHMARK.md`), upsert central idempotent vérifié
(un lot rejoué ne crée pas de doublon), synchronisation de bout en bout confirmée, la machine
à états complète de la file de synchro (y compris la transition vers `dead_letter` et son renvoi
manuel) observée sous échec réseau simulé plutôt que seulement documentée, et le chiffrement au
repos vérifié sur un vrai cycle fermeture/réouverture du navigateur (bon code accepté et données
retrouvées, mauvais code rejeté proprement).

## Ce qui reste à durcir pour une mise en production réelle

- Seuils de score (fuzzy matching, règles transactionnelles) à calibrer avec les experts métier CIF.
- Persistance locale en OPFS plutôt qu'IndexedDB simple, pour de meilleures performances sur de
  gros volumes et pour permettre un vrai partage d'état entre onglets (la coordination actuelle
  détecte et avertit un usage multi-onglet, elle ne fusionne pas l'état — voir
  `frontend/src/offline/README.md`, section 13).
- Authentification par agence (clé API / JWT) sur les endpoints `/sync/*`.
- Dashboard conformité central (l'API `/alerts` et `/alerts/{id}/decision` existent déjà, l'UI reste à faire).
- Le chiffrement au repos protège un terminal perdu/volé et non déverrouillé ; il ne remplace pas
  une gestion d'utilisateurs individuels — voir le modèle de menace détaillé dans
  `frontend/src/offline/README.md`, section 12.
