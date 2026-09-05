"""
Encodage phonétique ouest-africain (WAPE) et algorithmes de comparaison.

Aucune dépendance externe : le module doit tourner sur un poste de guichet
modeste, sans installation, conformément au principe hors-ligne d'abord.

Le WAPE n'a pas pour but de rendre deux variantes strictement identiques —
objectif irréaliste sur des noms comme Muhammad / Mahamadou. Il les rapproche
suffisamment pour qu'une distance de chaînes tranche ensuite de façon fiable.
C'est la combinaison des deux couches qui fait la détection, pas l'encodeur seul.
"""

import re
import unicodedata
from functools import lru_cache

# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

# Titres, particules et connecteurs patronymiques d'usage inconstant dans les
# états civils de l'espace UEMOA. Leur présence ou absence ne doit jamais
# faire échouer un rapprochement.
HONORIFIQUES = {
    "el", "al", "hadj", "hadji", "elhadj", "elhadji", "alhaji", "alhadji",
    "hajj", "hadjia", "haja", "cheikh", "cheick", "sheikh", "cheikhna",
    "mallam", "malam", "imam", "alhaj", "sidi", "sid",
    # connecteurs patronymiques sahéliens
    "ould", "ag", "ben", "bin", "ibn", "wld",
    # titres administratifs parfois saisis dans le champ nom
    "mr", "mme", "dr", "pr", "naba",
}

_NON_ALPHA = re.compile(r"[^a-z\s]")
_ESPACES = re.compile(r"\s+")


def deplier(texte: str) -> str:
    """Minuscules, suppression des diacritiques, ponctuation ramenée à l'espace."""
    texte = texte.lower().strip()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = texte.replace("-", " ").replace("'", " ").replace("’", " ")
    texte = _NON_ALPHA.sub(" ", texte)
    return _ESPACES.sub(" ", texte).strip()


@lru_cache(maxsize=100_000)
def _jetons_cache(nom: str) -> tuple[str, ...]:
    return tuple(t for t in deplier(nom).split() if t and t not in HONORIFIQUES)


def jetons(nom: str) -> list[str]:
    """Découpe un nom en jetons signifiants, honorifiques écartés."""
    return list(_jetons_cache(nom))


# --------------------------------------------------------------------------
# WAPE — West African Phonetic Encoding
# --------------------------------------------------------------------------

# L'ordre des règles est significatif : chaque substitution est appliquée sur
# le résultat de la précédente.
_REGLES = [
    # digraphes français et translittérations arabes
    ("sch", "sh"),
    ("ph", "f"),
    ("ch", "sh"),
    ("kh", "k"),
    ("gh", "g"),
    ("th", "t"),
    # 'ou' français == 'u' anglais == 'w' initial : Ouédraogo / Wedraogo
    ("ou", "u"),
    ("oo", "u"),
    ("w", "u"),
    # g doux français
    ("gu", "g"),
    ("ge", "je"),
    ("gi", "ji"),
    ("gy", "ji"),
    # c dur / c doux / q / x
    ("ck", "k"),
    ("ce", "se"),
    ("ci", "si"),
    ("cy", "si"),
    ("c", "k"),
    ("q", "k"),
    ("x", "ks"),
    # palatalisation : Diallo / Jallo / Djallo — Dyara / Jara
    ("dj", "j"),
    ("dy", "j"),
    ("dia", "ja"),
    ("die", "je"),
    ("dio", "ju"),
    ("diu", "ju"),
    # y consonantique ramené à i
    ("y", "i"),
    # h non prononcé : Mohamed / Moamed
    ("h", ""),
]

_DOUBLES = re.compile(r"(.)\1+")

# Classes vocaliques : o/u fusionnés (Mohamed / Muhammad),
# e/i fusionnés (Cissé / Cissi). Le 'a' reste distinct.
_TABLE_VOYELLES = str.maketrans({"o": "u", "e": "i"})


@lru_cache(maxsize=200_000)
def wape(jeton: str) -> str:
    """Code phonétique d'un jeton unique déjà déplié."""
    if not jeton:
        return ""
    code = jeton
    for motif, remplacement in _REGLES:
        code = code.replace(motif, remplacement)
    # 'e' final muet du français : Cisse -> Ciss
    if len(code) > 2 and code.endswith("e"):
        code = code[:-1]
    code = _DOUBLES.sub(r"\1", code)          # consonnes doublées
    code = code.translate(_TABLE_VOYELLES)     # classes vocaliques
    code = _DOUBLES.sub(r"\1", code)          # doublons nés du repliement
    return code


