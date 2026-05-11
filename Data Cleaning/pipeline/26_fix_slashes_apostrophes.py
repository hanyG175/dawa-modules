import pandas as pd
import re
import os

print("Fixing backslashes and apostrophes in NonRAG datasets...")

def fix_text_formatting(text):
    if not isinstance(text, str):
        return ""
    
    # 1. Remove backslashes
    text = text.replace('\\', '')
    
    # 2. Normalize smart/curly quotes to straight apostrophes
    text = text.replace('’', "'").replace('‘', "'").replace('`', "'").replace('´', "'")
    
    # 3. Fix floating apostrophes between letters (handles both French "l ' eau" and English "don ' t")
    # Matches a letter, optional space, apostrophe, optional space, letter
    # and replaces with letter'letter
    text = re.sub(r"([a-zA-Z])\s*'\s*([a-zA-Z])", r"\1'\2", text)
    
    # 4. Clean up any accidental double spaces resulting from general edits
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()

files = ['clinical_kb_english.csv', 'clinical_kb_french.csv', 'clinical_kb_arabic.csv']

for file in files:
    fpath = os.path.join('Data_Cleaned_NonRAG', file)
    print(f"Processing {file}...")
    df = pd.read_csv(fpath).fillna('')
    
    # Apply to all string columns
    for col in df.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            df[col] = df[col].apply(fix_text_formatting)
            
    df.to_csv(fpath, index=False, encoding='utf-8')
    print(f"✓ Fixed {fpath}")

print("Done! Backslashes removed and apostrophes corrected.")
