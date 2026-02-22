# Semantic Drug Search Engine - Data Scraping Component

A professional data scraping pipeline for gathering drug information from multiple sources to build a semantic search engine.

## Project Overview

**Thesis Project**: Master's Thesis
**Objective**: Build a semantic search engine for drug discovery and information retrieval
**Current Phase**: Data Collection & Scraping

## Project Structure

```
drug_scraper/
├── src/                          # Main source code
│   ├── scrapers/                # Data scraping modules
│   │   ├── __init__.py
│   │   ├── base_scraper.py      # Abstract base class
│   │   ├── drugbank_scraper.py  # DrugBank scraper
│   │   └── pubchem_scraper.py   # PubChem scraper
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   ├── logger.py            # Logging setup
│   │   ├── cache.py             # Caching utilities
│   │   └── validation.py        # Data validation
│   └── data/                    # Data processing
│       ├── __init__.py
│       ├── cleaner.py           # Data cleaning
│       └── storage.py           # Data storage management
├── data/                        # Data storage
│   ├── raw/                     # Raw scraped data
│   └── processed/               # Cleaned data
├── tests/                       # Unit tests
├── docs/                        # Documentation
├── config/                      # Configuration files
├── .github/                     # GitHub specific files
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── main.py                      # Entry point
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone/Navigate to project**:
   ```bash
   cd drug_scraper
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

## Configuration

All configurations are managed through:
- `config/config.yaml` - Main configuration file
- `.env` - Environment-specific variables (API keys, secrets)

## Running the Scraper

```bash
python main.py --source drugbank --limit 1000
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Code Standards
- Follow PEP 8 style guide
- Use type hints for functions
- Write docstrings for classes and functions
- Keep modules focused and single-responsibility

## Contributing

When adding new scrapers:
1. Extend `base_scraper.BaseScraper`
2. Implement required abstract methods
3. Add tests in `tests/` directory
4. Update documentation

## Data Sources

- DrugBank (www.drugbank.ca)
- PubChem (pubchem.ncbi.nlm.nih.gov)
- ChEMBL (www.ebi.ac.uk/chembl)

## Legal Notice

Ensure compliance with each data source's terms of service and robots.txt when scraping.

## Author

[Your Name]

## License

[Your License]
