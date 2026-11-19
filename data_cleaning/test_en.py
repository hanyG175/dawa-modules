import pandas as pd
import re

df_en = pd.read_csv('Data_Cleaned_NonRAG/clinical_kb_english.csv').fillna('')

patterns = {
    'Vidal / HAS': r'(?i)(vidal|transparency committee)',
    'CIP codes': r'(?i)cip13|cip\s*13|commercialisé',
    'Web Scraping': r'(?i)(drugs\.com|webmd|mayo clinic|medscape|retrieved on.*?\d{4}|read more|https?://|click here|all rights reserved|copyright)',
    'References': r'\[\s*\d+\s*\]',
    'JSON leaks': r'\{.*\".*\".*:',
    'Truncations': r'(?i)\b(?:the|and|of|in|to|with|a|an|or|for|is|are)\s*$',
    'Stuttering': r'(?i)(\b[a-zA-Z]{3,}\b(?:\s+[a-zA-Z]{2,}){0,4}?)(?:\s+\1){2,}'
}

print('--- SCANNING ENGLISH DATA (Data_Cleaned_NonRAG) ---')
for name, pattern in patterns.items():
    count = 0
    for col in df_en.columns:
        if df_en[col].dtype == object and col not in ['clinical_profile_id', 'drugbank_id', 'drugbank_name', 'dci']:
            hits = df_en[col].apply(lambda x: bool(re.search(pattern, str(x))))
            if hits.sum() > 0:
                count += hits.sum()
                print(f'[{name}] {col}: {hits.sum()} hits')
                sample = df_en.loc[hits, col].iloc[0]
                print(f'  Sample: {repr(str(sample)[:120])}...')
    print(f'Total {name}: {count}\n')
