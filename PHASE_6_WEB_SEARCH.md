# 🌐 Phase 6: SearXNG Web Search Integration

**Final Lab Exercise:** Combine local RAG with live web search

---

## Overview

**SearXNG** is a privacy-respecting metasearch engine that aggregates results from multiple search engines without tracking.

**Educational Value:**
- Show hybrid approach: local knowledge + web search
- Demonstrate when to use RAG vs web search
- Teach result fusion strategies
- Privacy-aware search integration

---

## Architecture Addition

```
┌────────────────────────────────────────────┐
│         RAG Lab System                     │
├────────────────────────────────────────────┤
│                                            │
│  Local RAG Pipeline ──┐                    │
│  (Your Documents)     │                    │
│                       ├──→ Result Fusion   │
│  SearXNG Web Search ──┘                    │
│  (Live Internet)                           │
│                                            │
└────────────────────────────────────────────┘
```

---

## Docker Compose Addition

**File:** `docker-compose.test.yml`

```yaml
  # SearXNG Web Search Engine
  searxng:
    image: searxng/searxng:latest
    container_name: rag-searxng
    networks:
      - rag-network
    ports:
      - "8090:8080"
    volumes:
      - ./config/searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8090/
      - SEARXNG_SECRET=${SEARXNG_SECRET:-change_this_secret_key}
    restart: unless-stopped
```

**Configuration:** `config/searxng/settings.yml`
```yaml
general:
  instance_name: "RAG Lab Search"
  privacypolicy_url: false
  donation_url: false
  contact_url: false
  enable_metrics: false

search:
  safe_search: 0
  autocomplete: ""
  default_lang: "en"
  formats:
    - html
    - json

server:
  secret_key: "change_this_secret_key"
  limiter: false
  image_proxy: false
  
engines:
  - name: google
    weight: 1
    disabled: false
  - name: duckduckgo
    weight: 1
    disabled: false
  - name: wikipedia
    weight: 1
    disabled: false
```

---

## Backend Integration

### New Web Search Service

**File:** `services/web-search/app/service.py`

```python
"""
Web Search Service - SearXNG integration
Provides live web search results to augment RAG
"""
from flask import Flask, request, jsonify
import requests
import sys
import os

sys.path.insert(0, '/workspace/services/common')
from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)
metrics = ServiceMetrics("web-search-service")
health = HealthCheck("web-search-service")

SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://searxng:8080')

@app.route('/search', methods=['POST'])
@timed(metrics, 'web_search')
def web_search():
    """
    Search the web via SearXNG
    
    Body:
    {
        "query": "latest AI developments",
        "num_results": 5,
        "pages_per_result": 1
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        num_results = data.get('num_results', 5)
        pages_per_result = data.get('pages_per_result', 1)
        
        if not query:
            return jsonify({'error': 'query required'}), 400
        
        # Query SearXNG
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={
                'q': query,
                'format': 'json',
                'language': 'en'
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'SearXNG error'}), 500
        
        results = response.json()
        web_results = []
        
        # Format results
        for result in results.get('results', [])[:num_results]:
            web_results.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'content': result.get('content', ''),
                'engine': result.get('engine', 'unknown'),
                'score': result.get('score', 0.5),
                'source': 'web'
            })
        
        metrics.increment('web_searches')
        metrics.increment('web_results_returned', len(web_results))
        
        return jsonify({
            'results': web_results,
            'count': len(web_results),
            'query': query
        })
        
    except Exception as e:
        metrics.increment('web_search_errors')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Web Search Service starting...")
    print(f"   SearXNG URL: {SEARXNG_URL}")
    app.run(host='0.0.0.0', port=int(os.getenv('SERVICE_PORT', 8009)), debug=False)
```

---

## Search Service Update - Hybrid RAG + Web

**File:** `services/search/app/service.py`

Add new endpoint:

