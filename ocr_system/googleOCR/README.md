# Google OCR Tool

A comprehensive OCR (Optical Character Recognition) tool using Google Drive API for extracting text from images.

## Features

- **Single Image Processing**: Process individual image files for text extraction
- **Batch Processing**: Process multiple images from a directory at once
- **Multiple Image Formats**: Support for PNG, JPG, JPEG, BMP, GIF, and TIFF formats
- **Text Statistics**: Get detailed statistics about extracted text
- **File Management**: Easy file reading, writing, and management
- **CLI Interface**: User-friendly command-line interface
- **Error Handling**: Comprehensive error handling and validation

## Project Structure

```
googleOCR/
├── __init__.py              # Package initialization
├── GoogleOCR.py             # Google Drive API integration
├── ocr_processor.py         # Main OCR processing logic
├── utils.py                 # Utility classes and functions
├── main.py                  # CLI entry point
├── drive-python-quickstart.json  # Google API credentials
└── README.md                # This file
```

## Components

### GoogleOCR
Core class for Google Drive API integration. Handles authentication and text extraction.

### OCRProcessor
Main orchestrator for OCR operations. Provides high-level API for:
- Single image processing
- Batch image processing
- Text extraction
- Results management

### ImageHandler
Utility class for image file operations:
- Image format validation
- Image file discovery
- Image metadata extraction

### FileHandler
Utility class for file operations:
- File reading/writing
- File existence checking
- File metadata extraction
- File deletion

### TextProcessor
Utility class for text processing:
- Text cleaning
- Word/line extraction
- Text statistics generation

## Usage

### Command Line Interface

Run the tool with:
```bash
python main.py
```

This opens an interactive menu with options:
1. Process single image
2. Batch process images from directory
3. Extract and display text from image
4. Get text statistics
5. Save results to file
6. Exit

### Programmatic Usage

```python
from ocr_processor import OCRProcessor

# Initialize processor
processor = OCRProcessor()

# Process single image
result = processor.process_image("path/to/image.png")
print(result["text"])

# Batch process
results = processor.batch_process_images("path/to/image_directory")

# Get extracted text directly
text = processor.get_extracted_text("path/to/image.png")

# Save results
output_path = processor.save_results(result, "output.txt")
```

## Requirements

- Python 3.7+
- google-api-python-client
- oauth2client
- httplib2

## Setup

1. Install dependencies:
```bash
pip install google-api-python-client oauth2client httplib2
```

2. Ensure `drive-python-quickstart.json` contains valid Google API credentials

3. Run the tool:
```bash
python main.py
```

## Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- Bitmap (.bmp)
- GIF (.gif)
- TIFF (.tiff)

## Error Handling

The tool includes comprehensive error handling for:
- Missing files
- Invalid image formats
- API authentication failures
- File writing errors
- Invalid directory paths

## API Reference

### OCRProcessor

#### `process_image(image_path, output_format="txt")`
Process a single image file.
- **Parameters**: image_path (str), output_format (str)
- **Returns**: dict with status, text, and metadata

#### `batch_process_images(image_directory, output_format="txt")`
Process multiple images from a directory.
- **Parameters**: image_directory (str), output_format (str)
- **Returns**: list of result dictionaries

#### `get_extracted_text(image_path)`
Get extracted text from an image.
- **Parameters**: image_path (str)
- **Returns**: str (extracted text)

#### `save_results(result, output_path=None)`
Save OCR results to file.
- **Parameters**: result (dict), output_path (str)
- **Returns**: str (path to saved file)

## Notes

- The tool creates `.txt` files with extracted text during processing
- Temporary files are cleaned up after processing
- All operations are logged in the output
- The tool supports UTF-8 encoding for text files

## Troubleshooting

**Issue**: Authentication fails
- **Solution**: Verify `drive-python-quickstart.json` contains valid credentials

**Issue**: Image format not supported
- **Solution**: Convert image to PNG, JPG, BMP, GIF, or TIFF format

**Issue**: Google Drive API quota exceeded
- **Solution**: Wait before processing more images or upgrade API quota

## Version

1.0.0

## License

MIT
