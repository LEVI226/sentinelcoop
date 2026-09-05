"""
Mesure comparative du moteur WAPE face à un Soundex de référence.

C'est la preuve chiffrée annoncée au §3.1 de la note de présentation. Un test
de rappel seul ne prouve rien — un moteur qui accepte tout détecte 100 % des
variantes et noie l'agent sous les faux positifs. Le protocole mesure donc
conjointement :

  1. le RAPPEL   : part des variantes attestées correctement rapprochées ;
  2. le BRUIT    : part des paires de noms sans rapport déclenchant à tort ;
  3. la MARGE    : écart entre le score des vraies variantes et celui des
                   paires sans rapport — ce qui détermine si un seuil existe.

Exécution :  python -m sentinellecoop.benchmark
"""

import csv
import random
from pathlib import Path

from .ingest import charger_onu
from .matcher import (SEUIL_BLOQUANT, SEUIL_INFORMATIF, PoidsJetons,
                      correspond_soundex, correspond_soundex_souple,
                      similarite_nom)
from .phonetics import code_nom

RACINE = Path(__file__).resolve().parent.parent
JEU_TEST = RACINE / "data" / "variantes_noms_ao.csv"
ECHANTILLON_BRUIT = 4000
GRAINE = 20260904  # premier jour du hackathon de Ouagadougou


def charger_variantes(chemin: Path = JEU_TEST) -> list[tuple[str, str, str]]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return [(l["reference"], l["variante"], l["categorie"])
                for l in csv.DictReader(f)]


# --------------------------------------------------------------------------
# Méthodes comparées
# --------------------------------------------------------------------------

def methodes(poids: PoidsJetons | None):
    """Chaque méthode répond : ce couple de noms déclenche-t-il une alerte ?"""
    return {
        "Soundex strict (tous jetons)":
            lambda a, b: correspond_soundex(a, b),
        "Soundex souple (un jeton)":
            lambda a, b: correspond_soundex_souple(a, b),
        "WAPE — code identique":
            lambda a, b: code_nom(a) == code_nom(b),
        f"WAPE + similarité ≥ {SEUIL_INFORMATIF:.2f} (informatif)":
            lambda a, b: similarite_nom(a, b, poids) >= SEUIL_INFORMATIF,
        f"WAPE + similarité ≥ {SEUIL_BLOQUANT:.2f} (bloquant)":
            lambda a, b: similarite_nom(a, b, poids) >= SEUIL_BLOQUANT,
    }


def paires_sans_rapport(noms: list[str], n: int) -> list[tuple[str, str]]:
    """Couples de noms distincts tirés du référentiel : aucun ne devrait
    déclencher d'alerte. Sert de mesure du bruit."""
    rng = random.Random(GRAINE)
    paires = []
    vus = set()
    while len(paires) < n:
        a, b = rng.sample(noms, 2)
        if a == b or (a, b) in vus:
            continue
        vus.add((a, b))
        paires.append((a, b))
    return paires


# --------------------------------------------------------------------------
# Exécution
# --------------------------------------------------------------------------

def executer() -> None:
    variantes = charger_variantes()
    entrees = charger_onu()
    corpus = [e.nom for e in entrees] + [a for e in entrees for a in e.alias]
    poids = PoidsJetons(corpus)
    bruit = paires_sans_rapport([e.nom for e in entrees if e.nom], ECHANTILLON_BRUIT)

    categories = sorted({c for _, _, c in variantes})
    fns = methodes(poids)

    print("=" * 78)
    print("BENCHMARK — MOTEUR PHONETIQUE OUEST-AFRICAIN vs SOUNDEX DE REFERENCE")
    print("=" * 78)
    print(f"Jeu de variantes  : {len(variantes)} couples attestés, "
          f"{len(categories)} catégories")
    print(f"Référentiel       : {len(entrees)} entrées ONU, {len(corpus)} libellés")
    print(f"Echantillon bruit : {len(bruit)} couples de noms sans rapport")
    print()

    # ---- rappel global et bruit -----------------------------------------
    largeur = max(len(n) for n in fns)
    print(f"{'Méthode':<{largeur}}  {'Rappel':>8}  {'Bruit':>8}  {'Ecart':>8}")
    print("-" * (largeur + 30))
    resultats = {}
    for nom, fn in fns.items():
        rappel = sum(fn(a, b) for a, b, _ in variantes) / len(variantes)
        faux = sum(fn(a, b) for a, b in bruit) / len(bruit)
        resultats[nom] = (rappel, faux)
        print(f"{nom:<{largeur}}  {rappel:>7.1%}  {faux:>7.1%}  "
              f"{rappel - faux:>+7.1%}")
    print()

    # ---- rappel par catégorie -------------------------------------------
    print("RAPPEL PAR CATEGORIE DE VARIATION")
    print("-" * 78)
    entete = f"{'Catégorie':<16}{'n':>4}"
    for nom in fns:
        entete += f"{nom.split(' (')[0][:22]:>24}"
    print(entete)
    for cat in categories:
        sous = [(a, b) for a, b, c in variantes if c == cat]
        ligne = f"{cat:<16}{len(sous):>4}"
        for fn in fns.values():
            taux = sum(fn(a, b) for a, b in sous) / len(sous)
            ligne += f"{taux:>23.0%} "
        print(ligne)
    print()

    # ---- marge de séparation --------------------------------------------
    scores_vrais = [similarite_nom(a, b, poids) for a, b, _ in variantes]
    scores_faux = [similarite_nom(a, b, poids) for a, b in bruit]
    scores_faux.sort()
    p99 = scores_faux[int(0.99 * len(scores_faux))]
    vrais_tries = sorted(scores_vrais)
    p05 = vrais_tries[int(0.05 * len(vrais_tries))]
    print("MARGE DE SEPARATION (score WAPE pondéré)")
    print("-" * 78)
    print(f"  Variantes attestées   — score médian {vrais_tries[len(vrais_tries)//2]:.3f}"
          f", 5e centile {p05:.3f}")
    print(f"  Couples sans rapport  — score médian {scores_faux[len(scores_faux)//2]:.3f}"
          f", 99e centile {p99:.3f}")
    print(f"  Fenêtre exploitable pour le seuil : [{p99:.3f} ; {p05:.3f}]"
          f"{'  — VIDE, seuil non séparant' if p99 >= p05 else ''}")
    print()

    # ---- échecs résiduels ------------------------------------------------
    manques = [(a, b, c) for a, b, c in variantes
               if similarite_nom(a, b, poids) < SEUIL_INFORMATIF]
    print(f"VARIANTES NON DETECTEES PAR LE MOTEUR ({len(manques)}/{len(variantes)})")
    print("-" * 78)
    if not manques:
        print("  aucune")
    for a, b, c in manques:
        print(f"  [{c:<15}] {a:<28} / {b:<28} "
              f"score {similarite_nom(a, b, poids):.3f}")


if __name__ == "__main__":
    executer()
