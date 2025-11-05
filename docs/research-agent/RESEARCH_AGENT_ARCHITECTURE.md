# 🤖 Background Research Agent Architecture

**Feature:** Autonomous AI Research Agent
**Purpose:** Continuously discover, fetch, and ingest AI trends, news, papers, and articles
**Status:** 🏗️ Design Phase

---

## 🎯 Vision

An autonomous background agent that:
- **Discovers** the latest AI trends, papers, news, and articles
- **Fetches** content from multiple sources (arXiv, Hugging Face, tech blogs)
- **Processes** and ingests content into the RAG knowledge base
- **Runs continuously** in the background (scheduled tasks)
- **Provides visibility** via UI dashboard

**End Result:** Your RAG system stays up-to-date with the latest AI developments automatically!

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Research Agent                        │
│                    (Port 8015)                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Scheduler  │  │   Scrapers   │  │  Processors  │ │
│  │              │  │              │  │              │ │
│  │ - Cron Jobs  │  │ - arXiv      │  │ - PDF Parse  │ │
│  │ - Triggers   │  │ - HF Papers  │  │ - Markdown   │ │
│  │ - Status     │  │ - Blogs      │  │ - Chunking   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
    ┌───────────────┐             ┌─────────────────┐
    │ Ingest Service│             │  Vector DB      │
    │   (Port 8001) │──────────▶  │  (Port 8005)    │
    └───────────────┘             └─────────────────┘
            │
            ▼
    ┌───────────────┐
    │ Knowledge Graph│
    │   (Port 8007) │
    └───────────────┘
```

---

## 📦 Components

### 1. Research Agent Service (NEW)

**Port:** 8015
**Language:** Python + Flask
**Purpose:** Orchestrate research discovery and ingestion

**Key Modules:**
- `scheduler.py` - APScheduler for cron jobs
- `scrapers/` - Individual scrapers for each source
- `processors/` - Content processing and cleaning
- `ingester.py` - Integration with ingest service
- `service.py` - Flask API and status endpoints

---

## 🔍 Data Sources

### Priority 1: Academic Papers

#### 1. arXiv.org
- **API:** https://arxiv.org/api/
- **Categories:** cs.AI, cs.LG, cs.CL, cs.CV
- **Frequency:** Daily
- **Content:** Titles, abstracts, PDFs
- **Example Query:**
  ```
  http://export.arxiv.org/api/query?
    search_query=cat:cs.AI+OR+cat:cs.LG&
    sortBy=submittedDate&
    sortOrder=descending&
    max_results=20
  ```

#### 2. Hugging Face Papers
- **Source:** https://huggingface.co/papers
- **Method:** RSS feed or web scraping
- **Frequency:** Daily
- **Content:** Curated top papers

### Priority 2: AI News & Blogs

#### 3. Tech Blogs
- **OpenAI Blog:** https://openai.com/blog
- **Google AI Blog:** https://ai.googleblog.com/
- **DeepMind Blog:** https://deepmind.google/discover/blog/
- **Anthropic News:** https://www.anthropic.com/news
- **Meta AI:** https://ai.meta.com/blog/
- **Method:** RSS feeds or web scraping
- **Frequency:** Daily

#### 4. AI News Aggregators
- **Papers With Code:** https://paperswithcode.com/latest
- **AI Weekly:** Various newsletters (if accessible)

### Priority 3: GitHub Repositories

#### 5. Trending AI Repos
- **Source:** GitHub Trending (https://github.com/trending)
- **Filter:** Language: Python, Jupyter Notebook
- **Topics:** artificial-intelligence, machine-learning, nlp, computer-vision
- **Content:** README.md files

---

## 🗓️ Scheduling Strategy

### Default Schedule

| Task | Frequency | Time (UTC) | Priority |
|------|-----------|------------|----------|
| arXiv Papers | Daily | 02:00 | High |
| Hugging Face Papers | Daily | 03:00 | High |
| Tech Blogs | Daily | 04:00 | Medium |
| GitHub Trending | Weekly | Sunday 05:00 | Low |
| System Cleanup | Weekly | Monday 06:00 | Low |

### Configurable Options

Users can configure:
- ✅ Enable/disable specific sources
- ✅ Adjust frequency (hourly, daily, weekly)
- ✅ Set custom time windows
- ✅ Trigger manual runs
- ✅ Set max items per run

---

## 🔄 Workflow

### 1. Discovery Phase

```python
def discover_papers():
    """
    Query arXiv for new papers in AI categories
    Returns: List of paper metadata (title, abstract, PDF URL, date)
    """
    # 1. Query arXiv API
    # 2. Parse XML response
    # 3. Filter by date (only papers from last 24h)
    # 4. Deduplicate against existing knowledge base
    # 5. Return metadata list
