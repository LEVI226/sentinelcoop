"""
Exporte les donnees necessaires a l'interface guichet (guichet/) en un seul
fichier JSON statique, pour que le navigateur n'ait ni serveur d'API a
interroger ni logique metier a reimplementer de facon independante :

  - le referentiel de filtrage (ONU reelle + watchlist demo) et le
    referentiel PPE, pour que guichet/app.js calcule lui-meme le filtrage en
    temps reel sur un nom tape au guichet (algorithme WAPE porte en
    JavaScript dans guichet/moteur.js, fidele a phonetics.py/matcher.py) ;
  - les seuils de decision (SEUIL_BLOQUANT/SEUIL_INFORMATIF), pour qu'ils ne
    soient jamais dupliques en dur dans le JavaScript ;
  - par client, les comptes et transactions, et les verdicts LBC/FT deja
    calcules par verdicts.py (M3/M4) — ceux-la restent precalcules cote
    Python car ils dependent d'un historique de transactions horodatees que
    l'agent ne saisit pas au guichet, a la difference du filtrage nominal.

Execution :  python -m sentinellecoop.exporter_demo
Sortie     :  data/verdicts_demo.json
"""

import json
from dataclasses import asdict
from pathlib import Path

from .dataset import Portefeuille
from .ingest import charger_onu, date_generation
from .matcher import SEUIL_BLOQUANT, SEUIL_INFORMATIF
from .referentiel_demo import charger_ppe, charger_sanctions_demo
from .verdicts import (consolider, detecter_activation_dispersion,
                       detecter_collecte_fractionnee, detecter_compte_rebond,
                       detecter_fractionnement)

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "data" / "verdicts_demo.json"


def referentiel_json() -> list[dict]:
    entrees = charger_onu() + charger_sanctions_demo()
    return [
        {"id": e.identifiant, "nom": e.nom, "alias": e.alias,
         "liste": e.liste, "reference": e.reference, "type": e.type_entree}
        for e in entrees
    ]


def ppe_json() -> list[dict]:
    return [
        {"id": p.id, "nom": p.nom, "alias": p.alias, "fonction": p.fonction,
         "depuis": p.depuis, "reexamen_prochain": p.reexamen_prochain,
         "en_retard": p.en_retard()}
        for p in charger_ppe()
    ]


def verdicts_lbc_ft_json(client, portefeuille) -> list[dict]:
    comptes_du_client = portefeuille.comptes_de(client.id)
    verdicts = []

    v = consolider(client, comptes_du_client)
    if v:
        verdicts.append(v)

    for compte in comptes_du_client:
        txs = portefeuille.transactions_de(compte.id)
        for detecteur in (detecter_fractionnement, detecter_compte_rebond,
                          detecter_activation_dispersion,
                          detecter_collecte_fractionnee):
            v = detecteur(client.id, compte, txs)
            if v:
                verdicts.append(v)

    return [asdict(v) for v in verdicts]


def clients_json(portefeuille: Portefeuille) -> list[dict]:
    sortie = []
    for client in portefeuille.clients:
        comptes = portefeuille.comptes_de(client.id)
        sortie.append({
            "id": client.id,
            "nom": client.nom,
            "type": client.type,
            "agence": client.agence,
            "ppe": client.ppe,
            "comptes": [
                {"id": c.id, "agence": c.agence, "solde": c.solde}
                for c in comptes
            ],
            "solde_consolide": sum(c.solde for c in comptes),
            "transactions": [
                {"id": t.id, "compte_id": t.compte_id, "date_heure": t.date_heure,
                 "montant": t.montant, "sens": t.sens,
                 "compte_contrepartie_id": t.compte_contrepartie_id,
                 "canal": t.canal}
                for t in sorted(portefeuille.transactions,
                                key=lambda t: t.date_heure)
                if t.compte_id in {c.id for c in comptes}
            ],
            "verdicts_lbc_ft": verdicts_lbc_ft_json(client, portefeuille),
        })
    return sortie


def executer() -> None:
    portefeuille = Portefeuille.charger()
    sortie = {
        "genere_le": date_generation(),
        "seuils": {"bloquant": SEUIL_BLOQUANT, "informatif": SEUIL_INFORMATIF},
        "referentiel": referentiel_json(),
        "ppe": ppe_json(),
        "clients": clients_json(portefeuille),
    }
    SORTIE.write_text(json.dumps(sortie, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    print(f"{SORTIE} ecrit : {len(sortie['referentiel'])} entrees referentiel, "
          f"{len(sortie['ppe'])} PPE, {len(sortie['clients'])} clients.")


if __name__ == "__main__":
    executer()
