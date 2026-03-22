"""Simple OCR pipeline using PaddleOCR."""

import logging
import warnings
from pathlib import Path
from typing import Dict, Any, Optional

# Suppress PaddleOCR warnings
logging.getLogger('paddle').setLevel(logging.ERROR)
logging.getLogger('paddleocr').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

from src.ocr.processors.pdf_processor import PDFProcessor
from src.ocr.processors.image_processor import ImageProcessor
from .paddle_engine import PaddleEngine

logger = logging.getLogger(__name__)


class PaddleOCRPipeline:
    """Simple pipeline for PaddleOCR with PDF and image support."""
    
    def __init__(
        self,
        paddle_engine: Optional[PaddleEngine] = None,
        pdf_processor: Optional[PDFProcessor] = None,
        image_processor: Optional[ImageProcessor] = None,
    ):
        """
        Initialize pipeline.
        
        Args:
            paddle_engine: PaddleEngine instance (creates default if None)
            pdf_processor: PDFProcessor instance (creates default if None)
            image_processor: ImageProcessor instance (creates default if None)
        """
        self.paddle_engine = paddle_engine or PaddleEngine()
        self.pdf_processor = pdf_processor or PDFProcessor()
        self.image_processor = image_processor or ImageProcessor()
        
        logger.info("PaddleOCR Pipeline initialized")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF or image file.
        
        Args:
            file_path: Path to PDF or image
            
        Returns:
            Dictionary with processing results
        """
        try:
            input_path = Path(file_path)
            logger.info(f"Processing: {input_path}")
            
            if input_path.suffix.lower() == ".pdf":
                return self._process_pdf(input_path)
            else:
                return self._process_image(input_path)
        
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return {"success": False, "error": str(e), "file_path": str(file_path)}
    
    def _process_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Process PDF file."""
        logger.info(f"Processing PDF: {file_path}")
        
        # Convert PDF pages to images
        images = self.pdf_processor.process(str(file_path))
        
        if not images:
            return {"success": False, "error": "Failed to extract images from PDF"}
        
        # Extract text from all pages
        all_text = []
        confidence_scores = []
        page_success_count = 0
        page_layouts = []
        all_layout_blocks = []

        for page_idx, image in enumerate(images, start=1):
            result = self.paddle_engine.extract_text(image)
            if result["success"]:
                all_text.append(result["text"])
                confidence_scores.append(result["confidence"])
                page_success_count += 1

            layout_result = self.paddle_engine.extract_layout(image)
            if layout_result.get("success"):
                blocks = layout_result.get("blocks", [])
                page_layouts.append(
                    {
                        "page": page_idx,
                        "blocks": blocks,
                    }
                )
                for block in blocks:
                    block_with_page = dict(block)
                    block_with_page["page"] = page_idx
                    all_layout_blocks.append(block_with_page)
                
        
        return {
            "success": page_success_count > 0,
            "file_path": str(file_path),
            "source_type": "pdf",
            "page_count": len(images),
            "processed_pages": page_success_count,
            "text": "\n\n".join(all_text),
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "layout_pages": page_layouts,
            "layout_blocks": all_layout_blocks,
            "layout_success": len(page_layouts) > 0,
        }
    
    def _process_image(self, file_path: Path) -> Dict[str, Any]:
        """Process image file."""
        logger.info(f"Processing image: {file_path}")
        
        # Preprocess image
        processed_path = self.image_processor.process(str(file_path))

        if processed_path is None:
            return {
                "success": False,
                "file_path": str(file_path),
                "source_type": "image",
                "text": "",
                "confidence": 0.0,
                "error": "Image preprocessing failed",
            }
        
        # Extract text
        result = self.paddle_engine.extract_text(processed_path)
        
        return {
            "success": result["success"],
            "file_path": str(file_path),
            "source_type": "image",
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
        }
