"""
Quick test to verify the OCR tool loads without errors
"""
import warnings
warnings.filterwarnings('ignore')

print("Testing OCR Tool Import...")
print("=" * 50)

try:
    print("1. Importing OCRProcessor...")
    from ocr_processor import OCRProcessor
    print("   ✓ OCRProcessor imported successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

try:
    print("2. Importing utils...")
    from utils import TextProcessor, FileHandler, ImageHandler
    print("   ✓ Utils imported successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

try:
    print("3. Importing GoogleOCR...")
    from GoogleOCR import GoogleOCR
    print("   ✓ GoogleOCR imported successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

try:
    print("4. Initializing OCRProcessor...")
    processor = OCRProcessor()
    print("   ✓ OCRProcessor initialized successfully")
except Exception as e:
    print(f"   ✗ Error (Warning - may fail if credentials missing): {e}")

print("\n" + "=" * 50)
print("✓ All imports successful! Tool is ready to use.")
print("=" * 50)
print("\nRun 'python main.py' to start the interactive CLI")
