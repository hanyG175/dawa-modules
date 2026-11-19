import pandas as pd
import re
from pathlib import Path

FOLDERS = [
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\Data_Cleaned_NonRAG"),
    Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\new_data_dawav2_improved")
]

def compress_stutter(text):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return text
    curr = str(text)
    # Attempt to compress repeating word blocks (1 to 5 words repeating)
    for length in range(5, 0, -1):
        pattern = r'(?i)(\b[a-zA-Z]{2,}\b(?:\s+[a-zA-Z]{2,}){0,'+str(length)+r'}?)(?:\s+\1){2,}'
        curr = re.sub(pattern, r'\g<1>', curr)
    return curr

def clean_english_artifacts(text, col_name):
    if pd.isna(text) or text == "[DATA UNAVAILABLE]": return "[DATA UNAVAILABLE]"
    val = str(text)
    
    scrape_patterns = [
        r'(?i)Read more:?.*', 
        r'(?i)For more:?.*',
        r'(?i)Do you have questions on this subject\?.*',
        r'(?i)Do you have questions related to this subject\?.*',
        r'(?i)Ask Sina,.*',
        r'(?i)artificial intelligence to answer all your.*',
        r'(?i)Sena is preparing the answer for you.*',
        r'(?i)Retrieved on.*?\d{4}\.?',
        r'(?i)\bDrugs\.com\.?', r'(?i)\bWebMD\b', r'(?i)\bMayo Clinic\b', r'(?i)\bMedscape\b', r'(?i)rxlist\.',
        r'(?i)all rights reserved', r'(?i)copyright', r'(?i)click here',
        r'https?://[^\s]+',
        r'\[\s*\d+\s*\]'
    ]
    for p in scrape_patterns:
        val = re.sub(p, '', val, flags=re.DOTALL)
        
    if 'interactions' in col_name or 'description' in col_name:
        val = re.sub(r'(?i)The information provided on drug interactions results from the synthesis.*?proof of safety\.', '', val)
        val = re.sub(r'(?i)transparency committee.*?\(reference price\)[^\n]*', '', val)
        val = re.sub(r'(?i)\bvidal\b', '', val)
        
    # Apply line-by-line filtering for description or conservation columns removing CIP leak.
    if 'conservation' in col_name or 'description' in col_name:
        lines = val.split('\n')
        kept = []
        for line in lines:
            if bool(re.search(r'(?i)cip13|cip:\s*\d{13}', line)) or bool(re.search(r'(?i)commercialis[eé]|marketed', line)):
                continue
            kept.append(line)
        val = '\n'.join(kept)
        
    # Fix the trailing preposition edge case
    val = re.sub(r'(?i)\b(?:the|and|of|in|to|with|a|an|or|for|is|are|at|by|from|as|on|which|that|d)\s*$', '', val.strip())
    
    val = val.strip()
    letters = len(re.sub(r'[^a-zA-Z]', '', val))
    if letters < 5:
        return "[DATA UNAVAILABLE]"
        
    return val

for folder in FOLDERS:
    if not folder.exists(): 
        continue
    for file in folder.glob("clinical_kb_english.csv"):
        df = pd.read_csv(file)
        for col in df.columns:
            if df[col].dtype == object and col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_name', 'dci', 'drugbank_status', 'is_translated', 'french_status', 'arabic_status']:
                df[col] = df[col].apply(lambda x: clean_english_artifacts(x, col))
                df[col] = df[col].apply(compress_stutter)
        df.to_csv(file, index=False, encoding='utf-8')
