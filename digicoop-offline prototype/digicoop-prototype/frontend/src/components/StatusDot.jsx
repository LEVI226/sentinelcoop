import { useEffect, useState } from "react";
import { onQueueChange, getQueueSnapshot, retryDeadLetterEntries } from "../offline/syncWorker";

// Le seul indicateur de connectivité visible à l'écran — passif, jamais
// bloquant : il ne fait qu'informer, il n'interrompt jamais le travail
// de l'agent (voir la discussion sur la bascule silencieuse).
export default function StatusDot() {
  const [snap, setSnap] = useState(getQueueSnapshot());

  useEffect(() => onQueueChange(setSnap), []);

  const online = snap.connection === "online";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#57655F", flexWrap: "wrap" }}>
      <span
        style={{
          width: 9,
          height: 9,
          borderRadius: "50%",
          background: online ? "#1F6F5C" : "#9AACA5",
          display: "inline-block",
        }}
      />
      {online ? "synchronisé" : "hors-ligne — file en attente"}
      {snap.pending > 0 && <span>· {snap.pending} en attente</span>}
      {snap.dead_letter > 0 && (
        <>
          <span style={{ color: "#B8862E" }}>· {snap.dead_letter} à renvoyer manuellement</span>
          <button
            type="button"
            onClick={retryDeadLetterEntries}
            style={{
              fontSize: 11,
              padding: "2px 8px",
              border: "1px solid #B8862E",
              borderRadius: 4,
              background: "transparent",
              color: "#B8862E",
              cursor: "pointer",
            }}
            title="Remet ces entrées dans le cycle normal de synchronisation (elles avaient dépassé le nombre maximal de tentatives)."
          >
            Renvoyer
          </button>
        </>
      )}
    </div>
  );
}
