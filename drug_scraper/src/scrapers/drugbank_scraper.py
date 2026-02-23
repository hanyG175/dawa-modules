"""DrugBank data scraper implementation."""

import logging
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DrugBankScraper(BaseScraper):
    """Scraper for DrugBank drug database using Selenium."""

    def __init__(self, timeout: int = 30, limit: int = 100, delay: float = 1.0, headless: bool = True):
        """
        Initialize DrugBank scraper.
        
        Args:
            timeout: Request timeout in seconds
            limit: Maximum number of drugs to scrape
            delay: Delay between requests in seconds (to be respectful)
            headless: Run browser in headless mode
        """
        super().__init__(name="DrugBank", timeout=timeout)
        self.base_url = "https://www.drugbank.ca"
        self.limit = limit
        self.delay = delay
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Initialize Selenium WebDriver with Edge."""
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
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        try:
            self.driver = webdriver.Edge(options=options)
            self.logger.info("Edge WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Edge WebDriver: {e}", exc_info=True)
            raise

    def _close_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed")

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape drug data from DrugBank using Selenium.

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
                    self.logger.info(f"[{idx+1}/{min(self.limit, len(unique_links))}] Scraping: {drug_url}")
                    
                    drug_data = self._scrape_drug_page(drug_url)
                    
                    if drug_data and self.validate_data(drug_data):
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

    def _scrape_drug_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape individual drug page using Selenium.

        Args:
            url: URL of the drug page

        Returns:
            Dictionary with drug information
        """
        try:
            self.driver.get(url)
            
            # Wait for content to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "h1")))
            
            time.sleep(0.5)  # Additional wait for dynamic content
            
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Extract drug name
            name_elem = soup.find("h1")
            name = name_elem.get_text(strip=True) if name_elem else None
            
            # Extract accession number (DrugBank ID) from page or URL
            accession = None
            accession_elem = soup.find("dt", string="DrugBank ID")
            if accession_elem:
                accession_dd = accession_elem.find_next("dd")
                if accession_dd:
                    accession = accession_dd.get_text(strip=True)
            
            # Fallback to extract from URL
            if not accession:
                accession = url.split("/")[-1] if "/drugs/" in url else None
            
            # Extract general description
            description = None
            description_elem = soup.find("dt", string="Description")
            if description_elem:
                desc_text = description_elem.find_next("dd")
                if desc_text:
                    description = desc_text.get_text(strip=True)
            
            if not name or not accession:
                return None
            
            return {
                "name": name,
                "accession_number": accession,
                "url": url,
                "description": description,
            }
            
        except TimeoutException:
            self.logger.warning(f"Timeout loading page: {url}")
            return None
        except Exception as e:
            self.logger.warning(f"Error scraping page {url}: {str(e)}")
            return None

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
