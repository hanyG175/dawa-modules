import json
import os

print("Loading unified database...")
with open('Database_Exports/unified_rag_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

db_en = []
db_fr = []
db_ar = []

for record in db:
    # Base structure that every language shares
    base = {
        "clinical_profile_id": record.get("clinical_profile_id"),
        "dci": record.get("dci"),
        "market_availability": record.get("market_availability", [])
    }
    
    # English record
    rec_en = base.copy()
    rec_en["clinical_knowledge"] = record.get("clinical_knowledge", {}).get("english", {})
    db_en.append(rec_en)
    
    # French record
    rec_fr = base.copy()
    rec_fr["clinical_knowledge"] = record.get("clinical_knowledge", {}).get("french", {})
    db_fr.append(rec_fr)
    
    # Arabic record
    rec_ar = base.copy()
    rec_ar["clinical_knowledge"] = record.get("clinical_knowledge", {}).get("arabic", {})
    db_ar.append(rec_ar)

print("Exporting separate JSON files...")

with open('Database_Exports/rag_database_english.json', 'w', encoding='utf-8') as f:
    json.dump(db_en, f, ensure_ascii=False, indent=2)
print("  -> Saved 'rag_database_english.json'")

with open('Database_Exports/rag_database_french.json', 'w', encoding='utf-8') as f:
    json.dump(db_fr, f, ensure_ascii=False, indent=2)
print("  -> Saved 'rag_database_french.json'")

with open('Database_Exports/rag_database_arabic.json', 'w', encoding='utf-8') as f:
    json.dump(db_ar, f, ensure_ascii=False, indent=2)
print("  -> Saved 'rag_database_arabic.json'")

print("\nDone! Exported 3 separated, RAG-optimized JSON files.")
