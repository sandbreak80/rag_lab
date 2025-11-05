# RAG Lab - Quick Reference

**Last Updated:** November 5, 2025
**Services:** 18 running
**Status:** ✅ Production ready (needs security hardening for internet)

---

## 🚀 Quick Start

### Access the System
- **Frontend:** http://localhost:3000
- **API Gateway:** http://localhost:8000
- **Ollama:** http://localhost:11434

### Test the System
```bash
# Health check all services
docker ps

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}'

# Trigger research agent
curl -X POST http://localhost:8015/trigger/all
```

---

## 🔌 Service Endpoints

### Core RAG Services
| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| **API Gateway** | 8000 | `/chat`, `/search` | Main entry point |
| **Vector DB** | 8005 | `/store`, `/query` | Document storage |
| **Ingest** | 8001 | `/upload`, `/ingest` | Document processing |
| **Search** | 8002 | `/search` | Hybrid search |
| **Chat** | 8003 | `/chat` | Conversational AI |

### Intelligence Layer (NEW)
| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| **Prompt Classifier** | 8017 | `/classify` | Query analysis |
| **Prompt Enhancement** | 8012 | `/enhance` | Framework-based rewriting |
| **Model Router** | 8018 | `/route` | Dynamic model selection |
| **Research Agent** | 8015 | `/status`, `/trigger/all` | Auto-discovery |

### LLM & Search
| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| **Ollama** | 11434 | `/api/generate` | Multi-model LLM |
| **SearXNG** | 8080 | `/search` | Meta search |
| **Web Search** | 8009 | `/search` | SearXNG wrapper |

### Support Services
| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| **Docling** | 8004 | `/convert` | PDF processing |
| **Embedding** | 8006 | `/embed` | Text embeddings |
| **Reranker** | 8008 | `/rerank` | Result ranking |
| **Auth** | 8014 | `/login`, `/verify` | Authentication |
| **Security** | 8013 | `/validate` | Input validation |
| **Redis** | 6379 | - | Caching |

---

## 🧠 New Features (Nov 5, 2025)

### 1. Prompt Classifier
Analyzes query intent, complexity, and recommends models

```bash
curl -X POST http://localhost:8017/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "How does hybrid search work?"}'
```

**Response:**
```json
{
  "intent": "informational",
  "domain": "technical",
  "complexity": 3,
  "detail_level": "moderate",
  "recommended_model": "gemma2:9b"
}
```

---

### 2. Prompt Enhancement
Rewrites queries using frameworks (CoT, ReAct, Few-Shot)

```bash
curl -X POST http://localhost:8012/enhance \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare RAG vs fine-tuning", "documents": []}'
```

**Strategies:**
- **CoT:** Step-by-step reasoning
- **ReAct:** Reasoning + acting
- **Few-Shot:** Example-based
- **Structured:** JSON output

---

### 3. Model Router
Automatically selects best LLM model

```bash
curl -X POST http://localhost:8018/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain quantum entanglement"}'
```

**Routing Logic:**
- **Simple (1-2)** → llama3.2:3b
- **Moderate (3)** → gemma2:9b
- **Complex (4-5)** → qwen2.5:14b

---

### 4. Research Agent
Autonomous AI research discovery

```bash
# Status
curl http://localhost:8015/status

# Trigger manual fetch
curl -X POST http://localhost:8015/trigger/all

# Get sources
curl http://localhost:8015/sources

# Get discovered items
curl http://localhost:8015/items
```

**Data Sources:**
- ✅ arXiv AI/ML papers
- ✅ Hugging Face Papers
- ✅ TechCrunch AI news
- ✅ VentureBeat AI news
- ✅ The Verge AI news
- ✅ OpenAI Blog

**Stats:**
- 91 items ingested
- 94.4% success rate
- Daily fetches at 2 AM UTC

---

## 📊 Models Available

### Ollama Models (Running)
```bash
curl http://localhost:11434/api/tags
```

**Loaded Models:**
- `llama3.2:1b` - Ultra-fast, simple queries
- `gemma2:2b` - Fast, general use
- `llama3.2:3b` - Default for simple queries
- `mistral:7b` - Standard queries
- `llama3.1:8b` - Balanced performance
- `gemma2:9b` - Moderate complexity
- `qwen2.5:14b` - Complex reasoning

**Embedding Model:**
- `mxbai-embed-large:latest` - Document embeddings

---

## 🗂️ Research Agent Data

### Current Ingestion Stats
```bash
# Get full status
curl -s http://localhost:8015/status | jq '.'

# Get recent items
curl -s http://localhost:8015/items?status=ingested | jq '.items[:5]'

# Get fetch history
curl -s http://localhost:8015/history?limit=10 | jq '.'
```

### Database Location
- **Path:** `/home/ubuntu/rag_lab/services/research-agent/data/research.db`
- **Type:** SQLite
- **Tables:** `sources`, `items`, `fetch_history`

