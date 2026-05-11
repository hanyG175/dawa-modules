import pandas as pd
import json
import os
import re

def create_rag_chunk(drug_name, fields_text, chunk_index):
    """Create a single RAG chunk"""
    chunk = f"[DRUG] {drug_name}\n\n{fields_text}"
    return {
        'id': f"{drug_name.lower().replace(' ', '_')}_{chunk_index}",
        'content': chunk,
        'length': len(chunk)
    }

def split_into_chunks(text, max_length=8000):
    """Split text into max_length chunks at sentence boundaries"""
    if not text or len(text) == 0:
        return []
    
    chunks = []
    current_chunk = ""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

print("Loading cleaned RAG datasets...")
df_en = pd.read_csv('Data_Exports_Cleaned/clinical_kb_english.csv').fillna('')
df_fr = pd.read_csv('Data_Exports_Cleaned/clinical_kb_french.csv').fillna('')

# Create output directory
os.makedirs('Database_Exports', exist_ok=True)

print("\n=== FLATTENING TO RAG FORMAT ===")

all_chunks = []
chunk_sizes = []

# Process English
print("Processing English...")
for idx, row in df_en.iterrows():
    if idx % 500 == 0:
        print(f"  Progress: {idx}/{len(df_en)}")
    
    drug_name = row.get('drugbank_name', f"Drug_{idx}")
    if not drug_name or drug_name == '':
        drug_name = f"Drug_{idx}"
    
    # Collect all field values
    fields_text = ""
    for col in df_en.columns:
        if col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_status', 'drugbank_name']:
            value = str(row[col]).strip()
            if value and value != '':
                fields_text += f"{value}\n"
    
    if fields_text.strip():
        chunks = split_into_chunks(fields_text.strip())
        for chunk_idx, chunk_text in enumerate(chunks):
            rag_chunk = create_rag_chunk(drug_name, chunk_text, chunk_idx)
            all_chunks.append(rag_chunk)
            chunk_sizes.append(rag_chunk['length'])

# Process French
print("Processing French...")
for idx, row in df_fr.iterrows():
    if idx % 500 == 0:
        print(f"  Progress: {idx}/{len(df_fr)}")
    
    drug_name = row.get('drugbank_name', f"Drug_FR_{idx}")
    if not drug_name or drug_name == '':
        drug_name = f"Drug_FR_{idx}"
    
    # Collect all field values
    fields_text = ""
    for col in df_fr.columns:
        if col not in ['clinical_profile_id', 'french_status']:
            value = str(row[col]).strip()
            if value and value != '':
                fields_text += f"{value}\n"
    
    if fields_text.strip():
        chunks = split_into_chunks(fields_text.strip())
        for chunk_idx, chunk_text in enumerate(chunks):
            rag_chunk = create_rag_chunk(drug_name, chunk_text, chunk_idx)
            all_chunks.append(rag_chunk)
            chunk_sizes.append(rag_chunk['length'])

print(f"\nTotal chunks created: {len(all_chunks)}")
print(f"Average chunk size: {sum(chunk_sizes) // len(chunk_sizes)} chars")
print(f"Max chunk size: {max(chunk_sizes)} chars")
print(f"Min chunk size: {min(chunk_sizes)} chars")

# Split into 6 parts
print("\n=== SPLITTING INTO 6 PARTS ===")
chunks_per_part = len(all_chunks) // 6
parts = []

for i in range(6):
    if i < 5:
        start_idx = i * chunks_per_part
        end_idx = (i + 1) * chunks_per_part
    else:
        start_idx = i * chunks_per_part
        end_idx = len(all_chunks)
    
    part_chunks = all_chunks[start_idx:end_idx]
    parts.append(part_chunks)
    print(f"Part {i+1}: {len(part_chunks)} chunks")

# Write to files
print("\n=== WRITING TO FILES ===")
total_size = 0

for part_num, part_chunks in enumerate(parts, 1):
    filename = f"Database_Exports/rag_flattened_part_{part_num}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        for chunk in part_chunks:
            f.write(f"[CHUNK_ID: {chunk['id']}]\n")
            f.write(chunk['content'])
            f.write(f"\n\n{'='*80}\n\n")
    
    file_size = os.path.getsize(filename)
    total_size += file_size
    print(f"✓ Part {part_num}: {filename} ({file_size / (1024*1024):.2f} MB)")

print(f"\nTotal size: {total_size / (1024*1024):.2f} MB")
print(f"✓ All files saved to: Database_Exports/")
