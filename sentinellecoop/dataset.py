"""
Chargement du dataset synthetique de clients, comptes et transactions.

Voir data/scenarios.md pour la description de chaque scenario et le verdict
attendu. Ce module ne fait que charger les CSV en objets Python ; la logique
de detection (M3/M4) vit dans verdicts.py.
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CSV_CLIENTS = RACINE / "data" / "clients.csv"
CSV_COMPTES = RACINE / "data" / "comptes.csv"
CSV_TRANSACTIONS = RACINE / "data" / "transactions.csv"


@dataclass
class Client:
    id: str
    nom: str
    type: str
    agence: str
    ppe: bool
    date_ouverture: str
    scenario: str
    rationale_activite: str = ""


@dataclass
class Compte:
    id: str
    client_id: str
    agence: str
    solde: int
    date_ouverture: str = ""


@dataclass
class Transaction:
    id: str
    compte_id: str
    date_heure: str
    montant: int
    sens: str
    compte_contrepartie_id: str = ""
    canal: str = ""
    scenario_tag: str = ""


def charger_clients(chemin: Path = CSV_CLIENTS) -> list[Client]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return [
            Client(
                id=ligne["id"],
                nom=ligne["nom"],
                type=ligne["type"],
                agence=ligne["agence"],
                ppe=ligne["ppe"].strip().lower() == "oui",
                date_ouverture=ligne["date_ouverture"],
                scenario=ligne["scenario"],
                rationale_activite=ligne.get("rationale_activite", ""),
            )
            for ligne in csv.DictReader(f)
        ]


def charger_comptes(chemin: Path = CSV_COMPTES) -> list[Compte]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return [
            Compte(
                id=ligne["id"],
                client_id=ligne["client_id"],
                agence=ligne["agence"],
                solde=int(ligne["solde"]),
                date_ouverture=ligne.get("date_ouverture", ""),
            )
            for ligne in csv.DictReader(f)
        ]


def charger_transactions(chemin: Path = CSV_TRANSACTIONS) -> list[Transaction]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return [
            Transaction(
                id=ligne["id"],
                compte_id=ligne["compte_id"],
                date_heure=ligne["date_heure"],
                montant=int(ligne["montant"]),
                sens=ligne["sens"],
                compte_contrepartie_id=ligne.get("compte_contrepartie_id", ""),
                canal=ligne.get("canal", ""),
                scenario_tag=ligne.get("scenario_tag", ""),
            )
            for ligne in csv.DictReader(f)
        ]


@dataclass
class Portefeuille:
    """Regroupement pratique pour interroger le dataset par client."""

    clients: list[Client] = field(default_factory=list)
    comptes: list[Compte] = field(default_factory=list)
    transactions: list[Transaction] = field(default_factory=list)

    @classmethod
    def charger(cls) -> "Portefeuille":
        return cls(
            clients=charger_clients(),
            comptes=charger_comptes(),
            transactions=charger_transactions(),
        )

    def comptes_de(self, client_id: str) -> list[Compte]:
        return [c for c in self.comptes if c.client_id == client_id]

    def transactions_de(self, compte_id: str) -> list[Transaction]:
        return [t for t in self.transactions if t.compte_id == compte_id]
