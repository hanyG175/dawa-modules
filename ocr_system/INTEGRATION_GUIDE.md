# OCR integration guide

The OCR boundary is intentionally small. The application exposes one adapter, `GoogleDriveOCRModule`, and leaves cleaning, validation, search, and DDI analysis to downstream components.

## Extract a file

```python
from src.google_ocr import GoogleDriveOCRModule

ocr = GoogleDriveOCRModule()
result = ocr.extract_from_bytes("prescription.jpg", image_bytes)

if not result.success:
    raise RuntimeError(result.error)

raw_text = result.text
```

`OCRResult` contains `file_name`, `file_type`, `text`, `characters`, `words`, `success`, and an optional `error`.

## Process PDF batches

```python
results = ocr.extract_batch_pdfs([
    ("notice-1.pdf", first_pdf_bytes),
    ("notice-2.pdf", second_pdf_bytes),
])
```

Batch mode accepts PDF files only. Each result should be checked independently because one failed document must not hide successful documents in the same batch.

## Downstream integration

The cleaning and validation module should accept `OCRResult.text` and return its own structured model. The future search engine should consume the validated medicine names or parsed prescription fields. Keeping those modules outside OCR avoids coupling them to Google Drive, OAuth, or temporary-file handling.

## Credentials

Place the Google OAuth client secret and token in `ocr_system/credentials/`, which is ignored by Git. Configure non-default names with:

```text
GOOGLE_OCR_CREDENTIALS_DIR=credentials
GOOGLE_OCR_CLIENT_SECRET_FILE=client_secret.json
GOOGLE_OCR_TOKEN_FILE=drive-python-quickstart.json
```

Never commit these files or real patient documents.
