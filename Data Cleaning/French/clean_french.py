import json
import re
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd


ROOT_DIR = Path("French/data")
OUT_DIR = Path("French/output")

# Source priority by field (best-practice: official source first for clinical text)
FIELD_PRIORITY = {
    "full_name": ["pharmanet", "gov-api", "vidal"],
    "brand_name": ["pharmanet", "vidal", "gov-api"],
    "dci": ["pharmanet", "vidal", "gov-api"],
    "form": ["pharmanet", "vidal", "gov-api"],
    "dosage": ["pharmanet", "vidal", "gov-api"],
    "conditionnement": ["pharmanet", "vidal", "gov-api"],
    "laboratory": ["pharmanet", "vidal", "gov-api"],
    "pays": ["pharmanet"],
    "tarif_reference_da": ["pharmanet"],
    "ppa_da": ["pharmanet"],
    "liste_prescription": ["pharmanet", "vidal", "gov-api"],
    "atc": ["gov-api", "vidal", "pharmanet"],
    "indications": ["gov-api", "vidal", "pharmanet"],
    "posology": ["gov-api", "vidal", "pharmanet"],
    "contraindications": ["gov-api", "vidal", "pharmanet"],
    "precautions": ["gov-api", "vidal", "pharmanet"],
    "interactions": ["gov-api", "vidal", "pharmanet"],
    "pregnancy_breastfeeding": ["gov-api", "vidal", "pharmanet"],
    "mechanism_of_action": ["vidal", "gov-api", "pharmanet"],
    "adverse_effects": ["vidal", "gov-api", "pharmanet"],
    "conservation": ["gov-api", "vidal", "pharmanet"],
}

NOISE_PATTERNS = [
    r"Redirection vers le haut de page\n?",
    r"\bImprimer\b\n?",
    r"HTML PUBLIC.*?strict\.dtd\"",
    r"\btemplate_\d+\b",
    r"Sommaire du résumé des caractéristiques du produit",
    r"Sommaire de la notice",
    r"Date de l'autorisation\s*:\s*\d{2}/\d{2}/\d{4}\n?",
    r"Cliquez ici(?:.*?)?(?=\n|$)",
    r"Redirection vers(?:\s.*?)?(?=\n|$)",
    r"Pas d'(?:ASMR|SMR) disponible.*?(?=\n|$)",
    r"plus d'informations dans l'aide(?:\n|$)?",
]


def clean_text(value: Any) -> str:
    """Normalize text for analytics + RAG."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = flatten_to_text(value)
    text = str(value)

    # Remove HTML tags if any
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove known boilerplate
    for p in NOISE_PATTERNS:
        text = re.sub(p, " ", text, flags=re.IGNORECASE | re.DOTALL)

    # Normalize spacing/newlines
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" \| ", "\n", text)  # Ensure custom joined fields separate properly
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def csv_cell_single_line(value: Any) -> str:
    """Make text safer for Excel CSV parsing/display by removing embedded newlines."""
    text = clean_text(value)
    text = re.sub(r"\s*\n+\s*", " | ", text)
    return text.strip()


def flatten_to_text(value: Any) -> str:
    """Convert nested JSON structures to clean readable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, (int, float, bool)):
        return str(value)

    if isinstance(value, list):
        parts = [flatten_to_text(v) for v in value]
        parts = [p for p in parts if p]
        return "\n".join(parts)

    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            txt = flatten_to_text(v)
            if txt:
                parts.append(f"{k}: {txt}")
        return "\n".join(parts)

    return clean_text(str(value))


def detect_source(doc: Dict[str, Any], file_path: Path) -> str:
    source = str(doc.get("source", "")).lower()
    language = str(doc.get("language", "")).lower()
    source_tag = str(doc.get("source_tag", "")).lower()
    fname = file_path.name.lower()

    if "gov" in language or "medicaments_gouv" in source or "gov-api" in fname:
        return "gov-api"
    if "vidal" in source or "vidal" in source_tag:
        return "vidal"
    if "pharmanet" in source or "pharmanet" in source_tag:
        return "pharmanet"
    return "unknown"


