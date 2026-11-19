"""Data storage management."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataStorage:
    """Manage data persistence and retrieval."""

    def __init__(self, storage_path: str = "./data"):
        """
        Initialize data storage.

        Args:
            storage_path: Base path for data storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_json(self, data: List[Dict[str, Any]], filename: str) -> bool:
        """
        Save data as JSON.

        Args:
            data: List of dictionaries to save
            filename: Output filename

        Returns:
            True if successful
        """
        try:
            output_path = self.storage_path / filename
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} records to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            return False

    def save_csv(self, data: List[Dict[str, Any]], filename: str) -> bool:
        """
        Save data as CSV.

        Args:
            data: List of dictionaries to save
            filename: Output filename

        Returns:
            True if successful
        """
        try:
            if not data:
                logger.warning("No data to save")
                return False

            output_path = self.storage_path / filename
            keys = data[0].keys()

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"Saved {len(data)} records to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return False

    def load_json(self, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load data from JSON.

        Args:
            filename: Input filename

        Returns:
            List of dictionaries or None if error
        """
        try:
            input_path = self.storage_path / filename
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} records from {input_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return None