---

## 🔧 Common Operations

### Restart Services
```bash
cd /home/ubuntu/rag_lab

# Restart specific service
docker compose restart research-agent

# Restart all
docker compose restart

# View logs
docker logs -f rag-research-agent
```

### Check Service Health
```bash
# All services
docker ps

# Specific service
curl http://localhost:8015/health
```

### GPU Status
```bash
# Check VRAM usage
nvidia-smi

# Detailed stats
nvidia-smi --query-gpu=name,memory.used,memory.free,utilization.gpu --format=csv
```

### Database Operations
```bash
# Research agent DB
docker exec rag-research-agent python -c "
import sys; sys.path.insert(0, '/app')
from database import Database
db = Database()
stats = db.get_stats()
print(stats)
"
```

---

## 📚 Documentation

### Architecture & Design
- `docs/FRAMEWORK_DECISION.md` - Why custom stack vs LangChain
- `docs/LLM_INFERENCE_COMPARISON.md` - Ollama vs vLLM vs llama.cpp
- `docs/VLLM_HARDWARE_REQUIREMENTS.md` - A4000 upgrade path
- `docs/UBUNTU_DEPLOYMENT.md` - Full deployment guide

### Development
- `docs/dev_notes/SESSION_COMPLETE_NOV_5_2025.md` - Today's progress
- `docs/NEXT_FEATURES_QUEUE.md` - Future enhancements
- `docs/SECURITY_HARDENING_INTERNET_FACING.md` - Security checklist

### Research Agent
- `docs/research-agent/README.md` - Research agent overview
- `docs/RESEARCH_AGENT_METADATA_BEST_PRACTICES.md` - Metadata guide
- `docs/RESEARCH_AGENT_SCRAPING_STACK.md` - Scraper tech stack

---

## 🎯 Next Steps

### Immediate (This Week)
1. ✅ Wire classifier/enhancer/router into API Gateway
2. ✅ Add UI toggles for prompt enhancement
3. ✅ Test full end-to-end flow

### Short Term (This Month)
1. 📊 Metadata filtering UI
2. 🧠 Query decomposition
3. 📱 Research agent dashboard

### Long Term (Next Quarter)
1. 🏗️ A4000 GPU upgrade → Enable vLLM
2. 🔄 Self-RAG implementation
3. 🌐 Production deployment with security hardening

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker logs rag-[service-name]

# Restart with rebuild
docker compose up -d --build [service-name]
```

### Out of VRAM
```bash
# Check usage
nvidia-smi

# Restart Ollama
docker compose restart ollama
```

### Research Agent Not Fetching
```bash
# Check scheduler
curl http://localhost:8015/health

# Manual trigger
curl -X POST http://localhost:8015/trigger/all

# Check logs
docker logs rag-research-agent | tail -50
```

### Ingest Service 404
```bash
# Check if running
docker ps | grep ingest

# Test endpoint
curl http://localhost:8001/health

# For programmatic ingest, use /ingest not /upload
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "test", "filename": "test.md", "metadata": {}}'
```

---

## 📞 Quick Commands Reference

```bash
# System status
docker ps
nvidia-smi

# Test core services
curl http://localhost:8000/health  # API Gateway
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8015/status  # Research Agent

# Trigger research fetch
curl -X POST http://localhost:8015/trigger/all

# Classify a query
curl -X POST http://localhost:8017/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here"}'

# Enhance a query
curl -X POST http://localhost:8012/enhance \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here", "documents": []}'

# Route to best model
curl -X POST http://localhost:8018/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here", "context": {}}'

# Full chat (goes through API Gateway)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "user_id": "test"}'
```

---

## 🎓 Learning Path

### Beginner → Intermediate
1. Understand basic RAG flow (ingest → embed → search → generate)
2. Experiment with different query types
3. Compare search strategies (vector vs hybrid)

### Intermediate → Advanced
1. Study prompt classification logic
2. Understand framework-based enhancement (CoT, ReAct)
3. Explore model routing decisions
4. Investigate research agent scrapers

### Advanced → Expert
1. Implement query decomposition
2. Build Self-RAG (iterative refinement)
3. Deploy vLLM with A4000
4. Scale to production (multi-user, load balancing)

---

## ✅ System Checklist

Before starting work:
- [ ] All services running (`docker ps`)
- [ ] Ollama models loaded (`curl localhost:11434/api/tags`)
- [ ] GPU available (`nvidia-smi`)
- [ ] Research agent healthy (`curl localhost:8015/health`)

After changes:
- [ ] Services restarted (`docker compose restart`)
- [ ] Logs checked (`docker logs [service]`)
- [ ] Endpoints tested (health checks)
- [ ] Documentation updated

---

**Happy RAG Building! 🚀**

