import pandas as pd
import re
import os

print("Deep cleaning NonRAG datasets to remove all brackets and citations...")

def deep_clean_nonrag(text):
    if not isinstance(text, str):
        return ""
    
    # 1. Remove anything inside square brackets completely (like [1], [FDA Label], [PubChem], [فرط التحسس])
    text = re.sub(r'\[.*?\]', '', text)
    
    # 2. Clean up any leftover orphan brackets (like a stray ']' at the start of a line)
    text = re.sub(r'(?m)^[\s\]]+', '', text)
    
    # 3. Clean up multiple spaces left behind by the removals
    text = re.sub(r'\s{2,}', ' ', text)
    
    # 4. Strip leading/trailing whitespace
    return text.strip()

folders = ['Data_Cleaned_NonRAG', 'new_data_dawav2_improved']
files = ['clinical_kb_english.csv', 'clinical_kb_french.csv', 'clinical_kb_arabic.csv']

for folder in folders:
    for file in files:
        fpath = os.path.join(folder, file)
        if not os.path.exists(fpath): continue
        print(f"Processing {file} in {folder}...")
    df = pd.read_csv(fpath).fillna('')
    
    # Apply to all columns except clinical_profile_id and drugbank metadata
    for col in df.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            df[col] = df[col].apply(deep_clean_nonrag)
            
    df.to_csv(fpath, index=False, encoding='utf-8')
    print(f"✓ Cleaned {fpath}")

print("Done! All brackets, tags, and citations have been removed from the NonRAG variants.")
