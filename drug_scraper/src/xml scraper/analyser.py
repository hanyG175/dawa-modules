"""DrugBank XML structure analyzer - helps understand the 1.8GB dataset."""

import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set


class DrugBankAnalyzer:
    """Analyzes DrugBank XML structure without loading entire file into memory."""
    
    def __init__(self, xml_file_path: str):
        """
        Initialize analyzer with path to DrugBank XML file.
        
        Args:
            xml_file_path: Path to the full database.xml file
        """
        self.xml_file = Path(xml_file_path)
        self.namespace = "{http://www.drugbank.ca}"
        
        if not self.xml_file.exists():
            raise FileNotFoundError(f"XML file not found: {xml_file_path}")
        
        print(f"✓ Found XML file: {self.xml_file.name} ({self.xml_file.stat().st_size / 1e9:.2f} GB)")
    
    def analyze_structure(self, sample_size: int = 10) -> Dict[str, Any]:
        """
        Analyze XML structure by reading first N drugs.
        Uses iterparse to efficiently stream data without loading entire file.
        
        Args:
            sample_size: Number of drugs to analyze (default: 10)
            
        Returns:
            Dictionary with structure analysis
        """
        print(f"\n📊 Analyzing first {sample_size} drugs...")
        
        drug_count = 0
        field_names: Set[str] = set()
        field_frequency = Counter()
        field_types = defaultdict(set)
        nested_structures = defaultdict(set)
        
        # Use iterparse to stream through XML without loading it all
        try:
            context = ET.iterparse(str(self.xml_file), events=('end',))
            
            for event, elem in context:
                # Only process drug elements
                if elem.tag == f"{self.namespace}drug":
                    drug_count += 1
                    
                    # Analyze this drug's structure
                    for child in elem.iter():
                        # Remove namespace for cleaner output
                        tag = child.tag.replace(self.namespace, "")
                        
                        if tag != "drug":
                            field_names.add(tag)
                            field_frequency[tag] += 1
                            
                            # Track if field has children (nested structure)
                            if len(child) > 0:
                                nested_structures[tag].add(len(child))
                            
                            # Track what kind of content it has
                            if child.text and child.text.strip():
                                field_types[tag].add("text")
                            if len(child) > 0:
                                field_types[tag].add("nested")
                            if child.attrib:
                                field_types[tag].add("attributes")
                    
                    # Clear element to free memory
                    elem.clear()
                    
                    if drug_count >= sample_size:
                        break
        
        except Exception as e:
            print(f"❌ Error parsing XML: {e}")
            return {}
        
        return {
            "drugs_analyzed": drug_count,
            "total_unique_fields": len(field_names),
            "field_names": sorted(field_names),
            "field_frequency": dict(field_frequency),
            "field_types": {k: list(v) for k, v in field_types.items()},
            "nested_structures": dict(nested_structures)
        }
    
    def get_single_drug(self, index: int = 0) -> Dict[str, Any]:
        """
        Extract and pretty-print a single drug entry.
        
        Args:
            index: Which drug to extract (0-based)
            
        Returns:
            Dictionary representation of the drug
        """
        print(f"\n🔍 Extracting drug #{index}...")
        
        drug_count = 0
        
        try:
            context = ET.iterparse(str(self.xml_file), events=('end',))
            
            for event, elem in context:
                if elem.tag == f"{self.namespace}drug":
                    if drug_count == index:
                        drug_data = self._parse_drug_element(elem)
                        return drug_data
                    
                    drug_count += 1
                    elem.clear()
            
            print(f"❌ Drug at index {index} not found")
            return {}
        
        except Exception as e:
            print(f"❌ Error extracting drug: {e}")
            return {}
    
    def _parse_drug_element(self, drug_elem) -> Dict[str, Any]:
        """Convert a drug XML element to a dictionary."""
        drug_dict = {}
        
        # Get attributes
        drug_dict["_attributes"] = dict(drug_elem.attrib)
        
        # Parse all child elements
        for child in drug_elem:
            tag = child.tag.replace(self.namespace, "")
            
            if len(child) == 0:
                # Leaf node - just text content
                drug_dict[tag] = child.text if child.text else None
            else:
                # Has nested children
                if tag not in drug_dict:
                    drug_dict[tag] = []
                
                item = {child.tag.replace(self.namespace, ""): []}
                for subchild in child:
                    subtag = subchild.tag.replace(self.namespace, "")
                    item[subtag] = subchild.text if subchild.text else None
                
                drug_dict[tag].append(item)
        
        return drug_dict
    
    def count_total_drugs(self) -> int:
        """Count total number of drugs in the database (slow)."""
        print("\n⏳ Counting total drugs (this may take a minute)...")
        
        count = 0
        try:
            context = ET.iterparse(str(self.xml_file), events=('end',))
            
            for event, elem in context:
                if elem.tag == f"{self.namespace}drug":
                    count += 1
                    if count % 5000 == 0:
                        print(f"   ... {count} drugs processed")
                    elem.clear()
        
        except Exception as e:
            print(f"❌ Error counting: {e}")
        
        return count
    
    def print_structure_summary(self):
        """Print a nice summary of the database structure."""
        analysis = self.analyze_structure(sample_size=5)
        
        if not analysis:
            return
        
        print("\n" + "="*60)
        print("📋 DRUGBANK XML STRUCTURE SUMMARY")
        print("="*60)
        print(f"\nDrugs Analyzed: {analysis['drugs_analyzed']}")
        print(f"Unique Fields Found: {analysis['total_unique_fields']}")
        
        print("\n🏷️  MAIN FIELDS (in order):")
        for i, field in enumerate(analysis['field_names'][:20], 1):
            freq = analysis['field_frequency'].get(field, 0)
            types = analysis['field_types'].get(field, [])
            type_str = ", ".join(types)
            print(f"   {i:2d}. {field:35s} [{type_str}]")
        
        if len(analysis['field_names']) > 20:
            print(f"   ... and {len(analysis['field_names']) - 20} more fields")
        
        print("\n🔗 IMPORTANT NESTED STRUCTURES:")
        nested = analysis['nested_structures']
        if nested:
            for field in ['targets', 'enzymes', 'carriers', 'transporters', 
                         'pathways', 'products', 'drug-interactions', 'dosages']:
                if field in nested:
                    print(f"   • {field}: contains lists of sub-items")
        
        print("\n" + "="*60)
    
    def extract_key_fields(self, drug_index: int = 0) -> Dict[str, Any]:
        """
        Extract most important fields from a drug for quick understanding.
        
        Args:
            drug_index: Which drug to extract
            
        Returns:
            Dictionary with key fields
        """
        drug = self.get_single_drug(drug_index)
        
        if not drug:
            return {}
        
        # Key fields we care about for semantic search
        key_fields = {
            'drugbank_id': drug.get('drugbank-id'),
            'name': drug.get('name'),
            'description': drug.get('description'),
            'indication': drug.get('indication'),
            'mechanism_of_action': drug.get('mechanism-of-action'),
            'groups': drug.get('groups'),
            'synonyms': drug.get('synonyms'),
            'cas_number': drug.get('cas-number'),
            'type': drug.get('_attributes', {}).get('type'),
        }
        
        return {k: v for k, v in key_fields.items() if v}


