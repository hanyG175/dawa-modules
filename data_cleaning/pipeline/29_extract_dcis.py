import pandas as pd
import json
import os

print("Extracting unique DCIs from market instances...")

# Load the market instances dataset
df = pd.read_csv('final_clean_backups/universal_market_instances.csv')

# Extract the distinct DCIs, format them to a consistent case (uppercase) to avoid duplicates like "abacavir" vs "ABACAVIR"
unique_dcis = df['dci'].dropna().astype(str).str.strip().str.upper().unique().tolist()

# Sort them alphabetically
unique_dcis = sorted(unique_dcis)

print(f"Found {len(unique_dcis)} distinct DCIs.")

os.makedirs('Database_Exports', exist_ok=True)

# 1. Save as CSV
csv_path = 'Database_Exports/unique_dcis.csv'
pd.DataFrame({'dci': unique_dcis}).to_csv(csv_path, index=False, encoding='utf-8')

# 2. Save as JSON template for translations
json_template = {dci: "" for dci in unique_dcis}
json_path = 'Database_Exports/arabic_dci_translation_mapping.json'

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_template, f, ensure_ascii=False, indent=4)

print(f"Saved CSV list to: {csv_path}")
print(f"Saved JSON dictionary template to: {json_path}")
