# OCR system

This application contains the Google Drive OCR workstream for the project. It accepts PDFs, scans, medicine images, and prescriptions, uploads them temporarily to Google Drive as Google Docs, and reads the exported plain text response.

## Responsibilities

- Send supported files through the Google Drive OCR workflow.
- Clean up temporary local input and text files after processing.
- Provide a small `GoogleDriveOCRModule` API for bytes and PDF batches.
- Expose the combined Flask application under `src/web`.

The OCR system does not own the drug search index or final clinical validation rules. Those remain integration boundaries in the DDI and data-cleaning workstreams.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a Google Cloud OAuth client for Google Drive and place the client secret and token in an ignored `credentials/` directory. Copy `.env.example` to `.env` if you need to change the credential directory or filenames.

The default environment values are:

```text
GOOGLE_OCR_CREDENTIALS_DIR=credentials
GOOGLE_OCR_CLIENT_SECRET_FILE=client_secret.json
GOOGLE_OCR_TOKEN_FILE=drive-python-quickstart.json
```

## Run

From this directory:

```powershell
python src\web\app.py
```

The Flask app runs on `http://127.0.0.1:5000` by default. It exposes `/api/extract` for one uploaded file and the combined DDI routes.

## Python API

```python
from src.google_ocr import GoogleDriveOCRModule

ocr = GoogleDriveOCRModule()
with open("examples/prescription.jpg", "rb") as file:
	result = ocr.extract_from_bytes("prescription.jpg", file.read())
print(result.text)
```

The pipeline intentionally returns structured OCR output without requiring the unfinished cleaning or search services. See `src/ocr/interfaces.py` for the contracts those services must implement.

## Layout

```text
src/
├── google_ocr/          Google Drive OCR adapter and result model
├── core/                Parsing, normalization, DDI, and LLM support
└── web/                 Combined OCR/DDI Flask app
```

Local datasets, credentials, logs, result exports, virtual environments, and caches are development artifacts. They are ignored and should not be published.
