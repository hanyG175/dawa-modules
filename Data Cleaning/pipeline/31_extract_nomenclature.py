import pandas as pd
import json
import os

print("Extracting mapping of Brand Names and DCIs from test_nomenclature.xlsx...")

# Load the excel file, skipping the first 4 rows containing the header metadata
# Row 5 (index 4) contains the actual column headers
df = pd.read_excel('test_nomenclature.xlsx', skiprows=4)

# Look for our specifically requested columns in French
dci_col = 'DENOMINATION COMMUNE INTERNATIONALE'
brand_col = 'NOM DE MARQUE'

if dci_col not in df.columns or brand_col not in df.columns:
    print("Warning: Expected columns not found. The columns in the file are:")
    print(df.columns.tolist())
    exit(1)

# Extract and deduplicate
mapping_df = df[[brand_col, dci_col]].drop_duplicates()

# Clean strings: remove NaNs, strip whitespaces
mapping_df = mapping_df.dropna()
mapping_df[brand_col] = mapping_df[brand_col].astype(str).str.strip()
mapping_df[dci_col] = mapping_df[dci_col].astype(str).str.strip().str.upper()

# Sort for readability
mapping_df = mapping_df.sort_values(by=[brand_col])

os.makedirs('Database_Exports', exist_ok=True)

# 1. Save as CSV
csv_path = 'Database_Exports/nomenclature_drug_to_dci.csv'
mapping_df.to_csv(csv_path, index=False, encoding='utf-8')

print(f"Found {len(mapping_df)} unique Brand/DCI combinations.")
print(f"Saved mapping list to: {csv_path}")

# 2. Save as JSON mapping (Brand -> DCI)
brand_to_dci = {}
for _, row in mapping_df.iterrows():
    brand = row[brand_col]
    dci = row[dci_col]
    if brand and dci:
        brand_to_dci[brand] = dci

json_path = 'Database_Exports/nomenclature_brand_to_dci.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(brand_to_dci, f, ensure_ascii=False, indent=4)

print(f"Saved Brand to DCI JSON mapping to: {json_path}")
