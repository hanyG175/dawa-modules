import pandas as pd
import os

print("Extracting mapping of Drug Names and DCIs...")

# Load the market instances dataset
df = pd.read_csv('final_clean_backups/universal_market_instances.csv')

# Extract unique combinations of medicine_name, brand_name, and dci
# This is useful for DDI (Drug-Drug Interaction) checkers which often only understand DCIs
# while users might search or provide brand_names/medicine_names.
mapping_df = df[['medicine_name', 'brand_name', 'dci']].drop_duplicates()

# Sort by medicine_name and brand_name for easier reading
mapping_df = mapping_df.sort_values(by=['medicine_name', 'brand_name'])

os.makedirs('Database_Exports', exist_ok=True)

# Save as CSV
csv_path = 'Database_Exports/drug_to_dci_mapping.csv'
mapping_df.to_csv(csv_path, index=False, encoding='utf-8')

print(f"Found {len(mapping_df)} unique combinations of Drug Names and DCIs.")
print(f"Saved mapping list to: {csv_path}")

# To make it even easier for programmatic use, optionally create a JSON mapping of brand_name -> DCI
brand_to_dci = {}
for _, row in mapping_df.iterrows():
    brand = str(row['brand_name']).strip()
    dci = str(row['dci']).strip()
    if brand and brand != 'nan' and dci and dci != 'nan':
        brand_to_dci[brand] = dci

json_path = 'Database_Exports/brand_to_dci_mapping.json'
import json
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(brand_to_dci, f, ensure_ascii=False, indent=4)

print(f"Saved Brand to DCI JSON mapping to: {json_path}")
