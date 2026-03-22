"""Image processor for handling image uploads and scans."""

import logging
from pathlib import Path
from typing import List, Optional
from PIL import Image
import cv2
import numpy as np

from . import BaseProcessor

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """
    Processor for image files (scans, photos, uploads).
    Handles image validation, preprocessing, and enhancement.
    """
    
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"}
    MAX_IMAGE_SIZE = (5000, 5000)  # Maximum dimensions
    MIN_IMAGE_SIZE = (100, 100)    # Minimum dimensions
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def __init__(self, enhance_quality: bool = True):
        """
        Initialize image processor.
        
        Args:
            enhance_quality: Whether to apply enhancement filters for OCR
        """
        super().__init__(name="ImageProcessor")
        self.enhance_quality = enhance_quality
    
    def validate_input(self, file_path: str) -> bool:
        """
        Validate image file format and size.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if valid image, False otherwise
        """
        if not self._validate_file_exists(file_path):
            return False
        
        path = Path(file_path)
        
        # Check format
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            self.logger.error(f"Unsupported format: {path.suffix}")
            return False
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            self.logger.error(f"File too large: {file_size} bytes")
            return False
        
        # Try to open image
        try:
            img = Image.open(path)
            img.verify()
            
            # Check dimensions
            if img.size < self.MIN_IMAGE_SIZE or img.size > self.MAX_IMAGE_SIZE:
                self.logger.error(f"Invalid image dimensions: {img.size}")
                return False
        except Exception as e:
            self.logger.error(f"Invalid image file: {str(e)}")
            return False
        
        return True
    
    def process(self, file_path: str) -> Image.Image:
        """
        Process image for OCR.
        Loads and optionally enhances image quality.
        
        Args:
            file_path: Path to image file
            
        Returns:
            PIL Image object
            
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image cannot be processed
        """
        if not self.validate_input(file_path):
            raise FileNotFoundError(f"Invalid image: {file_path}")
        
        try:
            self.logger.info(f"Processing image: {file_path}")
            image = Image.open(file_path)
            
            if self.enhance_quality:
                image = self._enhance_for_ocr(image)
            
            return image
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    def _enhance_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Apply enhancement filters to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Enhanced PIL Image object
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for OpenCV processing
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 1. Denoise
            img_cv = cv2.fastNlMeansDenoisingColored(
                img_cv,
                None,
                10,
                10,
                7,
                21,
            )
            
            # 2. Grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # 3. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 4. Thresholding for better text visibility
            _, thresh = cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)
            
            # Convert back to PIL Image
            enhanced_image = Image.fromarray(thresh)
            self.logger.debug("Applied OCR enhancement filters")
            
            return enhanced_image
        except Exception as e:
            self.logger.warning(f"Enhancement failed, returning original: {str(e)}")
            return image
    
    def get_image_info(self, file_path: str) -> dict:
        """
        Get metadata about image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary with image metadata
        """
        if not self.validate_input(file_path):
            return {}
        
        try:
            image = Image.open(file_path)
            return {
                "size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_mb": Path(file_path).stat().st_size / (1024 * 1024)
            }
        except Exception as e:
            self.logger.error(f"Error getting image info: {str(e)}")
            return {}
