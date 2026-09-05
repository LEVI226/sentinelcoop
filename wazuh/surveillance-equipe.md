# Surveillance Équipe — Synthèse des branches SentinelleCoop

> Document de synthèse consolidé pour le suivi des travaux de l'équipe depuis le pôle SOC (intégration Wazuh).
> Référence : branche `feature/security_audit` (socle SIEM `wazuh/`).
> Version du document : 2026-09-05.

---

## 1. Rappel du contexte

Le dépôt publique `LEVI226/sentinelcoop` est développé en parallèle par plusieurs pôles
(moteur de filtrage, interface guichet, synchronisation hors-ligne, sécurité/audit).
Le pôle SOC exploite, dans la branche `feature/security_audit`, le socle SIEM `wazuh/`
(règles de détection 0500/0501/0502, connecteur `feed_wazuh.py`, simulations
`sim-agent-011.sh`, démos `demo_cif.sh`/`demo_soc.sh`, requêtes OpenSearch `query_alerts.py`).

Ce document est une **photographie consolidée** de l'état des branches au 2026-09-05,
afin de :
1. connaitre les apports de chaque pôle ;
2. repérer les composants producteurs d'événements à brancher sur le SIEM ;
3. signaler les écarts de synchronisation à corriger en réunion d'équipe.

---

## 2. Topologie Git constatée

| Branche distante | HEAD | Rôle |
|---|---|---|
| `main` | `cc64d41` | Baseline : démo + moteur Python M1/M2 + dossier de soumission |
| `feature/security_audit` | `3204360` | **Pôle SOC** : intégration SIEM Wazuh (propulsée depuis ce document) |
| `feature/moteur-ia` | `d6e125a` | M3/M4 (verdicts), dataset synthétique, corpus CIF Topic 1 |
| `feature/ux-guichet` | `cd4e5a2` | Poste guichet SPA + prototype CIF Guard + modes dégradés |
| `offline_synch` | `cc64d41` | Placeholder (identique à `main` — sync signée documentée, non implémentée) |

Notes de topologie :
- `main`, `offline_synch` et l'ancien sommet de `security_audit` partageaient le même
  commit `cc64d41` ; `feature/moteur-ia` et `feature/ux-guichet` partagent une lignée
  commune (`88e11a3`) divergée de la baseline.
- La branche locale `feature/security_audit` est en avance sur son origine : elle porte
  le dossier `wazuh/` (commits `ea7c7e3`, `e863012`, `3204360`).

---

## 3. Détail par branche

### 3.1 `main` — baseline (HEAD `cc64d41` « docs: Ajout d'un guide Git pour l'équipe »)

**Composants clés**

| Chemin | Rôle |
|---|---|
| `sentinellecoop/ingest.py` | Ingestion du référentiel de sanctions ONU (XML consolidé) en objets normalisés |
| `sentinellecoop/matcher.py` | Rapprochement (distance de chaînes + rareté, double seuil BLOQUANT/INFORMATIF) |
| `sentinellecoop/phonetics.py` | Encodage phonétique ouest-africain (WAPE) |
| `sentinellecoop/screen.py` | Filtrage complet d'un client à l'entrée en relation, entièrement en local (hors-ligne) |
| `sentinellecoop/benchmark.py` | Mesure de performance/qualité du moteur sur le jeu de variantes |
| `build.py` | Génération des `.docx` de soumission (pandoc + marges/police) |
| `data/` | `un_consolidated.xml` (liste ONU réelle), `variantes_noms_ao.csv` (99 paires), `enr_bcft.txt`, `benchmark_resultats.txt` |
| `demo/` | Démo web monopage (app.js, index.html, styles.css, test-demo.js) |
| `docs/` | PLAN.md, PRD.md, SPECS.md |
| `soumission/` | Dossier de livraison hackathon (fiches, note, profils, mkdocx.js, prototype.zip) |

**Point de vue SIEM** : aucune instrumentation SIEM sur cette branche ; le moteur produit
des décisions (BLOQUANT / INFORMATIF / autorisé) et des alertes dans `demo/app.js`, sans
émission d'événements vers un SIEM.

---

### 3.2 `feature/moteur-ia` — HEAD `d6e125a` « feat: ajout corpus CIF et script d'organisation du corpus topic 1 »

**Apports vs baseline** : `corpusCIF/`, `organize_topic1_corpus.py`, enrichissement de
`data/` (clients, comptes, transactions, sanctions_demo, ppe_internes, scenarios,
`verdicts_demo.json`), `docs/ARCHITECTURE.md`, nouveaux modules `sentinellecoop/`.

**Composants clés (nouveaux/évolués)**

