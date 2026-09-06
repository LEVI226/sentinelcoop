// Le pattern outbox, isolé : c'est la seule pièce qui touche la table
// sync_queue directement. Le reste du module offline (syncWorker.js) ne
// manipule plus jamais de SQL brut, il appelle ces fonctions.
import { run, all } from "../db/localDb";

export function enqueue(entityType, uuid, payload) {
  const now = new Date().toISOString();
  run(
    `INSERT INTO sync_queue (uuid, entity_type, payload, status, attempts, next_retry_at, created_at)
     VALUES (?, ?, ?, 'pending', 0, ?, ?)`,
    [uuid, entityType, JSON.stringify(payload), now, now]
  );
}

export function due(limit, nowIso) {
  return all(
    `SELECT * FROM sync_queue WHERE status = 'pending' AND next_retry_at <= ?
     ORDER BY created_at LIMIT ?`,
    [nowIso, limit]
  );
}

export function markSynced(uuid) {
  run("UPDATE sync_queue SET status = 'synced' WHERE uuid = ?", [uuid]);
}

export function markFailed(uuid, attempts, nextRetryAt) {
  run("UPDATE sync_queue SET attempts = ?, next_retry_at = ? WHERE uuid = ?", [attempts, nextRetryAt, uuid]);
}

export function markDeadLetter(uuid, attempts) {
  run("UPDATE sync_queue SET status = 'dead_letter', attempts = ? WHERE uuid = ?", [attempts, uuid]);
}

/**
 * Renvoi manuel documenté dans le schéma d'état mais absent du code jusqu'ici
 * (voir l'auto-évaluation) : remet une entrée dead_letter à zéro (attempts=0,
 * disponible immédiatement) pour qu'elle reparte dans le cycle normal de
 * due()/push. N'agit que sur une entrée réellement en dead_letter — un uuid
 * déjà synced ou pending est ignoré, pas de risque de la faire régresser.
 */
export function requeueDeadLetter(uuid, nowIso) {
  run(
    "UPDATE sync_queue SET status = 'pending', attempts = 0, next_retry_at = ? WHERE uuid = ? AND status = 'dead_letter'",
    [nowIso, uuid]
  );
}

export function requeueAllDeadLetters(nowIso) {
  run("UPDATE sync_queue SET status = 'pending', attempts = 0, next_retry_at = ? WHERE status = 'dead_letter'", [nowIso]);
}

export function snapshot() {
  const count = (status) => all("SELECT COUNT(*) as n FROM sync_queue WHERE status = ?", [status])[0]?.n ?? 0;
  return { pending: count("pending"), dead_letter: count("dead_letter"), synced: count("synced") };
}
