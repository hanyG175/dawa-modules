import pandas as pd
import re
import html

def clean_french(text):
    if not isinstance(text, str): return text
    
    # Fix HTML and API apostrophes
    text = html.unescape(text)
    text = text.replace("&apos;", "'").replace("&#39;", "'").replace("’", "'").replace("&#039;", "'")
    text = text.replace("\\'", "'").replace('\"', '"')
    
    # Fix kerning: letters separated by single spaces (m e d i c i n e)
    def remove_kerning(match):
        return match.group(0).replace(' ', '')
    
    # Match sequences of at least 3 Latin letters separated by spaces
    text = re.sub(r'\b(?:[a-zA-ZÀ-ÿ]\s){3,}[a-zA-ZÀ-ÿ]\b', remove_kerning, text)
    
    # Compress spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

print("Cleaning French Data from Backups...")
df_fr = pd.read_csv('final_clean_backups/clinical_kb_french.csv').fillna('')

for col in df_fr.columns:
    if col not in ['clinical_profile_id', 'french_status']:
        df_fr[col] = df_fr[col].apply(clean_french)

# Update the backup
df_fr.to_csv('final_clean_backups/clinical_kb_french.csv', index=False)

# Also update the working Database_Exports so that when we flatten to txt next, it picks up the clean one
df_fr.to_csv('Database_Exports/clinical_kb_french.csv', index=False)
print("French cleaning complete. Backups and Database_Exports updated.")
