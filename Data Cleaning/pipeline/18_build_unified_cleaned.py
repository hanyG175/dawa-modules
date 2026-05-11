import pandas as pd
import re
import os

print("Loading cleaned CSVs from backups...")
df_en = pd.read_csv('final_clean_backups/clinical_kb_english.csv').fillna('')
df_fr = pd.read_csv('final_clean_backups/clinical_kb_french.csv').fillna('')
df_ar = pd.read_csv('Arabic_Cleaned_Dataset/clinical_kb_arabic_cleaned.csv').fillna('')
df_market = pd.read_csv('final_clean_backups/universal_market_instances.csv').fillna('')

print("Building unified database from cleaned data...")

# Set indices
df_en.set_index('clinical_profile_id', inplace=True)
df_fr.set_index('clinical_profile_id', inplace=True)
df_ar.set_index('clinical_profile_id', inplace=True)

market_grouped = df_market.groupby('clinical_profile_id')
all_ids = set(df_en.index) | set(df_fr.index) | set(df_ar.index) | set(df_market['clinical_profile_id'].dropna())
all_ids = {pid for pid in all_ids if pid and str(pid).strip()}

unified_database = []

for pid in sorted(all_ids):
    market_data = []
    dci_name = "UNKNOWN DCI"
    
    if pid in market_grouped.groups:
        group = df_market.loc[market_grouped.groups[pid]]
        market_data = group.drop(columns=['clinical_profile_id']).to_dict(orient='records')
        valid_dcis = group['dci'].dropna().unique()
        if len(valid_dcis) > 0 and valid_dcis[0]:
            dci_name = valid_dcis[0]
    
    en_data = df_en.loc[pid].to_dict() if pid in df_en.index else {}
    fr_data = df_fr.loc[pid].to_dict() if pid in df_fr.index else {}
    ar_data = df_ar.loc[pid].to_dict() if pid in df_ar.index else {}
    
    record = {
        "clinical_profile_id": str(pid),
        "dci": str(dci_name).strip(),
        "market_availability": market_data,
        "clinical_knowledge": {
            "english": en_data,
            "french": fr_data,
            "arabic": ar_data
        }
    }
    unified_database.append(record)

import json
output_path = 'Arabic_Cleaned_Dataset/unified_rag_database_cleaned.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(unified_database, f, ensure_ascii=False, indent=2)

print(f"Created unified database: {output_path}")
print(f"Total records: {len(unified_database)}")
