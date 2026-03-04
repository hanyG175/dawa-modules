# Drug Scraper Guide

This document explains how to use the different scrapers in the drug_scraper project for collecting drug data from multiple sources.

## Overview

The project includes multiple scrapers for collecting drug data from different sources:

1. **DrugBank Scraper** - Web scraper using Selenium for dynamic content
2. **XML Scraper** - Local XML file parser for DrugBank database exports
3. **PubChem Scraper** - Planned scraper for PubChem database (under development)

---

## Quick Start

### Prerequisites

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows PowerShell
source venv/bin/activate      # On Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

Run all scrapers:
```bash
python main.py
```

Run specific scraper:
```bash
python main.py --source drugbank
```

Specify output format and limits:
```bash
python main.py --source drugbank --output-format json --limit 500
python main.py --source drugbank --output-format csv --limit 100
```

---

## Available Scrapers

### 1. DrugBank Scraper

**Source**: https://www.drugbank.ca

**Type**: Web scraper using Selenium WebDriver (Edge browser)

**Features**:
- Automatically fetches drug data from DrugBank website
- Handles dynamic content loading
- Includes retry logic and rate limiting
- Respects robots.txt
- Runs in headless mode by default

#### Usage

From command line:
```bash
python main.py --source drugbank --limit 100
```

From Python code:
```python
from src.drugbank_scraper import DrugBankScraper

# Create scraper instance
scraper = DrugBankScraper(
    timeout=30,           # Request timeout in seconds
    limit=100,           # Maximum number of drugs to scrape
    delay=1.0,           # Delay between requests (seconds)
    headless=True        # Run without showing browser window
)

# Scrape data
data = scraper.scrape()

# Process data
for drug in data:
    print(drug)
```

**Configuration** (in `config/config.yaml`):
```yaml
scraping:
  timeout: 30
  retry_attempts: 3
  retry_delay: 5
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

rate_limiting:
  requests_per_second: 1
  respect_robots_txt: true

sources:
  drugbank:
    enabled: true
    base_url: "https://www.drugbank.ca"
    priority: 1
```

#### Output

Default output location: `data/raw/drugbank_raw.json`

Sample output structure:
```json
[
  {
    "id": "DB00001",
    "name": "Lepirudin",
    "description": "Lepirudin is...",
    "drugbank_id": "DB00001",
    "type": "Small Molecule",
    "synonyms": ["Refludan", "Leprudin"],
    "targets": [...],
    "pathways": [...]
  }
]
```

---

### 2. XML Scraper (DrugBank XML Extract)

**Source**: Local DrugBank XML file (`full database.xml`)

**Type**: Local file parser with streaming to handle large files efficiently

**Features**:
- Parses large XML files without loading entire file into memory
- Multiple output formats (JSON, CSV)
- Progress tracking
- Data filtering and limiting options

#### Usage

Extract to JSON:
```bash
cd src/xml_scraper
python extract_drugs.py --output drugs.json --limit 1000
```

Extract to CSV:
```bash
python extract_drugs.py --format csv --output drugs.csv
```

From Python code:
```python
from src.xml_scraper.extract_drugs import DrugBankExtractor

# Create extractor instance
extractor = DrugBankExtractor("full database.xml")

# Extract to JSON
count = extractor.extract_to_json(
    output_file="drugs.json",
    limit=500  # Optional: limit number of drugs
)

print(f"Extracted {count} drugs")
```

#### Inspect XML Structure

To explore the XML file structure:
```bash
python src/xml_scraper/inspect_drugs.py
```

This will display:
- Root element and namespace
- Drug element structure
- Sample drug entries
- Data field mappings

#### Output

Default output location: `data/raw/drugbank_xml_raw.json` or `.csv`

---

### 3. PubChem Scraper (Under Development)

**Source**: https://pubchem.ncbi.nlm.nih.gov

**Status**: Planned for implementation

**Expected Features**:
- API-based scraper for PubChem database
- Supports compound search and retrieval
- Chemical structure data access

