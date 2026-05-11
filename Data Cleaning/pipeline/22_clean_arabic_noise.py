import pandas as pd
import re

print("Loading Arabic RAG dataset...")
file_path = 'Data_Exports_Cleaned/clinical_kb_arabic.csv'
df = pd.read_csv(file_path).fillna('')

def clean_arabic_noise(text):
    if not text or not isinstance(text, str):
        return ""
    
    original = text
    
    # 1. Indian numeral patterns (e.g., ٤-٩-٤-٩-١-١-٤-٤-٤-٩-, ٤-١-١-١-)
    # Match chains of Indian numerals and dashes
    text = re.sub(r'[\u0660-\u0669\u06F0-\u06F9\s-]{5,}', '', text)
    
    # 2. Weird sequences of western Arabic numerals separated by spaces or dashes
    # e.g. "14 15 16 17" or "1 1 1 4"
    text = re.sub(r'(?:\b\d{1,2}(?:[\s,-]+|$)){3,}', '', text)
    
    # 3. Specific noise strings
    text = re.sub(r'ملوثات فصر فرص في المادة الخ(?: خ)*', '', text)
    text = re.sub(r'(?:خ\s+){2,}خ?', '', text)
    
    # 4. Repeating markers like (مار في مار في مار ملي)
    text = re.sub(r'\(مار في مار في مار ملي\)', '', text)
    
    # 5. Other noise artifacts seen in the check
    text = re.sub(r'\(5 أيام x 5 أيام x 5 أيام x 5 أيام', '5 أيام', text)
    text = re.sub(r'داء\s+(?:داء\s+)+', 'داء ', text)
    text = re.sub(r'رض\s+(?:رض\s+)+', 'رض ', text)
    text = re.sub(r'□\s+(?:□\s+)+', '', text)
    text = re.sub(r'-{5,}', '', text)
    
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    # If the text is left with just the RAG tags "[DRUG] [Field]", remove it completely
    # Pattern: ^\[.*?\] \[.*?\]$
    if re.match(r'^\[.*?\]\s*\[.*?\]$', text.strip()):
        return ""
        
    return text

print("Cleaning noise from all text columns...")
noise_cols = [col for col in df.columns if col != 'clinical_profile_id' and 'arabic' in col]
# Specifically include all RAG format fields
all_cols_to_clean = [col for col in df.columns if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_name']]

for col in all_cols_to_clean:
    df[col] = df[col].apply(clean_arabic_noise)

# Save back to RAG
df.to_csv(file_path, index=False, encoding='utf-8')
print(f"Saved cleaned RAG data to {file_path}")

# Also update the Non-RAG version for consistency
non_rag_path = 'Data_Cleaned_NonRAG/clinical_kb_arabic.csv'
df_nonrag = pd.read_csv(non_rag_path).fillna('')

for col in all_cols_to_clean:
    if col in df_nonrag.columns:
        df_nonrag[col] = df_nonrag[col].apply(clean_arabic_noise)

df_nonrag.to_csv(non_rag_path, index=False, encoding='utf-8')
print(f"Saved cleaned Non-RAG data to {non_rag_path}")

print("Done! Noise successfully filtered out.")
