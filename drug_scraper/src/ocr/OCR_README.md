# OCR System Documentation

## Overview

A modular, production-ready OCR system for extracting text from drug notices and user uploads. Designed to work independently while seamlessly integrating with external cleaning/validation and search modules.

## Architecture

### Components

1. **OCREngine** (`ocr_engine.py`)
   - Tesseract-based text extraction
   - Multi-language support
   - Confidence scoring
   - Detailed extraction with word-level confidence

2. **PDF Processor** (`processors/pdf_processor.py`)
   - Converts PDF pages to images (configurable DPI)
   - Page-by-page processing
   - Format validation

3. **Image Processor** (`processors/image_processor.py`)
   - Validates and loads images
   - Automatic quality enhancement for OCR
   - Size and format validation
   - Denoising and contrast enhancement

4. **Data Extractor** (`data_extraction.py`)
   - Extracts medicine names using pattern matching
   - Identifies prescription/dosage information
   - Extracts structured fields (manufacturer, indications, contraindications, etc.)
   - Formats data for downstream modules

5. **OCR Pipeline** (`pipeline.py`)
   - Coordinates all components
   - Manages external module integration
   - Provides high-level APIs for both use cases

## Use Cases

### Use Case 1: Processing Drug Notices (PDFs)

```python
from src.ocr import StandardOCRPipeline, MockDataCleaner

# Initialize
pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(MyDataCleaner())

# Process with cleaning
cleaned_results = pipeline.process_and_clean("drug_notice.pdf")

# Results are cleaned and validated
for data in cleaned_results:
    save_to_database(data)
```

**Workflow:**
1. User/system provides PDF
2. OCR system extracts text from all pages
3. Sends extracted data to cleaning/validation module
4. Cleaned data is stored

### Use Case 2: User Uploads (Prescriptions/Medicine Names)

```python
from src.ocr import StandardOCRPipeline, MockSearchEngine

# Initialize
pipeline = StandardOCRPipeline()
pipeline.register_search_engine(MySearchEngine())

# Process with search
results = pipeline.process_and_search("prescription.jpg")

# Display results to user
for drug in results:
    display_drug_info(drug)
```

**Workflow:**
1. User uploads image
2. OCR extracts medicine names/prescription text
3. Searches database for matching drugs
4. Returns results to user

## External Module Integration

### 1. Data Cleaner Integration

Implement the `DataCleanerInterface`:

```python
from src.ocr import DataCleanerInterface, ExtractedData

class YourDataCleaner(DataCleanerInterface):
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        # Your cleaning logic
        return cleaned_data
    
    def validate(self, data: Dict[str, Any]) -> bool:
        # Your validation logic
        return is_valid

# Register with pipeline
pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(YourDataCleaner())
```

### 2. Search Engine Integration

Implement the `SearchEngineInterface`:

```python
from src.ocr import SearchEngineInterface

class YourSearchEngine(SearchEngineInterface):
    def search(self, query: str) -> List[Dict[str, Any]]:
        # Your search logic
        return results
    
    def search_by_medicine_name(self, name: str) -> List[Dict[str, Any]]:
        # Specific medicine name search
        return results

# Register with pipeline
pipeline = StandardOCRPipeline()
pipeline.register_search_engine(YourSearchEngine())
```

## Component Usage

### OCREngine

```python
from src.ocr import OCREngine
from PIL import Image

# Initialize with multiple languages
ocr = OCREngine(languages=['eng', 'fra'])

# Load image
image = Image.open("document.jpg")

# Extract text
result = ocr.extract_text(image)
print(result['text'])
print(f"Confidence: {result['confidence']:.2%}")

# Detailed extraction with word-level confidence
detailed = ocr.extract_text_with_confidence(image)

# Structured extraction
structured = ocr.extract_structured_data(image)
```

### PDF Processor

```python
from src.ocr import PDFProcessor

# Initialize with DPI setting
pdf_proc = PDFProcessor(dpi=300)

# Convert PDF to images
images = pdf_proc.process("drug_notice.pdf")
print(f"Converted {len(images)} pages")

# Get page count
page_count = pdf_proc.get_page_count("drug_notice.pdf")
```

### Image Processor

