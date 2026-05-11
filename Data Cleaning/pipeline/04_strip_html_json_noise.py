import pandas as pd
import re

def strip_noise(text):
    if pd.isna(text): return ""
    text = str(text)
    
    # Remove HTML tags (e.g. <b>, <br>, <li>)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove unicode artifacts like \xa0 (non-breaking space)
    text = text.replace('\\xa0', ' ').replace('\xa0', ' ')
    
    # Try to safely unfold leftover JSON fragments if they're lists of dicts
    # Often happens in adverse_effects like: [{"effect": "Rash", "frequency": "Uncommon"}]
    # We will just strip purely empty brackets [] and {}
    text = text.replace('[]', '').replace('{}', '')
    
    # Clean up any messed up spaces caused by the replacements
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

for kb in ['clinical_kb_english.csv', 'clinical_kb_arabic.csv', 'clinical_kb_french.csv']:
    df = pd.read_csv(f'Database_Exports/{kb}')
    for col in df.columns:
        if 'status' not in col and 'id' not in col:
            df[col] = df[col].apply(strip_noise)
    df.to_csv(f'Database_Exports/{kb}', index=False)

print("HTML tags, unicode non-breaking spaces, and empty JSON artifacts stripped.")
