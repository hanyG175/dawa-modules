"""Main entry point for the drug scraper."""

import argparse
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.utils.config import Config
from src.scrapers.drugbank_scraper import DrugBankScraper
from src.scrapers.pubchem_scraper import PubChemScraper

# Setup logging
logger = setup_logger(__name__, log_level="INFO", log_file="logs/scraper.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Drug data scraper for semantic search engine"
    )
    parser.add_argument(
        "--source",
        choices=["drugbank", "pubchem", "all"],
        default="all",
        help="Data source to scrape",
    )
    parser.add_argument(
        "--limit", type=int, default=1000, help="Maximum number of records to scrape"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "csv"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    # Load configuration
    config = Config()
    logger.info(f"Starting drug scraper - Source: {args.source}")

    scrapers = []

    if args.source in ["drugbank", "all"]:
        scrapers.append(DrugBankScraper())

    if args.source in ["pubchem", "all"]:
        scrapers.append(PubChemScraper())

    for scraper in scrapers:
        logger.info(f"Starting {scraper.name} scraper...")
        # TODO: Implement scraping and data processing
        logger.info(f"Completed {scraper.name} scraper")

    logger.info("Scraping completed successfully")


if __name__ == "__main__":
    main()
