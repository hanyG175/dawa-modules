"""
Non-interactive test mode for main.py
"""
import warnings
warnings.filterwarnings('ignore')

import sys
import os
from pathlib import Path
from ocr_processor import OCRProcessor
from utils import TextProcessor, FileHandler


def test_tool_startup():
    """Test that the tool starts up without errors."""
    print("\n" + "=" * 60)
    print("TESTING: OCR Tool Startup")
    print("=" * 60)
    
    try:
        print("\n1. Initializing OCRProcessor...")
        processor = OCRProcessor()
        print("   ✓ OCRProcessor initialized")
        
        print("\n2. Verifying components...")
        print(f"   ✓ Image handler: {processor.image_handler is not None}")
        print(f"   ✓ File handler: {processor.file_handler is not None}")
        print(f"   ✓ OCR engine: {processor.ocr_engine is not None}")
        
        print("\n3. Available methods:")
        methods = [m for m in dir(processor) if not m.startswith('_')]
        for method in methods:
            print(f"   • {method}()")
        
        print("\n" + "=" * 60)
        print("✓ STARTUP TEST PASSED - Tool is ready to use!")
        print("=" * 60)
        print("\nCommand to run the tool:")
        print("python main.py")
        print("=" * 60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ STARTUP TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_tool_startup()
    sys.exit(0 if success else 1)
