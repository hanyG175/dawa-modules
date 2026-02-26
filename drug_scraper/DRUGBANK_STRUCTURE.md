# DrugBank XML Database Structure Guide

## Overview
- **File Size:** 1.90 GB
- **Format:** XML with namespace `http://www.drugbank.ca`
- **Structure:** Single root element `<drugbank>` containing multiple `<drug>` elements
- **Total Fields Per Drug:** 143 unique fields

## How the XSD Works

The `drugbank.xsd` file defines the XML schema. Key points:

1. **Root Element:** `<drugbank>` with attributes:
   - `version`: DrugBank version
   - `exported-on`: Export date

2. **Drug Element:** Each `<drug>` contains:
   - `type`: "small molecule" or "biotech"
   - `created`: Date created
   - `updated`: Last update date

## Main Drug Fields (143 total)

### Basic Information
```xml
<name>Aspirin</name>
<cas-number>50-78-2</cas-number>
<drugbank-id primary="true">DB00945</drugbank-id>
<description>Nonsteroidal anti-inflammatory agent...</description>
<type>small molecule</type>
```

### Classification & Grouping
```xml
<groups>
  <group>approved</group>
  <group>vet_approved</group>
</groups>

<synonyms>
  <synonym language="English">Acetylsalicylic Acid</synonym>
  <synonym>ASA</synonym>
</synonyms>

<categories>
  <category>
    <category>Anti-Inflammatory Agents</category>
    <mesh-id>D000894</mesh-id>
  </category>
</categories>
```

### Chemical Properties
```xml
<state>solid</state>
<average-mass>180.157</average-mass>
<monoisotopic-mass>180.042259</monoisotopic-mass>

<calculated-properties>
  <property>
    <kind>Molecular Formula</kind>
    <value>C9H8O4</value>
    <source>ChemAxon</source>
  </property>
</calculated-properties>
```

### Medical Information
```xml
<indication>For relief of headache, muscular aches...</indication>
<mechanism-of-action>Inhibits prostaglandin synthesis...</mechanism-of-action>
<pharmacodynamics>Reduces inflammation and pain...</pharmacodynamics>
<pharmacokinetics>Rapidly absorbed from GI tract...</pharmacokinetics>
<metabolism>Undergoes hydrolysis...</metabolism>
<toxicity>Overdose can cause...</toxicity>
```

### Interactions & Targets (IMPORTANT for semantic search)
```xml
<targets>
  <target position="1">
    <id>BE0000048</id>
    <name>Cyclooxygenase</name>
    <organism>Humans</organism>
    <actions>
      <action>Inhibitor</action>
    </actions>
    <known-action>yes</known-action>
  </target>
</targets>

<enzymes>
  <enzyme>
    <id>BE0001156</id>
    <name>Cytochrome P450 2C19</name>
  </enzyme>
</enzymes>

<drug-interactions>
  <drug-interaction>
    <drugbank-id>DB00564</drugbank-id>
    <name>Ibuprofen</name>
    <description>Risk of GI ulceration...</description>
  </drug-interaction>
</drug-interactions>
```

### Products & Dosages
```xml
<products>
  <product>
    <name>Aspirin</name>
    <labeller>Bayer</labeller>
    <ndc-id>0031-2107</ndc-id>
    <dosage-form>Tablet</dosage-form>
    <strength>325 mg</strength>
    <route>Oral</route>
    <approved>true</approved>
  </product>
</products>

<dosages>
  <dosage>
    <form>Tablet</form>
    <route>Oral</route>
    <strength>325 mg</strength>
  </dosage>
</dosages>
```

### Pathways
```xml
<pathways>
  <pathway>
    <smpdb-id>SMP0000107</smpdb-id>
    <name>Arachidonic Acid Metabolism</name>
    <category>Drug Metabolism</category>
    <drugs>
      <drug>
        <drugbank-id>DB00945</drugbank-id>
        <name>Aspirin</name>
      </drug>
    </drugs>
  </pathway>
</pathways>
```

