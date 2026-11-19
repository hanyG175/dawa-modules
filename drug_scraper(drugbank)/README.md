# Drug scraper

The scraper workstream collects and prepares drug data for the semantic search project. It currently has two useful paths: a Selenium-based DrugBank scraper and streaming tools for a local DrugBank XML export.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` only if a local workflow needs environment configuration. Do not commit the full DrugBank XML export or scraped output.

## Run the scraper

```powershell
python main.py --source drugbank --limit 10 --output-format json
```

Raw output is written beneath `data/raw/`. Check the source terms and robots policy before running a large scrape.

## Stream a DrugBank XML export

The XML tools do not load the entire database into memory:

```powershell
python src\xml_scraper\extract_drugs.py --output drugs.json --limit 1000
python src\xml_scraper\inspect_drugs.py
```

Pass the XML path explicitly when using the Python classes. The large `full database.xml` file is local input data and is intentionally ignored by the repository.

## Layout

```text
src/
├── drugbank_scraper.py  Selenium scraper implementation
├── scrapers/            Scraper interfaces
├── utils/               Configuration, logging, and validation
└── xml_scraper/         Streaming XML extraction tools
```

Run the test suite with `pytest` after changing scraper behavior.
