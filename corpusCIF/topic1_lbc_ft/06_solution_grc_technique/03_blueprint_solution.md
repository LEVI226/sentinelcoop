# Blueprint solution technique

## MVP recommandé

Construire un prototype web léger ou desktop local qui tourne sur Windows et reste utilisable sur Android via navigateur local ou PWA.

Parcours à démontrer:

- Ajouter ou importer un client fictif.
- Lancer le filtrage sanctions/PPE avec gestion des homonymies.
- Enregistrer une transaction.
- Générer une alerte transactionnelle.
- Revoir l'alerte dans une file conformité.
- Justifier la décision dans un journal d'audit.

## Modules

### 1. Ingestion et normalisation

- Nettoyage des noms.
- Suppression accents et ponctuation.
- Gestion alias et ordre prénom/nom.
- Normalisation pays, dates et montants.

### 2. Filtrage sanctions et PPE

- Recherche exacte.
- Recherche approximative par similarité.
- Pondération par date de naissance, pays, alias et type de personne.
- Niveau bloquant si score élevé sur une liste de sanctions.
- Niveau informatif ou revue renforcée pour PPE.

### 3. Détection transactionnelle

- Règles simples et explicables.
- Seuils configurables.
- Détection de fractionnement.
- Cumul par client, compte, canal et période.
- Comparaison au comportement habituel.

### 4. File d'alertes

- Alerte, motif, niveau, score, règle déclenchée.
- Statut: nouvelle, en revue, faux positif, escalade, déclaration.
- Commentaire obligatoire pour clôture.
- Journal horodaté.

### 5. Synchronisation faible connectivité

- Cache local des listes.
- Horodatage de la dernière mise à jour.
- Import manuel CSV/JSON si Internet absent.
- File locale des décisions à synchroniser.

## Stack conseillée

- Frontend: HTML/CSS/JavaScript ou React si déjà prêt.
- Backend local: Python FastAPI, Node/Express, ou SQLite direct selon l'équipe.
- Base: SQLite pour la démo.
- Dataset: CSV synthétique versionné.
- Matching noms: normalisation + distance de Levenshtein/Jaro-Winkler si disponible, sinon score maison documenté.

## Ce qu'il faut montrer au jury

- Les règles sont lisibles et modifiables.
- Le système distingue alerte bloquante et alerte informative.
- Le responsable conformité garde la décision finale.
- La solution garde une piste d'audit.
- La solution fonctionne sans données réelles.
- La solution reste utilisable avec faible connectivité.

## Risques techniques à anticiper

- Trop de faux positifs si le matching nom est naïf.
- Démo lente si les fichiers sanctions sont trop volumineux.
- Pitch faible si les règles ne sont pas explicables.
- Perte de points si le README n'explique pas les données synthétiques.
- Perte de crédibilité si la solution suppose un SI bancaire complet absent des SFD.
