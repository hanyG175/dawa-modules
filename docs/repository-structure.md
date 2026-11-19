# Repository structure

The repository is a monorepo organized by workstream. The applications remain separate because they currently have different dependency sets, entry points, and deployment assumptions.

```text
.
├── ddi_module/       Standalone DDI application
├── ocr_system/       OCR engine, parsers, and OCR web app
├── drug_scraper(drugbank)/ DrugBank scraper and XML tools
├── data_cleaning/    Multilingual cleaning experiments and pipelines
├── colaboration/     Experimental scraper service and notebooks
├── docs/             Repository-level documentation
├── README.md         Project overview and entry points
├── CONTRIBUTING.md   Contribution workflow
└── SECURITY.md       Secret and data-handling guidance
```

## Data boundaries

Source code belongs in the application directories. Raw documents, full DrugBank exports, generated CSV/JSON reports, logs, backups, and local database dumps are development inputs or outputs, not source code. They should remain ignored or be published separately with an explicit license and provenance record.

## Python boundaries

Each Python application owns its dependencies. This avoids forcing OCR, scraping, data cleaning, and DDI integrations into one environment while the interfaces are still evolving. When two components become a stable product boundary, extract a shared package with tests rather than importing across directories informally.

## Naming

Python package directories use lowercase `snake_case`. The historical `drug_scraper(drugbank)` directory is retained as a project label, while its Python package paths use standard names such as `src/xml_scraper`.