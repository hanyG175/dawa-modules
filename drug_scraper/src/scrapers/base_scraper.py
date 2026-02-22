"""Base scraper class defining the interface for all scrapers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all drug data scrapers."""

    def __init__(self, name: str, timeout: int = 30):
        """
        Initialize the base scraper.

        Args:
            name: Name of the scraper
            timeout: Request timeout in seconds
        """
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape data from the source.

        Returns:
            List of dictionaries containing scraped drug data
        """
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped data.

        Args:
            data: Dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
