import pandas as pd
import re
import html

# Load Universal Market Instances to get Drug Names for our Ancestry Tags
print("Loading names...")
univ_df = pd.read_csv('Database_Exports/universal_market_instances.csv').fillna('')

# Create a mapping of clinical_profile_id -> Clean Drug Name
id_to_name = {}
for _, row in univ_df.iterrows():
    pid = row['clinical_profile_id']
    name = row['dci'].strip().upper()
    if not name: name = row['medicine_name'].strip().upper()
    if not name: name = row['brand_name'].strip().upper()
    if not name: name = "UNKNOWN DRUG"
    id_to_name[pid] = name

def clean_metadata_and_json(text):
    if pd.isna(text) or not isinstance(text, str): return ""
    text = str(text)
    
    # 1. Clean HTML Entities
    text = html.unescape(text) # Handles &apos;, &quot;, etc.
    text = text.replace('&apos;', "'") # Just in case
    
    # 2. Clean leftover API Metadata 
    text = re.sub(r'(?m)^\s*-?\s*rubric_code:.*$', '', text)
    text = re.sub(r'(?m)^\s*-?\s*source_date:.*$', '', text)
    text = re.sub(r'(?m)^\s*-?\s*is_edited:.*$', '', text)
    text = re.sub(r'(?m)^\s*-?\s*title:.*$', '', text)
    text = re.sub(r'(?m)^\s*-?\s*text:\s*', '', text) # Remove the 'text:' label
    
    # 3. Clean broken JSON (Targeting the specific Vidal Adverse Effects dump)
    if '"effect"' in text and 'high_freq' in text:
        try:
            # Extract effects and frequencies
            effects = re.findall(r'"effect"\s*:\s*"([^"]+)"(?:[^{}]*?"frequency"\s*:\s*"([^"]*)")?', text)
            if effects:
                parsed_lines = []
                for eff, freq in effects:
                    # Fix unicode escapes safely
                    try: eff = eff.encode('utf-8').decode('unicode_escape')
                    except: pass
                    try: freq = freq.encode('utf-8').decode('unicode_escape') if freq else ""
                    except: pass
                    
                    if freq: parsed_lines.append(f"- {eff} ({freq})")
                    else: parsed_lines.append(f"- {eff}")
                text = '\n'.join(parsed_lines)
        except Exception as e:
            pass # fallback to original text if regex completely fails
            
    return text.strip()

def flatten_to_ancestry(text, drug_name, column_name):
    """
    Transforms hierarchical lists into "Self-Describing Rows".
    Format: [Drug] [Category] [Context] Value
    """
    if not text: return ""
    
    lines = text.split('\n')
    col_display = str(column_name).replace('_', ' ').title()
    if col_display.endswith(' Arabic'): col_display = col_display.replace(' Arabic', '')
    
    output = []
    current_header = ""
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # If it's a header we set by the hierarchical script
        if line.startswith('**') and line.endswith('**'):
            current_header = line.strip('* ')
            continue
            
        # Clean the bullet point marker
        val = line
        if line.startswith('-'):
            val = line.lstrip('- ').strip()
            
        if not val: continue
        
        # Build the semantic self-describing row
        row_str = f"[{drug_name}] [{col_display}]"
        
        if current_header and current_header.lower() not in col_display.lower():
            row_str += f" [{current_header}]"
            
        row_str += f" {val}"
        output.append(row_str)
        
    return '\n'.join(output)

files = ['clinical_kb_english.csv', 'clinical_kb_arabic.csv', 'clinical_kb_french.csv']

print("Converting KBs to Self-Describing Rows for RAG optimization...")
for kb in files:
    df = pd.read_csv(f'Database_Exports/{kb}').fillna('')
    for i, row in df.iterrows():
        pid = row['clinical_profile_id']
        drug_name = id_to_name.get(pid, "UNKNOWN DRUG")
        
        for col in df.columns:
            if 'status' not in col and 'id' not in col:
                raw_val = row[col]
                # 1. Clean noise
                cleaned_val = clean_metadata_and_json(raw_val)
                # 2. Flatten ancestry
                flat_val = flatten_to_ancestry(cleaned_val, drug_name, col)
                
                df.at[i, col] = flat_val
                
    df.to_csv(f'Database_Exports/{kb}', index=False)
    print(f"Finished processing {kb}")

print("Complete. All nested hierarchies flattened to Self-Describing Rows.")
