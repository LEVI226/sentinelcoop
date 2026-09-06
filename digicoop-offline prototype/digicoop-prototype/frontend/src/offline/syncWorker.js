// L'orchestrateur de l'axe offline : détection réseau → drainage de la file
// → accusé central → synchronisation descendante → déclenchement du
// rescreening (délégué, pas fait ici — voir onRescreenClient ci-dessous).
//
// Frontière volontaire : ce fichier ne connaît RIEN du moteur IA. Il reçoit
// une fonction `onRescreenClient(client) -> matches[]` en paramètre de
// startSyncWorker(). L'axe moteur IA peut donc changer d'implémentation
// (nouvel algorithme de matching, seuils différents) sans jamais toucher
// à ce fichier, et réciproquement cet axe peut être développé et testé
// avec un onRescreenClient factice tant que le moteur IA n'est pas prêt.
import { all, run, getMeta, setMeta } from "../db/localDb";
import { pushBatch, pullDelta } from "./api";
import { createConnectivitySentinel } from "./connectivitySentinel";
import * as queue from "./queue";
import { watchForOtherTabs, withSyncLock } from "./tabCoordination";
import { uuidv4 } from "../utils/uuid";

// Valeurs par défaut de production. Toutes surchargeables via les options de
// startSyncWorker() — c'est ce qui rend le backoff et le dead-letter
// réellement testables (voir tests/test_backoff_dead_letter.py, qui les
// réduit à quelques centaines de ms au lieu d'attendre 30 minutes/24h).
const DEFAULT_BATCH_SIZE = 50;
const DEFAULT_BACKOFF_STEPS_MS = [30_000, 60_000, 120_000, 300_000, 600_000, 1_800_000]; // 30s → 30min
const DEFAULT_MAX_ATTEMPTS = 10;
const DEFAULT_DEAD_LETTER_AGE_MS = 24 * 3600 * 1000;
const DEFAULT_PUSH_INTERVAL_MS = 15_000;
const DEFAULT_PULL_INTERVAL_MS = 60_000;

let apiBaseUrl = "";
let agencyId = "";
let sentinel = null;
let listeners = [];
let rescreenClient = () => []; // stub par défaut : aucune correspondance tant que non câblé
let cfg = {
  batchSize: DEFAULT_BATCH_SIZE,
  backoffStepsMs: DEFAULT_BACKOFF_STEPS_MS,
  maxAttempts: DEFAULT_MAX_ATTEMPTS,
  deadLetterAgeMs: DEFAULT_DEAD_LETTER_AGE_MS,
};

// Point d'entrée public utilisé par le reste de l'app (ex. ClientForm) pour
// pousser une écriture locale vers l'axe offline, sans connaître sa mécanique interne.
export function enqueueSync(entityType, uuid, payload) {
  queue.enqueue(entityType, uuid, payload);
  notify();
}

function backoffFor(attempts) {
  const jitter = 1 + (Math.random() * 0.4 - 0.2); // ±20 %, désynchronise les terminaux entre eux
  const steps = cfg.backoffStepsMs;
  const base = steps[Math.min(attempts, steps.length - 1)];
  return base * jitter;
}

function notify() {
  const snap = getQueueSnapshot();
  listeners.forEach((fn) => fn(snap));
}

export function getQueueSnapshot() {
  return { ...queue.snapshot(), connection: sentinel ? sentinel.getState() : "online" };
}

export function onQueueChange(fn) {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((f) => f !== fn);
  };
}

async function drainQueue() {
  const dueItems = queue.due(cfg.batchSize, new Date().toISOString());
  if (dueItems.length === 0) return;

  const items = dueItems.map((row) => ({
    uuid: row.uuid,
    entity_type: row.entity_type,
    agency_id: agencyId,
    payload: JSON.parse(row.payload),
  }));

  try {
    const result = await pushBatch(apiBaseUrl, agencyId, items);
    const byUuid = Object.fromEntries(result.results.map((r) => [r.uuid, r]));
    for (const row of dueItems) {
      const outcome = byUuid[row.uuid];
      if (outcome && outcome.status === "synced") {
        queue.markSynced(row.uuid);
      } else {
        markAttemptFailed(row);
      }
    }
  } catch {
    // Coupure en plein envoi : chaque entrée repart en pending avec backoff,
    // rien n'est perdu, le lot sera rejoué (idempotent côté central).
    dueItems.forEach(markAttemptFailed);
  }
  notify();
}

function markAttemptFailed(row) {
  const attempts = row.attempts + 1;
  const ageMs = Date.now() - new Date(row.created_at).getTime();
  if (attempts >= cfg.maxAttempts || ageMs >= cfg.deadLetterAgeMs) {
    queue.markDeadLetter(row.uuid, attempts);
    return;
  }
  queue.markFailed(row.uuid, attempts, new Date(Date.now() + backoffFor(attempts)).toISOString());
}

/**
 * Renvoi manuel des entrées dead_letter (bouton "Renvoyer" de StatusDot).
 * Remet attempts à 0 : elles repartent avec le premier palier de backoff,
 * pas en boucle immédiate qui re-échouerait instantanément si la cause du
 * blocage n'a pas changé.
 */