def safe_json_load(path: Path) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_json_files(root: Path) -> List[Path]:
    files = sorted(root.rglob("*.json"))
    # Exclude 'raw' directory which contains unscraped/raw individual files
    return [f for f in files if "raw" not in f.parts]


def get_instance_keys(root: Path, file_path: Path) -> Tuple[str, str]:
    """
    Expected structure:
    french_medicines/{medicine_name}/{instance_id}/.../{file}.json
    """
    try:
        # We need to extract the structure based on the known 'data/' anchor or directory hierarchy
        # The file_path might be like ".../French/data/ABACAVIR_SULFATE_EXPERIME_EN_ABACAVIR/111/.../file.json"
        
        # We find the parts relative to the folder containing the actual medicines.
        # If 'data' is part of the path, the medicine name is the folder right after 'data'.
        parts = file_path.parts
        if 'data' in parts:
            data_index = parts.index('data')
            medicine_name = parts[data_index + 1] if len(parts) > data_index + 1 else ""
            instance_id = parts[data_index + 2] if len(parts) > data_index + 2 else ""
        else:
            # Fallback to the relative_to logic if 'data' is not present
            rel = file_path.relative_to(root)
            medicine_name = rel.parts[0] if len(rel.parts) > 0 else ""
            instance_id = rel.parts[1] if len(rel.parts) > 1 else ""
            
        return medicine_name, instance_id
    except Exception:
        # Fallback just in case
        return "unknown", "unknown"


def extract_excel_meta(doc: Dict[str, Any]) -> Dict[str, str]:
    em = doc.get("excel_meta", {}) or {}
    return {
        "excel_brand_name": clean_text(em.get("brand_name")),
        "excel_dci": clean_text(em.get("dci_excel")),
        "excel_form": clean_text(em.get("forme")),
        "excel_dosage": clean_text(em.get("dosage")),
        "excel_conditionnement": clean_text(em.get("conditionnement")),
        "excel_type": clean_text(em.get("type")),
        "excel_statut": clean_text(em.get("statut")),
        "excel_n_enregistrement": clean_text(em.get("n_enregistrement")),
        "excel_code": clean_text(em.get("code")),
    }


def format_vidal_adverse_effects(ae: Dict[str, Any]) -> str:
    if not isinstance(ae, dict):
        return ""
    lines = []
    for system, payload in ae.items():
        if not isinstance(payload, dict):
            continue
        chunks = []
        for group in ["high_freq", "low_freq", "unknown_freq"]:
            items = payload.get(group, []) or []
            for it in items:
                if isinstance(it, dict):
                    effect = clean_text(it.get("effect"))
                    freq = clean_text(it.get("frequency"))
                    if effect:
                        chunks.append(f"- {effect}" + (f" ({freq})" if freq else ""))
        if chunks:
            lines.append(f"{system}:\n" + "\n".join(chunks))
    return clean_text("\n\n".join(lines))


