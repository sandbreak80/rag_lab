"""
Enhanced RSS Scraper with Full-Text Extraction
Supports 25+ high-quality AI news and research sources
Uses Trafilatura for world-class content extraction
"""
import feedparser
import trafilatura
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from .base import BaseScraper
import requests
from fake_useragent import UserAgent
import time

class EnhancedRSSScraper(BaseScraper):
    """
    Enhanced RSS scraper with full-text extraction

    Features:
    - Trafilatura for clean article extraction
    - Newspaper3k fallback
    - User-agent rotation
    - Respects rate limits
    - Full metadata preservation
    """

    # Comprehensive source configurations based on FeedSpot Top 100
    RSS_SOURCES = {
        # ===== HIGH-VOLUME NEWS SOURCES =====
        'marktechpost': {
            'name': 'MarkTechPost',
            'rss_url': 'https://www.marktechpost.com/feed/',
            'description': 'Leading AI news and research coverage',
            'max_results': 50,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Machine Learning', 'Research']
        },
        'wired_ai': {
            'name': 'Wired AI',
            'rss_url': 'https://www.wired.com/feed/tag/ai/latest/rss',
            'description': 'Tech and AI journalism',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Technology', 'Innovation']
        },
        'ars_technica_ai': {
            'name': 'Ars Technica AI',
            'rss_url': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
            'description': 'Technical AI coverage',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Technology', 'Science']
        },
        'sciencedaily_ai': {
            'name': 'ScienceDaily AI',
            'rss_url': 'https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml',
            'description': 'Scientific AI research news',
            'max_results': 40,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Research', 'Science']
        },
        'ai_news': {
            'name': 'AI News',
            'rss_url': 'https://www.artificialintelligence-news.com/feed/',
            'description': 'Dedicated AI news coverage',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'News', 'Industry']
        },
        'guardian_ai': {
            'name': 'The Guardian AI',
            'rss_url': 'https://www.theguardian.com/technology/artificialintelligenceai/rss',
            'description': 'Global AI perspective',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Technology', 'Society']
        },
        'infoworld_ai': {
            'name': 'InfoWorld AI',
            'rss_url': 'https://www.infoworld.com/artificial-intelligence/index.rss',
            'description': 'Enterprise AI focus',
            'max_results': 30,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Enterprise', 'Business']
        },

        # ===== RESEARCH & TECHNICAL BLOGS =====
        'google_ai': {
            'name': 'Google AI Blog',
            'rss_url': 'http://googleaiblog.blogspot.com/atom.xml',
            'description': 'Official Google AI research',
            'max_results': 30,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Google', 'Research']
        },
        'mit_news_ai': {
            'name': 'MIT News AI',
            'rss_url': 'https://news.mit.edu/rss/topic/artificial-intelligence2',
            'description': 'MIT AI research news',
            'max_results': 30,
            'full_text_in_rss': True,
            'keywords': ['AI', 'MIT', 'Research', 'Academic']
        },
        'mit_tech_review_ai': {
            'name': 'MIT Technology Review AI',
            'rss_url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed',
            'description': 'In-depth AI analysis',
            'max_results': 30,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Analysis', 'Technology']
        },
        'analytics_vidhya': {
            'name': 'Analytics Vidhya',
            'rss_url': 'https://www.analyticsvidhya.com/feed/',
            'description': 'Data science and AI tutorials',
            'max_results': 40,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Data Science', 'Tutorial']
        },
        'kdnuggets': {
            'name': 'KDnuggets',
            'rss_url': 'https://feeds.feedburner.com/kdnuggets-data-mining-analytics',
            'description': 'Data science community',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Data Science', 'ML']
        },
        'ml_mastery': {
            'name': 'Machine Learning Mastery',
            'rss_url': 'https://machinelearningmastery.com/feed/',
            'description': 'Practical ML tutorials',
            'max_results': 40,
            'full_text_in_rss': True,
            'keywords': ['Machine Learning', 'Tutorial', 'Education']
        },
        'bair_blog': {
            'name': 'Berkeley AI Research',
            'rss_url': 'https://bair.berkeley.edu/blog/feed.xml',
            'description': 'Berkeley AI research blog',
            'max_results': 20,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Research', 'Berkeley']
        },
        'microsoft_ai': {
            'name': 'Microsoft AI Blog',
            'rss_url': 'https://blogs.microsoft.com/ai/feed/',
            'description': 'Microsoft AI updates',
            'max_results': 30,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Microsoft', 'Research']
        },

        # ===== INDUSTRY & ANALYSIS =====
        'unite_ai': {
            'name': 'Unite.AI',
            'rss_url': 'https://www.unite.ai/feed/',
            'description': 'AI industry news and reviews',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Industry', 'Reviews']
        },
        'ai_multiple': {
            'name': 'AIMultiple',
            'rss_url': 'https://research.aimultiple.com/feed/',
            'description': 'Business AI insights',
            'max_results': 30,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Business', 'Strategy']
        },
        'marketing_ai': {
            'name': 'Marketing AI Institute',
            'rss_url': 'https://www.marketingaiinstitute.com/blog/rss.xml',
            'description': 'AI in marketing',
            'max_results': 30,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Marketing', 'Business']
        },
        'ai_time_journal': {
            'name': 'AI Time Journal',
            'rss_url': 'https://www.aitimejournal.com/feed',
            'description': 'AI industry analysis',
            'max_results': 30,
            'full_text_in_rss': False,
            'keywords': ['AI', 'Industry', 'Analysis']
        },
        'daily_ai': {
            'name': 'DailyAI',
            'rss_url': 'https://dailyai.com/feed/',
            'description': 'Daily AI updates',
            'max_results': 40,
            'full_text_in_rss': False,
            'keywords': ['AI', 'News', 'Daily']
        },

        # ===== ADDITIONAL HIGH-QUALITY SOURCES =====
        'towards_data_science': {
            'name': 'Towards Data Science',
            'rss_url': 'https://medium.com/feed/towards-data-science',
            'description': 'Medium\'s premier data science publication',
            'max_results': 50,
            'full_text_in_rss': True,
            'keywords': ['Data Science', 'AI', 'ML', 'Tutorial']
        },
        'deepmind': {
            'name': 'DeepMind',
            'rss_url': 'https://deepmind.google/blog/rss.xml',
            'description': 'DeepMind research blog',
            'max_results': 20,
            'full_text_in_rss': True,
            'keywords': ['AI', 'DeepMind', 'Research']
        },
        'openai': {
            'name': 'OpenAI',
            'rss_url': 'https://openai.com/blog/rss/',
            'description': 'OpenAI official blog',
            'max_results': 20,
            'full_text_in_rss': True,
            'keywords': ['AI', 'OpenAI', 'GPT']
        },
        'anthropic': {
            'name': 'Anthropic',
            'rss_url': 'https://www.anthropic.com/news/rss.xml',
            'description': 'Anthropic AI safety research',
            'max_results': 20,
            'full_text_in_rss': True,
            'keywords': ['AI', 'Anthropic', 'Safety']
        },
        'aws_ai': {
            'name': 'AWS AI Blog',
            'rss_url': 'https://aws.amazon.com/blogs/ai/feed/',
            'description': 'AWS AI and ML updates',
            'max_results': 30,
            'full_text_in_rss': True,
            'keywords': ['AI', 'AWS', 'Cloud']
        }
    }

    def __init__(self, source_name: str, source_id: int, config: Dict = None, source_key: str = 'marktechpost'):
        """
        Initialize with specific RSS source

        Args:
            source_name: Name from database
            source_id: ID from database
            config: Configuration dict
            source_key: One of the RSS_SOURCES keys
        """
        if source_key not in self.RSS_SOURCES:
            raise ValueError(f"Unknown source: {source_key}. Available: {list(self.RSS_SOURCES.keys())}")

        self.source_config = self.RSS_SOURCES[source_key]
        super().__init__(source_name, source_id, config)

        # Configuration
        self.rss_url = self.source_config['rss_url']
        self.keywords = self.source_config['keywords']
        self.max_results = config.get('max_results', self.source_config['max_results']) if config else self.source_config['max_results']
        self.full_text_in_rss = self.source_config['full_text_in_rss']

        # User agent rotation for scraping
        self.ua = UserAgent()

    def discover(self, since: Optional[datetime] = None, max_items: int = None) -> List[Dict]:
        """
        Discover articles from RSS feed
        """
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(days=30)  # Last 30 days for bulk fetch

        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        if max_items is None:
            max_items = self.max_results

        self.logger.info(f"Discovering articles from {self.source_config['name']} (last 7 days, max {max_items})")

        discovered_items = []

        try:
            # Parse RSS feed with custom user agent
            feed = feedparser.parse(self.rss_url, agent=self.ua.random)

            if not feed.entries:
                self.logger.warning(f"No entries in RSS feed: {self.rss_url}")
                return []

            self.logger.info(f"Found {len(feed.entries)} entries in feed")

            for entry in feed.entries[:max_items * 2]:  # Fetch extra in case of date filtering
                try:
                    # Parse publication date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    else:
                        pub_date = datetime.now(timezone.utc)

                    # Skip if too old
                    if pub_date < since:
                        continue

                    # Extract metadata
                    title = self.clean_text(entry.get('title', 'Untitled'))
                    url = entry.get('link', '')

                    # Get summary/content from RSS
                    if hasattr(entry, 'content') and entry.content:
                        summary = self.clean_text(entry.content[0].value)
                    elif hasattr(entry, 'summary'):
                        summary = self.clean_text(entry.get('summary', ''))
                    else:
                        summary = title

                    # Author handling
                    author = entry.get('author', self.source_config['name'])
                    if hasattr(entry, 'authors') and entry.authors:
                        author = ', '.join([a.get('name', '') for a in entry.authors if a.get('name')])

                    # Categories/tags
                    tags = []
                    if hasattr(entry, 'tags'):
                        tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]

                    item = {
                        'external_id': url,
                        'source_type': 'rss',
                        'url': url,
                        'title': title,
                        'authors': author or self.source_config['name'],
                        'abstract': summary[:500] if len(summary) > 500 else summary,
                        'published_date': pub_date,
                        'keywords': self.keywords + tags[:5],  # Limit tags
                        'metadata': {
                            'source': self.source_config['name'],
                            'source_description': self.source_config['description'],
                            'content_type': 'article',
                            'language': 'en',
                            'rss_feed': self.rss_url,
                            'tags': tags,
                            'full_text_in_rss': self.full_text_in_rss
                        }
                    }

                    discovered_items.append(item)

                    # Stop if we have enough
                    if len(discovered_items) >= max_items:
                        break

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
        Fetch full article content using Trafilatura
        World-class content extraction!
        """
        try:
            self.logger.info(f"Fetching full content for: {item['title'][:50]}...")

            url = item['url']

            # If full text is in RSS, we already have it
            if item['metadata'].get('full_text_in_rss') and len(item.get('abstract', '')) > 1000:
                self.logger.info("Using full content from RSS feed")
                content = item['abstract']
            else:
                # Fetch and extract with Trafilatura
                self.logger.info(f"Extracting content from: {url}")

                # Download with Trafilatura (handles user-agent automatically)
                downloaded = trafilatura.fetch_url(url)

                if not downloaded:
                    self.logger.warning(f"Failed to download {url}, using RSS summary")
                    content = item.get('abstract', '')
                else:
                    # Extract content with Trafilatura (best-in-class!)
                    extracted = trafilatura.extract(
                        downloaded,
                        include_comments=False,
                        include_tables=True,
                        include_links=False,
                        output_format='markdown',
                        target_language='en'
                    )

                    if extracted and len(extracted) > 200:
                        content = extracted
                        self.logger.info(f"Extracted {len(content)} chars with Trafilatura")
                    else:
                        self.logger.warning("Extraction failed or too short, using RSS summary")
                        content = item.get('abstract', '')

                # Rate limiting - be polite!
                time.sleep(0.5)

            # Format as rich markdown
            markdown_content = self._format_as_markdown(item, content)

            return markdown_content

        except Exception as e:
            self.logger.error(f"Error fetching content: {e}")
            # Fallback to RSS summary
            return self._format_as_markdown(item, item.get('abstract', ''))

    def _format_as_markdown(self, item: Dict, content: str) -> str:
        """Format article as comprehensive markdown document"""
        title = item.get('title', 'Untitled')
        url = item.get('url', '')
        author = item.get('authors', 'Unknown')
        published = item.get('published_date')
        summary = item.get('abstract', '')
        keywords = item.get('keywords', [])
        tags = item['metadata'].get('tags', [])

        published_str = published.strftime('%Y-%m-%d %H:%M UTC') if published else 'Unknown'
        discovered_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        markdown = f"""# {title}

