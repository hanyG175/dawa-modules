import pandas as pd
import re
import html
import os

def clean_arabic(text):
    if not isinstance(text, str): return text
    
    # Unescape HTML
    text = html.unescape(text)
    
    # Remove Kashida/Tatweel (repetitive line extensions in Arabic)
    text = re.sub(r'\u0640+', '', text)
    
    # Remove repetitive characters (3 or more)
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # Remove URLs and links
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove English API noise (like JSON keys, eg "drug_name":)
    text = re.sub(r'"[a-zA-Z_]+"\s*:', '', text)
    
    # Fix Arabic Kerning (letters separated by single spaces incorrectly)
    # Match sequences of Arabic letters separated by spaces
    def remove_kerning(match):
        return match.group(0).replace(' ', '')
    
    text = re.sub(r'(?:[\u0621-\u064A]\s){3,}[\u0621-\u064A]', remove_kerning, text)
    
    # Clean up excessive punctuation and spaces
    text = re.sub(r'([.?!,-_-])\1+', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

print("Cleaning Arabic Data from Backups...")
df_ar = pd.read_csv('final_clean_backups/clinical_kb_arabic.csv').fillna('')

for col in df_ar.columns:
    if col not in ['clinical_profile_id', 'arabic_status']:
        df_ar[col] = df_ar[col].apply(clean_arabic)

# Save cleaned non-RAG formatted data back to backups
df_ar.to_csv('final_clean_backups/clinical_kb_arabic.csv', index=False)

# RAG FORMATTING
os.makedirs('Arabic_RAG_Output', exist_ok=True)
rag_lines = []

for idx, row in df_ar.iterrows():
    pid = row['clinical_profile_id']
    content_blocks = []
    
    for col in df_ar.columns:
        if col not in ['clinical_profile_id', 'arabic_status'] and row[col]:
            # Flatten to RAG style
            content_blocks.append(f"[ARABIC - {col.upper().replace('_ARABIC', '')}]\n{row[col]}")
            
    if content_blocks:
        rag_lines.append(f"=== DRUG ID: {pid} ===\n" + "\n\n".join(content_blocks) + "\n---")

with open('Arabic_RAG_Output/rag_flattened_arabic.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(rag_lines))

print("Arabic cleaning complete. Saved to final_clean_backups and Arabic_RAG_Output/rag_flattened_arabic.txt")
