import os
import json

def check_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not data:
            return "empty"
            
        # Check if notice_text is empty or not present when expected
        # Let's inspect the keys to understand what "meaningless" could mean
        
        # typically: designation, url, num_enregistrement, notice_pdf_url, dci_code, etc.
        # usually we care about actual text like notice_text
        if isinstance(data, dict):
            # Check if it has any meaningful content (e.g. non-empty notice_text)
            if 'notice_text' not in data and 'text' not in data and 'content' not in data:
                # Let's check what keys actually exist
                pass
            
            # Count how many empty values
            empty_vals = sum(1 for v in data.values() if not v or (isinstance(v, str) and not v.strip()))
            if empty_vals == len(data):
                return "empty_values"
                
            if 'notice_text' in data and not data['notice_text'].strip():
                return "no_text"
                
        return "valid"
    except Exception as e:
        return f"corrupted: {e}"

p1 = 'PDFs_Filtered_Out'
p2 = 'PDFs'

for p in [p1]:
    files = [f for f in os.listdir(p) if f.endswith('.json')]
    stats = {}
    for f in files:
        res = check_json(os.path.join(p, f))
        stats[res] = stats.get(res, 0) + 1
    print(f"Folder {p}:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

