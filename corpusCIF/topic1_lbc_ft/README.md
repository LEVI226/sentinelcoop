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
- `06_solution_grc_technique/06_modele_reseau_multi_caisses.md`: modèle client/compte/caisse pour le réseau CIF.
- `06_solution_grc_technique/07_rbac_anonymisation_visibilite.md`: rôles, habilitations, pseudonymisation et visibilité différenciée.
- `06_solution_grc_technique/08_workflows_operations_caisse.md`: création compte, dépôt, retrait, procuration, carnet et formulaire.
- `06_solution_grc_technique/09_risque_geographique_et_parametrage_local.md`: paramétrage par zone comme Dori/Banfora.
- `06_solution_grc_technique/10_backlog_mvp_topic1.md`: backlog fonctionnel pour construire vite.
- `06_solution_grc_technique/11_spec_fonctionnelle_detaillee.md`: exigences fonctionnelles détaillées.
- `06_solution_grc_technique/12_roadmap_stack_dataset.md`: stack technique, roadmap 72h et utilisation du dataset.
- `06_solution_grc_technique/13_architecture_bancaire_cible.md`: architecture bancaire cible pour réseau CIF à forte volumétrie.
- `06_solution_grc_technique/14_schema_mvp_hackathon.md`: schéma MVP réaliste à livrer en 72h.
- `06_solution_grc_technique/15_matrice_choix_stack.csv`: comparaison des choix techniques.
- `05_jeu_donnees_synthetique/dictionnaire_donnees_synthetiques.csv`: base du dataset de démo.
- `05_jeu_donnees_synthetique/modele_donnees_reseau_cif.csv`: modèle de données réseau multi-caisses.
- `05_jeu_donnees_synthetique/catalogue_regles_alertes_topic1.csv`: règles d'alertes à implémenter.
- `05_jeu_donnees_synthetique/dataset_demo/`: CSV synthétiques prêts pour prototype.
- `99_index_manifestes/catalogue_assets_topic1.csv`: catalogue nettoyé des documents utiles.
- `99_index_manifestes/documents_prioritaires.md`: première liste de documents à lire.
- `99_index_manifestes/matrice_questions_cif_reponses_solution.md`: correspondance entre les questions CIF et la réponse solution.

## Lecture recommandée

1. Lire `01_cadrage_topic1.md`.
2. Ouvrir `documents_prioritaires.md` pour les sources réglementaires.
3. Charger le dataset synthétique depuis `dataset_demo/`.
4. Lire `matrice_questions_cif_reponses_solution.md` pour couvrir les remarques terrain.
5. Développer la démo autour de quatre parcours: onboarding client, transaction risquée, retrait par procuration, revue conformité réseau.
6. Préparer le pitch avec la grille du jury: pertinence, innovation, faisabilité, impact.
