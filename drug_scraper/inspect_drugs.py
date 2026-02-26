"""
Quick inspector to look at actual drug data from the XML.
Shows you exactly what fields are populated for real drugs.
"""

import json

from draft import DrugBankAnalyzer


def inspect_drug(index: int = 0):
    """Show detailed view of a single drug."""
    
    analyzer = DrugBankAnalyzer("full database.xml")
    drug = analyzer.get_single_drug(index)
    
    if not drug:
        print(f"❌ Could not find drug at index {index}")
        return
    
    print(f"\n{'='*70}")
    print(f"🔍 DRUG #{index} DETAILED VIEW")
    print(f"{'='*70}")
    
    # Group fields by type
    text_fields = ['drugbank_id', 'name', 'description', 'type', 'cas_number',
                   'indication', 'mechanism_of_action', 'pharmacodynamics',
                   'pharmacokinetics', 'metabolism', 'absorption', 'toxicity',
                   'half_life', 'protein_binding']
    
    list_fields = ['groups', 'synonyms']
    
    count_fields = ['num_targets', 'num_enzymes', 'num_interactions', 'num_pathways']
    
    # Print text fields
    print("\n📝 TEXT FIELDS:")
    print("-" * 70)
    for field in text_fields:
        value = drug.get(field)
        if value:
            # Truncate long values
            preview = str(value)[:150]
            if len(str(value)) > 150:
                preview += "..."
            print(f"  {field:25s}: {preview}")
    
    # Print list fields
    print("\n📋 LIST FIELDS:")
    print("-" * 70)
    for field in list_fields:
        value = drug.get(field)
        if value:
            if len(value) <= 3:
                print(f"  {field:25s}: {value}")
            else:
                print(f"  {field:25s}: {value[:3]} ... ({len(value)} total)")
    
    # Print counts
    print("\n🔗 INTERACTION COUNTS:")
    print("-" * 70)
    for field in count_fields:
        value = drug.get(field, 0)
        icon = "✓" if value > 0 else "○"
        print(f"  {icon} {field:23s}: {value}")
    
    print(f"\n{'='*70}\n")


def compare_drugs(index1: int = 0, index2: int = 1):
    """Compare two drugs side-by-side."""
    
    analyzer = DrugBankAnalyzer("full database.xml")
    drug1 = analyzer.get_single_drug(index1)
    drug2 = analyzer.get_single_drug(index2)
    
    print(f"\n{'='*80}")
    print(f"⚖️  COMPARING DRUG #{index1} vs DRUG #{index2}")
    print(f"{'='*80}")
    
    fields = ['name', 'type', 'indication', 'mechanism_of_action',
              'num_targets', 'num_interactions', 'num_pathways']
    
    print(f"\n{'Field':<30} {'Drug #' + str(index1):<25} {'Drug #' + str(index2):<25}")
    print("-" * 80)
    
    for field in fields:
        v1 = str(drug1.get(field, 'N/A'))[:22]
        v2 = str(drug2.get(field, 'N/A'))[:22]
        print(f"{field:<30} {v1:<25} {v2:<25}")
    
    print(f"\n{'='*80}\n")


def find_drugs_with_field(field_name: str = 'indication', min_count: int = 0):
    """Find first N drugs that have a specific populated field."""
    
    analyzer = DrugBankAnalyzer("full database.xml")
    
    print(f"\n🔍 Finding drugs with '{field_name}' field...")
    
    found = 0
    for i in range(20):  # Check first 20 drugs
        drug = analyzer.get_single_drug(i)
        
        if field_name in drug and drug[field_name]:
            value = drug[field_name]
            
            # Handle different types
            if isinstance(value, list):
                if len(value) > min_count:
                    found += 1
                    preview = f"{len(value)} items: {value[:2]}"
            else:
                preview = str(value)[:60]
            
            print(f"\n  Drug #{i}: {drug.get('name', 'Unknown')}")
            print(f"    {field_name}: {preview}...")
            
            if found >= 3:
                break
    
    if found == 0:
        print(f"  ❌ No drugs found with '{field_name}' in first 20")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔬 DRUGBANK INSPECTOR - Explore Real Drug Data")
    print("="*70)
    
    # Show a few example drugs
    print("\n1️⃣  Inspecting first drug (Calcium):")
    inspect_drug(0)
    
    print("\n2️⃣  Inspecting 4th drug (Lepirudin - has more data):")
    inspect_drug(3)
    
    print("\n3️⃣  Comparing drugs:")
    compare_drugs(0, 3)
    
    print("\n4️⃣  Finding drugs with clinical information:")
    find_drugs_with_field('indication')
    
    print("\n5️⃣  Finding drugs with drug interactions:")
    find_drugs_with_field('num_interactions', min_count=10)
    
    print("\n" + "="*70)
    print("✨ Done! Now you understand what data is available.")
    print("="*70)
