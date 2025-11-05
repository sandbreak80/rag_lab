"""
Tech News Scraper
Generic scraper for tech news sites using RSS feeds
"""
import feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from .base import BaseScraper
import requests
from bs4 import BeautifulSoup

class TechNewsScraper(BaseScraper):
    """Generic scraper for tech news RSS feeds"""

    # Common tech news RSS feeds
    NEWS_SOURCES = {
        'techcrunch_ai': {
            'name': 'TechCrunch AI',
            'rss_url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
            'keywords': ['AI', 'TechCrunch', 'news']
        },
        'venturebeat_ai': {
            'name': 'VentureBeat AI',
            'rss_url': 'https://venturebeat.com/category/ai/feed/',
            'keywords': ['AI', 'VentureBeat', 'news']
        },
        'theverge_ai': {
            'name': 'The Verge AI',
            'rss_url': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
            'keywords': ['AI', 'The Verge', 'news']
        }
    }

    def __init__(self, source_name: str, source_id: int, config: Dict = None, source_key: str = 'techcrunch_ai'):
        """
        Initialize with specific news source

        Args:
            source_name: Name from database
            source_id: ID from database
            config: Configuration dict
            source_key: One of the NEWS_SOURCES keys
        """
        if source_key not in self.NEWS_SOURCES:
            raise ValueError(f"Unknown source: {source_key}. Available: {list(self.NEWS_SOURCES.keys())}")

        self.source_config = self.NEWS_SOURCES[source_key]
        super().__init__(source_name, source_id, config)
        self.rss_url = self.source_config['rss_url']
        self.keywords = self.source_config['keywords']

    def discover(self, since: Optional[datetime] = None, max_items: int = 20) -> List[Dict]:
        """
        Discover news articles from RSS feed
        """
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(days=1)

        # Ensure timezone-aware
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        self.logger.info(f"Discovering articles from {self.source_config['name']} since {since.strftime('%Y-%m-%d')}")

        discovered_items = []

        try:
            # Parse RSS feed
            feed = feedparser.parse(self.rss_url)

            if not feed.entries:
                self.logger.warning(f"No entries found in feed: {self.rss_url}")
                return []

            for entry in feed.entries[:max_items]:
                try:
                    # Parse publication date
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed'):
                        pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    else:
                        pub_date = datetime.now(timezone.utc)

                    # Skip if too old
                    if pub_date < since:
                        continue

                    # Extract details
                    title = self.clean_text(entry.get('title', 'Untitled'))
                    url = entry.get('link', '')
                    summary = self.clean_text(entry.get('summary', ''))
                    author = entry.get('author', self.source_config['name'])

                    item = {
                        'external_id': url,  # Use URL as unique ID
                        'source_type': 'news',
                        'url': url,
                        'title': title,
                        'authors': author,
                        'abstract': summary[:500] if summary else title,
                        'published_date': pub_date,
                        'keywords': self.keywords,
                        'metadata': {
                            'source': self.source_config['name'],
                            'content_type': 'news_article',
                            'language': 'en',
                            'rss_feed': self.rss_url
                        }
                    }

                    discovered_items.append(item)

                except Exception as e:
                    self.logger.error(f"Error parsing entry: {e}")
                    continue

            self.logger.info(f"Discovered {len(discovered_items)} articles from {self.source_config['name']}")
            return discovered_items

        except Exception as e:
            self.logger.error(f"Error discovering articles: {e}")
            return []

    def fetch_content(self, item: Dict) -> Optional[str]:
        """
        Fetch full article content
        Uses basic web scraping - could be enhanced with Trafilatura
        """
        try:
            self.logger.info(f"Fetching content for: {item['title'][:50]}...")

            url = item['url']

            # Fetch page
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; RAG-Lab-Bot/1.0)'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to find article content
            # (Different sites use different selectors)
            content_selectors = [
                {'name': 'article'},
                {'class_': 'article-content'},
                {'class_': 'entry-content'},
                {'class_': 'post-content'},
                {'id': 'article-body'}
            ]

            content_div = None
            for selector in content_selectors:
                content_div = soup.find(**selector)
                if content_div:
                    break

            if not content_div:
                # Fallback: use summary from RSS
                self.logger.warning(f"Could not find article content, using RSS summary")
                content = item.get('abstract', '')
            else:
                # Remove unwanted elements
                for unwanted in content_div(["script", "style", "nav", "aside", "footer", "iframe"]):
                    unwanted.decompose()

                # Extract text
                content = content_div.get_text(separator='\n\n', strip=True)

            # Format as markdown
            markdown_content = self._format_as_markdown(item, content)

            return markdown_content

        except Exception as e:
            self.logger.error(f"Error fetching content: {e}")
            # Return RSS summary as fallback
            return self._format_as_markdown(item, item.get('abstract', ''))

    def _format_as_markdown(self, item: Dict, content: str) -> str:
        """Format news article as markdown"""
        title = item.get('title', 'Untitled')
        url = item.get('url', '')
        author = item.get('authors', 'Unknown')
        published = item.get('published_date')
        summary = item.get('abstract', '')

        published_str = published.strftime('%Y-%m-%d %H:%M UTC') if published else 'Unknown'
        discovered_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        markdown = f"""# {title}

## Article Metadata

**📰 Source:** {self.source_config['name']}
**✍️ Author:** {author}
**📅 Published:** {published_str}
**🌐 URL:** {url}

## Summary

{summary}

## Full Article

{content}

---

## Research Agent Metadata

**🤖 Discovered By:** Research Agent (Tech News Scraper)
**📅 Discovery Date:** {discovered_str}
**🔍 Source Type:** News Article
**📰 Publication:** {self.source_config['name']}
**🌍 Language:** English

**Keywords:** {', '.join(self.keywords)}

---

*This content was automatically discovered and ingested by the Research Agent. For the most up-to-date information, comments, and images, please visit the original URL above.*
"""

        return markdown


# Create specific scraper instances
class TechCrunchAIScraper(TechNewsScraper):
    """TechCrunch AI news scraper"""
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='techcrunch_ai')


class VentureBeatAIScraper(TechNewsScraper):
    """VentureBeat AI news scraper"""
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='venturebeat_ai')


class TheVergeAIScraper(TechNewsScraper):
    """The Verge AI news scraper"""
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='theverge_ai')

