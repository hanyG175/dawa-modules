"""
Utility functions for OCR tool
"""

import os
from pathlib import Path


class ImageHandler:
    """Handle image file operations."""

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}

    @classmethod
    def is_valid_image(cls, file_path):
        """
        Check if file is a valid image.

        Args:
            file_path (str): Path to file

        Returns:
            bool: True if valid image format
        """
        if not os.path.exists(file_path):
            return False

        extension = Path(file_path).suffix.lower()
        return extension in cls.SUPPORTED_FORMATS

    @classmethod
    def get_image_files(cls, directory):
        """
        Get all image files from a directory.

        Args:
            directory (str): Path to directory

        Returns:
            list: List of image file paths
        """
        image_files = []
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and cls.is_valid_image(file_path):
                image_files.append(file_path)
        return sorted(image_files)

    @classmethod
    def get_image_info(cls, file_path):
        """
        Get information about an image file.

        Args:
            file_path (str): Path to image file

        Returns:
            dict: File information
        """
        if not os.path.exists(file_path):
            return None

        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "extension": Path(file_path).suffix,
            "exists": True
        }


class FileHandler:
    """Handle file read/write operations."""

    @staticmethod
    def read_file(file_path, encoding="utf-8"):
        """
        Read file content.

        Args:
            file_path (str): Path to file
            encoding (str): File encoding

        Returns:
            str: File content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    def write_file(file_path, content, encoding="utf-8"):
        """
        Write content to file.

        Args:
            file_path (str): Path to file
            content (str): Content to write
            encoding (str): File encoding

        Returns:
            str: Path to written file
        """
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)

        return file_path

    @staticmethod
    def append_file(file_path, content, encoding="utf-8"):
        """
        Append content to file.

        Args:
            file_path (str): Path to file
            content (str): Content to append
            encoding (str): File encoding

        Returns:
            str: Path to file
        """
        with open(file_path, "a", encoding=encoding) as f:
            f.write(content)

        return file_path

    @staticmethod
    def file_exists(file_path):
        """
        Check if file exists.

        Args:
            file_path (str): Path to file

        Returns:
            bool: True if file exists
        """
        return os.path.exists(file_path)

    @staticmethod
    def delete_file(file_path):
        """
        Delete a file.

        Args:
            file_path (str): Path to file

        Returns:
            bool: True if successful
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    @staticmethod
    def get_file_info(file_path):
        """
        Get information about a file.

        Args:
            file_path (str): Path to file

        Returns:
            dict: File information
        """
        if not os.path.exists(file_path):
            return None

        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "extension": Path(file_path).suffix,
            "exists": True
        }


class TextProcessor:
    """Process and clean extracted text."""

    @staticmethod
    def clean_text(text):
        """
        Clean extracted text.

        Args:
            text (str): Raw text

        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        lines = [line.strip() for line in text.split("\n")]
        # Remove empty lines
        lines = [line for line in lines if line]
        return "\n".join(lines)

    @staticmethod
    def extract_words(text):
        """
        Extract words from text.

        Args:
            text (str): Text content

        Returns:
            list: List of words
        """
        return text.split()

    @staticmethod
    def extract_lines(text):
        """
        Extract lines from text.

        Args:
            text (str): Text content

        Returns:
            list: List of lines
        """
        return text.split("\n")

    @staticmethod
    def get_statistics(text):
        """
        Get text statistics.

        Args:
            text (str): Text content

        Returns:
            dict: Text statistics
        """
        words = text.split()
        lines = text.split("\n")

        return {
            "characters": len(text),
            "words": len(words),
            "lines": len(lines),
            "average_word_length": sum(len(w) for w in words) / len(words) if words else 0
        }
