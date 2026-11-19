"""Data cleaning and preprocessing utilities."""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Handle data cleaning and preprocessing."""

    @staticmethod
    def clean_drug_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and standardize drug data.

        Args:
            data: List of raw drug records

        Returns:
            List of cleaned drug records
        """
        cleaned = []

        for record in data:
            cleaned_record = DataCleaner._clean_record(record)
            if cleaned_record:
                cleaned.append(cleaned_record)

        logger.info(f"Cleaned {len(cleaned)} out of {len(data)} records")
        return cleaned

    @staticmethod
    def _clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a single record.

        Args:
            record: Single drug record

        Returns:
            Cleaned record or None if invalid
        """
        if not isinstance(record, dict):
            return None

        cleaned = {}

        # Clean string fields
        for key, value in record.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            elif value is None:
                cleaned[key] = ""
            else:
                cleaned[key] = value

        return cleaned
