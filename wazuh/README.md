# Intégration Wazuh — SOC de détection CIF / LBC-FT

Le dépôt embarque, sous `wazuh/`, le socle SIEM qui exploite les décisions de
filtrage de **SentinelleCoop** (screening LBC/FT) et les remonte comme alertes
de sécurité : **sanctions ONU, PEP, seuils déclaratifs, contournements**.

```
guichet (client/transaction)
   │  nom du client
   ▼
sentinellecoop.screen ──► décision BLOQUANT / INFORMATIF / autorisé
   │
   │  wazuh/feed_wazuh.py (JSON via UDP/514)
   ▼
Wazuh manager — analysisd (règles 0500-fraude + 0501-cif)
   ▼
OpenSearch « wazuh-alerts-* » ──► Dashboard
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `0501-regles-cif-uemoa.xml` | **10 règles de filtrage CIF** (100400–100409) : sanctions ONU, PEP, seuils CENTIF, pays sous embargo, contournement, MAJ liste, SFD |
| `0500-regles-fraude-uemoa.xml` | **12 règles fraude + piste d'audit** (100200–100301) : plafonds, structing, force brute, CDB direct, rupture de chaîne WORM |
| `0502-regles-securite-conformite-audit.xml` | **19 règles SOC** (100410–100428) : sécurité SI, piste d'audit, conformité (loi 046-2024, loi uniforme 03/2023, loi 001-2025, M3/M4) |
| `feed_wazuh.py` | Connecteur : exécute `sentinellecoop.screen` et émet la décision vers Wazuh (UDP 514) |
| `sim-agent-011.sh` | Simulateur d'agent threat-intel (CIF + sécurité SI + audit + conformité, cycle de 17 cas) |
| `demo_cif.sh` | Émission syslog des 6 scénarios CIF en ligne de commande |
| `demo_soc.sh` | Émission syslog des **19 scénarios SOC** (100410–100428) |
| `query_alerts.py` | Lecture des alertes depuis OpenSearch (préfixes modifiables) |
| `liste-sanctions-onu.md` | Sources officielles (ONU, BCEAO, GIABA) + mapping de règles |
| `surveillance-equipe.md` | **Synthèse consolidée des branches de l'équipe** (topologie, apports, écarts, sujets SIEM) |
| `contraintes-modele-leger.md` | **Audit du respect du cahier des charges modèle léger** (ressources, online+offline, rapidité, connexion ≤ 512 Ko) |
| `sync_github.sh` | Audit reproductible des branches distantes (génère le rapport de synthèse `RAPPORT_SYNTHESE_BRANCHES.md`) |

## Règles CIF (1004xx) — correspondance

| Décision SentinelleCoop / événement | `event_type` | `result` / champ | Règle |
|---|---|---|---|
| Screening **BLOQUANT** (score ≥ 0.90) | `filtrage_sanctions` | `MATCH` | 100400 (12) |
| Screening **INFORMATIF** (0.80–0.90) | `filtrage_sanctions` | `POSSIBLE_MATCH` / `FUZZY` | 100403 (8) |
| Ordre/virement vers entité sanctionnée | `virement` / `transfert` | `sanctioned=yes`, `REJECTED` | 100401 (14) |
| Personne politiquement exposée | `filtrage_personnes` | `PEP_HIT` | 100402 (10) |
| Dépassement du seuil déclaratif | `declaration_threshold` | `EXCEEDED` | 100404 (6) |
| Destination pays sensible / embargo | `transfert` | `risk_country=yes` | 100405 (10) |
| Désactivation/bypass du filtrage | `desactivation_filtrage` | — | 100406 (13) |
| Actualisation de la liste ONU OK | `liste_sanctions_update` | `OK` | 100407 (5) |
| Échec d'actualisation de la liste | `liste_sanctions_update` | `FAILED` | 100409 (7) |

## Règles SOC (1004xx) — sécurité SI, piste d'audit, conformité

`0502-regles-securite-conformite-audit.xml` (groupe `soc-securite,piste-audit,conformite`).

**Sécurité du système d'information**

| Événement | `event_type` | `result` / champ | Règle |
|---|---|---|---|
| Échec d'authentification système | `auth_failure` | `FAILED` | 100410 (3) |
| Élévation de privilèges / admin | `privilege_escalation` | `GRANTED` | 100411 (11) |
| Désactivation d'un contrôle de sécurité | `security_config_change` | `DISABLED`/`REMOVED` | 100412 (12) |
| Passage en mode dégradé (données de secours) | `degraded_mode` | `ACTIVATED` | 100413 (9) |
| Référentiel périmé (> 7 j) | `referentiel_fraicheur` | `PERIME`, `age_days` ≥ 8 | 100414 (7) |
| Export/extraction massive | `export_donnees` | `volume` ≥ 5 chiffres | 100415 (10) |
| Service SI en panne | `service_down` | `DOWN`/`OUTAGE` | 100416 (8) |

**Piste d'audit**

| Événement | `event_type` | `result` | Règle |
|---|---|---|---|
| Levée de blocage sans profil habilité (art. 91) | `action_levage` | `UNHABILITATED`/`REFUSED` | 100417 (14) |
| Dégradation du journal (réécriture/backdating) | `audit_tamper` | `TIMESTAMP_BACKDATED`/`REWRITE`/`DELETE` | 100418 (11) |
| Rapport confidentiel émis (tracé art. 21/23) | `rapport_confidentiel` | `GENERATED` | 100419 (5) |

**Règles de conformité**

| Événement | `event_type` | `result` / champ | Règle | Base |
|---|---|---|---|---|
| Réévaluation PPE en retard | `ppe_evaluation` | `LATE` | 100420 (10) | art. 29 loi uniforme |
| Absence de déclaration CENTIF > 24 h | `declaration_centif` | `MISSING`, `delai_hours` | 100421 (12) | art. 58 loi 046-2024 |
| Consolidation multi-comptes ≥ 1,5 M / 7 j | `consolidation_multi_compte` | `cumul_7j` | 100422 (10) | M3 (`SEUIL_CUMUL_7J`) |
| Compte rebond bloquant | `compte_rebond` | `BLOQUANT` | 100423 (12) | M4 |
| Activation-dispersion bloquante | `activation_dispersion` | `BLOQUANT` | 100424 (12) | M4 |
| Collecte fractionnée (≥ 4 bén. / 10 j) | `fractionnement` | `INFORMATIF` | 100425 (8) | M4 |
| Opération OBNL à risque FT | `operation_obnl` | `risk=FT` | 100426 (9) | art. 118, ENR |
| Mobile money multi-comptes / espèces | `mobile_money` | `typology` | 100427 (10) | typologies ENR |
| Échec de sync différentielle différée | `sync_differentielle` | `FAILED` | 100428 (6) | M1 (offline-sync) |

## Connecteur — usage

```bash
# depuis la racine du dépôt (sentinellecoop importable) :
python3 -m pip install -e .            # si besoin
python3 wazuh/feed_wazuh.py "Mohammed Ould Abdelaziz"
python3 wazuh/feed_wazuh.py --demo
python3 wazuh/feed_wazuh.py --events demo/evenements.json
```

## Déploiement sur le manager Wazuh (conteneur Docker)

```bash
docker cp wazuh/0501-regles-cif-uemoa.xml socuemoa-wazuh.manager-1:/var/ossec/etc/rules/0501-regles-cif-uemoa.xml
docker cp wazuh/0500-regles-fraude-uemoa.xml socuemoa-wazuh.manager-1:/var/ossec/etc/rules/0500-regles-fraude-uemoa.xml
docker exec socuemoa-wazuh.manager-1 bash -c 'cd /var/ossec/bin && ./wazuh-control restart analysisd'
```

> Le `rule_dir` du manager (`etc/rules`) **n'est pas récursif** : placer les fichiers
> directement dans `/var/ossec/etc/rules/`, pas dans un sous-dossier.
> Les descriptions interpolent avec `$(champ)` (pas `${champ}`).

## Vérification

```bash
# Alertes CIF indexées (démo agent contin : sim-agent-011.sh sur 10.22.20.111) :
python3 wazuh/query_alerts.py
# ou requête directe OpenSearch sur le préfixe 1004 du rule.id
```

> Démo de référence (SOC UEMOA) : `socuemoa-agent-011` (threat intel) émet en continu
> les événements CIF (100400/401/402/403/404/405/407) et SOC (100410/411/413/418/420/422) ;
> `demo_cif.sh` et `demo_soc.sh` couvrent l'ensemble via syslog.
> Seuil informatif du moteur : `SEUIL_INFORMATIF = 0.88` (`sentinellecoop/matcher.py`, ajusté
> le 05/09/2026) — le mapping feed_wazuh (BLOQUANT ≥ 0.90 → 100400 ; INFORMATIF → 100403) est
> indépendant de cette valeur.