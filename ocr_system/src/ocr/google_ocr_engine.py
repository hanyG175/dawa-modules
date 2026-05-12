"""Google Cloud Vision API OCR engine for text extraction."""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image
import io

try:
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

logger = logging.getLogger(__name__)


class GoogleOCREngine:
    """
    Google Cloud Vision API-based OCR engine for text extraction.
    Handles image and document processing with language support.
    """
    
    SUPPORTED_LANGUAGES = {
        "eng": "English",
        "fra": "French",
        "ara": "Arabic",
        "spa": "Spanish",
        "deu": "German",
        "ita": "Italian",
        "por": "Portuguese",
        "rus": "Russian",
        "jpn": "Japanese",
        "zho": "Chinese",
    }
    
    # Google Cloud language codes mapping
    LANGUAGE_HINTS = {
        "eng": "en-t-i0-handwrit",
        "fra": "fr",
        "ara": "ar",
        "spa": "es",
        "deu": "de",
        "ita": "it",
        "por": "pt",
        "rus": "ru",
        "jpn": "ja",
        "zho": "zh",
    }
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        languages: Optional[List[str]] = None,
    ):
        """
        Initialize Google OCR engine.
        
        Args:
            credentials_path: Path to Google Cloud service account JSON file
            languages: List of language codes (default: ["eng"])
            
        Raises:
            ImportError: If google-cloud-vision is not installed
            FileNotFoundError: If credentials file not found
        """
        if not GOOGLE_VISION_AVAILABLE:
            raise ImportError(
                "google-cloud-vision is not installed. "
                "Install it with: pip install google-cloud-vision"
            )
        
        self.languages = languages or ["eng"]
        self._validate_languages()
        
        # Initialize credentials
        if credentials_path is None:
            credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if credentials_path and os.path.exists(credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.info(f"Initialized Google Vision client with credentials from {credentials_path}")
            except Exception as e:
                logger.error(f"Failed to initialize with credentials: {e}")
                self.client = vision.ImageAnnotatorClient()
        else:
            # Use default credentials from environment
            self.client = vision.ImageAnnotatorClient()
            logger.info("Initialized Google Vision client with default credentials")
        
        self.credentials_path = credentials_path
    
    def _validate_languages(self) -> None:
        """Validate that all specified languages are supported."""
        unsupported = set(self.languages) - set(self.SUPPORTED_LANGUAGES.keys())
        if unsupported:
            logger.warning(f"Unsupported languages: {unsupported}. Falling back to English.")
            self.languages = ["eng"]
    
    def extract_text_from_image(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text from a single image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.client.document_text_detection(
                image=image,
                image_context=vision.ImageContext(
                    language_hints=self._get_language_hints()
                ),
            )
            
            return self._process_response(response, image_path, "image")
        
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return {
                "success": False,
                "raw_text": "",
                "confidence": 0.0,
                "error": str(e),
                "source": image_path,
            }
    
    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        filename: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Image content as bytes
            filename: Optional filename for logging
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            image = vision.Image(content=image_bytes)
            response = self.client.document_text_detection(
                image=image,
                image_context=vision.ImageContext(
                    language_hints=self._get_language_hints()
                ),
            )
            
            return self._process_response(response, filename, "bytes")
        
        except Exception as e:
            logger.error(f"Error extracting text from bytes ({filename}): {e}")
            return {
                "success": False,
                "raw_text": "",
                "confidence": 0.0,
                "error": str(e),
                "source": filename,
            }
    
    def extract_text_from_uri(
        self,
        image_uri: str,
    ) -> Dict[str, Any]:
        """
        Extract text from an image URL or Cloud Storage URI.
        
        Args:
            image_uri: GCS URI or HTTPS URL to image
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            image = vision.Image()
            image.source.image_uri = image_uri
            
            response = self.client.document_text_detection(
                image=image,
                image_context=vision.ImageContext(
                    language_hints=self._get_language_hints()
                ),
            )
            
            return self._process_response(response, image_uri, "uri")
        
        except Exception as e:
            logger.error(f"Error extracting text from {image_uri}: {e}")
            return {
                "success": False,
                "raw_text": "",
                "confidence": 0.0,
                "error": str(e),
                "source": image_uri,
            }
    
    def extract_with_layout(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text with layout information (blocks, paragraphs, lines).
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with text and detailed layout information
        """
        try:
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.client.document_text_detection(
                image=image,
                image_context=vision.ImageContext(
                    language_hints=self._get_language_hints()
                ),
            )
            
            result = self._process_response(response, image_path, "image")
            
            # Add layout information
            if response.text_annotations:
                result["layout"] = self._extract_layout(response)
            
            return result
        
        except Exception as e:
            logger.error(f"Error extracting layout from {image_path}: {e}")
            return {
                "success": False,
                "raw_text": "",
                "confidence": 0.0,
                "error": str(e),
                "source": image_path,
                "layout": [],
            }
    
    def _process_response(
        self,
        response: Any,
        source: str,
        source_type: str,
    ) -> Dict[str, Any]:
        """
        Process Google Vision API response.
        
        Args:
            response: Vision API response
            source: Source identifier
            source_type: Type of source (image, bytes, uri)
            
        Returns:
            Processed OCR result
        """
        if response.error.message:
            error_msg = f"Google Vision API error: {response.error.message}"
            logger.error(error_msg)
            return {
                "success": False,
                "raw_text": "",
                "confidence": 0.0,
                "error": error_msg,
                "source": source,
            }
        
        if not response.text_annotations:
            return {
                "success": True,
                "raw_text": "",
                "confidence": 0.0,
                "source": source,
                "source_type": source_type,
            }
        
        # First annotation is the full text
        full_text = response.full_text_annotation.text
        confidence = self._calculate_confidence(response)
        
        return {
            "success": True,
            "raw_text": full_text,
            "confidence": confidence,
            "source": source,
            "source_type": source_type,
            "language": response.full_text_annotation.pages[0].detected_languages if response.full_text_annotation.pages else [],
        }
    
    def _calculate_confidence(self, response: Any) -> float:
        """
        Calculate average confidence from response.
        
        Args:
            response: Vision API response
            
        Returns:
            Confidence score between 0 and 1
        """
        if not response.full_text_annotation.pages:
            return 0.0
        
        # Get block-level confidences
        confidences = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            if symbol.confidence > 0:
                                confidences.append(symbol.confidence)
        
        if not confidences:
            return 1.0
        
        return sum(confidences) / len(confidences)
    
    def _extract_layout(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract layout information from response.
        
        Args:
            response: Vision API response
            
        Returns:
            List of layout elements with bounding boxes
        """
        layout = []
        
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                block_text = ""
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            block_text += symbol.text
                        block_text += " "
                    block_text += "\n"
                
                # Get bounding box
                vertices = block.bounding_box.vertices
                bbox = {
                    "x": min(v.x for v in vertices),
                    "y": min(v.y for v in vertices),
                    "width": max(v.x for v in vertices) - min(v.x for v in vertices),
                    "height": max(v.y for v in vertices) - min(v.y for v in vertices),
                }
                
                layout.append({
                    "type": "block",
                    "text": block_text.strip(),
                    "bounding_box": bbox,
                    "confidence": self._calculate_block_confidence(block),
                })
        
        return layout
    
    def _calculate_block_confidence(self, block: Any) -> float:
        """Calculate confidence for a block."""
        confidences = []
        for paragraph in block.paragraphs:
            for word in paragraph.words:
                for symbol in word.symbols:
                    if symbol.confidence > 0:
                        confidences.append(symbol.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _get_language_hints(self) -> List[str]:
        """Get language hints for API call."""
        hints = []
        for lang in self.languages:
            if lang in self.LANGUAGE_HINTS:
                hints.append(self.LANGUAGE_HINTS[lang])
        return hints or ["en-t-i0-handwrit"]
    
    def batch_process(
        self,
        image_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Process multiple images.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            List of OCR results
        """
        results = []
        for image_path in image_paths:
            result = self.extract_text_from_image(image_path)
            results.append(result)
        
        return results
