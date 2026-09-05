# Rapport de nettoyage du corpus

## Méthode

Le nettoyage a été fait sans supprimer le corpus brut. Les fichiers originaux restent dans `corpusCIF/assets`. La couche Topic 1 copie uniquement les documents utiles au sujet LBC/FT/FP dans des dossiers de travail.

## Actions réalisées

- Extraction texte du briefing PPTX dans `source_extracts/`.
- Copie des trois sources hackathon principales dans `00_briefing_hackathon/`.
- Sélection des documents pertinents depuis `assets/`.
- Classement par usage: réglementation, GIABA, sanctions, contexte CIF.
- Déduplication par hash SHA-256.
- Création d'un catalogue CSV et JSON.
- Création d'un dictionnaire de données synthétiques.
- Rédaction des notes de cadrage, architecture, GRC et pitch.

## Résultat

- 173 assets retenus dans la bibliothèque Topic 1.
- 3 documents source hackathon copiés.
- 123 documents GIABA retenus.
- 8 documents réglementaires BCEAO/UEMOA retenus.
- 2 documents orientés sanctions/surveillance retenus.
- 40 documents de contexte CIF/DigiCoop-WA+ retenus.

## Ce qui reste en archive brute

Le dossier brut contient encore des documents moins directement utiles: rapports monétaires, formulaires, images institutionnelles, documents administratifs et pages non prioritaires. Ils sont conservés pour ne pas perdre de contexte, mais ils ne doivent pas guider le MVP.

## Limites

- Les PDF ne sont pas tous convertis en texte exploitable car les bibliothèques Python PDF ne sont pas installées dans l'environnement courant.
- Les anciens dossiers `pages/` et `raw_html/` du crawl ne sont plus visibles dans `corpusCIF` au moment de ce nettoyage. La bibliothèque Topic 1 repose donc principalement sur les assets PDF/images disponibles et les documents locaux.
- Certains rapports GIABA sont en anglais ou portugais; il faudra privilégier les rapports pays UEMOA et les typologies transversales pour le pitch.

## Nettoyage recommandé avant développement

- Ne pas supprimer `assets/`.
- Utiliser `topic1_lbc_ft/` comme corpus de travail.
- Lire en priorité `documents_prioritaires.md`.
- Convertir les PDF prioritaires en texte si un outil comme `pypdf`, `pdfplumber` ou `pdftotext` devient disponible.
- Garder toutes les données de démo synthétiques et versionnées.
