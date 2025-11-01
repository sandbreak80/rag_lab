# Microservices Architecture Plan for RAG Lab

## Executive Summary

**Goal**: Break the monolithic RAG container into multiple specialized services to:
1. ✅ **Observability**: Monitor each component with AppDynamics
2. ✅ **Scalability**: Scale bottlenecks independently
3. ✅ **Performance**: Identify which service is slow
4. ✅ **Isolation**: Failures don't cascade
5. ✅ **Demo-ready**: Perfect for showcasing container monitoring

---

## Current Architecture (Monolith)

```
┌─────────────────────────────────────────┐
│   markdown-rag-mcp (Single Container)  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Flask Web UI (port 5555)        │  │
│  │  - Serves HTML                   │  │
│  │  - Handles API requests          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  All RAG Components              │  │
│  │  - Parser                        │  │
│  │  - Indexer                       │  │
│  │  - Hybrid Search                 │  │
│  │  - Knowledge Graph               │  │
│  │  - Query Expansion               │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  ChromaDB (in-process)           │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  Ollama (separate)    │
        │  - Embeddings         │
        │  - LLM Generation     │
        └───────────────────────┘
```

**Problems:**
- ❌ Can't monitor individual components
- ❌ Can't scale bottlenecks (e.g., embedding is slow)
- ❌ Single point of failure
- ❌ Hard to identify performance issues
- ❌ Poor for AppDynamics demo

---

## Proposed Microservices Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Docker Network: rag-network                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────┐         ┌────────────────┐                      │
│  │  Web UI        │────────▶│  API Gateway   │                      │
│  │  (Frontend)    │         │  (Flask)       │                      │
│  │  Port: 5555    │         │  Port: 8000    │                      │
│  └────────────────┘         └────────┬───────┘                      │
│                                      │                               │
│                    ┌─────────────────┼────────────────┐             │
│                    │                 │                │             │
│                    ▼                 ▼                ▼             │
│         ┌─────────────────┐  ┌────────────┐  ┌────────────────┐   │
│         │  Ingest Service │  │  Search    │  │  Chat Service  │   │
│         │  (Upload/Parse) │  │  Service   │  │  (RAG)         │   │
│         │  Port: 8001     │  │  Port: 8002│  │  Port: 8003    │   │
│         └────────┬────────┘  └─────┬──────┘  └────────┬───────┘   │
│                  │                 │                    │           │
│                  ▼                 ▼                    ▼           │
│         ┌─────────────────┐  ┌────────────┐  ┌────────────────┐   │
│         │  Docling        │  │  Vector DB │  │  Embedding     │   │
│         │  Service        │  │  (ChromaDB)│  │  Service       │   │
│         │  Port: 8004     │  │  Port: 8005│  │  Port: 8006    │   │
│         └─────────────────┘  └─────┬──────┘  └────────┬───────┘   │
│                                    │                    │           │
│                                    ▼                    ▼           │
│                           ┌────────────────┐  ┌────────────────┐   │
│                           │  Knowledge     │  │  LLM Service   │   │
│                           │  Graph Service │  │  (Ollama)      │   │
│                           │  Port: 8007    │  │  Port: 11434   │   │
│                           └────────────────┘  └────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Service Breakdown

### 1. **Web UI Service** (Frontend)
**Purpose**: Serve static HTML/CSS/JS
**Tech**: Nginx or simple Flask static server
**Port**: 5555
**Metrics**:
- Page load times
- Static asset delivery
- Browser requests

**Why separate?**
- CDN-ready
- Can scale independently
- Clear separation of concerns

---

### 2. **API Gateway Service** (Orchestrator)
**Purpose**: Route requests to appropriate services
**Tech**: Flask with routing logic
**Port**: 8000
**Endpoints**:
- `GET /api/stats` → Vector DB Service
- `POST /api/upload` → Ingest Service
- `POST /api/search` → Search Service
- `POST /api/chat` → Chat Service

**Metrics**:
- Request routing latency
- Total requests per endpoint
- Error rates
- API response times

**Why separate?**
- Single entry point for monitoring
- Load balancing
- Rate limiting
- Authentication (future)