### External References
```xml
<external-identifiers>
  <external-identifier>
    <resource>PubChem Compound</resource>
    <identifier>2244</identifier>
  </external-identifier>
  <external-identifier>
    <resource>ChEMBL</resource>
    <identifier>CHEMBL25</identifier>
  </external-identifier>
</external-identifiers>

<general-references>
  <articles>
    <article>
      <pubmed-id>12345678</pubmed-id>
      <citation>Author et al., Journal 2023...</citation>
    </article>
  </articles>
</general-references>
```

## Important Nested Structures

| Field | Contains | Use Case |
|-------|----------|----------|
| `targets` | Protein/enzyme targets | Understanding mechanism of action |
| `enzymes` | Metabolizing enzymes | Understanding drug metabolism |
| `carriers` | Carrier proteins | Understanding transport |
| `transporters` | Transport proteins | Understanding distribution |
| `pathways` | Metabolic/biological pathways | Understanding drug pathways |
| `products` | Marketed drug products | Real-world availability |
| `drug-interactions` | Other drug interactions | Clinical safety |
| `dosages` | Dosage forms/strengths | Clinical information |
| `atc-codes` | ATC classification | Drug classification |
| `calculated-properties` | Computed molecular properties | Molecular/chemical info |

## Using the Analyzer

The `draft.py` file contains `DrugBankAnalyzer` class for efficiently reading this huge XML:

```python
from draft import DrugBankAnalyzer

# Initialize with XML path
analyzer = DrugBankAnalyzer("full database.xml")

# Get structure summary
analyzer.print_structure_summary()

# Extract a specific drug
drug = analyzer.get_single_drug(0)

# Count total drugs (slow!)
total = analyzer.count_total_drugs()

# Get key fields for semantic search
key_fields = analyzer.extract_key_fields(0)
```

## Memory-Efficient Processing

The analyzer uses `iterparse` which:
- ✅ Streams through the file without loading it all into RAM
- ✅ Clears parsed elements to free memory
- ✅ Works smoothly with 1.9GB files
- ✅ Allows sequential processing of drugs

## Key Fields for Your Semantic Search

For building your semantic drug search engine, focus on:

1. **Drug Identification**
   - `name`: Primary drug name
   - `synonyms`: Alternative names
   - `drugbank-id`: Unique identifier

2. **Clinical Information**
   - `indication`: What it's used for
   - `mechanism-of-action`: How it works
   - `description`: General information

3. **Chemical Information**
   - `calculated-properties`: SMILES, molecular formula, etc.
   - `cas-number`: Chemical identifier
   - `average-mass`: Molecular weight

4. **Relationships (for graph/semantic)**
   - `targets`: Protein targets
   - `drug-interactions`: Other drugs it interacts with
   - `pathways`: Biological pathways
   - `enzymes`: Metabolizing enzymes

5. **Metadata**
   - `groups`: Classification (approved, experimental, etc)
   - `products`: Commercial availability
   - `atc-codes`: Medical classification

## Next Steps

1. **Extract to JSON/CSV:** Use analyzer to extract drugs to structured format
2. **Build Index:** Create semantic search index on key fields
3. **Handle Relationships:** Parse targets, interactions, pathways for knowledge graph
4. **Validate Data:** Check for missing/malformed entries
5. **Optimize Storage:** Consider which fields are essential vs optional

## Common Issues & Solutions

**Problem:** File is too large to open in text editor
- **Solution:** Use the analyzer to extract specific sections

**Problem:** Don't understand nested structures
- **Solution:** Use `get_single_drug()` to see actual data

**Problem:** Want to count total drugs quickly
- **Solution:** Use `count_total_drugs()` (takes ~1-2 minutes)

**Problem:** Need specific field format
- **Solution:** Use `extract_key_fields()` or modify the parser
