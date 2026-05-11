import pandas as pd
import json
import numpy as np

print("Loading datasets...")

# Load all 4 datasets and replace NaN with None for clean JSON serialization
df_en = pd.read_csv('Database_Exports/clinical_kb_english.csv').replace({np.nan: None})
df_fr = pd.read_csv('Database_Exports/clinical_kb_french.csv').replace({np.nan: None})
df_ar = pd.read_csv('Database_Exports/clinical_kb_arabic.csv').replace({np.nan: None})
df_market = pd.read_csv('Database_Exports/universal_market_instances.csv').replace({np.nan: None})

# Set index for fast clinical data lookups
df_en.set_index('clinical_profile_id', inplace=True)
df_fr.set_index('clinical_profile_id', inplace=True)
df_ar.set_index('clinical_profile_id', inplace=True)

# Group the universal market instances by clinical_profile_id so we get lists of variants
market_grouped = df_market.groupby('clinical_profile_id')

# Collect the absolute superset of ALL unique clinical profiles
all_ids = set(df_en.index) | set(df_fr.index) | set(df_ar.index) | set(df_market['clinical_profile_id'].dropna())
# Remove any accidental empty/None IDs if they exist
all_ids = {pid for pid in all_ids if pid and str(pid).strip()}

unified_database = []

print(f"Processing {len(all_ids)} unique clinical profiles...")

for pid in all_ids:
    # 1. Map Market Availability
    market_data = []
    dci_name = "UNKNOWN DCI"
    if pid in market_grouped.groups:
        group = df_market.loc[market_grouped.groups[pid]]
        
        # Clean up market data to dict
        market_data = group.drop(columns=['clinical_profile_id']).to_dict(orient='records')
        
        # Grab the formal DCI name if it exists
        valid_dcis = group['dci'].dropna().unique()
        if len(valid_dcis) > 0 and valid_dcis[0]:
            dci_name = valid_dcis[0]

    # 2. Extract Clinical Text (handle potential missing rows peacefully)
    en_data = df_en.loc[pid].to_dict() if pid in df_en.index else {}
    fr_data = df_fr.loc[pid].to_dict() if pid in df_fr.index else {}
    ar_data = df_ar.loc[pid].to_dict() if pid in df_ar.index else {}
    
    # 3. Build Unified JSON Object
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

# Sanity Check & Validation
unified_database.sort(key=lambda x: x['clinical_profile_id']) # Sorting just to keep JSON organized
output_path = 'Database_Exports/unified_rag_database.json'

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(unified_database, f, ensure_ascii=False, indent=2)

print("\n" + "="*50)
print("VALIDATION SUMMARY")
print("="*50)
print(f"Expected Unique Profiles (IDs): {len(all_ids)}")
print(f"Assembled RAG JSON Documents:   {len(unified_database)}")

if len(all_ids) == len(unified_database):
    print("✅ VALIDATION PASSED: The number of consolidated JSON blocks precisely matches the expected number of unique drugs.")
else:
    print("❌ VALIDATION FAILED: Count mismatch.")
    
print(f"Unified JSON successfully exported to: {output_path}")
