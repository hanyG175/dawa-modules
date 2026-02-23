"""DrugBank data scraper implementation."""

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DrugBankScraper(BaseScraper):
    """Scraper for DrugBank drug database."""

    def __init__(self, timeout: int = 30, limit: int = 100, delay: float = 0.5):
        """
        Initialize DrugBank scraper.
        
        Args:
            timeout: Request timeout in seconds
            limit: Maximum number of drugs to scrape
            delay: Delay between requests in seconds (to be respectful)
        """
        super().__init__(name="DrugBank", timeout=timeout)
        self.base_url = "https://www.drugbank.ca"
        self.limit = limit
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept":   "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape drug data from DrugBank.

        Returns:
            List of drug records from DrugBank
        """
        self.logger.info(f"Starting DrugBank scraping (limit: {self.limit})...")
        drugs = []
        
        try:
            # Get the drugs directory page
            drugs_url = urljoin(self.base_url, "/drugs")
            self.logger.info(f"Fetching drugs list from {drugs_url}")
            
            response = self.session.get(drugs_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find all drug links (they're typically in a table or list)
            drug_links = soup.find_all("a", class_="btn-drug")
            
            if not drug_links:
                # Fallback: try to find links differently
                drug_links = soup.find_all("a", href=lambda x: x and "/drugs/" in x)
            
            self.logger.info(f"Found {len(drug_links)} drug links on directory")
            
            # Scrape individual drug pages
            for idx, link in enumerate(drug_links[:self.limit]):
                if idx >= self.limit:
                    break
                
                try:
                    drug_url = urljoin(self.base_url, link.get("href", ""))
                    drug_data = self._scrape_drug_page(drug_url)
                    
                    if drug_data and self.validate_data(drug_data):
                        drugs.append(drug_data)
                        self.logger.debug(f"Scraped: {drug_data.get('name')}")
                    
                    # Be respectful to the server
                    time.sleep(self.delay)
                    
                except Exception as e:
                    self.logger.warning(f"Error scraping drug {idx}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(drugs)} drugs from DrugBank")
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to scrape DrugBank: {str(e)}")
        
        return drugs

    def _scrape_drug_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape individual drug page.

        Args:
            url: URL of the drug page

        Returns:
            Dictionary with drug information
        """
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract drug name
        name_elem = soup.find("h1")
        name = name_elem.get_text(strip=True) if name_elem else None
        
        # Extract accession number (DrugBank ID)
        accession = None
        accession_elem = soup.find("dt", string="DrugBank ID")
        if accession_elem:
            accession = accession_elem.find_next("dd").get_text(strip=True)
        
        # Extract general description
        description = None
        description_elem = soup.find("dt", string="Description")
        if description_elem:
            description = description_elem.find_next("dd").get_text(strip=True)
        
        if not name or not accession:
            return None
        
        return {
            "name": name,
            "DrugBank ID": accession,
            "url": url,
            "description": description,
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate DrugBank drug data.

        Args:
            data: Dictionary containing drug information

        Returns:
            True if data is valid
        """
        required_fields = ["name", "accession_number"]
        return all(field in data for field in required_fields)
