"""
Hugging Face Papers scraper
Fetches trending papers from huggingface.co/papers
"""
import requests
import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class HuggingFaceScraper(BaseScraper):
    """Scraper for Hugging Face Papers"""

    HF_PAPERS_URL = "https://huggingface.co/papers"

    def discover(self, since: Optional[datetime] = None, max_items: int = 10) -> List[Dict]:
        """
        Discover trending papers from Hugging Face
        """
        if since is None:
            since = datetime.now() - timedelta(days=3)  # Last 3 days

        self.logger.info(f"Discovering Hugging Face papers")

        discovered_items = []

        try:
            # Fetch the papers page
            response = requests.get(self.HF_PAPERS_URL, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find paper cards (this is a simplified parser - may need adjustment)
            # HF page structure may change, so this is a best-effort scraper
            paper_links = soup.find_all('a', href=lambda x: x and '/papers/' in x, limit=max_items)

            for link in paper_links:
                try:
                    paper_url = f"https://huggingface.co{link['href']}" if link['href'].startswith('/') else link['href']

                    # Extract title from link text or find it nearby
                    title = link.get_text(strip=True) or "Untitled Paper"

                    # Generate a unique ID from URL
                    external_id = f"hf-{link['href'].split('/')[-1]}"

                    item = {
                        'external_id': external_id,
                        'title': self.clean_text(title),
                        'url': paper_url,
                        'authors': "Various",  # Would need deeper parsing
                        'abstract': "Trending paper from Hugging Face community",
                        'published_date': datetime.now(),  # Approximate
                        'metadata': {
                            'source': 'huggingface',
                            'trending': True
                        }
                    }

                    discovered_items.append(item)
                    self.logger.debug(f"Discovered: {item['title'][:50]}...")

                except Exception as e:
                    self.logger.error(f"Error parsing paper link: {e}")
                    continue

            self.logger.info(f"Discovered {len(discovered_items)} papers from Hugging Face")
            return discovered_items

        except Exception as e:
            self.logger.error(f"Error discovering Hugging Face papers: {e}")
            return []

    def fetch_content(self, item: Dict) -> Optional[str]:
        """
        Fetch paper content from Hugging Face
        """
        try:
            url = item.get('url')
            self.logger.info(f"Fetching content from: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = item.get('title', 'Untitled')

            # Try to find abstract or description
            abstract_div = soup.find('div', class_='abstract') or soup.find('p')
            abstract = abstract_div.get_text(strip=True) if abstract_div else item.get('abstract', '')

            # Format as markdown
            markdown = f"""# {title}

**Source:** Hugging Face Papers (Community Featured)
**URL:** {url}
**Discovery Date:** {datetime.now().strftime('%Y-%m-%d')}

## Description

{abstract}

## About

This paper was featured on Hugging Face Papers, indicating it has received attention from the ML community. Visit the URL above to see discussions, implementations, and related content.

---

*Auto-discovered by Research Agent*
"""

            return markdown

        except Exception as e:
            self.logger.error(f"Error fetching content for {item['title']}: {e}")
            return None

