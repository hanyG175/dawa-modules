# DrugBank Dataset - Quick Start Guide

## 📋 What You Have

- **File:** `full database.xml` (1.90 GB)
- **Format:** XML with DrugBank schema
- **Content:** Complete drug database with ~13,000+ drugs
- **Structure:** Complex nested XML with 143 different field types

## 🚀 Quick Start (3 Steps)

### Step 1: Understand the Structure
```bash
python draft.py
```
This will:
- Show the complete field structure
- Analyze the first 5 drugs
- Display key nested structures
- Give you guidance on usage

### Step 2: Extract Sample Drugs
```bash
# Extract 1000 drugs to JSON
python extract_drugs.py --format json --output drugs.json --limit 1000

# Or export to CSV
python extract_drugs.py --format csv --output drugs.csv --limit 1000
```

### Step 3: Use the Data
```python
from draft import DrugBankAnalyzer

analyzer = DrugBankAnalyzer("full database.xml")

# Get a specific drug
drug = analyzer.get_single_drug(0)
print(drug['name'])  # "Calcium"

# Count total drugs
total = analyzer.count_total_drugs()  # ~13,000
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `draft.py` | **Main tool** - Analyze & extract drugs efficiently |
| `extract_drugs.py` | **Utility** - Export to JSON/CSV format |
| `DRUGBANK_STRUCTURE.md` | **Reference** - Complete field documentation |
| `full database.xml` | Your downloaded database (1.90 GB) |
| `sample_drugs.json` | Example output (100 sample drugs) |

---

## 📊 What the Data Contains

### Per Drug - You Get:
- **ID & Names:** `drugbank_id`, `name`, `synonyms`
- **Chemistry:** `cas_number`, `molecular_formula`, `molecular_weight`
- **Medical Info:** `indication`, `mechanism_of_action`, `pharmacodynamics`
- **Interactions:** `targets`, `enzymes`, `drug_interactions`, `pathways`
- **Commercial:** `products`, `dosages`, `atc_codes`
- **References:** `publications`, `external_identifiers`

### Example Drug:
```json
{
  "drugbank_id": "DB00945",
  "name": "Aspirin",
  "indication": "For relief of headache, muscular aches...",
  "mechanism_of_action": "Inhibits prostaglandin synthesis...",
  "num_targets": 5,
  "num_interactions": 654,
  "num_pathways": 3
}
```

---

## 💡 Use Cases for Your Semantic Search Engine

### 1. **Drug Information Retrieval**
Extract these for semantic search:
- Drug names & synonyms
- Descriptions & indications
- Mechanism of action

### 2. **Similarity Search**
Build vectors from:
- Mechanism of action text
- Targets (similar targets = similar drugs)
- Pathways (drugs in same pathway are related)

### 3. **Drug Interaction Discovery**
Use:
- `drug_interactions` - Direct interactions with other drugs
- `enzymes` - Metabolic interactions
- `targets` - Mechanism similarities

### 4. **Clinical Knowledge Graph**
Connect:
- Drugs → Targets (protein interactions)
- Drugs → Pathways (biological pathways)
- Drugs → Other Drugs (interactions)
- Drugs → Indications (uses)

---

## 🔧 Common Tasks

### Extract all drugs for a specific disease
```python
from draft import DrugBankAnalyzer
import json

analyzer = DrugBankAnalyzer("full database.xml")

# You'd need to stream through and filter
# See extract_drugs.py for pattern
```

### Get all drugs with specific target
```python
# Similar approach - filter by num_targets > 0
# Or parse the full drug dict to examine targets
drug = analyzer.get_single_drug(0)
if drug.get('num_targets', 0) > 0:
    print(f"Drug {drug['name']} has targets")
```

### Export specific fields only
```python
# Modify extract_drugs.py to select fields you need
# Current extraction is in _extract_drug() method
```

---

## ⚡ Performance Tips

1. **Don't load entire file into memory**
   - The tools use `iterparse` for streaming
   - Processes one drug at a time

2. **For bulk operations**
   - Extract to JSON/CSV first (faster for repeated use)
   - Keep limits reasonable (100-1000 drugs)

3. **For full database processing**
   - Remove `--limit` from extraction
   - Will take several minutes but produces complete dataset
   - Run overnight if needed

---

## 🎯 Next Steps

1. **Understand your goals:**
   - What search capabilities do you need?
   - Which fields are most important?

2. **Extract relevant subset:**
   ```bash
   python extract_drugs.py --format json --output full_drugs.json
   ```
   (takes ~15-30 minutes for all ~13,000 drugs)

3. **Build your semantic engine:**
   - Use the JSON as input data
   - Create embeddings from key fields
   - Build search index

4. **Iterate:**
   - Test with sample data first
   - Add more drugs as needed
   - Refine fields based on feedback

---

## ❓ FAQ

**Q: Why is the file so large?**
A: It contains complete information for every drug including descriptions, interactions, pathways, references - all as nested XML.

**Q: Can I filter while extracting?**
A: Currently no filtering in extraction. Easy to add - modify `extract_drugs.py` if needed.

**Q: How many drugs are in the database?**
A: Run `analyzer.count_total_drugs()` to find out (takes ~1-2 minutes).

**Q: Which fields should I use for semantic search?**
A: Start with: `name`, `description`, `indication`, `mechanism_of_action`, `synonyms`. Add `targets` and `pathways` for relationship data.

**Q: Can I keep this in memory?**
A: For full database - unlikely. Better to extract to JSON and work with that, or stream-process as shown.

---

## 📞 Using the Analyzer

```python
from draft import DrugBankAnalyzer

# Initialize
analyzer = DrugBankAnalyzer("full database.xml")

# Print structure summary
analyzer.print_structure_summary()

# Get a specific drug
drug_0 = analyzer.get_single_drug(0)
drug_10 = analyzer.get_single_drug(10)

# Get key fields
key_fields = analyzer.extract_key_fields(0)

# Count (slow!)
total = analyzer.count_total_drugs()

# Get full analysis
analysis = analyzer.analyze_structure(sample_size=20)
```

---

Good luck with your semantic drug search engine! 🧪✨
