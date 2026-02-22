# Drug Scraper Project - Development Guidelines

## Project Overview
This is a Master's thesis project building a semantic drug search engine. The current phase focuses on data scraping from multiple drug databases (DrugBank, PubChem, ChEMBL).

## Code Structure
- `src/scrapers/` - Individual scraper implementations
- `src/utils/` - Configuration, logging, and utilities
- `src/data/` - Data processing and storage
- `tests/` - Unit tests
- `data/raw/` - Raw scraped data
- `data/processed/` - Cleaned and processed data

## Development Standards
1. All scrapers must extend `BaseScraper`
2. Follow PEP 8 style guide
3. Use type hints for all functions
4. Write docstrings for classes and public methods
5. Write tests for new functionality

## When Making Changes
- Update corresponding tests
- Run `pytest` before committing
- Update documentation in relevant files
- Follow existing code patterns

## Common Tasks
- **Add new scraper**: Extend `BaseScraper` in `src/scrapers/new_scraper.py`
- **Update config**: Edit `config/config.yaml` and `.env.example`
- **Add dependencies**: Update `requirements.txt`
- **Run scraper**: `python main.py --source [source] --limit [limit]`
- **Run tests**: `pytest tests/ -v`
