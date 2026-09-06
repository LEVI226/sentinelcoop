// Chiffrement au repos de la base locale — Web Crypto API native (aucune
// dépendance externe, disponible sur tout navigateur Android/Windows récent).
//
// Modèle de menace assumé et honnête (à annoncer tel quel devant le jury) :
//   - PROTÈGE contre : l'extraction du fichier IndexedDB d'un terminal volé
//     ou perdu (clé USB de récupération, accès physique au disque, terminal
//     Android rooté récupéré) — sans le code, le blob est un bruit AES-GCM
//     inexploitable.
//   - NE PROTÈGE PAS contre : une session déjà déverrouillée (le code est en
//     mémoire tant que l'onglet est ouvert), un keylogger, ou quelqu'un qui
//     connaît déjà le code de l'agence. Ce n'est pas un système multi-utilisateur
//     avec des comptes distincts — c'est un secret partagé par terminal,
//     au même niveau qu'un code PIN de carte SIM.
//   - Le code n'est jamais transmis au central ni stocké nulle part : il
//     n'existe que dans la tête de l'agent et dans la clé dérivée en mémoire.
//     Un code oublié signifie une base locale définitivement illisible
//     (voir PinGate.jsx) — c'est le prix normal d'un vrai chiffrement.
const PBKDF2_ITERATIONS = 210_000; // recommandation OWASP (2023) pour PBKDF2-HMAC-SHA256
const SALT_BYTES = 16;
const IV_BYTES = 12; // taille recommandée pour AES-GCM

export function generateSalt() {
  return crypto.getRandomValues(new Uint8Array(SALT_BYTES));
}

async function importPinAsKeyMaterial(pin) {
  const encoded = new TextEncoder().encode(pin);
  return crypto.subtle.importKey("raw", encoded, "PBKDF2", false, ["deriveKey"]);
}

/** Dérive une clé AES-256-GCM à partir du code agence + sel (jamais le code seul). */
export async function deriveKey(pin, salt) {
  const keyMaterial = await importPinAsKeyMaterial(pin);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

export async function encryptBytes(key, plainBytes) {
  const iv = crypto.getRandomValues(new Uint8Array(IV_BYTES));
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plainBytes);
  return { iv, ciphertext: new Uint8Array(ciphertext) };
}

/**
 * Déchiffre. AES-GCM inclut un tag d'authentification : un mauvais code
 * (donc une mauvaise clé) ne produit jamais un déchiffrement "silencieux"
 * avec des données corrompues — l'opération échoue franchement (exception).
 * C'est ce qui nous permet de dire "code incorrect" avec certitude côté UI.
 */
export async function decryptBytes(key, iv, ciphertext) {
  const plainBuffer = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ciphertext);
  return new Uint8Array(plainBuffer);
}
