# Google Drive OCR Module

## What this provides
- Single-file OCR for images and PDFs
- Batch OCR for PDFs
- Modern visual demo interface (Streamlit)
- In-memory workflow for uploads (temporary files are cleaned up)

## Main files
- src/google_drive_ocr/service.py : OCR module API
- src/google_drive_ocr/demo_app.py : visual upload interface
- run_google_ocr_demo.py : run the demo by executing this file directly

## How to use in code
```python
from src.google_drive_ocr import GoogleDriveOCRModule

ocr = GoogleDriveOCRModule()
result = ocr.extract_from_bytes("sample.png", image_bytes)

if result.success:
    print(result.text)
```

## Demo
Run the file directly from VS Code:
- run_google_ocr_demo.py

Then upload an image/PDF, or multiple PDFs in batch tab.
