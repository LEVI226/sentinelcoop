// Schéma local — chaque terminal a sa propre base SQLite (WASM), indépendante
// des autres agences, synchronisée uniquement via sync_queue vers le central.
export const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS clients (
  id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  birth_date TEXT,
  id_document TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT DEFAULT 'XOF',
  tx_type TEXT DEFAULT 'deposit',
  occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist_cache (
  id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  category TEXT NOT NULL,
  source TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  transaction_id TEXT,
  matched_name TEXT,
  match_score REAL,
  severity TEXT,
  decision TEXT DEFAULT 'pending',
  created_at TEXT NOT NULL
);

-- File de synchronisation : le cœur de l'offline-first (voir syncWorker.js).
CREATE TABLE IF NOT EXISTS sync_queue (
  uuid TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_retry_at TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

-- Index — sans eux, chaque écran (historique client, liste d'alertes) et
-- chaque tour du worker de synchro (due()) dégénère en scan complet de la
-- table. Négligeable à 50 lignes en démo, plus du tout à l'échelle d'une
-- vraie agence après plusieurs mois d'activité.
CREATE INDEX IF NOT EXISTS idx_transactions_client_id ON transactions(client_id);
CREATE INDEX IF NOT EXISTS idx_alerts_client_id ON alerts(client_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status_retry ON sync_queue(status, next_retry_at);
`;
