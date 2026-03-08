"""Base processor class for document and image processing."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Abstract base class for all document/image processors."""
    
    def __init__(self, name: str):
        """
        Initialize processor.
        
        Args:
            name: Name of the processor
        """
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate_input(self, file_path: str) -> bool:
        """
        Validate input file format and accessibility.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def process(self, file_path: str) -> List[Any]:
        """
        Process file and return processed output.
        
        Args:
            file_path: Path to file to process
            
        Returns:
            List of processed items (pages, images, etc.)
        """
        pass
    
    def _validate_file_exists(self, file_path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists, False otherwise
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
