# Data cleaning workstream

This directory contains the multilingual cleaning and preparation workflows used to turn scraped drug data into datasets for search, retrieval, and downstream analysis.

It includes exploratory scripts, numbered pipeline stages, notebooks, reports, and local input/output data. The numbered files describe historical processing steps, not a single command that is safe to run from a clean checkout.

## Working safely

1. Read the script before running it and confirm its input and output paths.
2. Work on a copy of the source data.
3. Keep generated exports and backups ignored.
4. Run the small validation scripts before publishing a dataset.
5. Record the source, transformation steps, and date for any dataset that leaves this directory.

## Main areas

```text
pipeline/       Numbered transformation and validation stages
Original Data/  Local raw inputs; not for publication
PDFs/           Local source documents; may contain sensitive material
drug_notices/   Notice-processing inputs and outputs
backups/        Local safety copies; ignored
*.ipynb         Exploratory analysis
```

The cleaning workflow is intentionally separate from the OCR and scraper applications. When a stable interface is agreed, it should consume versioned fixtures or an explicit data contract rather than importing scripts by path.