```

### 2. Fetch Phase

```python
def fetch_content(paper_metadata):
    """
    Download and extract content
    Returns: Processed content ready for ingestion
    """
    # 1. Download PDF or HTML
    # 2. Extract text (using docling for PDFs)
    # 3. Clean and format (markdown)
    # 4. Add metadata (source, date, author, tags)
    # 5. Return structured content
```

### 3. Process Phase

```python
def process_content(content):
    """
    Process content for ingestion
    Returns: Chunked content with metadata
    """
    # 1. Split into semantic chunks
    # 2. Generate embeddings (via embedding service)
    # 3. Extract keywords and entities
    # 4. Create knowledge graph nodes
    # 5. Return processed chunks
```

### 4. Ingest Phase

```python
def ingest_content(processed_chunks):
    """
    Ingest into knowledge base
    Returns: Ingestion status
    """
    # 1. Call ingest service API
    # 2. Store in vector database
    # 3. Update knowledge graph
    # 4. Log to research agent database
    # 5. Return success/failure
```

---

## 📊 Data Storage

### Research Agent Database (SQLite)

```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'arxiv', 'blog', 'github', etc.
    url TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_fetched TIMESTAMP,
    total_items_fetched INTEGER DEFAULT 0,
    config JSON  -- Source-specific configuration
);

CREATE TABLE fetch_history (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items_discovered INTEGER,
    items_ingested INTEGER,
    status TEXT,  -- 'success', 'partial', 'failed'
    error_message TEXT,
    duration_seconds REAL
);

CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    external_id TEXT UNIQUE,  -- e.g., arXiv ID
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ingested_at TIMESTAMP,
    status TEXT,  -- 'discovered', 'fetched', 'ingested', 'failed'
    content_hash TEXT,  -- To detect duplicates
    metadata JSON
);
```

---

## 🌐 API Endpoints

### Control Endpoints

```python
GET  /health
# Returns: Service health and scheduler status

GET  /status
# Returns: Current status of all sources and last fetch times

GET  /sources
# Returns: List of configured sources

POST /sources
# Create new source
# Body: {name, type, url, config}

PUT  /sources/<id>
# Update source configuration

POST /trigger/<source_id>
# Manually trigger a fetch for specific source

POST /trigger/all
# Manually trigger fetch for all enabled sources

GET  /history
# Returns: Fetch history (last N runs)

GET  /items
# Returns: List of discovered/ingested items
# Query params: ?status=ingested&limit=50

POST /config
# Update scheduler configuration
# Body: {daily_time: "02:00", max_items: 20}
```

### Dashboard Endpoints

```python
GET  /dashboard/stats
# Returns:
# {
#   "total_items": 1234,
#   "items_last_24h": 15,
#   "sources_active": 5,
#   "last_run": "2025-11-05T02:00:00Z",
#   "next_run": "2025-11-06T02:00:00Z",
#   "status": "idle"
# }

