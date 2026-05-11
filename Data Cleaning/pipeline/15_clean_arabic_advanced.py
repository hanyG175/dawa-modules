import pandas as pd
import re
import os

def is_medical_arabic(text):
    """Check if Arabic text is likely medical-related, not API noise"""
    if not text or len(text) < 10:
        return False
    
    # Count Arabic characters
    arabic_count = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(text.replace(' ', ''))
    
    # If less than 50% Arabic, it's likely noise
    if total_chars > 0 and arabic_count / total_chars < 0.5:
        return False
    
    # Discard common API noise patterns
    noise_patterns = [
        r'رابط|link|href|onclick|javascript',
        r'انقر|click|button|submit',
        r'تسجيل دخول|login|sign up|account',
        r'خطأ|error|exception',
        r'الصفحة غير موجودة|not found|404',
        r'([\u0600-\u06FF])\1{5,}',  # Repetitive letters (5+ same letter)
    ]
    
    for pattern in noise_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True

def clean_arabic_line(line):
    """Clean kerning errors, diacritics, and formatting issues in Arabic"""
    if not isinstance(line, str):
        return ""
    
    line = line.strip()
    if not line:
        return ""
    
    # 1. First, remove Arabic diacritics (these are the culprits in kerning)
    line = re.sub(r'[\u064B-\u0652]', '', line)
    
    # 2. Remove control characters and zero-width spaces
    line = re.sub(r'[\u200B-\u200D\u2060\uFEFF]', '', line)
    
    # 3. Fix tatweel characters (ـ) that break words
    line = line.replace('ـ', '')
    
    # 4. NOW fix kerning: detect sequences of single Arabic chars with spaces
    # Pattern: single char, space, single char, space, single char (repeated 3+ times)
    # This specifically targets malformed kerning like: ك ل ي م (without diacritics)
    # But will NOT remove the space between: "كلي م" and the next word
    # We do this by looking for patterns with 3+ single-char pieces
    def fix_kerning_in_sequence(match):
        # Get the matched sequence and split by spaces
        seq = match.group(0)
        # Only collapse if it's clearly kerning (many single chars separated by spaces)
        if len(seq.split()) >= 3:  # 3+ pieces separated by space = likely kerning
            return seq.replace(' ', '')
        return seq
    
    # Match: Arabic char + space + Arabic char, repeated pattern
    line = re.sub(r'([\u0600-\u06FF])\s+([\u0600-\u06FF])\s+([\u0600-\u06FF](?:\s+[\u0600-\u06FF])*)', 
                  lambda m: m.group(1) + m.group(2) + m.group(3).replace(' ', ''), line)
    
    # 5. Remove/collapse repetitive letter sequences (more than 3 same letters)
    line = re.sub(r'([\u0600-\u06FF])\1{3,}', r'\1\1', line)
    
    # 6. Fix multiple spaces (preserve single space between words)
    line = re.sub(r'\s{2,}', ' ', line)
    
    return line.strip()

def process_arabic_field(text):
    """Process and validate Arabic text field"""
    if not text or not isinstance(text, str):
        return ""
    
    lines = text.split('\n')
    valid_lines = []
    
    for line in lines:
        # Skip lines with excessive repetition or API patterns
        if re.search(r'([\u0600-\u06FF])\1{4,}', line):
            continue
        
        # Skip common API noise
        if any(x in line for x in ['•••', 'Create Account', 'الرجاء', 'يرجى', 'انقر']):
            continue
        
        cleaned = clean_arabic_line(line)
        
        # Verify it's actually medical Arabic
        if cleaned and is_medical_arabic(cleaned) and len(cleaned) >= 15:
            valid_lines.append(cleaned)
    
    return '\n'.join(valid_lines)

print("Loading Arabic backup...")
df_ar = pd.read_csv('final_clean_backups/clinical_kb_arabic.csv').fillna('')

print("Cleaning Arabic fields...")
arabic_cols = [col for col in df_ar.columns if 'arabic' in col.lower() or col in ['indications', 'posology']]

for col in arabic_cols:
    print(f"  Processing: {col}")
    df_ar[col] = df_ar[col].apply(process_arabic_field)

# Count empty records
empty_count = sum((df_ar.iloc[:, 2:].apply(lambda x: ''.join(x.astype(str)), axis=1) == '').astype(int))
print(f"Empty records after cleaning: {empty_count}")

# Create output folder
os.makedirs('Arabic_Cleaned_Dataset', exist_ok=True)

# Save cleaned CSV
output_path = 'Arabic_Cleaned_Dataset/clinical_kb_arabic_cleaned.csv'
df_ar.to_csv(output_path, index=False, encoding='utf-8')
print(f"Saved cleaned CSV to: {output_path}")
print(f"Total records: {len(df_ar)}")
