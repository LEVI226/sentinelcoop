# Changelog

Tous les changements notables du projet sont consignés ici.

## 2026-09-05

### Ajouté

- Constitution d'un corpus CIF/LBC-FT dans `corpusCIF/`.
- Création d'une couche de travail nettoyée: `corpusCIF/topic1_lbc_ft/`.
- Classement des sources Topic 1 par familles:
  - briefing hackathon;
  - réglementation BCEAO/UEMOA;
  - évaluations et typologies GIABA;
  - sanctions et surveillance;
  - contexte CIF/SFD;
  - données synthétiques;
  - solution GRC et technique.
- Ajout du script `organize_topic1_corpus.py`.
- Ajout du catalogue des assets Topic 1:
  - `catalogue_assets_topic1.csv`;
  - `catalogue_assets_topic1.json`.
- Ajout du dictionnaire de données synthétiques.
- Ajout du modèle de données réseau CIF.
- Ajout du catalogue de règles d'alertes.
- Ajout d'une matrice reliant les questions terrain CIF aux réponses solution.
- Ajout d'une spécification fonctionnelle détaillée Topic 1.
- Ajout d'un guide de reproduction.
- Ajout d'un journal des prompts et décisions.

### Clarifié

- Le Topic 1 ne couvre pas seulement un filtrage nom-liste.
- La solution doit traiter le contexte réseau CIF: plusieurs caisses, plusieurs comptes, visibilité différenciée et consolidation conformité.
- Le MVP doit garder la décision humaine dans le workflow conformité.
- La démo doit utiliser uniquement des données synthétiques.

### Nettoyé

- Déduplication des documents utiles par hash SHA-256.
- Séparation entre corpus brut et corpus de travail.
- Classement non destructif des documents pour éviter de perdre les sources originales.

### Limites connues

- Les PDF ne sont pas tous convertis en texte exploitable dans l'environnement courant.
- Les anciens dossiers `pages/` et `raw_html/` du crawl ne sont plus visibles dans `corpusCIF`.
- Le corpus brut contient encore des fichiers non prioritaires conservés en archive.
