import { useEffect, useState } from "react";
import { hasExistingDatabase } from "../db/localDb";

// Écran de verrouillage du terminal — le seul endroit où le code agence
// transite (jamais envoyé au réseau, voir db/crypto.js). Bloque l'accès à
// la base locale tant que le code n'est pas validé, mais ne bloque rien
// d'autre : aucune dépendance réseau ici, ça fonctionne aussi hors-ligne.
export default function PinGate({ onUnlock }) {
  const [mode, setMode] = useState(null); // "create" | "unlock"
  const [pin, setPin] = useState("");
  const [pin2, setPin2] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    hasExistingDatabase().then((exists) => setMode(exists ? "unlock" : "create"));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (pin.length < 4) {
      setError("Le code doit faire au moins 4 caractères.");
      return;
    }
    if (mode === "create" && pin !== pin2) {
      setError("Les deux codes ne correspondent pas.");
      return;
    }
    setBusy(true);
    try {
      await onUnlock(pin);
    } catch (err) {
      setError(err.message || "Code incorrect.");
      setBusy(false);
    }
  }

  if (mode === null) return null; // évite un flash "create" pendant la lecture d'IndexedDB

  return (
    <main style={{ fontFamily: "sans-serif", padding: 24, maxWidth: 360, margin: "72px auto" }}>
      <h1 style={{ fontSize: 18, marginBottom: 4 }}>Terminal verrouillé</h1>
      <p style={{ fontSize: 13, color: "#57655F" }}>
        {mode === "create"
          ? "Première utilisation de ce terminal : choisissez un code pour chiffrer la base locale (clients, alertes) au repos."
          : "Entrez le code de ce terminal pour déchiffrer sa base locale."}
      </p>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 10 }}>
        <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
          Code du terminal
          <input
            type="password"
            inputMode="numeric"
            autoFocus
            value={pin}
            onChange={(e) => setPin(e.target.value)}
          />
        </label>
        {mode === "create" && (
          <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
            Confirmer le code
            <input type="password" inputMode="numeric" value={pin2} onChange={(e) => setPin2(e.target.value)} />
          </label>
        )}
        {error && <p style={{ color: "#B3261E", fontSize: 12, margin: 0 }}>{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "…" : mode === "create" ? "Créer et démarrer" : "Déverrouiller"}
        </button>
      </form>
      {mode === "unlock" && (
        <p style={{ fontSize: 11, color: "#9AACA5", marginTop: 16 }}>
          Code oublié : il n'existe volontairement aucune porte dérobée (voir
          frontend/src/offline/README.md, section sécurité) — c'est le prix d'un chiffrement réel.
          Un administrateur devra réinitialiser ce terminal.
        </p>
      )}
    </main>
  );
}
