#!/usr/bin/env python3
"""Generate a complete synthetic Topic 1 dataset for the CIF hackathon demo."""

from __future__ import annotations

import csv
from pathlib import Path


OUT = Path("corpusCIF/topic1_lbc_ft/05_jeu_donnees_synthetique/dataset_demo")


def write_csv(filename: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    caisses = [
        {"caisse_id": "CAISSE_DORI", "nom": "Caisse populaire de Dori", "ville": "Dori", "pays": "Burkina Faso", "zone_risque": "rouge", "seuil_depot": 500000, "seuil_retrait": 500000, "delai_revue_alerte_h": 4, "mode_connectivite": "intermittente"},
        {"caisse_id": "CAISSE_BANFORA", "nom": "Caisse populaire de Banfora", "ville": "Banfora", "pays": "Burkina Faso", "zone_risque": "verte", "seuil_depot": 1000000, "seuil_retrait": 1000000, "delai_revue_alerte_h": 24, "mode_connectivite": "stable"},
        {"caisse_id": "CAISSE_OUAGA", "nom": "Caisse urbaine Ouagadougou", "ville": "Ouagadougou", "pays": "Burkina Faso", "zone_risque": "orange", "seuil_depot": 750000, "seuil_retrait": 750000, "delai_revue_alerte_h": 8, "mode_connectivite": "stable"},
        {"caisse_id": "CAISSE_COTONOU", "nom": "Caisse partenaire Cotonou", "ville": "Cotonou", "pays": "Benin", "zone_risque": "verte", "seuil_depot": 1200000, "seuil_retrait": 1200000, "delai_revue_alerte_h": 24, "mode_connectivite": "stable"},
    ]

    clients = [
        {"global_client_id": "GCLI_001", "local_client_id": "DOR_0001", "caisse_origine": "CAISSE_DORI", "type_client": "personne_physique", "nom": "KABORE AMADOU", "alias": "KABRE AMADOU", "date_naissance": "1984-03-18", "nationalite": "Burkina Faso", "activite": "commerce betail", "statut_ppe": "false", "score_risque_initial": 68},
        {"global_client_id": "GCLI_002", "local_client_id": "BAN_0001", "caisse_origine": "CAISSE_BANFORA", "type_client": "personne_physique", "nom": "OUEDRAOGO SALIFOU", "alias": "WEDRAOGO SALIF", "date_naissance": "1979-11-02", "nationalite": "Burkina Faso", "activite": "transport", "statut_ppe": "false", "score_risque_initial": 35},
        {"global_client_id": "GCLI_003", "local_client_id": "OUA_0001", "caisse_origine": "CAISSE_OUAGA", "type_client": "personne_physique", "nom": "DIALLO MAMADOU", "alias": "JALLO MAMADOU", "date_naissance": "1990-05-14", "nationalite": "Mali", "activite": "transfert marchandises", "statut_ppe": "false", "score_risque_initial": 62},
        {"global_client_id": "GCLI_004", "local_client_id": "DOR_0002", "caisse_origine": "CAISSE_DORI", "type_client": "personne_physique", "nom": "SAWADOGO FATIMATA", "alias": "", "date_naissance": "1993-07-09", "nationalite": "Burkina Faso", "activite": "petit commerce", "statut_ppe": "true", "score_risque_initial": 72},
        {"global_client_id": "GCLI_005", "local_client_id": "BAN_0002", "caisse_origine": "CAISSE_BANFORA", "type_client": "personne_physique", "nom": "NIKIEMA ALI", "alias": "", "date_naissance": "1988-01-22", "nationalite": "Burkina Faso", "activite": "agriculture", "statut_ppe": "false", "score_risque_initial": 28},
        {"global_client_id": "GCLI_006", "local_client_id": "OUA_0002", "caisse_origine": "CAISSE_OUAGA", "type_client": "personne_morale", "nom": "SOCIETE SAHEL TRADING", "alias": "SAHEL TRADING SARL", "date_naissance": "", "nationalite": "Burkina Faso", "activite": "import export", "statut_ppe": "false", "score_risque_initial": 70},
        {"global_client_id": "GCLI_007", "local_client_id": "COT_0001", "caisse_origine": "CAISSE_COTONOU", "type_client": "personne_morale", "nom": "ONG SOLIDARITE FRONTIERE", "alias": "OSF BENIN", "date_naissance": "", "nationalite": "Benin", "activite": "association humanitaire", "statut_ppe": "false", "score_risque_initial": 64},
        {"global_client_id": "GCLI_008", "local_client_id": "DOR_0003", "caisse_origine": "CAISSE_DORI", "type_client": "personne_physique", "nom": "MAIGA OUSMANE", "alias": "OUMAR MAIGA", "date_naissance": "1981-09-30", "nationalite": "Mali", "activite": "orpaillage", "statut_ppe": "false", "score_risque_initial": 78},
    ]

    pieces = [
        {"piece_id": "PID_001", "global_client_id": "GCLI_001", "type_piece": "CNIB", "numero_fictif": "BFA-19840318-001", "date_expiration": "2027-12-31", "statut": "valide"},
        {"piece_id": "PID_002", "global_client_id": "GCLI_002", "type_piece": "CNIB", "numero_fictif": "BFA-19791102-002", "date_expiration": "2026-08-31", "statut": "expiree"},
        {"piece_id": "PID_003", "global_client_id": "GCLI_003", "type_piece": "Passeport", "numero_fictif": "MLI-19900514-003", "date_expiration": "2028-05-01", "statut": "valide"},
        {"piece_id": "PID_004", "global_client_id": "GCLI_004", "type_piece": "CNIB", "numero_fictif": "BFA-19930709-004", "date_expiration": "2029-02-10", "statut": "valide"},
        {"piece_id": "PID_005", "global_client_id": "GCLI_005", "type_piece": "CNIB", "numero_fictif": "BFA-19880122-005", "date_expiration": "2027-01-01", "statut": "valide"},
        {"piece_id": "PID_006", "global_client_id": "GCLI_006", "type_piece": "RCCM", "numero_fictif": "RCCM-BF-OUA-006", "date_expiration": "2030-01-01", "statut": "valide"},
        {"piece_id": "PID_007", "global_client_id": "GCLI_007", "type_piece": "RCCM", "numero_fictif": "RCCM-BJ-COT-007", "date_expiration": "2030-01-01", "statut": "valide"},
        {"piece_id": "PID_008", "global_client_id": "GCLI_008", "type_piece": "CNIB", "numero_fictif": "MLI-19810930-008", "date_expiration": "2026-12-15", "statut": "valide"},
    ]

    beneficiaires = [
        {"beneficiaire_id": "BE_001", "global_client_id": "GCLI_006", "nom": "TRAORE ADAMA", "date_naissance": "1975-04-18", "part_detention": 60, "statut_ppe": "false"},
        {"beneficiaire_id": "BE_002", "global_client_id": "GCLI_006", "nom": "SANKARA MARIAM", "date_naissance": "1980-09-12", "part_detention": 40, "statut_ppe": "true"},
        {"beneficiaire_id": "BE_003", "global_client_id": "GCLI_007", "nom": "HOUNTONJI PAUL", "date_naissance": "1972-06-20", "part_detention": 0, "statut_ppe": "false"},
    ]

    comptes = [
        {"compte_id": "CPT_DOR_001", "global_client_id": "GCLI_001", "caisse_id": "CAISSE_DORI", "type_produit": "epargne", "date_ouverture": "2025-02-10", "solde": 425000, "statut": "actif"},
        {"compte_id": "CPT_BAN_001", "global_client_id": "GCLI_001", "caisse_id": "CAISSE_BANFORA", "type_produit": "depot", "date_ouverture": "2026-09-05", "solde": 980000, "statut": "actif"},
        {"compte_id": "CPT_BAN_002", "global_client_id": "GCLI_002", "caisse_id": "CAISSE_BANFORA", "type_produit": "epargne", "date_ouverture": "2024-11-12", "solde": 75000, "statut": "actif"},
        {"compte_id": "CPT_OUA_001", "global_client_id": "GCLI_003", "caisse_id": "CAISSE_OUAGA", "type_produit": "mobile", "date_ouverture": "2026-07-10", "solde": 130000, "statut": "actif"},
        {"compte_id": "CPT_DOR_002", "global_client_id": "GCLI_004", "caisse_id": "CAISSE_DORI", "type_produit": "epargne", "date_ouverture": "2026-08-20", "solde": 220000, "statut": "actif"},
        {"compte_id": "CPT_BAN_003", "global_client_id": "GCLI_005", "caisse_id": "CAISSE_BANFORA", "type_produit": "credit", "date_ouverture": "2025-05-01", "solde": -350000, "statut": "actif"},
        {"compte_id": "CPT_OUA_002", "global_client_id": "GCLI_006", "caisse_id": "CAISSE_OUAGA", "type_produit": "depot", "date_ouverture": "2026-01-18", "solde": 2200000, "statut": "actif"},
        {"compte_id": "CPT_COT_001", "global_client_id": "GCLI_007", "caisse_id": "CAISSE_COTONOU", "type_produit": "depot", "date_ouverture": "2026-03-11", "solde": 1800000, "statut": "actif"},
        {"compte_id": "CPT_DOR_003", "global_client_id": "GCLI_008", "caisse_id": "CAISSE_DORI", "type_produit": "epargne", "date_ouverture": "2026-09-01", "solde": 1500000, "statut": "actif"},
    ]

    mandats = [
        {"mandat_id": "MAND_001", "global_client_id": "GCLI_001", "mandataire_nom": "KABORE ISSA", "mandataire_piece": "CNIB-MAND-001", "date_debut": "2026-09-01", "date_fin": "2026-09-30", "plafond": 300000, "statut": "valide"},
        {"mandat_id": "MAND_002", "global_client_id": "GCLI_002", "mandataire_nom": "SOME PAUL", "mandataire_piece": "CNIB-MAND-002", "date_debut": "2026-08-01", "date_fin": "2026-09-01", "plafond": 200000, "statut": "expire"},
        {"mandat_id": "MAND_003", "global_client_id": "GCLI_008", "mandataire_nom": "SOME PAUL", "mandataire_piece": "CNIB-MAND-002", "date_debut": "2026-09-01", "date_fin": "2026-12-31", "plafond": 500000, "statut": "valide"},
    ]

    watchlists = [
        {"liste_id": "WL_001", "type_liste": "sanction", "nom": "KABRE AMADOU", "alias": "KABORE AMADOU", "pays": "Burkina Faso", "date_naissance": "1984-03-18", "criticite": "haute", "source": "synthetique_demo"},
        {"liste_id": "WL_002", "type_liste": "ppe", "nom": "SAWADOGO FATIMATA", "alias": "", "pays": "Burkina Faso", "date_naissance": "1993-07-09", "criticite": "moyenne", "source": "synthetique_demo"},
        {"liste_id": "WL_003", "type_liste": "sanction", "nom": "DIALLO MAMADOU", "alias": "JALLO MAMADOU", "pays": "Mali", "date_naissance": "1990-05-14", "criticite": "haute", "source": "synthetique_demo"},
        {"liste_id": "WL_004", "type_liste": "ppe", "nom": "SANKARA MARIAM", "alias": "", "pays": "Burkina Faso", "date_naissance": "1980-09-12", "criticite": "moyenne", "source": "synthetique_demo"},
        {"liste_id": "WL_005", "type_liste": "sanction", "nom": "MAIGA OUMAR", "alias": "OUMAR MAIGA", "pays": "Mali", "date_naissance": "1981-09-30", "criticite": "haute", "source": "synthetique_demo"},
    ]

    operations = [
        {"operation_id": "OP_001", "date_operation": "2026-09-05T08:30:00", "caisse_id": "CAISSE_DORI", "compte_id": "CPT_DOR_001", "type_operation": "depot", "montant": 240000, "canal": "guichet", "motif": "vente betail", "origine_fonds": "recette marche", "justificatif_id": "", "mandat_id": ""},
        {"operation_id": "OP_002", "date_operation": "2026-09-05T10:15:00", "caisse_id": "CAISSE_DORI", "compte_id": "CPT_DOR_001", "type_operation": "depot", "montant": 245000, "canal": "guichet", "motif": "vente betail", "origine_fonds": "recette marche", "justificatif_id": "", "mandat_id": ""},
        {"operation_id": "OP_003", "date_operation": "2026-09-05T15:40:00", "caisse_id": "CAISSE_DORI", "compte_id": "CPT_DOR_001", "type_operation": "depot", "montant": 230000, "canal": "guichet", "motif": "vente betail", "origine_fonds": "recette marche", "justificatif_id": "", "mandat_id": ""},
        {"operation_id": "OP_004", "date_operation": "2026-09-06T09:00:00", "caisse_id": "CAISSE_BANFORA", "compte_id": "CPT_BAN_001", "type_operation": "depot", "montant": 980000, "canal": "guichet", "motif": "commerce", "origine_fonds": "non renseignee", "justificatif_id": "", "mandat_id": ""},
        {"operation_id": "OP_005", "date_operation": "2026-09-06T11:20:00", "caisse_id": "CAISSE_BANFORA", "compte_id": "CPT_BAN_002", "type_operation": "retrait_procuration", "montant": 250000, "canal": "guichet", "motif": "depense familiale", "origine_fonds": "", "justificatif_id": "FORM_RET_002", "mandat_id": "MAND_002"},
        {"operation_id": "OP_006", "date_operation": "2026-09-06T13:10:00", "caisse_id": "CAISSE_OUAGA", "compte_id": "CPT_OUA_001", "type_operation": "virement", "montant": 600000, "canal": "mobile", "motif": "achat marchandises", "origine_fonds": "activite commerciale", "justificatif_id": "JUS_006", "mandat_id": ""},
        {"operation_id": "OP_007", "date_operation": "2026-09-06T14:00:00", "caisse_id": "CAISSE_DORI", "compte_id": "CPT_DOR_002", "type_operation": "ouverture_compte", "montant": 20000, "canal": "guichet", "motif": "adhesion", "origine_fonds": "epargne personnelle", "justificatif_id": "", "mandat_id": ""},
        {"operation_id": "OP_008", "date_operation": "2026-09-07T09:30:00", "caisse_id": "CAISSE_OUAGA", "compte_id": "CPT_OUA_002", "type_operation": "depot", "montant": 1500000, "canal": "virement", "motif": "contrat import", "origine_fonds": "client entreprise", "justificatif_id": "JUS_008", "mandat_id": ""},
        {"operation_id": "OP_009", "date_operation": "2026-09-07T10:45:00", "caisse_id": "CAISSE_DORI", "compte_id": "CPT_DOR_003", "type_operation": "retrait", "montant": 900000, "canal": "guichet", "motif": "achat or", "origine_fonds": "", "justificatif_id": "", "mandat_id": ""},
        {"operation_id": "OP_010", "date_operation": "2026-09-07T16:00:00", "caisse_id": "CAISSE_COTONOU", "compte_id": "CPT_COT_001", "type_operation": "depot", "montant": 1100000, "canal": "guichet", "motif": "don projet", "origine_fonds": "bailleur fictif", "justificatif_id": "JUS_010", "mandat_id": ""},
    ]

    alertes_attendues = [
        {"alerte_id": "ALT_001", "operation_id": "OP_001", "global_client_id": "GCLI_001", "type_alerte": "sanction", "niveau": "bloquant", "score": 96, "motif": "Correspondance forte avec liste sanction synthetique", "statut": "nouvelle"},
        {"alerte_id": "ALT_002", "operation_id": "OP_003", "global_client_id": "GCLI_001", "type_alerte": "fractionnement", "niveau": "informatif", "score": 82, "motif": "Trois depots sous seuil dans la meme journee a Dori", "statut": "nouvelle"},
        {"alerte_id": "ALT_003", "operation_id": "OP_004", "global_client_id": "GCLI_001", "type_alerte": "multi_comptes", "niveau": "informatif", "score": 76, "motif": "Client avec comptes dans Dori et Banfora, solde global eleve", "statut": "nouvelle"},
        {"alerte_id": "ALT_004", "operation_id": "OP_005", "global_client_id": "GCLI_002", "type_alerte": "procuration", "niveau": "bloquant", "score": 91, "motif": "Mandat expire pour retrait par procuration", "statut": "nouvelle"},
        {"alerte_id": "ALT_005", "operation_id": "OP_005", "global_client_id": "GCLI_002", "type_alerte": "cnib", "niveau": "bloquant", "score": 88, "motif": "Piece client expiree", "statut": "nouvelle"},
        {"alerte_id": "ALT_006", "operation_id": "OP_006", "global_client_id": "GCLI_003", "type_alerte": "sanction", "niveau": "bloquant", "score": 93, "motif": "Alias JALLO/DIALLO detecte", "statut": "nouvelle"},
        {"alerte_id": "ALT_007", "operation_id": "OP_007", "global_client_id": "GCLI_004", "type_alerte": "ppe", "niveau": "informatif", "score": 70, "motif": "Client PPE, vigilance renforcee", "statut": "nouvelle"},
        {"alerte_id": "ALT_008", "operation_id": "OP_008", "global_client_id": "GCLI_006", "type_alerte": "personne_morale", "niveau": "informatif", "score": 73, "motif": "Beneficiaire effectif PPE", "statut": "nouvelle"},
        {"alerte_id": "ALT_009", "operation_id": "OP_009", "global_client_id": "GCLI_008", "type_alerte": "zone", "niveau": "informatif", "score": 85, "motif": "Retrait eleve en zone rouge avec motif orpaillage", "statut": "nouvelle"},
        {"alerte_id": "ALT_010", "operation_id": "OP_009", "global_client_id": "GCLI_008", "type_alerte": "sanction", "niveau": "bloquant", "score": 90, "motif": "Alias OUMAR MAIGA proche liste sanction", "statut": "nouvelle"},
    ]

    roles = [
        {"role": "agent_caisse", "voir_client_local": "oui", "voir_details_autres_caisses": "non", "creer_operation": "oui", "traiter_alerte": "non", "modifier_seuil": "non", "exporter": "non"},
        {"role": "chef_caisse", "voir_client_local": "oui", "voir_details_autres_caisses": "non", "creer_operation": "oui", "traiter_alerte": "limite", "modifier_seuil": "non", "exporter": "non"},
        {"role": "conformite_caisse", "voir_client_local": "oui", "voir_details_autres_caisses": "indicateurs", "creer_operation": "non", "traiter_alerte": "oui", "modifier_seuil": "non", "exporter": "oui"},
        {"role": "conformite_reseau", "voir_client_local": "pseudonymise", "voir_details_autres_caisses": "oui_selon_besoin", "creer_operation": "non", "traiter_alerte": "oui", "modifier_seuil": "non", "exporter": "oui"},
        {"role": "admin", "voir_client_local": "non", "voir_details_autres_caisses": "non", "creer_operation": "non", "traiter_alerte": "non", "modifier_seuil": "oui", "exporter": "non"},
        {"role": "auditeur", "voir_client_local": "selon_mission", "voir_details_autres_caisses": "selon_mission", "creer_operation": "non", "traiter_alerte": "non", "modifier_seuil": "non", "exporter": "oui"},
    ]

    write_csv("caisses.csv", caisses)
    write_csv("clients.csv", clients)
    write_csv("pieces_identite.csv", pieces)
    write_csv("beneficiaires_effectifs.csv", beneficiaires)
    write_csv("comptes.csv", comptes)
    write_csv("mandats_procurations.csv", mandats)
    write_csv("listes_surveillance_synthetiques.csv", watchlists)
    write_csv("operations.csv", operations)
    write_csv("alertes_attendues.csv", alertes_attendues)
    write_csv("roles_permissions.csv", roles)
    print(f"Dataset generated in {OUT}")


if __name__ == "__main__":
    main()
