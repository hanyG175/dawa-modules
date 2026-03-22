"""
Demo script for Google OCR Tool
Shows all functionality without requiring actual image processing
"""
import warnings
warnings.filterwarnings('ignore')

from utils import ImageHandler, FileHandler, TextProcessor
from ocr_processor import OCRProcessor

def demo_image_handler():
    """Demonstrate ImageHandler functionality."""
    print("\n" + "=" * 60)
    print("DEMO 1: Image Handler")
    print("=" * 60)
    
    print("\nSupported image formats:", ImageHandler.SUPPORTED_FORMATS)
    
    test_files = ["photo.png", "scan.jpg", "document.bmp", "image.tiff", "doc.pdf", "text.txt"]
    print("\nChecking file types:")
    for file in test_files:
        is_valid = ImageHandler.is_valid_image(file)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {file:20} {status}")


def demo_file_handler():
    """Demonstrate FileHandler functionality."""
    print("\n" + "=" * 60)
    print("DEMO 2: File Handler")
    print("=" * 60)
    
    test_file = "demo_output.txt"
    test_content = "Hello from Google OCR Tool!\nThis is a demo file.\nLine 3: Test content."
    
    print(f"\n1. Writing to file: {test_file}")
    path = FileHandler.write_file(test_file, test_content)
    print(f"   ✓ File written to: {path}")
    
    print(f"\n2. Reading from file: {test_file}")
    content = FileHandler.read_file(test_file)
    print(f"   ✓ Content read:\n   {content}")
    
    print(f"\n3. File information:")
    info = FileHandler.get_file_info(test_file)
    if info:
        print(f"   ✓ File size: {info['size']} bytes")
        print(f"   ✓ File path: {info['path']}")
    
    print(f"\n4. Cleaning up...")
    deleted = FileHandler.delete_file(test_file)
    print(f"   ✓ File deleted: {deleted}")


def demo_text_processor():
    """Demonstrate TextProcessor functionality."""
    print("\n" + "=" * 60)
    print("DEMO 3: Text Processor")
    print("=" * 60)
    
    sample_text = """  Lorem ipsum dolor sit amet
    
    Consectetur adipiscing elit
    
    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua  """
    
    print("\n1. Original text (with extra whitespace):")
    print(f"   {repr(sample_text)}")
    
    print("\n2. Cleaned text:")
    cleaned = TextProcessor.clean_text(sample_text)
    print(f"   {cleaned}")
    
    print("\n3. Word extraction:")
    words = TextProcessor.extract_words(cleaned)
    print(f"   Total words: {len(words)}")
    print(f"   First 5 words: {words[:5]}")
    
    print("\n4. Line extraction:")
    lines = TextProcessor.extract_lines(cleaned)
    print(f"   Total lines: {len(lines)}")
    
    print("\n5. Text statistics:")
    stats = TextProcessor.get_statistics(cleaned)
    print(f"   Characters: {stats['characters']}")
    print(f"   Words: {stats['words']}")
    print(f"   Lines: {stats['lines']}")
    print(f"   Avg word length: {stats['average_word_length']:.2f}")


def demo_ocr_processor():
    """Demonstrate OCRProcessor functionality."""
    print("\n" + "=" * 60)
    print("DEMO 4: OCR Processor Status")
    print("=" * 60)
    
    try:
        processor = OCRProcessor()
        print("\n✓ OCRProcessor initialized successfully")
        print(f"✓ ImageHandler available: {processor.image_handler is not None}")
        print(f"✓ FileHandler available: {processor.file_handler is not None}")
        print(f"✓ GoogleOCR engine available: {processor.ocr_engine is not None}")
        
        print("\nOCR Tool Features:")
        print("  • Process single images")
        print("  • Batch process directories")
        print("  • Extract text from images")
        print("  • Generate text statistics")
        print("  • Save results to files")
        print("  • Validate image formats")
        print("  • Manage file operations")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  GOOGLE OCR TOOL - FEATURE DEMONSTRATION")
    print("=" * 60)
    
    demo_image_handler()
    demo_file_handler()
    demo_text_processor()
    demo_ocr_processor()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("\n1. To use the OCR tool interactively:")
    print("   python main.py")
    print("\n2. To test all functionality:")
    print("   python test_ocr.py")
    print("\n3. Requirements:")
    print("   - Valid Google Drive API credentials")
    print("   - Image files in PNG format")
    print("   - Internet connection for API access")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
