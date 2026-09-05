"""
Referentiels complementaires a la liste ONU, pour que le moteur puisse
filtrer les scenarios du dataset synthetique (data/scenarios.md).

data/sanctions_demo.csv reprend a l'identique les entrees de demonstration
deja utilisees par demo/app.js (ONU-DEM-017, ONU-DEM-061) : elles ne
proviennent pas de la vraie liste ONU (data/un_consolidated.xml) et ne
doivent jamais etre presentees comme telles hors demo.

data/ppe_internes.csv est le referentiel des Personnes Politiquement
Exposees (art. 29), distinct par nature des listes de sanctions : une PPE
n'est pas sanctionnee, elle appelle une vigilance renforcee et une
reevaluation periodique (art. 29 : reevaluation triennale).
"""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .ingest import Personne

RACINE = Path(__file__).resolve().parent.parent
CSV_SANCTIONS_DEMO = RACINE / "data" / "sanctions_demo.csv"
CSV_PPE = RACINE / "data" / "ppe_internes.csv"


def charger_sanctions_demo(chemin: Path = CSV_SANCTIONS_DEMO) -> list[Personne]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return [
            Personne(
                identifiant=ligne["id"],
                nom=ligne["nom"],
                alias=[a for a in ligne["alias"].split("|") if a],
                liste=ligne["liste"],
                type_entree=ligne["type_entree"],
            )
            for ligne in csv.DictReader(f)
        ]


@dataclass
class EntreePPE:
    id: str
    nom: str
    alias: list[str]
    fonction: str
    depuis: str
    reexamen_prochain: str

    def en_retard(self, aujourd_hui: date | None = None) -> bool:
        aujourd_hui = aujourd_hui or date.today()
        echeance = date.fromisoformat(self.reexamen_prochain)
        return echeance < aujourd_hui


def charger_ppe(chemin: Path = CSV_PPE) -> list[EntreePPE]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return [
            EntreePPE(
                id=ligne["id"],
                nom=ligne["nom"],
                alias=[a for a in ligne["alias"].split("|") if a],
                fonction=ligne["fonction"],
                depuis=ligne["depuis"],
                reexamen_prochain=ligne["reexamen_prochain"],
            )
            for ligne in csv.DictReader(f)
        ]


def trouver_ppe(nom_client: str, ppe: list[EntreePPE]) -> EntreePPE | None:
    """Rapprochement exact sur le nom ou un alias declare.

    Le rapprochement approximatif (variantes phonetiques) releve du moteur
    M2 (matcher.Index) ; ce referentiel interne, plus restreint, se pretant
    a une comparaison stricte le temps que le calibrage phonetique dedie aux
    PPE soit priorise.
    """
    cible = nom_client.strip().casefold()
    for entree in ppe:
        candidats = [entree.nom, *entree.alias]
        if cible in {c.strip().casefold() for c in candidats}:
            return entree
    return None
