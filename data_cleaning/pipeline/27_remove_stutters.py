import pandas as pd
import re
import os

print("Removing translation stutters from Arabic datasets...")

def remove_stutters(t):
    if not isinstance(t, str):
        return ""
    
    # Clean up massive repetition blocks first (4+ words repeated)
    t = re.sub(r'\b([^\s]+\s+[^\s]+\s+[^\s]+\s+[^\s]+)(?:\s+\1)+\b', r'\1', t)
    # 3-word repeats
    t = re.sub(r'\b([^\s]+\s+[^\s]+\s+[^\s]+)(?:\s+\1)+\b', r'\1', t)
    # 2-word repeats
    t = re.sub(r'\b([^\s]+\s+[^\s]+)(?:\s+\1)+\b', r'\1', t)
    # 1-word repeats
    t = re.sub(r'\b([^\s]+)(?:\s+\1)+\b', r'\1', t)
    
    # Specific edge cases for non-boundary matches (like words stuck together with punctuation)
    t = re.sub(r'(داء\s+){2,}', 'داء ', t)
    t = re.sub(r'(رض\s+){2,}', 'رض ', t)
    
    # Fix any remaining double spaces
    t = re.sub(r'\s{2,}', ' ', t)
    
    return t.strip()

# Apply to RAG format
rag_path = 'Data_Exports_Cleaned/clinical_kb_arabic.csv'
if os.path.exists(rag_path):
    print(f"Processing RAG format: {rag_path}")
    df_rag = pd.read_csv(rag_path).fillna('')
    for col in df_rag.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            df_rag[col] = df_rag[col].apply(remove_stutters)
    df_rag.to_csv(rag_path, index=False, encoding='utf-8')

# Apply to NonRAG format
nonrag_path = 'Data_Cleaned_NonRAG/clinical_kb_arabic.csv'
if os.path.exists(nonrag_path):
    print(f"Processing NonRAG format: {nonrag_path}")
    df_nonrag = pd.read_csv(nonrag_path).fillna('')
    for col in df_nonrag.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            df_nonrag[col] = df_nonrag[col].apply(remove_stutters)
    df_nonrag.to_csv(nonrag_path, index=False, encoding='utf-8')

# Re-generate the global Arabic RAG txt file for good measure
print("Re-generating global RAG text file with stutter-free text...")
def split_into_chunks(text, max_length=8000):
    if not text or len(text) == 0: return []
    chunks = []
    current_chunk = ""
    sentences = re.split(r'(?<=[.!?])\s+|\n', text)
    for sentence in sentences:
        if not sentence.strip(): continue
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            current_chunk += ("\n" + sentence if current_chunk else sentence)
        else:
            if current_chunk: chunks.append(current_chunk)
            current_chunk = sentence
    if current_chunk: chunks.append(current_chunk)
    return chunks

all_chunks = []
for idx, row in df_rag.iterrows():
    drug_name = row.get('drugbank_name', f"Drug_AR_{idx}")
    if not drug_name or str(drug_name).strip() == '': drug_name = f"Drug_AR_{idx}"
    
    fields_text = ""
    for col in df_rag.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            value = str(row[col]).strip()
            if value and value != '': fields_text += f"{value}\n"
    
    if fields_text.strip():
        chunks = split_into_chunks(fields_text.strip(), max_length=8000)
        for chunk_idx, chunk_text in enumerate(chunks):
            chunk_content = f"[DRUG] {drug_name}\n\n{chunk_text}"
            all_chunks.append({
                'id': f"{drug_name.lower().replace(' ', '_')}_AR_{chunk_idx}",
                'content': chunk_content
            })

out_filename = "Database_Exports/rag_flattened_arabic_global.txt"
with open(out_filename, 'w', encoding='utf-8') as f:
    for chunk in all_chunks:
        f.write(f"[CHUNK_ID: {chunk['id']}]\n")
        f.write(chunk['content'])
        f.write(f"\n\n{'='*80}\n\n")

print("Done! Stuttering successfully removed everywhere.")
