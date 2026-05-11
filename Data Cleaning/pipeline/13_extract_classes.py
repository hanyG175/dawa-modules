import json
import pandas as pd
import re

print("Building Therapeutic Class Mapping...")

# 1. Load Universal Market Instances to get French ATC and IDs
market_df = pd.read_csv('Database_Exports/universal_market_instances.csv').fillna('')

# We want one row per drug, extracting the distinct French ATC/class from the `atc` column
# The French ATC column contains chaotic strings like "Classe pharmacothérapeutique : Antihistaminiques...", we should regex extract it.
french_mapping = {}

for _, row in market_df.iterrows():
    pid = row['clinical_profile_id']
    if not pid: continue
    
    dci = row['dci'] if row['dci'] else row['medicine_name']
    atc_text = str(row['atc'])
    
    if pid not in french_mapping:
        french_mapping[pid] = {
            'clinical_profile_id': pid,
            'Drug Name': dci,
            'Therapeutic Class (French)': ''
        }
        
    # Extract French Class logic
    if french_mapping[pid]['Therapeutic Class (French)'] == '' and atc_text:
        # It's usually formatted as: "Classe pharmacothérapeutique : XXXXX, code ATC : YYYY."
        match = re.search(r'Classe pharmacothérapeutique\s*:\s*(.*?)(?:,|code ATC)', atc_text, re.IGNORECASE)
        if match:
            french_mapping[pid]['Therapeutic Class (French)'] = match.group(1).strip()
        else:
            # Maybe it starts with J - ANTI-INFECTIEUX GENERAUX
            short_match = re.search(r'^[A-Z]\d{0,2}\s*-\s*([^\|]+)', atc_text)
            if short_match:
                 french_mapping[pid]['Therapeutic Class (French)'] = short_match.group(1).strip()

# 2. Load Raw English Data to get English ATC Codes
english_mapping = {}
with open('colab_all_final_translated_results-20260415T173352Z-3-001/fused_en_data.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)

for item in en_data:
    if 'excel_meta' in item and 'code' in item['excel_meta']:
        raw_code = item['excel_meta']['code']
        # The code is usually like "14 B 195", turn to "CODE_14_B_195"
        pid = f"CODE_{raw_code.replace(' ', '_')}"
        atc_codes = item.get('atc_codes', [])
        
        class_str = ''
        if isinstance(atc_codes, list) and len(atc_codes) > 0:
            # Just take the first name as the primary class
            if 'name' in atc_codes[0]:
                class_str = atc_codes[0]['name']
        
        english_mapping[pid] = class_str

# 3. Compile the Table
results = []
for pid, fr_data in french_mapping.items():
    en_class = english_mapping.get(pid, '')
    fr_class = fr_data['Therapeutic Class (French)']
    
    # Clean up empty
    if not en_class and not fr_class:
        continue # Skip drugs we have zero class info for
        
    results.append({
        'clinical_profile_id': pid,
        'Drug Name': fr_data['Drug Name'],
        'Therapeutic Class (French)': fr_class.capitalize() if fr_class else 'Non spécifié',
        'Therapeutic Class (English)': en_class.capitalize() if en_class else 'Not specified'
    })

df_classes = pd.DataFrame(results)
df_classes.to_csv('therapeutic_classes_mapping.csv', index=False)

print(f"Exported therapeutic classes mapping for {len(df_classes)} drugs to 'therapeutic_classes_mapping.csv'")
