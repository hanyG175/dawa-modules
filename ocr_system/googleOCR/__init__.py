"""
Google OCR Tool - A comprehensive OCR solution using Google Drive API
"""

from .GoogleOCR import GoogleOCR
from .ocr_processor import OCRProcessor
from .utils import ImageHandler, FileHandler

__version__ = "1.0.0"
__all__ = ["GoogleOCR", "OCRProcessor", "ImageHandler", "FileHandler"]
