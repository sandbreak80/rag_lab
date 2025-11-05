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
    ArxivScraper,
    HuggingFaceScraper,
    TechCrunchAIScraper,
    VentureBeatAIScraper,
    TheVergeAIScraper,
    OpenAIBlogScraper
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
    'arxiv': ArxivScraper,
    'huggingface': HuggingFaceScraper,
    'techcrunch': TechCrunchAIScraper,
    'venturebeat': VentureBeatAIScraper,
    'theverge': TheVergeAIScraper,
    'openai_blog': OpenAIBlogScraper,
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