def extract_vidal(doc: Dict[str, Any]) -> Dict[str, str]:
    dci_data = doc.get("dci_data", {}) or {}
    atc_h = dci_data.get("atc_hierarchy", []) or []
    atc_codes = dci_data.get("atc_codes", []) or []

    return {
        "full_name": clean_text(doc.get("full_name")),
        "brand_name": clean_text(doc.get("excel_meta", {}).get("brand_name") or ""),
        "dci": clean_text(doc.get("dci_label") or doc.get("substance") or doc.get("excel_meta", {}).get("dci_excel")),
        "form": clean_text(doc.get("excel_meta", {}).get("forme")),
        "dosage": clean_text(doc.get("excel_meta", {}).get("dosage")),
        "conditionnement": clean_text(doc.get("excel_meta", {}).get("conditionnement")),
        "laboratory": clean_text((doc.get("laboratory", {}) or {}).get("name")),
        "pays": "",
        "tarif_reference_da": "",
        "ppa_da": "",
        "liste_prescription": clean_text(doc.get("list")),
        "atc": clean_text("\n".join(atc_h) if atc_h else " | ".join(atc_codes)),
        "indications": clean_text((doc.get("sections", {}) or {}).get("indications", "")),
        "posology": clean_text(dci_data.get("posology_text") or flatten_to_text(dci_data.get("posology_structured"))),
        "contraindications": clean_text((doc.get("sections", {}) or {}).get("contraindicationsAndWarnings", "")),
        "precautions": clean_text(
            "\n".join(dci_data.get("precautions", []) or [])
        ),
        "interactions": clean_text(dci_data.get("interactions_disclaimer")),
        "pregnancy_breastfeeding": clean_text(dci_data.get("pregnancy_breastfeeding_text")),
        "mechanism_of_action": clean_text(dci_data.get("mechanism_of_action")),
        "adverse_effects": format_vidal_adverse_effects(dci_data.get("adverse_effects", {})),
        "conservation": clean_text(flatten_to_text(doc.get("presentations", []))),
    }


def extract_gov(doc: Dict[str, Any]) -> Dict[str, str]:
    sections = doc.get("sections", {}) or {}
    rcp = sections.get("rcp_structured", {}) or {}
    notice = sections.get("notice_structured", {}) or {}
    target = doc.get("target", {}) or {}

    atc_txt = clean_text(rcp.get("pharmacodynamie") or sections.get("fiche_info", ""))

    return {
        "full_name": clean_text(target.get("SpecDenom01") or rcp.get("denomination") or doc.get("full_name")),
        "brand_name": clean_text(doc.get("excel_meta", {}).get("brand_name")),
        "dci": clean_text(doc.get("excel_meta", {}).get("dci_excel")),
        "form": clean_text(doc.get("excel_meta", {}).get("forme")),
        "dosage": clean_text(doc.get("excel_meta", {}).get("dosage")),
        "conditionnement": clean_text(doc.get("excel_meta", {}).get("conditionnement")),
        "laboratory": clean_text(rcp.get("7._TITULAIRE_DE_L’AUTORISATION_DE_MISE_SUR_LE_MARCHE")),
        "pays": "",
        "tarif_reference_da": "",
        "ppa_da": "",
        "liste_prescription": clean_text(doc.get("target", {}).get("ListeBdm") or rcp.get("liste")),
        "atc": atc_txt,
        "indications": clean_text(rcp.get("indications") or notice.get("qu_est_ce_que")),
        "posology": clean_text(rcp.get("posologie") or notice.get("comment_utiliser")),
        "contraindications": clean_text(rcp.get("contre_indications") or notice.get("informations_avant_utilisation")),
        "precautions": clean_text(rcp.get("mises_en_garde")),
        "interactions": clean_text(rcp.get("interactions")),
        "pregnancy_breastfeeding": clean_text(rcp.get("grossesse_allaitement")),
        "mechanism_of_action": clean_text(rcp.get("pharmacodynamie")),
        "adverse_effects": clean_text(rcp.get("effets_indesirables") or notice.get("effets_indesirables")),
        "conservation": clean_text(rcp.get("precautions_conservation") or notice.get("conservation")),
    }


