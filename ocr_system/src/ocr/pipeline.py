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
    
# ------------------------------------------------------------------------
# Main processing methods
# ------------------------------------------------------------------------
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

    def process_pdf(self, pdf_path: str) -> ExtractedData:
        """
        Process PDF document through complete OCR pipeline.
        Combines all pages into a single ExtractedData object.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Single ExtractedData object with all pages combined
            
        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF processing fails
        """
        self.logger.info(f"Starting PDF processing: {pdf_path}")
        
        try:
            # Step 1: Convert PDF to images
            self.logger.debug("Converting PDF to images...")
            images = self.pdf_processor.process(pdf_path)
            
            # Step 2: Process each page individually
            all_extracted_data = []
            for page_num, image in enumerate(images, 1):
                self.logger.debug(f"Processing PDF page {page_num}/{len(images)}")
                
                # Run OCR on page
                ocr_result = self._run_ocr_on_image(
                    image, 
                    source_type="pdf", 
                    metadata={"page": page_num}
                )
                
                # Extract structured data
                extracted_data = self.data_extractor.extract_from_ocr_result(
                    ocr_result,
                    source_file=pdf_path
                )
                
                all_extracted_data.append(extracted_data)
            
            # Step 3: Combine all pages into single ExtractedData object
            combined_data = self._combine_extracted_data(all_extracted_data, pdf_path)
            
            self.logger.info(f"Successfully processed {len(images)} pages and combined into single result")
            
            return combined_data
        
        except Exception as e:
            self.logger.error(f"PDF processing failed: {str(e)}")
            raise
    
    def _combine_extracted_data(
        self, 
        data_list: List[ExtractedData],
        pdf_path: str
    ) -> ExtractedData:
        """
        Combine multiple ExtractedData objects (from multiple pages) into one.
        
        Args:
            data_list: List of ExtractedData objects from individual pages
            pdf_path: Path to PDF file
            
        Returns:
            Single combined ExtractedData object
        """
        if not data_list:
            # Return empty ExtractedData if no data
            return ExtractedData(
                medicine_names=[],
                prescription_info=None,
                raw_text="",
                extracted_fields={},
                metadata={"source_file": pdf_path, "total_pages": 0}
            )
        
        if len(data_list) == 1:
            # If only one page, return as-is with updated metadata
            data = data_list[0]
            data.metadata["total_pages"] = 1
            return data
        
        # Combine multiple pages
        combined_raw_text = "\n" + "="*80 + "\nPAGE SEPARATOR\n" + "="*80 + "\n".join(
            d.raw_text for d in data_list
        )
        
        # Deduplicate and combine medicine names
        combined_medicine_names = []
        seen_names = set()
        for data in data_list:
            for name in data.medicine_names:
                name_upper = name.upper()
                if name_upper not in seen_names:
                    seen_names.add(name_upper)
                    combined_medicine_names.append(name)
        
        # Combine prescription info (take first non-None)
        combined_prescription_info = None
        for data in data_list:
            if data.prescription_info:
                combined_prescription_info = data.prescription_info
                break
        
        # Combine extracted fields
        combined_fields = self._merge_extracted_fields(data_list)
        
        # Combine metadata
        combined_metadata = {
            "source_file": pdf_path,
            "total_pages": len(data_list),
            "page_metadata": [d.metadata for d in data_list],
            "ocr_confidence": sum(
                d.metadata.get("ocr_confidence", 0) for d in data_list
            ) / len(data_list),  # Average confidence
        }
        
        return ExtractedData(
            medicine_names=combined_medicine_names,
            prescription_info=combined_prescription_info,
            raw_text=combined_raw_text,
            extracted_fields=combined_fields,
            metadata=combined_metadata
        )
    
    def _merge_extracted_fields(
        self, 
        data_list: List[ExtractedData]
    ) -> Dict[str, Any]:
        """
        Merge extracted fields from multiple pages.
        
        Args:
            data_list: List of ExtractedData objects
            
        Returns:
            Merged extracted fields dictionary
        """
        merged = {}
        
        # Collect all keys from all data objects
        all_keys = set()
        for data in data_list:
            all_keys.update(data.extracted_fields.keys())
        
        for key in all_keys:
            values = []
            
            for data in data_list:
                if key in data.extracted_fields:
                    value = data.extracted_fields[key]
                    if value is not None:
                        values.append(value)
            
            if not values:
                continue
            
            # Merge based on type
            first_value = values[0]
            
            if isinstance(first_value, list):
                # Merge lists, deduplicating
                merged_list = []
                seen = set()
                for v in values:
                    if isinstance(v, list):
                        for item in v:
                            item_key = str(item).upper() if isinstance(item, str) else str(item)
                            if item_key not in seen:
                                seen.add(item_key)
                                merged_list.append(item)
                    else:
                        item_key = str(v).upper() if isinstance(v, str) else str(v)
                        if item_key not in seen:
                            seen.add(item_key)
                            merged_list.append(v)
                merged[key] = merged_list
            
            elif isinstance(first_value, dict):
                # Merge dicts
                merged_dict = {}
                for v in values:
                    if isinstance(v, dict):
                        merged_dict.update(v)
                merged[key] = merged_dict
            
            else:
                # For strings and other types, take first value
                merged[key] = first_value
        
        return merged
    
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
    
#-------------------------------------------------------------------------
# Use case 1: Scraped drug notices
#-------------------------------------------------------------------------
    def process_and_clean(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF and send to cleaning module.
        For use case 1: scraped drug notices.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Cleaned data dictionary
            
        Raises:
            ValueError: If cleaner not registered
        """
        if self.data_cleaner is None:
            raise ValueError("Data cleaner not registered. Call register_data_cleaner() first.")
        
        self.logger.info(f"Processing PDF with cleaning: {pdf_path}")
        
        try:
            # Process PDF (returns single combined ExtractedData)
            extracted_data = self.process_pdf(pdf_path)
            
            # Clean the data
            cleaned_data = self.data_cleaner.clean(extracted_data)
            
            # Validate cleaned data
            if self.data_cleaner.validate(cleaned_data):
                self.logger.info("Data validated successfully")
                return cleaned_data
            else:
                self.logger.warning("Data validation failed")
                return cleaned_data
        
        except Exception as e:
            self.logger.error(f"Processing with cleaning failed: {str(e)}")
            raise
    
#-------------------------------------------------------------------------
# Use case 2: User uploads (prescriptions/medicine names)
#-------------------------------------------------------------------------
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
    
#-------------------------------------------------------------------------
# Private methods
#-------------------------------------------------------------------------
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

