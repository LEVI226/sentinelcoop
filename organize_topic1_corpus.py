#!/usr/bin/env python3
"""Build a clean Topic 1 working corpus from the collected raw assets."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpusCIF"
TOPIC = CORPUS / "topic1_lbc_ft"
ASSETS = CORPUS / "assets"
DOWNLOADS = Path(r"C:\Users\ulric\Downloads")


DIRS = {
    "briefing": TOPIC / "00_briefing_hackathon",
    "regulation": TOPIC / "01_reglementation_lbc_ft_fp",
    "giaba": TOPIC / "02_giaba_evaluations_typologies",
    "sanctions": TOPIC / "03_sanctions_listes_surveillance",
    "cif": TOPIC / "04_contexte_cif_sfd",
    "data": TOPIC / "05_jeu_donnees_synthetique",
    "solution": TOPIC / "06_solution_grc_technique",
    "indexes": TOPIC / "99_index_manifestes",
    "extracts": TOPIC / "source_extracts",
}


CATEGORY_RULES = {
    "regulation": [
        "Loi-uniforme-LBCFTFP",
        "directive_no02_2015",
        "instruction_no008_05_2015",
        "services-20de-20paiement",
        "Commission_Bancaire",
        "CommissionBancaire",
        "TraiteUMOA",
        "StatutsBCEAO",
    ],
    "sanctions": [
        "sanctions",
        "Publication_des_sanctions",
        "LISTES-20DES-20ETABLISSEMENTS",
    ],
    "giaba": [
        "giaba-org__",
        "MER",
        "FUR",
        "Follow-Up",
        "THREAT-ASSESSMENT",
        "CYBERCRIME",
        "MARITIME",
        "AML-CFT",
        "MONEY-LAUNDERING",
        "TYPOLOG",
        "Mutual",
        "Evaluation",
    ],
    "cif": [
        "wp-content__uploads__tdr",
        "hackathon",
        "rapport-annuel-cif",
        "reponses-hackathon",
        "digicoop",
        "cif",
    ],
}


PRIORITY_HINTS = [
    "Loi-uniforme-LBCFTFP",
    "directive_no02_2015",
    "instruction_no008_05_2015",
    "Publication_des_sanctions",
    "reponses-hackathon",
    "tdr-appel-a-candidatures-global-hackathon",
    "rapport-annuel-cif",
    "THREAT-ASSESSMENT",
    "AML-CFT",
    "CYBERCRIME",
    "MARITIME",
    "MER_",
    "2ND_MER",
    "MUTUAL",
]


def ensure_dirs() -> None:
    for directory in DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(name: str) -> str | None:
    lower = name.lower()
    for category, hints in CATEGORY_RULES.items():
        for hint in hints:
            if hint.lower() in lower:
                return category
    return None


def priority_score(name: str) -> int:
    lower = name.lower()
    score = 0
    for hint in PRIORITY_HINTS:
        if hint.lower() in lower:
            score += 10
    if name.lower().endswith(".pdf"):
        score += 3
    if "bceao-int__" in lower:
        score += 2
    if "giaba-org__" in lower:
        score += 1
    return score


def readable_name(name: str) -> str:
    cleaned = re.sub(r"--[a-f0-9]{10}(?=\.)", "", name)
    cleaned = cleaned.replace("bceao-int__sites__default__files__", "BCEAO__")
    cleaned = cleaned.replace("giaba-org__Frame__pdfviewer-", "GIABA__")
    cleaned = cleaned.replace("wp-content__uploads__", "CIF__")
    cleaned = cleaned.replace("__", " / ")
    cleaned = cleaned.replace("-20", " ")
    cleaned = cleaned.replace("-C3-A9", "e")
    cleaned = cleaned.replace("-C2-B0", "no")
    return cleaned


def safe_copy(src: Path, dest_dir: Path, used_names: set[str]) -> Path:
    base = readable_name(src.name)
    base = re.sub(r'[<>:"/\\|?*]+', "_", base).strip()
    base = re.sub(r"\s+", " ", base)
    if len(base) > 150:
        base = base[:145] + src.suffix
    candidate = dest_dir / base
    counter = 2
    while candidate.name.lower() in used_names or candidate.exists():
        candidate = dest_dir / f"{candidate.stem}-{counter}{src.suffix}"
        counter += 1
    shutil.copy2(src, candidate)
    used_names.add(candidate.name.lower())
    return candidate


def extract_pptx_text(pptx: Path, output: Path) -> None:
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    slides: list[str] = []
    with ZipFile(pptx) as archive:
        names = sorted(
            [name for name in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)],
            key=lambda item: int(re.search(r"(\d+)", item).group(1)),
        )
        for index, name in enumerate(names, 1):
            root = ET.fromstring(archive.read(name))
            texts = [node.text for node in root.findall(".//a:t", ns) if node.text]
            slides.append(f"## Slide {index}\n\n" + "\n".join(texts))
    output.write_text("\n\n".join(slides) + "\n", encoding="utf-8")


def repair_mojibake(text: str) -> str:
    try:
        repaired = text.encode("latin1").decode("utf-8")
        if repaired.count("é") + repaired.count("è") + repaired.count("à") > text.count("Ã"):
            return repaired
    except UnicodeError:
        pass
    return text


def copy_source_files() -> list[dict]:
    records: list[dict] = []
    source_files = [
        DOWNLOADS / "Briefing_Regles_Candidats_Hackathons_CIF_2026-09-05-v2.0.pptx",
        DOWNLOADS / "tdr-appel-a-candidatures-global-hackathon-cif-digicoop-wa-2026.pdf",
        DOWNLOADS / "directive_no02_2015_cm_uemoa_lbc_ft-2.pdf",
    ]
    used: set[str] = set()
    for src in source_files:
        if src.exists():
            dest = safe_copy(src, DIRS["briefing"], used)
            records.append({"kind": "source", "category": "briefing", "source_path": str(src), "clean_path": str(dest)})

    briefing = DOWNLOADS / "Briefing_Regles_Candidats_Hackathons_CIF_2026-09-05-v2.0.pptx"
    if briefing.exists():
        extract_pptx_text(briefing, DIRS["extracts"] / "briefing_regles_candidats_hackathons_cif_2026-09-05-v2.0.md")

    tdr_md = ROOT / "tdr-appel-a-candidatures-global-hackathon-cif-digicoop-wa-2026.md"
    if tdr_md.exists():
        text = repair_mojibake(tdr_md.read_text(encoding="utf-8", errors="ignore"))
        (DIRS["extracts"] / "tdr_hackathon_cif_2026_cleaned.md").write_text(text, encoding="utf-8")
    return records


def build_clean_assets() -> list[dict]:
    records: list[dict] = []
    seen_hashes: set[str] = set()
    used_names = {key: set() for key in DIRS}
    for src in sorted(ASSETS.glob("*")):
        if not src.is_file():
            continue
        category = classify(src.name)
        if category is None:
            continue
        file_hash = sha256(src)
        if file_hash in seen_hashes:
            continue
        seen_hashes.add(file_hash)
        dest = safe_copy(src, DIRS[category], used_names[category])
        records.append(
            {
                "category": category,
                "source_file": str(src.relative_to(CORPUS)),
                "clean_file": str(dest.relative_to(TOPIC)),
                "extension": src.suffix.lower(),
                "bytes": src.stat().st_size,
                "sha256": file_hash,
                "priority_score": priority_score(src.name),
                "label": readable_name(src.name),
            }
        )
    records.sort(key=lambda row: (-row["priority_score"], row["category"], row["label"]))
    return records


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_priority_markdown(records: list[dict]) -> None:
    top = [record for record in records if record["priority_score"] >= 10][:40]
    lines = [
        "# Documents prioritaires Topic 1",
        "",
        "Ces documents doivent alimenter directement le cadrage de la solution LBC/FT/FP.",
        "",
    ]
    for record in top:
        lines.extend(
            [
                f"## {record['label']}",
                "",
                f"- Categorie: {record['category']}",
                f"- Fichier: `{record['clean_file']}`",
                f"- Taille: {record['bytes']} octets",
                f"- Score priorite: {record['priority_score']}",
                "",
            ]
        )
    (DIRS["indexes"] / "documents_prioritaires.md").write_text("\n".join(lines), encoding="utf-8")


def write_synthetic_data_dictionary() -> None:
    rows = [
        ("client_id", "string", "Identifiant technique non nominatif", "C001", "synthetique", "Aucune donnee reelle"),
        ("nom_normalise", "string", "Nom fictif normalise pour filtrage", "KABORE AMADOU", "synthetique", "Tester homonymies"),
        ("alias", "string", "Variante orthographique ou translitteration", "KABORE AMADOU O.", "synthetique", "Tester fuzzy matching"),
        ("date_naissance", "date", "Date fictive de naissance", "1984-03-18", "synthetique", "Score de rapprochement"),
        ("pays_residence", "string", "Pays UEMOA ou autre", "Burkina Faso", "synthetique/public", "Risque pays"),
        ("type_client", "enum", "Personne physique, morale, occasionnel", "personne_physique", "synthetique", "Segmentation KYC"),
        ("statut_ppe", "boolean", "Indicateur PPE simule", "false", "synthetique", "Filtrage PPE"),
        ("score_kyc", "integer", "Score de risque client 0-100", "35", "calcule", "Justifier les regles"),
        ("compte_id", "string", "Identifiant de compte", "A1001", "synthetique", "Multi-comptes"),
        ("solde_compte", "decimal", "Solde courant du compte", "125000", "synthetique", "Solde global client"),
        ("transaction_id", "string", "Identifiant operation", "T00001", "synthetique", "Audit trail"),
        ("date_operation", "datetime", "Date et heure de l'operation", "2026-09-05T10:15:00", "synthetique", "Chronologie"),
        ("montant", "decimal", "Montant de l'operation", "950000", "synthetique", "Seuils et cumul"),
        ("sens", "enum", "debit ou credit", "credit", "synthetique", "Flux entrant/sortant"),
        ("canal", "enum", "guichet, mobile, agent, virement", "guichet", "synthetique", "Detection comportementale"),
        ("contrepartie_nom", "string", "Nom fictif de contrepartie", "SOCIETE ALPHA", "synthetique", "Filtrage transaction"),
        ("motif", "string", "Libelle operation", "Depot espece", "synthetique", "Scenarios suspects"),
        ("alerte_type", "enum", "sanction, ppe, seuil, fractionnement, inhabituel", "fractionnement", "calcule", "Qualification alerte"),
        ("alerte_niveau", "enum", "informatif, bloquant", "informatif", "calcule", "Workflow conformite"),
        ("decision_conformite", "enum", "a_revoir, faux_positif, escalade, declaration", "a_revoir", "calcule/humain", "Gouvernance"),
    ]
    path = DIRS["data"] / "dictionnaire_donnees_synthetiques.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["champ", "type", "description", "exemple", "source", "usage_topic1"])
        writer.writerows(rows)


def main() -> None:
    ensure_dirs()
    source_records = copy_source_files()
    asset_records = build_clean_assets()
    fields = ["category", "priority_score", "label", "clean_file", "source_file", "extension", "bytes", "sha256"]
    write_csv(DIRS["indexes"] / "catalogue_assets_topic1.csv", asset_records, fields)
    (DIRS["indexes"] / "catalogue_assets_topic1.json").write_text(
        json.dumps(asset_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DIRS["indexes"] / "sources_hackathon.json").write_text(
        json.dumps(source_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_priority_markdown(asset_records)
    write_synthetic_data_dictionary()
    summary = {
        "clean_assets": len(asset_records),
        "source_files": len(source_records),
        "by_category": {},
    }
    for record in asset_records:
        summary["by_category"].setdefault(record["category"], 0)
        summary["by_category"][record["category"]] += 1
    (TOPIC / "clean_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
