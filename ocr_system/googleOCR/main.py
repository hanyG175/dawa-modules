"""
Main entry point for Google OCR Tool
Provides CLI interface for OCR operations
"""

import sys
import os
import warnings
from pathlib import Path

# Suppress Google API warnings
warnings.filterwarnings('ignore')

from ocr_processor import OCRProcessor
from utils import TextProcessor, FileHandler


def print_menu():
    """Display the main menu."""
    print("\n" + "="*50)
    print("       Google OCR Tool - Main Menu")
    print("="*50)
    print("1. Process single image")
    print("2. Batch process images from directory")
    print("3. Extract and display text from image")
    print("4. Get text statistics")
    print("5. Save results to file")
    print("6. Exit")
    print("="*50)


def process_single_image():
    """Process a single image."""
    image_path = input("\nEnter image file path: ").strip()

    if not os.path.exists(image_path):
        print(f"Error: File not found - {image_path}")
        return

    try:
        processor = OCRProcessor()
        print("\nProcessing image...")
        result = processor.process_image(image_path)

        print("\n" + "-"*50)
        print("OCR Processing Complete!")
        print("-"*50)
        print(f"File: {result['file']}")
        print(f"Output file: {result['output_file']}")
        print(f"Status: {result['status']}")
        print("-"*50)
        print("Extracted Text:")
        print("-"*50)
        print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
        print("-"*50)

    except Exception as e:
        print(f"Error: {str(e)}")


def batch_process_images():
    """Batch process images from a directory."""
    directory = input("\nEnter directory path: ").strip()

    if not os.path.isdir(directory):
        print(f"Error: Directory not found - {directory}")
        return

    try:
        processor = OCRProcessor()
        print(f"\nProcessing images from: {directory}")
        results = processor.batch_process_images(directory)

        print("\n" + "-"*50)
        print("Batch Processing Results:")
        print("-"*50)

        for i, result in enumerate(results, 1):
            status = result.get("status", "unknown")
            file = result.get("file", "unknown")
            print(f"{i}. {file} - {status}")
            if status == "error":
                print(f"   Error: {result.get('error', 'Unknown error')}")

        print("-"*50)
        print(f"Total: {len(results)} files processed")

    except Exception as e:
        print(f"Error: {str(e)}")


def extract_text():
    """Extract and display text from image."""
    image_path = input("\nEnter image file path: ").strip()

    if not os.path.exists(image_path):
        print(f"Error: File not found - {image_path}")
        return

    try:
        processor = OCRProcessor()
        print("\nExtracting text...")
        text = processor.get_extracted_text(image_path)

        print("\n" + "="*50)
        print("Extracted Text:")
        print("="*50)
        print(text)
        print("="*50)

    except Exception as e:
        print(f"Error: {str(e)}")


def show_statistics():
    """Show text statistics."""
    image_path = input("\nEnter image file path: ").strip()

    if not os.path.exists(image_path):
        print(f"Error: File not found - {image_path}")
        return

    try:
        processor = OCRProcessor()
        print("\nExtracting text...")
        text = processor.get_extracted_text(image_path)

        stats = TextProcessor.get_statistics(text)

        print("\n" + "="*50)
        print("Text Statistics:")
        print("="*50)
        print(f"Total Characters: {stats['characters']}")
        print(f"Total Words: {stats['words']}")
        print(f"Total Lines: {stats['lines']}")
        print(f"Average Word Length: {stats['average_word_length']:.2f}")
        print("="*50)

    except Exception as e:
        print(f"Error: {str(e)}")


def save_results():
    """Save OCR results to file."""
    image_path = input("\nEnter image file path: ").strip()
    output_path = input("Enter output file path (leave empty for default): ").strip()

    if not os.path.exists(image_path):
        print(f"Error: File not found - {image_path}")
        return

    try:
        processor = OCRProcessor()
        print("\nProcessing image...")
        result = processor.process_image(image_path)

        if output_path:
            saved_path = processor.save_results(result, output_path)
        else:
            saved_path = processor.save_results(result)

        print(f"\nResults saved to: {saved_path}")

    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    """Main function to run the OCR tool."""
    print("\n" + "="*50)
    print("  Welcome to Google OCR Tool v1.0")
    print("="*50)

    while True:
        print_menu()
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            process_single_image()
        elif choice == "2":
            batch_process_images()
        elif choice == "3":
            extract_text()
        elif choice == "4":
            show_statistics()
        elif choice == "5":
            save_results()
        elif choice == "6":
            print("\nThank you for using Google OCR Tool!")
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()
