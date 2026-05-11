import pandas as pd
import json
import os

print("Extracting unique drug names...")

# Load the dataset
# We can use the English KB as it contains the authoritative drugbank_name for all profiles
df = pd.read_csv('Data_Cleaned_NonRAG/clinical_kb_english.csv')

# Extract unique brand/drug names
unique_drugs = df['drugbank_name'].dropna().unique().tolist()

# Clean up any trailing spaces and sort alphabetically
unique_drugs = sorted(list(set([str(drug).strip() for drug in unique_drugs if str(drug).strip()])))

print(f"Found {len(unique_drugs)} unique drug names.")

os.makedirs('Database_Exports', exist_ok=True)

# 1. Save as a simple CSV
csv_path = 'Database_Exports/unique_drug_names.csv'
pd.DataFrame({'drug_name': unique_drugs}).to_csv(csv_path, index=False, encoding='utf-8')

# 2. Save as a JSON dictionary template
# This format is perfect for later filling in the Arabic translations as values
# Example: {"PARACETAMOL": "باراسيتامول"}
json_template = {drug: "" for drug in unique_drugs}
json_path = 'Database_Exports/arabic_drug_translation_mapping.json'

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_template, f, ensure_ascii=False, indent=4)

print(f"Saved CSV list to: {csv_path}")
print(f"Saved JSON dictionary template to: {json_path}")
