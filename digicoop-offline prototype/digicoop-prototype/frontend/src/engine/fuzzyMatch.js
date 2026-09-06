// Moteur de correspondance floue — pur JS, sans dépendance externe, pour
// rester explicable devant un jury (pas de boîte noire) et léger sur un
// Android d'entrée de gamme.
//
// OPTIMISATION (voir frontend/src/engine/BENCHMARK.md) : la version initiale
// calculait un Levenshtein complet contre CHAQUE entrée de la liste de
// surveillance, sans sortie anticipée. Sur une vraie liste consolidée
// (ONU + UE + PPE nationale, facilement 10 000 à 50 000 entrées), ça
// dépassait largement le budget "temps réel" promis dans l'architecture.
// La version ci-dessous calcule EXACTEMENT le même résultat (aucune perte
// de rappel, aucun faux négatif introduit) mais s'arrête dès qu'il est
// mathématiquement certain qu'une entrée ne peut pas atteindre le seuil,
// sans avoir à terminer le calcul de la matrice complète.

function normalize(name) {
  return (name || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // enlève les accents (Traoré → traore)
    .replace(/[^a-z\s-]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Distance de Levenshtein plafonnée : si la distance réelle dépasse
 * maxDistance, la fonction s'arrête dès que c'est prouvé et renvoie
 * maxDistance + 1 (une valeur "au-delà du seuil", jamais un score exact
 * inventé). Deux sorties anticipées, toutes deux sans perte d'exactitude :
 *   1. Si |len(a) - len(b)| > maxDistance, la distance ne peut de toute
 *      façon jamais être ≤ maxDistance (identité mathématique connue).
 *   2. Pendant le calcul ligne par ligne, si le minimum de la ligne
 *      courante dépasse déjà maxDistance, aucune case suivante ne pourra
 *      redescendre en dessous (les coûts n'ajoutent jamais de valeur
 *      négative) — on arrête immédiatement.
 */
function levenshteinBounded(a, b, maxDistance) {
  const m = a.length;
  const n = b.length;

  if (Math.abs(m - n) > maxDistance) return maxDistance + 1;
  if (maxDistance < 0) return 0;

  let prevRow = new Array(n + 1);
  for (let j = 0; j <= n; j++) prevRow[j] = j;

  for (let i = 1; i <= m; i++) {
    const currRow = new Array(n + 1);
    currRow[0] = i;
    let rowMin = currRow[0];

    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      currRow[j] = Math.min(prevRow[j] + 1, currRow[j - 1] + 1, prevRow[j - 1] + cost);
      if (currRow[j] < rowMin) rowMin = currRow[j];
    }

    if (rowMin > maxDistance) return maxDistance + 1; // preuve suffisante, inutile de continuer
    prevRow = currRow;
  }

  return prevRow[n];
}

/**
 * Similarité exacte entre deux noms (0 à 1). Identique bit à bit à
 * l'ancienne implémentation non plafonnée — utilisée pour les quelques
 * candidats qui survivent au filtre rapide de matchAgainstWatchlist.
 */
export function similarity(nameA, nameB) {
  const a = normalize(nameA);
  const b = normalize(nameB);
  if (!a.length && !b.length) return 1;
  const maxLen = Math.max(a.length, b.length) || 1;
  const distance = levenshteinBounded(a, b, maxLen); // maxDistance = maxLen -> jamais plafonné, résultat exact
  return 1 - distance / maxLen;
}

/**
 * Compare un nom de client à toute la liste de surveillance en cache local
 * et retourne les correspondances au-dessus du seuil, triées par score.
 *
 * Optimisation : pour chaque entrée, on calcule d'abord la distance
 * plafonnée au maximum tolérable par le seuil (maxDistance = (1-seuil) *
 * longueur). Si l'entrée est rejetée par ce calcul plafonné, elle est de
 * toute façon sous le seuil — on ne perd donc aucune correspondance
 * valide (aucun faux négatif introduit), on économise juste le calcul
 * complet sur les entrées manifestement non pertinentes, qui sont
 * l'immense majorité d'une liste de sanctions face à un client donné.
 *
 * threshold=0.72 est un point de départ à ajuster avec les experts métier
 * CIF pendant le hackathon (trop bas = trop de faux positifs, trop haut =
 * on rate des homonymies/translittérations).
 */
export function matchAgainstWatchlist(clientName, watchlist, threshold = 0.72) {
  const a = normalize(clientName);
  const results = [];

  for (const entry of watchlist) {
    const b = normalize(entry.full_name);
    const maxLen = Math.max(a.length, b.length) || 1;
    const maxDistance = Math.floor((1 - threshold) * maxLen);

    const distance = levenshteinBounded(a, b, maxDistance);
    if (distance > maxDistance) continue; // preuve mathématique : sous le seuil, rejeté sans ambiguïté

    results.push({ entry, score: 1 - distance / maxLen });
  }

  return results.sort((x, y) => y.score - x.score);
}
