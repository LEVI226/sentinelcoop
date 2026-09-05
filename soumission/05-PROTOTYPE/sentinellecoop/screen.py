"""
Filtrage d'un client à l'entrée en relation — chaîne complète.

    python -m sentinellecoop.screen "Mohammed Ould Abdelaziz"

Le contrôle s'exécute intégralement en local : aucune donnée client ne quitte
l'institution, et la coupure du réseau n'interrompt pas le filtrage.
"""

import sys
import time
from datetime import datetime, timezone

from .ingest import charger_onu, date_generation
from .matcher import SEUIL_BLOQUANT, SEUIL_INFORMATIF, Index

DECISIONS = {
    "BLOQUANT": ("ALERTE BLOQUANTE",
                 "Opération suspendue (art. 91). Levée soumise à un profil habilité ; "
                 "information sans délai de l'autorité compétente."),
    "INFORMATIF": ("ALERTE INFORMATIVE",
                   "Mise en file de revue. Examen particulier au sens de l'art. 21 "
                   "et rapport confidentiel écrit à établir."),
}


def fraicheur() -> str:
    """Indicateur exigé en pratique par l'art. 89 : de quand date la liste ?"""
    brut = date_generation()
    if not brut:
        return "inconnue"
    genere = datetime.fromisoformat(brut.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - genere
    heures = delta.total_seconds() / 3600
    age = f"{heures:.1f} h" if heures < 48 else f"{delta.days} j"
    return f"{genere:%Y-%m-%d %H:%M UTC} (il y a {age})"


def filtrer(nom: str) -> int:
    entrees = charger_onu()
    index = Index.depuis(entrees)

    debut = time.perf_counter()
    resultats = index.filtrer(nom, seuil=SEUIL_INFORMATIF)
    ecoule = (time.perf_counter() - debut) * 1000

    print()
    print(f"  Référentiel ONU synchronisé : {fraicheur()}")
    print(f"  {len(entrees)} entrées filtrées en {ecoule:.0f} ms — hors ligne")
    print(f"  Seuils : bloquant {SEUIL_BLOQUANT:.2f} / informatif {SEUIL_INFORMATIF:.2f}")
    print()
    print(f"  CLIENT SAISI AU GUICHET : « {nom} »")
    print("  " + "-" * 72)

    if not resultats:
        print("  AUCUNE CORRESPONDANCE — entrée en relation autorisée.")
        print("  Décision horodatée et versée à la piste d'audit (art. 23).")
        print()
        return 0

    for r in resultats:
        if r.niveau == "SOUS_SEUIL":
            continue
        libelle, suite = DECISIONS[r.niveau]
        print(f"  {libelle}  —  score {r.score:.3f}")
        print(f"    Personne listée : {r.nom_liste}")
        if r.via_alias:
            print(f"    Rapprochement via l'alias : « {r.via_alias} »")
        details = [f"liste {r.liste}", f"réf. {r.reference}"]
        if r.nationalite:
            details.append(f"nationalité {r.nationalite}")
        if r.naissance:
            details.append(f"né(e) {r.naissance}")
        print(f"    {' — '.join(details)}")
        print(f"    Suite : {suite}")
        print()

    return 1 if any(r.niveau == "BLOQUANT" for r in resultats) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(filtrer(" ".join(sys.argv[1:])))
