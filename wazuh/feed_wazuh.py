#!/usr/bin/env python3
"""
Connecteur GABRIEL : moteur de filtrage sentinellecoop -> SIEM Wazuh.

Le resultat du filtrage d'entree en relation (guichet) est emis vers Wazuh
(UDP 514) sous forme d'evenements JSON consommes par the regles 100400-100409
(fichier regles/0501-regles-cif-uemoa.xml).

Usage :
    python3 feed_wazuh.py "Mohammed Ould Abdelaziz"        # filtre + envoi du resultat
    python3 feed_wazuh.py --demo                           # 6 evenements CIF de demonstration
    python3 feed_wazuh.py --events evt.json                # envoi d'un lot d'evenements JSON

Mapping des decisions du moteur vers the regles Wazuh :
    BLOQUANT   -> filtrage_sanctions result=MATCH        (regles 100400)
    INFORMATIF -> filtrage_sanctions result=POSSIBLE_MATCH (regles 100403)
"""

import json
import socket
import sys

HOTE_CIBLE = ("127.0.0.1", 514)
SOURCE_LISTE = "scsanctions.un.org"


def socket_udp() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def cible():
    if len(sys.argv) >= 3 and sys.argv[1] == "--hote":
        port = int(sys.argv[3][1:]) if len(sys.argv) > 3 else 514
        return (sys.argv[2], port)
    return HOTE_CIBLE


def envoyer(evenements: list[dict], hote) -> int:
    nb = 0
    with socket_udp() as s:
        for ev in evenements:
            s.sendto(json.dumps(ev, ensure_ascii=False).encode(), hote)
            nb += 1
    return nb


def demo() -> list[dict]:
    return [
        {"event_type": "filtrage_sanctions", "mode": "ONU_consolidated", "subject": "ABDOU YAYA",
         "result": "MATCH", "source": SOURCE_LISTE},
        {"event_type": "virement", "customer_id": "CI100091", "beneficiary": "ORGANISATION ALPHA",
         "amount": "500000", "sanctioned": "yes", "result": "REJECTED"},
        {"event_type": "filtrage_personnes", "subject": "MAMADOU TOURE", "result": "PEP_HIT",
         "source": "GIABA"},
        {"event_type": "declaration_threshold", "customer_id": "CI555001", "amount": "11000000",
         "result": "EXCEEDED"},
        {"event_type": "desactivation_filtrage", "customer_id": "op_backoffice_7", "src_ip": "10.0.0.5"},
        {"event_type": "liste_sanctions_update", "source": SOURCE_LISTE, "records": "3231",
         "result": "FAILED"},
    ]


def filtrer_nom(nom: str) -> list[dict]:
    """Exécute le filtrage sentinellecoop puis traduit la décision en événement Wazuh."""
    try:
        from sentinellecoop.ingest import charger_onu, date_generation
        from sentinellecoop.matcher import SEUIL_INFORMATIF, Index
    except ImportError as e:
        sys.exit(f"[feed_wazuh] module sentinellecoop indisponible ({e}). "
                 f"Exécuter depuis la racine du dépôt ou utiliser --demo / --events.")

    entrees = charger_onu()
    index = Index.depuis(entrees)
    resultats = index.filtrer(nom, seuil=SEUIL_INFORMATIF)

    evenements = []
    for r in resultats:
        if r.niveau == "SOUS_SEUIL":
            continue
        if r.niveau == "BLOQUANT":
            result, mode = "MATCH", "ONU_consolidated"
        else:
            result, mode = "POSSIBLE_MATCH", "ONU"
        ev = {
            "event_type": "filtrage_sanctions",
            "mode": mode,
            "subject": nom.upper(),
            "matched_name": r.nom_liste if r.niveau == "INFORMATIF" else None,
            "result": result,
            "score": round(r.score, 3),
            "source": SOURCE_LISTE,
        }
        evenements.append({k: v for k, v in ev.items() if v is not None})
    return evenements


def lot_json(chemin: str) -> list[dict]:
    with open(chemin, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--demo":
        evenements, lib = demo(), "démo"
    elif sys.argv[1] == "--events":
        evenements, lib = lot_json(sys.argv[2]), sys.argv[2]
    elif sys.argv[1] == "--hote":
        nom = sys.argv[4]
        evenements, lib = filtrer_nom(nom), f"filtrage de « {nom} »"
    else:
        nom = sys.argv[1]
        evenements, lib = filtrer_nom(nom), f"filtrage de « {nom} »"

    hote = cible()
    if evenements:
        nb = envoyer(evenements, hote)
        print(f"[feed_wazuh] {nb} événement(s) CIF ({lib}) envoyés à {hote[0]}:{hote[1]}")
    else:
        print(f"[feed_wazuh] {lib} : AUCUNE correspondance — rien à transmettre.")
    for ev in evenements:
        print("   ", json.dumps(ev, ensure_ascii=False))


if __name__ == "__main__":
    main()