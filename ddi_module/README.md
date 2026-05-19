# Standalone DDI Module

This folder is a self-contained version of the DDI workflow.
It keeps the prescription OCR + DDI + LLM flow and removes the old OCR-only landing page.

## Included

- `app.py`: standalone Flask app
- `launch.py`: one-command launcher that works from any folder
- `run_ddi_module.bat`: double-click launcher for Windows
- `templates/ddi_analyzer.html`: prescription/DDI UI
- `core/`: drug normalization, DDI checker, parsing, and LLM engine
- `engines/google_drive/`: Google Drive OCR wrapper
- `data/`: local datasets required by the normalizer

## Not included

- The original OCR-only home page
- Unrelated pages from the main project

## Requirements

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## External setup

The app automatically reads `ddi_module/.env` at startup.

### Google OCR

Put these files in `ddi_module/credentials/`:

- `client_secret_791442723837-7ch74jh2dpavoios3ko118ennk03o51i.apps.googleusercontent.com.json`
- `drive-python-quickstart.json`

### Neo4j

Set one of these combinations:

- `NEO4J_URI`
- `NEO4J_USER` or `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE` (optional)

### LLM

Optional, for the Qwen clinical report:

- `LLM_API_KEY`
- `LLM_API_URL` (optional)
- `LLM_MODEL` (optional)

## Run

Preferred launcher:

```bash
python launch.py
```

Or on Windows:

```bat
run_ddi_module.bat
```

Then open:

- [http://127.0.0.1:5000/ddi](http://127.0.0.1:5000/ddi)

## Behavior

- If Google OCR credentials are missing, uploads return a clear error.
- If Neo4j env vars are missing, the checker falls back to OpenFDA-only mode.
- If `LLM_API_KEY` is missing, the LLM report returns a clear error instead of crashing.

