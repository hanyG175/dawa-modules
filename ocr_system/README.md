# OCR System - Production-Ready Document and Image Processing

A standalone, modular OCR system for extracting text from drug notices (PDFs) and user-uploaded images (prescriptions/medicine photos). Designed to work independently with clean integration points for external cleaning/validation and search modules.

## Overview

This system handles two primary use cases:

1. **Drug Notice Processing**: Automatically read PDFs with drug information, extract structured data, and pass to cleaning/validation module
2. **User Upload Processing**: Users upload prescription/medicine images, system extracts medicine names and prescriptions, searches database for matches

## Quick Start

### Installation

```bash
# Navigate to ocr_system directory
cd ocr_system

# Install dependencies
pip install -r requirements.txt

# Ensure Tesseract is installed on your system:
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
```

### Basic Usage

```python
from src.ocr import StandardOCRPipeline, MockDataCleaner, MockSearchEngine

# Initialize pipeline
pipeline = StandardOCRPipeline()

# Use Case 1: Process drug notice PDF with cleaning
pipeline.register_data_cleaner(MockDataCleaner())
results = pipeline.process_and_clean("path/to/drug_notice.pdf")

# Use Case 2: Process user upload with search
pipeline.register_search_engine(MockSearchEngine())
results = pipeline.process_and_search("path/to/prescription.jpg")
```

## Architecture

### Components

- **OCREngine**: Tesseract-based text extraction with multi-language support
- **PDFProcessor**: Converts PDFs to images (configurable 150-600 DPI)
- **ImageProcessor**: Validates, enhances, and denoises images for OCR
- **DataExtractor**: Extracts medicine names, dosage, and structured fields
- **StandardOCRPipeline**: Orchestrates components and integrates external modules

### Project Structure

```
ocr_system/
├── requirements.txt              # Dependencies
├── README.md                      # This file
├── QUICK_START.md                # Quick reference (5 min read)
├── ARCHITECTURE.md                # Detailed architecture with diagrams
├── INTEGRATION_GUIDE.md           # How to integrate your modules
├── examples.py                    # 5 working examples
└── src/
    ├── __init__.py
    └── ocr/
        ├── __init__.py           # Public API
        ├── interfaces.py         # Abstract interfaces for external modules
        ├── ocr_engine.py         # Tesseract OCR
        ├── pipeline.py           # Main orchestration
        ├── data_extraction.py    # Data structuring
        ├── mocks.py              # Mock implementations for testing
        └── processors/
            ├── __init__.py       # Base processor
            ├── pdf_processor.py  # PDF handling
            └── image_processor.py # Image handling
```

## Use Cases

### Use Case 1: Drug Notices (PDF Processing)

```python
from src.ocr import StandardOCRPipeline
from your_module import YourDataCleaner

pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(YourDataCleaner())

# Process PDF through cleaning pipeline
cleaned_results = pipeline.process_and_clean("drug_notice.pdf")

# Store cleaned data
for data in cleaned_results:
    db.insert_drug(data)
```

**Data Flow:**
```
PDF → PDFProcessor → OCREngine → DataExtractor → YourDataCleaner → Database
```

### Use Case 2: User Uploads (Image Processing)

```python
from src.ocr import StandardOCRPipeline
from your_module import YourSearchEngine

pipeline = StandardOCRPipeline()
pipeline.register_search_engine(YourSearchEngine())

# Process image and search
search_results = pipeline.process_and_search("prescription.jpg")

# Display results to user
for drug in search_results:
    show_to_user(drug)
```

**Data Flow:**
```
Image → ImageProcessor → OCREngine → DataExtractor → YourSearchEngine → Results
```

## Integration

### For Data Cleaner Team

Implement `DataCleanerInterface`:

```python
from src.ocr import DataCleanerInterface, ExtractedData

class YourDataCleaner(DataCleanerInterface):
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        # Your cleaning logic
        return cleaned_data
    
    def validate(self, data: Dict[str, Any]) -> bool:
        # Your validation logic
        return is_valid
```

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for complete details.

### For Search Engine Team

Implement `SearchEngineInterface`:

```python
from src.ocr import SearchEngineInterface

class YourSearchEngine(SearchEngineInterface):
    def search(self, query: str) -> List[Dict[str, Any]]:
        # Your search logic
        return results
    
    def search_by_medicine_name(self, name: str) -> List[Dict[str, Any]]:
        # Your medicine name search
        return results
```

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for complete details.

## Features

✅ **Production Ready:**
- Comprehensive error handling
- Full logging support
- Input validation
- Type hints throughout
- Docstrings on all functions

✅ **Best Practices:**
- Abstract interfaces for loose coupling
- Mock implementations included
- Modular design
- Dependency injection support

✅ **Flexible Configuration:**
- Adjustable PDF DPI (150-600)
- Multi-language OCR support
- Image enhancement options
- Custom extraction patterns

## Dependencies

- `pytesseract==0.3.10` - OCR engine interface
- `pillow==10.1.0` - Image processing
- `pdf2image==1.17.0` - PDF to image conversion
- `opencv-python==4.8.1.78` - Advanced image filtering
- `numpy==1.24.3` - Numerical operations

System-level:
- Tesseract OCR (required for OCREngine)

## Documentation

Start with:
1. **[QUICK_START.md](./QUICK_START.md)** - 5-minute overview
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and design
3. **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Integration instructions
4. **[examples.py](./examples.py)** - Working code examples

## Testing

Mock implementations are provided for development without external modules:

```python
from src.ocr import MockDataCleaner, MockSearchEngine

# Use mocks for testing
cleaner = MockDataCleaner()
search = MockSearchEngine()
```

Run examples:

```bash
python examples.py
```

## Performance

- **PDF Conversion**: 0.5-2s per page (depends on DPI)
- **OCR**: 1-5s per page (depends on complexity)
- **Image Enhancement**: ~0.5s per image
- **Data Extraction**: <0.1s

Optimization tips:
- Use DPI 150 for speed, 300 for standard, 600 for high quality
- Disable image enhancement if speed is critical
- Batch processing for multiple documents
- Cache OCR results when possible

## Support

For questions and issues:
- See [QUICK_START.md](./QUICK_START.md) - FAQ section
- See [ARCHITECTURE.md](./ARCHITECTURE.md) - Design patterns
- See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) - Integration help
- Check docstrings in source code

## File Sizes

| Component | Size |
|-----------|------|
| ocr_engine.py | ~350 lines |
| pipeline.py | ~300 lines |
| data_extraction.py | ~350 lines |
| processors/pdf_processor.py | ~200 lines |
| processors/image_processor.py | ~350 lines |
| mocks.py | ~150 lines |
| interfaces.py | ~150 lines |
| **Total Code** | **~2000 lines** |

Plus comprehensive documentation (~2000+ lines)

## Next Steps

1. **Now**: Install and run examples
2. **Review**: Check ARCHITECTURE.md for design
3. **Plan**: Implement your cleaner module
4. **Integrate**: Follow INTEGRATION_GUIDE.md
5. **Test**: Use mock modules first
6. **Deploy**: Replace mocks with real modules

## License

Part of the PFE Semantic Drug Search Engine project.

---

**Ready to use.** Start with [QUICK_START.md](./QUICK_START.md) →
