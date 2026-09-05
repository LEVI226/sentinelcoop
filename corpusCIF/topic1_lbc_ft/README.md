# Corpus Topic 1 - Filtrage clients et transactions LBC/FT/FP

Ce dossier est la version nettoyée et orientée solution du corpus brut `corpusCIF`.

## Objectif

Préparer une solution hackathon pour la thématique 01: filtrage automatisé des clients et des transactions, profilage LBC/FT/FP, détection d'opérations suspectes et gestion des alertes dans des SFD d'Afrique de l'Ouest.

## Structure

- `00_briefing_hackathon/`: documents source du hackathon, TDR, briefing et directive locale.
- `01_reglementation_lbc_ft_fp/`: textes BCEAO/UEMOA, loi uniforme, directive, instructions, cadre institutionnel.
- `02_giaba_evaluations_typologies/`: rapports GIABA, évaluations mutuelles, suivis, typologies et menaces.
- `03_sanctions_listes_surveillance/`: documents utiles pour sanctions ciblées et surveillance.
- `04_contexte_cif_sfd/`: contexte CIF, DigiCoop-WA+, rapports et appels liés.
- `05_jeu_donnees_synthetique/`: dictionnaire des données à simuler pour la démo.
- `06_solution_grc_technique/`: cadrage produit, architecture, gouvernance, risques et conformité.
- `99_index_manifestes/`: catalogues et index de travail.
- `source_extracts/`: textes extraits du PPTX et TDR.

## Fichiers de pilotage

- `06_solution_grc_technique/01_cadrage_topic1.md`: lecture opérationnelle de ce qui est demandé.
- `06_solution_grc_technique/02_donnees_importantes.md`: données essentielles à collecter, simuler ou dériver.
- `06_solution_grc_technique/03_blueprint_solution.md`: architecture et MVP recommandé.
- `06_solution_grc_technique/04_gouvernance_risque_conformite.md`: contrôles GRC à présenter au jury.
- `05_jeu_donnees_synthetique/dictionnaire_donnees_synthetiques.csv`: base du dataset de démo.
- `99_index_manifestes/catalogue_assets_topic1.csv`: catalogue nettoyé des documents utiles.
- `99_index_manifestes/documents_prioritaires.md`: première liste de documents à lire.

## Lecture recommandée

1. Lire `01_cadrage_topic1.md`.
2. Ouvrir `documents_prioritaires.md` pour les sources réglementaires.
3. Construire le dataset synthétique à partir du dictionnaire.
4. Développer la démo autour de trois parcours: onboarding client, transaction risquée, revue conformité.
5. Préparer le pitch avec la grille du jury: pertinence, innovation, faisabilité, impact.
