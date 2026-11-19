import csv
import os
import re
from pathlib import Path
import shutil

BASE = Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning")
SRC_DIR = BASE / "new_data_dawav2_improved"
OUT_DIR = BASE / "new_data_rag"

MAX_CHUNK_LEN = 8000
BATCH_SIZE = 500

def load_universal_data():
    """Load and aggregate universal market data by clinical_profile_id"""
    univ_path = SRC_DIR / "universal_market_instances.csv"
    univ_map = {}
    with univ_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cp_id = r.get("clinical_profile_id", "").strip()
            if not cp_id:
                continue
            
            if cp_id not in univ_map:
                univ_map[cp_id] = {
                    "dci": set(),
                    "brands": set(),
                    "medicine_name": set(),
                    "forms": set()
                }
            
            dci = r.get("dci", "").strip()
            if dci: univ_map[cp_id]["dci"].add(dci)
            
            brand = r.get("brand_name", "").strip()
            if brand: univ_map[cp_id]["brands"].add(brand)
                
            med = r.get("medicine_name", "").strip()
            if med: univ_map[cp_id]["medicine_name"].add(med)
                
            form = r.get("form", "").strip()
            if form: univ_map[cp_id]["forms"].add(form)
            
    return univ_map

def split_into_chunks(text, max_length=MAX_CHUNK_LEN):
    if not text:
        return []
    # Split by actual sentence endings, keeping paragraphs together where possible
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    chunks = []
    current = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
            
        # Hard break for abnormally long unbreakable text sequences
        while len(s) > max_length:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(s[:max_length])
            s = s[max_length:]
            
        if len(current) + len(s) + 1 <= max_length:
            current = f"{current}\n{s}" if current else s
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks

def build_fields_text(row, skip_fields=None):
    skip_fields = set(skip_fields or [])
    parts = []
    for k, v in row.items():
        if k in skip_fields:
            continue
        v_str = str(v).strip()
        if v_str:
            # Format nicely: [field_name]: value
            clean_k = k.replace('_', ' ').title()
            parts.append(f"[{clean_k}]\n{v_str}")
    return "\n\n".join(parts)

def process_language(lang_name, univ_map):
    csv_path = SRC_DIR / f"clinical_kb_{lang_name}.csv"
    if not csv_path.exists():
        print(f"Skipping {lang_name}, file not found")
        return

    out_dir = OUT_DIR / lang_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear out old files if rewriting
    for p in out_dir.glob("*.txt"):
        p.unlink()

    all_chunks = []
    
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            cp_id = row.get("clinical_profile_id", "").strip()
            
            # 1. Build the Universal Identity Context that will PREPEND every chunk!
            drug_context = ""
            if cp_id in univ_map:
                u = univ_map[cp_id]
                dcis = ", ".join(sorted(u["dci"]))
                brands = ", ".join(sorted(u["brands"]))
                meds = ", ".join(sorted(u["medicine_name"]))
                
                parts = []
                if dcis: parts.append(f"DCI: {dcis}")
                elif meds: parts.append(f"DCI / Medicine: {meds}")
                
                if brands: parts.append(f"Brands Marketed: {brands}")
                
                drug_context = "\n".join(parts)
            else:
                # Fallback to drugbank_name if available (mostly for english)
                d_name = row.get("drugbank_name", "").strip()
                if d_name:
                    drug_context = f"Drug Name: {d_name}"
                else:
                    drug_context = f"Record ID: {cp_id}"

            # Let's frame the Drug Context clearly for the vectorizer
            header_context = f"[DRUG IDENTITY]\n{drug_context}\n[LANGUAGE]: {lang_name.upper()}\n"
            
            # 2. Extract clinical text
            skip = {"clinical_profile_id", "drugbank_id", "drugbank_name", "drugbank_status", "is_translated"}
            body_text = build_fields_text(row, skip_fields=skip)
            
            if not body_text.strip():
                continue
                
            # 3. Dynamically reserve budget for the header
            header_overhead = len(header_context) + len("[CLINICAL DATA]\n")
            available_chunk_size = MAX_CHUNK_LEN - header_overhead - 50 # 50 chars safety margin
            
            # Split clinical text, and append the Context Header to EVERY chunk!
            text_chunks = split_into_chunks(body_text, max_length=available_chunk_size)
            for c_idx, c_text in enumerate(text_chunks):
                chunk_id = f"{cp_id}_{lang_name}_{c_idx}"
                
                final_content = f"{header_context}\n[CLINICAL DATA]\n{c_text}"
                all_chunks.append((chunk_id, final_content))

    # Writing Global 
    global_path = out_dir / f"clinical_kb_{lang_name}_global.txt"
    with global_path.open("w", encoding="utf-8") as f:
        for chunk_id, content in all_chunks:
            f.write(f"[CHUNK_ID: {chunk_id}]\n")
            f.write(content)
            f.write("\n\n" + "=" * 80 + "\n\n")

    # Writing Batches
    if all_chunks:
        for i in range(0, len(all_chunks), BATCH_SIZE):
            batch_idx = i // BATCH_SIZE + 1
            batch_path = out_dir / f"{lang_name}_batch_{batch_idx:03d}.txt"
            with batch_path.open("w", encoding="utf-8") as f:
                for chunk_id, content in all_chunks[i:i + BATCH_SIZE]:
                    f.write(f"[CHUNK_ID: {chunk_id}]\n")
                    f.write(content)
                    f.write("\n\n" + "=" * 80 + "\n\n")

    print(f"Processed {lang_name}: generated {len(all_chunks)} heavily-contextualized chunks.")

def main():
    print("Loading Universal Market data to extract global drug identities...")
    univ_map = load_universal_data()
    print(f"Loaded {len(univ_map)} unique drug profiles.")
    
    for lang in ["arabic", "english", "french"]:
        process_language(lang, univ_map)
        
    # Nuke the old stupid 'universal' directory
    obsolete_univ = OUT_DIR / "universal"
    if obsolete_univ.exists():
        shutil.rmtree(obsolete_univ)
        print("Removed the standalone universal chunk directory.")

if __name__ == "__main__":
    main()
