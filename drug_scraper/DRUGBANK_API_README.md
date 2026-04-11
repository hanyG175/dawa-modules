# DrugBank Scraper API

A consolidated, standalone API service for scraping drug data from DrugBank. This is a single-file solution that combines all scraping logic previously scattered across multiple modules.

## Quick Start

### Run as CLI

```bash
# Scrape 5 drugs (quick test)
python drugbank.py --limit 5

# Scrape 100 drugs (default)
python drugbank.py --limit 100

# Scrape and save as CSV
python drugbank.py --limit 50 --output-format csv

# Show browser window while scraping
python drugbank.py --limit 10 --no-headless

# Debug mode with verbose logging
python drugbank.py --limit 5 --log-level DEBUG
```

### Use as Python API

```python
from drugbank import DrugBankScraperAPI, run_scraper

# Option 1: Direct API usage
scraper = DrugBankScraperAPI(limit=50, delay=1.0)
data = scraper.scrape()
print(f"Scraped {len(data)} drugs")

# Option 2: Scrape and save to file
result = scraper.scrape_and_save(output_dir="data/raw", output_format="json")
print(result)

# Option 3: Use runner function (recommended for external services)
result = run_scraper(limit=100, output_format="json", log_level="INFO")
print(result)
```

## CLI Options

```
--limit              Maximum number of drugs to scrape (default: 100)
--timeout            Request timeout in seconds (default: 30)
--delay              Delay between requests in seconds (default: 1.0)
--no-headless        Show browser window (default: headless mode)
--output-dir         Output directory (default: data/raw)
--output-format      Output format: json or csv (default: json)
--log-level          Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
```

## Output Format

The scraper returns drug data with the following fields:

```json
{
  "name": "Drug Name",
  "accession_number": "DB12345",
  "url": "https://www.drugbank.ca/drugs/DB12345",
  "description": "Chemical description..."
}
```

## Features

- ✅ Standalone single-file solution
- ✅ No external configuration files needed
- ✅ Comprehensive logging (console + file)
- ✅ Configurable delay between requests (respectful scraping)
- ✅ JSON and CSV export formats
- ✅ Built-in data validation
- ✅ Selenium-based scraping with Edge WebDriver
- ✅ Timeout handling and error recovery
- ✅ CLI and programmatic API interfaces

## File Location

`/drugbank.py` - Root directory (ready to use immediately)

## API Classes

### `DrugBankScraperAPI`

Main scraper class with full control over scraping parameters.

**Methods:**
- `scrape()` - Scrape drugs from DrugBank
- `scrape_and_save(output_dir, output_format)` - Scrape and save to file
- `_scrape_drug_page(url)` - Scrape individual drug page
- `_validate_drug_data(data)` - Validate scraped data

## Runner Function

### `run_scraper()`

Recommended for external runners and services. Returns result dictionary.

```python
result = run_scraper(
    limit=100,
    timeout=30,
    delay=1.0,
    headless=True,
    output_dir="data/raw",
    output_format="json",
    log_level="INFO"
)
```

Returns:
```json
{
  "success": true,
  "count": 100,
  "file": "data/raw/drugbank_20260330_020711.json",
  "format": "json"
}
```

## Requirements

This API uses the following Python packages:
- `selenium` - Web scraping automation
- `beautifulsoup4` - HTML parsing
- (Optional) `webdriver-manager` - For WebDriver management

Ensure your `requirements.txt` includes these dependencies.

## Logging

Logs are written to both:
1. Console (INFO level by default)
2. File: `logs/drugbank_scraper.log` (if scraping_and_save is used)

## Notes

- The scraper respects server load with configurable delays between requests
- Uses Edge WebDriver (ensure Microsoft Edge is installed)
- Runs in headless mode by default for efficiency
- All scraped data is validated before inclusion
- Handles timeouts and errors gracefully
