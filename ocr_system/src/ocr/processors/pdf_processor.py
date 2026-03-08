"""PDF document processor for converting PDFs to processable images."""

import logging
from pathlib import Path
from typing import List, Optional
from pdf2image import convert_from_path
from PIL import Image

from . import BaseProcessor

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    """
    Processor for PDF documents.
    Converts PDF pages to images for OCR processing.
    """
    
    SUPPORTED_FORMATS = {".pdf"}
    
    def __init__(self, dpi: int = 300):
        """
        Initialize PDF processor.
        
        Args:
            dpi: Dots per inch for PDF conversion (higher = better quality)
        """
        super().__init__(name="PDFProcessor")
        self.dpi = dpi
    
    def validate_input(self, file_path: str) -> bool:
        """
        Validate PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if valid PDF, False otherwise
        """
        if not self._validate_file_exists(file_path):
            return False
        
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            self.logger.error(f"Unsupported format: {path.suffix}. Expected .pdf")
            return False
        
        return True
    
    def process(self, file_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Image objects (one per page).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of PIL Image objects for each page
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF cannot be processed
        """
        if not self.validate_input(file_path):
            raise FileNotFoundError(f"Invalid PDF: {file_path}")
        
        try:
            self.logger.info(f"Processing PDF: {file_path} at {self.dpi} DPI")
            images = convert_from_path(file_path, dpi=self.dpi)
            self.logger.info(f"Successfully converted {len(images)} pages")
            return images
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get number of pages in PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        if not self.validate_input(file_path):
            return 0
        
        try:
            images = convert_from_path(file_path, first_page=1, last_page=1)
            # This gives us one page, but we need total count
            # For optimization, convert all and count
            images = convert_from_path(file_path)
            return len(images)
        except Exception as e:
            self.logger.error(f"Error getting page count: {str(e)}")
            return 0
