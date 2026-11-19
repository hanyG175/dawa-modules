import pandas as pd
import numpy as np
from pathlib import Path

FOLDERS_MAPPING = [
    {
        "backup_path": Path("backups"),
        "target_path": Path("Data_Cleaned_NonRAG")
    },
    {
        "backup_path": Path("new_data_dawav2_improved/_backup_clean"),
        "target_path": Path("new_data_dawav2_improved")
    }
]

LANGUAGES = ["arabic", "english", "french"]

ID_COLUMNS = {
    'clinical_profile_id', 'drugbank_id', 'drugbank_name', 'dci_arabic',
    'arabic_status', 'french_status', 'drugbank_status', 'is_translated'
}

def undo_enrichment():
    for fm in FOLDERS_MAPPING:
        b_dir = fm["backup_path"]
        t_dir = fm["target_path"]
        
        if not b_dir.exists() or not t_dir.exists():
            print(f"Skipping {t_dir.name} as paths don't exist.")
            continue
            
        print(f"\nProcessing {t_dir.name} from backups in {b_dir.name}...")
        
        for lang in LANGUAGES:
            b_file = b_dir / f"clinical_kb_{lang}_backup.csv"
            if not b_file.exists():
                b_file = b_dir / f"clinical_kb_{lang}.csv"
            
            if not b_file.exists():
                print(f"  Missing backup for {lang}")
                continue
                
            print(f"  -> Undoing enrichment for {lang}...")
            df = pd.read_csv(b_file, dtype=str).fillna("[DATA UNAVAILABLE]")
            
            # Find status column
            status_col = None
            if lang == "arabic" and "arabic_status" in df.columns:
                status_col = "arabic_status"
            elif lang == "french" and "french_status" in df.columns:
                status_col = "french_status"
            elif lang == "english" and "drugbank_status" in df.columns:
                status_col = "drugbank_status"
                
            has_is_translated = "is_translated" in df.columns
            
            wiped_count = 0
            for idx in df.index:
                # Check condition
                should_wipe = False
                if status_col and str(df.at[idx, status_col]).startswith("ai_translated"):
                    should_wipe = True
                if has_is_translated and str(df.at[idx, "is_translated"]).lower() == "true":
                    should_wipe = True
                    
                if should_wipe:
                    wiped_count += 1
                    # Set clinical data to empty
                    for col in df.columns:
                        if col not in ID_COLUMNS:
                            df.at[idx, col] = "[DATA UNAVAILABLE]"
                    
                    # Optionally reset status
                    if status_col:
                        # Find what language it was translated from to properly set missing?
                        # It doesn't matter, we'll set it to missing
                        df.at[idx, status_col] = "missing"
                    if has_is_translated:
                        df.at[idx, "is_translated"] = "false"
            
            print(f"     Wiped translated data for {wiped_count} rows.")
            # Save to target
            target_f = t_dir / f"clinical_kb_{lang}.csv"
            df.to_csv(target_f, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    undo_enrichment()