---

### 3. **Ingest Service** (Document Processing)
**Purpose**: Handle file uploads and parsing
**Tech**: Flask + Docling
**Port**: 8001
**Endpoints**:
- `POST /ingest/upload` - Accept file upload
- `POST /ingest/parse` - Parse document
- `GET /ingest/status/{job_id}` - Check status

**Process Flow**:
```
1. Receive upload (PDF/MD/TXT)
2. Validate file (size, type)
3. Call Docling Service (if PDF)
4. Extract markdown
5. Call Embedding Service
6. Store in Vector DB
7. Update Knowledge Graph
8. Return job_id
```

**Metrics**:
- Files processed per minute
- Average parsing time
- PDF vs MD vs TXT breakdown
- Error rate by file type
- Queue depth

**Why separate?**
- CPU-intensive (docling parsing)
- Can scale horizontally for bulk uploads
- Isolate failures (bad PDF doesn't crash everything)

---

### 4. **Docling Service** (PDF Parsing)
**Purpose**: Convert PDFs to clean markdown
**Tech**: Python + Docling library
**Port**: 8004
**Endpoints**:
- `POST /docling/parse` - Parse PDF to markdown
- `GET /docling/health` - Health check

**Metrics**:
- PDF parsing time
- Pages processed per second
- Memory usage (PDFs can be large)
- Success/failure rate

**Why separate?**
- Heavy compute workload
- Can use GPU if available
- Memory-intensive (50MB PDFs)
- Easy to swap for alternative parsers

---

### 5. **Embedding Service** (Vector Generation)
**Purpose**: Generate embeddings via Ollama
**Tech**: Python + Ollama client
**Port**: 8006
**Endpoints**:
- `POST /embed/text` - Generate embedding for text
- `POST /embed/batch` - Batch embeddings

**Process**:
```python
def embed(text: str) -> List[float]:
    # Call Ollama nomic-embed-text
    # Return 768-dim vector
    return embedding
```

**Metrics**:
- Embeddings generated per second
- Average embedding time
- Batch size
- Ollama latency
- Queue depth

**Why separate?**
- **This is the bottleneck** in most RAG systems
- Can add caching layer (Redis)
- Can scale to multiple Ollama instances
- Clear monitoring of embedding performance

---

### 6. **Vector DB Service** (ChromaDB)
**Purpose**: Store and search embeddings
**Tech**: ChromaDB server mode
**Port**: 8005
**Endpoints**:
- `POST /db/add` - Add embeddings
- `POST /db/search` - Vector similarity search
- `GET /db/stats` - Collection stats
- `DELETE /db/delete` - Remove documents

**Metrics**:
- Query latency (p50, p95, p99)
- Collection size
- Index build time
- Memory usage
- Concurrent queries

**Why separate?**
- Persistent data layer
- Can upgrade to production ChromaDB/Qdrant/Pinecone
- Database backups
- Separate scaling from compute

---

### 7. **Search Service** (Hybrid Search + Reranking)
**Purpose**: Orchestrate hybrid search pipeline
**Tech**: Python + BM25 + Graph
**Port**: 8002
**Endpoints**:
- `POST /search/query` - Execute search
- `POST /search/hybrid` - Hybrid vector + keyword
- `POST /search/rerank` - Rerank results

**Process Flow**:
```
1. Receive query
2. Query Expansion (LLM)
3. Vector search (Vector DB)
4. BM25 keyword search
5. Reciprocal Rank Fusion
6. Knowledge Graph enhancement
7. [Optional] LLM Reranking
8. Return ranked results
```

**Metrics**:
- Search latency (total)
- Vector search time
- BM25 search time
- Fusion time
- Graph lookup time
- Reranking time (if enabled)
- Results returned

**Why separate?**
- Complex orchestration
- Multiple dependencies (Vector DB, Graph, LLM)
- Can test different search strategies
- Clear performance breakdown

---

### 8. **Knowledge Graph Service** (Graph Queries)
**Purpose**: Manage document relationships
**Tech**: Python + NetworkX
**Port**: 8007
**Endpoints**:
- `POST /graph/add` - Add nodes/edges
- `GET /graph/related/{doc_id}` - Find related docs
- `GET /graph/path/{from}/{to}` - Find connection path
- `GET /graph/stats` - Graph statistics

**Metrics**:
- Graph size (nodes, edges)
- Query latency
- Path finding time
- Memory usage

**Why separate?**
- Graph operations can be slow
- Can upgrade to Neo4j/ArangoDB later
- Graph algorithms (PageRank, community detection)
- Independent scaling

---

### 9. **Chat Service** (RAG Orchestration)
**Purpose**: Generate answers with retrieved context
**Tech**: Python + Ollama client
**Port**: 8003
**Endpoints**:
- `POST /chat/ask` - Ask question (streaming)
- `POST /chat/context` - Generate context only

**Process Flow**:
```
1. Receive question
2. Call Search Service (get top-k chunks)
3. Build context
4. Call LLM Service (stream response)
5. Stream tokens to client
6. Return sources
```

**Metrics**:
- Questions per minute
- Context retrieval time
- LLM generation time (TTFT, TPS)
- Total response time
- Stream latency

**Why separate?**
- Streaming responses
- Can implement conversation memory
- Can add prompt templates
- Clear RAG pipeline monitoring

---

### 10. **LLM Service** (Ollama - Already Separate)
**Purpose**: Generate text and embeddings
**Tech**: Ollama
**Port**: 11434
**Endpoints**: (Ollama API)

**Metrics**:
- Token generation speed (tokens/sec)
- Time to first token (TTFT)
- Active requests
- Model load time
- GPU utilization

**Why already separate?**
- Heavy GPU workload
- Can run on different hardware
- Can use cloud LLM (OpenAI) as fallback

---

## Service Communication

### Message Flow Example: Upload PDF

```
User → Web UI → API Gateway → Ingest Service
                                    ↓
                            Docling Service (parse PDF)
                                    ↓
                            Embedding Service (generate vectors)
                                    ↓
                            Vector DB (store chunks)
                                    ↓
                            Knowledge Graph (add relationships)
                                    ↓
                            API Gateway → Web UI → User (✅ Indexed!)
```

### Message Flow Example: Ask Question

```
User → Web UI → API Gateway → Chat Service
                                    ↓
                            Search Service (find context)
                                    ↓ (parallel)
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            Vector DB      Knowledge Graph    BM25 Index
                    │               │               │
                    └───────────────┴───────────────┘
                                    ↓
                            LLM Service (generate answer)
                                    ↓
                            Chat Service (stream tokens)
                                    ↓
                            API Gateway → Web UI → User
```

---

## AppDynamics Monitoring Strategy

### Metrics to Track

#### 1. **Per-Service Metrics**
```yaml
web_ui:
  - page_load_time
  - static_asset_delivery_ms

api_gateway:
  - requests_per_minute
  - error_rate_percent
  - avg_latency_ms
  - endpoint_breakdown

ingest_service:
  - files_uploaded_per_minute
  - avg_parse_time_ms
  - pdf_parse_time_ms
  - md_parse_time_ms
  - queue_depth

docling_service:
  - pdf_pages_per_second
  - avg_pdf_parse_time_ms
  - memory_usage_mb
  - cpu_utilization_percent

embedding_service:
  - embeddings_per_second
  - avg_embedding_time_ms
  - batch_size
  - ollama_latency_ms
  - queue_depth

vector_db:
  - query_latency_p50_ms
  - query_latency_p95_ms
  - query_latency_p99_ms
  - collection_size
  - concurrent_queries

search_service:
  - total_search_time_ms
  - vector_search_time_ms
  - bm25_search_time_ms
  - fusion_time_ms
  - graph_time_ms
  - rerank_time_ms

knowledge_graph:
  - graph_nodes_count
  - graph_edges_count
  - query_latency_ms
  - memory_usage_mb

chat_service:
  - questions_per_minute
  - context_retrieval_time_ms
  - llm_generation_time_ms
  - total_response_time_ms
  - tokens_per_second

llm_service:
  - tokens_per_second
  - time_to_first_token_ms
  - active_requests
  - gpu_utilization_percent
```

#### 2. **Business Metrics**
```yaml
- documents_indexed_total
- documents_indexed_today
- searches_per_day
- questions_asked_today
- avg_user_satisfaction_score
- popular_queries
```

#### 3. **Service Health**
```yaml
per_service:
  - cpu_percent
  - memory_mb
  - disk_io_mbps
  - network_io_mbps
  - error_count
  - restart_count
  - uptime_seconds
```

---

## Docker Compose Configuration

### Network Architecture

```yaml
networks:
  rag-network:
    driver: bridge

volumes:
  chromadb-data:
  uploads:
  graph-data:
  indices:
```

### Services Configuration

#### Web UI
```yaml
web-ui:
  build: ./services/web-ui
  ports:
    - "5555:5555"
  networks:
    - rag-network
  environment:
    - API_GATEWAY_URL=http://api-gateway:8000
  depends_on:
    - api-gateway
```

#### API Gateway
```yaml
api-gateway:
  build: ./services/api-gateway
  ports:
    - "8000:8000"
  networks:
    - rag-network
  environment:
    - INGEST_SERVICE_URL=http://ingest-service:8001
    - SEARCH_SERVICE_URL=http://search-service:8002
    - CHAT_SERVICE_URL=http://chat-service:8003
  depends_on:
    - ingest-service
    - search-service
    - chat-service
```

#### Ingest Service
```yaml
ingest-service:
  build: ./services/ingest
  networks:
    - rag-network
  environment:
    - DOCLING_SERVICE_URL=http://docling-service:8004
    - EMBEDDING_SERVICE_URL=http://embedding-service:8006
    - VECTOR_DB_URL=http://vector-db:8005
    - GRAPH_SERVICE_URL=http://graph-service:8007
  volumes:
    - uploads:/uploads
  depends_on:
    - docling-service
    - embedding-service
    - vector-db
    - graph-service
```

#### Docling Service
```yaml
docling-service:
  build: ./services/docling
  networks:
    - rag-network
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

#### Embedding Service
```yaml
embedding-service:
  build: ./services/embedding
  networks:
    - rag-network
  environment:
    - OLLAMA_BASE_URL=http://llm-service:11434
    - EMBEDDING_MODEL=nomic-embed-text
  depends_on:
    - llm-service
```

#### Vector DB (ChromaDB)
```yaml
vector-db:
  image: chromadb/chroma:latest
  networks:
    - rag-network
  volumes:
    - chromadb-data:/chroma/chroma
  environment:
    - ALLOW_RESET=true
```

#### Search Service
```yaml
search-service:
  build: ./services/search
  networks:
    - rag-network
  environment:
    - VECTOR_DB_URL=http://vector-db:8005
    - GRAPH_SERVICE_URL=http://graph-service:8007
    - LLM_SERVICE_URL=http://llm-service:11434
  volumes:
    - indices:/indices
  depends_on:
    - vector-db
    - graph-service
```

#### Knowledge Graph Service
```yaml
graph-service:
  build: ./services/knowledge-graph
  networks:
    - rag-network
  volumes:
    - graph-data:/data
```

#### Chat Service
```yaml
chat-service:
  build: ./services/chat
  networks:
    - rag-network
  environment:
    - SEARCH_SERVICE_URL=http://search-service:8002
    - LLM_SERVICE_URL=http://llm-service:11434
  depends_on:
    - search-service
    - llm-service
```

#### LLM Service (Ollama)
```yaml
llm-service:
  image: ollama/ollama:latest
  networks:
    - rag-network
  ports:
    - "11434:11434"
  volumes:
    - ollama-models:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

---

## Implementation Strategy

### Phase 1: Prepare Service Skeleton (Day 1)
```bash
services/
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── ingest/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── docling/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── embedding/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── search/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── knowledge-graph/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── chat/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
└── web-ui/
    ├── Dockerfile
    └── nginx.conf
```

### Phase 2: Extract Code (Day 2)
- Move `src/indexer.py` logic → `ingest/app.py`
- Move `src/search.py` + `src/hybrid_search.py` → `search/app.py`
- Move `src/knowledge_graph.py` → `knowledge-graph/app.py`
- Move `src/webapp.py` chat logic → `chat/app.py`
- Create new API Gateway routing

### Phase 3: Docker Compose (Day 2)
- Create `docker-compose.microservices.yml`
- Define all services
- Set up networking
- Configure health checks

### Phase 4: Testing (Day 3)
- Test each service independently
- Test full pipeline (upload → index → search → chat)
- Performance testing
- Load testing

### Phase 5: Monitoring (Day 4)
- Add Prometheus metrics to each service
- Add AppDynamics instrumentation
- Create dashboards
- Set up alerts

---

## Benefits Summary

### 🎯 **Observability**
```
Before: Single container - can't see what's slow
After:  See exact bottleneck
        "Oh, embedding takes 80% of time!"
        "Docling parsing is the slowest!"
```

### 📊 **Scalability**
```
Before: Scale entire app (wasteful)
After:  Scale just embedding service
        docker-compose up --scale embedding-service=5
```

### 🔍 **Debugging**
```
Before: Logs mixed together
After:  Per-service logs
        docker logs embedding-service
```

### 🚀 **Performance**
```
Before: Everything blocks
After:  Parallel processing
        Upload → Parse → Embed (all parallel)
```

### 💰 **Cost Optimization**
```
Before: Over-provision everything
After:  Right-size each service
        - Docling: High CPU, high memory
        - API Gateway: Low CPU, low memory
        - Embedding: Medium CPU, high GPU
```

---

## Migration Path

### Option A: Big Bang (Risky)
- Build all services at once
- Switch in one go
- Fast but high risk

### Option B: Strangler Pattern (Recommended)
```
Week 1: Keep monolith, add Vector DB service
Week 2: Add Embedding service, route through it
Week 3: Add Search service
Week 4: Add Ingest service
Week 5: Add remaining services
Week 6: Deprecate monolith
```

### Option C: Side-by-Side
- Run both architectures
- A/B test performance
- Gradual traffic migration

---

## Estimated Effort

| Phase | Work | Time |
|-------|------|------|
| Planning & Design | This doc! | ✅ Done |
| Service Skeleton | Create directory structure | 2 hours |
| Code Extraction | Split monolith | 8 hours |
| Dockerization | Dockerfiles + compose | 4 hours |
| Testing | Integration tests | 8 hours |
| Monitoring Setup | Metrics + dashboards | 4 hours |
| Documentation | Update README | 2 hours |
| **Total** | | **28 hours (3-4 days)** |

---

## Next Steps

**Recommended Actions:**

1. ✅ **Review this plan** - Get feedback
2. 📁 **Create service directories** - Set up skeleton
3. 🐋 **Start with Vector DB** - Easiest to extract (ChromaDB has server mode)
4. 🧮 **Extract Embedding Service** - High impact (this is the bottleneck)
5. 🔍 **Extract Search Service** - Complex but valuable
6. 📄 **Add Ingest + Docling** - New functionality + service
7. 💬 **Extract Chat Service** - Final piece
8. 🎨 **Update Web UI** - Point to API Gateway
9. 📊 **Add monitoring** - AppDynamics integration
10. 🚀 **Deploy & demo** - Show off the architecture!

---

## Questions to Consider

1. **ChromaDB Server Mode**: Use official ChromaDB server or custom wrapper?
2. **Authentication**: Add auth between services? (Service mesh? JWT?)
3. **API Versioning**: `/v1/search`, `/v2/search`?
4. **Message Queue**: Add RabbitMQ/Redis for async processing?
5. **Caching**: Redis for embeddings/search results?
6. **Service Discovery**: Consul/Eureka or simple DNS?
7. **Load Balancing**: Nginx/Traefik in front of API Gateway?
8. **Deployment**: Kubernetes? Docker Swarm? Just Compose?

---

## Conclusion

This microservices architecture provides:
- ✅ Clear separation of concerns
- ✅ Independent scaling
- ✅ Excellent observability (AppDynamics ready!)
- ✅ Easy to understand and debug
- ✅ Production-ready path

**Perfect for showcasing container monitoring and RAG architecture!**

