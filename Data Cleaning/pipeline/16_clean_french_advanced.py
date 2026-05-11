import pandas as pd
import re
import os

def clean_french_apostrophies(text):
    """Fix API-extracted apostrophies formatting in French"""
    if not isinstance(text, str):
        return ""
    
    # Fix common API apostrophe corruptions
    text = re.sub(r"l\s+'", "l'", text)  # l ' -> l'
    text = re.sub(r"d\s+'", "d'", text)  # d ' -> d'
    text = re.sub(r"n\s+'", "n'", text)  # n ' -> n'
    text = re.sub(r"t\s+'", "t'", text)  # t ' -> t'
    text = re.sub(r"s\s+'", "s'", text)  # s ' -> s'
    
    # Fix curly quotes
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    
    return text

def clean_french_kerning(text):
    """Fix kerning errors in French text"""
    if not isinstance(text, str):
        return ""
    
    # Fix spaced-out letters (common OCR issue)
    # m e d i c a m e n t -> medicament
    text = re.sub(r'([a-z])\s+([a-z])', r'\1\2', text)
    
    # Fix double spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def remove_api_noise(text):
    """Remove API noise, links, and unrelated sentences"""
    if not isinstance(text, str):
        return ""
    
    # Remove HTML entities and tags
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-z]+;', '', text)
    
    # Remove URLs
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'www\.[^\s]+', '', text)
    
    # Remove repetitive dots/dashes (paywall indicators)
    text = re.sub(r'•{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)
    text = re.sub(r'-{5,}', '', text)
    
    # Remove lines with common API noise
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        # Skip common non-medical phrases
        if any(x in line.lower() for x in ['cliquez', 'créer un compte', 'sign in', 'javascript', 'onclick', 'button']):
            continue
        clean_lines.append(line)
    
    return '\n'.join(clean_lines)

def process_french_field(text):
    """Complete French field processing"""
    if not text or not isinstance(text, str):
        return ""
    
    text = clean_french_apostrophies(text)
    text = clean_french_kerning(text)
    text = remove_api_noise(text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

print("Loading French backup...")
df_fr = pd.read_csv('final_clean_backups/clinical_kb_french.csv').fillna('')

print("Cleaning French fields...")
french_cols = [col for col in df_fr.columns if col not in ['clinical_profile_id', 'french_status']]

for col in french_cols:
    print(f"  Processing: {col}")
    df_fr[col] = df_fr[col].apply(process_french_field)

# Save cleaned CSV
output_path = 'final_clean_backups/clinical_kb_french.csv'
df_fr.to_csv(output_path, index=False, encoding='utf-8')
print(f"Updated French CSV: {output_path}")
print(f"Total records: {len(df_fr)}")