def code_nom(nom: str) -> str:
    """Code WAPE d'un nom complet, jetons triés pour absorber l'inversion
    nom/prénom entre la pièce d'identité et la saisie au guichet."""
    return " ".join(sorted(wape(j) for j in jetons(nom)))


def squelette(jeton: str) -> str:
    """Squelette consonantique — clé de blocage grossière pour l'indexation."""
    return re.sub(r"[aeiu]", "", wape(jeton))


# --------------------------------------------------------------------------
# Référence : Soundex (le moteur « classique » servant de témoin au benchmark)
# --------------------------------------------------------------------------

_SOUNDEX = {
    **dict.fromkeys("bfpv", "1"),
    **dict.fromkeys("cgjkqsxz", "2"),
    **dict.fromkeys("dt", "3"),
    "l": "4",
    **dict.fromkeys("mn", "5"),
    "r": "6",
}


def soundex(jeton: str) -> str:
    """Soundex américain standard, tel qu'implémenté par les moteurs du marché."""
    jeton = deplier(jeton).replace(" ", "")
    if not jeton:
        return ""
    premiere = jeton[0].upper()
    codes = [_SOUNDEX.get(c, "") for c in jeton]
    sortie = []
    precedent = codes[0]
    for c, code in zip(jeton[1:], codes[1:]):
        if code and code != precedent:
            sortie.append(code)
        if c not in "hw":          # h et w ne séparent pas deux codes égaux
            precedent = code
    return (premiere + "".join(sortie) + "000")[:4]


def code_nom_soundex(nom: str) -> str:
    return " ".join(sorted(soundex(j) for j in jetons(nom)))


# --------------------------------------------------------------------------
# Distances de chaînes
# --------------------------------------------------------------------------

def jaro(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    portee = max(len(a), len(b)) // 2 - 1
    if portee < 0:
        portee = 0
    a_vu = [False] * len(a)
    b_vu = [False] * len(b)
    correspondances = 0
    for i, ca in enumerate(a):
        debut = max(0, i - portee)
        fin = min(i + portee + 1, len(b))
        for j in range(debut, fin):
            if not b_vu[j] and b[j] == ca:
                a_vu[i] = b_vu[j] = True
                correspondances += 1
                break
    if not correspondances:
        return 0.0
    # transpositions
    k = 0
    transpositions = 0
    for i, vu in enumerate(a_vu):
        if not vu:
            continue
        while not b_vu[k]:
            k += 1
        if a[i] != b[k]:
            transpositions += 1
        k += 1
    transpositions //= 2
    m = correspondances
    return (m / len(a) + m / len(b) + (m - transpositions) / m) / 3


def jaro_winkler(a: str, b: str, p: float = 0.1) -> float:
    """Jaro pondéré par le préfixe commun — les erreurs de saisie portent
    rarement sur les premières lettres d'un patronyme."""
    base = jaro(a, b)
    prefixe = 0
    for ca, cb in zip(a[:4], b[:4]):
        if ca != cb:
            break
        prefixe += 1
    return base + prefixe * p * (1 - base)


def damerau_levenshtein(a: str, b: str) -> int:
    """Distance d'édition avec transpositions (alignement optimal)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if not la:
        return lb
    if not lb:
        return la
    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cout = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cout)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[la][lb]


@lru_cache(maxsize=500_000)
def similarite_jeton(a: str, b: str) -> float:
    """Similarité [0,1] entre deux jetons, calculée sur leurs codes WAPE.

    Combine Jaro-Winkler (robuste aux insertions/omissions) et la distance
    d'édition normalisée (robuste aux transpositions), en retenant la plus
    favorable des deux : chacune rattrape les angles morts de l'autre.
    """
    ca, cb = wape(a), wape(b)
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0
    jw = jaro_winkler(ca, cb)
    dl = 1 - damerau_levenshtein(ca, cb) / max(len(ca), len(cb))
    return max(jw, dl)
