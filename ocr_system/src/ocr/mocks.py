"""Mock implementations for testing and demo purposes."""

from .interfaces import DataCleanerInterface, SearchEngineInterface, ExtractedData
from typing import Dict, List, Any, Optional


class MockDataCleaner(DataCleanerInterface):
    """Mock data cleaner for testing."""
    
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        """Return data as-is (mock implementation)."""
        return {
            "medicine_names": data.medicine_names,
            "prescription_info": data.prescription_info,
            "raw_text": data.raw_text,
            "extracted_fields": data.extracted_fields,
            "metadata": data.metadata,
        }


class MockSearchEngine(SearchEngineInterface):
    """Mock search engine for testing."""
    
    def search(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Return empty results (mock implementation)."""
        return []
