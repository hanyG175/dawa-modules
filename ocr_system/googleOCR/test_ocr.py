"""
Test script for Google OCR Tool
"""

import os
import sys
from pathlib import Path
from ocr_processor import OCRProcessor
from utils import ImageHandler, FileHandler, TextProcessor


def test_image_handler():
    """Test ImageHandler functionality."""
    print("\n" + "="*50)
    print("Testing ImageHandler")
    print("="*50)

    # Test supported formats
    print("Supported formats:", ImageHandler.SUPPORTED_FORMATS)

    # Test image validation
    test_files = ["test.png", "test.jpg", "test.pdf", "test.txt"]
    for file in test_files:
        is_valid = ImageHandler.is_valid_image(file)
        print(f"Is '{file}' valid image? {is_valid}")


def test_file_handler():
    """Test FileHandler functionality."""
    print("\n" + "="*50)
    print("Testing FileHandler")
    print("="*50)

    # Test file operations
    test_file = "test_output.txt"
    test_content = "Hello, World!\nThis is a test."

    # Write file
    result = FileHandler.write_file(test_file, test_content)
    print(f"Write file result: {result}")

    # Read file
    content = FileHandler.read_file(test_file)
    print(f"Read file content: {content}")

    # Check file exists
    exists = FileHandler.file_exists(test_file)
    print(f"File exists: {exists}")

    # Get file info
    info = FileHandler.get_file_info(test_file)
    print(f"File info: {info}")

    # Delete file
    deleted = FileHandler.delete_file(test_file)
    print(f"File deleted: {deleted}")


def test_text_processor():
    """Test TextProcessor functionality."""
    print("\n" + "="*50)
    print("Testing TextProcessor")
    print("="*50)

    test_text = "  Hello world  \n\n  This is a test  \n  With multiple lines  "

    # Clean text
    cleaned = TextProcessor.clean_text(test_text)
    print(f"Cleaned text:\n{cleaned}\n")

    # Extract words
    words = TextProcessor.extract_words(test_text)
    print(f"Words: {words}\n")

    # Extract lines
    lines = TextProcessor.extract_lines(test_text)
    print(f"Lines: {lines}\n")

    # Get statistics
    stats = TextProcessor.get_statistics(test_text)
    print(f"Statistics: {stats}")


def test_ocr_processor():
    """Test OCRProcessor functionality."""
    print("\n" + "="*50)
    print("Testing OCRProcessor")
    print("="*50)

    try:
        processor = OCRProcessor()
        print("OCRProcessor initialized successfully")

        # List supported formats
        print(f"Image handler initialized: {processor.image_handler is not None}")
        print(f"File handler initialized: {processor.file_handler is not None}")
        print(f"OCR engine initialized: {processor.ocr_engine is not None}")

    except Exception as e:
        print(f"Error initializing OCRProcessor: {str(e)}")


def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("  Google OCR Tool - Test Suite")
    print("="*50)

    test_image_handler()
    test_file_handler()
    test_text_processor()
    test_ocr_processor()

    print("\n" + "="*50)
    print("  All tests completed!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
