// Base locale du terminal : SQLite compilé en WebAssembly (sql.js), persisté
// CHIFFRÉ (AES-256-GCM, voir crypto.js) dans IndexedDB pour survivre à la
// fermeture du navigateur. C'est ce module qui remplace un « serveur local »
// — il n'y en a pas, tout tient dans l'onglet.
import initSqlJs from "sql.js";
import { SCHEMA_SQL } from "./schema";
import { generateSalt, deriveKey, encryptBytes, decryptBytes } from "./crypto";

const IDB_NAME = "digicoop-terminal";
const IDB_STORE = "sqlite-file";
const IDB_KEY = "main.db";
const PERSIST_DEBOUNCE_MS = 1000; // regroupe les écritures rafales (ex. client + transaction + alerte)

let SQL = null;
let db = null;
let encryptionKey = null;
let dbSalt = null;
let persistTimer = null;
let flushHooksInstalled = false;

function openIdb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(IDB_STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function loadPersistedRecord() {
  try {
    const idb = await openIdb();
    return await new Promise((resolve) => {
      const tx = idb.transaction(IDB_STORE, "readonly");
      const req = tx.objectStore(IDB_STORE).get(IDB_KEY);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => resolve(null);
    });
  } catch {
    return null; // premier lancement, ou navigateur en navigation privée : on repart d'une base vide
  }
}

/** Utilisé par PinGate.jsx pour savoir s'il faut proposer "créer un code" ou "entrer le code". */
export async function hasExistingDatabase() {
  const record = await loadPersistedRecord();
  return !!(record && record.ciphertext);
}

/**
 * Déverrouille (ou initialise) la base chiffrée à partir du code agence.
 * Ne construit PAS encore la base sql.js — voir getDb(). Sépare bien les
 * deux étapes : celle-ci ne dépend que de crypto.js, getDb() ne dépend que
 * de sql.js. Lève une erreur explicite si le code est incorrect (tag GCM
 * invalide), jamais un déchiffrement silencieusement corrompu.
 */
export async function unlockDatabase(pin) {
  const record = await loadPersistedRecord();

  if (!record || !record.ciphertext) {
    dbSalt = generateSalt();
    encryptionKey = await deriveKey(pin, dbSalt);
    return { created: true, plainBytes: null };
  }

  const key = await deriveKey(pin, record.salt);
  try {
    const plainBytes = await decryptBytes(key, record.iv, record.ciphertext);
    dbSalt = record.salt;
    encryptionKey = key;
    return { created: false, plainBytes };
  } catch {
    throw new Error("Code incorrect — impossible de déchiffrer la base locale de ce terminal.");
  }
}

/** Persistance immédiate (chiffrée). Préférer schedulePersist()/flushPersist() ailleurs. */
export async function persist() {
  if (!db || !encryptionKey) return;
  try {
    const plainBytes = db.export();
    const { iv, ciphertext } = await encryptBytes(encryptionKey, plainBytes);
    const idb = await openIdb();
    const tx = idb.transaction(IDB_STORE, "readwrite");
    tx.objectStore(IDB_STORE).put({ salt: dbSalt, iv, ciphertext }, IDB_KEY);
  } catch (err) {
    console.warn("Persistance locale impossible :", err);
  }
}

/**
 * Persistance différée : regroupe les écritures rapprochées (ex. la
 * séquence client → transaction → alerte d'un seul dépôt guichet) en un
 * seul export()+chiffrement au lieu d'un par ligne insérée. run() l'appelle
 * automatiquement — les composants n'ont plus besoin d'appeler persist()
 * eux-mêmes après chaque écriture.
 */
export function schedulePersist() {
  if (persistTimer) clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    persistTimer = null;
    persist();
  }, PERSIST_DEBOUNCE_MS);
}

/** Force l'écriture immédiate d'une persistance en attente (fermeture d'onglet, tests). */
export function flushPersist() {
  if (persistTimer) {
    clearTimeout(persistTimer);
    persistTimer = null;
  }
  return persist();
}

function installFlushHooks() {
  if (flushHooksInstalled || typeof window === "undefined") return;
  flushHooksInstalled = true;
  // beforeunload seul est trop tardif sur mobile (l'OS peut tuer l'onglet
  // sans jamais le déclencher) — visibilitychange couvre le cas "l'agent
  // change d'appli sans fermer le navigateur", bien plus fréquent sur Android.
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushPersist();
  });
  window.addEventListener("beforeunload", () => {
    flushPersist();
  });
}

export async function getDb(plainBytes) {
  if (db) return db;
  SQL = await initSqlJs({ locateFile: () => "/sql-wasm.wasm" });
  db = plainBytes ? new SQL.Database(plainBytes) : new SQL.Database();
  db.run(SCHEMA_SQL);
  installFlushHooks();
  await persist();
  return db;
}

export function run(sql, params = []) {
  db.run(sql, params);
  schedulePersist();
}

export function all(sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const rows = [];
  while (stmt.step()) rows.push(stmt.getAsObject());
  stmt.free();
  return rows;
}

export function getMeta(key) {
  const rows = all("SELECT value FROM sync_meta WHERE key = ?", [key]);
  return rows.length ? rows[0].value : null;
}

export function setMeta(key, value) {
  run(
    `INSERT INTO sync_meta (key, value) VALUES (?, ?)
     ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
    [key, value]
  );
}