**Configuration** (in `config/config.yaml`):
```yaml
sources:
  pubchem:
    enabled: false  # Not yet implemented
    base_url: "https://pubchem.ncbi.nlm.nih.gov"
    priority: 2
```

---

## Command Line Options

```
usage: main.py [-h] [--source {drugbank,pubchem,all}] 
               [--limit LIMIT] 
               [--output-format {json,csv}]

Drug data scraper for semantic search engine

optional arguments:
  -h, --help                          Show this help message
  --source {drugbank,pubchem,all}     Data source to scrape (default: all)
  --limit LIMIT                       Maximum number of records to scrape
                                      (default: 1000)
  --output-format {json,csv}          Output format (default: json)
```

### Examples

```bash
# Scrape 500 drugs from DrugBank
python main.py --source drugbank --limit 500

# Scrape all sources and save as CSV
python main.py --source all --output-format csv

# Quick test with 10 records
python main.py --source drugbank --limit 10

# Scrape 1000 records from each source
python main.py --source all --limit 1000
```

---

## Configuration

Edit `config/config.yaml` to customize scraper behavior:

```yaml
scraping:
  timeout: 30              # Request timeout (seconds)
  retry_attempts: 3        # Number of retry attempts
  retry_delay: 5           # Delay between retries (seconds)
  user_agent: "..."        # HTTP User-Agent header

rate_limiting:
  requests_per_second: 1   # Rate limit for requests
  respect_robots_txt: true # Respect website's robots.txt

storage:
  raw_path: "./data/raw"
  processed_path: "./data/processed"
  format: "json"

logging:
  level: "INFO"
  file: "./logs/scraper.log"
  max_file_size: 10485760  # 10MB
  backup_count: 5
```

---

## Output Formats

### JSON Format

```json
[
  {
    "id": "DB00001",
    "name": "Drug Name",
    "description": "...",
    "type": "Small Molecule",
    "synonyms": ["name1", "name2"]
  }
]
```

**Advantages**: 
- Nested data support
- Preserves complex structures
- Easier for API integration

**Location**: `data/raw/{source}_raw.json`

### CSV Format

| id | name | description | type | synonyms |
|----|------|-------------|------|----------|
| DB00001 | Drug Name | ... | Small Molecule | name1;name2 |

**Advantages**:
- Compatible with Excel/spreadsheets
- Easier for simple data analysis
- Lightweight format

**Location**: `data/raw/{source}_raw.csv`

---

## Data Validation

Each scraper implements data validation before storing results. The `BaseScraper` class requires all implementations to have a `validate_data()` method:

```python
def validate_data(self, data: Dict[str, Any]) -> bool:
    """Validate scraped drug data."""
    # Implementation-specific validation
    return is_valid
```

Validation checks may include:
- Required fields presence
- Data type verification
- Format validation
- Duplicate detection

---

## Logging

All scraper activities are logged to:
- **Console**: Real-time progress updates
- **File**: `logs/scraper.log` - Complete execution history

Log levels:
- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures

Example log output:
```
2024-03-04 10:15:30 INFO: Starting drug scraper - Source: drugbank
2024-03-04 10:15:31 INFO: Starting DrugBank scraper...
2024-03-04 10:15:45 INFO: Successfully scraped 100 records from DrugBank
2024-03-04 10:15:46 INFO: Saved 100 records to data/raw/drugbank_raw.json
```

---

## Error Handling

The scrapers include robust error handling:

```python
try:
    data = scraper.scrape()
except Exception as e:
    logger.error(f"Error scraping {scraper.name}: {str(e)}", exc_info=True)
```

Common issues and solutions:

| Issue | Cause | Solution |
|-------|-------|----------|
| "XML file not found" | File path incorrect | Ensure `full database.xml` exists in project root |
| Connection timeout | Network or server unreachable | Check internet connection, retry later |
| Permission denied | File write issues | Check folder permissions on `data/` directory |
| Browser not found | Selenium driver issue | Install Edge browser or update WebDriver |

---

## Best Practices

