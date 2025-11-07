"""
Research Agent Service
Autonomous background agent for discovering and ingesting AI research content
"""
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict
from flask import Flask, request, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# Add common to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace')

from config import SERVICE_NAME, SERVICE_PORT
from database import db
from scrapers import (
    # Legacy scrapers (6)
    ArxivScraper,
    HuggingFaceScraper,
    TechCrunchAIScraper,
    VentureBeatAIScraper,
    TheVergeAIScraper,
    OpenAIBlogScraper,
    # New RSS scrapers (25) - FeedSpot Top 100
    MarkTechPostScraper,
    WiredAIScraper,
    ArsTechnicaAIScraper,
    ScienceDailyAIScraper,
    AINewsScraper,
    GuardianAIScraper,
    InfoWorldAIScraper,
    GoogleAIBlogScraper,
    MITNewsAIScraper,
    MITTechReviewAIScraper,
    AnalyticsVidhyaScraper,
    KDnuggetsScraper,
    MLMasteryScraper,
    BAIRBlogScraper,
    MicrosoftAIBlogScraper,
    UniteAIScraper,
    AIMultipleScraper,
    MarketingAIScraper,
    AITimeJournalScraper,
    DailyAIScraper,
    TowardsDataScienceScraper,
    DeepMindBlogScraper,
    OpenAIBlogScraperNew,
    AnthropicScraper,
    AWSAIBlogScraper
)

# Import build info
try:
    from services.common.build_info import get_service_version
except ImportError:
    def get_service_version(name):
        return {'service': name, 'version': '1.0.0', 'build_number': 'dev', 'environment': 'development'}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
INGEST_SERVICE_URL = os.getenv('INGEST_SERVICE_URL', 'http://ingest-service:8001')

# Scheduler
scheduler = BackgroundScheduler()
scheduler_running = False

# ============================================================================
# SCRAPER REGISTRY
# ============================================================================

SCRAPER_CLASSES = {
    # Legacy scrapers (6)
    'arxiv': ArxivScraper,
    'huggingface': HuggingFaceScraper,
    'techcrunch': TechCrunchAIScraper,
    'venturebeat': VentureBeatAIScraper,
    'theverge': TheVergeAIScraper,
    'openai_blog': OpenAIBlogScraper,

    # High-Volume News Sources (7)
    'marktechpost': MarkTechPostScraper,
    'wired_ai': WiredAIScraper,
    'ars_technica_ai': ArsTechnicaAIScraper,
    'sciencedaily_ai': ScienceDailyAIScraper,
    'ai_news': AINewsScraper,
    'guardian_ai': GuardianAIScraper,
    'infoworld_ai': InfoWorldAIScraper,

    # Research & Technical Blogs (8)
    'google_ai': GoogleAIBlogScraper,
    'mit_news_ai': MITNewsAIScraper,
    'mit_tech_review_ai': MITTechReviewAIScraper,
    'analytics_vidhya': AnalyticsVidhyaScraper,
    'kdnuggets': KDnuggetsScraper,
    'ml_mastery': MLMasteryScraper,
    'bair_blog': BAIRBlogScraper,
    'microsoft_ai': MicrosoftAIBlogScraper,

    # Industry & Analysis (5)
    'unite_ai': UniteAIScraper,
    'ai_multiple': AIMultipleScraper,
    'marketing_ai': MarketingAIScraper,
    'ai_time_journal': AITimeJournalScraper,
    'daily_ai': DailyAIScraper,

    # Premium Sources (5)
    'towards_data_science': TowardsDataScienceScraper,
    'deepmind': DeepMindBlogScraper,
    'openai': OpenAIBlogScraperNew,
    'anthropic': AnthropicScraper,
    'aws_ai': AWSAIBlogScraper,
}

def get_scraper(source):
    """Get scraper instance for a source"""
    scraper_class = SCRAPER_CLASSES.get(source['type'])
    if not scraper_class:
        raise ValueError(f"Unknown scraper type: {source['type']}")

    # Parse config JSON if it exists
    config = eval(source['config']) if source['config'] else {}

    return scraper_class(source['name'], source['id'], config)

# ============================================================================
# FETCH LOGIC
# ============================================================================

