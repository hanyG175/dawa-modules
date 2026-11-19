import pandas as pd
import re
from pathlib import Path

FOLDERS = [
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\Data_Cleaned_NonRAG"),
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\new_data_dawav2_improved")
]

UI_KEYWORDS = [
    "create account", "sign up", "build, train", "build train",
    "data library", "machine-learning", "machine learning",
    "subscribe to", "upgrade to", "premium feature", 
    "créer un compte", "s'inscrire", "modèles d'apprentissage",
    "abonnez-vous", "version premium", "bibliothèque de données",
    "إنشاء حساب", "اشتراك", "تسجيل الدخول", "نماذج التعلم", 
    "مكتبة البيانات", "الترقية", "سجل الآن"
]

# Specifically target clinical/pharmacokinetic sections for missing-data flags
CLINICAL_COLS = {
    'indications', 'associated_conditions', 'pharmacodynamics', 'mechanism_of_action', 
    'absorption', 'volume_of_distribution', 'metabolism', 'route_of_elimination', 
    'half_life', 'clearance', 'adverse_effects', 'toxicity', 'warnings', 
    'contraindications', 'dosage_and_administration', 'posology', 'precautions', 
    'interactions', 'pregnancy_breastfeeding', 'conservation', 'overdosage', 
    'description', 'pediatric_use', 'geriatric_use',
    'indications_arabic', 'posology_arabic', 'contraindications_arabic', 
    'adverse_effects_arabic', 'interactions_arabic', 'pregnancy_breastfeeding_arabic', 
    'conservation_arabic', 'mechanism_of_action_arabic', 'warnings_arabic', 
    'overdosage_arabic', 'description_arabic', 'pediatric_use_arabic', 'geriatric_use_arabic'
}

def clean_ui_and_paywalls(text, col_name, is_clinical):
    if pd.isna(text):
        return "[DATA UNAVAILABLE]" if is_clinical else ""
    
    val = str(text).strip()
    if not val or val.lower() == "nan":
        return "[DATA UNAVAILABLE]" if is_clinical else val
    if val == "[DATA UNAVAILABLE]":
        return val
        
    lines = val.split('\n')
    kept = []
    
    for line in lines:
        lower_line = line.lower()
        # Rule 1: Marketing / UI bleed
        if any(kw in lower_line for kw in UI_KEYWORDS):
            continue
            
        # Rule 2: Paywall placeholders (consecutive ••• or .........)
        if re.search(r'•{3,}', line) or re.search(r'\.{8,}', line):
            continue
            
        kept.append(line)
        
    res = "\n".join(kept).strip()
    
    # Rule 3: Flag incomplete sections
    # If a clinical text field is left with almost no content after filtering out the noise
    if is_clinical:
        # Fixed to include Arabic characters [\u0600-\u06FF] and French accents
        alpha_num_count = len(re.sub(r'[^\w\u0600-\u06FFàâçéèêëîïôûùüÿñæœ]', '', res))
        if not res or alpha_num_count < 5:
            return "[DATA UNAVAILABLE]"
            
    return res

def fix_numeric_stutters(text):
    if not isinstance(text, str) or text == "[DATA UNAVAILABLE]":
        return text
        
    # Rule 4: Verify numbers & units (Remove translation stutters like "10 mg 10 mg")
    # Captures a number + unit exactly duplicated back-to-back
    pattern = r'\b(\d+(?:[.,]\d+)?\s*(?:mg|g|ml|mcg|µg|kg|h|ui|iu|mEq|%)(?:/\w+)?)\s+\1\b'
    prev = None
    curr = text
    while prev != curr:
        prev = curr
        curr = re.sub(pattern, r'\1', curr, flags=re.IGNORECASE)
    
    return curr

print("Starting deep clean for UI bleeds, paywalls, and translated number stutters...")

for folder in FOLDERS:
    if not folder.exists():
        continue
    
    print(f"\nProcessing folder: {folder.name}")
    for file in folder.glob("*.csv"):
        print(f"  -> Cleaning {file.name}")
        df = pd.read_csv(file)
        
        for col in df.columns:
            # Determine if this column requires the [DATA UNAVAILABLE] gap-fill rule
            is_clinical_col = (col in CLINICAL_COLS)
            
            # Apply rules
            df[col] = df[col].apply(lambda x: clean_ui_and_paywalls(x, col, is_clinical_col))
            df[col] = df[col].apply(fix_numeric_stutters)
            
        # Write the cleaned file back
        df.to_csv(file, index=False, encoding='utf-8')

print("\nCleaning complete!")
