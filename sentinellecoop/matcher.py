"""
Moteur de rapprochement : alignement de jetons, pondération par rareté,
double seuil bloquant / informatif (art. 21 et 91 de la Loi uniforme).
"""

import math
from collections import Counter
from dataclasses import dataclass, field

from .phonetics import code_nom_soundex, jetons, similarite_jeton, wape

# Seuils par défaut. Fixés dès le premier jour puis affinés — jamais bloquants
# pour la suite du développement (cf. plan des 72 heures).
SEUIL_BLOQUANT = 0.90
SEUIL_INFORMATIF = 0.80


# --------------------------------------------------------------------------
# Pondération par rareté du jeton
# --------------------------------------------------------------------------

class PoidsJetons:
    """Fréquence inverse des jetons dans le portefeuille.

    Dans un portefeuille burkinabè, « Ouédraogo » ne discrimine presque rien
    tandis qu'un prénom rare discrimine beaucoup. Pondérer par la rareté est
    le levier principal de réduction des faux positifs.
    """

    def __init__(self, corpus: list[str] | None = None):
        self.compte: Counter = Counter()
        self.total = 0
        if corpus:
            self.alimenter(corpus)

    def alimenter(self, corpus: list[str]) -> None:
        for nom in corpus:
            for j in set(jetons(nom)):
                self.compte[wape(j)] += 1
            self.total += 1

    def poids(self, jeton: str) -> float:
        if not self.total:
            return 1.0
        n = self.compte.get(wape(jeton), 0)
        return math.log((self.total + 1) / (n + 1)) + 1.0


# --------------------------------------------------------------------------
# Similarité au niveau du nom complet
# --------------------------------------------------------------------------

def _score_directionnel(source: list[str], cible: list[str],
                        poids: PoidsJetons | None) -> float:
    """Part pondérée des jetons de `source` retrouvés dans `cible`."""
    total = 0.0
    somme_poids = 0.0
    for ts in source:
        meilleure = max(similarite_jeton(ts, tc) for tc in cible)
        p = poids.poids(ts) if poids else 1.0
        total += meilleure * p
        somme_poids += p
    return total / somme_poids if somme_poids else 0.0


def similarite_nom(a: str, b: str, poids: PoidsJetons | None = None) -> float:
    """Similarité symétrique entre deux noms complets.

    L'alignement des jetons est indépendant de l'ordre : il absorbe l'inversion
    nom/prénom entre la pièce d'identité et la saisie au guichet.

    Le score est la **moyenne harmonique des deux directions**, et non la
    meilleure des deux. Ce choix corrige un défaut qui ne se voit qu'en
    conditions réelles : le référentiel ONU contient des alias d'un seul jeton
    (« Saleh », « Mohammad »). Une mesure unidirectionnelle leur accorde un
    score parfait dès qu'un jeton voisin figure dans le nom du client, et fait
    alerter « Salifou Ouédraogo » sur l'alias « Saleh ». La moyenne harmonique
    exige que les deux noms se recouvrent mutuellement, et effondre ce cas.
    """
    ja, jb = jetons(a), jetons(b)
    if not ja or not jb:
        return 0.0
    s_ab = _score_directionnel(ja, jb, poids)
    s_ba = _score_directionnel(jb, ja, poids)
    if s_ab <= 0 or s_ba <= 0:
        return 0.0
    return 2 * s_ab * s_ba / (s_ab + s_ba)


# --------------------------------------------------------------------------
# Résultat de filtrage
# --------------------------------------------------------------------------

@dataclass
class Correspondance:
    score: float
    nom_liste: str
    identifiant: str
    liste: str
    reference: str
    nationalite: str = ""
    naissance: str = ""
    via_alias: str = ""

    @property
    def niveau(self) -> str:
        if self.score >= SEUIL_BLOQUANT:
            return "BLOQUANT"
        if self.score >= SEUIL_INFORMATIF:
            return "INFORMATIF"
        return "SOUS_SEUIL"


@dataclass
class Index:
    """Index de filtrage sur le référentiel de sanctions."""

    enregistrements: list = field(default_factory=list)
    poids: PoidsJetons = field(default_factory=PoidsJetons)

    @classmethod
    def depuis(cls, enregistrements: list) -> "Index":
        idx = cls(enregistrements=enregistrements)
        corpus = []
        for e in enregistrements:
            corpus.append(e.nom)
            corpus.extend(e.alias)
        idx.poids = PoidsJetons(corpus)
        return idx

    def filtrer(self, nom: str, seuil: float = SEUIL_INFORMATIF,
                limite: int = 10) -> list[Correspondance]:
        """Filtre un nom contre l'intégralité du référentiel.

        Chaque alias est évalué au même titre que le nom principal : un client
        qui se présente sous un alias listé doit déclencher l'alerte.
        """
        trouvees: list[Correspondance] = []
        for e in self.enregistrements:
            meilleur = similarite_nom(nom, e.nom, self.poids)
            via = ""
            for alias in e.alias:
                s = similarite_nom(nom, alias, self.poids)
                if s > meilleur:
                    meilleur, via = s, alias
            if meilleur >= seuil:
                trouvees.append(Correspondance(
                    score=round(meilleur, 4),
                    nom_liste=e.nom,
                    identifiant=e.identifiant,
                    liste=e.liste,
                    reference=e.reference,
                    nationalite=e.nationalite,
                    naissance=e.naissance,
                    via_alias=via,
                ))
        trouvees.sort(key=lambda c: c.score, reverse=True)
        return trouvees[:limite]


# --------------------------------------------------------------------------
# Témoin : moteur « classique » fondé sur Soundex
# --------------------------------------------------------------------------

def correspond_soundex(a: str, b: str) -> bool:
    """Rapprochement tel que le pratique un moteur du marché non adapté :
    égalité stricte des codes Soundex de tous les jetons."""
    ca, cb = code_nom_soundex(a), code_nom_soundex(b)
    return bool(ca) and ca == cb


def correspond_soundex_souple(a: str, b: str) -> bool:
    """Variante indulgente : au moins un jeton partage son code Soundex.
    Fournit au témoin sa meilleure chance possible."""
    sa = {c for c in code_nom_soundex(a).split() if c}
    sb = {c for c in code_nom_soundex(b).split() if c}
    return bool(sa & sb)
