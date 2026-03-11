# PaddleOCR Implementation

Simple, lightweight PaddleOCR wrapper for text extraction from PDFs and images.

## Installation

```bash
pip install paddleocr
```

## Quick Start

### Basic Image OCR

```python
from src.paddle_ocr.paddle_engine import PaddleEngine

engine = PaddleEngine()
result = engine.extract_text("document.jpg")
print(result["text"])
```

### Pipeline (PDF & Images)

```python
from src.paddle_ocr.paddle_pipeline import PaddleOCRPipeline

pipeline = PaddleOCRPipeline()
result = pipeline.process_document("document.pdf")
print(result["text"])
```

## API

### PaddleEngine

#### `extract_text(image_path: str) -> Dict`
Extract text from a single image.

Returns dict with:
- `text`: Extracted text
- `confidence`: Average confidence (0-1)
- `success`: Boolean

```python
result = engine.extract_text("image.jpg")
if result["success"]:
    print(result["text"])
```

### PaddleOCRPipeline

#### `process_document(file_path: str) -> Dict`
Process PDF or image file.

Returns dict with:
- `success`: Processing success status
- `text`: Extracted text
- `source_type`: "pdf" or "image"
- `page_count`: For PDFs, number of pages

```python
result = pipeline.process_document("file.pdf")
if result["success"]:
    print(result["text"])
```

## Features

- ✅ Multi-language support (40+ languages)
- ✅ Automatic text angle detection
- ✅ PDF to image conversion included
- ✅ Optional GPU acceleration
- ✅ Simple, focused API

## Configuration

```python
# Default English
engine = PaddleEngine()

# Multiple languages
engine = PaddleEngine(languages=["en", "ar", "fr"])

# GPU support
engine = PaddleEngine(use_gpu=True)
```

## Supported Languages

- English (en), Arabic (ar), French (fr), Chinese (zh)
- Russian (ru), Japanese (ja), Korean (ko), German (de), Spanish (es)
- And 30+ more languages

See [PaddleOCR docs](https://github.com/PaddlePaddle/PaddleOCR) for full list.

## Integration

Works with existing OCR pipeline using:
- `PDFProcessor` for PDF handling
- `ImageProcessor` for image preprocessing

