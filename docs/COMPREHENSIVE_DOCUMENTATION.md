# 🎓 Educational RAG Lab - Complete System Documentation

**Version:** 1.0.0
**Date:** November 1, 2025
**Status:** Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Services](#services)
4. [Educational Features](#educational-features)
5. [Configuration Presets](#configuration-presets)
6. [API Reference](#api-reference)
7. [Deployment Guide](#deployment-guide)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

The Educational RAG Lab is a comprehensive, interactive learning environment for understanding Retrieval Augmented Generation (RAG) systems. It provides hands-on experimentation with real-time performance metrics, configuration management, and comparative analysis.

### Key Features

- **Interactive Settings Panel**: 6 quick presets, 6 RAG pipeline toggles, 4 LLM configuration sliders
- **Real-time Metrics Dashboard**: Component-level latency breakdown, status indicators
- **A/B Comparison Mode**: Side-by-side configuration testing with automatic winner determination
- **Progressive Lab Guide**: 6 interactive sections with completion tracking
- **Web Search Integration**: SearXNG-powered external data retrieval
- **Production-Ready**: Optimized "Production" preset for real-world deployment

### Learning Objectives

Students will learn:
- RAG architecture and components
- Performance tradeoffs (quality vs speed vs cost)
- Configuration impact on results
- Hybrid search strategies
- Knowledge graph enhancement
- LLM re-ranking techniques
- External data integration
- Production deployment best practices

---

## Architecture

### Microservices Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB UI (Flask)                           │
│  Port 5555 - Single-page application with educational features  │
│  - Settings Panel (left sidebar)                                │
│  - Lab Guide (right sidebar)                                    │
│  - Metrics Dashboard (top)                                      │
│  - Comparison Modal (overlay)                                   │
│  - Chat Interface (center)                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼─────┐
        │  Search      │ │ Ingest │ │  Vector   │
        │  Service     │ │ Service│ │  DB       │
        │  Port 8002   │ │ 8001   │ │  Port 8005│
        └──────┬───────┘ └────────┘ └───────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼──┐  ┌───▼──────┐
│ BM25  │  │Graph│  │ Reranker │
│ Index │  │8007 │  │ Port 8008│
└───────┘  └─────┘  └──────────┘
               │
        ┌──────┴──────┐
        │             │
    ┌───▼───┐    ┌───▼────┐
    │Ollama │    │SearXNG │
    │11434  │    │8080+8009│
    └───────┘    └────────┘
```

### Data Flow

1. **User Query** → Web UI
2. **Configuration** → Search Service (`/search_with_config`)
3. **Parallel Retrieval**:
   - Vector Search (embeddings)
   - BM25 Search (keywords)
   - Web Search (optional, SearXNG)
4. **Fusion** → Reciprocal Rank Fusion
5. **Enhancement** → Knowledge Graph (optional)
6. **Re-ranking** → LLM Re-ranking (optional)
7. **Context** → Ollama LLM
8. **Response** → Streaming back to UI
9. **Metrics** → Real-time dashboard update

---

## Services

### 1. Web UI (Port 5555)

**Technology:** Flask + Vanilla JavaScript
**Purpose:** Educational interface with interactive learning features

**Endpoints:**
- `GET /` - Main application
- `GET /api/stats` - Vault statistics
- `POST /api/search` - Search documents
- `POST /api/chat` - Chat with RAG (streaming)
- `POST /api/upload` - Upload documents
- `GET /api/presets` - Get configuration presets
- `POST /api/evaluate` - Run evaluation

**Features:**
- Settings panel (collapsible, left)
- Lab guide (collapsible, right)
- Metrics dashboard (expandable)
- Comparison modal (overlay)
- File upload (drag-and-drop)
- Chat interface (markdown rendering)

### 2. Search Service (Port 8002)

**Technology:** Flask + Python
**Purpose:** Orchestrate hybrid search with configurable pipeline

**Endpoints:**
- `POST /search` - Standard search
- `POST /search_with_config` - Configurable search with metrics
- `POST /build_bm25_index` - Build/rebuild BM25 index
- `POST /search/vector` - Vector-only search
- `POST /search/bm25` - BM25-only search
- `GET /health` - Health check
- `GET /metrics` - Service metrics

**Configuration Options:**
- `use_query_expansion` - Enhance query with synonyms
- `use_bm25` - Enable BM25 keyword search
- `use_hybrid` - Combine vector + BM25
- `use_graph` - Add knowledge graph results
- `use_reranking` - LLM-based reranking
- `use_web_search` - Include web results
- `top_k` - Number of results to return

**Performance Metrics Returned:**
- Total latency (ms)
- Component breakdown (expansion, vector, BM25, fusion, graph, reranking)
- Percentage of total time per component
- Result counts per method
- Success/failure indicators

### 3. Vector DB (Port 8005)

**Technology:** ChromaDB + Flask
**Purpose:** Vector storage and similarity search

**Endpoints:**
- `POST /add` - Add documents with embeddings
- `POST /search` - Vector similarity search
- `GET /get_all` - Retrieve all documents
- `DELETE /delete` - Delete documents
- `GET /health` - Health check

**Storage:**
- Collection: `markdown_vault`
- Embedding Model: `nomic-embed-text`
- Persistence: `/chroma/chroma` volume

### 4. Embedding Service (Port 8006)

**Technology:** Ollama + Flask
**Purpose:** Generate embeddings for documents and queries

**Endpoints:**
- `POST /embed` - Generate single embedding
- `POST /embed_batch` - Batch embeddings
- `GET /health` - Health check

**Model:** `nomic-embed-text` (768 dimensions)

### 5. Ingest Service (Port 8001)

**Technology:** Flask + Docling + AgenticChunker
**Purpose:** Process and ingest documents

**Endpoints:**
- `POST /upload` - Upload and process file
- `POST /process` - Process text directly
- `GET /health` - Health check

**Supported Formats:**
- PDF, Word (doc/docx), Excel (xls/xlsx)
- PowerPoint (ppt/pptx), Text (txt/md/markdown)
- RTF, and more

**Processing Pipeline:**
1. File validation (size, type)
2. Docling parsing (PDF → Markdown)
3. Entity extraction (optional)
4. Agentic chunking (LLM-powered)
5. Embedding generation
6. Vector DB storage
7. BM25 index update

### 6. Knowledge Graph (Port 8007)

**Technology:** NetworkX + Flask
**Purpose:** Graph-based document relationships

**Endpoints:**
- `POST /build` - Build graph from documents
- `GET /related/{doc_id}` - Get related documents
- `POST /save` - Persist graph to disk
- `POST /load` - Load graph from disk
- `GET /health` - Health check

**Graph Structure:**
- Nodes: Documents, tags, folders
- Edges: Similarity, co-occurrence, hierarchy
- Weights: Relevance scores

### 7. Reranker Service (Port 8008)

**Technology:** Ollama LLM + Flask
**Purpose:** LLM-based result reranking

**Endpoints:**
- `POST /rerank` - Rerank search results
- `GET /health` - Health check

**Process:**
1. Receive query + results
2. Generate relevance scores via LLM
3. Re-order by relevance
4. Return reranked results

**Cost:** ~2000ms latency, high LLM usage

### 8. SearXNG (Port 8080)

**Technology:** SearXNG metasearch engine
**Purpose:** Privacy-preserving web search

**Configuration:**
- Engines: Google, DuckDuckGo, Wikipedia, StackOverflow
- Output: HTML + JSON
- Timeout: 10s

### 9. Web Search Service (Port 8009)

**Technology:** Flask + Requests
**Purpose:** Wrapper for SearXNG with metrics

**Endpoints:**
- `POST /search` - Web search with metrics
- `GET /health` - Health check

**Returns:**
- Results (title, url, content, engine)
- Web docs returned count
- Avg pages per document
- Latency (ms)
- Engines used

### 10. Ollama (Port 11434)

**Technology:** Ollama LLM server
**Purpose:** Local LLM inference

**Models Used:**
- `llama3.2:1b` - Fast (low latency)
- `llama3.2:3b` - Balanced (default)
- `llama3.2:8b` - Accurate (high quality)
- `nomic-embed-text` - Embeddings

---

## Educational Features

### 1. Settings Panel

**Location:** Left sidebar (collapsible)
**Toggle Button:** ⚙️ (bottom-left)

**Quick Presets (6):**
1. **Minimal** - Baseline, vector only (~40ms)
2. **Fast** - Query expansion + vector (~60ms)
3. **Balanced** ⭐ - Hybrid search (~120ms) - RECOMMENDED
4. **Quality** - All except reranking (~250ms)
5. **Maximum** - Everything ON (~2500ms)
6. **Production** 🏆 - Optimized for real-world (~300ms)

**RAG Pipeline Toggles (6):**
- Query Expansion (+5% recall, +10ms)
- BM25 Keyword Search (+15% recall, +20ms)
- Hybrid Fusion (+20% recall, +30ms)
- Knowledge Graph (+5% recall, +50ms)
- LLM Re-ranking (+10% precision, +2000ms)
- Web Search (SearXNG) (+5 docs, +500-1000ms)

**Search Parameters:**
- Top-K Results (1-20 slider)

**LLM Settings (4):**
- Model (1B/3B/8B dropdown)
- Temperature (0-1 slider)
- Max Tokens (100-2000 slider)
- Context Window (1000-8000 slider)

**Expected Performance Preview:**
- Precision estimate
- Recall estimate
- Latency estimate

**Persistence:** All settings saved to `localStorage`

### 2. Metrics Dashboard

**Location:** Below header (auto-appears after first query)

**Key Metrics (4 cards):**
- Total Latency (ms)
- Results Found (count)
- Search Method (hybrid/vector)
- Precision (estimated %)

**Detailed Breakdown (collapsible):**
- Query Expansion (time + %)
- Vector Search (time + %)
- BM25 Search (time + %)
- Fusion (time + %)
- Knowledge Graph (time + %)
- LLM Re-ranking (time + %)

**Component Status:**
- Active components (green dots)
- Inactive components (gray dots)

**Features:**
- Real-time updates
- Smooth animations
- Percentage breakdown visualization
- Color-coded status indicators

### 3. Comparison Mode

**Trigger:** "⚖️ Compare Configurations" button in metrics dashboard

**Modal Layout:**
- Side-by-side columns (Config A vs B)
- 9 metrics per configuration
- Winner badge (🏆) on faster config
- Key insights summary
- Action buttons (Use A, Use B, Close)

**Insights Generated:**
- Latency differences with % improvement
- Search method differences
- Result count differences
- Component enable/disable differences

**Automatic Tracking:**
- Current query = Config A
- Previous query = Config B
- Persists to `localStorage`

### 4. Lab Guide

**Location:** Right sidebar (collapsible)
**Toggle Button:** 📖 (bottom-right)

**Progress Tracker:**
- Progress bar (0-100%)
- X of 6 sections complete
- Persists to `localStorage`

**6 Interactive Sections:**

**Section 1: Getting Started**
- Intro to RAG and settings panel
- Task: Explore preset buttons
- Learning: Baseline configurations

**Section 2: Your First Query**
- Run a query, observe metrics
- Task: Ask "What is vector search?"
- Learning: Metrics dashboard basics

**Section 3: Understanding Metrics**
- Learn to read performance data
- Task: Expand detailed view
- Learning: Latency breakdown, bottlenecks

**Section 4: Configuration Experiments**
- Compare presets and toggles
- Task: Test Minimal vs Maximum
- Learning: Performance tradeoffs

**Section 5: Advanced Features**
- Knowledge Graph and Re-ranking
- Task: Enable advanced components
- Learning: Cost/benefit analysis

**Section 6: Production Configuration**
- Take-home system design
- Task: Load Production preset
- Learning: Real-world optimization

**Features per Section:**
- Expandable/collapsible content
- Checkbox completion tracking
- Tips and warnings
- Code examples
- Green highlighting when complete

**Resources Section:**
- GitHub repository link
- System architecture doc
- External RAG learning resources

**Quick Actions:**
- Reset Progress
- Load Production preset

---

## Configuration Presets

### Minimal (Baseline)

**Purpose:** Establish baseline performance

**Config:**
```json
{
  "use_query_expansion": false,
  "use_bm25": false,
  "use_hybrid": false,
  "use_graph": false,
  "use_reranking": false,
  "use_web_search": false,
  "top_k": 5
}
```

**LLM:**
- Model: llama3.2:3b
- Temperature: 0.5
- Max Tokens: 500
- Context: 2000

**Expected:**
- Precision: 60-70%
- Recall: 50-60%
- Latency: 30-50ms

**Use Case:** Baseline measurement, ultra-low latency needs

### Fast

**Purpose:** Optimized for speed with some quality improvement

**Config:**
```json
{
  "use_query_expansion": true,
  "use_bm25": false,
  "use_hybrid": false,
  "use_graph": false,
  "use_reranking": false,
  "use_web_search": false,
  "top_k": 5
}
```

**LLM:**
- Model: llama3.2:1b
- Temperature: 0.3
- Max Tokens: 300
- Context: 2000

**Expected:**
- Precision: 65-75%
- Recall: 55-65%
- Latency: 40-60ms

**Use Case:** Autocomplete, real-time search, high QPS

### Balanced ⭐ (Recommended)

**Purpose:** Best balance of quality and speed

**Config:**
```json
{
  "use_query_expansion": true,
  "use_bm25": true,
  "use_hybrid": true,
  "use_graph": false,
  "use_reranking": false,
  "use_web_search": false,
  "top_k": 10
}
```

**LLM:**
- Model: llama3.2:3b
- Temperature: 0.5
- Max Tokens: 500
- Context: 4000

**Expected:**
- Precision: 85-90%
- Recall: 80-85%
- Latency: 100-150ms

**Use Case:** General purpose, daily use, most applications

### Quality

**Purpose:** High quality without extreme latency

**Config:**
```json
{
  "use_query_expansion": true,
  "use_bm25": true,
  "use_hybrid": true,
  "use_graph": true,
  "use_reranking": false,
  "use_web_search": false,
  "top_k": 15
}
```

**LLM:**
- Model: llama3.2:3b
- Temperature: 0.3
- Max Tokens: 1000
- Context: 6000

**Expected:**
- Precision: 90-95%
- Recall: 85-92%
- Latency: 200-300ms

**Use Case:** Research, complex queries, comprehensive results

### Maximum (Slow)

**Purpose:** Best possible quality

**Config:**
```json
{
  "use_query_expansion": true,
  "use_bm25": true,
  "use_hybrid": true,
  "use_graph": true,
  "use_reranking": true,
  "use_web_search": false,
  "top_k": 20
}
```

**LLM:**
- Model: llama3.2:8b
- Temperature: 0.1
- Max Tokens: 1500
- Context: 8000

**Expected:**
- Precision: 95-98%
- Recall: 90-95%
- Latency: 2000-3000ms

**Use Case:** Critical queries, research papers, legal documents

### Production 🏆 (Take-Home)

**Purpose:** Optimized for real-world deployment

**Config:**
```json
{
  "use_query_expansion": true,
  "use_bm25": true,
  "use_hybrid": true,
  "use_graph": true,
  "use_reranking": false,
  "use_web_search": false,
  "top_k": 10
}
```

**LLM:**
- Model: llama3.2:3b
- Temperature: 0.3
- Max Tokens: 1000
- Context: 6000

**Expected:**
- Precision: 92-96%
- Recall: 88-93%
- Latency: 250-350ms

**Use Case:** Production deployments, API services, scalable RAG

**Why This Config:**
- Excellent quality (92-96% precision)
- Acceptable latency (<350ms)
- No expensive LLM re-ranking
- Scalable to high QPS
- Production-proven
- Students can deploy immediately

---

## API Reference

### Web UI Endpoints

#### GET /api/presets

Get all configuration presets.

**Response:**
```json
{
  "presets": {
    "minimal": {...},
    "fast": {...},
    "balanced": {...},
    "quality": {...},
    "maximum": {...},
    "production": {...}
  },
  "feature_impacts": {...}
}
```

#### POST /api/evaluate

Run evaluation on test dataset.

**Request:**
```json
{
  "config": {
    "use_query_expansion": true,
    "use_bm25": true,
    ...
  }
}
```

**Response:**
```json
{
  "metrics": {
    "precision": 0.85,
    "recall": 0.82,
    "mrr": 0.78,
    "ndcg": 0.81,
    "f1": 0.83
  },
  "per_difficulty": {...},
  "latency_ms": 1250
}
```

### Search Service Endpoints

#### POST /search_with_config

Configurable search with detailed metrics.

**Request:**
```json
{
  "query": "vector search explanation",
  "config": {
    "use_query_expansion": true,
    "use_bm25": true,
    "use_hybrid": true,
    "use_graph": false,
    "use_reranking": false,
    "use_web_search": false,
    "top_k": 10
  }
}
```

**Response:**
```json
{
  "results": [...],
  "count": 10,
  "query": {
    "original": "vector search explanation",
    "expanded": "vector search semantic similarity explanation"
  },
  "config_used": {...},
  "metrics": {
    "total_latency_ms": 125.4,
    "query_expansion_ms": 12.3,
    "vector_search_ms": 45.2,
    "bm25_search_ms": 23.1,
    "fusion_ms": 8.5,
    "graph_enhancement_ms": 0,
    "reranking_ms": 0,
    "breakdown_percent": {
      "query_expansion": 9.8,
      "vector_search": 36.0,
      "bm25_search": 18.4,
      "fusion": 6.8,
      "graph": 0,
      "reranking": 0
    },
    "method": "hybrid",
    "query_expanded": true,
    "vector_results_count": 10,
    "bm25_results_count": 10
  }
}
```

### Web Search Endpoint

#### POST /web-search/search

Search the web using SearXNG.

**Request:**
```json
{
  "query": "RAG retrieval augmented generation",
  "limit": 5,
  "categories": "general"
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "Retrieval-Augmented Generation - Wikipedia",
      "url": "https://...",
      "content": "...",
      "engine": "google",
      "score": 0.95,
      "estimated_pages": 2
    }
  ],
  "count": 5,
  "web_docs_returned": 5,
  "avg_pages_per_doc": 1.8,
  "latency_ms": 850,
  "engines_used": ["google", "brave"]
}
```

---

## Deployment Guide

### Prerequisites

- Docker and Docker Compose
- Ollama running locally (port 11434)
- 8GB+ RAM recommended
- 10GB+ disk space

### Quick Start

```bash
# Clone repository
git clone https://github.com/sandbreak80/rag_lab.git
cd rag_lab

# Start all services
docker-compose -f docker-compose.test.yml up -d

# Wait for services to initialize (~30 seconds)
sleep 30

# Check service health
./START_SERVICES.sh

# Access UI
open http://localhost:5555
```

### Service Ports

- 5555: Web UI
- 8001: Ingest Service
- 8002: Search Service
- 8005: Vector DB
- 8006: Embedding Service
- 8007: Knowledge Graph
- 8008: Reranker
- 8009: Web Search
- 8080: SearXNG
- 11434: Ollama

### Environment Variables

**docker-compose.test.yml** configures:
- `SERVICE_NAME` - Service identifier
- `SERVICE_PORT` - Port number
- `OLLAMA_BASE_URL` - Ollama endpoint
- `SEARXNG_URL` - SearXNG endpoint
- `PYTHONPATH` - Python module paths

### Data Persistence

**Volumes:**
- `chromadb-data` - Vector database
- `uploads` - Uploaded documents
- `indices` - BM25 index files

**Config:**
- `config/searxng/settings.yml` - SearXNG config

### Stopping Services

```bash
# Stop all
docker-compose -f docker-compose.test.yml down

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.test.yml down -v
```

---

## Troubleshooting

### Common Issues

**Issue:** Web UI not loading
**Solution:** Check if port 5555 is available, restart container

**Issue:** Search returns no results
**Solution:** Upload documents first, check Vector DB health

**Issue:** BM25 not working
**Solution:** Build BM25 index via `/build_bm25_index` endpoint

**Issue:** SearXNG timeout
**Solution:** Check internet connection, increase timeout in settings.yml

**Issue:** Ollama connection failed
**Solution:** Ensure Ollama running on host at port 11434

### Health Checks

```bash
# Check all services
curl http://localhost:5555/api/stats
curl http://localhost:8002/health
curl http://localhost:8005/health
curl http://localhost:8009/health

# Check Ollama
curl http://localhost:11434/api/tags
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.test.yml logs

# Specific service
docker logs rag-web-ui
docker logs rag-search-service
docker logs rag-searxng
```

### Reset Everything

```bash
# Nuclear option - fresh start
docker-compose -f docker-compose.test.yml down -v
docker system prune -af
docker-compose -f docker-compose.test.yml up -d
```

---

## Performance Optimization

### For Low Latency

- Use "Fast" preset
- Disable re-ranking
- Disable knowledge graph
- Reduce top-k to 5
- Use llama3.2:1b model

### For High Quality

- Use "Quality" or "Maximum" preset
- Enable all components
- Increase top-k to 15-20
- Use llama3.2:8b model

### For Production

- Use "Production" preset (best balance)
- Enable query expansion, BM25, hybrid, graph
- Disable re-ranking (too slow)
- Top-k: 10
- llama3.2:3b model

---

## Security Considerations

- SearXNG secret key should be changed in production
- No authentication on endpoints (add if deploying publicly)
- File upload validation (50MB limit, type checking)
- Rate limiting not implemented (add for production)

---

## Future Enhancements

- User authentication
- Multi-tenancy support
- Advanced evaluation metrics (faithfulness, hallucination detection)
- Cost tracking (tokens, API calls)
- Batch query testing
- Export/share configurations
- Mobile app version
- Cloud deployment templates (AWS, GCP, Azure)

---

## License

MIT License - See LICENSE file

---

## Support

- GitHub Issues: https://github.com/sandbreak80/rag_lab/issues
- Documentation: This file
- Lab Guide: Built into UI (📖 button)

---

**Built with ❤️ for education**

Last Updated: November 1, 2025

