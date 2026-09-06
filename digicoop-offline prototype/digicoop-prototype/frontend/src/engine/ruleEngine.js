// Règles transactionnelles simples et explicables — les seuils (montant,
// cumul, fréquence) sont des points de départ à ajuster avec les experts
// métier CIF présents pendant le hackathon, pas des valeurs figées.
export function evaluateTransaction(transaction, clientHistory = []) {
  const flags = [];

  if (transaction.amount >= 2_000_000) {
    flags.push({ rule: "montant_eleve", weight: 0.5, detail: `Montant élevé : ${transaction.amount} XOF` });
  }

  const last24h = clientHistory.filter(
    (t) => Date.now() - new Date(t.occurred_at).getTime() < 24 * 3600 * 1000
  );
  const sumLast24h = last24h.reduce((s, t) => s + t.amount, 0) + transaction.amount;

  if (sumLast24h >= 3_000_000 && last24h.length >= 2) {
    flags.push({
      rule: "cumul_24h",
      weight: 0.4,
      detail: `Cumul 24h : ${sumLast24h} XOF sur ${last24h.length + 1} opérations`,
    });
  }

  if (last24h.length >= 4) {
    flags.push({
      rule: "frequence_suspecte",
      weight: 0.3,
      detail: `${last24h.length + 1} opérations en 24h (structuration possible)`,
    });
  }

  const score = Math.min(1, flags.reduce((s, f) => s + f.weight, 0));
  return { score, flags };
}
