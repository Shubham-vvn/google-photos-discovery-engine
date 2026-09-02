"""
Base Scraper Interface

Defines the abstract interface for all data source scrapers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class BaseScraper(ABC):
    """Abstract base class for all data source scrapers."""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape data from the source.
        Returns a list of raw documents (dicts).
        """
        pass

    @abstractmethod
    def get_source_id(self, raw_item: Dict[str, Any]) -> str:
        """Extract the platform-specific unique ID."""
        pass

    def create_raw_document(
        self,
        raw_item: Dict[str, Any],
        text: str,
        source_id: str,
        metadata: Dict[str, Any],
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a standardized raw document dictionary."""
        return {
            "source": self.source_name,
            "source_id": str(source_id),
            "author": author or str(source_id),
            "text": text,
            "timestamp": metadata.get("timestamp"),
            "metadata": metadata,
            "scraped_at": datetime.utcnow().isoformat(),
        }
