"""Data validation utilities."""

from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def validate_drug_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate drug data structure.

    Args:
        data: Dictionary containing drug information

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check required fields
    required_fields = ["name"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")

    # Validate name is string
    if "name" in data and not isinstance(data["name"], str):
        errors.append("Field 'name' must be a string")

    return len(errors) == 0, errors


def sanitize_string(value: str) -> str:
    """
    Sanitize string data.

    Args:
        value: String to sanitize

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    return value.strip()