```python
from src.ocr import ImageProcessor

# Initialize with enhancement
img_proc = ImageProcessor(enhance_quality=True)

# Process image
image = img_proc.process("prescription.jpg")

# Get image info
info = img_proc.get_image_info("prescription.jpg")
print(f"Size: {info['size']}")
print(f"Format: {info['format']}")
```

### Data Extractor

```python
from src.ocr import DataExtractor
from src.ocr import OCRResult

extractor = DataExtractor()

# Create OCR result
ocr_result = OCRResult(
    raw_text=extracted_text,
    confidence=0.92,
    source_type="pdf",
    metadata={"page": 1}
)

# Extract structured data
extracted = extractor.extract_from_ocr_result(ocr_result)
print(extracted.medicine_names)
print(extracted.prescription_info)
print(extracted.extracted_fields)

# Format for cleaner module
cleaner_data = extractor.format_for_cleaner(extracted)

# Format for search module
search_data = extractor.format_for_search(extracted)
```

## Data Models

### OCRResult
```python
@dataclass
class OCRResult:
    raw_text: str           # Raw extracted text
    confidence: float       # 0-1 confidence score
    source_type: str        # "pdf" or "image"
    metadata: Dict[str, Any]  # Additional metadata
```

### ExtractedData
```python
@dataclass
class ExtractedData:
    medicine_names: List[str]        # Extracted medicine names
    prescription_info: Optional[str]  # Dosage, administration info
    raw_text: str                     # Original OCR text
    extracted_fields: Dict[str, Any]  # Structured data (manufacturer, etc.)
    metadata: Dict[str, Any]          # Processing metadata
```

## Configuration

### Multi-language Support

```python
from src.ocr import OCREngine

# Initialize with specific languages
ocr = OCREngine(languages=['eng', 'fra', 'deu'])

# Add language dynamically
ocr.add_language('spa')

# Set complete language list
ocr.set_languages(['eng', 'fra'])
```

### Image Enhancement

```python
from src.ocr import ImageProcessor

# Enable enhancement (default)
img_proc = ImageProcessor(enhance_quality=True)

# Enhancement includes:
# - Denoising
# - Grayscale conversion
# - Contrast enhancement (CLAHE)
# - Thresholding
```

### PDF Quality

```python
from src.ocr import PDFProcessor

# Higher DPI = better quality but slower
pdf_proc = PDFProcessor(dpi=300)  # Default: 300
pdf_proc = PDFProcessor(dpi=150)  # Faster, lower quality
pdf_proc = PDFProcessor(dpi=600)  # High quality, slower
```

## Dependencies

- **pytesseract**: OCR engine interface
- **pillow**: Image processing
- **pdf2image**: PDF conversion
- **opencv-python**: Advanced image enhancement
- **numpy**: Numerical operations

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Error Handling

All components include comprehensive error handling:

```python
from src.ocr import StandardOCRPipeline

pipeline = StandardOCRPipeline()

try:
    results = pipeline.process_pdf("drug_notice.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Processing error: {e}")
```

## Testing & Mock Modules

For development and testing without external modules:

```python
from src.ocr import MockDataCleaner, MockSearchEngine

# Use mocks for testing
cleaner = MockDataCleaner()
search_engine = MockSearchEngine()

pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(cleaner)
pipeline.register_search_engine(search_engine)
```

## Performance Notes

1. **PDF Processing**: Convert high-resolution PDFs at appropriate DPI (300 is standard)
2. **Image Enhancement**: Takes ~500ms per image, can be disabled for speed
3. **OCR Accuracy**: Depends on image quality - enhancement helps significantly
4. **Multi-threading**: Pipeline can be run in parallel for batch processing

## Logging

All components use Python's logging module:

```python
import logging
from src.utils.logger import setup_logger

logger = setup_logger("ocr_system", log_level="DEBUG")
```

## Best Practices

1. **Always validate input files** before processing
2. **Handle exceptions** - file operations can fail
3. **Register external modules early** before processing
4. **Use appropriate image quality** - balance speed vs accuracy
5. **Cache OCR results** for frequently used documents
6. **Log all operations** for debugging
7. **Test with mocks first** before integrating real modules

## Future Enhancements

- Handwriting recognition support
- Layout detection and structure preservation
- Document segmentation
- Batch processing with progress tracking
- Results caching
- Database integration
- Web API wrapper
