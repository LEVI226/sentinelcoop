# Axe Offline-First — Documentation complète

Ce document couvre entièrement l'axe « mode offline » du terminal DigiCoop :
pourquoi il existe, comment il fonctionne, comment l'intégrer, comment le
tester, et ce qu'il reste à durcir. Il est pensé pour qu'un tiers (un
membre de l'équipe, un membre du jury qui lit le code, ou vous-même dans
six mois) comprenne l'ensemble sans avoir à recomposer le puzzle à partir
du code seul.

---

## 1. Rôle et périmètre de cet axe

Cet axe répond à une exigence non négociable du hackathon (briefing règles,
5 septembre) : le terminal doit fonctionner sur un Android ou un Windows
standard, en mode dégradé (connectivité faible ou absente), sans que
l'agent ne s'en aperçoive.

Ce dossier (`frontend/src/offline/`) est la seule partie du code qui gère :
- la détection de l'état du réseau,
- la mise en file d'attente des écritures locales,
- leur envoi vers le central quand c'est possible,
- la récupération des mises à jour de listes de sanctions/PPE,
- la résilience face aux échecs (retry, dead-letter, et leur renvoi manuel),
- la coordination entre onglets d'un même terminal (`tabCoordination.js`).

Le chiffrement au repos de la base locale (`db/crypto.js`) est un fichier
partagé (`db/`, pas `offline/`) puisqu'il protège toute la base — clients et
alertes compris, pas seulement la file de synchro — mais c'est cet axe qui
en a poussé l'implémentation (voir section 12) et qui en documente le
modèle de menace, parce que c'est un axe « durcissement offline » au sens
large, pas seulement « file d'attente ».

Ce dossier ne gère jamais l'interface (React), ni le calcul du filtrage
PPE/sanctions (moteur IA), ni le stockage central (PostgreSQL). Ces trois
responsabilités appartiennent aux trois autres axes du projet.

---

## 2. Pourquoi cette architecture

Les coopératives financières (SFD) ciblées ont une connectivité intermittente
et du matériel modeste. Deux options existaient :

1. **Online-first avec repli offline** : l'app suppose le réseau disponible,
   et affiche un mode dégradé quand il ne l'est pas. Rejeté : ça implique
   un écran « vous êtes hors-ligne » qui interrompt l'agent, et un risque
   réel de bloquer une opération de guichet en attendant une réponse réseau.
2. **Offline-first** : l'app suppose *toujours* qu'elle tourne en local ;
   le réseau n'est qu'un moyen de synchroniser en arrière-plan, jamais une
   condition pour que le filtrage fonctionne. C'est ce qui est implémenté ici.

Conséquence directe : le filtrage LBC/FT/FP (moteur IA) tourne intégralement
dans le navigateur, jamais via un appel réseau. Cet axe n'intervient
*qu'après coup*, pour propager ce qui s'est passé localement vers le central,
et redescendre les mises à jour de listes.

---

## 3. Vue d'ensemble du workflow

```
Écriture locale → Mise en file → Sentinelle réseau → (bifurcation silencieuse)
   → Envoi par lot → Accusé central → Synchronisation descendante → Rescreening local
   → Reprise automatique (si une coupure était survenue)
```

Ce n'est pas un pipeline linéaire à sens unique : c'est une boucle. Un match
trouvé lors du rescreening redevient lui-même une écriture locale, qui
repart en étape 1. Le système ne s'arrête jamais de tourner tant que le
terminal est ouvert.

### Détail de chaque étape