| Chemin | Rôle |
|---|---|
| `sentinellecoop/dataset.py` | Charge le dataset synthétique (clients/comptes/transactions CSV) en objets Python |
| `sentinellecoop/verdicts.py` | Moteur M3/M4 : consolidation multi-comptes, fractionnement, compte rebond, collecte fractionnée, activation-dispersion (seuils documentés) |
| `sentinellecoop/exporter_demo.py` | Exporte référentiel + verdicts + seuils en `data/verdicts_demo.json` (interface sans serveur API) |
| `sentinellecoop/referentiel_demo.py` | Référentiels complémentaires : sanctions de démo (`sanctions_demo.csv`) + PPE internes (`ppe_internes.csv`) |
| `sentinellecoop/verifier_dataset.py` | Test de non-régression : chaque client du dataset doit produire le verdict attendu |
| `sentinellecoop/matcher.py` (évolué) | Seuil informatif relevé 0.80 → **0.88** |
| `corpusCIF/topic1_lbc_ft/` | Corpus documentaire structuré du Topic 1 (briefing, réglementation, GIABA, sanctions, dataset, solution GRC, index/manifestes, extraits sources) |
| `docs/ARCHITECTURE.md` | Vue système M1-M5 + répartition par branche du travail parallèle |

**Point de vue SIEM** :
- Événements **conformité LBC/FT** potentiels : consolidation ≥ 1,5 M XOF/7 j, fractionnement
  de dépôt, compte rebond, collecte fractionnée FT, activation-dispersion → règles
  **100422-100425** de `wazuh/0502`.
- Événements **filtrage** : hits BLOQUANT/INFORMATIF (M2) → règles **100400/100403**,
  hits PPE (M1) → **100402**.
- Événement **fraîcheur** : `fraicheur()` dans `screen.py` (âge du référentiel) →
  règle **100414** (art. 89).
- **Aucune émission SIEM dans la branche** : les événements sont calculés mais non émis.

---

### 3.3 `feature/ux-guichet` — HEAD `cd4e5a2` « feat(ux): add improved CIF Guard prototype (SPA) »

**Apports vs baseline** : `guichet/` (poste guichet SPA), `prototype-ux/`, socle partagé
M3/M4 identique à moteur-ia (dataset, `verdicts.py`, exporteurs).

**Composants clés (nouveaux/évolués)**

