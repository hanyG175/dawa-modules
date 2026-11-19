import pandas as pd
import re

def normalize_units(text):
    # Inserts a space between a number and common medical units, e.g., 140mg -> 140 mg
    # Covers mg, g, ml, l, ui, iu, mcg, µg, kg
    return re.sub(r'(?<=\d)(mg|g|ml|l|ui|iu|mcg|µg|kg)\b', r' \1', text, flags=re.IGNORECASE)

def normalize_ranges(text, lang):
    # Consolidates ranges to explicitly tie the numbers together so the LLM treats it as one entity:
    # 280 à 420 -> 280-420
    # 280 to 420 -> 280-420
    # 280 إلى 420 -> 280-420
    if lang == 'fr':
        text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*(?:à|a|-)\s*(\d+(?:[.,]\d+)?)\b', r'\1-\2', text, flags=re.IGNORECASE)
    elif lang == 'en':
        text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*(?:to|-)\s*(\d+(?:[.,]\d+)?)\b', r'\1-\2', text, flags=re.IGNORECASE)
    elif lang == 'ar':
        text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*(?:إلى|-)\s*(\d+(?:[.,]\d+)?)\b', r'\1-\2', text)
    return text

def normalize_abbreviations(text, lang):
    # Global routing standardization dictionary
    if lang == 'fr':
        replacements = {
            r'\bI\.?V\.?\b|intraveineux': 'Voie intraveineuse',
            r'\bI\.?M\.?\b|intramusculaire': 'Voie intramusculaire',
            r'\bS\.?C\.?\b|sous-?cutan[eé]e?': 'Voie sous-cutanée',
            r'\bp\.?o\.?\b|per os|oralement': 'Voie orale'
        }
    elif lang == 'en':
        replacements = {
            r'\bI\.?V\.?\b|intravenously': 'Intravenous',
            r'\bI\.?M\.?\b|intramuscularly': 'Intramuscular',
            r'\bS\.?C\.?\b|subcutaneously': 'Subcutaneous',
            r'\bp\.?o\.?\b|per os|orally': 'Oral'
        }
    elif lang == 'ar':
        replacements = {
            r'\bI\.?V\.?\b|وريديا|في الوريد': 'وريدي',
            r'\bI\.?M\.?\b|عضليا|في العضل': 'عضلي',
            r'\bS\.?C\.?\b|تحت الجلد': 'تحت الجلد',
            r'\bp\.?o\.?\b|عن طريق الفم|فمويا': 'عن طريق الفم'
        }
    else:
        return text

    for pattern, replacement in replacements.items():
        # Using lambda to preserve case of surrounding text wouldn't strictly apply here as we want to globally standardize the route name
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    return text

def final_pass(text, lang):
    if pd.isna(text) or not isinstance(text, str): return ""
    text = normalize_units(text)
    text = normalize_ranges(text, lang)
    text = normalize_abbreviations(text, lang)
    return text

print("Standardizing units, ranges, and abbreviations globally...")

mapping = {
    'clinical_kb_english.csv': 'en',
    'clinical_kb_arabic.csv': 'ar',
    'clinical_kb_french.csv': 'fr'
}

for kb, lang in mapping.items():
    df = pd.read_csv(f'Database_Exports/{kb}').fillna('')
    for col in df.columns:
        if 'status' not in col and 'id' not in col:
            df[col] = df[col].apply(lambda x: final_pass(x, lang))
    df.to_csv(f'Database_Exports/{kb}', index=False)
    print(f"Finalized '{kb}' ({lang.upper()})")

print("Data consistently cleaned and optimized for unambiguous RAG search!")