| # | Étape | Ce qui se passe | Fichier |
|---|---|---|---|
| 1 | Écriture locale | Un client, une transaction ou une alerte est écrit dans SQLite (par un autre axe) | *(appelant externe)* |
| 2 | Mise en file | La même écriture est dupliquée dans `sync_queue`, statut `pending`, UUID déjà généré côté appelant | `queue.js::enqueue` |
| 3 | Sentinelle réseau | Ping actif périodique vers `/health`, avec hystérésis (2 échecs pour passer OFFLINE, 1 succès pour repasser ONLINE) | `connectivitySentinel.js` |
| 4 | Bifurcation silencieuse | Si ONLINE → drainage immédiat de la file. Si OFFLINE → la file continue de grossir, rien d'autre ne se produit, aucun signal visible côté agent | `syncWorker.js::startSyncWorker` |
| 5 | Envoi par lot | Jusqu'à 50 entrées `pending` envoyées groupées et compressées vers `POST /sync/push` | `syncWorker.js::drainQueue`, `api.js::pushBatch` |
| 6 | Accusé central | Le central fait un upsert par UUID (idempotent) et confirme ; l'entrée locale passe à `synced` | `queue.js::markSynced` |
| 7 | Synchronisation descendante | `GET /sync/pull?since=<dernier timestamp>` récupère le delta des listes de sanctions/PPE | `syncWorker.js::pullAndRescreen`, `api.js::pullDelta` |
| 8 | Rescreening local | La base clients est repassée au filtre par lots de 50 via `requestIdleCallback`, pour ne jamais geler l'interface | `syncWorker.js::rescreenExistingClients` |
| 9 | Reprise automatique | Si une coupure avait eu lieu, la sentinelle redétecte le réseau et relance elle-même les étapes 5 à 8, sans action de l'agent | `connectivitySentinel.js` → callback `onChange` |

---

## 4. La machine à états d'une entrée de synchronisation

Le chemin heureux (étapes 5-6 ci-dessus) n'est qu'un cas parmi d'autres.
Voici le cycle de vie complet d'une ligne de `sync_queue` :

```
                        ┌────────────────────────────┐
                        │   échec / timeout           │
                        │   backoff 30s → 30min        │
                        │   (jitter ±20%)               │
                        ▼                               │
   PENDING ───(réseau détecté)───▶ SYNCING ──────────────┘
      │                              │
      │                       (200 OK, upsert)
      │                              ▼
      │                           SYNCED
      │
      └──(10 tentatives OU > 24h)──▶ DEAD_LETTER ──(bouton "Renvoyer",
                                                      StatusDot.jsx)──▶ PENDING
```

Le point important : `DEAD_LETTER` n'est jamais une perte de données. C'est
un signal explicite qu'une entrée a besoin d'une intervention humaine —
jamais un échec silencieux. Le renvoi manuel (`retryDeadLetterEntries()`
dans `syncWorker.js`, exposé via un bouton dans `StatusDot.jsx`) remet
`attempts` à 0 : l'entrée repart avec le premier palier de backoff, pas en
boucle immédiate qui re-échouerait aussitôt si la cause du blocage n'a pas
changé entre-temps.

---

## 5. Architecture des fichiers

| Fichier | Responsabilité | Ce qu'il touche |
|---|---|---|
| `connectivitySentinel.js` | Détecte ONLINE/OFFLINE, expose l'état | Rien d'autre que `fetch` vers `/health` |
| `queue.js` | Le pattern outbox : lit/écrit `sync_queue`, rien d'autre | Table `sync_queue` uniquement |
| `syncWorker.js` | Orchestrateur : relie sentinelle, file, API, verrous multi-onglets, et déclenche le rescreening | `queue.js`, `connectivitySentinel.js`, `api.js`, `tabCoordination.js`, tables `clients`/`alerts`/`watchlist_cache` |
| `api.js` | Les deux seuls appels réseau de tout le module | `fetch` vers `/sync/push` et `/sync/pull` |
| `tabCoordination.js` | Détecte un second onglet ouvert sur le même terminal, sérialise push/pull entre onglets via Web Locks | `navigator.locks` uniquement — aucune table |

Fichier partagé (hors de ce dossier mais documenté ici, voir section 12) :

| Fichier | Responsabilité |
|---|---|
| `../db/crypto.js` | Dérivation de clé (PBKDF2) et chiffrement/déchiffrement (AES-256-GCM) de la base locale |

Aucun de ces fichiers n'importe quoi que ce soit depuis `engine/` (moteur IA)
ou `components/` (frontend). C'est une frontière volontaire, pas un oubli.

---

## 6. Référence API du module

### `connectivitySentinel.js`

