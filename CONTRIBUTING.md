# Contributing

Thanks for contributing. This repository contains several independent workstreams, so a change should make its intended application obvious.

## Before you start

1. Read the README in the application you are changing.
2. Create or activate the virtual environment for that application.
3. Check `git status` and keep unrelated existing work untouched.
4. Never add credentials, private datasets, generated reports, or virtual environments.

## Making a change

- Keep changes focused on one component.
- Prefer small modules with explicit inputs and outputs.
- Preserve existing public behavior unless the change is intentional and documented.
- Add or update tests for behavior that can be tested without external services.
- Update the relevant README when setup or behavior changes.
- Use lowercase `snake_case` names for Python packages and modules.

## Validation

Run the narrowest useful check first, then the broader check when practical:

```powershell
# Python syntax check for a touched module
python -m compileall path\to\module

# OCR application import check
cd ocr_system
python -c "from src.google_ocr import GoogleDriveOCRModule"
```

For integrations requiring Neo4j, Google Drive, OpenFDA, or an LLM, document the required service and validate the fallback behavior locally when possible.

## Pull requests

Describe:

- what changed and why;
- which application or data workflow it affects;
- how it was validated;
- any credentials, services, or datasets needed to reproduce it;
- known limitations or follow-up work.