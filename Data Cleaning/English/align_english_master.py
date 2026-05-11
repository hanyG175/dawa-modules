import json
import re
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


ROOT_DIR = Path("English/data")
FRENCH_MERGED_CSV = Path("French/output/french_medicines_merged.csv")
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
    text = text.replace('‚', ',')
    
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


def extract_english_clinical_data(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Parse only the English clinical & mapping fields from DrugBank JSON."""
    pharm = doc.get("pharmacology", {}) or {}
    rxnav = doc.get("rxnav_mapping", {}) or {}
    
    return {
        "drugbank_id": clean_text(doc.get("accession_number", "") or rxnav.get("drugbank_id", "")),
        "drugbank_name": clean_text(doc.get("name", "")),
        "rxnav_rxcui": clean_text(rxnav.get("rxcui", "")),
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


def build_english_rag_content(row: Dict[str, Any]) -> str:
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
    if not FRENCH_MERGED_CSV.exists():
        raise FileNotFoundError(f"Master French CSV not found: {FRENCH_MERGED_CSV}")
    if not ROOT_DIR.exists():
        raise FileNotFoundError(f"English Data directory not found: {ROOT_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Master French Dataset (5000+ instances)
    master_df = pd.read_csv(FRENCH_MERGED_CSV, sep=';', dtype=str)
    # Give nulls a blank string so they don't break anything
    master_df.fillna("", inplace=True)
    
    print(f"Loaded Master Algerian Dataset with {len(master_df)} distinct instances.")
    
    # 2. Index the English JSOn files by their excel_meta 'code' or 'n_enregistrement'
    # so we know exactly which one to map to which master instance.
    json_files = list(ROOT_DIR.rglob("*.json"))
    print(f"Indexing {len(json_files)} English JSON files...")
    
    english_by_code: Dict[str, Dict[str, Any]] = {}
    english_by_n_enreg: Dict[str, Dict[str, Any]] = {}
    english_by_brand: Dict[str, Dict[str, Any]] = {}
    english_by_dci: Dict[str, Dict[str, Any]] = {}
    
    for fp in json_files:
        doc = safe_json_load(fp)
        if not isinstance(doc, dict):
            continue
            
        excel_meta = doc.get("excel_meta", {}) or {}
        code = clean_text(excel_meta.get("code", ""))
        n_enregistrement = clean_text(excel_meta.get("n_enregistrement", ""))
        brand_name = clean_text(excel_meta.get("brand_name", ""))
        dci_str = clean_text(excel_meta.get("dci", ""))
        
        # We index by all available identifiers to maximize matching
        eng_data = extract_english_clinical_data(doc)
        
        if code:
            english_by_code[code] = eng_data
        if n_enregistrement:
            english_by_n_enreg[n_enregistrement] = eng_data
        if brand_name:
            english_by_brand[brand_name] = eng_data
        if dci_str:
            english_by_dci[dci_str] = eng_data

    print(f"Successfully indexed English mapping targets (Codes: {len(english_by_code)}, Registrations: {len(english_by_n_enreg)}, Brands: {len(english_by_brand)}).")

    # 3. Create the final mapped instances
    mapped_instances: List[Dict[str, Any]] = []
    found_mapping_count = 0
    not_mapped_count = 0

    for _, row in master_df.iterrows():
        # Reconstruct identity from French Master
        base_record = {
            "medicine_name": row.get("medicine_name", ""),
            "instance_id": row.get("instance_id", ""),
            "brand_name": row.get("brand_name", ""),
            "dci": row.get("dci", ""),
            "form": row.get("form", ""),
            "dosage": row.get("dosage", ""),
            "conditionnement": row.get("conditionnement", ""),
            "laboratory": row.get("laboratory", ""),
            "pays": row.get("pays", ""),
            "tarif_reference_da": row.get("tarif_reference_da", ""),
            "ppa_da": row.get("ppa_da", ""),
            "liste_prescription": row.get("liste_prescription", ""),
            "atc": row.get("atc", ""),
            "excel_n_enregistrement": row.get("excel_n_enregistrement", ""),
            "excel_code": row.get("excel_code", ""),
        }
        
        # Lookup matching English clinical data
        excel_code = clean_text(row.get("excel_code", ""))
        n_enregistrement = clean_text(row.get("excel_n_enregistrement", ""))
        brand_name = clean_text(row.get("brand_name", ""))
        dci = clean_text(row.get("dci", "")) # Used as another fallback if needed
        
        eng_data = english_by_code.get(excel_code)
        if not eng_data:
            eng_data = english_by_n_enreg.get(n_enregistrement)
        if not eng_data:
            eng_data = english_by_brand.get(brand_name)
        if not eng_data:
            eng_data = english_by_dci.get(dci)

            
        if eng_data:
            # Merge clinical English payload
            base_record.update(eng_data)
            found_mapping_count += 1
            base_record["drugbank_status"] = "found"
        else:
            # No DrugBank data scraped for this instance
            base_record.update({k: "" for k in extract_english_clinical_data({}).keys()})
            not_mapped_count += 1
            base_record["drugbank_status"] = "not_found"

        base_record["rag_content"] = build_english_rag_content(base_record)
        mapped_instances.append(base_record)

    # 4. Generate Final DataFrames
    df_mapped = pd.DataFrame(mapped_instances)
    
    # Flatten text fields for Excel CSV exports
    for col in df_mapped.columns:
        df_mapped[col] = df_mapped[col].apply(csv_cell_single_line)

    merged_out = OUT_DIR / "complete_english_medicines_merged.csv"
    rag_out = OUT_DIR / "Complete_English_Cleaned_Data_For_RAG.csv"

    # 4. First pass grouping: fill missing from successfully matched siblings by DCI
    # If a record wasn't found in DrugBank but another record with the SAME DCI was,
    # we can copy the clinical data over.
    found_df = df_mapped[df_mapped["drugbank_status"] == "found"].copy()
    
    # Pre-build a dictionary of DCI -> first found clinical payload
    clinical_cols = [
        "drugbank_id", "drugbank_name", "rxnav_rxcui", "description", 
        "indications", "associated_conditions", "pharmacodynamics", 
        "mechanism_of_action", "absorption", "volume_of_distribution", 
        "metabolism", "route_of_elimination", "half_life", 
        "clearance", "adverse_effects", "toxicity"
    ]
    
    dci_clinical_mapping = {}
    for _, row in found_df.iterrows():
        dci = str(row["dci"]).lower().strip()
        if dci and dci not in dci_clinical_mapping:
            # Save the clinical fields
            dci_clinical_mapping[dci] = {col: row[col] for col in clinical_cols}
            
    # Apply to not-found instances
    newly_found = 0
    for idx, row in df_mapped.iterrows():
        if row["drugbank_status"] == "not_found":
            dci = str(row["dci"]).lower().strip()
            if dci and dci in dci_clinical_mapping:
                # Copy fields
                for col in clinical_cols:
                    df_mapped.at[idx, col] = dci_clinical_mapping[dci][col]
                df_mapped.at[idx, "drugbank_status"] = "found"
                
                # Rebuild rag content
                updated_row = df_mapped.iloc[idx].to_dict()
                df_mapped.at[idx, "rag_content"] = build_english_rag_content(updated_row)
                
                newly_found += 1
                found_mapping_count += 1
                not_mapped_count -= 1

    # Flatten text fields for Excel CSV exports
    for col in df_mapped.columns:
        df_mapped[col] = df_mapped[col].apply(csv_cell_single_line)

    # Export full dataset
    df_mapped.to_csv(
        merged_out,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    # Export RAG specialized dataset
    rag_df = df_mapped[[
        "brand_name", "dci", "drugbank_name", "form", "dosage", 
        "excel_n_enregistrement", "excel_code", "drugbank_status", "rag_content"
    ]]
    rag_df.to_csv(
        rag_out,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    print(f"\nSUMMARY ALIGNMENT:")
    print(f"  Master Algerian instances:     {len(master_df)}")
    print(f"  Successfully mapped DrugBank:  {found_mapping_count}")
    print(f"  No DrugBank scrape found:      {not_mapped_count}")
    print(f"\nSaved Full Set: {merged_out}")
    print(f"Saved RAG Set:  {rag_out}")
    print(f"All {len(df_mapped)} instances perfectly aligned with French database.")


if __name__ == "__main__":
    main()
