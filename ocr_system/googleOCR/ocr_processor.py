"""
OCR Processor - Main orchestrator for OCR operations
"""

import os
from pathlib import Path
from GoogleOCR import GoogleOCR
from utils import ImageHandler, FileHandler


class OCRProcessor:
    """
    Main class for processing OCR tasks.
    Handles image files, PDFs, and manages the OCR workflow.
    """

    def __init__(self):
        """Initialize the OCR processor with Google OCR engine."""
        self.ocr_engine = GoogleOCR()
        self.image_handler = ImageHandler()
        self.file_handler = FileHandler()

    def process_image(self, image_path, output_format="txt"):
        """
        Process a single image file for OCR.

        Args:
            image_path (str): Path to the image file
            output_format (str): Output format ('txt' or 'json')

        Returns:
            dict: Extracted text and metadata
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Validate image
        if not self.image_handler.is_valid_image(image_path):
            raise ValueError(f"Invalid image format: {image_path}")

        # Get base name without extension
        base_name = Path(image_path).stem

        try:
            # Run OCR
            self.ocr_engine.run(base_name)

            # Read extracted text
            output_file = f"{base_name}.txt"
            if os.path.exists(output_file):
                extracted_text = self.file_handler.read_file(output_file)

                result = {
                    "status": "success",
                    "file": image_path,
                    "text": extracted_text,
                    "output_file": output_file,
                    "format": output_format
                }

                return result
            else:
                raise Exception(f"Output file not created: {output_file}")

        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")

    def batch_process_images(self, image_directory, output_format="txt"):
        """
        Process multiple images in a directory.

        Args:
            image_directory (str): Path to directory containing images
            output_format (str): Output format

        Returns:
            list: Results for each image
        """
        if not os.path.isdir(image_directory):
            raise ValueError(f"Directory not found: {image_directory}")

        results = []
        image_files = self.image_handler.get_image_files(image_directory)

        for image_file in image_files:
            try:
                result = self.process_image(image_file, output_format)
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "file": image_file,
                    "error": str(e)
                })

        return results

    def get_extracted_text(self, image_path):
        """
        Get extracted text from an image.

        Args:
            image_path (str): Path to image file

        Returns:
            str: Extracted text
        """
        result = self.process_image(image_path)
        return result["text"]

    def save_results(self, result, output_path=None):
        """
        Save OCR results to file.

        Args:
            result (dict): OCR result
            output_path (str): Path to save results

        Returns:
            str: Path to saved file
        """
        if output_path is None:
            base_name = Path(result["file"]).stem
            output_path = f"{base_name}_ocr_result.txt"

        self.file_handler.write_file(output_path, result["text"])
        return output_path
