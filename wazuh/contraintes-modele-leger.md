# Surveillance des contraintes — Modèle léger SentinelleCoop

> Audit de conformité des travaux de l'équipe (toutes branches) par rapport au
> cahier des charges du modèle de détection fraude / blanchiment :
> 1. Modèle **léger**, non gourmand en ressources matérielles ;
> 2. Connexion **mixte online + offline** ;
> 3. Requêtes **rapides** ;
> 4. Connexion **≤ 512 Ko maxi** par payload réseau.
>
> Référence : branche `feature/security_audit` (socle SIEM `wazuh/`).
> Version du document : 2026-09-05. Régénérable/actualisable à chaque audit.

---

## 0. Périmètre audité (état des branches à l'audit)

| Branche | HEAD | Contenu audité |
|---|---|---|
| `main` | `df2558c` | moteur M1/M2, demo, `.github/workflows/apisec-scan.yml` (nouveau) |
| `feature/moteur-ia` | `d6e125a` | M3/M4 (`verdicts.py`), dataset synthétique, corpusCIF |
| `feature/ux-guichet` | `cd4e5a2` | poste guichet SPA + mode dégradé, `prototype-ux/` |
| `offline_synch` | `cc64d41` | **placeholder, zéro code** |
| `feature/security_audit` | `eb0a966` | socle SIEM `wazuh/` (règles, connecteur UDP, scripts) |

---

## 1. Modèle léger / ressources matérielles — **CONFORME**

**Constat** : le moteur est 100 % standard-library Python 3.11+.
- Aucune dépendance tierce : ni tensorflow/pytorch/pandas/sklearn/numpy, ni `requests`.
  Vérifié sur `matcher.py`, `phonetics.py`, `screen.py`, `ingest.py`, `dataset.py`,
  `verdicts.py`, `exporter_demo.py`, `referentiel_demo.py`, `verifier_dataset.py`.
- Aucun `requirements.txt`, `pyproject.toml`, `setup.py` dans tout l'arbre.
- Taille du code moteur : **~54 Ko** (matcher 7,5 Ko + phonetics 8,6 Ko + verdicts 11,8 Ko
  + benchmark 6,3 Ko + ingest 3,6 Ko + screen 3,0 Ko + dataset 3,5 Ko + exporter 4,6 Ko
  + referentiel 2,9 Ko + verifier 2,7 Ko).
- Portage guichet : `guichet/moteur.js` (7,5 Ko) réimplémente WAPE + Jaro-Winkler +
  Damerau-Levenshtein en **pure JS, zéro dépendance** ; fonctionne en `file://`.
- Surface d'imports pour `screen.py` = 11 modules stdlib, pour `verdicts.py` = 9.
- Source : `soumission/05-PROTOTYPE/README.md` — « Aucune dépendance externe… doit
  s'installer sur un poste de guichet modeste ».

**Points de vigilance** :
- `.github/workflows/apisec-scan.yml` (droits : `security-events: write`) exécute un
  conteneur **tiers APIsec.ai** sur chaque push/PR `main` + cron hebdo `16 6 * * 2`.
  Impact matériel nul sur le moteur, mais dépendance extérieure à auditer (déjà noté).

---

## 2. Connexion mixte online + offline — **PARTIEL (volet offline OK, volet online à bâtir)**

### 2.1 Volet offline — **CONFORME**

- `screen.py` : « Le contrôle s'exécute intégralement en local : aucune donnée client ne
  quitte l'institution, et la coupure du réseau n'interrompt pas le filtrage. »
- Poste guichet : **une seule requête réseau** `fetch("../data/verdicts_demo.json")`
  (`guichet/app.js:59`) ; en cas d'échec (<code>catch</code> réseau, `file://`, HTTP ≠ 200),
  bascule automatique sur la copie embarquée `guichet/donnees_secours.js`
  (`guichet/app.js:68-72`), chargée via `<script>` (fonctionne hors-ligne).
- Trois états gérés : nominal (données fraîches) → périmé > 7 j (alerte non bloquante,
  art. 89) → dégradé (secours embarqué). Le filtrage ne s'arrête jamais.
- `demo/` et `guichet/moteur.js` : aucun appel réseau (fetch/XHR/WS : grep vide).

### 2.2 Volet online / synchronisation — **NON CONFORME**

