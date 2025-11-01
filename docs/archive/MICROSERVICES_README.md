# Microservices Setup Guide

## Overview

This RAG Lab project has been refactored into a microservices architecture for:
- ✅ **Better Observability** - Monitor each component individually
- ✅ **Independent Scaling** - Scale bottlenecks (embedding, docling) separately
- ✅ **Fault Isolation** - Service failures don't cascade
- ✅ **AppDynamics Ready** - Perfect for container performance monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     rag-network                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Web UI (5555) → API Gateway (8000)                     │
│                          ↓                               │
│        ┌─────────────────┼────────────────┐            │
│        ▼                 ▼                ▼            │
│   Ingest (8001)    Search (8002)    Chat (8003)       │
│        ↓                 ↓                ↓            │
│   Docling (8004)   Vector DB (8005)  Embedding (8006) │
│                          ↓                              │
│                    Graph (8007)                         │
│                          ↓                              │
│                    Ollama (11434)                       │
└─────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Purpose | Key Endpoints |
|---------|------|---------|---------------|
| **API Gateway** | 8000 | Request routing | `/api/upload`, `/api/search`, `/api/chat` |
| **Ingest Service** | 8001 | File upload & processing | `/upload`, `/upload/url` |
| **Search Service** | 8002 | Hybrid search | `/search`, `/search/vector`, `/search/bm25` |
| **Chat Service** | 8003 | RAG orchestration | `/ask`, `/stream` |
| **Docling Service** | 8004 | PDF → Markdown | `/parse` |
| **Vector DB** | 8005 | ChromaDB wrapper | `/add`, `/search`, `/stats` |
| **Embedding Service** | 8006 | Text → Vectors | `/embed`, `/embed/batch` |
| **Graph Service** | 8007 | Knowledge graph | `/related/<id>` |
| **Ollama LLM** | 11434 | LLM generation | (Ollama API) |
| **Web UI** | 5555 | Frontend | http://localhost:5555 |

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Ollama (or use Docker Ollama service)
- At least 8GB RAM
- (Optional) NVIDIA GPU for faster LLM

### 2. Set Environment Variables

```bash
# Set your vault path (optional, for indexing existing documents)
export VAULT_PATH=/path/to/your/markdown/vault

# Or use docker-compose.override.yml (recommended)
cp docker-compose.override.yml.example docker-compose.override.yml
# Edit docker-compose.override.yml with your vault path
```

### 3. Start Services

```bash
# Build and start all services
docker-compose -f docker-compose.microservices.yml up --build

# Or start in detached mode
docker-compose -f docker-compose.microservices.yml up -d --build

# View logs
docker-compose -f docker-compose.microservices.yml logs -f

# View specific service logs
docker logs -f rag-api-gateway
docker logs -f rag-ingest-service
docker logs -f rag-embedding-service
```

### 4. Pull Ollama Models

```bash
# If using Docker Ollama
docker exec -it rag-llm-service ollama pull nomic-embed-text
docker exec -it rag-llm-service ollama pull llama3.2:3b

# Or if Ollama is running locally
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

### 5. Access the Application

- **Web UI**: http://localhost:5555
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000 (service info)

## Usage

### Upload a Document

**Via UI:**
1. Go to http://localhost:5555
2. Look for upload button (if implemented)
3. Select PDF, MD, or TXT file (max 50MB)
4. Wait for processing

**Via API:**
```bash
# Upload file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"

# Upload from URL
curl -X POST http://localhost:8000/api/upload/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.pdf"}'
```

### Search

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AppDynamics?", "limit": 5}'
```

### Ask a Question

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I configure monitoring?", "num_contexts": 5}'
```

## Monitoring & Observability

### Health Checks

Check health of all services:
```bash
# API Gateway
curl http://localhost:8000/health

# Individual services
curl http://localhost:8001/health  # Ingest
curl http://localhost:8002/health  # Search
curl http://localhost:8003/health  # Chat
curl http://localhost:8005/health  # Vector DB
curl http://localhost:8006/health  # Embedding
```

### Metrics

Get metrics from all services:
```bash
# Aggregated metrics
curl http://localhost:8000/metrics

# Individual service metrics
curl http://localhost:8006/metrics | jq .  # Embedding service
curl http://localhost:8005/metrics | jq .  # Vector DB
```

Example metrics output:
```json
{
  "service": "embedding-service",
  "counters": {
    "embed_requests": 145,
    "cache_hits": 98,
    "cache_misses": 47,
    "embeddings_generated": 47
  },
  "timers": {
    "embed_text": {
      "count": 145,
      "avg": 145.3,
      "p95": 234.5,
      "p99": 456.7
    }
  },
  "gauges": {
    "cache_size": 145
  }
}
```

### System Statistics

```bash
# Get overall system stats
curl http://localhost:8000/api/stats

# Get service status
curl http://localhost:8000/services
```

## Scaling

Scale individual services based on load:

```bash
# Scale embedding service (often the bottleneck)
docker-compose -f docker-compose.microservices.yml up -d --scale embedding-service=3

# Scale ingest service for high upload volume
docker-compose -f docker-compose.microservices.yml up -d --scale ingest-service=2