export function retryDeadLetterEntries() {
  queue.requeueAllDeadLetters(new Date().toISOString());
  notify();
}

async function pullAndRescreen() {
  const since = getMeta("last_pull_ts") || "1970-01-01T00:00:00";
  const { watchlist, server_time } = await pullDelta(apiBaseUrl, since);

  if (watchlist.length === 0) {
    setMeta("last_pull_ts", server_time);
    return;
  }

  for (const entry of watchlist) {
    run(
      `INSERT INTO watchlist_cache (id, full_name, category, source, updated_at)
       VALUES (?, ?, ?, ?, ?)
       ON CONFLICT(id) DO UPDATE SET full_name = excluded.full_name,
                                      category = excluded.category,
                                      updated_at = excluded.updated_at`,
      [entry.id, entry.full_name, entry.category, entry.source, entry.updated_at]
    );
  }
  setMeta("last_pull_ts", server_time);
  rescreenExistingClients();
}

// Traite la base clients par lots pour ne jamais geler l'interface. Chaque
// match trouvé ici est une nouvelle alerte, qui redevient une entrée
// pending côté push — la boucle qui referme le workflow.
function rescreenExistingClients() {
  const clients = all("SELECT * FROM clients");
  if (clients.length === 0) return;

  let i = 0;
  const idle = typeof window !== "undefined" && window.requestIdleCallback
    ? window.requestIdleCallback
    : (fn) => setTimeout(fn, 0);

  function processChunk() {
    const chunk = clients.slice(i, i + 50);
    chunk.forEach((client) => {
      const matches = rescreenClient(client); // délégué à l'axe moteur IA
      if (matches.length > 0) {
        const best = matches[0];
        const alertId = uuidv4();
        const createdAt = new Date().toISOString();
        run(
          `INSERT INTO alerts (id, client_id, matched_name, match_score, severity, decision, created_at)
           VALUES (?, ?, ?, ?, 'blocking', 'pending', ?)`,
          [alertId, client.id, best.entry.full_name, best.score, createdAt]
        );
        enqueueSync("alert", alertId, {
          client_id: client.id,
          matched_name: best.entry.full_name,
          match_score: best.score,
          severity: "blocking",
          decision: "pending",
        });
      }
    });
    i += 50;
    if (i < clients.length) idle(processChunk);
    else notify();
  }
  processChunk();
}

/**
 * Démarre l'axe offline.
 * @param {object} opts
 * @param {string} opts.baseUrl - URL de l'API centrale
 * @param {string} opts.agency - identifiant de l'agence/terminal
 * @param {(client) => Array<{entry: object, score: number}>} [opts.onRescreenClient]
 *        Contrat avec l'axe moteur IA : reçoit un client, renvoie les
 *        correspondances triées par score. Optionnel — sans lui, le
 *        rescreening ne trouve simplement jamais rien (mode dégradé sûr).
 * @param {() => void} [opts.onMultiTabConflict]
 *        Appelé si ce terminal est déjà ouvert dans un autre onglet (voir
 *        tabCoordination.js) — l'app doit avertir l'agent, pas bloquer.
 * @param {number} [opts.batchSize]
 * @param {number[]} [opts.backoffStepsMs]
 * @param {number} [opts.maxAttempts]
 * @param {number} [opts.deadLetterAgeMs]
 * @param {number} [opts.pushIntervalMs]
 * @param {number} [opts.pullIntervalMs]
 *        Ces six derniers paramètres ont des valeurs de production par
 *        défaut (voir constantes DEFAULT_* en haut du fichier) ; ils ne sont
 *        surchargés que par les tests automatisés du backoff/dead-letter.
 */
export function startSyncWorker({
  baseUrl,
  agency,
  onRescreenClient,
  onMultiTabConflict,
  batchSize = DEFAULT_BATCH_SIZE,
  backoffStepsMs = DEFAULT_BACKOFF_STEPS_MS,
  maxAttempts = DEFAULT_MAX_ATTEMPTS,
  deadLetterAgeMs = DEFAULT_DEAD_LETTER_AGE_MS,
  pushIntervalMs = DEFAULT_PUSH_INTERVAL_MS,
  pullIntervalMs = DEFAULT_PULL_INTERVAL_MS,
}) {
  apiBaseUrl = baseUrl;
  agencyId = agency;
  if (onRescreenClient) rescreenClient = onRescreenClient;
  cfg = { batchSize, backoffStepsMs, maxAttempts, deadLetterAgeMs };

  watchForOtherTabs(() => {
    if (onMultiTabConflict) onMultiTabConflict();
  });

  const guardedDrain = () => withSyncLock("push", drainQueue);
  const guardedPull = () => withSyncLock("pull", pullAndRescreen);

  sentinel = createConnectivitySentinel(apiBaseUrl, (state) => {
    if (state === "online") {
      guardedDrain().then(guardedPull).catch(() => {});
    }
    notify();
  });
  sentinel.start();

  setInterval(() => {
    if (sentinel.getState() === "online") guardedDrain().catch(() => {});
  }, pushIntervalMs);

  setInterval(() => {
    if (sentinel.getState() === "online") guardedPull().catch(() => {});
  }, pullIntervalMs);

  return sentinel;
}
