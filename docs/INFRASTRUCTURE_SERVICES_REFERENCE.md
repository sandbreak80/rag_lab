# RAG Lab - Complete Infrastructure & Services Reference

**Last Updated:** November 17, 2025
**Version:** 3.0
**Total Services:** 20+ microservices

---

## 📋 Table of Contents

1. [Service Overview](#service-overview)
2. [Core RAG Services](#core-rag-services)
3. [Document Processing Services](#document-processing-services)
4. [Advanced RAG Services](#advanced-rag-services)
5. [Intelligence Layer Services](#intelligence-layer-services)
6. [Web Search Services](#web-search-services)
7. [API & Frontend Services](#api--frontend-services)
8. [Security Services](#security-services)
9. [Observability Stack](#observability-stack)
10. [Data Flow Architecture](#data-flow-architecture)
11. [Service Dependencies](#service-dependencies)
12. [Port Reference](#port-reference)

---

## 🎯 Service Overview

The RAG Lab is built as a **microservices architecture** with 20+ specialized services, each handling a specific responsibility. This design enables:

- **Scalability**: Scale individual services based on load
- **Observability**: Monitor each service independently
- **Maintainability**: Update services without affecting others
- **Flexibility**: Swap implementations (e.g., different LLM providers)
- **Educational Value**: Understand how production RAG systems are architected

---

## 🔧 Core RAG Services

### 1. Vector Database Service (`vector-db`)
- **Port:** 8005
- **Container:** `rag-vector-db`
- **Technology:** ChromaDB (Python wrapper)
- **Purpose:** Stores document embeddings for semantic search
- **Key Endpoints:**
  - `POST /add` - Add documents with embeddings
  - `POST /search` - Vector similarity search
  - `GET /stats` - Collection statistics
  - `POST /reset` - Clear all data
- **Data Persistence:** `chromadb-data` volume
- **Dependencies:** None (foundation service)
- **Health Check:** `http://localhost:8005/health`

**What it does:**
- Maintains a vector collection (`markdown_vault`) of document chunks
- Performs cosine similarity search to find relevant documents
- Stores metadata (doc_id, chunk_id, file_name, published_at, etc.)
- Supports filtering by metadata

---

### 2. Embedding Service (`embedding-service`)
- **Port:** 8006
- **Container:** `rag-embedding-service`
- **Technology:** Ollama (nomic-embed-text model)
- **Purpose:** Converts text to vector embeddings
- **Key Endpoints:**
  - `POST /embed` - Generate embedding for text
  - `POST /embed/batch` - Batch embedding generation
  - `GET /health` - Service health
- **Dependencies:** Ollama service
- **Caching:** In-memory cache (10K embeddings)
- **Health Check:** `http://localhost:8006/health`

**What it does:**
- Takes text input and returns 768-dimensional vectors
- Uses `nomic-embed-text` model via Ollama
- Caches frequently used embeddings for performance
- Supports batch processing for efficiency

---

### 3. Search Service (`search-service`)
- **Port:** 8002
- **Container:** `rag-search-service`
- **Technology:** Hybrid search (Vector + BM25)
- **Purpose:** Orchestrates multi-strategy search
- **Key Endpoints:**
  - `POST /search` - Hybrid search (vector + BM25)
  - `POST /search/vector` - Vector-only search
  - `POST /search/bm25` - Keyword-only search
  - `POST /search_with_config` - Advanced search with all features
- **Dependencies:** Vector DB, Embedding Service, Knowledge Graph, Reranker
- **Data Persistence:** `bm25-indices` volume
- **Health Check:** `http://localhost:8002/health`

**What it does:**
- Performs vector similarity search (semantic)
- Performs BM25 keyword search (lexical)
- Combines results using Reciprocal Rank Fusion (RRF)
- Optionally enhances with knowledge graph relationships
- Optionally re-ranks results using LLM
- Supports query expansion for better recall

**Features:**
- **Hybrid Search:** Combines vector and BM25 for best of both worlds
- **Query Expansion:** Generates related queries for better coverage
- **Knowledge Graph Enhancement:** Finds related documents via graph
- **LLM Re-ranking:** Uses LLM to score relevance

---

### 4. Chat Service (`chat-service`)
- **Port:** 8003
- **Container:** `rag-chat-service`
- **Technology:** Flask + Ollama
- **Purpose:** Conversational RAG interface
- **Key Endpoints:**
  - `POST /ask` - Ask a question (RAG query)
  - `POST /stream` - Streaming response
  - `GET /context` - Get conversation context
- **Dependencies:** Search Service, Ollama
- **Health Check:** `http://localhost:8003/health`

**What it does:**
- Takes user queries and retrieves relevant context
- Sends context + query to LLM for synthesis
- Returns natural language answers with citations
- Supports streaming responses for real-time feedback

---

## 📄 Document Processing Services

### 5. Docling Service (`docling-service`)
- **Port:** 8004
- **Container:** `rag-docling-service`
- **Technology:** Docling (IBM) + PyPDF fallback
- **Purpose:** High-quality PDF to Markdown conversion
- **Key Endpoints:**
  - `POST /parse` - Parse PDF file
  - `POST /parse/url` - Parse PDF from URL
  - `GET /health` - Service health
- **Dependencies:** None
- **Features:**
  - Preserves document structure (tables, headers, lists)
  - OCR support for scanned PDFs
  - Fallback to PyPDF for compatibility
  - Handles large PDFs (up to 10MB by default)

**What it does:**
- Converts PDF files to structured Markdown
- Extracts text, tables, and metadata
- Preserves document hierarchy
- Returns clean, chunkable text

---

### 6. Ingest Service (`ingest-service`)
- **Port:** 8001
- **Container:** `rag-ingest-service`
- **Technology:** Flask + Agentic Chunking
- **Purpose:** Document ingestion pipeline
- **Key Endpoints:**
  - `POST /upload` - Upload and process document
  - `POST /upload/url` - Ingest from URL
  - `GET /status` - Ingestion status
- **Dependencies:** Docling, Embedding, Vector DB
- **Data Persistence:** `uploads` volume
- **Health Check:** `http://localhost:8001/health`

**What it does:**
1. Receives uploaded files (PDF, MD, TXT)
2. Parses documents (uses Docling for PDFs)
3. **Agentic Chunking:** Uses LLM to find semantic boundaries
4. Generates embeddings for each chunk
5. Stores in vector database
6. Updates BM25 index
7. Updates knowledge graph

**Agentic Chunking:**
- Uses LLM to identify semantic boundaries (not fixed-size chunks)
- Preserves complete ideas within chunks
- Better retrieval quality than fixed-size chunking
- Configurable target size (default: 450 tokens)

---

## 🧠 Advanced RAG Services

### 7. Knowledge Graph Service (`knowledge-graph`)
- **Port:** 8007
- **Container:** `rag-knowledge-graph`
- **Technology:** NetworkX (Python graph library)
- **Purpose:** Document relationship management
- **Key Endpoints:**
  - `GET /related/<doc_id>` - Find related documents
  - `GET /stats` - Graph statistics
  - `POST /reset` - Clear graph
- **Dependencies:** Vector DB
- **Data Persistence:** `knowledge-graph` volume
- **Health Check:** `http://localhost:8007/health`

**What it does:**
- Builds a graph of document relationships
- Links documents that share entities or topics
- Enhances search by finding related documents
- Supports graph-based traversal for discovery

**Algorithm:**
- Extracts entities and topics from documents
- Creates edges between related documents
- Uses hybrid scoring (entity overlap + semantic similarity)

---

### 8. Re-ranking Service (`reranker`)
- **Port:** 8008
- **Container:** `rag-reranker`
- **Technology:** LLM-based relevance scoring
- **Purpose:** Improve result ranking using LLM
- **Key Endpoints:**
  - `POST /rerank` - Re-rank search results
  - `GET /health` - Service health
- **Dependencies:** Ollama
- **Health Check:** `http://localhost:8008/health`

**What it does:**
- Takes initial search results
- Uses LLM to score relevance to query
- Combines hybrid search score (60%) + LLM score (40%)
- Returns re-ranked results

**Benefits:**
- Better precision than pure vector/keyword search
- Understands query intent
- Can handle complex queries

---

## 🌐 Web Search Services

### 9. SearXNG (`searxng`)
- **Port:** 8080
- **Container:** `rag-searxng`
- **Technology:** SearXNG (meta-search engine)
- **Purpose:** Web search aggregation
- **Key Endpoints:**
  - `GET /search?q=<query>` - Web search
- **Dependencies:** None
- **Health Check:** `http://localhost:8080/`

**What it does:**
- Aggregates results from multiple search engines
- Provides privacy-focused web search
- Returns structured JSON results
- No tracking or personalization

---

### 10. Web Search Service (`web-search`)
- **Port:** 8009
- **Container:** `rag-web-search`
- **Technology:** SearXNG wrapper
- **Purpose:** Web search integration for RAG
- **Key Endpoints:**
  - `POST /search` - Search web and format for RAG
  - `GET /health` - Service health
- **Dependencies:** SearXNG, Ollama (for query expansion)
- **Health Check:** `http://localhost:8009/health`

**What it does:**
- Wraps SearXNG for RAG integration
- Formats web results as RAG sources
- Supports query expansion for better coverage
- Deduplicates and ranks results
- Returns up to 20 results (configurable)

**Features:**
- Multi-query search (expands query for better coverage)
- Result deduplication
- Score boosting for multi-query matches
- Timeout handling (30s default)

---

## 🎨 API & Frontend Services

### 11. API Gateway (`api-gateway`)
- **Port:** 8000 (internal only, accessed via Nginx)
- **Container:** `rag-api-gateway`
- **Technology:** Flask
- **Purpose:** Legacy API gateway (being phased out)
- **Key Endpoints:**
  - `POST /api/chat` - Chat endpoint
  - `POST /api/search` - Search endpoint
  - `GET /api/services` - Service status
- **Dependencies:** Multiple backend services
- **Note:** Being replaced by `rag-api-v1`

---

### 12. RAG API v1 (`rag-api-v1`)
- **Port:** 8080 (internal only, accessed via Nginx on port 3000)
- **Container:** `rag-api-v1`
- **Technology:** FastAPI + OpenTelemetry
- **Purpose:** Modern RAG API with full observability
- **Key Endpoints:**
  - `POST /v1/rag/query` - Main RAG query endpoint
  - `GET /v1/rag/response/<request_id>` - Poll for cached responses
  - `GET /v1/prompts` - List system prompts
  - `PUT /v1/prompts/<id>` - Update system prompt
  - `GET /version` - Service version
- **Dependencies:** Vector DB, Embedding, Web Search, Ollama, Redis
- **Health Check:** `http://localhost:8080/ready`

**What it does:**
- Main entry point for RAG queries
- Orchestrates: Vector Search → Web Search → KG Search → Rerank → LLM Synthesis
- Implements weighted scoring (RAG: 1.0x, KG: 0.9x, Web: 0.65x)
- Stores responses in Redis for polling
- Full OpenTelemetry instrumentation
- Dynamic system prompt loading

**Features:**
- **Weighted Scoring:** Prioritizes RAG/Research sources over web
- **Response Caching:** Redis-based caching for page refresh resilience
- **Prompt Management:** Edit system prompts via API
- **Observability:** Full tracing and metrics

---

### 13. Frontend (`frontend`)
- **Port:** 3000 (host) → 80 (container)
- **Container:** `rag-frontend`
- **Technology:** React + TypeScript + Vite + Nginx
- **Purpose:** Modern web UI
- **Dependencies:** RAG API v1
- **Health Check:** `http://localhost:3000`

**What it does:**
- Provides interactive chat interface
- Settings panel for RAG configuration
- Real-time metrics dashboard
- Document upload interface
- Research agent UI
- Prompt editor UI
- Source visualization

**Features:**
- **Chat Interface:** Real-time streaming responses
- **Settings Panel:** Configure all RAG features
- **Metrics Dashboard:** Performance waterfall charts
- **Document Management:** Upload and manage documents
- **Research Agent:** Monitor and trigger research discovery
- **Prompt Editor:** View and edit system prompts
- **Source Display:** Expandable source list with type indicators

---

## 🔒 Security Services

### 14. Security Guardrails (`security-guardrails`)
- **Port:** 8013
- **Container:** `rag-security-guardrails`
- **Technology:** ML models (PII detection, toxicity)
- **Purpose:** Enterprise LLM security
- **Key Endpoints:**
  - `POST /analyze` - Analyze input/output for security issues
  - `GET /health` - Service health
- **Dependencies:** None
- **Health Check:** `http://localhost:8013/health`

**What it does:**
- Detects PII in queries and responses
- Identifies toxic or harmful content
- Enforces content policies
- Logs security events

---

### 15. Authentication Service (`auth-service`)
- **Port:** 8014
- **Container:** `rag-auth-service`
- **Technology:** JWT + SQLite
- **Purpose:** User authentication
- **Key Endpoints:**
  - `POST /login` - User login
  - `POST /verify` - Verify JWT token
  - `GET /users` - List users (admin)
- **Dependencies:** None
- **Data Persistence:** `auth-data` volume
- **Health Check:** `http://localhost:8014/health`

**What it does:**
- Manages user accounts
- Issues JWT tokens
- Validates authentication
- Supports role-based access

---

## 🤖 Intelligence Layer Services

### 16. Research Agent (`research-agent`)
- **Port:** 8015
- **Container:** `rag-research-agent`
- **Technology:** Autonomous AI discovery
- **Purpose:** Auto-discover and ingest AI research papers
- **Key Endpoints:**
  - `GET /status` - Agent status
  - `POST /trigger/all` - Trigger discovery for all sources
  - `POST /reset` - Clear research database
- **Dependencies:** Ingest Service, Docling Service
- **Data Persistence:** `research-agent-data` volume

**What it does:**
- Monitors RSS feeds for AI research papers
- Downloads and processes PDFs
- Ingests into vector database
- Tracks what's been processed
- Runs on schedule or manual trigger

**Sources:**
- ArXiv (AI/ML papers)
- Hacker News (AI discussions)
- Reddit r/MachineLearning
- Custom RSS feeds

---

### 17. Prompt Classifier (`prompt-classifier`)
- **Port:** 8017
- **Container:** `rag-prompt-classifier`
- **Technology:** LLM-based classification
- **Purpose:** Categorize user queries
- **Key Endpoints:**
  - `POST /classify` - Classify query intent
  - `GET /health` - Service health
- **Dependencies:** None
- **Health Check:** `http://localhost:8017/health`

**What it does:**
- Classifies queries by intent (factual, creative, analytical, etc.)
- Routes to appropriate models
- Optimizes prompt structure
- Enables intelligent routing

---

### 18. Prompt Enhancement (`prompt-enhancement`)
- **Port:** 8012
- **Container:** `rag-prompt-enhancement`
- **Technology:** Framework-based rewriting
- **Purpose:** Improve prompts using frameworks
- **Key Endpoints:**
  - `POST /enhance` - Enhance prompt
  - `GET /health` - Service health
- **Dependencies:** Ollama, Prompt Classifier
- **Health Check:** `http://localhost:8012/health`

**What it does:**
- Applies prompt engineering frameworks (Chain-of-Thought, etc.)
- Rewrites prompts for better results
- Adapts to query type
- Improves LLM output quality

---

### 19. Model Router (`model-router`)
- **Port:** 8018
- **Container:** `rag-model-router`
- **Technology:** Intelligent routing
- **Purpose:** Select best model for query
- **Key Endpoints:**
  - `POST /route` - Get recommended model
  - `GET /health` - Service health
- **Dependencies:** Ollama, Prompt Classifier
- **Health Check:** `http://localhost:8018/health`

**What it does:**
- Analyzes query complexity
- Selects appropriate model (small/fast vs large/quality)
- Optimizes for latency vs quality trade-off
- Routes to best model for task

---

### 20. Query Decomposer (`query-decomposer`)
- **Port:** 8019
- **Container:** `rag-query-decomposer`
- **Technology:** LLM-based decomposition
- **Purpose:** Break complex queries into sub-queries
- **Key Endpoints:**
  - `POST /decompose` - Decompose query
  - `GET /health` - Service health
- **Dependencies:** Ollama
- **Health Check:** `http://localhost:8019/health`

**What it does:**
- Identifies multi-part queries
- Breaks into simpler sub-queries
- Executes sub-queries in parallel
- Combines results

---

### 21. Self-RAG (`self-rag`)
- **Port:** 8020
- **Container:** `rag-self-rag`
- **Technology:** Self-reflection RAG
- **Purpose:** Quality-aware retrieval
- **Key Endpoints:**
  - `POST /query` - Self-RAG query
  - `GET /health` - Service health
- **Dependencies:** Ollama, Search Service
- **Health Check:** `http://localhost:8020/health`

**What it does:**
- Retrieves documents
- Self-assesses retrieval quality
- Retrieves more if needed
- Generates answer with confidence

---

## 🖥️ LLM Service

### 22. Ollama (`ollama`)
- **Port:** 11434
- **Container:** `rag-ollama`
- **Technology:** Ollama (local LLM server)
- **Purpose:** LLM inference engine
- **Key Endpoints:**
  - `POST /api/generate` - Generate text
  - `POST /api/embed` - Generate embeddings
  - `GET /api/tags` - List models
- **Dependencies:** None (foundation service)
- **Data Persistence:** `ollama-models` volume
- **GPU Support:** Yes (NVIDIA GPU required)
- **Health Check:** `ollama list`

**What it does:**
- Runs local LLM models (llama3.1:8b, llama3.2:3b, etc.)
- Provides OpenAI-compatible API
- Supports multiple models simultaneously
- GPU-accelerated inference

**Models:**
- `llama3.1:8b` - Default chat model (4.7GB)
- `llama3.2:3b` - Fast, small model (2GB)
- `nomic-embed-text` - Embedding model (274MB)
- Additional models available

---

## 📊 Observability Stack

### 23. OpenTelemetry Collector (`otel-collector`)
- **Ports:** 4317 (gRPC), 4318 (HTTP), 8889 (Prometheus)
- **Container:** `rag-otel-collector`
- **Technology:** OpenTelemetry
- **Purpose:** Collect traces and metrics
- **Dependencies:** None
- **Exports to:** Tempo (traces), Prometheus (metrics)

**What it does:**
- Receives OpenTelemetry data from services
- Processes and routes traces to Tempo
- Exports metrics to Prometheus
- Aggregates observability data

---

### 24. Prometheus (`prometheus`)
- **Port:** 9090
- **Container:** `rag-prometheus`
- **Technology:** Prometheus
- **Purpose:** Time-series metrics database
- **Data Persistence:** `prometheus-data` volume
- **Dependencies:** None

**What it does:**
- Scrapes metrics from all services
- Stores time-series data
- Provides query language (PromQL)
- Supports alerting rules

---

### 25. Grafana (`grafana`)
- **Port:** 3001
- **Container:** `rag-grafana`
- **Technology:** Grafana
- **Purpose:** Metrics and traces visualization
- **Data Persistence:** `grafana-data` volume
- **Dependencies:** Prometheus, Tempo

**What it does:**
- Visualizes Prometheus metrics
- Displays distributed traces from Tempo
- Provides dashboards for monitoring
- Supports alerting

---

### 26. Tempo (`tempo`)
- **Ports:** 3200 (HTTP), 4319 (OTLP gRPC)
- **Container:** `rag-tempo`
- **Technology:** Tempo
- **Purpose:** Distributed tracing backend
- **Data Persistence:** `tempo-data` volume
- **Dependencies:** None

**What it does:**
- Stores distributed traces
- Provides trace query API
- Integrates with Grafana
- Supports trace search

---

### 27. Loki (`loki`)
- **Port:** 3100
- **Container:** `rag-loki`
- **Technology:** Loki
- **Purpose:** Log aggregation
- **Data Persistence:** `loki-data` volume
- **Dependencies:** None

**What it does:**
- Aggregates logs from all services
- Provides log query API
- Integrates with Grafana
- Indexes logs for fast search

---

### 28. Promtail (`promtail`)
- **Container:** `rag-promtail`
- **Technology:** Promtail
- **Purpose:** Log shipper
- **Dependencies:** Loki

**What it does:**
- Collects logs from Docker containers
- Ships logs to Loki
- Parses and labels logs
- Handles log rotation

---

### 29. cAdvisor (`cadvisor`)
- **Port:** 9080
- **Container:** `rag-cadvisor`
- **Technology:** cAdvisor
- **Purpose:** Container metrics
- **Dependencies:** None

**What it does:**
- Collects container resource usage (CPU, memory, network)
- Exposes Prometheus metrics
- Tracks container performance

---

### 30. Node Exporter (`node-exporter`)
- **Port:** 9100
- **Container:** `rag-node-exporter`
- **Technology:** Prometheus Node Exporter
- **Purpose:** System metrics
- **Dependencies:** None

**What it does:**
- Collects host system metrics (CPU, memory, disk, network)
- Exposes Prometheus metrics
- Monitors hardware health

---

### 31. Health Exporter (`health-exporter`)
- **Port:** 9099
- **Container:** `rag-health-exporter`
- **Technology:** Custom Python service
- **Purpose:** Docker health status
- **Dependencies:** Docker socket

**What it does:**
- Monitors Docker container health
- Exposes health status as Prometheus metrics
- Tracks service availability

---

## 💾 Supporting Services

### 32. Redis (`redis`)
- **Port:** 6379 (internal only)
- **Container:** `rag-redis`
- **Technology:** Redis
- **Purpose:** Caching and rate limiting
- **Data Persistence:** `redis-data` volume
- **Dependencies:** None

**What it does:**
- Caches RAG responses (30-minute TTL)
- Stores rate limit counters
- Provides fast key-value storage
- Supports pub/sub for real-time features

---

### 33. Metrics Store (`metrics-store`)
- **Port:** 8011
- **Container:** `rag-metrics-store`
- **Technology:** SQLite
- **Purpose:** Historical metrics storage
- **Data Persistence:** `metrics-data` volume
- **Dependencies:** None

**What it does:**
- Stores historical performance metrics
- Provides metrics query API
- Tracks long-term trends
- Supports analytics

---

## 🔄 Data Flow Architecture

### Query Flow (RAG Query)

```
User Query
    ↓
Frontend (React)
    ↓
Nginx (Reverse Proxy)
    ↓
RAG API v1 (FastAPI)
    ↓
┌─────────────────────────────────────┐
│ 1. Vector Search (parallel)         │
│    → Embedding Service              │
│    → Vector DB                      │
│                                     │
│ 2. Web Search (parallel)            │
│    → Web Search Service             │
│    → SearXNG                        │
│                                     │
│ 3. Knowledge Graph (parallel)       │
│    → Knowledge Graph Service        │
│                                     │
│ 4. Combine & Weight                 │
│    → Weighted Scoring               │
│    → RAG: 1.0x, KG: 0.9x, Web: 0.65x│
│                                     │
│ 5. Re-rank (optional)               │
│    → Reranker Service               │
│    → LLM scoring                    │
│                                     │
│ 6. LLM Synthesis                    │
│    → Ollama                         │
│    → Generate answer                │
│                                     │
│ 7. Store in Redis                   │
│    → Cache response (30min TTL)     │
└─────────────────────────────────────┘
    ↓
Response to Frontend
    ↓
Display with Sources
```

### Document Ingestion Flow

```
Document Upload
    ↓
Frontend
    ↓
RAG API v1
    ↓
Ingest Service
    ↓
┌─────────────────────────────────────┐
│ 1. Parse Document                   │
│    → Docling Service (PDF)          │
│    → Text extraction                │
│                                     │
│ 2. Agentic Chunking                 │
│    → LLM finds semantic boundaries  │
│    → Preserves complete ideas       │
│                                     │
│ 3. Generate Embeddings              │
│    → Embedding Service              │
│    → Batch processing               │
│                                     │
│ 4. Store in Vector DB               │
│    → Vector DB Service              │
│    → Metadata storage               │
│                                     │
│ 5. Update BM25 Index                │
│    → Search Service                 │
│    → Keyword indexing               │
│                                     │
│ 6. Update Knowledge Graph           │
│    → Knowledge Graph Service        │
│    → Relationship extraction        │
└─────────────────────────────────────┘
    ↓
Document Ready for Search
```

---

## 🔗 Service Dependencies

### Foundation Services (No Dependencies)
- Ollama
- Vector DB
- SearXNG
- Redis
- Observability stack (Prometheus, Tempo, Loki)

### Layer 1 (Depend on Foundation)
- Embedding Service → Ollama
- Web Search Service → SearXNG
- Docling Service → None

### Layer 2 (Depend on Layer 1)
- Ingest Service → Docling, Embedding, Vector DB
- Search Service → Vector DB, Embedding, Knowledge Graph, Reranker
- Knowledge Graph → Vector DB

### Layer 3 (Depend on Layer 2)
- Chat Service → Search Service, Ollama
- RAG API v1 → Vector DB, Embedding, Web Search, Ollama, Redis

### Layer 4 (Depend on Layer 3)
- Frontend → RAG API v1

---

## 🔌 Port Reference

| Port | Service | External Access |
|------|---------|----------------|
| 3000 | Frontend | ✅ Yes |
| 3001 | Grafana | ✅ Yes |
| 8000 | API Gateway (legacy) | ❌ Internal only |
| 8001 | Ingest Service | ✅ Yes |
| 8002 | Search Service | ✅ Yes |
| 8003 | Chat Service | ✅ Yes |
| 8004 | Docling Service | ✅ Yes |
| 8005 | Vector DB | ✅ Yes |
| 8006 | Embedding Service | ✅ Yes |
| 8007 | Knowledge Graph | ✅ Yes |
| 8008 | Reranker | ✅ Yes |
| 8009 | Web Search | ✅ Yes |
| 8011 | Metrics Store | ✅ Yes |
| 8012 | Prompt Enhancement | ✅ Yes |
| 8013 | Security Guardrails | ✅ Yes |
| 8014 | Auth Service | ✅ Yes |
| 8015 | Research Agent | ✅ Yes |
| 8017 | Prompt Classifier | ✅ Yes |
| 8018 | Model Router | ✅ Yes |
| 8019 | Query Decomposer | ✅ Yes |
| 8020 | Self-RAG | ✅ Yes |
| 8080 | RAG API v1 | ❌ Internal only (via Nginx) |
| 8080 | SearXNG | ✅ Yes |
| 9090 | Prometheus | ✅ Yes |
| 9100 | Node Exporter | ✅ Yes |
| 9080 | cAdvisor | ✅ Yes |
| 9099 | Health Exporter | ✅ Yes |
| 9400 | DCGM Exporter (GPU) | ✅ Yes (if enabled) |
| 11434 | Ollama | ✅ Yes |
| 3100 | Loki | ✅ Yes |
| 3200 | Tempo | ✅ Yes |
| 4317 | OTel Collector (gRPC) | ✅ Yes |
| 4318 | OTel Collector (HTTP) | ✅ Yes |
| 8889 | OTel Collector (Prometheus) | ✅ Yes |

---

## 📦 Data Volumes

| Volume | Purpose | Size Estimate |
|--------|---------|---------------|
| `chromadb-data` | Vector embeddings | ~1GB per 10K documents |
| `bm25-indices` | Keyword search indices | ~100MB per 10K documents |
| `knowledge-graph` | Graph relationships | ~50MB per 10K documents |
| `uploads` | Uploaded documents | Varies |
| `ollama-models` | LLM models | ~20GB (all models) |
| `redis-data` | Cache and rate limits | ~100MB |
| `research-agent-data` | Research database | ~50MB |
| `auth-data` | User accounts | ~10MB |
| `prometheus-data` | Metrics history | ~1GB per month |
| `grafana-data` | Dashboards | ~100MB |
| `tempo-data` | Traces | ~500MB per month |
| `loki-data` | Logs | ~1GB per month |
| `security-models` | ML models | ~500MB |
| `metrics-data` | Historical metrics | ~100MB |

---

## 🎯 Service Health Checks

All services implement health check endpoints. Check service health:

```bash
# Check all services
docker compose ps

# Check specific service
curl http://localhost:8005/health  # Vector DB
curl http://localhost:8006/health  # Embedding
curl http://localhost:8002/health  # Search
curl http://localhost:8080/ready   # RAG API v1
```

---

## 📚 Next Steps

- [Architecture Deep Dive](ARCHITECTURE.md)
- [Deployment Guide](deployment/DEPLOYMENT_QUICKSTART.md)
- [Best Practices](BEST_PRACTICES.md)
- [Troubleshooting](TROUBLESHOOTING.md)

---

**Last Updated:** November 17, 2025
**Maintained by:** RAG Lab Team