# ============================================================================
# USAGE EXAMPLE - Run this to understand your DrugBank file!
# ============================================================================

def demo_parser():
    """Demonstrates how to extract specific drug fields."""
    
    print("\n" + "="*60)
    print("🎓 HOW TO USE THE ANALYZER")
    print("="*60)
    
    xml_path = "full database.xml"
    analyzer = DrugBankAnalyzer(xml_path)
    
    # Example 1: Get structure summary
    print("\n1️⃣ Get structure overview:")
    analyzer.print_structure_summary()
    
    # Example 2: Extract a specific drug
    print("\n2️⃣ Extract a specific drug (e.g., drug #0):")
    drug = analyzer.get_single_drug(0)
    print("   # Returns complete dict with all fields")
    
    # Example 3: Count drugs
    print("\n3️⃣ Count total drugs in database:")
    total = analyzer.count_total_drugs()
    
    # Example 4: Get key fields
    print("\n4️⃣ Get key fields for semantic search:")
    print("   key_fields = analyzer.extract_key_fields(0)")
    
    print("\n" + "="*60)
    print("📚 KEY FIELDS FOR SEMANTIC SEARCH")
    print("="*60)
    
    fields_info = {
        "name": "Drug name (e.g., 'Aspirin')",
        "description": "Detailed description of drug",
        "indication": "Medical uses/indications",
        "mechanism_of_action": "How the drug works",
        "synonyms": "Alternative names",
        "groups": "Classification (approved, experimental, etc)",
        "targets": "Protein targets it interacts with",
        "pathways": "Metabolic/biological pathways",
        "drug_interactions": "Interactions with other drugs",
        "dosages": "Recommended dosages and forms",
        "pharmacodynamics": "Effects on the body",
        "pharmacokinetics": "How body processes the drug",
    }
    
    for field, desc in fields_info.items():
        print(f"   • {field:25s} : {desc}")


if __name__ == "__main__":
    xml_path = "full database.xml"
    
    try:
        analyzer = DrugBankAnalyzer(xml_path)
        
        # Get structure summary
        analyzer.print_structure_summary()
        
        # Show example usage
        demo_parser()
        
    except Exception as e:
        print(f"❌ Error: {e}")