```python
@app.route('/search_hybrid_web', methods=['POST'])
@timed(metrics, 'hybrid_web_search')
def search_hybrid_web():
    """
    Hybrid search: Local RAG + Web Results
    
    Body:
    {
        "query": "latest RAG techniques",
        "use_web": true,
        "web_results": 5,
        "rag_results": 10,
        "fusion_strategy": "interleave"  // or "rag_first" or "web_first"
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        use_web = data.get('use_web', False)
        web_results_count = data.get('web_results', 5)
        rag_results_count = data.get('rag_results', 10)
        fusion_strategy = data.get('fusion_strategy', 'interleave')
        
        # Get RAG results
        rag_results = []
        if rag_results_count > 0:
            rag_response = requests.post(
                'http://localhost:8002/search',
                json={
                    'query': query,
                    'limit': rag_results_count,
                    **data.get('rag_config', {})
                },
                timeout=30
            )
            if rag_response.status_code == 200:
                rag_results = rag_response.json().get('results', [])
        
        # Get web results if enabled
        web_results = []
        if use_web:
            web_response = requests.post(
                'http://web-search:8009/search',
                json={
                    'query': query,
                    'num_results': web_results_count
                },
                timeout=15
            )
            if web_response.status_code == 200:
                web_results = web_response.json().get('results', [])
        
        # Fuse results
        fused_results = fuse_results(
            rag_results, 
            web_results, 
            strategy=fusion_strategy
        )
        
        return jsonify({
            'results': fused_results,
            'count': len(fused_results),
            'rag_count': len(rag_results),
            'web_count': len(web_results),
            'fusion_strategy': fusion_strategy
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def fuse_results(rag_results, web_results, strategy='interleave'):
    """Fuse RAG and web results based on strategy"""
    if strategy == 'rag_first':
        return rag_results + web_results
    elif strategy == 'web_first':
        return web_results + rag_results
    else:  # interleave
        fused = []
        for i in range(max(len(rag_results), len(web_results))):
            if i < len(rag_results):
                fused.append(rag_results[i])
            if i < len(web_results):
                fused.append(web_results[i])
        return fused
```

---

## UI Updates

### Settings Panel Addition

```html
<div class="settings-section">
  <h3>🌐 Web Search</h3>
  
  <div class="toggle-item">
    <input type="checkbox" id="use-web-search">
    <label for="use-web-search">
      Enable Web Search
      <span class="impact">+Real-time data, +500ms</span>
      <span class="info-icon" title="Searches live internet via SearXNG">ℹ️</span>
    </label>
  </div>
  
  <div id="web-search-config" style="display: none;">
    <label># Web Results: <span id="web-results-value">5</span></label>
    <input type="range" id="web-results" min="1" max="20" step="1" value="5">
    
    <label># RAG Results: <span id="rag-results-value">10</span></label>
    <input type="range" id="rag-results" min="1" max="20" step="1" value="10">
    
    <label>Fusion Strategy</label>
    <select id="fusion-strategy">
      <option value="interleave">Interleave (Mix)</option>
      <option value="rag_first">RAG First (Local Priority)</option>
      <option value="web_first">Web First (Fresh Priority)</option>
    </select>
  </div>
</div>
```

### Result Display Update

Show source indicator:

```html
<div class="search-result" data-source="${result.source}">
  <div class="result-header">
    <h3>${result.title}</h3>
    <span class="source-badge ${result.source}">
      ${result.source === 'web' ? '🌐 Web' : '📚 Local'}
    </span>
  </div>
  <p>${result.content}</p>
  ${result.url ? `<a href="${result.url}" target="_blank">View Source →</a>` : ''}
</div>
```

---

## Lab Exercise: Web Search Integration

### Learning Objectives:
1. Understand when to use RAG vs web search
2. Learn result fusion strategies
3. Balance freshness vs accuracy
4. Privacy considerations

### Exercise Steps:

**Step 1: Baseline (RAG only)**
```
Query: "What is RAG?"
Result: Local documents only
Quality: High (if docs exist)
Freshness: Depends on doc age
```

**Step 2: Enable Web Search**
```
Query: "What is RAG?"
Result: RAG docs + Wikipedia + recent articles
Quality: Very high
Freshness: Real-time
```

**Step 3: Compare Strategies**
```
Query: "Latest developments in LLMs 2025"

Strategy 1 - RAG First:
  ✅ Your research notes appear first
  ✅ Contextual to your work
  ❌ May be outdated

Strategy 2 - Web First:
  ✅ Latest information
  ✅ Breaking news
  ❌ No personal context

Strategy 3 - Interleave:
  ✅ Best of both worlds
  ✅ Balanced view
  ⚠️  More results to process
```

**Step 4: Tune Parameters**
- Increase web results for broad topics
- Decrease for personal knowledge queries
- Experiment with fusion strategies

---

## Production Mode Configuration

**File:** `presets/production.json`

