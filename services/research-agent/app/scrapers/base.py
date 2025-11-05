"""
Base scraper class for all content sources
Provides common functionality for discovering and fetching content
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all scrapers"""

    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        self.source_name = source_name
        self.source_id = source_id
        self.config = config or {}
        self.logger = logging.getLogger(f"scraper.{source_name}")

    @abstractmethod
    def discover(self, since: Optional[datetime] = None, max_items: int = 20) -> List[Dict]:
        """
        Discover new items from the source

        Args:
            since: Only discover items newer than this date
            max_items: Maximum number of items to discover

        Returns:
            List of discovered items with metadata:
            [
                {
                    'external_id': 'unique-id',
                    'title': 'Item title',
                    'url': 'https://...',
                    'authors': 'Author names',
                    'abstract': 'Brief description',
                    'published_date': datetime,
                    'metadata': {...}
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def fetch_content(self, item: Dict) -> Optional[str]:
        """
        Fetch full content for an item

        Args:
            item: Item dictionary from discover()

        Returns:
            Markdown-formatted content string, or None if fetch failed
        """
        pass

    def generate_content_hash(self, content: str) -> str:
        """Generate a hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def should_fetch_item(self, item: Dict) -> bool:
        """
        Determine if an item should be fetched
        Override this for custom filtering logic
        """
        return True

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Remove special characters that might cause issues
        text = text.replace('\x00', '')

        return text.strip()

    def format_authors(self, authors: List[str]) -> str:
        """Format author list as string"""
        if not authors:
            return "Unknown"

        if len(authors) <= 3:
            return ", ".join(authors)
        else:
            return f"{', '.join(authors[:3])}, et al."

    def truncate_abstract(self, abstract: str, max_length: int = 500) -> str:
        """Truncate abstract to reasonable length"""
        if not abstract:
            return ""

        if len(abstract) <= max_length:
            return abstract

        return abstract[:max_length].rsplit(' ', 1)[0] + "..."

