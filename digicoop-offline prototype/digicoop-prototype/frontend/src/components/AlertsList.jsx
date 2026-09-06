import { useEffect, useState } from "react";
import { all } from "../db/localDb";

// Étape 6 (vue locale) : ce que l'agent voit tant que le central n'a pas
// encore reçu la synchronisation — utile aussi pour la démo réseau coupé.
export default function AlertsList({ refreshKey }) {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    setAlerts(all("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 20"));
  }, [refreshKey]);

  if (alerts.length === 0) {
    return <p style={{ color: "#57655F", fontSize: 13 }}>Aucune alerte locale pour l'instant.</p>;
  }

  return (
    <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse", marginTop: 12 }}>
      <thead>
        <tr style={{ textAlign: "left", color: "#57655F" }}>
          <th>Client</th>
          <th>Correspondance</th>
          <th>Sévérité</th>
          <th>Décision</th>
        </tr>
      </thead>
      <tbody>
        {alerts.map((a) => (
          <tr key={a.id}>
            <td>{a.client_id.slice(0, 8)}…</td>
            <td>{a.matched_name || "règle transactionnelle"}</td>
            <td>{a.severity}</td>
            <td>{a.decision}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
