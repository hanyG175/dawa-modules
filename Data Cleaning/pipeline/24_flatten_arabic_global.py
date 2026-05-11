import pandas as pd
import json
import os
import re

def create_rag_chunk(drug_name, fields_text, chunk_index):
    """Create a single RAG chunk"""
    chunk = f"[DRUG] {drug_name}\n\n{fields_text}"
    return {
        'id': f"{drug_name.lower().replace(' ', '_')}_AR_{chunk_index}",
        'content': chunk,
        'length': len(chunk)
    }

def split_into_chunks(text, max_length=8000):
    """Split text into max_length chunks at sentence boundaries"""
    if not text or len(text) == 0:
        return []
    
    chunks = []
    current_chunk = ""
    
    # Simple split by punctuation or newlines for Arabic sentences
    sentences = re.split(r'(?<=[.!?])\s+|\n', text)
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            if current_chunk:
                current_chunk += "\n" + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

print("Loading cleaned Arabic RAG dataset...")
df_ar = pd.read_csv('Data_Exports_Cleaned/clinical_kb_arabic.csv').fillna('')

# Create output directory
os.makedirs('Database_Exports', exist_ok=True)

print("\n=== FLATTENING ARABIC TO RAG FORMAT ===")

all_chunks = []
chunk_sizes = []

print("Processing Arabic...")
for idx, row in df_ar.iterrows():
    if idx > 0 and idx % 500 == 0:
        print(f"  Progress: {idx}/{len(df_ar)}")
    
    drug_name = row.get('drugbank_name', f"Drug_AR_{idx}")
    if not drug_name or str(drug_name).strip() == '':
        drug_name = f"Drug_AR_{idx}"
    
    # Collect all field values
    fields_text = ""
    for col in df_ar.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            value = str(row[col]).strip()
            if value and value != '':
                fields_text += f"{value}\n"
    
    if fields_text.strip():
        # Optional chunking just to keep within the 8000 char Context Window limit per chunk, 
        # but all results will go into a single text file.
        chunks = split_into_chunks(fields_text.strip(), max_length=8000)
        for chunk_idx, chunk_text in enumerate(chunks):
            rag_chunk = create_rag_chunk(drug_name, chunk_text, chunk_idx)
            all_chunks.append(rag_chunk)
            chunk_sizes.append(rag_chunk['length'])

print(f"\nTotal chunks created: {len(all_chunks)}")
if chunk_sizes:
    print(f"Average chunk size: {sum(chunk_sizes) // len(chunk_sizes)} chars")

out_filename = "Database_Exports/rag_flattened_arabic_global.txt"
print(f"\n=== WRITING TO SINGLE GLOBAL FILE ===")
with open(out_filename, 'w', encoding='utf-8') as f:
    for chunk in all_chunks:
        f.write(f"[CHUNK_ID: {chunk['id']}]\n")
        f.write(chunk['content'])
        f.write(f"\n\n{'='*80}\n\n")

file_size = os.path.getsize(out_filename)
print(f"✓ Saved Global Arabic RAG File: {out_filename} ({file_size / (1024*1024):.2f} MB)")
