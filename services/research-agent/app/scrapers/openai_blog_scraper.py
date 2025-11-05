"""
OpenAI Blog Scraper
Discovers new posts from OpenAI's official blog
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .base import BaseScraper

class OpenAIBlogScraper(BaseScraper):
    """Scraper for OpenAI blog posts"""

    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config)
        self.base_url = config.get('base_url', "https://openai.com/blog/") if config else "https://openai.com/blog/"

    def discover(self, since: Optional[datetime] = None, max_items: int = 20) -> List[Dict]:
        """
        Discover new blog posts from OpenAI
        """
        if since is None:
            since = datetime.now() - timedelta(days=7)

        self.logger.info(f"Discovering OpenAI blog posts since {since.strftime('%Y-%m-%d')}")

        discovered_items = []

        try:
            # Fetch blog page
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find blog post links (adjust selectors based on actual HTML)
            # This is a placeholder - would need to inspect actual OpenAI blog structure
            articles = soup.find_all('article', limit=max_items)

            for article in articles:
                try:
                    # Extract article details (adjust selectors)
                    title_elem = article.find('h2') or article.find('h3')
                    link_elem = article.find('a')
                    date_elem = article.find('time')
                    excerpt_elem = article.find('p')

                    if not title_elem or not link_elem:
                        continue

                    title = self.clean_text(title_elem.get_text())
                    url = link_elem.get('href')
                    if not url.startswith('http'):
                        url = f"https://openai.com{url}"

                    # Parse date
                    pub_date = datetime.now()
                    if date_elem and date_elem.get('datetime'):
                        pub_date = datetime.fromisoformat(date_elem.get('datetime').replace('Z', '+00:00'))

                    # Skip if too old
                    if pub_date < since:
                        continue

                    excerpt = self.clean_text(excerpt_elem.get_text()) if excerpt_elem else ""

                    item = {
                        'external_id': url,  # Use URL as unique ID
                        'source_type': 'blog',
                        'url': url,
                        'title': title,
                        'authors': 'OpenAI',
                        'abstract': excerpt[:500] if excerpt else title,
                        'published_date': pub_date,
                        'keywords': ['OpenAI', 'announcement', 'blog'],
                        'metadata': {
                            'company': 'OpenAI',
                            'content_type': 'blog_post',
                            'language': 'en'
                        }
                    }

                    discovered_items.append(item)

                except Exception as e:
                    self.logger.error(f"Error parsing article: {e}")
                    continue

            self.logger.info(f"Discovered {len(discovered_items)} posts from OpenAI blog")
            return discovered_items

        except Exception as e:
            self.logger.error(f"Error discovering OpenAI blog posts: {e}")
            return []

    def fetch_content(self, item: Dict) -> Optional[str]:
        """
        Fetch full blog post content
        """
        try:
            self.logger.info(f"Fetching content for: {item['title'][:50]}...")

            url = item['url']
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find main content (adjust selector based on actual HTML)
            content_div = soup.find('article') or soup.find('div', class_='content')

            if not content_div:
                self.logger.warning(f"Could not find content div for {url}")
                return None

            # Extract text content
            # Remove script and style elements
            for script in content_div(["script", "style", "nav", "footer"]):
                script.decompose()

            # Get text
            content = content_div.get_text(separator='\n', strip=True)

            # Format as markdown
            markdown_content = self._format_as_markdown(item, content)

            return markdown_content

        except Exception as e:
            self.logger.error(f"Error fetching content for {item['url']}: {e}")
            return None

    def _format_as_markdown(self, item: Dict, content: str) -> str:
        """
        Format blog post as markdown
        """
        title = item.get('title', 'Untitled')
        url = item.get('url', '')
        published = item.get('published_date')
        excerpt = item.get('abstract', '')

        published_str = published.strftime('%Y-%m-%d') if published else 'Unknown'
        discovered_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        markdown = f"""# {title}

## Post Metadata

**🏢 Source:** OpenAI Blog
**📅 Published:** {published_str}
**🌐 URL:** {url}

## Summary

{excerpt}

## Full Content

{content}

---

## Research Agent Metadata

**🤖 Discovered By:** Research Agent (OpenAI Blog Scraper)
**📅 Discovery Date:** {discovered_str}
**🔍 Source Type:** Company Blog Post
**🏢 Company:** OpenAI
**🌍 Language:** English

**Keywords:** OpenAI, AI announcements, company blog

---

*This content was automatically discovered and ingested by the Research Agent. For the most up-to-date information and images, please visit the original URL above.*
"""

        return markdown

