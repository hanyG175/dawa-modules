import pandas as pd
import re

print("Loading Arabic RAG dataset...")
file_path = 'Data_Exports_Cleaned/clinical_kb_arabic.csv'
df = pd.read_csv(file_path).fillna('')

def clean_arabic_noise(text):
    if not text or not isinstance(text, str):
        return ""
    
    # Let's fix specific exact strings the user doesn't want
    text = re.sub(r'ملوثات', '', text)
    text = re.sub(r'فصر فرص في المادة الخ(?: خ)*', '', text)
    text = re.sub(r'خ\s+خ\s+خ(?: خ)*', '', text)
    text = re.sub(r'مار في مار في مار ملي', '', text)
    
    # Check again for sequences
    text = re.sub(r'[\u0660-\u0669\u06F0-\u06F9\s-]{5,}', '', text)
    text = re.sub(r'(?:\b\d{1,2}(?:[\s,-]+|$)){3,}', '', text)
    
    text = re.sub(r'\s{2,}', ' ', text).strip()
    text = re.sub(r'\[\s+\]', '[]', text) # cleanup empty tags if any inner text removed
    
    if re.match(r'^\[.*?\]\s*\[.*?\]$', text.strip()):
        return ""
        
    return text

print("Cleaning remaining noise from all text columns...")
all_cols_to_clean = [col for col in df.columns if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_name']]

for col in all_cols_to_clean:
    df[col] = df[col].apply(clean_arabic_noise)

# Save back to RAG
df.to_csv(file_path, index=False, encoding='utf-8')
print(f"Saved cleaned RAG data to {file_path}")

# Update Non-RAG version as well
non_rag_path = 'Data_Cleaned_NonRAG/clinical_kb_arabic.csv'
df_nonrag = pd.read_csv(non_rag_path).fillna('')

for col in all_cols_to_clean:
    if col in df_nonrag.columns:
        df_nonrag[col] = df_nonrag[col].apply(clean_arabic_noise)

df_nonrag.to_csv(non_rag_path, index=False, encoding='utf-8')
print(f"Saved cleaned Non-RAG data to {non_rag_path}")
