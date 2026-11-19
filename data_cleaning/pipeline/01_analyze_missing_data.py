import pandas as pd

def get_present_ids(df, status_col):
    return set(df[~df[status_col].str.contains('missing', na=False)]['clinical_profile_id'])

# Load KBs
kb_en = pd.read_csv('Database_Exports/clinical_kb_english.csv')
kb_ar = pd.read_csv('Database_Exports/clinical_kb_arabic.csv')
kb_fr = pd.read_csv('Database_Exports/clinical_kb_french.csv')

present_en = get_present_ids(kb_en, 'drugbank_status')
present_ar = get_present_ids(kb_ar, 'arabic_status')
present_fr = get_present_ids(kb_fr, 'french_status')

# Load missing lists
try:
    missing_en = pd.read_csv('completely_missing_english.csv')['clinical_profile_id'].tolist()
except: missing_en = []
try:
    missing_ar = pd.read_csv('completely_missing_arabic.csv')['clinical_profile_id'].tolist()
except: missing_ar = []
try:
    missing_fr = pd.read_csv('completely_missing_french.csv')['clinical_profile_id'].tolist()
except: missing_fr = []

report_data = []

def check_missing(missing_list, lang_name):
    for pid in missing_list:
        found_en = pid in present_en
        found_ar = pid in present_ar
        found_fr = pid in present_fr
        
        # We want to log it if it's missing in this language but available in AT LEAST ONE other language
        # (Though we can also just log all of them so the user has a full matrix)
        report_data.append({
            'clinical_profile_id': pid,
            'missing_in': lang_name,
            'is_available_in_en': found_en,
            'is_available_in_ar': found_ar,
            'is_available_in_fr': found_fr,
            'can_be_rescued': (lang_name == 'English' and (found_ar or found_fr)) or \
                              (lang_name == 'Arabic' and (found_en or found_fr)) or \
                              (lang_name == 'French' and (found_en or found_ar))
        })

check_missing(missing_en, 'English')
check_missing(missing_ar, 'Arabic')
check_missing(missing_fr, 'French')

report_df = pd.DataFrame(report_data)
report_df.to_csv('cross_language_missing_report.csv', index=False)

print("=== Cross-Language Availability Report ===")
print(f"Total entries in report: {len(report_df)}")

for lang, total in [('English', len(missing_en)), ('Arabic', len(missing_ar)), ('French', len(missing_fr))]:
    rescued = len(report_df[(report_df['missing_in'] == lang) & (report_df['can_be_rescued'] == True)])
    print(f"{lang} missing profiles that CAN be translated from others: {rescued} / {total}")

fully_missing = len(report_df[(report_df['is_available_in_en'] == False) & 
                              (report_df['is_available_in_ar'] == False) & 
                              (report_df['is_available_in_fr'] == False)]['clinical_profile_id'].unique())

print(f"\nProfiles that are completely missing across ALL 3 languages: {fully_missing}")
print("Report saved to 'cross_language_missing_report.csv'")
