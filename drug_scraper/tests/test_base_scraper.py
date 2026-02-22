"""Tests for base scraper functionality."""

import pytest
from src.scrapers.base_scraper import BaseScraper


class MockScraper(BaseScraper):
    """Mock scraper for testing."""

    def scrape(self):
        return [{"name": "Test Drug", "id": "1"}]

    def validate_data(self, data):
        return "name" in data and "id" in data


def test_base_scraper_initialization():
    """Test scraper initialization."""
    scraper = MockScraper(name="TestScraper", timeout=15)
    assert scraper.name == "TestScraper"
    assert scraper.timeout == 15


def test_scraper_representation():
    """Test scraper string representation."""
    scraper = MockScraper()
    assert "MockScraper" in repr(scraper)
