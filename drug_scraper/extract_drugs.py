"""
Extract DrugBank drugs to JSON format for easier processing.

Usage:
    python extract_drugs.py --output drugs.json --limit 1000
    python extract_drugs.py --format csv --output drugs.csv
"""

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional


class DrugBankExtractor:
    """Extracts drugs from DrugBank XML to structured formats."""
    
    def __init__(self, xml_file: str):
        self.xml_file = Path(xml_file)
        self.namespace = "{http://www.drugbank.ca}"
        
        if not self.xml_file.exists():
            raise FileNotFoundError(f"XML file not found: {xml_file}")
    
    def extract_to_json(self, output_file: str, limit: Optional[int] = None) -> int:
        """
        Extract drugs to JSON format.
        
        Args:
            output_file: Output JSON file path
            limit: Maximum number of drugs to extract
            
        Returns:
            Number of drugs extracted
        """
        print(f"📤 Extracting drugs to JSON...")
        
        drugs = []
        count = 0
        
        try:
            context = ET.iterparse(str(self.xml_file), events=('end',))
            
            for event, elem in context:
                if elem.tag == f"{self.namespace}drug":
                    drug = self._extract_drug(elem)
                    drugs.append(drug)
                    count += 1
                    
                    if count % 500 == 0:
                        print(f"   ✓ Extracted {count} drugs...")
                    
                    elem.clear()
                    
                    if limit and count >= limit:
                        break
            
            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(drugs, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {count} drugs to {output_file}")
            return count
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0
    
    def extract_to_csv(self, output_file: str, limit: Optional[int] = None) -> int:
        """
        Extract drugs to CSV format with key fields.
        
        Args:
            output_file: Output CSV file path
            limit: Maximum number of drugs to extract
            
        Returns:
            Number of drugs extracted
        """
        print(f"📤 Extracting drugs to CSV...")
        
        fields = [
            'drugbank_id', 'name', 'description', 'type', 'groups',
            'indication', 'mechanism_of_action', 'cas_number'
        ]
        
        count = 0
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                
                context = ET.iterparse(str(self.xml_file), events=('end',))
                
                for event, elem in context:
                    if elem.tag == f"{self.namespace}drug":
                        drug = self._extract_drug(elem)
                        
                        # Flatten for CSV
                        row = {
                            'drugbank_id': drug.get('drugbank_id', ''),
                            'name': drug.get('name', ''),
                            'description': drug.get('description', ''),
                            'type': drug.get('type', ''),
                            'groups': '|'.join(drug.get('groups', [])),
                            'indication': drug.get('indication', ''),
                            'mechanism_of_action': drug.get('mechanism_of_action', ''),
                            'cas_number': drug.get('cas_number', ''),
                        }
                        
                        writer.writerow(row)
                        count += 1
                        
                        if count % 500 == 0:
                            print(f"   ✓ Extracted {count} drugs...")
                        
                        elem.clear()
                        
                        if limit and count >= limit:
                            break
            
            print(f"✅ Saved {count} drugs to {output_file}")
            return count
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0
    
    def _extract_drug(self, drug_elem) -> Dict[str, Any]:
        """Extract key fields from a drug element."""
        ns = self.namespace
        
        # Get attributes
        drug_type = drug_elem.get('type', '')
        
        # Get basic fields
        drug_data = {
            'drugbank_id': self._get_text(drug_elem, f'{ns}drugbank-id'),
            'name': self._get_text(drug_elem, f'{ns}name'),
            'description': self._get_text(drug_elem, f'{ns}description'),
            'type': drug_type,
            'cas_number': self._get_text(drug_elem, f'{ns}cas-number'),
        }
        
        # Get groups
        groups_elem = drug_elem.find(f'{ns}groups')
        if groups_elem is not None:
            drug_data['groups'] = [g.text for g in groups_elem.findall(f'{ns}group') if g.text]
        
        # Get medical info
        drug_data['indication'] = self._get_text(drug_elem, f'{ns}indication')
        drug_data['mechanism_of_action'] = self._get_text(drug_elem, f'{ns}mechanism-of-action')
        drug_data['pharmacodynamics'] = self._get_text(drug_elem, f'{ns}pharmacodynamics')
        drug_data['metabolism'] = self._get_text(drug_elem, f'{ns}metabolism')
        
        # Get synonyms
        synonyms_elem = drug_elem.find(f'{ns}synonyms')
        if synonyms_elem is not None:
            drug_data['synonyms'] = [s.text for s in synonyms_elem.findall(f'{ns}synonym') if s.text]
        
        # Count of interactive elements
        drug_data['num_targets'] = len(drug_elem.findall(f'{ns}targets/{ns}target'))
        drug_data['num_enzymes'] = len(drug_elem.findall(f'{ns}enzymes/{ns}enzyme'))
        drug_data['num_interactions'] = len(drug_elem.findall(f'{ns}drug-interactions/{ns}drug-interaction'))
        drug_data['num_pathways'] = len(drug_elem.findall(f'{ns}pathways/{ns}pathway'))
        
        return drug_data
    
    def _get_text(self, elem, xpath: str) -> str:
        """Get text from an element using xpath."""
        child = elem.find(xpath)
        return child.text.strip() if child is not None and child.text else ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract DrugBank drugs to structured formats")
    parser.add_argument('--xml', default='full database.xml', help='Input XML file path')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--limit', type=int, help='Maximum number of drugs to extract')
    
    args = parser.parse_args()
    
    try:
        extractor = DrugBankExtractor(args.xml)
        
        if args.format == 'json':
            count = extractor.extract_to_json(args.output, args.limit)
        else:
            count = extractor.extract_to_csv(args.output, args.limit)
        
        print(f"\n✨ Done! Extracted {count} drugs.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
