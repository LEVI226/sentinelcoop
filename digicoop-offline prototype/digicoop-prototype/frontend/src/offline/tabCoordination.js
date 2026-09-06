// Coordination multi-onglets — Web Locks API (supportée sur Chrome/Edge
// Android et Windows depuis 2020, donc compatible "terminal standard").
//
// Ce qu'il faut savoir avant de lire ce fichier : la base locale (sql.js)
// vit EN MÉMOIRE dans chaque onglet séparément et n'est écrite dans
// IndexedDB qu'au moment du persist() de CET onglet précis (voir
// db/localDb.js). Deux onglets ouverts en même temps sur le même terminal
// ne partagent donc pas leur état — si l'agent ouvre le terminal dans un
// second onglet, le premier onglet ignore tout des écritures faites dans
// le second, et inversement. Le dernier des deux à persister écrase le
// blob chiffré de l'autre : une vraie perte de données silencieuse.
//
// Fusionner correctement l'état entre onglets demanderait de partager la
// base en mémoire (OPFS + SharedWorker, ou un vrai backend local), ce qui
// est hors budget pour ce hackathon. Le choix assumé ici est donc : ne pas
// prétendre résoudre la fusion, mais EMPÊCHER la situation dangereuse en la
// détectant et en avertissant l'agent, pour qu'il ferme un des deux onglets
// avant de continuer à saisir des opérations.
//
// Un second verrou (SYNC_LOCK) protège en plus, pour les navigateurs qui
// ignoreraient l'avertissement, contre la conséquence la plus visible côté
// central : deux onglets qui pousseraient/tireraient la file de synchro en
// même temps (requêtes dupliquées, pas de corruption possible côté central
// grâce à l'upsert idempotent, mais du bruit réseau inutile).
const SINGLE_TAB_LOCK = "digicoop-terminal-single-tab";
const SYNC_LOCK_PREFIX = "digicoop-sync-";

function hasLocksApi() {
  return typeof navigator !== "undefined" && !!navigator.locks;
}

/**
 * Signale si cet onglet est le seul à tenir le rôle "actif" pour ce
 * terminal. Appelle onConflict() si un autre onglet tenait déjà le verrou
 * au moment de l'appel. Ne bloque jamais l'onglet appelant : dégradé mais
 * fonctionnel si l'API Web Locks est absente (vieux WebView Android).
 */
export function watchForOtherTabs(onConflict) {
  if (!hasLocksApi()) return; // pas de détection possible, on continue quand même (dégradé, pas bloquant)

  navigator.locks.request(SINGLE_TAB_LOCK, { ifAvailable: true }, (lock) => {
    if (!lock) {
      onConflict();
      return; // ne prend pas le verrou : ne fait rien d'autre, ne bloque pas cet onglet
    }
    // Garde le verrou tant que cet onglet vit — jamais résolue volontairement ;
    // le navigateur la libère automatiquement à la fermeture/rechargement de l'onglet.
    return new Promise(() => {});
  });
}

/**
 * Exécute fn() seulement si aucun autre onglet du même terminal n'est déjà
 * en train de faire la même opération de synchro (push OU pull, verrous
 * distincts). Si le verrou est pris ailleurs, ce tour est simplement sauté
 * — la prochaine minuterie réessaiera ; rien n'est perdu, la file reste
 * intacte côté SQLite tant qu'elle n'est pas marquée synced/dead_letter.
 */
export function withSyncLock(name, fn) {
  if (!hasLocksApi()) return fn(); // pas de coordination possible : on exécute quand même (comportement d'origine)

  return navigator.locks.request(`${SYNC_LOCK_PREFIX}${name}`, { ifAvailable: true }, (lock) => {
    if (!lock) return undefined; // un autre onglet a déjà la main sur cette opération ce tour-ci
    return fn();
  });
}
