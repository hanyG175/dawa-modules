import pandas as pd
import re

def remove_section_noise(text):
    if not isinstance(text, str): return text
    
    # Clean bracketed references
    pattern = r'\s*\(\s*(?:voir\s+rubriques?|pour\s+les.*voir\s+rubriques?|pour\s+plus.*voir\s+rubriques?|see\s+sections?|انظر\s+(?:القسم|البند|الأقسام|الفقرة)).*?\)\s*'
    text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # Clean trailing unbounded references
    pattern_2 = r'\s*[:-]?\s*(?:voir\s+rubriques?|see\s+sections?|انظر\s+(?:القسم|البند|الأقسام|الفقرة)).*?$'
    text = re.sub(pattern_2, '', text, flags=re.IGNORECASE | re.MULTILINE)

    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\[\s*\]', '', text)
    
    return text.strip()

def remove_duplicate_tags(text):
    if not isinstance(text, str): return text
    redundant_pairs = [
        (r'\[Posology\]', r'\[Posologie\]'),
        (r'\[Posology\]', r'\[الجرعة\]'),
        (r'\[Indications\]', r'\[Indication\]'),
        (r'\[Indications\]', r'\[دواعي الاستعمال\]'),
        (r'\[Adverse Effects\]', r'\[Effets indésirables\]'),
        (r'\[Adverse Effects\]', r'\[الآثار الجانبية\]'),
        (r'\[Contraindications\]', r'\[Contre-indications\]'),
        (r'\[Contraindications\]', r'\[موانع الاستعمال\]'),
        (r'\[Interactions\]', r'\[Interactions\]'),
        (r'\[Pregnancy Breastfeeding\]', r'\[Grossesse et allaitement\]'),
        (r'\[Pregnancy Breastfeeding\]', r'\[الحمل والرضاعة\]'),
    ]
    for eng_tag, local_tag in redundant_pairs:
        text = re.sub(f'{eng_tag}\\s*{local_tag}', eng_tag, text, flags=re.IGNORECASE)
    return text

def merge_empty_headers(text):
    if not isinstance(text, str): return text
    lines = text.split('\n')
    if len(lines) <= 1: return text

    merged_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        tag_match = re.match(r'^((?:\[.*?\]\s*)+)(.*)$', line)
        
        if tag_match and i + 1 < len(lines):
            tags = tag_match.group(1).strip()
            content = tag_match.group(2).strip()
            
            next_tag_match = re.match(r'^((?:\[.*?\]\s*)+)(.*)$', lines[i+1].strip())
            
            if next_tag_match and tags == next_tag_match.group(1).strip():
                if content.endswith(':') or (len(content) < 80 and not any(char.isdigit() for char in content)):
                    merged_line = f"{tags} {content} {next_tag_match.group(2).strip()}".strip()
                    lines[i+1] = merged_line
                    i += 1 
                    continue
        
        merged_lines.append(line)
        i += 1
        
    return '\n'.join(merged_lines)

def polish_rag_text(text):
    if pd.isna(text) or not isinstance(text, str): return text
    text = remove_section_noise(text)
    text = remove_duplicate_tags(text)
    text = merge_empty_headers(text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

mapping = {
    'clinical_kb_english.csv': 'en',
    'clinical_kb_arabic.csv': 'ar',
    'clinical_kb_french.csv': 'fr'
}

for kb, lang in mapping.items():
    path = f'Database_Exports/{kb}'
    df = pd.read_csv(path).fillna('')
    for col in df.columns:
        if 'status' not in col and 'id' not in col and 'dci' not in col:
            df[col] = df[col].apply(polish_rag_text)
    df.to_csv(path, index=False)
    print(f"Polished '{kb}' ({lang.upper()})")
