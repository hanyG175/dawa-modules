"""
OCR Module for extracting text from drug notices and user uploads.
Supports both PDF documents and image scanning.
"""

from .ocr_engine import OCREngine
from .processors.pdf_processor import PDFProcessor
from .processors.image_processor import ImageProcessor
from .data_extraction import DataExtractor
from .pipeline import StandardOCRPipeline
from .simple_pipeline import SimpleOCRPipeline
from .interfaces import (
    OCRPipeline,
    DataCleanerInterface,
    SearchEngineInterface,
    OCRResult,
    ExtractedData,
)
from .mocks import MockDataCleaner, MockSearchEngine

__all__ = [
    "OCREngine",
    "PDFProcessor",
    "ImageProcessor",
    "DataExtractor",
    "StandardOCRPipeline",
    "SimpleOCRPipeline",
    "OCRPipeline",
    "DataCleanerInterface",
    "SearchEngineInterface",
    "OCRResult",
    "ExtractedData",
    "MockDataCleaner",
    "MockSearchEngine",
]

__version__ = "0.1.0"
