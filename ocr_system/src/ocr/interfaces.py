"""
Abstract interfaces for OCR pipeline integration with external modules.
These interfaces allow loose coupling with cleaning/validation and search modules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class OCRResult:
    """Result from OCR processing."""
    
    raw_text: str
    confidence: float
    source_type: str  # "pdf" or "image"
    metadata: Dict[str, Any]
    

@dataclass
class ExtractedData:
    """Extracted and formatted data ready for downstream processing."""
    
    medicine_names: List[str]
    prescription_info: Optional[str]
    raw_text: str
    extracted_fields: Dict[str, Any]
    metadata: Dict[str, Any]


class DataCleanerInterface(ABC):
    """
    Interface for data cleaning and validation module.
    To be implemented by the external cleaning/validation module.
    """
    
    @abstractmethod
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        """
        Clean and structure extracted data.
        
        Args:
            data: Extracted data from OCR
            
        Returns:
            Cleaned and structured data dictionary
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate cleaned data.
        
        Args:
            data: Cleaned data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        pass


class SearchEngineInterface(ABC):
    """
    Interface for search engine module.
    To be implemented by the external search engine module.
    """
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for drugs by extracted text.
        
        Args:
            query: Medicine name or prescription text
            
        Returns:
            List of matching drug records
        """
        pass
    
    @abstractmethod
    def search_by_medicine_name(self, medicine_name: str) -> List[Dict[str, Any]]:
        """
        Search specifically by medicine name.
        
        Args:
            medicine_name: Name of medicine to search
            
        Returns:
            List of matching drug records
        """
        pass


class OCRPipeline(ABC):
    """
    Main OCR processing pipeline.
    Coordinates between document processing, OCR, data extraction,
    and integration with external modules.
    """
    
    @abstractmethod
    def process_pdf(self, pdf_path: str) -> List[ExtractedData]:
        """
        Process PDF document through OCR pipeline.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of extracted data from all pages
        """
        pass
    
    @abstractmethod
    def process_image(self, image_path: str) -> ExtractedData:
        """
        Process image (scan/photo) through OCR pipeline.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted data from image
        """
        pass
    
    @abstractmethod
    def register_data_cleaner(self, cleaner: DataCleanerInterface) -> None:
        """
        Register external data cleaning module.
        
        Args:
            cleaner: Implementation of DataCleanerInterface
        """
        pass
    
    @abstractmethod
    def register_search_engine(self, engine: SearchEngineInterface) -> None:
        """
        Register external search engine module.
        
        Args:
            engine: Implementation of SearchEngineInterface
        """
        pass