```js
createConnectivitySentinel(apiBaseUrl, onChange) -> { start(), stop(), getState() }
```
- `onChange(state)` est appelé **uniquement lors d'un changement d'état** (jamais à chaque ping), avec `state` valant `"online"` ou `"offline"`.
- `getState()` renvoie l'état courant sans effet de bord.

### `queue.js`

```js
enqueue(entityType, uuid, payload)          // insère une ligne 'pending'
due(limit, nowIso) -> row[]                 // lignes prêtes à être (re)tentées
markSynced(uuid)
markFailed(uuid, attempts, nextRetryAt)
markDeadLetter(uuid, attempts)
requeueDeadLetter(uuid, nowIso)             // renvoi manuel d'UNE entrée
requeueAllDeadLetters(nowIso)               // renvoi manuel de TOUTES les entrées dead_letter
snapshot() -> { pending, dead_letter, synced }
```
`entityType` vaut `"client"`, `"transaction"` ou `"alert"` — doit correspondre
exactement aux types acceptés par `POST /sync/push` côté central
(voir `backend/app/schemas.py::SyncItem`).

### `syncWorker.js`

```js
startSyncWorker({
  baseUrl, agency, onRescreenClient, onMultiTabConflict,
  batchSize, backoffStepsMs, maxAttempts, deadLetterAgeMs,
  pushIntervalMs, pullIntervalMs,
}) -> sentinel
enqueueSync(entityType, uuid, payload)      // API publique pour le reste de l'app
getQueueSnapshot() -> { pending, dead_letter, synced, connection }
onQueueChange(fn) -> unsubscribe()
retryDeadLetterEntries()                    // renvoi manuel (bouton StatusDot)
```
`onRescreenClient` est **le seul point de contact avec le moteur IA** (voir
section 7). Sans lui, le rescreening ne trouve jamais rien — mode dégradé
sûr, pas un plantage.

`onMultiTabConflict` est appelé si ce terminal est déjà ouvert dans un
autre onglet (voir section 13) — à l'app de prévenir l'agent, ce fichier ne
décide jamais de fermer quoi que ce soit lui-même.

Les six derniers paramètres (`batchSize` → `pullIntervalMs`) ont des
valeurs de production par défaut (voir section 8) ; ils ne sont surchargés
que par les tests automatisés du backoff/dead-letter
(`tests/test_backoff_dead_letter.py`), jamais en usage normal.

### `api.js`

```js
pushBatch(apiBaseUrl, agencyId, items) -> { results: [{uuid, status, detail}], server_time }
pullDelta(apiBaseUrl, since) -> { watchlist: [...], server_time }
```
Ces deux fonctions ne font que l'appel HTTP et la désérialisation JSON —
aucune logique métier ici, elle vit entièrement dans `syncWorker.js`.

---

## 7. Contrat d'intégration avec les autres axes

**Avec le moteur IA (dépendance entrante uniquement)**
Ce dossier n'importe jamais `engine/*`. L'intégration se fait dans
`App.jsx`, à un seul endroit :

```js
import { startSyncWorker } from "./offline/syncWorker";
import { screenClient } from "./engine/screening";

startSyncWorker({ baseUrl, agency, onRescreenClient: screenClient });
```

Tant que le moteur IA n'est pas prêt, un stub suffit et ne casse rien :
`onRescreenClient: () => []`.

**Avec le frontend (API exposée)**
- `ClientForm.jsx` appelle `enqueueSync(...)` après chaque écriture locale.
- `StatusDot.jsx` s'abonne à `onQueueChange(...)` pour afficher l'état, sans
  jamais lire `sync_queue` directement.

**Avec le backend (contrat de données)**
Le format des items poussés doit correspondre exactement à
`schemas.SyncItem` côté central : `{ uuid, entity_type, agency_id, payload }`.
Toute évolution de ce contrat doit être coordonnée avec l'axe backend avant
d'être codée ici.

---

## 8. Paramètres de configuration

