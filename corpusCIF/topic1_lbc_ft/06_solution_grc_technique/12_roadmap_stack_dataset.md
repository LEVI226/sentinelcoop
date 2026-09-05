# Roadmap, dataset et stack technique Topic 1

## Décision produit

Construire un assistant conformité LBC/FT/FP léger pour réseau de caisses.

Le MVP doit prouver quatre choses:

- filtrer un client ou une transaction contre sanctions/PPE;
- consolider le risque d'un client qui possède plusieurs comptes dans plusieurs caisses;
- générer des alertes explicables;
- protéger la visibilité des données par rôle.

## Dataset à utiliser

Le dataset de démo est dans:

`05_jeu_donnees_synthetique/dataset_demo/`

Fichiers:

- `caisses.csv`: caisses, villes, zones de risque et seuils locaux.
- `clients.csv`: clients physiques et moraux fictifs.
- `pieces_identite.csv`: CNIB, passeports et RCCM fictifs.
- `beneficiaires_effectifs.csv`: bénéficiaires effectifs pour personnes morales.
- `comptes.csv`: comptes détenus dans plusieurs caisses.
- `mandats_procurations.csv`: retraits par procuration.
- `listes_surveillance_synthetiques.csv`: sanctions/PPE fictives.
- `operations.csv`: dépôts, retraits, virements et ouvertures de compte.
- `alertes_attendues.csv`: résultat attendu des règles.
- `roles_permissions.csv`: RBAC de démonstration.

## Scénario principal de démonstration

1. Connexion comme agent de Dori.
2. Consultation de la caisse Dori en zone rouge.
3. Création ou consultation du client `GCLI_001`.
4. Affichage de ses comptes locaux et d'un signal réseau indiquant un autre compte à Banfora.
5. Saisie de trois dépôts sous seuil dans la même journée.
6. Déclenchement d'une alerte de fractionnement.
7. Déclenchement d'une alerte sanction par homonymie forte.
8. Connexion comme conformité réseau.
9. Vue consolidée du client multi-caisses.
10. Décision conformité avec journal d'audit.

Deuxième scénario:

1. Retrait par procuration sur `GCLI_002`.
2. Mandat expiré.
3. CNIB expirée.
4. Alerte bloquante.

Troisième scénario:

1. Caisse Dori en zone rouge.
2. Retrait élevé lié à une activité sensible comme orpaillage.
3. Alerte zone + seuil + activité.

## Stack technique recommandée

### Frontend

Recommandé: React + Vite + TypeScript.

Pourquoi:

- rapide à développer en hackathon;
- fonctionne sur navigateur Windows et Android;
- facile à transformer en PWA;
- bonne ergonomie pour tableaux, formulaires et workflow d'alertes.

UI:

- Tailwind CSS ou CSS simple si l'équipe veut réduire les dépendances;
- composants sobres: tableau alertes, fiche client, formulaire opération, détail alerte.

### Backend

Recommandé: FastAPI + Python.

Pourquoi:

- excellent pour lire CSV, SQLite et règles métier;
- facile à documenter avec OpenAPI;
- simple à connecter plus tard à un SI existant;
- l'équipe peut réutiliser la logique de filtrage Python déjà présente dans `sentinellecoop`.

Alternative plus compacte:

- Node.js + Express si l'équipe maîtrise mieux JavaScript.

### Base locale

Recommandé: SQLite.

Pourquoi:

- léger;
- fonctionne hors ligne;
- aucun serveur lourd;
- facile à embarquer;
- adapté à un poste de caisse ou une PWA avec backend local.

### Interopérabilité

Prévoir trois formats:

- CSV pour import/export hackathon;
- JSON pour synchronisation entre caisse et réseau;
- API REST pour intégration future avec SI existants.

Endpoints MVP:

- `POST /clients/screen`
- `POST /operations`
- `GET /clients/{id}/risk-summary`
- `GET /alerts`
- `POST /alerts/{id}/decision`
- `POST /watchlists/import`
- `GET /audit-log`

### Moteur de règles

Commencer simple:

- règles Python lisibles;
- seuils dans `caisses.csv`;
- alertes dans une table SQLite;
- score explicable par règle déclenchée.

Éviter un modèle IA opaque pour le MVP. L'innovation doit venir du contexte réseau, du matching adapté aux noms ouest-africains, du mode hors ligne et de la gouvernance des données.

## Innovation à défendre

### 1. Matching local adapté

Utiliser le moteur WAPE déjà présent dans `sentinellecoop` pour mieux gérer:

- Diallo/Jallo/Djallo;
- Ouedraogo/Wedraogo;
- Mohamed/Muhammad/Mahamadou;
- inversion nom/prénom;
- alias incomplets.

### 2. Conformité réseau pseudonymisée

Un agent local ne voit pas tout le réseau. La conformité réseau voit les signaux nécessaires: client multi-comptes, score consolidé, alertes critiques, solde global, cumul.

### 3. Paramétrage par zone

Dori et Banfora n'ont pas le même risque. Les seuils et délais changent selon la zone.

### 4. Offline-first

Les listes de surveillance restent disponibles localement. Le système affiche la date de dernière mise à jour et bloque ou alerte si la liste devient obsolète.

### 5. Workflow GRC

Chaque alerte a:

- une règle;
- un score;
- un niveau;
- une décision humaine;
- une justification;
- une trace d'audit.

## Architecture cible

```text
Frontend React/PWA
        |
        v
API FastAPI locale ou réseau
        |
        +-- SQLite caisse
        +-- Moteur filtrage sanctions/PPE
        +-- Moteur règles transactions
        +-- Journal d'audit
        |
        v
Synchronisation JSON/REST
        |
        v
Référentiel conformité réseau
```

## Ordre de construction sur 72h

### Jour 1

- Charger les CSV dans SQLite.
- Créer les écrans: clients, opérations, alertes.
- Implémenter RBAC simple.
- Implémenter filtrage exact + approximatif sur listes synthétiques.

### Jour 2

- Implémenter règles: seuil, fractionnement, CNIB, procuration, zone.
- Ajouter vue client consolidée.
- Ajouter journal d'audit.
- Préparer scénarios de démo.

### Jour 3

- Polir UX.
- Ajouter export alertes.
- Tester offline ou mode liste locale.
- Répéter pitch 8 minutes.
- Écrire README technique.

## Ce qu'il faut absolument livrer

- Dataset synthétique clair.
- Démo live fluide.
- README d'installation.
- Explication des règles.
- Vue RBAC.
- Journal d'audit.
- Scénario Dori/Banfora.
- Scénario multi-comptes.
- Scénario retrait par procuration.

## Ce qu'il faut éviter

- Une solution qui dépend d'une connexion permanente.
- Une solution qui ne traite que l'ouverture de compte.
- Une solution qui ignore les transactions.
- Une solution qui donne toutes les données à tous les rôles.
- Une solution qui prétend remplacer le responsable conformité.
- Une solution sans dataset synthétique documenté.
