# Quick Start Guide - New Features

## 🚀 Getting Started

### Start Services
```bash
docker-compose -f docker-compose.test.yml up -d
```

Wait ~15 seconds for all services to start.

### Verify Health
```bash
# Check all services
for port in 8001 8002 8003 8004 8005 8006 8007 8008; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r .status)"
done
```

Expected output: All services show `healthy`

### Build Indices
```bash
# Build BM25 index (required for hybrid search)
curl -X POST http://localhost:8002/index/build

# Build knowledge graph (required for graph enhancement)
curl -X POST http://localhost:8007/build
```

---

## 🧪 Test New Features

### 1. Knowledge Graph
```bash
# View graph stats
curl http://localhost:8007/stats

# Find related documents
curl http://localhost:8007/related/example.md?limit=5
```

### 2. Re-ranking
```bash
# Re-rank search results (test data)
curl -X POST http://localhost:8008/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "vector search",
    "results": [
      {"content": "Vector embeddings...", "metadata": {"title": "Embeddings"}, "score": 0.9}
    ],
    "limit": 5
  }'
```

### 3. Entity Extraction
```bash
# Upload a document - entities will be extracted automatically
curl -X POST http://localhost:8001/upload \
  -F "file=@your_document.pdf"
```

---

## 🔍 Search with New Features

### Standard Search (Fast - 100ms)
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how does vector search work?",
    "limit": 10
  }'
```

### With Knowledge Graph (+50ms)
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how does vector search work?",
    "limit": 10,
    "use_graph": true
  }'
```

### With Re-ranking (+2000ms, best precision)
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how does vector search work?",
    "limit": 10,
    "use_reranking": true
  }'
```

### All Features Enabled
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how does vector search work?",
    "limit": 10,
    "expand_query": true,
    "use_graph": true,
    "use_reranking": true
  }'
```

---

## 📊 View Metrics

```bash
# Knowledge graph metrics
curl http://localhost:8007/metrics

# Re-ranker metrics
curl http://localhost:8008/metrics

# Ingest metrics (includes entity extraction)
curl http://localhost:8001/metrics
```

---

## 🌐 Web UI

Open http://localhost:5555 in your browser.

The UI automatically uses:
- ✅ Query expansion
- ✅ Hybrid search (vector + BM25)
- ⚠️ Graph and re-ranking are OFF by default (add them via search service API)

---

## 💡 Performance Tips

### Production Mode (Fast)
Use only hybrid search (default):
- Latency: ~100ms
- Precision: 90-95%

### High Precision Mode
Enable re-ranking for critical queries:
- Latency: ~2100ms
- Precision: 95-100%
- Use for: Research, compliance, critical decisions

### Comprehensive Mode
Enable both graph and re-ranking:
- Latency: ~2150ms
- Recall: 90-95%
- Precision: 95-100%
- Use for: Offline batch processing, reports

---

## 🐛 Troubleshooting

### Service Not Responding
```bash
# Check logs
docker-compose -f docker-compose.test.yml logs [service-name]

# Restart service
docker-compose -f docker-compose.test.yml restart [service-name]
```

### Knowledge Graph Not Loading
```bash
# Rebuild graph
curl -X POST http://localhost:8007/build
```

### Re-ranking Timeout
Re-ranking is slow by design (LLM scoring). Consider:
- Reducing result count
- Using faster model (llama3.2:1b)
- Disabling for real-time queries

---

## 📚 More Information

- **IMPLEMENTATION_COMPLETE.md** - Full feature documentation
- **TEST_RESULTS.md** - Validation results
- **SUMMARY.md** - Executive summary