| Paramètre | Valeur par défaut | Option `startSyncWorker()` | Remarque |
|---|---|---|---|
| Taille de lot (push) | 50 | `batchSize` | à réduire si la 2G est très mauvaise pendant le hackathon |
| Palier de backoff | 30s, 1m, 2m, 5m, 10m, 30m | `backoffStepsMs` | plafonné à 30 min |
| Jitter | ±20 % | *(non paramétrable)* | désynchronise plusieurs terminaux d'une même agence |
| Seuil dead-letter | 10 tentatives OU 24h | `maxAttempts`, `deadLetterAgeMs` | le premier des deux déclenche |
| Ping réseau (online) | toutes les 12s | *(constante `connectivitySentinel.js`)* | |
| Ping réseau (offline) | toutes les 20s | *(constante `connectivitySentinel.js`)* | plus espacé pour économiser batterie/data |
| Hystérésis | 2 échecs consécutifs | *(constante `connectivitySentinel.js`)* | évite le clignotement online/offline |
| Timeout d'un ping | 4s | *(constante `connectivitySentinel.js`)* | |
| Cadence de drainage | toutes les 15s (si online) | `pushIntervalMs` | en plus du déclenchement immédiat au retour du réseau |
| Cadence de pull | toutes les 60s (si online) | `pullIntervalMs` | idem |
| Persistance différée | 1s après la dernière écriture | *(constante `db/localDb.js` → `PERSIST_DEBOUNCE_MS`)* | regroupe client+transaction+alerte d'un même dépôt en un seul export chiffré |
| Itérations PBKDF2 | 210 000 | *(constante `db/crypto.js`)* | recommandation OWASP 2023 pour PBKDF2-HMAC-SHA256 |

Les six premiers paramètres exposés comme options existent précisément
pour que `tests/test_backoff_dead_letter.py` puisse les réduire à quelques
centaines de millisecondes et observer une transition PENDING → DEAD_LETTER
en quelques secondes au lieu d'attendre jusqu'à 24h en conditions réelles.

---

## 9. Scénario de démonstration (jury)

C'est le scénario qui démontre concrètement cet axe pendant les 10 minutes
de pitch (démonstration live obligatoire, briefing règles) :

1. Terminal et central démarrés, synchronisés (`StatusDot` affiche « synchronisé »).
2. Couper le réseau (mode avion, ou arrêter le central).
3. Créer un client avec une opération à montant élevé → l'alerte apparaît
   **instantanément** dans « Alertes locales », le statut passe à
   « hors-ligne — file en attente ». Rien n'a été bloqué côté agent.
4. Reconnecter → en quelques secondes, sans aucune action, l'alerte apparaît
   côté central (`GET /alerts`). C'est la bascule silencieuse en action.

---

## 10. Ce qui a été vérifié (pas seulement écrit)

- **Idempotence** : un même lot poussé deux fois côté central ne crée pas
  de doublon (vérifié en interrogeant directement la base après un rejeu).
- **Fonctionnement 100 % hors-ligne** : test navigateur (Playwright) sans
  aucun central démarré — le terminal charge, filtre, et génère une alerte
  locale normalement.
- **Synchronisation de bout en bout** : une alerte créée localement,
  réseau coupé, apparaît côté central dans les ~20 secondes suivant la
  reconnexion, sans action manuelle.
- **Découplage du moteur IA** : `syncWorker.js` ne contient plus aucun
  `import` vers `engine/*` — vérifié par relecture et par le fait que les
  tests ci-dessus passent toujours avec l'injection via `App.jsx`.
- **Backoff et dead-letter réellement exercés** (et non plus seulement
  documentés) : `tests/test_backoff_dead_letter.py` force l'échec de
  `POST /sync/push` par interception réseau (Playwright `page.route`),
  observe la progression `PENDING → SYNCING → PENDING` avec compteur de
  tentatives croissant, la transition en `DEAD_LETTER` une fois le seuil
  configuré atteint, puis vérifie que le bouton « Renvoyer » ramène
  l'entrée en `PENDING` et qu'elle atteint `SYNCED` une fois le réseau
  simulé comme fonctionnel à nouveau. Ce test simule aussi la réponse de
  succès du central (limitation de l'interception réseau de Playwright sur
  une même URL mock puis réelle, documentée en tête du fichier de test) —
  c'est `test_end_to_end_sync.py`, séparément, qui prouve qu'une vraie
  réponse du vrai central fait progresser la file.
