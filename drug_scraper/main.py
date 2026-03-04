"""Main entry point for the drug scraper."""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.drugbank_scraper import DrugBankScraper
from src.utils.config import Config
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_level="INFO", log_file="logs/scraper.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Drug data scraper for semantic search engine"
    )
    parser.add_argument(
        "--source",
        choices=["drugbank", "all"],
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

    # Create output directory if it doesn't exist
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_data = {}

    for scraper in scrapers:
        logger.info(f"Starting {scraper.name} scraper...")
        
        try:
            # Scrape data with limit
            if scraper.name == "DrugBank":
                data = scraper.scrape()
            else:
                data = scraper.scrape()
            
            all_data[scraper.name.lower()] = data
            logger.info(f"Successfully scraped {len(data)} records from {scraper.name}")
            
            # Save raw data
            output_file = output_dir / f"{scraper.name.lower()}_raw.{args.output_format}"
            
            if args.output_format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif args.output_format == "csv":
                if data:
                    with open(output_file, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            
            logger.info(f"Saved {len(data)} records to {output_file}")
            
        except Exception as e:
            logger.error(f"Error scraping {scraper.name}: {str(e)}", exc_info=True)
        
        logger.info(f"Completed {scraper.name} scraper")

    logger.info("Scraping completed successfully")


if __name__ == "__main__":
    main()
