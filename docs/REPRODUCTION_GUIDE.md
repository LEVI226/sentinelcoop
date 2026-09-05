# Guide de reproduction

Ce document explique comment reprendre le projet sans dépendre d'une IA.

## Objectif du projet

Construire une solution pour le Topic 1 du Hackathon CIF DigiCoop-WA+: filtrage clients et transactions LBC/FT/FP pour des SFD et coopératives financières d'Afrique de l'Ouest.

La solution doit couvrir:

- filtrage sanctions et PPE;
- gestion des homonymies et translittérations;
- profilage KYC;
- détection d'opérations suspectes ou inhabituelles;
- alertes informatives et bloquantes;
- multi-comptes dans plusieurs caisses;
- fonctionnement faible connectivité;
- RBAC, anonymisation et audit trail.

## Prérequis

- Windows avec PowerShell.
- Python 3.11 ou plus récent.
- Accès au dossier projet: `C:\Users\ulric\Documents\cifHackathon`.
- Les documents sources du hackathon dans `Downloads`, si l'on veut reconstruire la couche Topic 1:
  - `Briefing_Regles_Candidats_Hackathons_CIF_2026-09-05-v2.0.pptx`
  - `tdr-appel-a-candidatures-global-hackathon-cif-digicoop-wa-2026.pdf`
  - `directive_no02_2015_cm_uemoa_lbc_ft-2.pdf`

## Structure importante

- `sentinellecoop/`: prototype de filtrage noms/sanctions.
- `data/`: données techniques du prototype.
- `docs/`: documentation projet.
- `corpusCIF/assets/`: corpus brut collecté.
- `corpusCIF/topic1_lbc_ft/`: corpus nettoyé et orienté Topic 1.

## Reproduire le nettoyage Topic 1

Depuis la racine du projet:

```powershell
python organize_topic1_corpus.py
```

Le script:

- copie les sources hackathon dans `corpusCIF/topic1_lbc_ft/00_briefing_hackathon/`;
- extrait le texte du briefing PPTX;
- classe les documents utiles par catégorie;
- déduplique par hash SHA-256;
- génère les catalogues CSV/JSON;
- crée le dictionnaire de données synthétiques;
- crée les règles d'alertes.

## Vérifier le script

```powershell
python -m py_compile organize_topic1_corpus.py
```

## Lire le corpus nettoyé

Commencer par:

```text
corpusCIF/topic1_lbc_ft/README.md
corpusCIF/topic1_lbc_ft/99_index_manifestes/matrice_questions_cif_reponses_solution.md
corpusCIF/topic1_lbc_ft/06_solution_grc_technique/11_spec_fonctionnelle_detaillee.md
```

Puis lire:

```text
corpusCIF/topic1_lbc_ft/06_solution_grc_technique/06_modele_reseau_multi_caisses.md
corpusCIF/topic1_lbc_ft/06_solution_grc_technique/07_rbac_anonymisation_visibilite.md
corpusCIF/topic1_lbc_ft/06_solution_grc_technique/08_workflows_operations_caisse.md
corpusCIF/topic1_lbc_ft/06_solution_grc_technique/09_risque_geographique_et_parametrage_local.md
```

## Reproduire le prototype de filtrage

Depuis la racine:

```powershell
python -m sentinellecoop.ingest
python -m sentinellecoop.benchmark
python -m sentinellecoop.screen "Amine Mohammed Oul Haq Sam Kan"
python -m sentinellecoop.screen "Salifou Ouedraogo"
```

## Règle de maintenance

Tout changement important doit être ajouté à:

- `CHANGELOG.md`
- `docs/PROMPTS_AND_DECISIONS.md`
- ce guide si la reproduction change.

Le projet doit rester explicable par ses fichiers. L'IA peut aider à produire, mais la documentation doit permettre à une personne de reprendre le travail seule.
