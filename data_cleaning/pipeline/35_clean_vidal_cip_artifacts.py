import pandas as pd
import re
from pathlib import Path

FOLDERS = [
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\Data_Cleaned_NonRAG"),
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\new_data_dawav2_improved")
]

def clean_interactions(text):
    if pd.isna(text): return "[DATA UNAVAILABLE]"
    val = str(text)
    # Remove Vidal disclaimers
    val = re.sub(r'(?i)Les informations fournies sur les interactions médicamenteuses résultent de la synthèse.*?base Vidal ne doit jamais être interprétée comme une preuve d\'innocuité', '', val)
    # Generic short Vidal strings
    val = re.sub(r'(?i)les informations fournies sur les interactions.*?(\n|$)', '', val)
    val = re.sub(r'(?i)vidal', '', val) # remove literal vidal matches in case remnants
    val = val.strip()
    if not val or len(val) < 10:
        return "[DATA UNAVAILABLE]"
    return val

def clean_conservation(text):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return "[DATA UNAVAILABLE]"
    lines = str(text).split('\n')
    kept = []
    for line in lines:
        if bool(re.search(r'(?i)cip13', line)) or bool(re.search(r'(?i)commercialis[eé]', line)):
            continue
        kept.append(line)
    res = '\n'.join(kept).strip()
    if not res:
        return "[DATA UNAVAILABLE]"
    return res

def clean_adverse_effects(text):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return "[DATA UNAVAILABLE]"
    val = str(text).strip()
    
    # Skip this logic for Arabic
    if re.search(r'[\u0600-\u06FF]', val):
        return val

        return "[DATA UNAVAILABLE]"
    return val

def clean_moa(text):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return "[DATA UNAVAILABLE]"
    val = str(text)
    # Strip dangling articles
    val = re.sub(r'(?i)\b(?:l\'a|à|de|et|l\'|ou|le|la|les|un|une|des)\s*$', '', val).strip()
    if not val:
        return "[DATA UNAVAILABLE]"
    return val

print("Starting deep clean for Vidal, CIP, Adverse Effects headers, and MOA truncations...")

for folder in FOLDERS:
    if not folder.exists(): 
        print(f"Skipping {folder}")
        continue
    print(f"\nProcessing folder: {folder.name}")
    for file in folder.glob("*.csv"):
        print(f"  -> Cleaning {file.name}")
        df = pd.read_csv(file)
        
        # Interactions
        for interact_col in ['interactions', 'interactions_arabic', 'interactions_english']:
            if interact_col in df.columns:
                df[interact_col] = df[interact_col].apply(clean_interactions)
                
        # Conservation
        for cons_col in ['conservation', 'conservation_arabic', 'conservation_english']:
            if cons_col in df.columns:
                df[cons_col] = df[cons_col].apply(clean_conservation)
                
        # Adverse Effects
        for ae_col in ['adverse_effects', 'adverse_effects_arabic', 'adverse_effects_english']:
            if ae_col in df.columns:
                df[ae_col] = df[ae_col].apply(clean_adverse_effects)
                
        # MOA
        for moa_col in ['mechanism_of_action', 'mechanism_of_action_arabic', 'mechanism_of_action_english']:
            if moa_col in df.columns:
                df[moa_col] = df[moa_col].apply(clean_moa)

        df.to_csv(file, index=False, encoding='utf-8')

print("Artifacts scrubbed!")
