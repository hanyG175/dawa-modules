import pandas as pd
import re
import os
import json

def clean_arabic_kerning_safe(text):
    """
    Clean Arabic kerning WITHOUT removing spaces between words.
    Only fixes:
    - Diacritics removal
    - Control characters
    - Repetitive letters (4+ same letter → 2 letters)
    - Tatweel character
    """
    if not isinstance(text, str):
        return ""
    
    text = text.strip()
    if not text:
        return ""
    
    # 1. Remove Arabic diacritics (these cause the kerning appearance)
    text = re.sub(r'[\u064B-\u0652]', '', text)
    
    # 2. Remove control characters and zero-width spaces
    text = re.sub(r'[\u200B-\u200D\u2060\uFEFF]', '', text)
    
    # 3. Remove tatweel characters
    text = text.replace('ـ', '')
    
    # 4. Collapse repetitive sequences (4+ same letter → 2)
    text = re.sub(r'([\u0600-\u06FF])\1{3,}', r'\1\1', text)
    
    # 5. Clean multiple spaces (but preserve single spaces between words)
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()

def process_arabic_field_safe(text):
    """Process Arabic field safely"""
    if not text or not isinstance(text, str):
        return ""
    
    lines = text.split('\n')
    valid_lines = []
    
    for line in lines:
        # Skip paywall indicators
        if re.search(r'•{3,}', line):
            continue
        
        # Skip API noise
        if any(x in line for x in ['Create Account', 'الرجاء', 'يرجى', 'انقر']):
            continue
        
        cleaned = clean_arabic_kerning_safe(line)
        
        if cleaned and len(cleaned) >= 15:
            valid_lines.append(cleaned)
    
    return '\n'.join(valid_lines)

def clean_french_apostrophies_safe(text):
    """Fix API-extracted apostrophies in French without removing word spaces"""
    if not isinstance(text, str):
        return ""
    
    # Fix common API apostrophe corruptions
    text = re.sub(r"l\s+'", "l'", text)
    text = re.sub(r"d\s+'", "d'", text)
    text = re.sub(r"n\s+'", "n'", text)
    text = re.sub(r"t\s+'", "t'", text)
    text = re.sub(r"s\s+'", "s'", text)
    
    # Fix curly quotes
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    
    return text

def clean_french_kerning_safe(text):
    """Fix French kerning WITHOUT removing spaces between words"""
    if not isinstance(text, str):
        return ""
    
    # Only fix isolated spaced-out letters (kerning patterns like: m e d i c a m e n t)
    # But NOT normal word spacing like "medicament patient"
    
    # Pattern: single letter followed by space and another single letter, repeated 3+ times
    # This catches: m e d i c a m e n t
    # But NOT: medicament patient
    
    # Match pattern: [a-z] space [a-z] space [a-z] (at least 3 pieces)
    text = re.sub(r'([a-z])\s+([a-z])\s+([a-z])\s+([a-z])', r'\1\2\3\4', text)
    text = re.sub(r'([a-z])\s+([a-z])\s+([a-z])', r'\1\2\3', text)
    
    # Clean multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()