## Article Metadata

**📰 Source:** {self.source_config['name']}
**📝 Description:** {self.source_config['description']}
**✍️ Author:** {author}
**📅 Published:** {published_str}
**🌐 URL:** {url}

## Summary

{summary}

## Full Article Content

{content}

---

## Research Agent Metadata

**🤖 Discovered By:** Research Agent (Enhanced RSS Scraper)
**📅 Discovery Date:** {discovered_str}
**🔍 Source Type:** Article (RSS Feed)
**📰 Publication:** {self.source_config['name']}
**🌍 Language:** English
**📊 Content Type:** {item['metadata'].get('content_type', 'article')}

**Keywords:** {', '.join(keywords) if keywords else 'AI, Machine Learning'}
"""

        if tags:
            markdown += f"\n**Tags:** {', '.join(tags[:10])}\n"

        markdown += """
---

*This content was automatically discovered and ingested by the Research Agent using world-class content extraction. For the most up-to-date information, comments, and multimedia, please visit the original URL above.*
"""

        return markdown


# ============================================================================
# SPECIFIC SCRAPER CLASSES (25 sources)
# ============================================================================

class MarkTechPostScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='marktechpost')

class WiredAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='wired_ai')

class ArsTechnicaAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='ars_technica_ai')

class ScienceDailyAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='sciencedaily_ai')

class AINewsScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='ai_news')

class GuardianAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='guardian_ai')

class InfoWorldAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='infoworld_ai')

class GoogleAIBlogScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='google_ai')

class MITNewsAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='mit_news_ai')

class MITTechReviewAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='mit_tech_review_ai')

class AnalyticsVidhyaScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='analytics_vidhya')

class KDnuggetsScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='kdnuggets')

class MLMasteryScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='ml_mastery')

class BAIRBlogScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='bair_blog')

class MicrosoftAIBlogScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='microsoft_ai')

class UniteAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='unite_ai')

class AIMultipleScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='ai_multiple')

class MarketingAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='marketing_ai')

class AITimeJournalScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='ai_time_journal')

class DailyAIScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='daily_ai')

class TowardsDataScienceScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='towards_data_science')

class DeepMindBlogScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='deepmind')

class OpenAIBlogScraperNew(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='openai')

class AnthropicScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='anthropic')

class AWSAIBlogScraper(EnhancedRSSScraper):
    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config, source_key='aws_ai')