GET  /dashboard/timeline
# Returns: Timeline of recent fetch activities (for visualization)
```

---

## 🎨 UI Components

### Research Agent Dashboard (NEW)

**Location:** `/research` route in frontend

**Sections:**

1. **Status Overview Card**
   - Current status (idle/fetching/processing)
   - Last run time
   - Next scheduled run
   - Total items discovered/ingested

2. **Source Cards**
   - Grid of source cards (arXiv, HF Papers, Blogs, etc.)
   - Each shows: enabled status, last fetch time, item count
   - Toggle to enable/disable
   - "Fetch Now" button

3. **Recent Activity Timeline**
   - Visual timeline of recent fetches
   - Success/failure indicators
   - Click to see details

4. **Configuration Panel**
   - Schedule settings
   - Max items per run
   - Content filters
   - Notification preferences

5. **Content Browser**
   - Browse discovered items
   - Filter by source, date, status
   - Preview content
   - Manual ingest button for items that failed

---

## 🔧 Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

✅ **Day 1-2:**
- Create `research-agent` service directory structure
- Set up Flask app with basic endpoints
- Add to `docker-compose.yml`
- Create SQLite database schema

✅ **Day 3-4:**
- Implement APScheduler integration
- Create base scraper class
- Add status tracking

✅ **Day 5:**
- Integration with ingest service
- Basic health check and status endpoints

### Phase 2: Scrapers (Week 2)

✅ **Day 1-2: arXiv Scraper**
- Query arXiv API
- Parse XML responses
- Download PDFs
- Extract text (integrate with docling)

✅ **Day 3: Hugging Face Papers**
- RSS feed parsing
- Web scraping fallback
- Content extraction

✅ **Day 4-5: Tech Blogs**
- RSS aggregator
- Multiple blog sources
- Content cleaning

### Phase 3: UI Dashboard (Week 3)

✅ **Day 1-3:**
- Create `ResearchAgentPage` component
- Status overview cards
- Source management UI

✅ **Day 4-5:**
- Activity timeline visualization
- Configuration panel
- Content browser

### Phase 4: Advanced Features (Week 4)

✅ **Optional Enhancements:**
- Email/Slack notifications on new content
- Content quality scoring
- Automatic summarization
- Tag/topic extraction
- Duplicate detection improvements
- Retry logic for failed fetches

---

## 🛡️ Security & Safety

### Rate Limiting
- Respect API rate limits (arXiv: 1 req/3sec)
- Implement exponential backoff
- Cache responses

### Content Validation
- Scan for malicious content
- Validate URLs before fetching
- Sanitize extracted text

### Resource Management
- Limit concurrent downloads
- Set timeouts (30s per fetch)
- Clean up temp files
- Monitor disk usage

---

## 📈 Monitoring & Metrics

### Key Metrics

- **Discovery Rate:** Items discovered per day
- **Ingestion Rate:** Items successfully ingested per day
- **Success Rate:** Percentage of successful fetches
- **Latency:** Time from discovery to ingestion
- **Storage:** Total content size in knowledge base
- **Coverage:** Number of active sources

### Logging

```python
# Example log output
2025-11-05 02:00:00 [INFO] Scheduler triggered: arxiv_daily
2025-11-05 02:00:01 [INFO] Querying arXiv API: cs.AI, last 24h
2025-11-05 02:00:03 [INFO] Discovered 15 new papers
2025-11-05 02:00:05 [INFO] Fetching paper: "Attention Is All You Need v2"
2025-11-05 02:00:12 [INFO] Downloaded PDF (2.3 MB)
2025-11-05 02:00:45 [INFO] Extracted text (1,234 tokens)
2025-11-05 02:00:48 [INFO] Ingested 15/15 papers successfully
2025-11-05 02:00:48 [INFO] Run completed: 48 seconds, 100% success
```

---

## 🚀 Quick Start (Once Implemented)

```bash
# 1. Start the research agent
docker compose up -d research-agent

# 2. Check status
curl http://localhost:8015/status

# 3. Trigger manual fetch
curl -X POST http://localhost:8015/trigger/all

# 4. View dashboard
open http://localhost:3000/research
```

---

## 💡 Future Enhancements

1. **Smart Filtering**
   - ML model to predict relevance
   - User feedback loop (upvote/downvote)
   - Personalized recommendations

2. **Multi-Language Support**
   - Translate non-English content
   - Language-specific sources

3. **Collaborative Filtering**
   - Share discoveries with other users
   - Community-curated collections

4. **Advanced Summarization**
   - LLM-powered summaries
   - Key insights extraction
   - Visual diagrams from papers

5. **Integration with Chat**
   - "What's new in AI?" command
   - Automatic topic updates
   - Citation tracking

---

## 📊 Success Metrics

### MVP Success Criteria

✅ **Functional:**
- Successfully fetch papers from arXiv daily
- Ingest 90%+ of discovered content
- UI dashboard shows real-time status

✅ **Performance:**
- Complete daily run in < 5 minutes
- < 1% failure rate
- No impact on main RAG system

✅ **User Experience:**
- Clear status visibility
- Manual trigger works
- Easy source configuration

### Long-Term Goals

- **Coverage:** 5+ active sources
- **Volume:** 50+ new items per week
- **Accuracy:** 95%+ relevant content
- **Uptime:** 99.9% scheduler reliability

---

**Next Steps:** Begin Phase 1 implementation! 🚀

