import pandas as pd
import re

def optimize_hierarchy(text):
    if pd.isna(text) or not isinstance(text, str): return ""
    text = str(text).strip()
    if not text: return ""
    
    # Early exit to preserve the highly structured pregnancy parsing we did previously
    if "Grossesse (Mois:" in text or "الحمل (الأشهر:" in text or "Pregnancy (Months:" in text:
        # Just clean up any weird dots if present, but leave the rest
        return text.replace('·', '-')

    # Replace weird dot bullets
    text = text.replace('·', '-')
    
    # Split text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    formatted_lines = []
    
    for line in lines:
        # Strip existing bullets to re-evaluate the line
        clean_line = re.sub(r'^[\-\*\•\>]\s+', '', line).strip()
        if not clean_line: continue
        
        words = clean_line.split()
        
        # Establish criteria for a "Title" vs a "Bullet"
        # 1. It must be relatively short (<= 8 words)
        # 2. It must not start with a digit (like "50 UI/kg" or "1. Take daily")
        # 3. It must not end in a sentence-ending punctuation mark (., !, ?, :, ;)
        # 4. For Latin scripts (EN/FR), it should start with a capital letter. Arabic is exempt from this.
        
        is_title = False
        if len(words) <= 8 and not clean_line[0].isdigit() and clean_line[-1] not in '.!?:;':
            has_arabic = bool(re.search(r'[\u0600-\u06FF]', clean_line))
            if has_arabic:
                is_title = True
            else:
                # Check for uppercase first letter
                if clean_line[0].isupper():
                    is_title = True
                    
        if is_title:
            # Format as a bolded, self-contained sub-header
            # We add a newline before it to give it spacing from previous bullets
            formatted_lines.append(f"\n**{clean_line}**")
        else:
            # If it's a long sentence or a specific value, it remains a bullet
            # Ensure it doesn't double up on bullets if one was already there, though we stripped it above
            formatted_lines.append(f"- {clean_line}")

    # Rejoin the text
    result = '\n'.join(formatted_lines).strip()
    
    # Clean up excessive newlines created by adding spacing before titles
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result

print("Starting hierarchical restructuring...")
for kb in ['clinical_kb_english.csv', 'clinical_kb_arabic.csv', 'clinical_kb_french.csv']:
    df = pd.read_csv(f'Database_Exports/{kb}').fillna('')
    for col in df.columns:
        if 'status' not in col and 'id' not in col:
            df[col] = df[col].apply(optimize_hierarchy)
    
    df.to_csv(f'Database_Exports/{kb}', index=False)
    print(f"Hierarchical Chunking applied to {kb}")

print("Done. Text is now highly structured with bolded headers and nested bullet points.")
