"""PaddleOCR engine - simple wrapper around PaddleOCR library."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np

# Must be set before importing PaddleOCR
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['GLOG_minloglevel'] = '3'

try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("Install PaddleOCR with: pip install paddleocr")

logger = logging.getLogger(__name__)


class PaddleEngine:
    """Simple PaddleOCR wrapper for text extraction."""
    
    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False):
        """
        Initialize OCR engine.
        
        Args:
            languages: Language codes (default: ["en"]) - note: use first language for now
            use_gpu: Use GPU acceleration (default: False)
        """
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        
        # Use only the first language
        primary_lang = self.languages[0] if self.languages else "en"
        
        logger.info(f"Initializing PaddleOCR with language: {primary_lang}")
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=primary_lang,
            use_gpu=use_gpu,
            show_log=False,
        )
    
    def extract_text(self, image_input: Any) -> Dict[str, Any]:
        """
        Extract text from image.
        
        Args:
            image_input: Image path, numpy array, or PIL image
            
        Returns:
            Dictionary with 'text', 'confidence', and 'success' keys
        """
        try:
            logger.info(f"Extracting text from: {image_input}")
            prepared_input = self._prepare_input(image_input)
            results = self.ocr.ocr(prepared_input, cls=True)
            
            if not results or not results[0]:
                return {"text": "", "confidence": 0.0, "success": False}
            
            # Extract text and confidence
            texts = []
            confidences = []
            for line in results[0]:
                if len(line) > 1 and len(line[1]) >= 2:
                    text = line[1][0]
                    confidence = float(line[1][1])
                    if text:
                        texts.append(text)
                        confidences.append(confidence)
            
            full_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"Extracted text with confidence: {avg_confidence:.2%}")
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "success": bool(full_text),
            }
        except Exception as e:
            logger.error(f"OCR extraction error: {str(e)}")
            return {"text": "", "confidence": 0.0, "success": False, "error": str(e)}

    def _prepare_input(self, image_input: Any) -> Any:
        """Prepare input for PaddleOCR v2 `ocr()` API."""
        if isinstance(image_input, (str, Path)):
            return str(image_input)

        if isinstance(image_input, np.ndarray):
            return image_input

        # Handle PIL images without forcing PIL import dependency at module load
        if hasattr(image_input, "mode") and hasattr(image_input, "size"):
            try:
                return np.array(image_input)
            except Exception:
                pass

        raise TypeError("Unsupported image input type. Use file path, numpy.ndarray, or PIL image.")
