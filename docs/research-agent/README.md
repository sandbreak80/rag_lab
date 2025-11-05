# 🤖 Research Agent Documentation

Autonomous AI research content discovery and ingestion system.

---

## 📚 Documentation Index

### Core Architecture
- **[ARCHITECTURE.md](RESEARCH_AGENT_ARCHITECTURE.md)** - System design, components, and data flow
- **[DEDUPLICATION.md](RESEARCH_AGENT_DEDUPLICATION.md)** - Content deduplication strategy and implementation

### Best Practices
- **[METADATA_BEST_PRACTICES.md](RESEARCH_AGENT_METADATA_BEST_PRACTICES.md)** - Metadata schema and structure
- **[SCRAPING_STACK.md](RESEARCH_AGENT_SCRAPING_STACK.md)** - Web scraping tools and strategies

---

## 🎯 What is the Research Agent?

The Research Agent is an **autonomous background service** that:
- 🔍 **Discovers** new AI research papers, articles, and news
- 📥 **Fetches** full content with comprehensive metadata
- 🧹 **Processes** and cleans content
- 💾 **Ingests** into the RAG system's vector database
- 🔄 **Runs automatically** on a schedule (daily/weekly)

**Result:** Your knowledge base stays up-to-date with the latest AI research!

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Research Agent Service                 │
│                  (Port 8015)                        │
└────────────────────┬────────────────────────────────┘
                     ↓
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼────┐
    │  arXiv   │          │ Hugging  │
    │ Scraper  │          │   Face   │
    └────┬─────┘          └─────┬────┘
         │                      │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │  Discovery Phase     │
         │  - Find new papers   │
         │  - Extract metadata  │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │  Fetch Phase         │
         │  - Get full content  │
         │  - Format as markdown│
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │  Deduplication       │
         │  - Check if seen     │
         │  - Skip duplicates   │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │  Ingest Phase        │
         │  - Send to ingest    │
         │  - Store in vector DB│
         └──────────────────────┘
```

---

## 📦 Components

### Service
- **Location:** `/services/research-agent/`
- **Port:** 8015
- **Technology:** Python, Flask, APScheduler
- **Database:** SQLite (for tracking sources and items)

### Scrapers
- **arXiv Scraper:** AI/ML papers from arXiv.org
- **Hugging Face Scraper:** Papers from Hugging Face Papers
- **Extensible:** Easy to add new sources (tech blogs, news sites)

### Database Schema
- **sources:** Configured data sources (arXiv, HF, etc.)
- **research_items:** Discovered items with metadata
- **fetch_history:** Historical fetch records and statistics

---

## 🚀 API Endpoints

### Health & Status
```bash
GET /health
# Returns service health and scheduler status

GET /status
# Returns detailed status with source info and statistics
```

### Manual Triggers
```bash
POST /trigger/<source_id>
# Manually trigger fetch for specific source

POST /trigger/all
# Trigger fetch for all enabled sources
```

### Source Management
```bash
GET /sources
# List all configured sources

PUT /sources/<source_id>
# Update source configuration (enable/disable, etc.)
```

### Items & History
```bash
GET /items?limit=20&status=ingested
# List discovered items with filters

GET /history?source_id=1&limit=10
# Get fetch history for a source
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Service
SERVICE_PORT=8015
SERVICE_NAME=research-agent

# Dependencies
INGEST_SERVICE_URL=http://ingest-service:8001
DOCLING_SERVICE_URL=http://docling-service:8004

# Database
DB_PATH=/data/research_agent.db

# PDF Processing (Optional)
USE_DOCLING_FOR_PDFS=false  # Set to 'true' for full PDF extraction
MAX_PDF_SIZE_MB=10          # Skip PDFs larger than this
```

### Schedule Configuration
Default: Daily at 02:00 UTC (after arXiv daily update)

Can be customized in `service.py`:
```python
scheduler.add_job(
    scheduled_fetch_all,
    trigger='cron',
    hour=2,  # Change this
    minute=0,
    id='daily_fetch'
)
```

---

## 📊 Current Status

### ✅ Completed
- Service architecture and implementation
- arXiv scraper with comprehensive metadata
- Hugging Face scraper
- Database models and API
- Scheduling system
- Docker integration
- `/ingest` endpoint for programmatic ingestion

### ⚠️ In Progress
- **BLOCKER:** Ingestion issue (0/20 papers ingested)
- End-to-end testing

### 📋 Planned
- Content deduplication (see DEDUPLICATION.md)
- Additional sources (tech blogs, news)
- UI dashboard
- Advanced metadata extraction
- Quality scoring

---

## 🔍 Debugging

### Check Service Logs
```bash
docker logs rag-research-agent --tail 50
```

### Check Database
```bash
docker exec rag-research-agent ls -lh /data/
```

### Manual Test
```bash
# Trigger manual fetch
curl -X POST http://localhost:8015/trigger/1

# Check status
curl http://localhost:8015/status | jq .

# View discovered items
curl http://localhost:8015/items?limit=5 | jq .
```

---

## 📈 Future Enhancements

See individual documentation files for detailed plans:
- **Deduplication:** Prevent re-ingesting same content
- **Adaptive Scheduling:** Adjust frequency based on source activity
- **Quality Filtering:** Score and filter low-quality sources
- **Cross-Source Matching:** Detect same content across different sites
- **UI Dashboard:** Visualize discoveries and manage sources

---

## 🤝 Contributing

To add a new scraper:

1. Create scraper class in `services/research-agent/app/scrapers/`
2. Inherit from `BaseScraper`
3. Implement `discover()` and `fetch_content()` methods
4. Register in `service.py`
5. Add source to database
6. Test!

Example:
```python
from scrapers.base import BaseScraper

class MyNewScraper(BaseScraper):
    def discover(self, since, max_items):
        # Return list of discovered items
        pass

    def fetch_content(self, item):
        # Return markdown content
        pass
```

---

**Status:** 🟡 In Development
**Last Updated:** November 5, 2025

