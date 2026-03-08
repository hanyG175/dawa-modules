# OCR System - Quick Reference

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Tesseract is installed on your system
# Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
```

## Quick Start - 3 Steps

### Step 1: Basic Setup
```python
from src.ocr import StandardOCRPipeline

pipeline = StandardOCRPipeline()
```

### Step 2: For Drug Notices (PDF)
```python
pipeline.register_data_cleaner(YourDataCleaner())
results = pipeline.process_and_clean("drug_notice.pdf")
```

### Step 3: For User Uploads (Image)
```python
pipeline.register_search_engine(YourSearchEngine())
results = pipeline.process_and_search("prescription.jpg")
```

## Use With Mocks (While developing)

```python
from src.ocr import StandardOCRPipeline, MockDataCleaner, MockSearchEngine

pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(MockDataCleaner())
pipeline.register_search_engine(MockSearchEngine())

# Test without real modules
results = pipeline.process_and_clean("drug_notice.pdf")
```

## Component Overview

| Component | Purpose | Input | Output |
|-----------|---------|-------|--------|
| **PDFProcessor** | Convert PDF → Images | PDF file path | List of PIL Images |
| **ImageProcessor** | Load & enhance images | Image file path | Enhanced PIL Image |
| **OCREngine** | Extract text from images | PIL Image | Text + confidence score |
| **DataExtractor** | Structure extracted data | Raw OCR text | Medicine names, dosage, etc. |
| **StandardOCRPipeline** | Orchestrate everything | PDF/Image path | Cleaned or search results |

## Data Models

```python
# What you send to OCR system
pdf_path: str          # Path to PDF file
image_path: str        # Path to image file

# What you get back from extraction
ExtractedData:
  - medicine_names: List[str]
  - prescription_info: Optional[str]
  - raw_text: str
  - extracted_fields: Dict[str, Any]
  - metadata: Dict[str, Any]

# What you get after cleaning
cleaned_data: Dict[str, Any]  # Your custom structure

# What you get after search
drug_results: List[Dict[str, Any]]  # Drug records
```

## Common Tasks

### Extract text from PDF
```python
from src.ocr import StandardOCRPipeline

pipeline = StandardOCRPipeline()
extracted = pipeline.process_pdf("document.pdf")

for page in extracted:
    print(page.raw_text)
    print(page.medicine_names)
```

### Extract text from image
```python
pipeline = StandardOCRPipeline()
extracted = pipeline.process_image("prescription.jpg")

print(extracted.raw_text)
print(extracted.medicine_names)
```

### Process with cleaning
```python
pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(MyDataCleaner())

results = pipeline.process_and_clean("notice.pdf")
for data in results:
    print(data)  # Cleaned data
```

### Process with search
```python
pipeline = StandardOCRPipeline()
pipeline.register_search_engine(MySearchEngine())

results = pipeline.process_and_search("prescription.jpg")
for drug in results:
    print(f"{drug['name']} - {drug['indication']}")
```

### Using individual components
```python
from src.ocr import OCREngine, PDFProcessor, DataExtractor
from PIL import Image

# PDF to images
pdf_proc = PDFProcessor(dpi=300)
images = pdf_proc.process("document.pdf")

# OCR
ocr = OCREngine(languages=['eng'])
for image in images:
    result = ocr.extract_text(image)
    print(result['text'])

# Extract structure
extractor = DataExtractor()
extracted = extractor.extract_from_ocr_result(result)
print(extracted.medicine_names)
```

## Configuration Options

### OCREngine
```python
OCREngine(
    languages=['eng', 'fra'],  # Supported languages
    config="--psm 3 --oem 3"   # Tesseract config
)
```

### PDFProcessor
```python
PDFProcessor(
    dpi=300  # Quality: 150 (fast), 300 (standard), 600 (high)
)
```

### ImageProcessor
```python
ImageProcessor(
    enhance_quality=True  # Auto enhance for OCR
)
```

## Error Handling

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

## Logging

```python
import logging
from src.utils.logger import setup_logger

logger = setup_logger("ocr", log_level="DEBUG")
pipeline = StandardOCRPipeline()
# All operations logged automatically
```

## Testing

```python
# Run example code
python examples_ocr.py

# Use mocks for testing
from src.ocr import MockDataCleaner, MockSearchEngine

cleaner = MockDataCleaner()
search = MockSearchEngine()
```

## File Structure

```
src/ocr/
├── __init__.py              # Main exports
├── interfaces.py            # Abstract interfaces for external modules
├── ocr_engine.py            # Tesseract-based OCR
├── pipeline.py              # Main orchestration
├── data_extraction.py       # Data structuring
├── mocks.py                 # Mock implementations for testing
├── processors/
│   ├── __init__.py
│   ├── pdf_processor.py     # PDF handling
│   └── image_processor.py   # Image handling
├── OCR_README.md            # Full documentation
└── tests/                   # Unit tests (when ready)
```

## Integration Points

### For Data Cleaner Team
```python
from src.ocr import DataCleanerInterface, ExtractedData

class DataCleaner(DataCleanerInterface):
    def clean(self, data: ExtractedData) -> Dict:
        # Your cleaning logic
        pass
    
    def validate(self, data: Dict) -> bool:
        # Your validation logic
        pass
```

### For Search Engine Team
```python
from src.ocr import SearchEngineInterface

class SearchEngine(SearchEngineInterface):
    def search(self, query: str) -> List[Dict]:
        pass
    
    def search_by_medicine_name(self, name: str) -> List[Dict]:
        pass
```

## Performance Tips

1. **DPI**: Use 300 for standard documents, 150 for speed, 600 for clarity
2. **Enhancement**: Disable if speed is critical
3. **Languages**: Only add languages you need
4. **Batch Processing**: Process multiple files in parallel
5. **Caching**: Cache OCR results for frequently used documents

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tesseract not found | Install from https://github.com/UB-Mannheim/tesseract/wiki |
| Poor OCR accuracy | Increase DPI or enable enhancement |
| Slow processing | Reduce DPI or disable enhancement |
| Import errors | Run `pip install -r requirements.txt` |
| Module not found | Ensure OCR module is in `src/` directory |

## Next Steps

1. **Now**: Use with mock modules to understand the system
2. **When ready**: Implement your cleaner module → integrate it
3. **When ready**: Implement your search engine → integrate it
4. **Production**: Test with real data, optimize for performance

## Need Help?

See:
- [Full Documentation](./src/ocr/OCR_README.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)
- [Examples](./examples_ocr.py)