def remove_api_noise(text):
    """Remove API noise, links, and unrelated sentences"""
    if not isinstance(text, str):
        return ""
    
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'www\.[^\s]+', '', text)
    text = re.sub(r'•{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)
    text = re.sub(r'-{5,}', '', text)
    
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        if any(x in line.lower() for x in ['cliquez', 'créer un compte', 'sign in', 'javascript', 'onclick', 'button']):
            continue
        clean_lines.append(line)
    
    return '\n'.join(clean_lines)

def process_french_field_safe(text):
    """Complete French field processing"""
    if not text or not isinstance(text, str):
        return ""
    
    text = clean_french_apostrophies_safe(text)
    text = clean_french_kerning_safe(text)
    text = remove_api_noise(text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

print("Loading RAG-formatted datasets from final_clean_backups...")
df_en_rag = pd.read_csv('final_clean_backups/clinical_kb_english.csv').fillna('')
df_fr_rag = pd.read_csv('final_clean_backups/clinical_kb_french.csv').fillna('')
df_ar_rag = pd.read_csv('final_clean_backups/clinical_kb_arabic.csv').fillna('')
df_market = pd.read_csv('final_clean_backups/universal_market_instances.csv').fillna('')

# Create output directories
os.makedirs('Data_Exports_Cleaned', exist_ok=True)
os.makedirs('Data_Cleaned_NonRAG', exist_ok=True)

print("\n=== CLEANING RAG-FORMATTED DATASETS ===")

# Clean Arabic (RAG format)
print("Cleaning Arabic (RAG format)...")
arabic_cols = [col for col in df_ar_rag.columns if 'arabic' in col.lower() or col in ['indications', 'posology']]
for col in arabic_cols:
    df_ar_rag[col] = df_ar_rag[col].apply(process_arabic_field_safe)

# Clean French (RAG format)
print("Cleaning French (RAG format)...")
french_cols = [col for col in df_fr_rag.columns if col not in ['clinical_profile_id', 'french_status']]
for col in french_cols:
    df_fr_rag[col] = df_fr_rag[col].apply(process_french_field_safe)

# Save cleaned RAG versions
print("\nSaving cleaned RAG-formatted datasets...")
df_en_rag.to_csv('Data_Exports_Cleaned/clinical_kb_english.csv', index=False, encoding='utf-8')
df_fr_rag.to_csv('Data_Exports_Cleaned/clinical_kb_french.csv', index=False, encoding='utf-8')
df_ar_rag.to_csv('Data_Exports_Cleaned/clinical_kb_arabic.csv', index=False, encoding='utf-8')
df_market.to_csv('Data_Exports_Cleaned/universal_market_instances.csv', index=False, encoding='utf-8')

print("✓ Cleaned RAG datasets saved to: Data_Exports_Cleaned/")

print("\n=== EXTRACTING NON-RAG VERSIONS ===")

def extract_non_rag_text(text):
    """Remove RAG formatting [TAG] [CATEGORY] prefixes to get raw text"""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove leading [TAG] patterns at the start of lines
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        # Strip all leading [..] patterns
        cleaned = re.sub(r'^(?:\[.*?\]\s*)+', '', line)
        if cleaned:
            clean_lines.append(cleaned)
    
    return '\n'.join(clean_lines)

# Extract non-RAG versions
print("Extracting non-RAG English...")
for col in df_en_rag.columns:
    if col not in ['clinical_profile_id', 'drugbank_status', 'drugbank_id', 'drugbank_name']:
        df_en_rag[col] = df_en_rag[col].apply(extract_non_rag_text)

print("Extracting non-RAG French...")
for col in df_fr_rag.columns:
    if col not in ['clinical_profile_id', 'french_status']:
        df_fr_rag[col] = df_fr_rag[col].apply(extract_non_rag_text)

print("Extracting non-RAG Arabic...")
for col in df_ar_rag.columns:
    if col not in ['clinical_profile_id', 'arabic_status']:
        df_ar_rag[col] = df_ar_rag[col].apply(extract_non_rag_text)

# Save non-RAG versions
print("Saving non-RAG datasets...")
df_en_rag.to_csv('Data_Cleaned_NonRAG/clinical_kb_english.csv', index=False, encoding='utf-8')
df_fr_rag.to_csv('Data_Cleaned_NonRAG/clinical_kb_french.csv', index=False, encoding='utf-8')
df_ar_rag.to_csv('Data_Cleaned_NonRAG/clinical_kb_arabic.csv', index=False, encoding='utf-8')
df_market.to_csv('Data_Cleaned_NonRAG/universal_market_instances.csv', index=False, encoding='utf-8')

print("✓ Non-RAG datasets saved to: Data_Cleaned_NonRAG/")

print("\n=== SUMMARY ===")
print(f"✓ English: {len(df_en_rag)} records")
print(f"✓ French: {len(df_fr_rag)} records (kerning + apostrophies fixed)")
print(f"✓ Arabic: {len(df_ar_rag)} records (kerning + repetition fixed)")
print(f"✓ Market: {len(df_market)} instances")
print("\nTwo folders created:")
print("  1. Data_Exports_Cleaned/ - RAG-formatted, cleaned")
print("  2. Data_Cleaned_NonRAG/ - Non-RAG format, cleaned")
