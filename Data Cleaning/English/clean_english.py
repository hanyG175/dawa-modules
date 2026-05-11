import json
import re
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


ROOT_DIR = Path("English/data")
OUT_DIR = Path("English/output")


def clean_text(value: Any) -> str:
    """Normalize text for analytics + RAG."""
    if pd.isna(value) or value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = str(value)
        
    text = str(value)
    # Remove HTML tags if any
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize spacing/newlines
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" \| ", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    
    # Simple cleanup of unicode/noise
    text = text.replace('‚', ',')  # Fix weird commas from the scrape
    
    return text.strip()


def csv_cell_single_line(value: Any) -> str:
    """Make text safer for Excel CSV parsing/display by removing embedded newlines."""
    text = clean_text(value)
    text = re.sub(r"\s*\n+\s*", " | ", text)
    return text.strip()


def safe_json_load(path: Path) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def extract_english_data(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Parse unified record from DrugBank scraped JSON."""
    excel_meta = doc.get("excel_meta", {}) or {}
    pharm = doc.get("pharmacology", {}) or {}
    rxnav = doc.get("rxnav_mapping", {}) or {}
    atc_codes = doc.get("atc_codes", []) or []
    
    atc_text = " | ".join([f"{a.get('code', '')}: {a.get('name', '')}" for a in atc_codes])
    
    return {
        # Identity (Algerian Specs)
        "brand_name": clean_text(excel_meta.get("brand_name", "")),
        "dci": clean_text(excel_meta.get("dci_excel", "")),
        "form": clean_text(excel_meta.get("forme", "")),
        "dosage": clean_text(excel_meta.get("dosage", "")),
        "conditionnement": clean_text(excel_meta.get("conditionnement", "")),
        "liste_prescription": clean_text(excel_meta.get("liste", "")),
        "laboratory": clean_text(excel_meta.get("laboratoire", "")),
        "pays": clean_text(excel_meta.get("pays", "")),
        "market_status": clean_text(excel_meta.get("statut", "")),
        "type": clean_text(excel_meta.get("type", "")),
        "excel_n_enregistrement": clean_text(excel_meta.get("n_enregistrement", "")),
        "excel_code": clean_text(excel_meta.get("code", "")),
        
        # Source Mapping
        "drugbank_id": clean_text(doc.get("accession_number", "") or rxnav.get("drugbank_id", "")),
        "drugbank_name": clean_text(doc.get("name", "")),
        "rxnav_rxcui": clean_text(rxnav.get("rxcui", "")),
        "atc": clean_text(atc_text),
        
        # Clinical Data (DrugBank Specs)
        "description": clean_text(doc.get("description", "")),
        "indications": clean_text(pharm.get("indication", "")),
        "associated_conditions": clean_text(pharm.get("associated_conditions", "")),
        "pharmacodynamics": clean_text(pharm.get("pharmacodynamics", "")),
        "mechanism_of_action": clean_text(pharm.get("mechanism_of_action", "")),
        "absorption": clean_text(pharm.get("absorption", "")),
        "volume_of_distribution": clean_text(pharm.get("volume_of_distribution", "")),
        "metabolism": clean_text(pharm.get("metabolism", "")),
        "route_of_elimination": clean_text(pharm.get("route_of_elimination", "")),
        "half_life": clean_text(pharm.get("half-life", "")),
        "clearance": clean_text(pharm.get("clearance", "")),
        "adverse_effects": clean_text(pharm.get("adverse_effects", "")),
        "toxicity": clean_text(pharm.get("toxicity", "")),
    }


def build_rag_content(row: Dict[str, Any]) -> str:
    """Build the final English RAG payload."""
    blocks = [
        ("Brand Name (Algeria)", row.get("brand_name")),
        ("Active Component (DCI)", row.get("dci")),
        ("DrugBank Equivalent", row.get("drugbank_name")),
        ("Form", row.get("form")),
        ("Dosage", row.get("dosage")),
        ("Conditioning", row.get("conditionnement")),
        ("Description", row.get("description")),
        ("Indications", row.get("indications")),
        ("Associated Conditions", row.get("associated_conditions")),
        ("Mechanism of Action", row.get("mechanism_of_action")),
        ("Pharmacodynamics", row.get("pharmacodynamics")),
        ("Absorption", row.get("absorption")),
        ("Metabolism", row.get("metabolism")),
        ("Half-life", row.get("half_life")),
        ("Route of Elimination", row.get("route_of_elimination")),
        ("Clearance", row.get("clearance")),
        ("Toxicity", row.get("toxicity")),
    ]
    text = "\n".join([f"{k}: {v}" for k, v in blocks if v])
    return clean_text(text)


def main() -> None:
    if not ROOT_DIR.exists():
        raise FileNotFoundError(f"Directory not found: {ROOT_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_files = sorted(ROOT_DIR.rglob("*.json"))
    
    print(f"Found {len(json_files)} English JSON files to process...")

    instances: List[Dict[str, Any]] = []

    for i, fp in enumerate(json_files, 1):
        if i % 500 == 0:
            print(f"  Processed {i}/{len(json_files)} files...")

        doc = safe_json_load(fp)
        if not isinstance(doc, dict):
            continue

        extracted = extract_english_data(doc)
        extracted["source_file"] = fp.name
        extracted["rag_content"] = build_rag_content(extracted)
        instances.append(extracted)

    df = pd.DataFrame(instances)
    if df.empty:
        print("No English JSON data parsed.")
        return

    # Grouping/Merging identical instances based on unique registration number or brand+code
    # (Though in English/data they are mostly split already)
    # We will output as unique lines directly.
    
    found_count = df["drugbank_name"].astype(bool).sum()
    not_found_count = len(df) - found_count
    
    # Flatten text fields for Excel CSV exports
    for col in df.columns:
        df[col] = df[col].apply(csv_cell_single_line)

    # 1. Full Merge Table
    merged_out = OUT_DIR / "english_medicines_merged.csv"
    df.to_csv(
        merged_out,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    # 2. Optimized RAG Table
    rag_df = df[[
        "brand_name", "dci", "drugbank_name", "form", "dosage", 
        "excel_n_enregistrement", "excel_code", "rag_content"
    ]]
    rag_out = OUT_DIR / "English_Cleaned_Data_For_RAG.csv"
    rag_df.to_csv(
        rag_out,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    print(f"Saved: {merged_out}")
    print(f"Saved: {rag_out}")
    print(f"\nSUMMARY:")
    print(f"  Total Algerian instances read: {len(df)}")
    print(f"  Mapped to DrugBank (Found):    {found_count}")
    print(f"  Not Mapped (Not Found):        {not_found_count}")
    print(f"All are included in the final CSV.\n")


if __name__ == "__main__":
    main()
