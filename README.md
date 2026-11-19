# DAWA Modules: OCR, drug-interaction and data pipelines

Python components from DAWA, a graduation project on a medicine information assistant
for Algeria. The repo covers the data and document-processing side of the project:
prescription OCR, drug-name parsing, a drug-drug interaction (DDI) workflow, DrugBank
extraction tools, and multilingual data cleaning.

> **Not medical advice.** This is a research and learning project. It must not be used
> to make decisions about medication. Always consult a doctor or pharmacist.

## My contribution

<!-- TODO: fill in before publishing. Keep only what is true and delete this comment. -->
- **Built by me:** [list the modules you wrote, e.g. OCR parsing, DDI workflow, scrapers, data cleaning]
- **Built with others:** [list modules written together, and with whom/what role]
- **RAG assistant (not in this repo):** I prepared and cleaned the data it uses and designed
  its prompts. The RAG framework is [RAGFlow](https://github.com/infiniflow/ragflow), which
  I did not write, running on a hosted VM.

## How the pieces fit

```
prescription / medicine image
        |
   ocr_system  ->  text
        |
   drug-name parsing  ->  list of drugs
        |
   ddi_module  ->  interaction check (Neo4j graph + OpenFDA, optional LLM summary)

drug_scraper + data_cleaning  ->  the drug data the other parts rely on
```

## Repository map

| Directory | Purpose | Status |
| --- | --- | --- |
| [`ocr_system`](ocr_system) | OCR, document parsing, and the OCR web app | Active development |
| [`ddi_module`](ddi_module) | Prescription and drug-drug interaction workflow | Active development |
| [`drug_scraper(drugbank)`](drug_scraper%28drugbank%29) | DrugBank scraping and XML extraction tools | Active development |
| [`data_cleaning`](data_cleaning) | Data-cleaning pipelines for multilingual drug data | Research |
| [`colaboration`](colaboration) | Experimental scraper app and experiments | Experimental |

## Implemented

- Google Drive OCR for PDFs, scans, prescriptions, and medicine images
- Drug-name and prescription parsing after OCR
- A standalone DDI workflow with optional Google OCR, Neo4j, OpenFDA, and LLM integrations
- DrugBank scraping and streaming XML extraction
- Data-cleaning pipelines for multilingual drug data
- An experimental scraper service

Some integrations need external credentials or services and will not run in a clean checkout.

## Quick start (Windows PowerShell)

Each application has its own dependencies. Use a separate virtual environment per app.

**DDI module**

```powershell
cd ddi_module
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python launch.py
```

Served at `http://127.0.0.1:5000/ddi`. See [`ddi_module/README.md`](ddi_module/README.md).

**OCR system** (needs Google Drive OAuth credentials)

```powershell
cd ocr_system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python src\web\app.py
```

See [`ocr_system/README.md`](ocr_system/README.md).

**Drug scraper**

```powershell
cd 'drug_scraper(drugbank)'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --source drugbank --limit 10
```

## Data and licensing

- The full DrugBank XML file is local input only and is not in this repo. DrugBank data
  has its own license terms, so check them before using or sharing any data derived from it.
- The Neo4j exports in `ddi_module/data/neo4j` were [describe the source and confirm you are
  allowed to publish them, or remove them from the repo].
- Code license: [choose one, e.g. MIT]. Third-party data and services keep their own licenses.

## Final UI and hosted components

- The final UI is maintained outside this repository. [Add a link only if you have the
  owner's permission, and name the owner.]
- Screenshots: [add 2 or 3 sanitized screenshots here, with no patient data, after approval].
- The RAG assistant runs on a dedicated VM. Its configuration, credentials, indexed
  documents and embeddings are not in this repo.

## Limitations

The components do not yet share one deployment pipeline, one database contract, or automated
CI. This is a research project being shaped into a publishable repo.

## Contributing and security

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and
[`docs/repository-structure.md`](docs/repository-structure.md). Never commit credentials,
`.env` files, caches, virtual environments, or raw proprietary data.
