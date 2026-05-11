import pandas as pd
import re
import os

os.makedirs('Database_Exports/final_clean_backups', exist_ok=True)
kbs = ['clinical_kb_english.csv', 'clinical_kb_arabic.csv', 'clinical_kb_french.csv', 'universal_market_instances.csv']
for kb in kbs:
    src = f'Database_Exports/{kb}'
    if os.path.exists(src):
        pd.read_csv(src, dtype=str).fillna('').to_csv(f'Database_Exports/final_clean_backups/{kb}', index=False)

def basic_text_clean(text):
    if pd.isna(text) or not isinstance(text, str): return ""
    
    # Check if this string belongs to the messy table format, if so, don't break the pipelines
    is_messy_table = 'Grossesse (mois)' in text and '| Allaitement |' in text
    
    # Remove URLs
    text = re.sub(r'https?:\/\/\S+|www\.\S+', '', text)
    # Remove repeated punctuation
    text = re.sub(r'[\.\-\_]{3,}', ' ', text)
    
    # Reformat vertical bars to new lines unless it's the specific table
    if not is_messy_table:
        text = text.replace(' | ', '\n')
    
    # Collapse multiple newlines and spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def parse_pregnancy_table(text, lang):
    if pd.isna(text) or not isinstance(text, str): return ""
    text = text.strip()
    
    if 'Grossesse (mois)' in text and 'Allaitement' in text and 'Risques' in text:
        # Extract the months
        month_match = re.search(r'Grossesse \(mois\)\s*\|\s*Allaitement\s*\|([^|]*(?:\|[^|]+)*?)\|?\s*Risques', text)
        if month_match:
            raw_months = month_match.group(1)
            months = raw_months.replace('|', ',').replace(' ', '').strip(', ')
        else:
            months = "1-9"
            
        # Example messy ending: "Risques | II | III | III | Contre-indication relative | II | Précaution"
        # 1st Roman = Pregnancy Risk (II)
        # 2nd Roman = Breastfeeding Risk (III)
        romans_found = re.findall(r'\b(I|II|III|IV)\b', text.split('Risques')[-1])
        preg_risk = romans_found[0] if len(romans_found) > 0 else ""
        bf_risk = romans_found[1] if len(romans_found) > 1 else ""
        
        # Legend mapping
        # II is always precaution, III is relative contraindication based on user spec
        legend = {}
        legend['I'] = 'Autorisé'
        legend['II'] = 'Précaution (Precaution)'
        legend['III'] = 'Contre-indication relative (Relative contraindication)'
        legend['IV'] = 'Contre-indication absolue (Absolute contraindication)'

        mapped_preg = legend.get(preg_risk, preg_risk)
        mapped_bf = legend.get(bf_risk, bf_risk)
        
        if not mapped_preg: mapped_preg = "Non spécifié"
        if not mapped_bf: mapped_bf = "Non spécifié"
        
        if lang == 'en':
            return f"Pregnancy (Months: {months}): {mapped_preg}. Breastfeeding: {mapped_bf}."
        elif lang == 'ar':
            return f"الحمل (الأشهر: {months}): {mapped_preg}. الرضاعة الطبيعية: {mapped_bf}."
        else:
            return f"Grossesse (Mois: {months}): {mapped_preg}. Allaitement: {mapped_bf}."
    
    return text

def clean_database(file_path, lang):
    df = pd.read_csv(file_path, dtype=str).fillna('')
    for col in df.columns:
        if 'status' not in col and 'clinical_profile_id' not in col:
            df[col] = df[col].apply(basic_text_clean)
            
            # Target specifically pregnancy/breastfeeding columns
            if 'pregnancy' in col or 'grossesse' in col or 'breastfeeding' in col:
                df[col] = df[col].apply(lambda x: parse_pregnancy_table(x, lang))
                
    df.to_csv(file_path, index=False)

def clean_forms():
    df = pd.read_csv('Database_Exports/universal_market_instances.csv', dtype=str).fillna('')
    def map_form(val):
        v = str(val).upper().strip()
        v = re.sub(r'^COMP\.?$', 'COMPRIMÉ', v)
        v = re.sub(r'^INJ\.?$', 'INJECTABLE', v)
        v = re.sub(r'^SOL\.?$', 'SOLUTION', v)
        v = re.sub(r'^GEL\.?$', 'GÉLULE', v)
        v = re.sub(r'^SUPP\.?|SUPPOS\.?', 'SUPPOSITOIRE', v)
        v = re.sub(r'^GTE\.?|GOUT\.?', 'GOUTTES', v)
        v = re.sub(r'^PDRE\.?|PDR\.?', 'POUDRE', v)
        v = re.sub(r'^POM\.?|POMM\.?', 'POMMADE', v)
        v = re.sub(r'^SIR\.?|SIROP\.?', 'SIROP', v)
        v = re.sub(r'^COLLYR\.?|COLL\.?', 'COLLYRE', v)
        v = re.sub(r'^SUSP\.?$', 'SUSPENSION', v)
        v = re.sub(r'^SAC\.?|SACH\.?', 'SACHET', v)
        v = re.sub(r'^FL\.?|FLAC\.?', 'FLACON', v)
        return v.title()

    if 'form' in df.columns:
        df['form'] = df['form'].apply(map_form)
    df.to_csv('Database_Exports/universal_market_instances.csv', index=False)

print("Starting Deep Clean...")
clean_database('Database_Exports/clinical_kb_english.csv', 'en')
print("English KB Cleaned.")
clean_database('Database_Exports/clinical_kb_arabic.csv', 'ar')
print("Arabic KB Cleaned.")
clean_database('Database_Exports/clinical_kb_french.csv', 'fr')
print("French KB Cleaned.")
clean_forms()
print("Forms normalized.")
print("All tasks finished successfully.")