def fetch_from_source(source_id: int, manual: bool = False):
    """
    Fetch new content from a specific source
    """
    start_time = time.time()
    source = db.get_source(source_id)

    if not source:
        logger.error(f"Source {source_id} not found")
        return

    logger.info(f"{'[MANUAL]' if manual else '[SCHEDULED]'} Starting fetch for: {source['name']}")

    items_discovered = 0
    items_ingested = 0
    items_failed = 0
    error_message = None

    try:
        # Get scraper
        scraper = get_scraper(source)

        # Determine "since" date
        # For learning lab: always look back at least 7 days to ensure demo works
        if source['last_fetched']:
            since = datetime.fromisoformat(source['last_fetched'])
            # Ensure we look back at least 7 days for demo/testing
            min_lookback = datetime.now() - timedelta(days=7)
            if since > min_lookback:
                since = min_lookback
                logger.info(f"Expanded lookback window to 7 days for demo purposes")
        else:
            since = datetime.now() - timedelta(days=7)  # First run: last week

        # Discover items
        logger.info(f"Discovering items since {since.strftime('%Y-%m-%d %H:%M')}")
        discovered = scraper.discover(since=since, max_items=20)
        items_discovered = len(discovered)
        logger.info(f"Discovered {items_discovered} items")

        # Process each item
        for item in discovered:
            try:
                # Create item in database (or get existing)
                item_id = db.create_item(
                    source_id=source_id,
                    external_id=item['external_id'],
                    title=item['title'],
                    url=item['url'],
                    authors=item.get('authors'),
                    abstract=item.get('abstract'),
                    metadata=item.get('metadata')
                )

                if item_id is None:
                    # Item already exists, check if we should retry
                    existing_item = db.find_item_by_external_id(item['external_id'])
                    if existing_item and existing_item['status'] == 'failed':
                        logger.info(f"Retrying failed item: {item['external_id']}")
                        item_id = existing_item['id']
                    elif existing_item and existing_item['status'] == 'ingested':
                        logger.debug(f"Item already ingested: {item['external_id']}")
                        continue
                    else:
                        logger.debug(f"Item already exists: {item['external_id']}")
                        continue

                # Fetch full content
                logger.info(f"Fetching content for: {item['title'][:50]}...")
                content = scraper.fetch_content(item)

                if not content:
                    logger.warning(f"No content fetched for item {item_id}")
                    db.update_item_status(item_id, 'failed', 'Failed to fetch content')
                    items_failed += 1
                    continue

                # Ingest into RAG system
                success = ingest_content(item, content)

                if success:
                    db.update_item_status(item_id, 'ingested')
                    items_ingested += 1
                    logger.info(f"✅ Ingested: {item['title'][:50]}...")
                else:
                    db.update_item_status(item_id, 'failed', 'Ingestion failed')
                    items_failed += 1
                    logger.warning(f"❌ Failed to ingest: {item['title'][:50]}...")

            except Exception as e:
                logger.error(f"Error processing item: {e}")
                items_failed += 1
                continue

        status = 'success' if items_failed == 0 else ('partial' if items_ingested > 0 else 'failed')

    except Exception as e:
        logger.error(f"Error fetching from {source['name']}: {e}")
        error_message = str(e)
        status = 'failed'

    # Record fetch history
    duration = time.time() - start_time
    db.create_fetch_record(
        source_id=source_id,
        items_discovered=items_discovered,
        items_ingested=items_ingested,
        items_failed=items_failed,
        status=status,
        duration_seconds=duration,
        error_message=error_message
    )

    logger.info(f"Fetch complete: {items_ingested}/{items_discovered} ingested in {duration:.1f}s (Status: {status})")

