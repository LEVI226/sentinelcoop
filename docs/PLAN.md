# Plan - PRD -> Plan -> Specs -> Code/Build/Test -> Review -> Deployment

## Phase 1 - PRD

Statut: fait.

Livrables:

- `PRODUCT.md`
- `docs/PRD.md`

Decision principale: construire une demo web statique, locale et sans dependances.

## Phase 2 - Plan

Statut: fait.

Ordre de construction:

1. Creer la surface web de demo.
2. Ajouter les donnees synthetiques.
3. Implementer le filtrage client cote demo.
4. Implementer consolidation multi-comptes et fractionnement.
5. Ajouter alertes, audit et rapport.
6. Tester les cas de demonstration.
7. Lancer un serveur local pour repetition.

## Phase 3 - Specs

Statut: fait.

Livrable:

- `docs/SPECS.md`

## Phase 4 - Code / Build / Test

Statut: en cours.

Livrables cibles:

- `demo/index.html`
- `demo/styles.css`
- `demo/app.js`
- `demo/test-demo.js`

## Phase 5 - Review

Statut: a faire apres build.

Checklist:

- aucun texte important ne deborde sur desktop/mobile;
- les quatre scenes du pitch sont visibles;
- les donnees simulees sont explicites;
- les alertes ont une action claire;
- le rapport contient motif, score, horodatage et decision.

## Phase 6 - Deployment

Statut: a faire apres tests.

Deploiement prevu: serveur local Python.

Commande:

```powershell
python -m http.server 8787 -d demo
```

URL:

```text
http://localhost:8787
```