def extract_pharmanet(doc: Dict[str, Any]) -> Dict[str, str]:
    return {
        "full_name": clean_text(doc.get("designation")),
        "brand_name": clean_text(doc.get("nom_commercial") or doc.get("excel_meta", {}).get("brand_name")),
        "dci": clean_text(doc.get("dci_name") or doc.get("excel_meta", {}).get("dci_excel")),
        "form": clean_text(doc.get("forme_pharmanet") or doc.get("excel_meta", {}).get("forme")),
        "dosage": clean_text(doc.get("dosage_pharmanet") or doc.get("excel_meta", {}).get("dosage")),
        "conditionnement": clean_text(doc.get("conditionnement_pharmanet") or doc.get("excel_meta", {}).get("conditionnement")),
        "laboratory": clean_text(doc.get("laboratoire")),
        "pays": clean_text(doc.get("pays")),
        "tarif_reference_da": clean_text(doc.get("tarif_reference_da")),
        "ppa_da": clean_text(doc.get("ppa_da")),
        "liste_prescription": clean_text(doc.get("liste")),
        "atc": clean_text(doc.get("code_dci", "") or doc.get("dci_code", "")),
        "indications": clean_text(doc.get("classe_therapeutique")),
        "posology": clean_text(doc.get("notice_text")),
        "contraindications": "",
        "precautions": "",
        "interactions": clean_text(flatten_to_text(doc.get("interactions", []))),
        "pregnancy_breastfeeding": "",
        "mechanism_of_action": clean_text(doc.get("classe_pharmacologique")),
        "adverse_effects": "",
        "conservation": "",
    }


def extract_normalized_fields(source: str, doc: Dict[str, Any]) -> Dict[str, str]:
    if source == "vidal":
        return extract_vidal(doc)
    if source == "gov-api":
        return extract_gov(doc)
    if source == "pharmanet":
        return extract_pharmanet(doc)
    return {k: "" for k in FIELD_PRIORITY.keys()}


