"""PDF document processor for converting PDFs to processable images."""

import io
import logging
from pathlib import Path
from typing import List, Optional
from PIL import Image
import fitz  # PyMuPDF

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
            
            # Open PDF with PyMuPDF (fitz)
            pdf_document = fitz.open(file_path)
            images = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Render page to image with DPI
                zoom = self.dpi / 72.0  # 72 DPI is default
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            
            pdf_document.close()
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
            pdf_document = fitz.open(file_path)
            page_count = len(pdf_document)
            pdf_document.close()
            return page_count
        except Exception as e:
            self.logger.error(f"Error getting page count: {str(e)}")
            return 0
