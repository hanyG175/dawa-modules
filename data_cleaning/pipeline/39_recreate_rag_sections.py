import csv
import json
import os
import re
from pathlib import Path
import shutil

BASE = Path(r"c:/Users/LENOVO/Code/PFE/data_cleaning")
FOLDERS = [
    ("Data_Cleaned_NonRAG", "base"),
    ("new_data_dawav2_improved", "new")
]
OUT_BASE = BASE / "new_data_rag"

LANGUAGES = ["arabic", "english", "french"]

# Match standard ATC codes like J01XA01
ATC_CODE_PATTERN = re.compile(r'\b([A-Z]\d{2}[A-Z]{1,2}\d{1,2})\b', re.IGNORECASE)

def get_clean_section_name(col_name):
    # Remove language suffixes
    col_name = re.sub(r'_(arabic|english|french)$', '', col_name, flags=re.IGNORECASE)
    return col_name.replace('_', ' ').title()

def clean_atc(atc_str):
    if not atc_str:
        return "None specified"
    
    parts = [p.strip() for p in atc_str.split("|") if p.strip()]
    
    # Check if it looks like a clean hierarchy:
    # All parts should be short, and we filter out long sentences or paragraph noise.
    if len(parts) > 1 and all(len(p) < 80 for p in parts) and not any(
        any(kw in p.lower() for kw in ["ordonnance", "remboursable", "pictogramme", "cliquant", "médicament", "indications thérapeutiques"]) 
        for p in parts
    ):
        return " | ".join(parts)
        
    # Search for standard ATC codes
    found_codes = ATC_CODE_PATTERN.findall(atc_str)
    if found_codes:
        codes = sorted(list(set(c.upper() for c in found_codes)))
        return " | ".join(codes)
        
    # If the whole string is short enough, keep it if it does not contain noise keywords
    if len(atc_str) < 120 and not any(
        kw in atc_str.lower() for kw in ["ordonnance", "remboursable", "pictogramme", "cliquant", "médicament", "indications thérapeutiques"]
    ):
        return atc_str
        
    return "None specified"

def split_content(content, max_chars=12000):
    """Splits text content into chunks of at most max_chars, keeping sentences/paragraphs intact if possible."""
    if len(content) <= max_chars:
        return [content]
    
    chunks = []
    current_chunk = []
    current_len = 0
    
    # Split by paragraph first
    paragraphs = content.split("\n")
    for para in paragraphs:
        if len(para) > max_chars:
            # If current chunk has data, flush it
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            
            # Split paragraph by sentence
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                if len(sent) > max_chars:
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                        current_chunk = []
                        current_len = 0
                    
                    # Split sentence by words
                    words = sent.split(" ")
                    temp_chunk = []
                    temp_len = 0
                    for word in words:
                        if temp_len + len(word) + 1 > max_chars:
                            chunks.append(" ".join(temp_chunk))
                            temp_chunk = [word]
                            temp_len = len(word)
                        else:
                            temp_chunk.append(word)
                            temp_len += len(word) + 1
                    if temp_chunk:
                        chunks.append(" ".join(temp_chunk))
                else:
                    if current_len + len(sent) + 1 > max_chars:
                        chunks.append("\n".join(current_chunk))
                        current_chunk = [sent]
                        current_len = len(sent)
                    else:
                        current_chunk.append(sent)
                        current_len += len(sent) + 1
        else:
            if current_len + len(para) + 1 > max_chars:
                chunks.append("\n".join(current_chunk))
                current_chunk = [para]
                current_len = len(para)
            else:
                current_chunk.append(para)
                current_len += len(para) + 1
                
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks

def load_universal_data(univ_path):
    univ_map = {}
    if not univ_path.exists():
        return univ_map
    with univ_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cp_id = r.get("clinical_profile_id", "").strip()
            if not cp_id: continue
            
            if cp_id not in univ_map:
                univ_map[cp_id] = {"dci": set(), "brands": set(), "atc": set()}
            
            dci = r.get("dci", "").strip()
            if dci: univ_map[cp_id]["dci"].add(dci)
            
            brand = r.get("brand_name", "").strip()
            if brand: univ_map[cp_id]["brands"].add(brand)
            
            atc = r.get("atc", "").strip()
            if atc:
                cleaned_atc = clean_atc(atc)
                if cleaned_atc and cleaned_atc != "None specified":
                    univ_map[cp_id]["atc"].add(cleaned_atc)
    return univ_map

