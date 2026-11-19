import pandas as pd
import re
from pathlib import Path

FOLDERS = [
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\Data_Cleaned_NonRAG"),
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\new_data_dawav2_improved")
]

def clean_scrape_markdown(text):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return "[DATA UNAVAILABLE]"
    val = str(text)
    
    # Remove references like [1][2] or [ 1 ] 
    val = re.sub(r'\[\s*\d+\s*\]', '', val)
    
    # Strip URL structures
    val = re.sub(r'https?://[^\s]+', '', val)
    
    # Strip english medical website names that leaked
    val = re.sub(r'(?i)(Drugs\.com\.?|WebMD|Mayo Clinic|Medscape|Retrieved on.*?\d{4}\.?)', '', val)
    
    # Strip Arabic website scrapes / Medical metadata
    arab_scrapes = [
        r'اقرأ المزيد(?:.*)?', r'إقرأ المزيد(?:.*)?', r'للمزيد من المعلومات(?:.*)?', 
        r'حقوق النشر(?:.*)?', r'جميع الحقوق محفوظة(?:.*)?', 
        r'(?i)Joseph Ratliff et al\..*?Nutrition Examination Survey(?:.*)?',
        r'الطبي', r'ويب طب', r'سينا\b', r'هل لديك اسئلة(?:\s+متعلقة.*)?',
        r'اكتب سؤالك هنا(?:.*)?', r'اقرأ أيضاً.*?'
    ]
    for pattern in arab_scrapes:
        val = re.sub(pattern, '', val, flags=re.DOTALL)
        
    val = val.strip()
    return val if val else "[DATA UNAVAILABLE]"

def compress_arabic_stutter(text):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return text
    curr = str(text)
    # Target exact word repetitions (1 to 5 words repeating)
    for length in range(5, 0, -1):
        pattern = r'([\u0600-\u06FFa-zA-Z]{2,}(?:\s+[\u0600-\u06FFa-zA-Z]{2,}){0,'+str(length)+r'}?)(?:\s+\1){2,}'
        curr = re.sub(pattern, r'\g<1>', curr)
    
    # Also compress single letter stutters like "ا ا ا"
    curr = re.sub(r'(?i)\b([\u0600-\u06FFa-zA-Z])(?:\s+\1){2,}\b', r'\1', curr)
    
    return curr

for folder in FOLDERS:
    if not folder.exists(): continue
    for file in folder.glob("clinical_kb_arabic.csv"):
        df = pd.read_csv(file)
        
        for col in df.columns:
            if 'arabic' in col and col not in ['dci_arabic', 'arabic_status', 'is_translated', 'clinical_profile_id']:
                df[col] = df[col].apply(clean_scrape_markdown)
                df[col] = df[col].apply(compress_arabic_stutter)
                # Re-validate non-empty meaning
                letters = len(re.sub(r'[^\u0600-\u06FFa-zA-Z]', '', str(df[col])))
                
                df[col] = df[col].apply(lambda x: "[DATA UNAVAILABLE]" if (pd.isna(x) or str(x).strip() == "" or (len(re.sub(r'[^\u0600-\u06FFa-zA-Z]', '', str(x))) < 5)) else str(x).strip())
                
        df.to_csv(file, index=False, encoding='utf-8')
print("Finished cleaning scraping elements and stuttering from Arabic.")
