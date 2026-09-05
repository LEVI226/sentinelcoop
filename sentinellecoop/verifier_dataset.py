"""
Verifie que le moteur produit, pour chaque client du dataset synthetique
(data/scenarios.md), exactement le verdict attendu — ni oubli, ni fausse
alerte. Sert de test de non-regression pour M2 (filtrage), M1 (PPE) et les
detections M3/M4 ajoutees dans verdicts.py.

Execution :  python -m sentinellecoop.verifier_dataset
"""

import sys

from .dataset import Portefeuille
from .ingest import charger_onu
from .matcher import Index
from .referentiel_demo import charger_ppe, charger_sanctions_demo
from .verdicts import evaluer_client

# (categorie, severite) attendus par client — voir data/scenarios.md,
# tableau « Verdicts attendus, par client ».
ATTENDU: dict[str, set[tuple[str, str]]] = {
    # Diallo Mamadou : filtrage (nom deja sanctionne), fractionnement et
    # consolidation multi-comptes (LBC), collecte fractionnee et
    # activation-dispersion (FT) — plusieurs typologies sur le meme profil,
    # deliberement, plutot que d'inventer des clients supplementaires.
    "C-1029": {("FILTRAGE", "BLOQUANT"), ("LBC", "INFORMATIF"),
               ("FT", "INFORMATIF"), ("FT", "BLOQUANT")},
    # Awa Sawadogo : temoin neutre, aucune alerte attendue.
    "C-2214": set(),
    # Ouedraogo Salif : PPE (referentiel interne) et compte rebond (LBC).
    "C-3091": {("PPE", "INFORMATIF"), ("LBC", "BLOQUANT")},
}


def construire_index() -> Index:
    referentiel = charger_onu() + charger_sanctions_demo()
    return Index.depuis(referentiel)


def executer() -> int:
    portefeuille = Portefeuille.charger()
    index = construire_index()
    ppe = charger_ppe()

    echecs = 0
    print(f"{'Client':10} {'Scenario':32} {'Attendu':22} {'Obtenu':22} Statut")
    print("-" * 95)

    for client in portefeuille.clients:
        verdicts = evaluer_client(client, portefeuille, index, ppe)
        obtenu = {(v.categorie, v.severite) for v in verdicts}
        attendu = ATTENDU.get(client.id, set())
        ok = obtenu == attendu
        echecs += 0 if ok else 1

        texte_attendu = ", ".join(f"{c}/{s}" for c, s in sorted(attendu)) or "aucune"
        texte_obtenu = ", ".join(f"{c}/{s}" for c, s in sorted(obtenu)) or "aucune"
        statut = "OK" if ok else "ECHEC"
        print(f"{client.id:10} {client.scenario:32} {texte_attendu:22} "
              f"{texte_obtenu:22} {statut}")

        if not ok:
            for v in verdicts:
                print(f"    -> {v.categorie}/{v.severite} : {v.motif}")

    print("-" * 95)
    total = len(portefeuille.clients)
    print(f"{total - echecs}/{total} clients conformes au verdict attendu.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(executer())
