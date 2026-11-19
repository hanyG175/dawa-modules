import pandas as pd
import numpy as np
from deep_translator import GoogleTranslator
import time
import os

# Create backup of exports
os.makedirs('Database_Exports/backups', exist_ok=True)
for kb in ['english', 'arabic', 'french']:
    src = f'Database_Exports/clinical_kb_{kb}.csv'
    if os.path.exists(src):
        pd.read_csv(src).to_csv(f'Database_Exports/backups/clinical_kb_{kb}_backup.csv', index=False)

def dict_to_kb(d):
    return {k: (v if pd.notna(v) else '') for k, v in d.items()}

kb_en = pd.read_csv('Database_Exports/clinical_kb_english.csv', dtype=str).fillna('').set_index('clinical_profile_id').to_dict('index')
kb_ar = pd.read_csv('Database_Exports/clinical_kb_arabic.csv', dtype=str).fillna('').set_index('clinical_profile_id').to_dict('index')
kb_fr = pd.read_csv('Database_Exports/clinical_kb_french.csv', dtype=str).fillna('').set_index('clinical_profile_id').to_dict('index')

report = pd.read_csv('cross_language_missing_report.csv')
to_rescue = report[report['can_be_rescued'] == True].to_dict('records')

def extract_source(pid, lang):
    if lang == 'fr':
        row = kb_fr.get(pid, {})
        return {
            'indications': row.get('indications', ''),
            'posology': row.get('posology', ''),
            'contra': row.get('contraindications', ''),
            'prec': row.get('precautions', ''),
            'inter': row.get('interactions', ''),
            'preg': row.get('pregnancy_breastfeeding', ''),
            'moa': row.get('mechanism_of_action', ''),
            'adv': row.get('adverse_effects', ''),
            'cons': row.get('conservation', '')
        }
    elif lang == 'ar':
        row = kb_ar.get(pid, {})
        return {
            'indications': row.get('indications_arabic', ''),
            'posology': row.get('posology_arabic', ''),
            'contra': row.get('contraindications_arabic', ''),
            'prec': row.get('pregnancy_breastfeeding_arabic', ''),
            'inter': row.get('interactions_arabic', ''),
            'preg': row.get('pregnancy_breastfeeding_arabic', ''),
            'moa': row.get('mechanism_of_action_arabic', ''),
            'adv': row.get('adverse_effects_arabic', ''),
            'cons': row.get('conservation_arabic', '')
        }
    elif lang == 'en':
        row = kb_en.get(pid, {})
        return {
            'indications': row.get('indications', ''),
            'posology': '',
            'contra': row.get('toxicity', ''),
            'prec': row.get('associated_conditions', ''),
            'inter': '',
            'preg': '',
            'moa': row.get('mechanism_of_action', ''),
            'adv': row.get('adverse_effects', ''),
            'cons': ''
        }
    return {}

def inject_target(pid, target_lang, translated, source_lang):
    status_str = f"ai_translated_deep_from_{source_lang}"
    if target_lang == 'fr':
        row = kb_fr[pid]
        row['indications'] = translated.get('indications', '')
        row['posology'] = translated.get('posology', '')
        row['contraindications'] = translated.get('contra', '')
        row['precautions'] = translated.get('prec', '')
        row['interactions'] = translated.get('inter', '')
        row['pregnancy_breastfeeding'] = translated.get('preg', '')
        row['mechanism_of_action'] = translated.get('moa', '')
        row['adverse_effects'] = translated.get('adv', '')
        row['conservation'] = translated.get('cons', '')
        row['french_status'] = status_str
    elif target_lang == 'ar':
        row = kb_ar[pid]
        row['indications_arabic'] = translated.get('indications', '')
        row['posology_arabic'] = translated.get('posology', '')
        row['contraindications_arabic'] = translated.get('contra', '')
        row['pregnancy_breastfeeding_arabic'] = translated.get('preg', '')
        row['interactions_arabic'] = translated.get('inter', '')
        row['mechanism_of_action_arabic'] = translated.get('moa', '')
        row['adverse_effects_arabic'] = translated.get('adv', '')
        row['conservation_arabic'] = translated.get('cons', '')
        row['arabic_status'] = status_str
    elif target_lang == 'en':
        row = kb_en[pid]
        row['indications'] = translated.get('indications', '')
        row['mechanism_of_action'] = translated.get('moa', '')
        row['adverse_effects'] = translated.get('adv', '')
        row['toxicity'] = translated.get('contra', '')
        
        desc_parts = [translated.get(k, '') for k in ['posology', 'prec', 'inter', 'cons'] if translated.get(k, '')]
        row['description'] = " \n ".join(desc_parts)
        row['drugbank_status'] = status_str

language_map = {'English': 'en', 'Arabic': 'ar', 'French': 'fr'}

print(f"Starting deep translation for {len(to_rescue)} profiles...")

count_success = 0
for idx, task in enumerate(to_rescue):
    pid = task['clinical_profile_id']
    target_full = task['missing_in']
    t_lang = language_map[target_full]
    
    # Determine best source
    if t_lang == 'en':
        s_lang = 'fr' if task['is_available_in_fr'] else 'ar'
    elif t_lang == 'ar':
        s_lang = 'fr' if task['is_available_in_fr'] else 'en'
    else: # fr
        s_lang = 'en' if task['is_available_in_en'] else 'ar'
    
    source_data = extract_source(pid, s_lang)
    
    translated_data = {}
    has_data = False
    
    for k, v in source_data.items():
        v_str = str(v).strip()
        if len(v_str) > 3:
            try:
                # Chunk to 4900 chars just to be safe with limits
                tr_text = GoogleTranslator(source=s_lang, target=t_lang).translate(v_str[:4900])
                translated_data[k] = tr_text
                has_data = True
            except Exception as e:
                print(f"  [!] Translation failed for {pid} field {k}: {e}")
                translated_data[k] = ""
        else:
            translated_data[k] = ""
            
    if has_data:
        inject_target(pid, t_lang, translated_data, s_lang)
        count_success += 1
        
    if (idx + 1) % 20 == 0:
        print(f"Progress: {idx + 1} / {len(to_rescue)} (Rescued {count_success})")
        # Periodic saves
        pd.DataFrame.from_dict(kb_en, orient='index').reset_index().rename(columns={'index': 'clinical_profile_id'}).to_csv('Database_Exports/clinical_kb_english.csv', index=False)
        pd.DataFrame.from_dict(kb_ar, orient='index').reset_index().rename(columns={'index': 'clinical_profile_id'}).to_csv('Database_Exports/clinical_kb_arabic.csv', index=False)
        pd.DataFrame.from_dict(kb_fr, orient='index').reset_index().rename(columns={'index': 'clinical_profile_id'}).to_csv('Database_Exports/clinical_kb_french.csv', index=False)

# Final Save
print("Saving final results...")
pd.DataFrame.from_dict(kb_en, orient='index').reset_index().rename(columns={'index': 'clinical_profile_id'}).to_csv('Database_Exports/clinical_kb_english.csv', index=False)
pd.DataFrame.from_dict(kb_ar, orient='index').reset_index().rename(columns={'index': 'clinical_profile_id'}).to_csv('Database_Exports/clinical_kb_arabic.csv', index=False)
pd.DataFrame.from_dict(kb_fr, orient='index').reset_index().rename(columns={'index': 'clinical_profile_id'}).to_csv('Database_Exports/clinical_kb_french.csv', index=False)

print(f"Successfully rescued {count_success} profiles!")
