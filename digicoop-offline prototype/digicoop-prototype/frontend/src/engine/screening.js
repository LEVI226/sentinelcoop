// Orchestre le parcours de contrôle en local, en temps réel :
// client → comptes et solde global → filtrage PPE/sanctions → opération
// contrôlée → alerte persistante (le renvoi vers sync_queue est fait par
// l'appelant, voir components/ClientForm.jsx et syncWorker.js).
import { all } from "../db/localDb";
import { matchAgainstWatchlist } from "./fuzzyMatch";
import { evaluateTransaction } from "./ruleEngine";

// Étape 2 : comptes & solde global — agrégation multi-comptes, 100% locale.
export function getClientOverview(clientId) {
  const transactions = all(
    "SELECT * FROM transactions WHERE client_id = ? ORDER BY occurred_at DESC",
    [clientId]
  );
  const balance = transactions.reduce(
    (s, t) => s + (t.tx_type === "withdrawal" ? -t.amount : t.amount),
    0
  );
  return { transactions, balance };
}

// Étape 3 : filtrage PPE/sanctions — fuzzy matching contre le cache local.
export function screenClient(client) {
  const watchlist = all("SELECT * FROM watchlist_cache");
  return matchAgainstWatchlist(client.full_name, watchlist);
}

// Étape 4 : opération contrôlée — décision immédiate (autorisée / surveillée / retenue).
export function screenOperation(client, transaction) {
  const { transactions } = getClientOverview(client.id);
  const nameMatches = screenClient(client);
  const ruleResult = evaluateTransaction(transaction, transactions);
  const bestMatch = nameMatches[0];

  let severity = null;
  if (bestMatch && bestMatch.score >= 0.9) severity = "blocking";
  else if (bestMatch && bestMatch.score >= 0.72) severity = "informative";
  else if (ruleResult.score >= 0.7) severity = "blocking";
  else if (ruleResult.score >= 0.4) severity = "informative";

  const decision =
    severity === "blocking" ? "retenue" : severity === "informative" ? "autorisee_surveillee" : "autorisee";

  return { decision, severity, nameMatches, ruleResult };
}
