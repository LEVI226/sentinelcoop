/*
 * Portage JavaScript du moteur de filtrage phonetique ouest-africain.
 *
 * Fidele ligne a ligne a sentinellecoop/phonetics.py et matcher.py (Python,
 * "moteur de reference" de SentinelleCoop) : memes regles WAPE, memes
 * distances de chaines, meme ponderation par rarete, memes seuils. C'est un
 * portage documente, pas une reimplementation independante — en cas de
 * doute sur une regle, la source de verite reste le fichier Python cite en
 * commentaire a cote de chaque fonction.
 *
 * Necessaire cote navigateur parce que le filtrage nominal (M2) doit
 * reagir en temps reel a un nom tape au guichet (art. 20 du TDR) : il n'y a
 * pas de serveur d'API a interroger dans cette demo hors-ligne, seulement
 * des fichiers statiques.
 */

// -- Normalisation ---------------------------------------------------------
// cf. phonetics.py: HONORIFIQUES, deplier(), jetons()

const HONORIFIQUES = new Set([
  "el", "al", "hadj", "hadji", "elhadj", "elhadji", "alhaji", "alhadji",
  "hajj", "hadjia", "haja", "cheikh", "cheick", "sheikh", "cheikhna",
  "mallam", "malam", "imam", "alhaj", "sidi", "sid",
  "ould", "ag", "ben", "bin", "ibn", "wld",
  "mr", "mme", "dr", "pr", "naba",
]);

const _MARQUES_DIACRITIQUES = new RegExp("[\\u0300-\\u036f]", "g");

function deplier(texte) {
  texte = texte.toLowerCase().trim();
  texte = texte.normalize("NFD").replace(_MARQUES_DIACRITIQUES, "");
  texte = texte.replace(/[-'’]/g, " ");
  texte = texte.replace(/[^a-z\s]/g, " ");
  return texte.replace(/\s+/g, " ").trim();
}

function jetons(nom) {
  return deplier(nom).split(" ").filter((t) => t && !HONORIFIQUES.has(t));
}

// -- WAPE — West African Phonetic Encoding ---------------------------------
// cf. phonetics.py: _REGLES, wape(). L'ordre des regles est significatif.

const REGLES = [
  ["sch", "sh"], ["ph", "f"], ["ch", "sh"], ["kh", "k"], ["gh", "g"], ["th", "t"],
  ["ou", "u"], ["oo", "u"], ["w", "u"],
  ["gu", "g"], ["ge", "je"], ["gi", "ji"], ["gy", "ji"],
  ["ck", "k"], ["ce", "se"], ["ci", "si"], ["cy", "si"], ["c", "k"], ["q", "k"], ["x", "ks"],
  ["dj", "j"], ["dy", "j"], ["dia", "ja"], ["die", "je"], ["dio", "ju"], ["diu", "ju"],
  ["y", "i"],
  ["h", ""],
];

const _wapeCache = new Map();

function wape(jeton) {
  if (!jeton) return "";
  const cache = _wapeCache.get(jeton);
  if (cache !== undefined) return cache;
  let code = jeton;
  for (const [motif, remplacement] of REGLES) code = code.split(motif).join(remplacement);
  if (code.length > 2 && code.endsWith("e")) code = code.slice(0, -1);
  code = code.replace(/(.)\1+/g, "$1");
  code = code.replace(/o/g, "u").replace(/e/g, "i");
  code = code.replace(/(.)\1+/g, "$1");
  _wapeCache.set(jeton, code);
  return code;
}

// -- Distances de chaines ---------------------------------------------------
// cf. phonetics.py: jaro(), jaro_winkler(), damerau_levenshtein()

function jaro(a, b) {
  if (a === b) return 1.0;
  if (!a || !b) return 0.0;
  const portee = Math.max(0, Math.floor(Math.max(a.length, b.length) / 2) - 1);
  const aVu = new Array(a.length).fill(false);
  const bVu = new Array(b.length).fill(false);
  let correspondances = 0;
  for (let i = 0; i < a.length; i++) {
    const debut = Math.max(0, i - portee);
    const fin = Math.min(i + portee + 1, b.length);
    for (let j = debut; j < fin; j++) {
      if (!bVu[j] && b[j] === a[i]) {
        aVu[i] = bVu[j] = true;
        correspondances++;
        break;
      }
    }
  }
  if (!correspondances) return 0.0;
  let k = 0, transpositions = 0;
  for (let i = 0; i < a.length; i++) {
    if (!aVu[i]) continue;
    while (!bVu[k]) k++;
    if (a[i] !== b[k]) transpositions++;
    k++;
  }
  transpositions = Math.floor(transpositions / 2);
  const m = correspondances;
  return (m / a.length + m / b.length + (m - transpositions) / m) / 3;
}

function jaroWinkler(a, b, p = 0.1) {
  const base = jaro(a, b);
  let prefixe = 0;
  const n = Math.min(a.length, b.length, 4);
  for (let i = 0; i < n; i++) {
    if (a[i] !== b[i]) break;
    prefixe++;
  }
  return base + prefixe * p * (1 - base);
}

function damerauLevenshtein(a, b) {
  if (a === b) return 0;
  const la = a.length, lb = b.length;
  if (!la) return lb;
  if (!lb) return la;
  const d = Array.from({ length: la + 1 }, () => new Array(lb + 1).fill(0));
  for (let i = 0; i <= la; i++) d[i][0] = i;
  for (let j = 0; j <= lb; j++) d[0][j] = j;
  for (let i = 1; i <= la; i++) {
    for (let j = 1; j <= lb; j++) {
      const cout = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cout);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
      }
    }
  }
  return d[la][lb];
}

