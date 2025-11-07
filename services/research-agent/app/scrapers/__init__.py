"""
Content scrapers for various AI research sources
31 total sources: 6 legacy + 25 new RSS feeds
"""
from .base import BaseScraper
from .arxiv_scraper import ArxivScraper
from .huggingface_scraper import HuggingFaceScraper
from .tech_news_scraper import TechCrunchAIScraper, VentureBeatAIScraper, TheVergeAIScraper
from .openai_blog_scraper import OpenAIBlogScraper

# New: 25 Enhanced RSS Scrapers (FeedSpot Top 100)
from .rss_scraper import (
    # High-Volume News (7)
    MarkTechPostScraper,
    WiredAIScraper,
    ArsTechnicaAIScraper,
    ScienceDailyAIScraper,
    AINewsScraper,
    GuardianAIScraper,
    InfoWorldAIScraper,

    # Research & Technical Blogs (8)
    GoogleAIBlogScraper,
    MITNewsAIScraper,
    MITTechReviewAIScraper,
    AnalyticsVidhyaScraper,
    KDnuggetsScraper,
    MLMasteryScraper,
    BAIRBlogScraper,
    MicrosoftAIBlogScraper,

    # Industry & Analysis (5)
    UniteAIScraper,
    AIMultipleScraper,
    MarketingAIScraper,
    AITimeJournalScraper,
    DailyAIScraper,

    # Premium Sources (5)
    TowardsDataScienceScraper,
    DeepMindBlogScraper,
    OpenAIBlogScraperNew,
    AnthropicScraper,
    AWSAIBlogScraper
)

__all__ = [
    # Legacy scrapers
    'BaseScraper',
    'ArxivScraper',
    'HuggingFaceScraper',
    'TechCrunchAIScraper',
    'VentureBeatAIScraper',
    'TheVergeAIScraper',
    'OpenAIBlogScraper',

    # New RSS scrapers
    'MarkTechPostScraper',
    'WiredAIScraper',
    'ArsTechnicaAIScraper',
    'ScienceDailyAIScraper',
    'AINewsScraper',
    'GuardianAIScraper',
    'InfoWorldAIScraper',
    'GoogleAIBlogScraper',
    'MITNewsAIScraper',
    'MITTechReviewAIScraper',
    'AnalyticsVidhyaScraper',
    'KDnuggetsScraper',
    'MLMasteryScraper',
    'BAIRBlogScraper',
    'MicrosoftAIBlogScraper',
    'UniteAIScraper',
    'AIMultipleScraper',
    'MarketingAIScraper',
    'AITimeJournalScraper',
    'DailyAIScraper',
    'TowardsDataScienceScraper',
    'DeepMindBlogScraper',
    'OpenAIBlogScraperNew',
    'AnthropicScraper',
    'AWSAIBlogScraper'
]

