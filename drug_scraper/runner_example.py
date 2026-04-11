"""
Example runner that demonstrates how to call the DrugBank Scraper API.

This file shows different ways to use the drugbank.py API from external runners.
"""

import json

from drugbank import DrugBankScraperAPI, run_scraper


def example_1_basic_cli():
    """Example 1: Use as command-line tool"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Command-line interface")
    print("="*80)
    print("Run this command:")
    print("  python drugbank.py --limit 10 --output-format json")
    print("\nThis will scrape 10 drugs and save to data/raw/drugbank_*.json")


def example_2_direct_api():
    """Example 2: Direct API usage - basic scraping"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Direct API usage - basic scraping")
    print("="*80)
    
    scraper = DrugBankScraperAPI(limit=3, delay=0.5)
    print(f"Created scraper: {scraper.name}")
    
    # This would actually scrape (commented out to save time)
    # data = scraper.scrape()
    # print(f"Scraped {len(data)} drugs")


def example_3_scrape_and_save():
    """Example 3: Direct API usage - scrape and save"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Direct API usage - scrape and save")
    print("="*80)
    
    scraper = DrugBankScraperAPI(
        limit=5,
        timeout=30,
        delay=1.0,
        headless=True,
        log_level="INFO"
    )
    
    # result = scraper.scrape_and_save(
    #     output_dir="data/raw",
    #     output_format="json"
    # )
    # print(json.dumps(result, indent=2))


def example_4_runner_function():
    """Example 4: Use runner function (recommended for services)"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Runner function (recommended for external services)")
    print("="*80)
    
    print("Code:")
    print("""
    result = run_scraper(
        limit=50,
        timeout=30,
        delay=1.0,
        headless=True,
        output_dir="data/raw",
        output_format="json",
        log_level="INFO"
    )
    
    print(result)
    # Output: {"success": true, "count": 50, "file": "data/raw/drugbank_*.json", "format": "json"}
    """)


def example_5_custom_parameters():
    """Example 5: Customize all parameters"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Full customization")
    print("="*80)
    
    print("""
    # Create scraper with all custom parameters
    scraper = DrugBankScraperAPI(
        timeout=60,           # Allow more time per page
        limit=200,            # Scrape 200 drugs
        delay=2.0,            # Be extra respectful with 2s delay
        headless=False,       # Show browser for debugging
        log_level="DEBUG"     # Verbose logging
    )
    
    data = scraper.scrape()
    print(f"Scraped {len(data)} drugs successfully!")
    
    # Or scrape and save directly
    result = scraper.scrape_and_save(
        output_dir="data/my_exports",
        output_format="csv"   # Save as CSV instead of JSON
    )
    """)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DRUGBANK SCRAPER API - USAGE EXAMPLES")
    print("="*80)
    
    example_1_basic_cli()
    example_2_direct_api()
    example_3_scrape_and_save()
    example_4_runner_function()
    example_5_custom_parameters()
    
    print("\n" + "="*80)
    print("For more information, see DRUGBANK_API_README.md")
    print("="*80 + "\n")
