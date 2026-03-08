"""OCR engine using Tesseract for text extraction."""

import logging
from typing import Dict, List, Optional, Any
from PIL import Image
import pytesseract
from pytesseract import Output

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Tesseract-based OCR engine for text extraction from images.
    Handles language configuration and quality settings.
    """
    
    SUPPORTED_LANGUAGES = {
        "eng": "English",
        "fra": "French",
        "ara": "Arabic",
        # Add more as needed
    }
    
    def __init__(self, languages: Optional[List[str]] = None, config: Optional[str] = None):
        """
        Initialize OCR engine.
        
        Args:
            languages: List of language codes (default: ["eng"])
                      See SUPPORTED_LANGUAGES for options
            config: Custom Tesseract config string (advanced users)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.languages = languages or ["eng"]
        self.lang_string = "+".join(self.languages)
        
        # Default optimized config for medical documents
        self.config = config or "--psm 3 --oem 3"
        
        self.logger.info(f"OCR Engine initialized with languages: {self.lang_string}")
    
    def extract_text(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract text from image using Tesseract OCR.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            self.logger.debug("Starting OCR text extraction")
            
            text = pytesseract.image_to_string(
                image,
                lang=self.lang_string,
                config=self.config
            )
            
            confidence = self._get_average_confidence(image)
            
            return {
                "text": text.strip(),
                "confidence": confidence,
                "languages": self.languages,
                "raw_data": None
            }
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "languages": self.languages,
                "error": str(e)
            }
    
    def extract_text_with_confidence(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract text with detailed confidence scores for each word.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with detailed OCR results including word-level confidence
        """
        try:
            self.logger.debug("Starting detailed OCR extraction with confidence")
            
            # Get detailed data with confidence
            data = pytesseract.image_to_data(
                image,
                lang=self.lang_string,
                config=self.config,
                output_type=Output.DICT
            )
            
            # Construct full text
            full_text = " ".join(
                word for word in data.get("text", [])
                if word.strip()
            )
            
            # Calculate statistics
            confidences = [
                int(conf) for conf in data.get("conf", [])
                if int(conf) > 0
            ]
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "text": full_text.strip(),
                "confidence": avg_confidence / 100.0,  # Normalize to 0-1
                "word_count": len([c for c in confidences if c > 0]),
                "languages": self.languages,
                "detailed_data": data
            }
        except Exception as e:
            self.logger.error(f"Detailed OCR extraction failed: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "languages": self.languages,
                "error": str(e)
            }
    
    def extract_structured_data(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract structured data (blocks, paragraphs, lines, words) from image.
        Useful for understanding layout and structure.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with structured OCR data
        """
        try:
            self.logger.debug("Starting structured OCR extraction")
            
            data = pytesseract.image_to_data(
                image,
                lang=self.lang_string,
                config=self.config,
                output_type=Output.DICT
            )
            
            # Parse structured data
            blocks = self._parse_blocks(data)
            
            return {
                "blocks": blocks,
                "text": " ".join(word for word in data.get("text", []) if word.strip()),
                "total_words": len([w for w in data.get("text", []) if w.strip()]),
                "languages": self.languages
            }
        except Exception as e:
            self.logger.error(f"Structured extraction failed: {str(e)}")
            return {
                "blocks": [],
                "text": "",
                "total_words": 0,
                "error": str(e)
            }
    
    def _get_average_confidence(self, image: Image.Image) -> float:
        """
        Calculate average OCR confidence.
        
        Args:
            image: PIL Image object
            
        Returns:
            Average confidence score (0-1)
        """
        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.lang_string,
                config=self.config,
                output_type=Output.DICT
            )
            
            confidences = [
                int(conf) for conf in data.get("conf", [])
                if int(conf) > 0
            ]
            
            if not confidences:
                return 0.0
            
            return sum(confidences) / len(confidences) / 100.0
        except Exception as e:
            self.logger.debug(f"Could not calculate confidence: {str(e)}")
            return 0.0
    
    def _parse_blocks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Tesseract output data into structured blocks.
        
        Args:
            data: Output from pytesseract.image_to_data
            
        Returns:
            List of block dictionaries
        """
        blocks = []
        current_block = None
        
        for i, block_num in enumerate(data.get("block_num", [])):
            if block_num != (current_block.get("block_num") if current_block else -1):
                if current_block:
                    blocks.append(current_block)
                current_block = {
                    "block_num": block_num,
                    "lines": [],
                    "text": ""
                }
            
            text = data["text"][i]
            if text.strip():
                current_block["text"] += text + " "
        
        if current_block:
            blocks.append(current_block)
        
        return blocks
    
    def add_language(self, language_code: str) -> None:
        """
        Add additional language for OCR.
        
        Args:
            language_code: Language code (e.g., 'fra' for French)
        """
        if language_code not in self.languages:
            self.languages.append(language_code)
            self.lang_string = "+".join(self.languages)
            self.logger.info(f"Added language: {language_code}")
    
    def set_languages(self, language_codes: List[str]) -> None:
        """
        Set complete language list.
        
        Args:
            language_codes: List of language codes
        """
        self.languages = language_codes
        self.lang_string = "+".join(self.languages)
        self.logger.info(f"Languages set to: {self.lang_string}")
