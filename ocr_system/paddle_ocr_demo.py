"""PaddleOCR Demo - Practical examples of using PaddleOCR."""

import os
import sys
import logging
import warnings
from pathlib import Path
from io import StringIO

# Set environment variable to disable model source check
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# Suppress all PaddleOCR and C++ backend output
os.environ['PADDLE_PDX_ENABLE_LOGGING'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('paddle').setLevel(logging.ERROR)
logging.getLogger('paddleocr').setLevel(logging.ERROR)
logging.getLogger('paddlex').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

from src.paddle_ocr.paddle_engine import PaddleEngine
from src.paddle_ocr.paddle_pipeline import PaddleOCRPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def extract_from_image():
    """Extract text from an image file."""
    print("\n" + "="*60)
    print("Example 1: Extract Text from Image")
    print("="*60)
    
    engine = PaddleEngine()
    image_path = r"sample.jpg"
    result = engine.extract_text(image_path)
    
    if result['success']:
        print(f"[SUCCESS] Text extracted")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Text: {result['text']}...")
    else:
        print(f"[FAILED] {result.get('error', 'Unknown error')}")


def extract_from_pdf():
    """Extract text from a PDF document."""
    print("\n" + "="*60)
    print("Example 2: Extract Text from PDF")
    print("="*60)
    
    pipeline = PaddleOCRPipeline()
    pdf_path = "med.pdf"
    result = pipeline.process_document(pdf_path)
    
    if result['success']:
        print(f"[SUCCESS] PDF processed")
        print(f"Pages: {result.get('page_count', 'Unknown')}")
        print(f"Average Confidence: {result.get('average_confidence', 0.0):.2%}")
        print(f"Text: {result['text'][:200]}")
    else:
        print(f"[FAILED] {result.get('error', 'Unknown error')}")



def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("PaddleOCR - Practical Usage Examples")
    print("="*60)
    
    extract_from_image()
    extract_from_pdf()

if __name__ == "__main__":
    main()
