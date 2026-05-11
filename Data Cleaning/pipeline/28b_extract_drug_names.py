import pandas as pd
import json
import os
import re

print("Extracting unique drug names from RAG headers...")

# We will load the original RAG backup to reliably extract the drug names from the headers
df = pd.read_csv('final_clean_backups/clinical_kb_english.csv').fillna('')

unique_drugs = set()

# The first bracketed item in the indications or description column contains the drug name
for text in df['indications'].tolist() + df['description'].tolist():
    if not text:
        continue
    # Extract text from the very first bracket
    match = re.match(r'^\s*\[(.*?)\]', str(text))
    if match:
        name = match.group(1).strip()
        if name:
            unique_drugs.add(name)

# Sort them alphabetically
unique_drugs = sorted(list(unique_drugs))

print(f"Found {len(unique_drugs)} unique drug/brand names.")

os.makedirs('Database_Exports', exist_ok=True)

# 1. Save as CSV
csv_path = 'Database_Exports/unique_drug_names.csv'
pd.DataFrame({'drug_name': unique_drugs}).to_csv(csv_path, index=False, encoding='utf-8')

# 2. Save as JSON template for Arabic translations
json_template = {drug: "" for drug in unique_drugs}
json_path = 'Database_Exports/arabic_drug_translation_mapping.json'

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_template, f, ensure_ascii=False, indent=4)

print(f"Saved CSV list to: {csv_path}")
print(f"Saved JSON dictionary template to: {json_path}")