### 1. **Respect Rate Limits**
```python
scraper = DrugBankScraper(delay=2.0)  # 2 second delay between requests
```

### 2. **Use Appropriate Limits**
```bash
# Test run
python main.py --source drugbank --limit 10

# Production run
python main.py --source drugbank --limit 10000
```

### 3. **Monitor Logs**
```bash
# Watch logs in real-time
Get-Content logs/scraper.log -Wait  # PowerShell
tail -f logs/scraper.log            # Linux/Mac
```

### 4. **Validate Output**
```python
import json

with open("data/raw/drugbank_raw.json") as f:
    data = json.load(f)
    print(f"Total records: {len(data)}")
    print(f"Sample: {data[0]}")
```

### 5. **Handle Large Datasets**
For large XML files, use streaming instead of loading all in memory:
```bash
python src/xml_scraper/extract_drugs.py --limit 5000 --chunk-size 500
```

---

## Testing

Run tests for scrapers:
```bash
pytest tests/ -v
pytest tests/ -k "scraper" -v  # Run only scraper tests
```

Run specific scraper test:
```bash
pytest tests/test_drugbank_scraper.py -v
```

---

## Project Structure

```
drug_scraper/
├── main.py                          # Entry point
├── src/
│   ├── drugbank_scraper.py          # DrugBank web scraper
│   ├── scrapers/
│   │   └── base_scraper.py          # Base class for all scrapers
│   ├── xml_scraper/
│   │   ├── extract_drugs.py         # XML to JSON/CSV converter
│   │   ├── inspect_drugs.py         # XML structure inspector
│   │   └── analyser.py              # Data analysis tools
│   ├── data/
│   │   ├── cleaner.py               # Data cleaning utilities
│   │   └── storage.py               # Data storage operations
│   └── utils/
│       ├── config.py                # Configuration loader
│       ├── logger.py                # Logging setup
│       └── validation.py            # Data validation
├── config/
│   └── config.yaml                  # Configuration file
├── data/
│   ├── raw/                         # Raw scraped data
│   └── processed/                   # Cleaned data
└── logs/
    └── scraper.log                  # Scraper activity log
```

---

## Next Steps

### For Developers

1. **Implement PubChem Scraper**: Create `src/scrapers/pubchem_scraper.py`
   ```python
   from src.scrapers.base_scraper import BaseScraper
   
   class PubChemScraper(BaseScraper):
       """Scraper for PubChem database."""
       def scrape(self):
           # Implementation here
           pass
   ```

2. **Add ChEMBL Scraper**: Similar to PubChem

3. **Data Processing**: Use tools in `src/data/cleaner.py` to process raw data

4. **Testing**: Add tests in `tests/` directory

### For Users

1. **Run scrapers** to collect data from your preferred source
2. **Process data** using cleaning utilities
3. **Export results** for analysis or API integration
4. **Monitor logs** for issues and performance

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'selenium'"

**Solution**: Install missing dependencies
```bash
pip install selenium beautifulsoup4
```

### Issue: "WebDriver executable needs to be in PATH"

**Solution**: Ensure Edge browser is installed, or specify driver path:
```python
scraper = DrugBankScraper()
# The scraper auto-downloads the correct WebDriver
```

### Issue: XML file too large, running out of memory

**Solution**: Use the streaming XML parser:
```bash
python src/xml_scraper/extract_drugs.py --limit 5000
```

### Issue: No data being scraped

**Solution**: Check configuration and logs
```bash
# Review configuration
cat config/config.yaml

# Check logs for errors
Get-Content logs/scraper.log -Tail 50  # Last 50 lines
```

---

## Contributing

When creating new scrapers:

1. Extend `BaseScraper` class
2. Implement `scrape()` and `validate_data()` methods
3. Add logging throughout
4. Include docstrings
5. Write unit tests
6. Update this documentation

---

## License

This project is part of a Master's thesis on semantic drug search engines.

---

## Support

For issues or questions:
1. Check the logs in `logs/scraper.log`
2. Review this documentation
3. Inspect the code comments in relevant scraper files
4. Run tests to validate your setup