def pick_best_doc_per_source(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Keep best doc by source:
    - found=true preferred
    - higher _match_score preferred
    """
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        src = r["source"]
        old = out.get(src)
        if old is None:
            out[src] = r
            continue

        old_key = (1 if old["found"] else 0, float(old.get("match_score", 0)))
        new_key = (1 if r["found"] else 0, float(r.get("match_score", 0)))
        if new_key > old_key:
            out[src] = r
    return out


def coalesce_by_priority(per_source_fields: Dict[str, Dict[str, str]], field: str) -> str:
    for src in FIELD_PRIORITY.get(field, ["gov-api", "vidal", "pharmanet"]):
        val = per_source_fields.get(src, {}).get(field, "")
        if val:
            return val
    return ""


def build_rag_content(row: Dict[str, Any]) -> str:
    blocks = [
        ("Nom du médicament", row.get("brand_name")),
        ("Nom complet", row.get("full_name")),
        ("DCI (Principe actif)", row.get("dci")),
        ("Forme", row.get("form")),
        ("Dosage", row.get("dosage")),
        ("Conditionnement", row.get("conditionnement")),
        ("Laboratoire", row.get("laboratory")),
        ("Pays", row.get("pays")),
        ("Tarif de référence (DA)", row.get("tarif_reference_da")),
        ("PPA (DA)", row.get("ppa_da")),
        ("Liste de prescription", row.get("liste_prescription")),
        ("ATC", row.get("atc")),
        ("Indications", row.get("indications")),
        ("Posologie", row.get("posology")),
        ("Contre-indications", row.get("contraindications")),
        ("Précautions", row.get("precautions")),
        ("Interactions", row.get("interactions")),
        ("Grossesse / Allaitement", row.get("pregnancy_breastfeeding")),
        ("Mécanisme d'action", row.get("mechanism_of_action")),
        ("Effets indésirables", row.get("adverse_effects")),
        ("Conservation", row.get("conservation")),
    ]
    text = "\n".join([f"{k}: {v}" for k, v in blocks if v])
    return clean_text(text)


def main() -> None:
    if not ROOT_DIR.exists():
        raise FileNotFoundError(f"Directory not found: {ROOT_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    json_files = list_json_files(ROOT_DIR)
    source_rows: List[Dict[str, Any]] = []

    print(f"Found {len(json_files)} JSON files to process. Starting extraction...")

    for i, fp in enumerate(json_files, 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{len(json_files)} files...")
            
        doc = safe_json_load(fp)
        if not doc:
            continue

        # Some files (e.g., global aggregates) may be JSON arrays, not source documents
        if not isinstance(doc, dict):
            continue

        med_name, inst_id = get_instance_keys(ROOT_DIR, fp)
        source = detect_source(doc, fp)
        found = bool(doc.get("found", True))
        reason = clean_text(doc.get("reason"))
        match_score = float(doc.get("_match_score", doc.get("target", {}).get("_match_score", 0) or 0))

        normalized = extract_normalized_fields(source, doc)
        excel_meta = extract_excel_meta(doc)

        source_rows.append({
            "medicine_name": med_name,
            "instance_id": inst_id,
            "source": source,
            "file_path": str(fp.as_posix()),
            "found": found,
            "reason": reason,
            "match_score": match_score,
            "url": clean_text(doc.get("url")),
            **excel_meta,
            **normalized,
        })

    src_df = pd.DataFrame(source_rows)
    if src_df.empty:
        print("No JSON data found.")
        return

    # Write source-level relational table
    src_out = OUT_DIR / "french_source_documents.csv"
    src_df.to_csv(
        src_out,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    # Build instance-level merged table
    instance_rows: List[Dict[str, Any]] = []
    rag_rows: List[Dict[str, Any]] = []

    grouped = src_df.groupby(["medicine_name", "instance_id"], dropna=False)
    for (medicine_name, instance_id), g in grouped:
        records = g.to_dict("records")
        best_by_source = pick_best_doc_per_source(records)

        per_source_fields: Dict[str, Dict[str, str]] = {}
        for src, row in best_by_source.items():
            per_source_fields[src] = {k: clean_text(row.get(k, "")) for k in FIELD_PRIORITY.keys()}

        merged = {"medicine_name": medicine_name, "instance_id": instance_id}
        for field in FIELD_PRIORITY.keys():
            merged[field] = coalesce_by_priority(per_source_fields, field)

        # Keep traceability and identity metadata from excel
        merged["excel_n_enregistrement"] = coalesce_by_priority(
            {
                s: {"excel_n_enregistrement": r.get("excel_n_enregistrement", "")}
                for s, r in best_by_source.items()
            },
            "excel_n_enregistrement"
        )
        merged["excel_code"] = coalesce_by_priority(
            {s: {"excel_code": r.get("excel_code", "")} for s, r in best_by_source.items()},
            "excel_code"
        )
        merged["available_sources"] = "|".join(sorted(best_by_source.keys()))
        merged["rag_content"] = build_rag_content(merged)

        instance_rows.append(merged)
        rag_rows.append({
            "medicine_name": medicine_name,
            "instance_id": instance_id,
            "brand_name": merged.get("brand_name", ""),
            "dci": merged.get("dci", ""),
            "source_trace": merged["available_sources"],
            "rag_content": merged["rag_content"],
        })

    inst_df = pd.DataFrame(instance_rows)
    rag_df = pd.DataFrame(rag_rows)

    # Flatten multiline text fields to avoid row-visual corruption in Excel
    for col in inst_df.columns:
        inst_df[col] = inst_df[col].apply(csv_cell_single_line)
    for col in rag_df.columns:
        rag_df[col] = rag_df[col].apply(csv_cell_single_line)

    inst_out = OUT_DIR / "french_medicines_merged.csv"
    rag_out = OUT_DIR / "French_Cleaned_Data_For_RAG.csv"

    inst_df.to_csv(
        inst_out,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )
    rag_df.to_csv(
        rag_out,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    print(f"Saved: {src_out}")
    print(f"Saved: {inst_out}")
    print(f"Saved: {rag_out}")
    print(f"Rows -> source: {len(src_df)}, merged instances: {len(inst_df)}, rag rows: {len(rag_df)}")


if __name__ == "__main__":
    main()