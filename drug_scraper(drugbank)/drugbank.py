"""
DrugBank Scraper API Service

This is a consolidated, standalone API service for scraping drug data from DrugBank.
Can be called directly or used as a runner service.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logger(
    name: Optional[str] = None,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================================
# DRUGBANK SCRAPER API
# ============================================================================

class DrugBankScraperAPI:
    """
    DrugBank Scraper API Service
    
    Scrapes drug data from DrugBank using Selenium WebDriver.
    This is the main API that can be called by runners or external services.
    """

    def __init__(
        self,
        timeout: int = 30,
        limit: int = 100,
        delay: float = 1.0,
        headless: bool = True,
        log_file: Optional[str] = None,
        log_level: str = "INFO",
    ):
        """
        Initialize DrugBank Scraper API.

        Args:
            timeout: Request timeout in seconds (default: 30)
            limit: Maximum number of drugs to scrape (default: 100)
            delay: Delay between requests in seconds to be respectful (default: 1.0)
            headless: Run browser in headless mode (default: True)
            log_file: Path to log file (default: None)
            log_level: Logging level (default: INFO)
        """
        self.name = "DrugBank"
        self.base_url = "https://www.drugbank.ca"
        self.timeout = timeout
        self.limit = limit
        self.delay = delay
        self.headless = headless
        self.driver = None
        
        # Setup logging
        self.logger = setup_logger(
            name=self.__class__.__name__,
            log_level=log_level,
            log_file=log_file,
        )
        
        self.logger.info(
            f"DrugBank Scraper API initialized: "
            f"limit={limit}, timeout={timeout}s, delay={delay}s"
        )

    def _setup_driver(self) -> None:
        """Initialize Selenium WebDriver with Edge."""
        try:
            # Suppress logging
            os.environ['WDM_LOG_LEVEL'] = '0'
            
            options = EdgeOptions()
            
            if self.headless:
                options.add_argument("--headless")
            
            # Suppress error messages and improve stability
            options.add_argument("--disable-logging")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-component-extensions-with-background-pages")
            options.add_argument("--disable-sync")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                "Safari/537.36 Edg/120.0.0.0"
            )
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            self.driver = webdriver.Edge(options=options)
            self.logger.info("Edge WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Edge WebDriver: {e}", exc_info=True)
            raise

    def _close_driver(self) -> None:
        """Close Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed")
            except Exception as e:
                self.logger.warning(f"Error closing WebDriver: {e}")

    def _extract_text_from_dt_dd(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """
        Extract text from a dt/dd pair in the HTML.
        
        Args:
            soup: BeautifulSoup object
            label: The label to search for
            
        Returns:
            The text value or None
        """
        try:
            dt_elem = soup.find("dt", string=label)
            if dt_elem:
                dd_elem = dt_elem.find_next("dd")
                if dd_elem:
                    return dd_elem.get_text(strip=True)
        except Exception:
            pass
        return None

    def _extract_section_content(self, soup: BeautifulSoup, section_title: str) -> Optional[str]:
        """
        Extract content from a major section on the drug page.
        
        Args:
            soup: BeautifulSoup object
            section_title: The section title to search for
            
        Returns:
            The section content or None
        """
        try:
            # Look for h2 or h3 with the section title
            heading = soup.find(["h2", "h3"], string=lambda x: x and section_title.lower() in x.lower())
            if heading:
                # Find the parent container or next paragraph/div
                content_elem = heading.find_next(["p", "div", "article"])
                if content_elem:
                    return content_elem.get_text(strip=True)[:500]  # Limit to 500 chars
        except Exception:
            pass
        return None

    def _scrape_drug_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape individual drug page using Selenium and extract comprehensive drug information.

        Args:
            url: URL of the drug page

        Returns:
            Dictionary with comprehensive drug information or None if failed
        """
        try:
            self.driver.get(url)
            
            # Wait for content to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "h1")))
            
            time.sleep(0.5)  # Additional wait for dynamic content
            
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # ============================================================
            # BASIC INFORMATION
            # ============================================================
            
            # Extract drug name
            name_elem = soup.find("h1")
            name = name_elem.get_text(strip=True) if name_elem else None
            
            # Extract accession number (DrugBank ID)
            accession = self._extract_text_from_dt_dd(soup, "DrugBank ID")
            
            # Fallback to extract from URL
            if not accession:
                accession = url.split("/")[-1] if "/drugs/" in url else None
            
            if not name or not accession:
                self.logger.warning(f"Missing required fields for {url}")
                return None
            
            # ============================================================
            # GENERAL INFORMATION
            # ============================================================
            
            drug_data = {
                "name": name,
                "accession_number": accession,
                "url": url,
            }
            
            # Description
            description = self._extract_text_from_dt_dd(soup, "Description")
            if description:
                drug_data["description"] = description
            
            # Drug Type
            drug_type = self._extract_text_from_dt_dd(soup, "Type")
            if drug_type:
                drug_data["drug_type"] = drug_type
            
            # State
            state = self._extract_text_from_dt_dd(soup, "State")
            if state:
                drug_data["state"] = state
            
            # ============================================================
            # CHEMICAL INFORMATION
            # ============================================================
            
            # Chemical Formula
            formula = self._extract_text_from_dt_dd(soup, "Chemical Formula")
            if formula:
                drug_data["chemical_formula"] = formula
            
            # Molecular Weight
            mol_weight = self._extract_text_from_dt_dd(soup, "Molecular Weight")
            if mol_weight:
                drug_data["molecular_weight"] = mol_weight
            
            # SMILES
            smiles = self._extract_text_from_dt_dd(soup, "SMILES")
            if smiles:
                drug_data["smiles"] = smiles
            
            # InChI
            inchi = self._extract_text_from_dt_dd(soup, "InChI")
            if inchi:
                drug_data["inchi"] = inchi
            
            # InChI Key
            inchi_key = self._extract_text_from_dt_dd(soup, "InChI Key")
            if inchi_key:
                drug_data["inchi_key"] = inchi_key
            
            # ============================================================
            # PHARMACOLOGY & THERAPEUTIC INFORMATION
            # ============================================================
            
            # Indication
            indication = self._extract_text_from_dt_dd(soup, "Indication")
            if indication:
                drug_data["indication"] = indication
            
            # Mechanism of Action
            mechanism = self._extract_text_from_dt_dd(soup, "Mechanism of action")
            if mechanism:
                drug_data["mechanism_of_action"] = mechanism
            
            # Pharmacodynamics
            pharmacodynamics = self._extract_text_from_dt_dd(soup, "Pharmacodynamics")
            if pharmacodynamics:
                drug_data["pharmacodynamics"] = pharmacodynamics
            
            # Mechanism of Action (alternative format)
            if "mechanism_of_action" not in drug_data:
                mechanism_alt = self._extract_section_content(soup, "Mechanism of Action")
                if mechanism_alt:
                    drug_data["mechanism_of_action"] = mechanism_alt
            
            # ============================================================
            # ABSORPTION & METABOLISM
            # ============================================================
            
            # Absorption
            absorption = self._extract_text_from_dt_dd(soup, "Absorption")
            if absorption:
                drug_data["absorption"] = absorption
            
            # Distribution
            distribution = self._extract_text_from_dt_dd(soup, "Distribution")
            if distribution:
                drug_data["distribution"] = distribution
            
            # Metabolism
            metabolism = self._extract_text_from_dt_dd(soup, "Metabolism")
            if metabolism:
                drug_data["metabolism"] = metabolism
            
            # Elimination
            elimination = self._extract_text_from_dt_dd(soup, "Elimination")
            if elimination:
                drug_data["elimination"] = elimination
            
            # Half-life
            halflife = self._extract_text_from_dt_dd(soup, "Half-life")
            if halflife:
                drug_data["half_life"] = halflife
            
            # ============================================================
            # TOXICITY & ADVERSE EFFECTS
            # ============================================================
            
            # Toxicity
            toxicity = self._extract_text_from_dt_dd(soup, "Toxicity")
            if toxicity:
                drug_data["toxicity"] = toxicity
            
            # ============================================================
            # EXTERNAL IDENTIFIERS
            # ============================================================
            
            # CAS Number
            cas = self._extract_text_from_dt_dd(soup, "CAS number")
            if cas:
                drug_data["cas_number"] = cas
            
            # PubChem Compound ID
            pubchem_cid = self._extract_text_from_dt_dd(soup, "PubChem Compound")
            if pubchem_cid:
                drug_data["pubchem_compound_id"] = pubchem_cid
            
            # ChEMBL ID
            chembl = self._extract_text_from_dt_dd(soup, "ChEMBL")
            if chembl:
                drug_data["chembl_id"] = chembl
            
            # ============================================================
            # CATEGORIES & CLASSIFICATION
            # ============================================================
            
            # Extract categories
            categories = []
            try:
                category_links = soup.find_all("a", href=lambda x: x and "/categories/" in x)
                for link in category_links[:10]:  # Limit to 10 categories
                    cat_text = link.get_text(strip=True)
                    if cat_text and cat_text not in categories:
                        categories.append(cat_text)
            except Exception:
                pass
            
            if categories:
                drug_data["categories"] = categories
            
            # ============================================================
            # INTERACTION PARTNERS (if available)
            # ============================================================
            
            # Extract targets count
            try:
                targets_section = soup.find("dt", string="Targets")
                if targets_section:
                    targets_dd = targets_section.find_next("dd")
                    if targets_dd:
                        targets_count = targets_dd.get_text(strip=True)
                        drug_data["targets_count"] = targets_count
            except Exception:
                pass
            
            # Extract enzymes count
            try:
                enzymes_section = soup.find("dt", string="Enzymes")
                if enzymes_section:
                    enzymes_dd = enzymes_section.find_next("dd")
                    if enzymes_dd:
                        enzymes_count = enzymes_dd.get_text(strip=True)
                        drug_data["enzymes_count"] = enzymes_count
            except Exception:
                pass
            
            # Extract carriers count
            try:
                carriers_section = soup.find("dt", string="Carriers")
                if carriers_section:
                    carriers_dd = carriers_section.find_next("dd")
                    if carriers_dd:
                        carriers_count = carriers_dd.get_text(strip=True)
                        drug_data["carriers_count"] = carriers_count
            except Exception:
                pass
            
            return drug_data
            
        except TimeoutException:
            self.logger.warning(f"Timeout loading page: {url}")
            return None
        except Exception as e:
            self.logger.warning(f"Error scraping page {url}: {str(e)}")
            return None

    def _validate_drug_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate DrugBank drug data.

        Args:
            data: Dictionary containing drug information

        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ["name", "accession_number"]
        is_valid = all(field in data and data[field] for field in required_fields)
        return is_valid

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape drug data from DrugBank.

        Returns:
            List of drug records from DrugBank
        """
        self.logger.info(f"Starting DrugBank scraping (limit: {self.limit})...")
        drugs = []
        
        try:
            self._setup_driver()
            
            # Get the drugs directory page
            drugs_url = urljoin(self.base_url, "/drugs")
            self.logger.info(f"Fetching drugs list from {drugs_url}")
            
            self.driver.get(drugs_url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Find all drug links
            drug_links = soup.find_all("a", href=lambda x: x and "/drugs/" in x)
            
            # Filter out duplicates and navigation links
            seen_urls = set()
            unique_links = []
            for link in drug_links:
                href = link.get("href", "")
                if href not in seen_urls and "/drugs/DB" in href:
                    seen_urls.add(href)
                    unique_links.append(link)
            
            self.logger.info(f"Found {len(unique_links)} unique drug links")
            
            # Scrape individual drug pages
            for idx, link in enumerate(unique_links[:self.limit]):
                if idx >= self.limit:
                    break
                
                try:
                    drug_url = urljoin(self.base_url, link.get("href", ""))
                    self.logger.info(
                        f"[{idx+1}/{min(self.limit, len(unique_links))}] Scraping: {drug_url}"
                    )
                    
                    drug_data = self._scrape_drug_page(drug_url)
                    
                    if drug_data and self._validate_drug_data(drug_data):
                        drugs.append(drug_data)
                        self.logger.debug(f"Successfully scraped: {drug_data.get('name')}")
                    
                    # Be respectful to the server
                    time.sleep(self.delay)
                    
                except Exception as e:
                    self.logger.warning(f"Error scraping drug {idx+1}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(drugs)} drugs from DrugBank")
            
        except Exception as e:
            self.logger.error(f"Failed to scrape DrugBank: {str(e)}", exc_info=True)
        
        finally:
            self._close_driver()
        
        return drugs

    def scrape_and_save(
        self,
        output_dir: str = "data/raw",
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Scrape data and save to file.

        Args:
            output_dir: Directory to save output files
            output_format: Output format ('json' or 'csv')

        Returns:
            Dictionary with scraping results and file path
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Scrape data
        data = self.scrape()
        
        if not data:
            self.logger.warning("No data scraped")
            return {"success": False, "message": "No data scraped", "count": 0}
        
        # Save data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format.lower() == "json":
            output_file = output_path / f"drugbank_{timestamp}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(data)} records to {output_file}")
            return {
                "success": True,
                "count": len(data),
                "file": str(output_file),
                "format": "json",
            }
        elif output_format.lower() == "csv":
            import csv
            output_file = output_path / f"drugbank_{timestamp}.csv"
            if data:
                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                self.logger.info(f"Saved {len(data)} records to {output_file}")
                return {
                    "success": True,
                    "count": len(data),
                    "file": str(output_file),
                    "format": "csv",
                }
        
        return {"success": False, "message": f"Unknown format: {output_format}"}


# ============================================================================
# RUNNER INTERFACE
# ============================================================================

def run_scraper(
    limit: int = 100,
    timeout: int = 30,
    delay: float = 1.0,
    headless: bool = True,
    output_dir: str = "data/raw",
    output_format: str = "json",
    log_level: str = "INFO",
) -> Dict[str, Any]:
    """
    Run the DrugBank scraper with specified parameters.

    This is the main entry point for external runners.

    Args:
        limit: Maximum number of drugs to scrape
        timeout: Request timeout in seconds
        delay: Delay between requests in seconds
        headless: Run browser in headless mode
        output_dir: Directory to save output files
        output_format: Output format ('json' or 'csv')
        log_level: Logging level

    Returns:
        Dictionary with scraping results
    """
    scraper = DrugBankScraperAPI(
        timeout=timeout,
        limit=limit,
        delay=delay,
        headless=headless,
        log_file="logs/drugbank_scraper.log",
        log_level=log_level,
    )
    
    return scraper.scrape_and_save(
        output_dir=output_dir,
        output_format=output_format,
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DrugBank Scraper API Service"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of drugs to scrape (default: 100)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show browser window (default: headless mode)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory (default: data/raw)",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args()
    
    result = run_scraper(
        limit=args.limit,
        timeout=args.timeout,
        delay=args.delay,
        headless=not args.no_headless,
        output_dir=args.output_dir,
        output_format=args.output_format,
        log_level=args.log_level,
    )
    
    print("\n" + "="*80)
    print("SCRAPING RESULTS")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80)
