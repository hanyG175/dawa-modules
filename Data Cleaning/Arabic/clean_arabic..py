import json
import re
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


ROOT_DIR = Path("Arabic/data")
FRENCH_MERGED_CSV = Path("French/output/french_medicines_merged.csv")
OUT_DIR = Path("Arabic/output")


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
    
    return text.strip()


def csv_cell_single_line(value: Any) -> str:
    """Make text safer for Excel CSV parsing/display by removing embedded newlines."""
    text = clean_text(value)
    text = re.sub(r"\s*\n+\s*", " | ", text)
    return text.strip()


def safe_json_load(path: Path) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def build_arabic_rag_content(row: Dict[str, Any]) -> str:
    """Build the final Arabic RAG payload."""
    blocks = [
        ("الإسم التجاري (الجزائر)", row.get("brand_name")),
        ("المادة الفعالة (DCI)", row.get("dci_arabic")),
        ("الشكل الصيدلاني", row.get("form")),
        ("الجرعة", row.get("dosage")),
        ("التعبئة", row.get("conditionnement")),
        ("دواعي الإستعمال", row.get("indications_arabic")),
        ("الجرعة وطريقة الإستعمال", row.get("posology_arabic")),
        ("موانع الإستعمال", row.get("contraindications_arabic")),
        ("الأعراض الجانبية", row.get("adverse_effects_arabic")),
        ("التفاعلات الدوائية", row.get("interactions_arabic")),
        ("الحمل والرضاعة", row.get("pregnancy_breastfeeding_arabic")),
        ("طريقة الحفظ", row.get("conservation_arabic")),
        ("آلية العمل", row.get("mechanism_of_action_arabic")),
    ]
    text = "\n".join([f"{k}: {v}" for k, v in blocks if v])
    return clean_text(text)


