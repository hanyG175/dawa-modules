"""Configuration management for the drug scraper."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration management."""

    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML config file
            env_file: Path to .env file
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv(".env")

        # Load YAML config if provided
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        # First check environment variables
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return env_value

        # Then check YAML config
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def get_dict(self) -> Dict[str, Any]:
        """Get entire configuration as dictionary."""
        return self.config.copy()


# Global config instance
_config = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
