"""
Complete OCR Pipeline implementation.
Coordinates between document processing, OCR, and data extraction.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .interfaces import (
    OCRPipeline,
    OCRResult,
    ExtractedData,
    DataCleanerInterface,
    SearchEngineInterface
)
from .ocr_engine import OCREngine
from .processors.pdf_processor import PDFProcessor
from .processors.image_processor import ImageProcessor
from .data_extraction import DataExtractor

logger = logging.getLogger(__name__)


class StandardOCRPipeline(OCRPipeline):
    """
    Standard OCR pipeline implementation.
    Handles both PDF and image processing with integration points for
    external cleaning and search modules.
    """
    
    def __init__(
        self,
        ocr_engine: Optional[OCREngine] = None,
        pdf_processor: Optional[PDFProcessor] = None,
        image_processor: Optional[ImageProcessor] = None,
        data_extractor: Optional[DataExtractor] = None
    ):
        """
        Initialize OCR pipeline.
        
        Args:
            ocr_engine: OCREngine instance (default: creates new)
            pdf_processor: PDFProcessor instance (default: creates new)
            image_processor: ImageProcessor instance (default: creates new)
            data_extractor: DataExtractor instance (default: creates new)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.ocr_engine = ocr_engine or OCREngine()
        self.pdf_processor = pdf_processor or PDFProcessor()
        self.image_processor = image_processor or ImageProcessor()
        self.data_extractor = data_extractor or DataExtractor()
        
        # External module integrations
        self.data_cleaner: Optional[DataCleanerInterface] = None
        self.search_engine: Optional[SearchEngineInterface] = None
        
        self.logger.info("OCR Pipeline initialized with all components")
    
    def process_pdf(self, pdf_path: str) -> List[ExtractedData]:
        """
        Process PDF document through complete OCR pipeline.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of ExtractedData objects (one per page)
            
        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF processing fails
        """
        self.logger.info(f"Starting PDF processing: {pdf_path}")
        
        try:
            # Step 1: Convert PDF to images
            self.logger.debug("Converting PDF to images...")
            images = self.pdf_processor.process(pdf_path)
            
            # Step 2: Process each page
            extracted_data_list = []
            for page_num, image in enumerate(images, 1):
                self.logger.debug(f"Processing PDF page {page_num}/{len(images)}")
                
                # Run OCR on page
                ocr_result = self._run_ocr_on_image(image, source_type="pdf", metadata={"page": page_num})
                
                # Extract structured data
                extracted_data = self.data_extractor.extract_from_ocr_result(
                    ocr_result,
                    source_file=pdf_path
                )
                
                extracted_data_list.append(extracted_data)
            
            self.logger.info(f"Successfully processed {len(extracted_data_list)} pages from PDF")
            return extracted_data_list
        
        except Exception as e:
            self.logger.error(f"PDF processing failed: {str(e)}")
            raise
    
    def process_image(self, image_path: str) -> ExtractedData:
        """
        Process image (scan/upload) through complete OCR pipeline.
        
        Args:
            image_path: Path to image file
            
        Returns:
            ExtractedData object
            
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image processing fails
        """
        self.logger.info(f"Starting image processing: {image_path}")
        
        try:
            # Step 1: Load and enhance image
            self.logger.debug("Loading and enhancing image...")
            image = self.image_processor.process(image_path)
            
            # Step 2: Run OCR
            ocr_result = self._run_ocr_on_image(image, source_type="image")
            
            # Step 3: Extract structured data
            extracted_data = self.data_extractor.extract_from_ocr_result(
                ocr_result,
                source_file=image_path
            )
            
            self.logger.info(f"Successfully processed image: {image_path}")
            return extracted_data
        
        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            raise
    
    def process_and_clean(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process PDF and send to cleaning module.
        For use case 1: scraped drug notices.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of cleaned data dictionaries
            
        Raises:
            ValueError: If cleaner not registered
        """
        if self.data_cleaner is None:
            raise ValueError("Data cleaner not registered. Call register_data_cleaner() first.")
        
        self.logger.info(f"Processing PDF with cleaning: {pdf_path}")
        
        try:
            # Process PDF
            extracted_data_list = self.process_pdf(pdf_path)
            
            # Clean each page's data
            cleaned_results = []
            for extracted_data in extracted_data_list:
                cleaned_data = self.data_cleaner.clean(extracted_data)
                
                # Validate cleaned data
                if self.data_cleaner.validate(cleaned_data):
                    cleaned_results.append(cleaned_data)
                    self.logger.debug("Data validated successfully")
                else:
                    self.logger.warning("Data validation failed, skipping entry")
            
            self.logger.info(f"Cleaned {len(cleaned_results)} entries from PDF")
            return cleaned_results
        
        except Exception as e:
            self.logger.error(f"Processing with cleaning failed: {str(e)}")
            raise
    
    def process_and_search(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Process image and search for drugs.
        For use case 2: user uploads (prescriptions/medicine names).
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of search results
            
        Raises:
            ValueError: If search engine not registered
        """
        if self.search_engine is None:
            raise ValueError("Search engine not registered. Call register_search_engine() first.")
        
        self.logger.info(f"Processing image with search: {image_path}")
        
        try:
            # Process image
            extracted_data = self.process_image(image_path)
            
            # Format for search
            search_queries = self.data_extractor.format_for_search(extracted_data)
            
            # Execute searches
            results = []
            
            # Search by medicine names
            if search_queries.get("medicine_names"):
                for medicine_name in search_queries["medicine_names"]:
                    try:
                        drug_results = self.search_engine.search_by_medicine_name(medicine_name)
                        results.extend(drug_results)
                    except Exception as e:
                        self.logger.warning(f"Search failed for {medicine_name}: {str(e)}")
            
            # Fallback: general search
            if not results and search_queries.get("primary_query"):
                try:
                    results = self.search_engine.search(search_queries["primary_query"])
                except Exception as e:
                    self.logger.warning(f"General search failed: {str(e)}")
            
            # Remove duplicates
            results = self._deduplicate_results(results)
            
            self.logger.info(f"Found {len(results)} drug matches")
            return results
        
        except Exception as e:
            self.logger.error(f"Processing with search failed: {str(e)}")
            raise
    
    def register_data_cleaner(self, cleaner: DataCleanerInterface) -> None:
        """
        Register external data cleaning module.
        
        Args:
            cleaner: Implementation of DataCleanerInterface
        """
        self.data_cleaner = cleaner
        self.logger.info(f"Data cleaner registered: {cleaner.__class__.__name__}")
    
    def register_search_engine(self, engine: SearchEngineInterface) -> None:
        """
        Register external search engine module.
        
        Args:
            engine: Implementation of SearchEngineInterface
        """
        self.search_engine = engine
        self.logger.info(f"Search engine registered: {engine.__class__.__name__}")
    
    def _run_ocr_on_image(self, image, source_type: str, metadata: Optional[Dict[str, Any]] = None) -> OCRResult:
        """
        Run OCR on image and return result.
        
        Args:
            image: PIL Image object
            source_type: "pdf" or "image"
            metadata: Additional metadata
            
        Returns:
            OCRResult object
        """
        self.logger.debug(f"Running OCR ({source_type})...")
        
        ocr_data = self.ocr_engine.extract_text_with_confidence(image)
        
        return OCRResult(
            raw_text=ocr_data.get("text", ""),
            confidence=ocr_data.get("confidence", 0.0),
            source_type=source_type,
            metadata=metadata or {}
        )
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate results based on drug ID or name.
        
        Args:
            results: List of drug results
            
        Returns:
            Deduplicated list
        """
        seen = set()
        deduplicated = []
        
        for result in results:
            # Use drug ID or name as unique identifier
            key = result.get("id") or result.get("name")
            if key and key not in seen:
                seen.add(key)
                deduplicated.append(result)
        
        return deduplicated