- `offline_synch` = **placeholder identique à la baseline, zéro code** (pas de delta,
  pas de signature, pas d'horodatage de sync).
- `ingest.py` charge un **instantané complet** du XML, pas de correctif différentiel.
- Docs `ARCHITECTURE.md` : M1 « Partiel — correctif différentiel signé » listé comme manque.
- Règle SIEM **100428 `sync_differentielle`** définie (`0502…xml:106-110`) mais émise
  **uniquement par la simulation** `demo_soc.sh:24` — aucune implémentation réelle.
- `prototype-ux/index.html`:8-10 appelle **Google Fonts** (sortie réseau cosmétique) ;
  son « mode offline » est une simulation UI (`toggleOffline()`), pas de stockage local.

**Écart principal** : la connexion mixte « à jour » manque. Le guichet est robuste
hors-ligne mais s'appuie sur un **instantané statique versionné** ; aucun mécanisme
de delta signé / file locale de décisions / import CSV manuel (pourtant spécifiés dans
`corpusCIF/…/03_blueprint_solution.md` §5).

---

## 3. Rapidité des requêtes — **PARTIEL**

- **Mesure annoncée** : « Filtrage bout-en-bout : **520 ms** pour 1 011 entrées et 3 778
  libellés, hors ligne » (README.md:65 et reprises dans 3 documents de soumission).
- **Réserve** : la mesure de `screen.py:43-45` encadre **uniquement `index.filtrer`** et
  exclut le parsing XML (2,08 Mo) + construction de l'Index → le chiffre « bout-en-bout »
  est optimiste (réel = parsing + index + filtrage).
- **Complexité** : `Index.filtrer` = boucle naïve **O(N)** sur 3 778 libellés, x2 appels
  directionnels x 2·m·n évaluations jetons ≈ **~68 000 évaluations `similarite_jeton` /
  requête**. OK pour 1 011 entrées ; amorti par `lru_cache` (jusqu'à 500 000 entrées)
  **au sein d'un même process** ; **inopérant entre deux invocations CLI**.
- `verdicts.py` : consolidation O(k) ; fractionnement / collecte = O(t·log t) ;
  compte rebond / activation-dispersion = **O(E·S)** (mauvais cas O(t²)).
- `dataset.py` recharge tous les CSV à chaque appel (bénin : fichiers ≤ 1,5 Ko).
- Référentiel rechargé **à chaque lancement** (`screen.py:40-41`) — pas de cache persistant.
- **Aucun benchmark de latence** dans `benchmark_resultats.txt` (que du rappel/bruit).

**Piste prioritaire** : exploiter l'index de blocage `phonetics.squelette`
(`phonetics.py:132`, déjà présent mais **jamais utilisé**) pour sortir du O(N) avant
d'envisager les 42k+ entrées réelles.

---

## 4. Connexion ≤ 512 Ko — **PARTIEL (échec UNIQUEMENT sur le référentiel brut)**

Mesures (octets exacts, blobs git) :

| Fichier (branche) | Octets | Ko | ≤ 512 Ko |
|---|---:|---:|:---:|
| `data/un_consolidated.xml` (liste ONU réelle) | 2 176 185 | **2 125** | **NON** (4,2×) |
| `data/verdicts_demo.json` (indenté, servi HTTP) | 241 332 | 236 | OUI |
| `guichet/donnees_secours.js` (compact, embarqué) | 186 214 | 182 | OUI |
| `prototype-ux/index.html` | 103 141 | 101 | OUI |
| Chargement page guichet (index+styles+secours+moteur+app+JSON) | ~467 000 | ~456 | OUI (marge faible) |
| Événements SIEM UDP/514 (`feed_wazuh.py`, `demo_*.sh`) | ~90–150 | < 0,2 | OUI |
| `guichet/app.js` | 16 632 | 16 | OUI |
| `data/enr_bcft.txt` | 17 039 | 17 | OUI |
| `sentinellecoop/verdicts.py` | 11 781 | 12 | OUI |
| `corpusCIF/…/catalogue_assets_topic1.json` | 104 164 | 102 | OUI |
| `corpusCIF/…/catalogue_assets_topic1.csv` | 76 211 | 74 | OUI |
| CSV dataset (clients/comptes/transactions/ppe/sanctions) | ≤ 1 544 | ≤ 1,5 | OUI |

**Lecture** :
- Les payloads de fonctionnement et de sync « type » respectent le budget
  (235,7 Ko indenté / 181,8 Ko compact < 512 Ko).
- **Le seul dépassement** est `un_consolidated.xml` = 2,08 Mo (≈ 4,2× le budget).
  C'est précisément l'actif que la sync M1 doit rafraîchir : un transfert intégral
  dépasse le plafond, un **correctif différentiel signé** (objet du volet online du §2.2)
  rétablirait la conformité.
- Événements SIEM : 90–150 octets chacun — conformes.

---

## 5. Synthèse / écarts à traiter

| Critère | Verdict | Action requise |
|---|---|---|
| 1. Léger (ressources) | **CONFORME** | — maintenir l'exclusion des dépendances lourdes |
| 2. Mixte online + offline | **PARTIEL** | implémenter `offline_synch` : delta signé, file de décisions, import CSV/JSON manuel ; émettre réellement `sync_differentielle` (100428) |
| 3. Rapidité | **PARTIEL** | activer l'index de blocage `phonetics.squelette` ; mesurer la latence bout-en-bout (parsing inclus) ; indexer les transactions par compte |
| 4. ≤ 512 Ko | **PARTIEL** | ne jamais transférer `un_consolidated.xml` en entier ; passer la liste ONU en delta/compression (< 512 Ko) |

**Classement des écarts par priorité pour le SOC** :
1. **Sync différentielle signée + événement 100428** — verrou fonctionnel de la connexion
   mixte (bloque 2 et 4 simultanément).
2. **Index de blocage par squelette** — verrou de performance pour la montée à l'échelle (3).
3. **Instrumentation latence bout-en-bout honnête** — la métrique 520 ms doit inclure le
   parsing (3).
4. **Intégration SIEM des branches métier** — guichet/moteur-ia n'émettent toujours rien
   vers Wazuh (uniquement connecteur `security_audit`).

---

*Auteur : PREDATOR (SOC UEMOA). Document de surveillance, à régénérer après chaque
modification des branches de l'équipe.*