def process_language(src_dir_path, out_dir_path, lang_name, univ_map):
    csv_path = src_dir_path / f"clinical_kb_{lang_name}.csv"
    if not csv_path.exists():
        print(f"Skipping {lang_name} in {src_dir_path.name}, file not found")
        return

    lang_out_dir = out_dir_path / lang_name
    lang_out_dir.mkdir(parents=True, exist_ok=True)

    txt_out_path = lang_out_dir / f"clinical_kb_{lang_name}_chunks.txt"
    
    # Skips these metadata columns
    skips = {
        "clinical_profile_id", "drugbank_id", "drugbank_name", "drugbank_status",
        "is_translated", "french_status", "arabic_status", "dci_arabic"
    }

    chunks_generated = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f, \
         txt_out_path.open("w", encoding="utf-8") as txt_f:
         
        reader = csv.DictReader(f)
        for row in reader:
            cp_id = row.get("clinical_profile_id", "").strip()
            if not cp_id:
                continue
                
            # Extract Identity
            drug_val = ""
            if lang_name == "arabic":
                drug_val = row.get("dci_arabic", "").strip()
            if not drug_val:
                drug_val = row.get("drugbank_name", "").strip()
            if not drug_val and cp_id in univ_map and univ_map[cp_id]["dci"]:
                drug_val = " | ".join(sorted(univ_map[cp_id]["dci"]))
            if not drug_val:
                drug_val = "Unknown Drug"

            brands_val = "None listed"
            category_val = "None specified"
            if cp_id in univ_map:
                if univ_map[cp_id]["brands"]:
                    brands_val = ", ".join(sorted(univ_map[cp_id]["brands"]))
                if univ_map[cp_id]["atc"]:
                    category_val = " | ".join(sorted(univ_map[cp_id]["atc"]))

            # Iterate columns to create section chunks
            for col, val in row.items():
                if col in skips:
                    continue
                content = str(val).strip()
                if not content or content.lower() == 'nan':
                    continue
                
                section_name = get_clean_section_name(col)
                
                # Split content into smaller chunks if necessary
                content_subchunks = split_content(content, max_chars=12000)
                total_parts = len(content_subchunks)
                
                for part_idx, sub_content in enumerate(content_subchunks, 1):
                    current_section = f"{section_name} (Part {part_idx}/{total_parts})" if total_parts > 1 else section_name
                    
                    # Format chunk perfectly matched to instructions and user requests
                    chunk_text = (
                        f"DRUG CODE: {cp_id}\n"
                        f"DRUG: {drug_val}\n"
                        f"BRANDS: {brands_val}\n"
                        f"CATEGORY: {category_val}\n"
                        f"SECTION: {current_section}\n\n"
                        f"{sub_content}"
                    )
                    
                    # Write to TXT
                    txt_f.write(chunk_text)
                    txt_f.write("\n\n" + "="*80 + "\n\n")
                    
                    chunks_generated += 1

    print(f"[{lang_name.upper()} | {src_dir_path.name}] Generated {chunks_generated} section-level chunks.")

def main():
    # Only clean the target directory if it exists
    if OUT_BASE.exists():
        print(f"Cleaning output directory: {OUT_BASE}")
        shutil.rmtree(OUT_BASE)
        
    for src_folder, tgt_subfolder in FOLDERS:
        src_dir_path = BASE / src_folder
        out_dir_path = OUT_BASE / tgt_subfolder
        
        univ_path = src_dir_path / "universal_market_instances.csv"
        print(f"\nProcessing directory: {src_dir_path.name}")
        univ_map = load_universal_data(univ_path)
        print(f"Loaded {len(univ_map)} universal profiles.")
        
        for lang in LANGUAGES:
            process_language(src_dir_path, out_dir_path, lang, univ_map)

if __name__ == "__main__":
    main()
