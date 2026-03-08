"""
Placeholder implementations and mock modules for development and testing.
These demonstrate how to integrate with the OCR system.
"""

import logging
from typing import Dict, List, Any

from .interfaces import DataCleanerInterface, SearchEngineInterface, ExtractedData

logger = logging.getLogger(__name__)


class MockDataCleaner(DataCleanerInterface):
    """
    Mock implementation of data cleaner.
    Replace with actual cleaner when module is ready.
    """
    
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        """
        Mock cleaning implementation.
        
        Args:
            data: Extracted data from OCR
            
        Returns:
            Cleaned data dictionary
        """
        logger.info("MockDataCleaner.clean() called - use real cleaner in production")
        
        return {
            "status": "mock",
            "medicine_names": data.medicine_names,
            "prescription_info": data.prescription_info,
            "fields": data.extracted_fields,
            "ocr_confidence": data.metadata.get("ocr_confidence", 0.0),
            "note": "This is mock data - integrate real cleaner for production"
        }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Mock validation implementation.
        
        Args:
            data: Cleaned data dictionary
            
        Returns:
            Always True for mock
        """
        logger.info("MockDataCleaner.validate() called - use real cleaner in production")
        return True


class MockSearchEngine(SearchEngineInterface):
    """
    Mock implementation of search engine.
    Replace with actual search engine when module is ready.
    """
    
    # Simulated drug database
    MOCK_DRUGS = {
        "aspirin": [
            {
                "id": "DRUG_001",
                "name": "Aspirin",
                "active_ingredient": "Acetylsalicylic acid",
                "dosage": ["500mg", "1000mg"],
                "manufacturer": "MockPharma",
                "indication": "Pain relief, anti-inflammatory",
                "confidence": 0.95
            }
        ],
        "ibuprofen": [
            {
                "id": "DRUG_002",
                "name": "Ibuprofen",
                "active_ingredient": "Ibuprofen",
                "dosage": ["200mg", "400mg", "600mg"],
                "manufacturer": "MockPharma",
                "indication": "Pain relief, fever reduction",
                "confidence": 0.92
            }
        ],
        "paracetamol": [
            {
                "id": "DRUG_003",
                "name": "Paracetamol",
                "active_ingredient": "Acetaminophen",
                "dosage": ["500mg", "1000mg"],
                "manufacturer": "MockPharma",
                "indication": "Fever reduction, pain relief",
                "confidence": 0.94
            }
        ]
    }
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Mock search implementation.
        Performs simple keyword matching on mock database.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching mock drug results
        """
        logger.info(f"MockSearchEngine.search() called with query: {query}")
        
        query_lower = query.lower().strip()
        results = []
        
        for drug_name, drug_list in self.MOCK_DRUGS.items():
            if query_lower in drug_name or drug_name in query_lower:
                results.extend(drug_list)
        
        if not results:
            logger.warning(f"No mock results found for query: {query}")
        
        return results
    
    def search_by_medicine_name(self, medicine_name: str) -> List[Dict[str, Any]]:
        """
        Mock search by medicine name.
        
        Args:
            medicine_name: Name of medicine to search
            
        Returns:
            List of matching mock drug results
        """
        logger.info(f"MockSearchEngine.search_by_medicine_name() called with: {medicine_name}")
        
        medicine_lower = medicine_name.lower().strip()
        results = []
        
        for drug_name, drug_list in self.MOCK_DRUGS.items():
            if medicine_lower in drug_name or drug_name in medicine_lower:
                results.extend(drug_list)
        
        return results