- **Chiffrement au repos non contournable par un mauvais code** : vérifié
  qu'un code incorrect fait échouer `decryptBytes()` (tag d'authentification
  AES-GCM invalide) plutôt que de renvoyer une base corrompue silencieuse.
- **Optimisation du filtrage flou non régressive** : voir
  `frontend/src/engine/BENCHMARK.md` — mêmes résultats de correspondance,
  gain de performance mesuré à toutes les échelles testées (50 à 50 000
  entrées).

- **Chiffrement au repos survit à un vrai cycle fermeture/réouverture** :
  `tests/test_encryption_roundtrip.py` utilise un profil Chromium
  persistant (pas un navigateur neuf à chaque fois, comme les autres tests)
  pour prouver trois choses dans l'ordre : un client + une alerte saisis
  puis l'onglet fermé ; la réouverture avec un mauvais code échoue
  proprement (jamais de base corrompue affichée) ; la réouverture avec le
  bon code déchiffre et retrouve l'alerte.

Pour rejouer ces vérifications : voir `frontend/tests/test_offline_only.py`,
`frontend/tests/test_end_to_end_sync.py`,
`frontend/tests/test_backoff_dead_letter.py` et
`frontend/tests/test_encryption_roundtrip.py`, et la section correspondante
du `README.md` à la racine du projet.

---

## 11. Limites connues et pistes de durcissement

Ce qui a été effectivement corrigé depuis la première version de ce
prototype (fuzzy matching non borné, aucun chiffrement, backoff/dead-letter
jamais testés, aucune coordination multi-onglets, aucun index, persistance
non groupée) est désormais couvert par les sections précédentes et par
`BENCHMARK.md`. Ce qui reste, honnêtement, en dehors du périmètre de ce
prototype de hackathon :

- **`navigator.onLine` n'est pas utilisé** volontairement (peu fiable en
  2G/3G) — mais le ping actif consomme un peu de données même à l'arrêt ;
  à surveiller si la facture data des agences est un critère.
- **La coordination multi-onglets détecte et avertit, elle ne fusionne
  pas** : deux onglets ouverts sur le même terminal restent deux bases
  SQLite en mémoire distinctes tant qu'ils sont ouverts. Web Locks empêche
  les doublons de requêtes réseau et l'app avertit l'agent, mais la vraie
  solution (état partagé entre onglets) demanderait OPFS + SharedWorker —
  hors budget de ce hackathon (voir section 13).
- **Persistance via IndexedDB simple**, pas encore OPFS — suffisant pour la
  démo, mais moins performant sur de gros volumes en production, et c'est
  aussi ce qui empêche un vrai partage d'état entre onglets (point ci-dessus).
- **Pas d'authentification** sur `/sync/push` et `/sync/pull` dans ce
  prototype — à ajouter par l'axe backend+sécurité avant toute donnée réelle
  (qui de toute façon n'est pas autorisée pendant le hackathon).
- **Seuils de backoff et de taille de lot** choisis par défaut, jamais
  calibrés sur un vrai réseau 2G ouest-africain — à tester sur site si
  possible pendant le hackathon.
- **Le chiffrement au repos protège un scénario précis** (appareil perdu ou
  volé, extraction du fichier IndexedDB) — pas une session déjà déverrouillée
  ni un appareil compromis pendant qu'il tourne. Voir le modèle de menace
  complet dans `db/crypto.js` et la section 12.
- **Web Locks API** : supportée sur Chrome/Edge Android et Windows récents
  (le "terminal standard" visé), mais absente de certains WebView Android
  embarqués plus anciens. Dégradation prévue et testée en pensée (le code
  bascule sur "pas de coordination possible, on continue quand même") mais
  pas vérifiée sur un vrai vieux WebView faute de matériel disponible
  pendant le hackathon.
- **Performance mesurée sur machine de développement**, pas sur un vrai
  terminal Android bas de gamme — voir les limites détaillées de
  `BENCHMARK.md`.

---

## 12. Chiffrement au repos de la base locale

Ajouté en réponse à un écart identifié lors d'une auto-évaluation du
prototype : les documents d'architecture évoquaient un « SQLite chiffré au
repos », mais la première version livrée du code ne chiffrait rien.

**Ce qui est implémenté** (`db/crypto.js`, intégré dans `db/localDb.js`) :
- Un code choisi par l'agent (`PinGate.jsx`, à la première ouverture du
  terminal) sert de secret d'entrée.