function similariteJeton(a, b) {
  const ca = wape(a), cb = wape(b);
  if (!ca || !cb) return 0.0;
  if (ca === cb) return 1.0;
  const jw = jaroWinkler(ca, cb);
  const dl = 1 - damerauLevenshtein(ca, cb) / Math.max(ca.length, cb.length);
  return Math.max(jw, dl);
}

// -- Ponderation par rarete du jeton -----------------------------------------
// cf. matcher.py: PoidsJetons

class PoidsJetons {
  constructor(corpus) {
    this.compte = new Map();
    this.total = 0;
    if (corpus) this.alimenter(corpus);
  }

  alimenter(corpus) {
    for (const nom of corpus) {
      const uniques = new Set(jetons(nom));
      for (const j of uniques) {
        const code = wape(j);
        this.compte.set(code, (this.compte.get(code) || 0) + 1);
      }
      this.total++;
    }
  }

  poids(jeton) {
    if (!this.total) return 1.0;
    const n = this.compte.get(wape(jeton)) || 0;
    return Math.log((this.total + 1) / (n + 1)) + 1.0;
  }
}

// -- Similarite au niveau du nom complet --------------------------------------
// cf. matcher.py: _score_directionnel(), similarite_nom()

function scoreDirectionnel(source, cible, poids) {
  let total = 0, sommePoids = 0;
  for (const ts of source) {
    let meilleure = 0;
    for (const tc of cible) meilleure = Math.max(meilleure, similariteJeton(ts, tc));
    const p = poids ? poids.poids(ts) : 1.0;
    total += meilleure * p;
    sommePoids += p;
  }
  return sommePoids ? total / sommePoids : 0;
}

function similariteNom(a, b, poids) {
  const ja = jetons(a), jb = jetons(b);
  if (!ja.length || !jb.length) return 0.0;
  const sab = scoreDirectionnel(ja, jb, poids);
  const sba = scoreDirectionnel(jb, ja, poids);
  if (sab <= 0 || sba <= 0) return 0.0;
  return (2 * sab * sba) / (sab + sba);
}

// -- Index de filtrage --------------------------------------------------------
// cf. matcher.py: Index

class Index {
  constructor(enregistrements) {
    this.enregistrements = enregistrements;
    const corpus = [];
    for (const e of enregistrements) {
      corpus.push(e.nom);
      for (const a of e.alias) corpus.push(a);
    }
    this.poids = new PoidsJetons(corpus);
  }

  filtrer(nom, seuil, limite = 10) {
    const trouvees = [];
    for (const e of this.enregistrements) {
      let meilleur = similariteNom(nom, e.nom, this.poids);
      let via = "";
      for (const alias of e.alias) {
        const s = similariteNom(nom, alias, this.poids);
        if (s > meilleur) {
          meilleur = s;
          via = alias;
        }
      }
      if (meilleur >= seuil) {
        trouvees.push({
          score: Math.round(meilleur * 10000) / 10000,
          nom_liste: e.nom,
          identifiant: e.id,
          liste: e.liste,
          reference: e.reference,
          via_alias: via,
        });
      }
    }
    trouvees.sort((a, b) => b.score - a.score);
    return trouvees.slice(0, limite);
  }
}
