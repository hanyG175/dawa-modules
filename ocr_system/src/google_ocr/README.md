# Google Drive OCR adapter

`GoogleDriveOCRModule` is the only OCR implementation in this application. It accepts image or PDF bytes, creates a temporary local file, sends it through the Google Drive OCR workflow, reads the exported text, and removes temporary files.

```python
from src.google_ocr import GoogleDriveOCRModule

ocr = GoogleDriveOCRModule()
result = ocr.extract_from_bytes("notice.pdf", pdf_bytes)

if result.success:
    print(result.text)
```

Supported extensions are `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`, and `.pdf`. OAuth credentials belong in the ignored `credentials/` directory. Configure alternate filenames with `GOOGLE_OCR_CREDENTIALS_DIR`, `GOOGLE_OCR_CLIENT_SECRET_FILE`, and `GOOGLE_OCR_TOKEN_FILE`.
