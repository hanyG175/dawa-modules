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
    "مكتبة البيانات", "الترقية", "سجل الآن",
    "هل لديك اسئلة متعلقة في هذا الموضوع", "اسال سينا",
    "ذكاء اصطناعي للاجابة عن كل اسئلتك الطبية", "اكتب سؤالك هنا"
]

def clean_arabic_ui_and_artifacts(text, col_name=None):
    if pd.isna(text): return "[DATA UNAVAILABLE]"
    val = str(text)
    
    if val == "[DATA UNAVAILABLE]": return val
    
    # 1. UI Bleed logic from script 34
    lines = val.split('\n')
    kept = []
    for line in lines:
        lower_line = line.lower()
        if any(kw in lower_line for kw in UI_KEYWORDS): continue
        if re.search(r'•{3,}', line) or re.search(r'\.{8,}', line): continue
        kept.append(line)
    val = '\n'.join(kept)

    # 2. Arabic Vidal / HAS disclaimers specific to interactions
    if col_name and 'interactions' in col_name:
        val = re.sub(r'(?i)المعلومات المقدمة عن التفاعلات الدوائية هي نتيجة.*?مراكز تنسيق البرامج والتنسيق\.?', '', val)
        val = re.sub(r'(?i)نظرا لأن الدواء هو دواء عام، فإن لجنة الشفافية.*?\(السعر المرجعي\)[^\n]*', '', val)

    # 3. JSON metadata / translations leaks specific to Adverse effects
    if col_name and 'adverse_effects' in col_name:
        if val.strip().startswith('{') and '"' in val and ':' in val:
            return "[DATA UNAVAILABLE]"
            
    # 4. Truncations in MOA
    if col_name and 'mechanism' in col_name:
        val = re.sub(r'(?i)\b(?:في|من|على|إلى|عن|بـ|لـ|ال)\s*$', '', val.strip())

    val = val.strip()
    
    # Fallback to [DATA UNAVAILABLE] if mainly just symbols or less than 5 letters (Arabic or Latin)
    letters = len(re.sub(r'[^\u0600-\u06FFa-zA-Z]', '', val))
    if letters < 5:
        return "[DATA UNAVAILABLE]"
        
    return val

print("Starting deep clean for Arabic...")

for folder in FOLDERS:
    if not folder.exists(): 
        continue
    print(f"\nProcessing folder: {folder.name}")
    for file in folder.glob("clinical_kb_arabic.csv"):
        print(f"  -> Cleaning {file.name}")
        df = pd.read_csv(file)
        
        # Apply the global cleanup to ALL clinical columns like script 34 used to
        for col in df.columns:
            if 'arabic' in col and col not in ['dci_arabic', 'arabic_status', 'is_translated', 'clinical_profile_id', 'drugbank_status', 'french_status']:
                df[col] = df[col].apply(lambda x: clean_arabic_ui_and_artifacts(x, col_name=col))

        df.to_csv(file, index=False, encoding='utf-8')

print("Arabic artifacts scrubbed!")