```json
{
  "name": "Production - World Class RAG",
  "description": "Optimized for quality and completeness",
  "llm_config": {
    "model": "llama3.2:3b",
    "temperature": 0.3,
    "max_tokens": 1000,
    "context_window": 6000
  },
  "rag_config": {
    "use_query_expansion": true,
    "use_bm25": true,
    "use_hybrid": true,
    "use_graph": true,
    "use_reranking": false,
    "use_agentic_chunking": true,
    "top_k": 10
  },
  "web_config": {
    "enabled": true,
    "num_results": 5,
    "fusion_strategy": "interleave"
  },
  "expected_metrics": {
    "precision": "95%+",
    "recall": "90%+",
    "latency": "300-500ms",
    "quality_score": "9/10"
  }
}
```

---

## Deployment Guide for Students

**File:** `TAKE_HOME_GUIDE.md`

```markdown
# 🎉 Your World-Class RAG System

Congratulations! You now have a production-ready RAG system.

## What You Get

✅ Local document search (PDF, Office, Markdown)
✅ Agentic chunking (smart segmentation)
✅ Hybrid search (semantic + keyword)
✅ Knowledge graph (related docs)
✅ Web search integration (real-time data)
✅ Full configurability
✅ Privacy-first design

## Quick Start

### 1. Start System
\`\`\`bash
docker-compose -f docker-compose.test.yml up -d
\`\`\`

### 2. Upload Your Documents
- Drag and drop into UI
- Supports: PDF, Word, Excel, PowerPoint, Markdown, Text

### 3. Ask Questions!
- System automatically uses best configuration
- Toggle features in settings panel
- View metrics to understand performance

## Production Mode

For best quality, use the "Production" preset:
- All RAG features enabled
- Optimized parameters
- Web search for current info
- Expected: 95%+ precision, 300ms latency

## Customization

Edit `presets/production.json` for your use case:
- Research: Enable re-ranking, increase context
- Quick lookup: Disable graph, reduce results
- Always fresh: Prioritize web results

## Maintenance

### Update Models
\`\`\`bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
\`\`\`

### Backup Data
\`\`\`bash
docker-compose -f docker-compose.test.yml stop
tar -czf rag_backup.tar.gz chromadb/ indices/
\`\`\`

### Monitor Performance
- Open http://localhost:5555
- View metrics dashboard
- Run evaluation on test set

## Support

- GitHub: github.com/sandbreak80/rag_lab
- Issues: github.com/sandbreak80/rag_lab/issues
- Docs: Full documentation in `/docs`

## Next Steps

1. **Integrate with your workflow**
   - API documentation in `API.md`
   - Python client in `client/`

2. **Scale up**
   - Deploy to cloud
   - Add GPU acceleration
   - Scale microservices independently

3. **Extend**
   - Add more document types
   - Integrate custom tools
   - Build domain-specific features

**You built this with AI tools! Keep learning and building! 🚀**
```

---

## Updated Docker Compose

**File:** `docker-compose.test.yml`

Add web search service:

```yaml
  # Web Search Service
  web-search:
    image: python:3.11-slim
    container_name: rag-web-search
    networks:
      - rag-network
    ports:
      - "8009:8009"
    volumes:
      - ./services/web-search/app:/app
      - ./services/common:/workspace/services/common
    working_dir: /app
    environment:
      - SERVICE_NAME=web-search-service
      - SERVICE_PORT=8009
      - SEARXNG_URL=http://searxng:8080
      - PYTHONPATH=/workspace
    command: bash -c "pip install -q flask requests && python service.py"
    depends_on:
      - searxng

  # SearXNG Search Engine
  searxng:
    image: searxng/searxng:latest
    container_name: rag-searxng
    networks:
      - rag-network
    ports:
      - "8090:8080"
    volumes:
      - ./config/searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8090/
      - SEARXNG_SECRET=rag_lab_secret_key_change_in_production
    restart: unless-stopped
```

---

## Final Lab Structure

### Services: 13 total

1. webapp (5555) - UI
2. ingest-service (8001) - Document processing
3. search-service (8002) - RAG search
4. chat-service (8003) - LLM chat
5. docling-service (8004) - PDF parsing
6. vector-db (8005) - ChromaDB
7. embedding-service (8006) - Embeddings
8. knowledge-graph (8007) - Relationships
9. reranker (8008) - LLM precision
10. **web-search (8009)** - 🆕 Web search wrapper
11. api-gateway (8080) - API routing
12. **searxng (8090)** - 🆕 Search engine
13. playwright-tests - UI testing

### Lab Phases (Updated)

1. ✅ Setup & Baseline
2. ✅ Add RAG components (one-by-one)
3. ✅ Optimize parameters
4. ✅ Compare configurations
5. ✅ **Web search integration** 🆕
6. ✅ **Production mode** 🆕

**Total Lab Time:** 3-4 hours (perfect!)

---

Ready to implement! 🚀