| Chemin | Rôle |
|---|---|
| `guichet/index.html` | Poste guichet SPA : onglets Filtrage / Transactions / Alertes / Audit, indicateur de fraîcheur, bannière mode dégradé |
| `guichet/app.js` | Filtrage temps réel pendant la saisie, affichage verdicts M3/M4 précalculés, journal local, mode dégradé à 3 niveaux |
| `guichet/moteur.js` | Portage JavaScript documenté de `phonetics.py`/`matcher.py` (WAPE, distances, seuils) — filtrage offline navigateur |
| `guichet/moteur.test.mjs` | Test de parité JS/Python sur les 99 variantes attestées (`variantes_noms_ao.csv`) |
| `guichet/build_secours.js` | Génération de `donnees_secours.js` (copie embarquée de `verdicts_demo.json` pour mode file://) |
| `guichet/styles.css` | Styles du poste guichet (direction visuelle par statut d'alerte) |
| `prototype-ux/index.html` | Prototype SPA « CIF Guard » amélioré (1708 lignes), cible de refonte UX |

**Point de vue SIEM** :
- **Mode dégradé activé** (bascule vers données de secours embarquées) → règle **100413**.
- **Référentiel périmé > 7 j** (art. 89) → règle **100414**.
- **Journal / piste d'audit local** du poste (alertes, levées, filtrages) → règles
  **100417-100419** (`avertissement_levage_non_habilite`, `rupture_audit_worm`...).
- **Filtrage nominal temps réel** → événements `filtrage_sanctions` / `filtrage_personnes`
  → règles **100400-100403**.
- **Aucune émission SIEM dans la branche** : les états significatifs sont présents mais non émis.

---

### 3.4 `offline_synch` — HEAD `cc64d41` (identique à `main`)

- **Aucun code propre** : la sync différentielle **signée** des référentiels (couche M1,
  décrite dans `docs/ARCHITECTURE.md`) est documentée mais **non implémentée**.
- Placeholder de travail pour le pôle synchronisation.

**Point de vue SIEM** : une fois implémentée, surveiller le type d'événement de mise à jour
de la liste de sanctions : succès → règle **100407** (`liste_sanctions_update`), échec →
règle **100409** (`liste_sanctions_update_echec`).

---

### 3.5 `feature/security_audit` — `ea7c7e3` → `3204360` (pôle SOC, ce socle)

**Apport** : dossier `wazuh/` complet.

| Chemin | Rôle |
|---|---|
| `wazuh/0500-regles-fraude-uemoa.xml` | 12 règles fraude + piste d'audit (IDs 100200-100301) : plafonds, structing, force brute, CDB, rupture chaîne WORM |
| `wazuh/0501-regles-cif-uemoa.xml` | 10 règles CIF (100400-100409) : sanctions ONU, PEP, seuils CENTIF, pays sous embargo, contournement, MAJ liste, SFD |
| `wazuh/0502-regles-securite-conformite-audit.xml` | 19 règles SOC (100410-100428) : sécurité SI, piste d'audit, conformité (lois 046-2024, uniforme 03/2023, 001-2025, M3/M4) |
| `wazuh/feed_wazuh.py` | Connecteur : exécute `sentinellecoop.screen` et émet la décision vers Wazuh (UDP 514) |
| `wazuh/sim-agent-011.sh` | Simulateur d'agent threat-intel (17 cas : CIF + sécurité SI + audit + conformité) |
| `wazuh/demo_cif.sh` | Émission syslog des 6 scénarios CIF en CLI |
| `wazuh/demo_soc.sh` | Émission syslog des 19 scénarios SOC (100410-100428) |
| `wazuh/query_alerts.py` | Lecture des alertes depuis OpenSearch (préfixes configurables) |
| `wazuh/liste-sanctions-onu.md` | Sources officielles (ONU, BCEAO, GIABA) + mapping règles |
| `wazuh/sync_github.sh` | Audit reproductible des branches (génère ce rapport de synthèse) |

---

## 4. Synthèse transversale

| Branche | HEAD | Apport principal | Couche SIEM |
|---|---|---|---|
| `main` | `cc64d41` | Baseline démo + moteur Python M1/M2 + soumission | Aucune |
| `feature/moteur-ia` | `d6e125a` | M3/M4 (verdicts), dataset, export JSON, corpus CIF | Aucune (calculs prêts) |
| `feature/ux-guichet` | `cd4e5a2` | Poste guichet SPA + prototype CIF Guard + modes dégradés | Aucune (états siem-significatifs prêts) |
| `offline_synch` | `cc64d41` | Placeholder (identique à `main`) | Aucune |
| `feature/security_audit` | `3204360` | `wazuh/` : règles 1002xx-1004xx, connecteur UDP, simulations, query OpenSearch | **Intégration SIEM complète** |

### Écarts de synchronisation à signaler à l'équipe

1. **`offline_synch` n'a aucun code propre** : la synchro signée M1 reste documentée mais
   non implémentée (branche placeholder).
2. **`moteur-ia` et `ux-guichet` n'ont pas intégré `wazuh/`** ; inversement, `security_audit`
   ne voit ni les verdicts M3/M4 ni le guichet. **L'intégration bout-en-bout reste à faire** :
   `guichet → screen/verdicts → feed_wazuh.py → Wazuh`.
3. La branche `feature/securite-audit` (ancien nom) a été **supprimée/renommée** en
   `feature/security_audit` lors de la restructuration — depuis le SOC nous travaillons sur le nouveau nom.

---

## 5. Sujets SIEM à surveiller dès l'intégration

- **Filtrage en temps réel au guichet** (100400-100405, 100402) : cœur de la valeur démo.
- **Fraude & structing** (100200-100301) : complémentaires aux alertes M3/M4.
- **Audit & conformité** (100417-100424) : démonstration de conformité aux art. 21/23/29,
  lois 046-2024 et uniforme 03/2023.
- **Sécurité SI** (100410-100416) : mode dégradé, fraîcheur référentiel, export massif —
  directement vérifiables dans le comportement du poste guichet.

---

## 6. Recommandations

1. **Branchage SIEM** : faire émettre à `verdicts.py` et au poste guichet des événements
   syslog consomptibles par les règles 0500/0501/0502 (le connecteur `feed_wazuh.py` attend
   exactement les champs documentés dans `wazuh/README.md`).
2. **Référentiel de test commun** : activer les seuils M3/M4 (`data/verdicts_demo.json`,
   `SEUIL_CUMUL_7J=1 500 000`, `SEUIL_INFORMATIF=0.88`) pour que le SOC corrèle alertes
   SIEM et verdicts guichet.
3. **Synchronisation** : implémenter la sync signée des listes sur `offline_synch` pour
   couvrir les règles 100407/100409.
4. **Relance de l'audit** : régénérer cette synthèse à tout moment via
   `bash wazuh/sync_github.sh --rapport`.

---

*Auteur : PREDATOR (SOC UEMOA). Document généré pour le suivi de l'équipe hackathon CIF.*