def ingest_content(item: Dict, content: str) -> bool:
    """
    Ingest content into the RAG system via ingest service
    """
    try:
        # Prepare markdown content with metadata
        filename = f"research_{item['external_id']}.md"

        # Call ingest service
        response = requests.post(
            f"{INGEST_SERVICE_URL}/ingest",
            json={
                'content': content,
                'filename': filename,
                'metadata': {
                    'source': 'research-agent',
                    'external_id': item['external_id'],
                    'title': item['title'],
                    'url': item['url'],
                    'authors': item.get('authors'),
                    'ingested_at': datetime.now().isoformat(),
                    'tags': ['research', 'auto-discovered']
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            logger.info(f"Successfully ingested content")
            return True
        else:
            logger.error(f"Ingest service returned {response.status_code}: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error ingesting content: {e}")
        return False

# ============================================================================
# SCHEDULER
# ============================================================================

def scheduled_fetch_all():
    """Scheduled job to fetch from all enabled sources"""
    logger.info("⏰ Scheduled fetch triggered for all enabled sources")

    sources = db.get_all_sources(enabled_only=True)

    for source in sources:
        try:
            fetch_from_source(source['id'], manual=False)
        except Exception as e:
            logger.error(f"Error in scheduled fetch for {source['name']}: {e}")

def start_scheduler():
    """Start the background scheduler"""
    global scheduler_running

    if scheduler_running:
        logger.warning("Scheduler already running")
        return

    # Schedule daily fetch at 2 AM UTC
    scheduler.add_job(
        scheduled_fetch_all,
        'cron',
        hour=2,
        minute=0,
        id='daily_fetch',
        replace_existing=True
    )

    scheduler.start()
    scheduler_running = True
    logger.info("✅ Scheduler started - daily fetch at 02:00 UTC")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler_running

    if not scheduler_running:
        return

    scheduler.shutdown()
    scheduler_running = False
    logger.info("Scheduler stopped")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint with build information"""
    build_info = get_service_version(SERVICE_NAME)
    return jsonify({
        'status': 'healthy',
        'scheduler_running': scheduler_running,
        'timestamp': datetime.now().isoformat(),
        **build_info
    })

@app.route('/status', methods=['GET'])
def status():
    """Get current status and statistics"""
    stats = db.get_stats()
    sources = db.get_all_sources()

    # Get next run time
    next_run = None
    if scheduler_running:
        jobs = scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None

    return jsonify({
        'status': 'idle' if not scheduler_running else 'running',
        'scheduler_running': scheduler_running,
        'next_scheduled_run': next_run,
        'stats': stats,
        'sources': [{
            'id': s['id'],
            'name': s['name'],
            'type': s['type'],
            'enabled': bool(s['enabled']),
            'last_fetched': s['last_fetched'],
            'total_items_fetched': s['total_items_fetched']
        } for s in sources]
    })

@app.route('/sources', methods=['GET'])
def get_sources():
    """Get all sources"""
    sources = db.get_all_sources()
    return jsonify({'sources': sources})

@app.route('/sources', methods=['POST'])
def create_source():
    """Create a new source"""
    data = request.json

    source_id = db.create_source(
        name=data['name'],
        source_type=data['type'],
        url=data['url'],
        config=data.get('config'),
        enabled=data.get('enabled', True)
    )

    return jsonify({'success': True, 'source_id': source_id}), 201

@app.route('/sources/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    """Update a source"""
    data = request.json
    db.update_source(source_id, **data)
    return jsonify({'success': True})

@app.route('/trigger/<int:source_id>', methods=['POST'])
def trigger_fetch(source_id):
    """Manually trigger a fetch for specific source"""
    fetch_from_source(source_id, manual=True)
    return jsonify({'success': True, 'message': f'Fetch triggered for source {source_id}'})

@app.route('/trigger/all', methods=['POST'])
def trigger_fetch_all():
    """Manually trigger fetch for all enabled sources"""
    sources = db.get_all_sources(enabled_only=True)

    for source in sources:
        try:
            fetch_from_source(source['id'], manual=True)
        except Exception as e:
            logger.error(f"Error fetching from {source['name']}: {e}")

    return jsonify({'success': True, 'message': f'Fetch triggered for {len(sources)} sources'})

@app.route('/trigger/custom', methods=['POST'])
def trigger_fetch_custom():
    """
    Trigger fetch with custom parameters (for UI)

    JSON body:
        source_limit: Number of sources to fetch from (1-31, default: all)
        days_back: Days of history to fetch (1-90, default: 30)
        rebuild_kg: Whether to rebuild knowledge graph after (default: true)

    Example:
        POST /trigger/custom
        {
            "source_limit": 10,
            "days_back": 7,
            "rebuild_kg": true
        }
    """
    import threading

    data = request.get_json() or {}
    source_limit = data.get('source_limit', 31)  # Default: all sources
    days_back = data.get('days_back', 30)  # Default: 30 days
    rebuild_kg = data.get('rebuild_kg', True)  # Default: rebuild KG

    # Validate parameters
    source_limit = max(1, min(source_limit, 31))  # Clamp 1-31
    days_back = max(1, min(days_back, 90))  # Clamp 1-90

    # Get sources
    all_sources = db.get_all_sources(enabled_only=True)
    sources_to_fetch = all_sources[:source_limit]

    logger.info(f"Custom fetch triggered: {source_limit} sources, {days_back} days")

    def fetch_and_rebuild():
        """Background task to fetch and rebuild KG"""
        try:
            # Fetch from selected sources
            processed = 0
            errors = []
            items_count = 0

            for source in sources_to_fetch:
                try:
                    # Note: days_back parameter is received from UI but not yet implemented
                    # TODO: Update fetch_from_source to accept days_back parameter
                    result = fetch_from_source(source['id'], manual=True)
                    processed += 1
                    # Note: fetch_from_source doesn't return item count easily
                except Exception as e:
                    error_msg = f"Error fetching {source['name']}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            logger.info(f"Fetch complete: {processed}/{len(sources_to_fetch)} sources")

            # Rebuild knowledge graph if requested
            if rebuild_kg and processed > 0:
                logger.info("Triggering knowledge graph rebuild...")
                try:
                    kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
                    kg_response = requests.post(
                        f"{kg_url}/build",
                        json={'algorithm': 'wikilinks'},
                        timeout=300  # 5 minutes
                    )
                    if kg_response.status_code == 200:
                        logger.info("✅ Knowledge graph rebuilt successfully")
                    else:
                        logger.warning(f"KG rebuild returned {kg_response.status_code}")
                except Exception as e:
                    logger.error(f"Failed to rebuild knowledge graph: {e}")

            logger.info("Custom fetch complete!")

        except Exception as e:
            logger.error(f"Error in fetch_and_rebuild: {e}")

    # Start background task
    thread = threading.Thread(target=fetch_and_rebuild, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': f'Fetch started for {len(sources_to_fetch)} sources ({days_back} days)',
        'source_limit': source_limit,
        'days_back': days_back,
        'sources_selected': len(sources_to_fetch),
        'rebuild_kg': rebuild_kg,
        'status': 'running'
    })

@app.route('/trigger/batch', methods=['POST'])
def trigger_fetch_batch():
    """
    Trigger fetch for a batch of sources (pagination support)

    Query parameters:
        batch_size: Number of sources to fetch (default: 5)
        offset: Starting index (default: 0)

    Example:
        POST /trigger/batch?batch_size=5&offset=0  # First 5 sources
        POST /trigger/batch?batch_size=5&offset=5  # Next 5 sources
    """
    batch_size = request.args.get('batch_size', 5, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Get all enabled sources
    all_sources = db.get_all_sources(enabled_only=True)
    total_sources = len(all_sources)

    # Slice for this batch
    batch_sources = all_sources[offset:offset + batch_size]

    if not batch_sources:
        return jsonify({
            'success': False,
            'message': 'No sources in this batch',
            'offset': offset,
            'batch_size': batch_size,
            'total_sources': total_sources,
            'processed': 0,
            'has_more': False
        })

    # Fetch from batch
    processed = 0
    errors = []
    for source in batch_sources:
        try:
            fetch_from_source(source['id'], manual=True)
            processed += 1
        except Exception as e:
            error_msg = f"Error fetching {source['name']}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    has_more = (offset + batch_size) < total_sources
    next_offset = offset + batch_size if has_more else None

    return jsonify({
        'success': True,
        'message': f'Batch fetch complete: {processed}/{len(batch_sources)} successful',
        'offset': offset,
        'batch_size': batch_size,
        'total_sources': total_sources,
        'processed': processed,
        'errors': errors,
        'has_more': has_more,
        'next_offset': next_offset,
        'progress': f'{min(offset + batch_size, total_sources)}/{total_sources}'
    })

@app.route('/history', methods=['GET'])
def get_history():
    """Get fetch history"""
    limit = request.args.get('limit', 50, type=int)
    history = db.get_fetch_history(limit=limit)
    return jsonify({'history': history})

@app.route('/items', methods=['GET'])
def get_items():
    """Get discovered items"""
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    items = db.get_items(status=status, limit=limit, offset=offset)
    return jsonify({'items': items, 'count': len(items)})

@app.route('/', methods=['GET'])
def root():
    """Service info"""
    return jsonify({
        'service': 'Research Agent',
        'version': '1.0.0',
        'description': 'Autonomous AI research content discovery and ingestion',
        'features': [
            'arXiv paper discovery',
            'Hugging Face Papers tracking',
            'Scheduled automatic fetching',
            'Direct RAG integration',
            'Source management',
            'Fetch history tracking'
        ],
        'endpoints': {
            'status': '/status',
            'sources': '/sources',
            'trigger': '/trigger/all or /trigger/<id>',
            'history': '/history',
            'items': '/items'
        }
    })

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_default_sources():
    """Create default sources if they don't exist"""
    # arXiv source
    if not db.get_source_by_name('arXiv AI/ML'):
        db.create_source(
            name='arXiv AI/ML',
            source_type='arxiv',
            url='https://arxiv.org',
            config={'categories': ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV'], 'max_results': 20},
            enabled=True
        )
        logger.info("Created default arXiv source")

    # Hugging Face source
    if not db.get_source_by_name('Hugging Face Papers'):
        db.create_source(
            name='Hugging Face Papers',
            source_type='huggingface',
            url='https://huggingface.co/papers',
            config={'max_results': 10},
            enabled=True
        )
        logger.info("Created default Hugging Face source")

    # TechCrunch AI source
    if not db.get_source_by_name('TechCrunch AI'):
        db.create_source(
            name='TechCrunch AI',
            source_type='techcrunch',
            url='https://techcrunch.com/category/artificial-intelligence/',
            config={'max_results': 10},
            enabled=True
        )
        logger.info("Created default TechCrunch AI source")

    # VentureBeat AI source
    if not db.get_source_by_name('VentureBeat AI'):
        db.create_source(
            name='VentureBeat AI',
            source_type='venturebeat',
            url='https://venturebeat.com/category/ai/',
            config={'max_results': 10},
            enabled=True
        )
        logger.info("Created default VentureBeat AI source")

    # The Verge AI source
    if not db.get_source_by_name('The Verge AI'):
        db.create_source(
            name='The Verge AI',
            source_type='theverge',
            url='https://www.theverge.com/ai-artificial-intelligence',
            config={'max_results': 10},
            enabled=True
        )
        logger.info("Created default The Verge AI source")

    # OpenAI Blog source
    if not db.get_source_by_name('OpenAI Blog'):
        db.create_source(
            name='OpenAI Blog',
            source_type='openai_blog',
            url='https://openai.com/blog/',
            config={'max_results': 10},
            enabled=True
        )
        logger.info("Created default OpenAI Blog source")

    # ========== NEW: 25 Enhanced RSS Sources (FeedSpot Top 100) ==========

    # HIGH-VOLUME NEWS SOURCES (7)
    if not db.get_source_by_name('MarkTechPost'):
        db.create_source(
            name='MarkTechPost',
            source_type='marktechpost',
            url='https://www.marktechpost.com/feed/',
            config={'max_results': 50},
            enabled=True
        )
        logger.info("Created MarkTechPost source")

    if not db.get_source_by_name('Wired AI'):
        db.create_source(
            name='Wired AI',
            source_type='wired_ai',
            url='https://www.wired.com/feed/tag/ai/latest/rss',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created Wired AI source")

    if not db.get_source_by_name('Ars Technica AI'):
        db.create_source(
            name='Ars Technica AI',
            source_type='ars_technica_ai',
            url='https://feeds.arstechnica.com/arstechnica/technology-lab',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created Ars Technica AI source")

    if not db.get_source_by_name('ScienceDaily AI'):
        db.create_source(
            name='ScienceDaily AI',
            source_type='sciencedaily_ai',
            url='https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created ScienceDaily AI source")

    if not db.get_source_by_name('AI News'):
        db.create_source(
            name='AI News',
            source_type='ai_news',
            url='https://www.artificialintelligence-news.com/feed/',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created AI News source")

    if not db.get_source_by_name('The Guardian AI'):
        db.create_source(
            name='The Guardian AI',
            source_type='guardian_ai',
            url='https://www.theguardian.com/technology/artificialintelligenceai/rss',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created The Guardian AI source")

    if not db.get_source_by_name('InfoWorld AI'):
        db.create_source(
            name='InfoWorld AI',
            source_type='infoworld_ai',
            url='https://www.infoworld.com/artificial-intelligence/index.rss',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created InfoWorld AI source")

    # RESEARCH & TECHNICAL BLOGS (8)
    if not db.get_source_by_name('Google AI Blog'):
        db.create_source(
            name='Google AI Blog',
            source_type='google_ai',
            url='http://googleaiblog.blogspot.com/atom.xml',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created Google AI Blog source")

    if not db.get_source_by_name('MIT News AI'):
        db.create_source(
            name='MIT News AI',
            source_type='mit_news_ai',
            url='https://news.mit.edu/rss/topic/artificial-intelligence2',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created MIT News AI source")

    if not db.get_source_by_name('MIT Technology Review AI'):
        db.create_source(
            name='MIT Technology Review AI',
            source_type='mit_tech_review_ai',
            url='https://www.technologyreview.com/topic/artificial-intelligence/feed',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created MIT Technology Review AI source")

    if not db.get_source_by_name('Analytics Vidhya'):
        db.create_source(
            name='Analytics Vidhya',
            source_type='analytics_vidhya',
            url='https://www.analyticsvidhya.com/feed/',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created Analytics Vidhya source")

    if not db.get_source_by_name('KDnuggets'):
        db.create_source(
            name='KDnuggets',
            source_type='kdnuggets',
            url='https://feeds.feedburner.com/kdnuggets-data-mining-analytics',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created KDnuggets source")

    if not db.get_source_by_name('Machine Learning Mastery'):
        db.create_source(
            name='Machine Learning Mastery',
            source_type='ml_mastery',
            url='https://machinelearningmastery.com/feed/',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created Machine Learning Mastery source")

    if not db.get_source_by_name('Berkeley AI Research'):
        db.create_source(
            name='Berkeley AI Research',
            source_type='bair_blog',
            url='https://bair.berkeley.edu/blog/feed.xml',
            config={'max_results': 20},
            enabled=True
        )
        logger.info("Created Berkeley AI Research source")

    if not db.get_source_by_name('Microsoft AI Blog'):
        db.create_source(
            name='Microsoft AI Blog',
            source_type='microsoft_ai',
            url='https://blogs.microsoft.com/ai/feed/',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created Microsoft AI Blog source")

    # INDUSTRY & ANALYSIS (5)
    if not db.get_source_by_name('Unite.AI'):
        db.create_source(
            name='Unite.AI',
            source_type='unite_ai',
            url='https://www.unite.ai/feed/',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created Unite.AI source")

    if not db.get_source_by_name('AIMultiple'):
        db.create_source(
            name='AIMultiple',
            source_type='ai_multiple',
            url='https://research.aimultiple.com/feed/',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created AIMultiple source")

    if not db.get_source_by_name('Marketing AI Institute'):
        db.create_source(
            name='Marketing AI Institute',
            source_type='marketing_ai',
            url='https://www.marketingaiinstitute.com/blog/rss.xml',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created Marketing AI Institute source")

    if not db.get_source_by_name('AI Time Journal'):
        db.create_source(
            name='AI Time Journal',
            source_type='ai_time_journal',
            url='https://www.aitimejournal.com/feed',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created AI Time Journal source")

    if not db.get_source_by_name('DailyAI'):
        db.create_source(
            name='DailyAI',
            source_type='daily_ai',
            url='https://dailyai.com/feed/',
            config={'max_results': 40},
            enabled=True
        )
        logger.info("Created DailyAI source")

    # PREMIUM SOURCES (5)
    if not db.get_source_by_name('Towards Data Science'):
        db.create_source(
            name='Towards Data Science',
            source_type='towards_data_science',
            url='https://medium.com/feed/towards-data-science',
            config={'max_results': 50},
            enabled=True
        )
        logger.info("Created Towards Data Science source")

    if not db.get_source_by_name('DeepMind Blog'):
        db.create_source(
            name='DeepMind Blog',
            source_type='deepmind',
            url='https://deepmind.google/blog/rss.xml',
            config={'max_results': 20},
            enabled=True
        )
        logger.info("Created DeepMind Blog source")

    if not db.get_source_by_name('OpenAI Blog RSS'):
        db.create_source(
            name='OpenAI Blog RSS',
            source_type='openai',
            url='https://openai.com/blog/rss/',
            config={'max_results': 20},
            enabled=True
        )
        logger.info("Created OpenAI Blog RSS source")

    if not db.get_source_by_name('Anthropic'):
        db.create_source(
            name='Anthropic',
            source_type='anthropic',
            url='https://www.anthropic.com/news/rss.xml',
            config={'max_results': 20},
            enabled=True
        )
        logger.info("Created Anthropic source")

    if not db.get_source_by_name('AWS AI Blog'):
        db.create_source(
            name='AWS AI Blog',
            source_type='aws_ai',
            url='https://aws.amazon.com/blogs/ai/feed/',
            config={'max_results': 30},
            enabled=True
        )
        logger.info("Created AWS AI Blog source")

    logger.info("✅ All 31 sources initialized (6 legacy + 25 new RSS feeds)")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("🤖 Starting Research Agent...")

    # Initialize database and default sources
    initialize_default_sources()

    # Start scheduler
    start_scheduler()

    # Run Flask app
    logger.info(f"Research Agent running on port {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

