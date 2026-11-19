import pandas as pd
import re
from pathlib import Path

print("Restoring Arabic files...")
ar_backup_nonrag = pd.read_csv('backups/clinical_kb_arabic_backup.csv').fillna('')
ar_backup_nonrag.to_csv('Data_Cleaned_NonRAG/clinical_kb_arabic.csv', index=False, encoding='utf-8')

ar_backup_dawa = pd.read_csv('new_data_dawav2_improved/_backup_clean/clinical_kb_arabic.csv').fillna('')
ar_backup_dawa.to_csv('new_data_dawav2_improved/clinical_kb_arabic.csv', index=False, encoding='utf-8')
print("Restored.")
