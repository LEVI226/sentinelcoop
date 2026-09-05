"""
Verdicts M3 (profilage, consolidation) et M4 (comportemental) appliques au
dataset synthetique de data/clients.csv, comptes.csv et transactions.csv.

Le filtrage nominal (M2) et le referentiel PPE (M1) sont deja implementes
ailleurs (matcher.py, referentiel_demo.py) : ce module les orchestre et y
ajoute la logique qui manquait encore, decrite dans docs/ARCHITECTURE.md
section 3 comme relevant de l'axe feature/moteur-ia :

  - solde global consolide sur plusieurs comptes (art. 13 e) ;
  - fractionnement d'un depot sur une fenetre glissante (art. 21 a, LBC) ;
  - compte rebond : reception puis retransfert rapide (art. 13 f, LBC) ;
  - collecte fractionnee vers de multiples beneficiaires (FT) ;
  - activation puis dispersion rapide d'un compte peu actif (FT).

SEUIL_CUMUL_7J et SEUIL_UNITAIRE_ATTENTION reprennent les seuils deja choisis
par demo/app.js (sevenDayTotal >= 1 500 000, montant < 500 000 pour compter
comme fractionnement) : ce ne sont pas des valeurs nouvelles inventees pour ce
module, mais celles deja utilisees par la demo pour les memes 3 clients. Les
autres seuils (fenetres et ratios pour compte rebond, activation-dispersion,
collecte fractionnee) sont propres a ce module, car la demo n'a pas d'equivalent
date/horodate a leur emprunter — ce sont des seuils de demonstration (voir
data/scenarios.md « Seuils de demonstration »), pas calibres sur un
portefeuille reel.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .dataset import Client, Compte, Portefeuille, Transaction
from .matcher import Correspondance, Index
from .referentiel_demo import EntreePPE, trouver_ppe

SEUIL_CUMUL_7J = 1_500_000
FENETRE_CUMUL_JOURS = 7
SEUIL_UNITAIRE_ATTENTION = 500_000

SEUIL_CONSOLIDATION = 1_500_000

FENETRE_REBOND_HEURES = 2
RATIO_REBOND_MIN = 0.8

FENETRE_DISPERSION_HEURES = 6
MIN_SORTIES_DISPERSION = 3
RATIO_DISPERSION_MIN = 0.8

MIN_BENEFICIAIRES_COLLECTE = 4
FENETRE_COLLECTE_JOURS = 10


@dataclass
class Verdict:
    client_id: str
    categorie: str      # FILTRAGE | PPE | LBC | FT
    severite: str        # BLOQUANT | INFORMATIF
    motif: str
    details: dict = field(default_factory=dict)


def _date(t: Transaction) -> datetime:
    return datetime.strptime(t.date_heure, "%Y-%m-%d %H:%M")


# --------------------------------------------------------------------------
# M2 (filtrage nominal) + M1 (PPE) — orchestration
# --------------------------------------------------------------------------

def filtrer_client(client: Client, index: Index) -> Verdict | None:
    correspondances = index.filtrer(client.nom)
    if not correspondances:
        return None
    meilleure: Correspondance = correspondances[0]
    if meilleure.niveau == "SOUS_SEUIL":
        return None
    return Verdict(
        client_id=client.id,
        categorie="FILTRAGE",
        severite=meilleure.niveau,
        motif=f"rapprochement avec « {meilleure.nom_liste} » "
              f"({meilleure.liste}, score {meilleure.score})"
              + (f" via alias « {meilleure.via_alias} »" if meilleure.via_alias else ""),
        details={"identifiant_liste": meilleure.identifiant, "score": meilleure.score},
    )


def verifier_ppe(client: Client, ppe: list[EntreePPE]) -> Verdict | None:
    entree = trouver_ppe(client.nom, ppe)
    if entree is None:
        return None
    motif = f"personne politiquement exposee depuis {entree.depuis} ({entree.fonction})"
    if entree.en_retard():
        motif += " — reevaluation triennale en retard (art. 29)"
    return Verdict(
        client_id=client.id,
        categorie="PPE",
        severite="INFORMATIF",
        motif=motif,
        details={"ppe_id": entree.id, "en_retard": entree.en_retard()},
    )


# --------------------------------------------------------------------------
# M3 — consolidation multi-comptes
# --------------------------------------------------------------------------

def consolider(client: Client, comptes_du_client: list[Compte]) -> Verdict | None:
    if len(comptes_du_client) < 2:
        return None
    total = sum(c.solde for c in comptes_du_client)
    if total < SEUIL_CONSOLIDATION:
        return None
    if any(c.solde >= SEUIL_CONSOLIDATION for c in comptes_du_client):
        # Un compte isole depasse deja le seuil : ce n'est pas la
        # consolidation qui apporte l'information, pas de double-alerte.
        return None
    return Verdict(
        client_id=client.id,
        categorie="LBC",
        severite="INFORMATIF",
        motif=f"solde global consolide de {total} FCFA sur {len(comptes_du_client)} comptes "
              f"(agences : {', '.join(sorted({c.agence for c in comptes_du_client}))}), "
              f"alors qu'aucun compte pris isolement ne depasse le seuil",
        details={"total": total, "comptes": [c.id for c in comptes_du_client]},
    )


# --------------------------------------------------------------------------
# M4 — comportemental
# --------------------------------------------------------------------------

def detecter_fractionnement(client_id: str, compte: Compte,
                             transactions_du_compte: list[Transaction]) -> Verdict | None:
    entrees = sorted((t for t in transactions_du_compte if t.sens == "entree"),
                      key=_date)
    if len(entrees) < 2:
        return None
    if any(t.montant >= SEUIL_UNITAIRE_ATTENTION for t in entrees):
        return None
    span = _date(entrees[-1]) - _date(entrees[0])
    if span > timedelta(days=FENETRE_CUMUL_JOURS):
        return None
    total = sum(t.montant for t in entrees)
    if total < SEUIL_CUMUL_7J:
        return None
    return Verdict(
        client_id=client_id,
        categorie="LBC",
        severite="INFORMATIF",
        motif=f"{len(entrees)} depots de {min(t.montant for t in entrees)} a "
              f"{max(t.montant for t in entrees)} FCFA sur {span.days + 1} jours "
              f"(compte {compte.id}), cumul {total} FCFA, aucun depot "
              f"individuellement suspect",
        details={"compte": compte.id, "total": total,
                  "transactions": [t.id for t in entrees]},
    )


def detecter_compte_rebond(client_id: str, compte: Compte,
                            transactions_du_compte: list[Transaction]) -> Verdict | None:
    entrees = [t for t in transactions_du_compte if t.sens == "entree"]
    sorties = [t for t in transactions_du_compte if t.sens == "sortie"]
    for entree in entrees:
        for sortie in sorties:
            delai = _date(sortie) - _date(entree)
            if timedelta(0) < delai <= timedelta(hours=FENETRE_REBOND_HEURES) \
                    and sortie.montant >= RATIO_REBOND_MIN * entree.montant:
                minutes = int(delai.total_seconds() // 60)
                return Verdict(
                    client_id=client_id,
                    categorie="LBC",
                    severite="BLOQUANT",
                    motif=f"reception de {entree.montant} FCFA (compte {compte.id}) "
                          f"suivie {minutes} min plus tard d'un transfert sortant de "
                          f"{sortie.montant} FCFA vers {sortie.compte_contrepartie_id or 'un tiers'} "
                          f"— signature de layering",
                    details={"compte": compte.id, "entree": entree.id, "sortie": sortie.id,
                              "delai_minutes": minutes},
                )
    return None


def detecter_activation_dispersion(client_id: str, compte: Compte,
                                    transactions_du_compte: list[Transaction]) -> Verdict | None:
    entrees = [t for t in transactions_du_compte if t.sens == "entree"]
    for entree in entrees:
        fenetre_fin = _date(entree) + timedelta(hours=FENETRE_DISPERSION_HEURES)
        sorties = [
            t for t in transactions_du_compte
            if t.sens == "sortie" and _date(entree) < _date(t) <= fenetre_fin
        ]
        destinataires = {t.compte_contrepartie_id for t in sorties if t.compte_contrepartie_id}
        total_sorties = sum(t.montant for t in sorties)
        if len(destinataires) >= MIN_SORTIES_DISPERSION \
                and total_sorties >= RATIO_DISPERSION_MIN * entree.montant:
            return Verdict(
                client_id=client_id,
                categorie="FT",
                severite="BLOQUANT",
                motif=f"reception ponctuelle de {entree.montant} FCFA sur un compte peu actif "
                      f"(compte {compte.id}) suivie, en moins de {FENETRE_DISPERSION_HEURES}h, "
                      f"d'une dispersion de {total_sorties} FCFA vers {len(destinataires)} "
                      f"destinataires distincts",
                details={"compte": compte.id, "entree": entree.id,
                          "destinataires": sorted(destinataires), "total_sorties": total_sorties},
            )
    return None


def detecter_collecte_fractionnee(client_id: str, compte: Compte,
                                   transactions_du_compte: list[Transaction]) -> Verdict | None:
    if detecter_activation_dispersion(client_id, compte, transactions_du_compte):
        # Une reception suivie d'une dispersion rapide est deja qualifiee par
        # detecter_activation_dispersion : ne pas requalifier les memes
        # sorties en collecte, sous peine de doublon. Un seuil numerique fixe
        # ne suffit pas a distinguer les deux cas (une reception de 400 000
        # FCFA, sous SEUIL_UNITAIRE_ATTENTION, peut tout de meme declencher
        # une dispersion) ; se referer au detecteur lui-meme est la seule
        # facon de rester coherent avec ses propres conditions.
        return None
    sorties = sorted(
        (t for t in transactions_du_compte
         if t.sens == "sortie" and t.compte_contrepartie_id
         and t.montant < SEUIL_UNITAIRE_ATTENTION),
        key=_date,
    )
    beneficiaires = {t.compte_contrepartie_id for t in sorties}
    if len(beneficiaires) < MIN_BENEFICIAIRES_COLLECTE:
        return None
    span = _date(sorties[-1]) - _date(sorties[0])
    if span > timedelta(days=FENETRE_COLLECTE_JOURS):
        return None
    total = sum(t.montant for t in sorties)
    return Verdict(
        client_id=client_id,
        categorie="FT",
        severite="INFORMATIF",
        motif=f"{len(sorties)} transferts sortants de {min(t.montant for t in sorties)} a "
              f"{max(t.montant for t in sorties)} FCFA vers {len(beneficiaires)} "
              f"beneficiaires distincts sur {span.days + 1} jours (compte {compte.id}), "
              f"sans mouvement entrant correspondant",
        details={"compte": compte.id, "total": total,
                  "beneficiaires": sorted(beneficiaires)},
    )


# --------------------------------------------------------------------------
# Orchestration par client
# --------------------------------------------------------------------------

def evaluer_client(client: Client, portefeuille: Portefeuille,
                    index_sanctions: Index, ppe: list[EntreePPE]) -> list[Verdict]:
    verdicts: list[Verdict] = []

    v = filtrer_client(client, index_sanctions)
    if v:
        verdicts.append(v)

    v = verifier_ppe(client, ppe)
    if v:
        verdicts.append(v)

    comptes_du_client = portefeuille.comptes_de(client.id)

    v = consolider(client, comptes_du_client)
    if v:
        verdicts.append(v)

    for compte in comptes_du_client:
        txs = portefeuille.transactions_de(compte.id)
        for detecteur in (detecter_fractionnement, detecter_compte_rebond,
                          detecter_activation_dispersion, detecter_collecte_fractionnee):
            v = detecteur(client.id, compte, txs)
            if v:
                verdicts.append(v)

    return verdicts
