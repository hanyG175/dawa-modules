"""Data extraction and formatting for OCR results."""

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .interfaces import OCRResult, ExtractedData

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Extracts and formats structured data from OCR results.
    Focuses on identifying medicine names and prescription information.
    """
    
    def __init__(self):
        """Initialize data extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Common medical keywords for identifying prescription sections
        self.prescription_keywords = {
            "rx", "prescription", "prescrit", "dosage", "dose", "mg", "ml",
            "comprimés", "tablets", "capsules", "injection", "inhalation",
            "posologie", "posology", "administration", "usage", "application"
        }
        
        # Keywords for identifying medicine name sections
        self.medicine_keywords = {
            "medicine", "drug", "medicament", "médicament", "active substance",
            "substance active", "brand name", "nom commercial", "product"
        }
    
    def extract_from_ocr_result(
        self,
        ocr_result: OCRResult,
        source_file: Optional[str] = None
    ) -> ExtractedData:
        """
        Extract structured data from OCR result.
        
        Args:
            ocr_result: OCRResult object from OCR engine
            source_file: Optional source file path
            
        Returns:
            ExtractedData object with structured information
        """
        raw_text = ocr_result.raw_text
        
        # Extract medicine names using pattern matching
        medicine_names = self._extract_medicine_names(raw_text)
        
        # Extract prescription information
        prescription_info = self._extract_prescription_info(raw_text)
        
        # Extract other fields
        extracted_fields = self._extract_fields(raw_text)
        
        # Build metadata
        metadata = {
            "source_type": ocr_result.source_type,
            "ocr_confidence": ocr_result.confidence,
            "source_file": source_file,
            "extraction_method": "regex_pattern_matching"
        }
        metadata.update(ocr_result.metadata)
        
        return ExtractedData(
            medicine_names=medicine_names,
            prescription_info=prescription_info,
            raw_text=raw_text,
            extracted_fields=extracted_fields,
            metadata=metadata
        )
    
    def _extract_medicine_names(self, text: str) -> List[str]:
        """
        Extract potential medicine names from text.
        Uses heuristics: capitalized words, common patterns.
        
        Args:
            text: Raw OCR text
            
        Returns:
            List of potential medicine names
        """
        medicine_names = []
        
        # Pattern 1: Words that appear after medicine-related keywords
        pattern1 = r'(?:medicine|medicament|drug|product|brand|substance)[:\s]+([A-Z][a-zA-Z0-9\s\-]*)'
        matches1 = re.findall(pattern1, text, re.IGNORECASE)
        medicine_names.extend(matches1)
        
        # Pattern 2: Lines that start with capital letters (likely names)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Check if line matches typical medicine name format
            if line and line[0].isupper() and len(line) > 2 and len(line) < 100:
                # Avoid lines that look like regular sentences
                if not re.match(r'^[A-Z][a-z]+ [a-z]+ .*', line):
                    medicine_names.append(line)
        
        # Remove duplicates and short entries
        medicine_names = list(set(medicine_names))
        medicine_names = [
            name.strip() for name in medicine_names
            if len(name.strip()) > 2 and len(name.strip()) < 100
        ]
        
        self.logger.debug(f"Extracted {len(medicine_names)} potential medicine names")
        return medicine_names
    
    def _extract_prescription_info(self, text: str) -> Optional[str]:
        """
        Extract prescription/dosage information.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Prescription information text or None
        """
        # Look for dosage patterns
        dosage_pattern = r'(\d+\s*(?:mg|ml|g|ug|%|unit)(?:\s*/\s*\d+\s*(?:mg|ml|g|ug|%|unit))?)'
        dosages = re.findall(dosage_pattern, text, re.IGNORECASE)
        
        # Look for administration patterns
        admin_pattern = r'(?:administration|usage|take|prendre|utilisation)[:\s]+([^\n]+)'
        admin_info = re.findall(admin_pattern, text, re.IGNORECASE)
        
        # Look for posology patterns
        posology_pattern = r'(?:posologie|posology|dosage)[:\s]+([^\n]+)'
        posology_info = re.findall(posology_pattern, text, re.IGNORECASE)
        
        # Combine information
        info_parts = []
        if dosages:
            info_parts.append(f"Dosage: {', '.join(set(dosages))}")
        if admin_info:
            info_parts.append(f"Administration: {admin_info[0]}")
        if posology_info:
            info_parts.append(f"Posology: {posology_info[0]}")
        
        if info_parts:
            prescription_info = " | ".join(info_parts)
            self.logger.debug(f"Extracted prescription info: {prescription_info}")
            return prescription_info
        
        return None
    
    def _extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract structured fields from text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Dictionary of extracted fields
        """
        fields = {}
        
        # Active ingredient
        active_pattern = r'(?:active\s+(?:ingredient|substance)|substance\s+active)[:\s]+([^\n]+)'
        active_match = re.search(active_pattern, text, re.IGNORECASE)
        if active_match:
            fields["active_ingredient"] = active_match.group(1).strip()
        
        # Manufacturer/Laboratory
        lab_pattern = r'(?:manufacturer|fabricant|laboratory|laboratoire)[:\s]+([^\n]+)'
        lab_match = re.search(lab_pattern, text, re.IGNORECASE)
        if lab_match:
            fields["manufacturer"] = lab_match.group(1).strip()
        
        # Indications
        indication_pattern = r'(?:indications|indication|used\s+for)[:\s]+([^\n]+)'
        indication_matches = re.findall(indication_pattern, text, re.IGNORECASE)
        if indication_matches:
            fields["indications"] = indication_matches
        
        # Contraindications
        contra_pattern = r'(?:contraindications|contra-indication)[:\s]+([^\n]+)'
        contra_matches = re.findall(contra_pattern, text, re.IGNORECASE)
        if contra_matches:
            fields["contraindications"] = contra_matches
        
        # Side effects
        side_pattern = r'(?:side\s+effects|side\s+effect|adverse\s+effects|effets\s+secondaires)[:\s]+([^\n]+)'
        side_matches = re.findall(side_pattern, text, re.IGNORECASE)
        if side_matches:
            fields["side_effects"] = side_matches
        
        # Storage information
        storage_pattern = r'(?:storage|store|conservation)[:\s]+([^\n]+)'
        storage_match = re.search(storage_pattern, text, re.IGNORECASE)
        if storage_match:
            fields["storage"] = storage_match.group(1).strip()
        
        self.logger.debug(f"Extracted {len(fields)} structured fields")
        return fields
    
    def format_for_cleaner(self, extracted_data: ExtractedData) -> Dict[str, Any]:
        """
        Format extracted data for the cleaning/validation module.
        Standardizes format for downstream processing.
        
        Args:
            extracted_data: ExtractedData object
            
        Returns:
            Dictionary formatted for cleaner module
        """
        return {
            "raw_text": extracted_data.raw_text,
            "extracted_fields": {
                "medicine_names": extracted_data.medicine_names,
                "prescription_info": extracted_data.prescription_info,
                **extracted_data.extracted_fields
            },
            "metadata": extracted_data.metadata,
            "ocr_confidence": extracted_data.metadata.get("ocr_confidence", 0.0)
        }
    
    def format_for_search(self, extracted_data: ExtractedData) -> Dict[str, str]:
        """
        Format extracted data as search queries.
        Prepares data for search engine module.
        
        Args:
            extracted_data: ExtractedData object
            
        Returns:
            Dictionary with search queries
        """
        queries = {
            "medicine_names": extracted_data.medicine_names,
            "primary_query": " ".join(extracted_data.medicine_names[:1]) if extracted_data.medicine_names else "",
            "alternative_queries": extracted_data.medicine_names[1:] if len(extracted_data.medicine_names) > 1 else [],
            "prescription_query": extracted_data.prescription_info or "",
            "full_text": extracted_data.raw_text
        }
        
        return {
            k: v for k, v in queries.items()
            if v and (isinstance(v, str) and v.strip() or isinstance(v, list) and v)
        }