# Scale search service
docker-compose -f docker-compose.microservices.yml up -d --scale search-service=2
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.microservices.yml logs [service-name]

# Restart specific service
docker-compose -f docker-compose.microservices.yml restart [service-name]

# Rebuild service
docker-compose -f docker-compose.microservices.yml up -d --build [service-name]
```

### Cannot Connect to Service

```bash
# Check if service is running
docker-compose -f docker-compose.microservices.yml ps

# Check network
docker network inspect rag-network

# Check service health
curl http://localhost:8000/services
```

### Out of Memory

```bash
# Check container resource usage
docker stats

# Increase limits in docker-compose.microservices.yml
# Or reduce number of scaled instances
```

### Slow Performance

1. **Check metrics** to find bottleneck:
   ```bash
   curl http://localhost:8000/metrics | jq .
   ```

2. **Scale the slow service**:
   ```bash
   # If embedding is slow
   docker-compose -f docker-compose.microservices.yml up -d --scale embedding-service=3
   ```

3. **Check Ollama GPU usage**:
   ```bash
   docker exec -it rag-llm-service nvidia-smi
   ```

## Development

### Modify a Service

1. Edit code in `services/[service-name]/app/service.py`
2. Rebuild:
   ```bash
   docker-compose -f docker-compose.microservices.yml up -d --build [service-name]
   ```

### Add a New Service

1. Create directory: `services/new-service/`
2. Add `app/service.py`, `requirements.txt`, `Dockerfile`
3. Add to `docker-compose.microservices.yml`
4. Update API Gateway routing

### Run Tests

```bash
# Run all tests
docker-compose -f docker-compose.microservices.yml exec web-ui pytest

# Test specific service
docker-compose -f docker-compose.microservices.yml exec ingest-service pytest /app/tests
```

## Cleanup

```bash
# Stop all services
docker-compose -f docker-compose.microservices.yml down

# Stop and remove volumes (DELETES DATA!)
docker-compose -f docker-compose.microservices.yml down -v

# Remove images
docker-compose -f docker-compose.microservices.yml down --rmi all
```

## Migration from Monolith

If you're coming from the single-container setup:

1. **Export existing data:**
   ```bash
   # Copy ChromaDB data
   docker cp markdown-rag-mcp:/workspace/indices ./indices_backup
   ```

2. **Start microservices:**
   ```bash
   docker-compose -f docker-compose.microservices.yml up --build
   ```

3. **Import data:**
   ```bash
   # Copy to new volume
   docker cp ./indices_backup/chromadb rag-vector-db:/chroma/chroma
   ```

## AppDynamics Integration

### Per-Service Monitoring

Each service exposes:
- `/health` - Health check endpoint
- `/metrics` - Performance metrics endpoint

### Key Metrics to Monitor

1. **Embedding Service**
   - `embeddings_per_second`
   - `avg_embedding_time_ms`
   - `cache_hit_rate`

2. **Vector DB**
   - `query_latency_p95_ms`
   - `collection_size`

3. **Ingest Service**
   - `files_uploaded_per_minute`
   - `avg_parse_time_ms`

4. **Search Service**
   - `total_search_time_ms`
   - `vector_search_time_ms`
   - `bm25_search_time_ms`

5. **Chat Service**
   - `questions_per_minute`
   - `total_response_time_ms`
   - `context_retrieval_time_ms`

### Dashboard Setup

Create dashboards in AppDynamics tracking:
- Service health (green/red status)
- Request rates per service
- Latency (p50, p95, p99) per service
- Error rates
- Resource usage (CPU, memory)

## Architecture Decisions

### Why Microservices?

1. **Observability** - See exactly which component is slow
2. **Scalability** - Scale bottlenecks independently
3. **Development** - Teams can work on services independently
4. **Deployment** - Deploy updates to one service without affecting others
5. **Technology** - Use different tech stacks per service if needed

### Service Communication

- **Synchronous HTTP** - Simple, easy to debug
- **No message queue** (initially) - Reduce complexity
- **Docker networking** - Service discovery via DNS
- **Shared volumes** - For persistent data (ChromaDB, uploads)

### Data Flow

**Upload Pipeline:**
```
Client → API Gateway → Ingest Service
                         ↓
                    Docling Service (PDF → MD)
                         ↓
                    Embedding Service (MD → vectors)
                         ↓
                    Vector DB (store)
```

**Query Pipeline:**
```
Client → API Gateway → Chat Service
                         ↓
                    Search Service
                         ↓ (parallel)
            Vector DB + BM25 + Graph
                         ↓
                    Ollama (LLM)
                         ↓
                    Client (streaming)
```

## Next Steps

1. ✅ Upload AppDynamics documentation PDF
2. ✅ Test search and chat
3. ✅ Monitor performance in AppDynamics
4. ✅ Identify bottlenecks
5. ✅ Scale as needed

## Support

- 📖 Architecture doc: `MICROSERVICES_ARCHITECTURE.md`
- 📊 Status doc: `MICROSERVICES_STATUS.md`
- 🐛 Issues: Check service logs
- 💡 Questions: Review this README

---

**Built with ❤️ for observability and performance monitoring**

