# Prompts et décisions

Ce fichier garde la mémoire des demandes formulées pendant le projet et des décisions prises pour que le travail reste reproductible sans IA.

## Principe

Ne pas construire un projet que seule l'IA peut expliquer. Chaque choix important doit laisser une trace humaine: objectif, décision, fichiers produits et commande de reproduction.

## Prompt 1 - Constituer le corpus CIF

### Demande

Constituer un corpus complet à partir de `https://www.cif-ao.org/` dans `C:\Users\ulric\Documents\cifHackathon\corpusCIF`.

### Décisions

- Utiliser le sitemap du site CIF pour découvrir les pages.
- Sauvegarder les pages, documents et médias internes.
- Créer un index JSONL.
- Garder les assets bruts pour éviter toute perte de source.

### Résultat

- Dossier `corpusCIF/`.
- Assets bruts dans `corpusCIF/assets/`.

## Prompt 2 - Ajouter BCEAO, GIABA et directive UEMOA

### Demande

Compléter le corpus pour travailler sur le topic LCF/LBC-FT du hackathon avec:

- directive no 02/2015/CM/UEMOA;
- BCEAO;
- GIABA;
- loi uniforme LBC/FT/FP.

### Décisions

- Ajouter les sources publiques BCEAO et GIABA au corpus.
- Copier le PDF local `directive_no02_2015_cm_uemoa_lbc_ft-2.pdf`.
- Garder les documents réglementaires et rapports GIABA dans les assets.

### Résultat

- Corpus enrichi dans `corpusCIF/assets/`.

## Prompt 3 - Nettoyer pour Topic 1

### Demande

Regarder ce qui est demandé aux équipes Topic 1, présenter mieux le corpus, identifier les données importantes et nettoyer pour une solution technique et GRC de qualité.

### Décisions

- Créer une couche spécifique `corpusCIF/topic1_lbc_ft/`.
- Séparer les documents par usage métier.
- Produire des notes actionnables plutôt qu'un simple inventaire.
- Ajouter un dictionnaire de données synthétiques.
- Ajouter un blueprint technique et une note GRC.

### Résultat

- `01_cadrage_topic1.md`
- `02_donnees_importantes.md`
- `03_blueprint_solution.md`
- `04_gouvernance_risque_conformite.md`
- `05_plan_pitch_8_minutes.md`
- `dictionnaire_donnees_synthetiques.csv`

## Prompt 4 - Intégrer les retours terrain CIF

### Demande

Prendre en compte les sujets remontés par les interlocuteurs CIF:

- réseau composé de plusieurs structures;
- client avec plusieurs comptes dans différentes caisses;
- dépôts, retraits, création de compte;
- retrait par procuration;
- seuils et justification des fonds;
- motifs, produits, personnes physiques et morales;
- flux financiers;
- KYC;
- risques locaux selon la ville, comme Dori et Banfora;
- délai de filtrage;
- interopérabilité réseau;
- anonymisation;
- RBAC;
- validité CNIB;
- carnet caisse;
- formulaire de retrait.

### Décisions

- Modéliser la conformité au niveau réseau, pas seulement au niveau compte.
- Introduire `global_client_id` pseudonymisé pour consolider les risques sans exposer toute l'identité.
- Distinguer visibilité caisse, conformité caisse, conformité réseau et audit.
- Ajouter des règles de zones à risque.
- Ajouter des workflows de caisse détaillés.
- Ajouter des règles d'alerte prêtes à implémenter.

### Résultat

- `06_modele_reseau_multi_caisses.md`
- `07_rbac_anonymisation_visibilite.md`
- `08_workflows_operations_caisse.md`
- `09_risque_geographique_et_parametrage_local.md`
- `10_backlog_mvp_topic1.md`
- `11_spec_fonctionnelle_detaillee.md`
- `modele_donnees_reseau_cif.csv`
- `catalogue_regles_alertes_topic1.csv`
- `matrice_questions_cif_reponses_solution.md`

## Prompt 5 - Documenter pour survivre sans IA

### Demande

Créer une documentation étape par étape, un changelog et garder les prompts utilisés pour pouvoir faire vivre le projet sans IA.

### Décisions

- Ajouter un guide de reproduction.
- Ajouter un changelog à la racine.
- Ajouter ce journal des prompts et décisions.
- Poser une règle de maintenance documentaire.

### Résultat

- `docs/REPRODUCTION_GUIDE.md`
- `CHANGELOG.md`
- `docs/PROMPTS_AND_DECISIONS.md`

## Commande de reproduction principale

```powershell
python organize_topic1_corpus.py
```

## Commande de vérification

```powershell
python -m py_compile organize_topic1_corpus.py
```
