"""CSV export functionality for OCR results."""

import csv
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export OCR extracted data to CSV format."""
    
    def __init__(self):
        """Initialize CSV exporter."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def export_single_result(
        self,
        extracted_data: Dict[str, Any],
        output_file: str
    ) -> str:
        """
        Export a single OCR result to CSV.
        
        Args:
            extracted_data: Dictionary with extracted pharmaceutical data
            output_file: Path to output CSV file
            
        Returns:
            Path to saved CSV file
        """
        try:
            # Flatten nested structures for CSV
            flat_data = self._flatten_data(extracted_data)
            
            # Write to CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=flat_data.keys())
                writer.writeheader()
                writer.writerow(flat_data)
            
            self.logger.info(f"Exported data to {output_file}")
            return output_file
        
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def export_multiple_results(
        self,
        results_list: List[Dict[str, Any]],
        output_file: str
    ) -> str:
        """
        Export multiple OCR results to CSV.
        
        Args:
            results_list: List of extracted data dictionaries
            output_file: Path to output CSV file
            
        Returns:
            Path to saved CSV file
        """
        try:
            if not results_list:
                self.logger.warning("No results to export")
                return output_file
            
            # Flatten all results
            flat_results = [self._flatten_data(result) for result in results_list]
            
            # Get all unique fieldnames from all results
            fieldnames = set()
            for flat_result in flat_results:
                fieldnames.update(flat_result.keys())
            fieldnames = sorted(list(fieldnames))
            
            # Write to CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flat_results)
            
            self.logger.info(f"Exported {len(results_list)} results to {output_file}")
            return output_file
        
        except Exception as e:
            self.logger.error(f"Error exporting multiple results to CSV: {e}")
            raise
    
    def _flatten_data(self, data: Dict[str, Any], parent_key: str = '') -> Dict[str, str]:
        """
        Flatten nested dictionaries and lists for CSV export.
        
        Args:
            data: Nested dictionary structure
            parent_key: Parent key for nested items
            
        Returns:
            Flattened dictionary
        """
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}_{key}" if parent_key else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                items.extend(self._flatten_data(value, new_key).items())
            elif isinstance(value, list):
                # Join list items with semicolon
                if value:
                    # If list contains dicts, convert to JSON
                    if isinstance(value[0], dict):
                        items.append((new_key, json.dumps(value)))
                    else:
                        items.append((new_key, "; ".join(str(item) for item in value)))
                else:
                    items.append((new_key, ""))
            else:
                # Convert value to string
                items.append((new_key, str(value) if value is not None else ""))
        
        return dict(items)
    
    def export_detailed(
        self,
        extracted_data: Dict[str, Any],
        output_file: str
    ) -> str:
        """
        Export with detailed field breakdown (one field per row).
        
        Args:
            extracted_data: Dictionary with extracted data
            output_file: Path to output CSV file
            
        Returns:
            Path to saved CSV file
        """
        try:
            rows = []
            
            # Add basic info
            medicine_names = extracted_data.get("extracted_fields", {}).get("medicine_names", [])
            for name in medicine_names:
                rows.append({
                    "Field Type": "Medicine Name",
                    "Value": name,
                    "Confidence": extracted_data.get("ocr_confidence", ""),
                    "Source": extracted_data.get("metadata", {}).get("source_file", "")
                })
            
            # Add prescription info
            prescription_info = extracted_data.get("extracted_fields", {}).get("prescription_info")
            if prescription_info:
                rows.append({
                    "Field Type": "Prescription Info",
                    "Value": prescription_info,
                    "Confidence": extracted_data.get("ocr_confidence", ""),
                    "Source": extracted_data.get("metadata", {}).get("source_file", "")
                })
            
            # Add other extracted fields
            extracted_fields = extracted_data.get("extracted_fields", {})
            for field_key, field_value in extracted_fields.items():
                if field_key not in ["medicine_names", "prescription_info"]:
                    if isinstance(field_value, list):
                        for item in field_value:
                            rows.append({
                                "Field Type": field_key,
                                "Value": str(item),
                                "Confidence": extracted_data.get("ocr_confidence", ""),
                                "Source": extracted_data.get("metadata", {}).get("source_file", "")
                            })
                    else:
                        rows.append({
                            "Field Type": field_key,
                            "Value": str(field_value),
                            "Confidence": extracted_data.get("ocr_confidence", ""),
                            "Source": extracted_data.get("metadata", {}).get("source_file", "")
                        })
            
            # Write to CSV
            if rows:
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=["Field Type", "Value", "Confidence", "Source"])
                    writer.writeheader()
                    writer.writerows(rows)
                
                self.logger.info(f"Exported detailed data to {output_file}")
            
            return output_file
        
        except Exception as e:
            self.logger.error(f"Error exporting detailed data to CSV: {e}")
            raise
