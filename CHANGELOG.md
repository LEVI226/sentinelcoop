# Changelog

Tous les changements notables du projet sont consignés ici.

## 2026-09-06

### Ajouté — modèle et évaluation

- `notebooks/modele_sentinellecoop.ipynb` : cycle de vie complet du modèle (problème métier → données → EDA → entraînement → évaluation → intégration edge → surveillance), 41 cellules, exécuté de bout en bout avant livraison.
- Matrice de confusion ajoutée pour la baseline et pour le modèle, moyennée sur les 5 graines, avec les cases nommées en termes métier (faux négatif = une personne sanctionnée franchit le guichet ; faux positif = un client légitime bloqué). Baseline : 0,8 non-détection et 8,0 blocages à tort ; modèle : 0,2 non-détection et 19,0 blocages à tort.
- Réserve de prévalence explicitée et **calculée depuis les données** (104 paires positives pour 320 négatives, soit ~1 pour 3) afin que l'affirmation ne puisse pas diverger du jeu réel — une première rédaction affirmait à tort que l'échantillon était équilibré.
- **Résultat mesuré, négatif et assumé** : la régression logistique à 7 variables n'améliore pas le seuil 0.88 en production. Sur 5 graines, coût baseline 24,0 ± 20,7 contre 23,0 ± 15,0 pour le modèle — un écart de −1,0 qui vaut 5 % d'un écart-type. Le modèle double les faux positifs (8,0 → 19,0) pour éviter 0,6 faux négatif et ne gagne que sur 2 graines sur 5. **Non promu** : le seuil empirique du 5 septembre est validé, pas dépassé.
- Règle alternative testée (`sim_ponderee ≥ 0.88 ET min_jeton ≥ t`) : identique à la baseline sur 4 graines sur 5, un seul faux positif évité sur la cinquième, seuil `t` instable de 0,383 à 0,754. Non retenue.
- Méthode : négatifs durs issus du **vrai référentiel ONU** (1011 entrées, 3745 libellés) plutôt que de paires artificielles ; découpage par identité avant génération des paires ; référentiel ONU partitionné entre splits ; vérification de fuite explicite à chaque exécution ; seuils choisis sur validation uniquement.
- `notebooks/README.md` : résultat principal, procédure d'exécution et limites.
- Score de risque transactionnel **non supervisé** (médiane + MAD robustes, contributions par variable) — aucune étiquette inventée, aucune précision annoncée. Artefact de 1 043 octets, inférence Python pur mesurée à 4 µs par client, soit 0,20 % du budget réseau de 512 Ko.
- Correction de reproductibilité : `hash()` sur chaîne, randomisé à chaque processus Python, remplacé par un rang déterministe. Deux exécutions successives donnent désormais des chiffres identiques.

### Ajouté

- `sentinellecoop/reseau.py` : résolution d'identité réseau (nombre de comptes qu'un même client détient à travers plusieurs caisses), à partir de la pièce d'identité (CNIB/NIP/RCCM) et, à défaut, du nom + date de naissance via le moteur de rapprochement existant (`matcher.similarite_nom`).
- Vérification intégrée : le regroupement recalculé est comparé au `global_client_id` déjà assigné dans `corpusCIF/.../dataset_demo/` (vérité terrain) — 0 écart sur les 8 clients, dont le cas KABORE AMADOU correctement détecté multi-caisses (Dori + Banfora, solde consolidé 1 405 000 FCFA, cf. `alertes_attendues.csv` ALT_003).
- Démonstration synthétique dédiée (aucune donnée réelle) validant la règle de secours nom+date de naissance quand la pièce d'identité est absente, cas non couvert par le dataset réel (chaque client y a déjà une pièce unique).
- Choix documenté : pas de modèle ML entraîné (Isolation Forest/XGBoost/SHAP écartés) — casserait le critère « zéro dépendance lourde » déjà audité comme CONFORME sur la branche `feature/security_audit` (`wazuh/contraintes-modele-leger.md`), et aucun cas réel étiqueté disponible pour un entraînement supervisé défendable.

### Documentation

- Ajout de `docs/RECETTE_HACKATHON.md` : couverture du thème 1, règles du briefing, preuves attendues et scénario de huit minutes.
- Ajout de `docs/MAINTENANCE_SANS_IA.md` : diagnostic, correction, validation, traçabilité et retour à un état connu.
- Signalement de l'incompatibilité des commandes historiques sur noms réels avec la démonstration synthétique exigée.
- Distinction entre exigences, fonctionnalités documentées et capacités effectivement testées.
- Aucune modification du moteur ni validation fonctionnelle dans cette évolution ; recette à exécuter.

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
