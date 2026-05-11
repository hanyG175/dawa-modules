import sys
import json
import re
import os

def clean_line(line):
    cleaned = re.sub(r'^(?:\[.*?\]\s*)+', '', line.strip())
    
    if re.search(r'^\\?\[.*?\\?\]', cleaned) or len(re.findall(r'\\?\[.*?\\?\]', cleaned)) > 1:
        return ""
        
    if ']' in cleaned and cleaned.startswith('['):
        cleaned = cleaned[cleaned.rfind(']') + 1:].strip()
        
    cleaned = re.sub(r'\s+\d+\s+[.,]', '.', cleaned)
    cleaned = re.sub(r'\bLabel\s*[.,]', '.', cleaned)
    
    return cleaned.strip()

def process_text_field(text):
    if not text or not isinstance(text, str):
        return []
    valid_lines = []
    for line in text.split('\n'):
        if re.search(r'•{3,}', line):
            continue
            
        if any(x in line for x in ["Create Account", "Indication Type", "Approval Level", "Patient Characteristics"]):
            continue
            
        cleaned = clean_line(line)
        if len(cleaned) >= 15:
            valid_lines.append(cleaned)
    return valid_lines

def format_market_availability(market_list):
    if not market_list:
        return []
    lines = []
    for item in market_list:
        parts = []
        if item.get('brand_name'): parts.append(f"Brand: {item['brand_name']}")
        if item.get('form'): parts.append(f"Form: {item['form']}")
        if item.get('dosage'): parts.append(f"Dosage: {item['dosage']}")
        if item.get('conditionnement'): parts.append(f"Pack: {item['conditionnement']}")
        
        reg = item.get('excel_n_enregistrement') or item.get('excel_code')
        if reg: parts.append(f"Reg: {reg}")
        
        if parts:
            lines.append(" | ".join(parts))
            
        atc = str(item.get('atc', '')).strip()
        if atc:
            if re.match(r'^[0-9A-Z]{5,8}$', atc):
                continue
            lines.append(f"ATC: {atc}")
    return lines

def main():
    input_path = 'Arabic_Cleaned_Dataset/unified_rag_database_cleaned.json'
    skipped_path = 'Arabic_Cleaned_Dataset/skipped_drugs_cleaned.txt'
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    total_records = 0
    skipped_records = 0
    written_chunks = 0
    skipped_ids = []
    
    file_index = 1
    records_per_file = 400
    current_out_f = open(f'Arabic_Cleaned_Dataset/rag_flattened_cleaned_part_{file_index}.txt', 'w', encoding='utf-8')
    
    for item in data:
        if total_records > 0 and total_records % records_per_file == 0:
            current_out_f.close()
            file_index += 1
            current_out_f = open(f'Arabic_Cleaned_Dataset/rag_flattened_cleaned_part_{file_index}.txt', 'w', encoding='utf-8')
            
        total_records += 1
        dci = item.get('dci', 'UNKNOWN DRUG')
        pid = item.get('clinical_profile_id', 'UNKNOWN_ID')
        
        ma_lines = format_market_availability(item.get('market_availability', []))
        
        ck_blocks = []
        ck_length = 0
        ck = item.get('clinical_knowledge', {})
        
        # Only process English and French (no Arabic)
        for lang, lang_key in [('ENGLISH', 'english'), ('FRENCH', 'french')]:
            lang_data = ck.get(lang_key, {})
            if not lang_data: continue
            
            for field_name, text_val in lang_data.items():
                if not text_val or str(text_val).strip() == '': continue
                if field_name in ['drugbank_status', 'french_status', 'arabic_status', 'drugbank_id', 'drugbank_name']: continue
                    
                cleaned_lines = process_text_field(text_val)
                if cleaned_lines:
                    clean_field_name = field_name.replace('_arabic', '').replace('_', ' ').upper()
                    block_text = f"[{lang} - {clean_field_name}]\n" + '\n'.join(cleaned_lines) + "\n"
                    ck_blocks.append(block_text)
                    ck_length += len(block_text)
        
        if ck_length < 100:
            skipped_records += 1
            skipped_ids.append(pid)
            continue
            
        part = 1
        current_chunk = f"=== DRUG: {dci} ===\nID: {pid}\n\n"
        if ma_lines:
            current_chunk += "[MARKET AVAILABILITY]\n" + "\n".join(ma_lines) + "\n\n"
            
        for block in ck_blocks:
            if len(current_chunk) + len(block) > 8000 and len(current_chunk) > 500:
                current_chunk += "---\n\n"
                current_out_f.write(current_chunk)
                written_chunks += 1
                part += 1
                current_chunk = f"=== DRUG: {dci} (PART {part}) ===\nID: {pid}\n\n"
            
            current_chunk += block + "\n"
            
        current_chunk += "---\n\n"
        current_out_f.write(current_chunk)
        written_chunks += 1
            
    current_out_f.close()

    with open(skipped_path, 'w', encoding='utf-8') as sf:
        sf.write('\n'.join(skipped_ids))

    print("\n=== SUMMARY ===")
    print(f"Total Records: {total_records}")
    print(f"Skipped Records (< 100 chars): {skipped_records}")
    print(f"Total Chunks Written: {written_chunks}")
    print(f"Total Files Generated: {file_index}")

if __name__ == '__main__':
    main()
