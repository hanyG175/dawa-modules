# Semantic Drug Search Engine

This repository contains the working parts of a graduation project for a semantic drug search and drug-interaction platform. It is organized as a small monorepo because the project includes several related applications and data workflows rather than one deployable service.

## Repository map

| Directory | Purpose | Status |
| --- | --- | --- |
| [`ocr_system`](ocr_system) | OCR, document parsing, and the OCR web application | Active development |
| [`ddi_module`](ddi_module) | Standalone prescription and drug-drug interaction workflow | Active development |
| [`drug_scraper(drugbank)`](drug_scraper%28drugbank%29) | DrugBank scraping and XML extraction tools | Active development |
| [`data_cleaning`](data_cleaning) | Experimental and production data-cleaning pipelines | Research / data work |
| [`colaboration`](colaboration) | Experimental scraper application and experiments | Experimental |

The Neo4j node and relationship exports used by the DDI workflow live in [`ddi_module/data/neo4j`](ddi_module/data/neo4j). New exports, credentials, caches, virtual environments, and runtime output should not be committed.

## What is currently implemented

- Google Drive OCR for PDFs, scans, prescriptions, and medicine images.
- Drug-name and prescription parsing after OCR.
- A standalone DDI workflow with optional Google OCR, Neo4j, OpenFDA, and LLM integrations.
- DrugBank scraping and streaming XML extraction utilities.
- Data-cleaning pipelines for multilingual drug data.
- An experimental scraper service.

Some integrations are intentionally optional and require external credentials or services. The repository does not pretend that those services are available in a clean checkout.

## Quick start

Each application has its own dependencies. Use a separate virtual environment for each Python application, or install only the component you are working on.

### DDI module

```powershell
cd ddi_module
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python launch.py
```

The app is served at `http://127.0.0.1:5000/ddi`. Google credentials and service configuration are documented in [`ddi_module/README.md`](ddi_module/README.md).

### OCR system

```powershell
cd ocr_system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python src\web\app.py
```

The OCR system requires Google Drive OAuth credentials. See [`ocr_system/README.md`](ocr_system/README.md).

### Drug scraper

```powershell
cd 'drug_scraper(drugbank)'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --source drugbank --limit 10
```

The full DrugBank XML file is intentionally treated as local input data and should not be uploaded to a public repository.

## Development conventions

- Keep application dependencies in the application directory that uses them.
- Keep credentials in local `.env` files or ignored credential directories. Commit only `.env.example` files.
- Keep generated files under ignored data/output directories; commit small, intentional fixtures only.
- Prefer package-safe names: lowercase letters, numbers, and underscores for Python packages.
- Add tests beside the component they protect, or under a clearly named top-level test suite.
- Do not commit `__pycache__`, virtual environments, `node_modules`, logs, generated reports, or raw proprietary datasets.

More project guidance is in [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and [`docs/repository-structure.md`](docs/repository-structure.md).

## Current limitations

This is a research project being shaped into a publishable repository. The OCR, DDI, scraper, and data-cleaning components do not yet share one deployment pipeline, one database contract, or one automated CI workflow. Those boundaries are deliberate and documented so that future integration work can happen without hiding the current state.

## Final UI and separately hosted components

The **final UI is maintained outside this repository** and is not the frontend currently reproduced here. Its source repository, release status, and ownership should be confirmed before it is linked publicly.

- UI repository: [DAWA Frontend]([docs/screenshots](https://github.com/BelkacemYerfa/dawa-frontend))
- Presentation screenshots: stored in [`docs/screenshots`](docs/screenshots) when approved and sanitized
- The screenshots in this repository should show synthetic or anonymized data only

A **RAG assistant** is also used in the project. It is implemented with **RAGFlow and prompt engineering**, with the knowledge and conversation service hosted on a dedicated virtual machine.

The RAG assistant is therefore documented as an external deployment rather than a self-contained module in this repository:

- This repository does not include the private VM configuration or credentials.
- This repository does not include private indexed documents or proprietary embeddings.
- API endpoints and access procedures are documented only for authorized team members.

This separation keeps the repository honest: cloning it provides the OCR, parsing, DDI, scraping, and data-cleaning components, while the final UI and hosted RAG service require separately maintained repositories or controlled infrastructure.