- La clé de chiffrement réelle est dérivée de ce code via **PBKDF2-HMAC-SHA256,
  210 000 itérations**, avec un sel aléatoire de 16 octets généré une fois
  par terminal et stocké (en clair — un sel n'a pas besoin d'être secret)
  à côté du blob chiffré.
- Le blob exporté par sql.js (`db.export()`) est chiffré avec **AES-256-GCM**
  avant d'être écrit dans IndexedDB ; un vecteur d'initialisation (IV) de
  12 octets est régénéré à chaque écriture.
- AES-GCM inclut un tag d'authentification : un mauvais code produit un
  échec de déchiffrement franc, jamais une base corrompue silencieuse — ce
  qui permet d'afficher « code incorrect » avec certitude côté UI.

**Modèle de menace assumé** (voir aussi le commentaire en tête de `crypto.js`) :
- Protège contre l'extraction du fichier IndexedDB d'un terminal volé ou
  perdu (accès physique au disque, terminal Android rooté récupéré).
- Ne protège pas contre une session déjà déverrouillée (le code est en
  mémoire tant que l'onglet reste ouvert), un keylogger, ou un attaquant qui
  connaît déjà le code de l'agence. Ce n'est pas un système multi-utilisateur
  avec des comptes distincts — c'est un secret partagé par terminal, au même
  niveau qu'un code PIN de carte SIM.
- Le code n'est **jamais transmis au central** ni stocké nulle part en clair.
  Un code oublié rend la base locale définitivement illisible — c'est le
  prix normal d'un vrai chiffrement, pas un bug : voir l'avertissement
  affiché par `PinGate.jsx`.

---

## 13. Coordination multi-onglets (`tabCoordination.js`)

Ajouté pour la même raison : le README annonçait une architecture robuste,
mais rien n'empêchait deux onglets du même terminal de tourner en parallèle
et de s'écraser silencieusement l'un l'autre au moment de la persistance
(voir section 11 pour la limite honnête de cette correction).

**Ce qui est implémenté**, via l'API `navigator.locks` (Web Locks) :
- **Détection** : au démarrage, chaque onglet tente de prendre un verrou
  `digicoop-terminal-single-tab`. Le premier l'obtient et le garde jusqu'à
  sa fermeture. Un second onglet ne l'obtient pas (`ifAvailable: true`,
  jamais bloquant) et reçoit un callback `onConflict()`, remonté jusqu'à
  `App.jsx` qui affiche un bandeau d'avertissement — sans jamais bloquer
  l'onglet ni perdre de données déjà saisies.
- **Anti-doublon réseau** : `drainQueue()` et `pullAndRescreen()` sont
  chacune enveloppées dans leur propre verrou (`digicoop-sync-push`,
  `digicoop-sync-pull`). Si un onglet tient déjà l'un de ces verrous, l'autre
  saute simplement ce tour — rien n'est perdu, la file reste `pending`
  jusqu'au prochain cycle.
- **Dégradation gracieuse** : si `navigator.locks` est absent (vieux
  WebView Android), les deux mécanismes ci-dessus sont simplement désactivés
  et le code se comporte comme avant — jamais un plantage.

Ce que ça ne fait PAS (assumé, voir section 11) : fusionner l'état de deux
onglets déjà ouverts. Chaque onglet garde sa propre base SQLite en mémoire ;
la coordination empêche le pire (écrasement silencieux au niveau du
stockage, requêtes réseau dupliquées) et avertit l'agent, elle ne rend pas
l'usage multi-onglet réellement sûr pour la saisie.
