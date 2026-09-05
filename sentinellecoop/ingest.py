"""
Ingestion du référentiel de sanctions.

Source de démonstration : liste consolidée du Conseil de sécurité des Nations
unies, publique et gratuite. Les listes nationales communiquées par l'autorité
compétente au titre de l'article 124 se branchent sur le même modèle normalisé.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
XML_ONU = RACINE / "data" / "un_consolidated.xml"


@dataclass
class Personne:
    """Entrée normalisée du référentiel, commune à toutes les sources."""

    identifiant: str
    nom: str
    alias: list[str] = field(default_factory=list)
    liste: str = ""
    reference: str = ""
    nationalite: str = ""
    naissance: str = ""
    inscrit_le: str = ""
    type_entree: str = "PERSONNE"


def _texte(noeud, balise: str) -> str:
    e = noeud.find(balise)
    return (e.text or "").strip() if e is not None and e.text else ""


def _nom_complet(noeud) -> str:
    parts = [_texte(noeud, b) for b in
             ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")]
    return " ".join(p for p in parts if p)


def _alias(noeud, balise: str) -> list[str]:
    sorties = []
    for a in noeud.findall(balise):
        nom = _texte(a, "ALIAS_NAME")
        if nom:
            sorties.append(" ".join(nom.replace("\n", " ").split()))
    return sorties


def _nationalite(noeud) -> str:
    n = noeud.find("NATIONALITY")
    return _texte(n, "VALUE") if n is not None else ""


def _naissance(noeud) -> str:
    d = noeud.find("INDIVIDUAL_DATE_OF_BIRTH")
    if d is None:
        return ""
    for balise in ("DATE", "YEAR", "FROM_YEAR"):
        v = _texte(d, balise)
        if v:
            return v
    return ""


def charger_onu(chemin: Path = XML_ONU) -> list[Personne]:
    """Parse la liste consolidée ONU (personnes physiques et entités)."""
    racine = ET.parse(chemin).getroot()
    entrees: list[Personne] = []

    for n in racine.findall("INDIVIDUALS/INDIVIDUAL"):
        entrees.append(Personne(
            identifiant=_texte(n, "DATAID"),
            nom=_nom_complet(n),
            alias=_alias(n, "INDIVIDUAL_ALIAS"),
            liste=_texte(n, "UN_LIST_TYPE"),
            reference=_texte(n, "REFERENCE_NUMBER"),
            nationalite=_nationalite(n),
            naissance=_naissance(n),
            inscrit_le=_texte(n, "LISTED_ON"),
            type_entree="PERSONNE",
        ))

    for n in racine.findall("ENTITIES/ENTITY"):
        entrees.append(Personne(
            identifiant=_texte(n, "DATAID"),
            nom=_texte(n, "FIRST_NAME"),
            alias=_alias(n, "ENTITY_ALIAS"),
            liste=_texte(n, "UN_LIST_TYPE"),
            reference=_texte(n, "REFERENCE_NUMBER"),
            inscrit_le=_texte(n, "LISTED_ON"),
            type_entree="ENTITE",
        ))

    return entrees


def date_generation(chemin: Path = XML_ONU) -> str:
    """Horodatage de génération de la liste — matière première de
    l'indicateur de fraîcheur exigé par l'article 89."""
    return ET.parse(chemin).getroot().get("dateGenerated", "")


if __name__ == "__main__":
    entrees = charger_onu()
    personnes = [e for e in entrees if e.type_entree == "PERSONNE"]
    alias = sum(len(e.alias) for e in entrees)
    print(f"Liste ONU générée le : {date_generation()}")
    print(f"{len(personnes)} personnes, {len(entrees) - len(personnes)} entités, "
          f"{alias} alias")
    for e in personnes[:3]:
        print(f"  [{e.reference}] {e.nom} — {len(e.alias)} alias — liste {e.liste}")