def main() -> None:
    if not FRENCH_MERGED_CSV.exists():
        raise FileNotFoundError(f"Master French CSV not found: {FRENCH_MERGED_CSV}")
    if not ROOT_DIR.exists():
        raise FileNotFoundError(f"Arabic Data directory not found: {ROOT_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Master French Dataset
    master_df = pd.read_csv(FRENCH_MERGED_CSV, sep=';', dtype=str)
    master_df.fillna("", inplace=True)
    print(f"Loaded Master Algerian Dataset with {len(master_df)} distinct instances.")
    
    # 2. Load Arabic JSON lists
    medicines = safe_json_load(ROOT_DIR / "Medicine.json")
    leaflets = safe_json_load(ROOT_DIR / "Leaflet.json")
    officials = safe_json_load(ROOT_DIR / "OfficialMedicine.json")
    
    if not (len(medicines) == len(leaflets) == len(officials)):
        print("WARNING: Arabic JSON lists differ in length!")
        
    # Index Arabic mapping targets
    arabic_by_code: Dict[str, Dict[str, Any]] = {}
    arabic_by_n_enreg: Dict[str, Dict[str, Any]] = {}
    arabic_by_brand: Dict[str, Dict[str, Any]] = {}
    arabic_by_dci: Dict[str, Dict[str, Any]] = {}
    
    for i in range(min(len(medicines), len(leaflets), len(officials))):
        med = medicines[i]
        leaf = leaflets[i]
        off = officials[i]
        
        code = clean_text(off.get("code", ""))
        n_enregistrement = clean_text(off.get("registrationNumber", ""))
        brand_name = clean_text(med.get("brandName", ""))
        dci_str = clean_text(off.get("dciExcel", ""))
        
        arab_data = {
            "dci_arabic": clean_text(med.get("dci", "")),
            "indications_arabic": clean_text(leaf.get("indications", "")),
            "posology_arabic": clean_text(leaf.get("posology", "")),
            "contraindications_arabic": clean_text(leaf.get("contraindicationsAndWarnings", "")),
            "adverse_effects_arabic": clean_text(leaf.get("adverseEffects", "")),
            "interactions_arabic": clean_text(leaf.get("interactions", "")),
            "pregnancy_breastfeeding_arabic": clean_text(leaf.get("pregnancyBreastfeeding", "")),
            "conservation_arabic": clean_text(leaf.get("conservation", "")),
            "mechanism_of_action_arabic": clean_text(leaf.get("mechanismOfAction", "")),
            "url_arabic": clean_text(med.get("url", "")),
            "source_arabic": clean_text(med.get("source", "")),
        }
        
        if code:
            arabic_by_code[code] = arab_data
        if n_enregistrement:
            arabic_by_n_enreg[n_enregistrement] = arab_data
        if brand_name:
            arabic_by_brand[brand_name] = arab_data
        if dci_str:
            arabic_by_dci[dci_str] = arab_data

    print(f"Successfully indexed Arabic mapping targets (Codes: {len(arabic_by_code)}, Registrations: {len(arabic_by_n_enreg)}, Brands: {len(arabic_by_brand)}, DCI: {len(arabic_by_dci)}).")

    # 3. Create mapped instances
    mapped_instances: List[Dict[str, Any]] = []
    found_mapping_count = 0
    not_mapped_count = 0
    
    for _, row in master_df.iterrows():
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
        
        excel_code = clean_text(row.get("excel_code", ""))
        n_enregistrement = clean_text(row.get("excel_n_enregistrement", ""))
        brand_name = clean_text(row.get("brand_name", ""))
        dci = clean_text(row.get("dci", ""))
        
        arab_data = arabic_by_code.get(excel_code)
        if not arab_data:
            arab_data = arabic_by_n_enreg.get(n_enregistrement)
        if not arab_data:
            arab_data = arabic_by_brand.get(brand_name)
        if not arab_data:
            arab_data = arabic_by_dci.get(dci)
            
        if arab_data:
            base_record.update(arab_data)
            found_mapping_count += 1
            base_record["arabic_status"] = "found"
        else:
            base_record.update({
                "dci_arabic": "", "indications_arabic": "", "posology_arabic": "", 
                "contraindications_arabic": "", "adverse_effects_arabic": "", 
                "interactions_arabic": "", "pregnancy_breastfeeding_arabic": "", 
                "conservation_arabic": "", "mechanism_of_action_arabic": "",
                "url_arabic": "", "source_arabic": ""
            })
            not_mapped_count += 1
            base_record["arabic_status"] = "not_found"

        base_record["rag_content"] = build_arabic_rag_content(base_record)
        mapped_instances.append(base_record)

    # 4. First pass dataframe grouping to fill missing from successfully matched siblings by DCI
    df_mapped = pd.DataFrame(mapped_instances)
    found_df = df_mapped[df_mapped["arabic_status"] == "found"].copy()
    
    clinical_cols = [
        "dci_arabic", "indications_arabic", "posology_arabic", 
        "contraindications_arabic", "adverse_effects_arabic", 
        "interactions_arabic", "pregnancy_breastfeeding_arabic", 
        "conservation_arabic", "mechanism_of_action_arabic",
        "url_arabic", "source_arabic"
    ]
    
    dci_clinical_mapping = {}
    for _, row in found_df.iterrows():
        dci = str(row["dci"]).lower().strip()
        if dci and dci not in dci_clinical_mapping:
            dci_clinical_mapping[dci] = {col: row[col] for col in clinical_cols}
            
    # Apply to not-found instances
    newly_found = 0
    for idx, row in df_mapped.iterrows():
        if row["arabic_status"] == "not_found":
            dci = str(row["dci"]).lower().strip()
            if dci and dci in dci_clinical_mapping:
                for col in clinical_cols:
                    df_mapped.at[idx, col] = dci_clinical_mapping[dci][col]
                df_mapped.at[idx, "arabic_status"] = "found"
                
                updated_row = df_mapped.iloc[idx].to_dict()
                df_mapped.at[idx, "rag_content"] = build_arabic_rag_content(updated_row)
                
                newly_found += 1
                found_mapping_count += 1
                not_mapped_count -= 1

    # Flatten text fields for Excel CSV exports
    for col in df_mapped.columns:
        df_mapped[col] = df_mapped[col].apply(csv_cell_single_line)

    merged_out = OUT_DIR / "complete_arabic_medicines_merged.csv"
    rag_out = OUT_DIR / "Complete_Arabic_Cleaned_Data_For_RAG.csv"

    df_mapped.to_csv(
        merged_out,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    rag_df = df_mapped[[
        "brand_name", "dci", "dci_arabic", "form", "dosage", 
        "excel_n_enregistrement", "excel_code", "arabic_status", "rag_content"
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
    print(f"  Successfully mapped Arabic:    {found_mapping_count}")
    print(f"  No Arabic scrape found:        {not_mapped_count}")
    print(f"\nSaved Full Set: {merged_out}")
    print(f"Saved RAG Set:  {rag_out}")
    print(f"All {len(df_mapped)} instances perfectly aligned with French database.")


if __name__ == "__main__":
    main()
