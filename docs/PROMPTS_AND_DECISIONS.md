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

## 2026-09-06 — Règles et autonomie de maintenance

Résumé de la demande utilisateur (pas une transcription intégrale) : respecter toutes les règles du hackathon CIF thème 1 et documenter les étapes, changements et prompts pour maintenir le projet sans IA.

Extrait exact : « Ne construis pas avec l’IA quelque chose que seule l'IA serait capable de t’expliquer ensuite. »

Décisions : compléter les documents existants ; créer une recette traçable ; signaler l'usage historique de noms réels ; ne pas présenter une documentation comme une validation du logiciel. Sources : demande, briefing déjà examiné, README et guides locaux.

Fichiers : docs/RECETTE_HACKATHON.md, docs/MAINTENANCE_SANS_IA.md, README.md, docs/REPRODUCTION_GUIDE.md, CHANGELOG.md et ce journal.

Vérification : présence des fichiers et liens documentaires ; aucun test fonctionnel exécuté. Les anciens prompts absents ne sont pas reconstitués ni inventés.

### Modèle pour chaque prochaine intervention IA

Date / membre / outil et modèle si connus / prompt exact expurgé des secrets / pièces jointes et versions / changements retenus ou rejetés / justification humaine / fichiers / tests et résultats / commit après revue. Ne jamais archiver de secrets ni de données personnelles dans ce journal.

## 2026-09-06 — Résolution d'identité réseau (NIP/CNIB) et refus d'un modèle ML entraîné

Membre : Ulric. Outil : Claude Code (Sonnet 5).

Résumé de la demande (pas une transcription intégrale) : l'utilisateur a partagé un notebook AML externe (XGBoost/LightGBM/SHAP/NetworkX/protocole A2A) et un document d'architecture externe (« CIF-NEXUS ») proposant plusieurs modèles ML (Isolation Forest, classification de risque, graph anomaly detection), puis a demandé de créer un dataset clair correspondant au flux client → comptes/solde global → filtrage PPE/sanctions → opération contrôlée → alerte persistante → décision humaine et audit, de « commencer l'entraînement du modèle » et de livrer aux équipes. Demande explicite additionnelle : détecter le nombre de comptes qu'un même client possède dans le réseau via le numéro NIP de sa CNIB.

Décisions :
- Ne pas adopter le stack ML du notebook externe ni des modèles proposés (Isolation Forest, XGBoost, SHAP, NetworkX) : ça romprait le critère « zéro dépendance lourde » déjà audité CONFORME par la branche `feature/security_audit` (`wazuh/contraintes-modele-leger.md`), et aucun cas réel étiqueté n'est disponible pour un entraînement supervisé défendable devant un jury.
- Constater que le dataset `corpusCIF/topic1_lbc_ft/05_jeu_donnees_synthetique/dataset_demo/` couvre déjà la quasi-totalité des familles de données proposées par le document externe (KYC, comptes multi-caisses, watchlist sanctions/PPE, bénéficiaires effectifs, alertes labellisées) sauf la résolution d'identité réseau par pièce d'identité.
- Construire `sentinellecoop/reseau.py` : regroupement par numéro de pièce (CNIB/NIP/RCCM), puis à défaut par nom + date de naissance en réutilisant le moteur de rapprochement existant (`matcher.similarite_nom`) plutôt qu'un second algorithme.
- Vérifier le regroupement recalculé contre le `global_client_id` déjà assigné dans le CSV (vérité terrain), à la manière de `verifier_dataset.py`.
- Ajouter un scénario synthétique dédié pour exercer la règle de secours (nom + naissance, sans pièce), absente du dataset réel où chaque client a déjà une pièce unique.

Fichiers : `sentinellecoop/reseau.py` (créé), `CHANGELOG.md`, ce journal.

Tests et résultats : `python -m sentinellecoop.reseau` → 8 identités résolues, 0 écart vs `global_client_id`, cas multi-caisses KABORE AMADOU (Dori + Banfora, solde consolidé 1 405 000 FCFA) correctement détecté, démonstration de fusion sans pièce validée (« OK »). Code de sortie 0.

Point ouvert, à trancher en équipe et non par cette session seule : si un modèle ML léger (ex. score statistique sans dépendance, ou scikit-learn en dépendance unique assumée) doit être ajouté plus tard, ça doit repasser par une décision d'équipe explicite vu l'impact sur l'audit de conformité déjà écrit.

## 2026-09-06 — Notebook du cycle de vie du modèle, et résultat négatif assumé

Membre : Ulric. Outil : Claude Code (Opus 5).

Résumé de la demande : repartir sur une base saine ; dire ce qui doit être fait pour le modèle, le dataset à constituer et l'intégration ; livrer un notebook complet et clair pour un modèle optimisé, léger, edge computing. Consigne explicite de l'utilisateur : « ne mens pas ». Choix de l'utilisateur en réponse aux questions de cadrage : notebook à la fois pipeline et narratif ; numpy + pandas + matplotlib autorisés dans le notebook ; périmètre « noms + score de risque transaction ».

Décisions :
- Périmètre transaction traité en **non supervisé** et non en classification supervisée, malgré la formulation de la demande : les seules étiquettes disponibles seraient produites par nos propres règles (`verdicts.py`), un modèle entraîné dessus les réapprendrait avec une couche d'opacité en plus. Écart au choix de l'utilisateur assumé et expliqué, pas silencieux.
- Négatifs durs construits à partir du **vrai référentiel ONU** plutôt que de paires artificielles : c'est la seule façon de mesurer les faux positifs réellement rencontrés au guichet.
- Découpage par identité avant génération des paires, référentiel ONU partitionné entre splits, vérification de fuite affichée à chaque exécution, seuils choisis sur validation uniquement.
- Évaluation sur 5 graines : une conclusion tirée d'un seul tirage sur ~430 paires n'aurait pas été fiable.
- **Le modèle n'est pas promu.** Il ne bat pas le seuil 0.88 de façon distinguable du bruit. La règle alternative `min_jeton` n'est pas retenue non plus. Ce résultat négatif est le livrable, pas un échec à masquer.
- Le générateur du notebook n'est pas versionné : le `.ipynb` est la seule source de vérité, pour éviter deux fichiers à maintenir en parallèle.

Fichiers : `notebooks/modele_sentinellecoop.ipynb` (créé), `notebooks/README.md` (créé), `CHANGELOG.md`, ce journal.

Tests et résultats : les 18 cellules de code exécutées dans l'ordre, sans erreur, en ~1 minute ; chaque chiffre cité dans le markdown vérifié contre la sortie réelle. Bug de reproductibilité corrigé en cours de route (`hash()` sur chaîne randomisé par processus) — deux exécutions successives donnent désormais des résultats identiques.

Décision humaine restant à prendre : le dossier `ia_delivery/` (modèle logistique antérieur, non suivi par git, `promotion_observed: false`) n'a pas été modifié. L'équipe doit décider s'il est committé avec ses limites documentées, corrigé, ou retiré.
