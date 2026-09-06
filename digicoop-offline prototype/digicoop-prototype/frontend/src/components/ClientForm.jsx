import { useState } from "react";
import { run } from "../db/localDb";
import { screenOperation } from "../engine/screening";
import { enqueueSync } from "../offline/syncWorker";
import { uuidv4 } from "../utils/uuid";

// Étape 1 (client) + déclenche 2, 3, 4 et 5 du parcours de contrôle,
// entièrement en local et en temps réel — voir engine/screening.js.
export default function ClientForm({ onResult }) {
  const [fullName, setFullName] = useState("");
  const [amount, setAmount] = useState("");

  function handleSubmit(e) {
    e.preventDefault();

    const client = { id: uuidv4(), full_name: fullName, birth_date: null, id_document: null };
    const createdAt = new Date().toISOString();
    run(
      "INSERT INTO clients (id, full_name, birth_date, id_document, created_at) VALUES (?, ?, ?, ?, ?)",
      [client.id, client.full_name, client.birth_date, client.id_document, createdAt]
    );
    enqueueSync("client", client.id, { ...client, created_at: createdAt });

    let transaction = { amount: 0, occurred_at: createdAt };
    if (amount) {
      transaction = {
        id: uuidv4(),
        client_id: client.id,
        amount: parseFloat(amount),
        currency: "XOF",
        tx_type: "deposit",
        occurred_at: createdAt,
      };
      run(
        "INSERT INTO transactions (id, client_id, amount, currency, tx_type, occurred_at) VALUES (?, ?, ?, ?, ?, ?)",
        [transaction.id, transaction.client_id, transaction.amount, transaction.currency, transaction.tx_type, transaction.occurred_at]
      );
      enqueueSync("transaction", transaction.id, transaction);
    }

    // Étape 3 + 4 : filtrage temps réel et décision sur l'opération.
    const result = screenOperation(client, transaction);

    // Étape 5 : alerte persistante — seulement si quelque chose a été détecté.
    if (result.severity) {
      const alertId = uuidv4();
      const bestMatch = result.nameMatches[0];
      const alertCreatedAt = new Date().toISOString();
      run(
        `INSERT INTO alerts (id, client_id, transaction_id, matched_name, match_score, severity, decision, created_at)
         VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)`,
        [
          alertId,
          client.id,
          transaction.id || null,
          bestMatch ? bestMatch.entry.full_name : null,
          bestMatch ? bestMatch.score : result.ruleResult.score,
          result.severity,
          alertCreatedAt,
        ]
      );
      enqueueSync("alert", alertId, {
        client_id: client.id,
        transaction_id: transaction.id || null,
        matched_name: bestMatch ? bestMatch.entry.full_name : null,
        match_score: bestMatch ? bestMatch.score : result.ruleResult.score,
        severity: result.severity,
        decision: "pending",
      });
    }

    onResult({ client, transaction, result });
    setFullName("");
    setAmount("");
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 420, marginTop: 16 }}>
      <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
        Nom complet du client
        <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </label>
      <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
        Montant de l'opération (XOF, optionnel)
        <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
      </label>
      <button type="submit">Filtrer et enregistrer</button>
    </form>
  );
}
