import pandas as pd
import re
import os

def clean_english_line(line):
    """Clean English text"""
    if not isinstance(line, str):
        return ""
    
    # Remove HTML entities
    line = re.sub(r'&#\d+;', '', line)
    line = re.sub(r'&[a-z]+;', '', line)
    
    # Remove URLs
    line = re.sub(r'https?://[^\s]+', '', line)
    
    # Remove paywall indicators
    line = re.sub(r'•{3,}', '', line)
    line = re.sub(r'\.{4,}', '', line)
    
    # Remove inline citations
    line = re.sub(r'\s+\d+\s+[.,]', '.', line)
    line = re.sub(r'\bLabel\s*[.,]', '.', line)
    
    # Clean spacing
    line = re.sub(r'\s+', ' ', line)
    
    return line.strip()

def process_english_field(text):
    """Process English field"""
    if not text or not isinstance(text, str):
        return ""
    
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        cleaned = clean_english_line(line)
        if cleaned and len(cleaned) >= 15:
            clean_lines.append(cleaned)
    
    return '\n'.join(clean_lines)

print("Loading English backup...")
df_en = pd.read_csv('final_clean_backups/clinical_kb_english.csv').fillna('')

print("Cleaning English fields...")
english_cols = [col for col in df_en.columns if col not in ['clinical_profile_id', 'drugbank_status', 'drugbank_id', 'drugbank_name']]

for col in english_cols:
    print(f"  Processing: {col}")
    df_en[col] = df_en[col].apply(process_english_field)

# Save cleaned CSV
output_path = 'final_clean_backups/clinical_kb_english.csv'
df_en.to_csv(output_path, index=False, encoding='utf-8')
print(f"Updated English CSV: {output_path}")
print(f"Total records: {len(df_en)}")
