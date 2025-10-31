# 📚 Documentation Index

**Complete Guide to World-Class RAG System**

This index helps you navigate all documentation for the Markdown RAG MCP Server.

---

## 🚀 Getting Started

**New to the project? Start here:**

1. **[README.md](../README.md)** - Project overview, quick start, features
2. **[QUICK_STATUS.md](../QUICK_STATUS.md)** - Current system status at a glance
3. **[COMPREHENSIVE_TEST_REPORT.md](../COMPREHENSIVE_TEST_REPORT.md)** - Test results and performance metrics

**Estimated reading time:** 30 minutes

---

## 📖 Core Documentation

### Architecture & Design

**[ARCHITECTURE.md](ARCHITECTURE.md)**  
Deep technical dive into system architecture, component design, data flow, and algorithms.

**Topics covered:**
- System overview and technology stack
- Component architecture (Parser, Chunker, Searcher, etc.)
- Data flow (ingestion, query pipeline)
- Algorithm details (RRF, BM25, graph traversal)
- Design decisions and trade-offs
- Scalability considerations
- Security model

**Audience:** Developers, architects  
**Reading time:** 60 minutes

---

### RAG Techniques & Performance

**[RAG_DEEP_DIVE.md](RAG_DEEP_DIVE.md)**  
Exhaustive explanation of RAG features, why they work, and how they're implemented.

**Topics covered:**
- What is RAG? (fundamentals)
- Problems with naive RAG
- Agentic chunking (deep dive)
- Hybrid search (Vector + BM25 + RRF)
- Query expansion strategies
- Knowledge graph implementation
- LLM re-ranking trade-offs
- Technology stack decisions
- Performance analysis
- Real-world examples
- Comparison with alternatives

**Audience:** ML engineers, RAG practitioners  
**Reading time:** 90 minutes

---

### Roadmap & Future Plans

**[ROADMAP.md](ROADMAP.md)**  
Complete development roadmap from completed features to long-term vision.

**Topics covered:**
- Completed features (Phases 1-3)
- Current status and known issues
- Short-term roadmap (3 months)
  - Performance optimizations
  - Incremental indexing
  - Advanced filters
- Medium-term roadmap (6 months)
  - Multi-vault support
  - PDF/document support
  - Multi-modal RAG
- Long-term vision (12+ months)
  - Distributed deployment
  - Active learning
  - Enterprise features
- Research ideas (GNNs, ColBERT, multilingual)
- Community requests

**Audience:** Contributors, stakeholders  
**Reading time:** 45 minutes

---

## 🧪 Testing & Quality

### Test Reports

**[COMPREHENSIVE_TEST_REPORT.md](../COMPREHENSIVE_TEST_REPORT.md)**  
Complete test results, performance benchmarks, and quality metrics.

**Contents:**
- Test results (60/60 passing)
- Performance metrics (recall, precision, latency)
- Component impact analysis
- Issues found and fixed
- Test coverage breakdown
- Performance benchmarks
- Recommendations

**Audience:** QA, developers  
**Reading time:** 30 minutes

---

### Dependencies

**[DEPENDENCIES.md](../DEPENDENCIES.md)**  
Complete list of project dependencies and installation guide.

**Contents:**
- Core dependencies (ChromaDB, Ollama, Flask)
- Advanced RAG dependencies (rank-bm25, NetworkX)
- Testing dependencies (pytest, Playwright)
- Installation instructions
- Troubleshooting

**Audience:** Developers, DevOps  
**Reading time:** 15 minutes

---

## 🛠️ Development

### Development Practices

**[DEV_PRACTICES.md](../DEV_PRACTICES.md)**  
Coding standards, workflow, and best practices.

**Contents:**
- Docker-only development enforcement
- Code style and formatting
- Git workflow
- Testing requirements
- Documentation standards

**Audience:** Contributors  
**Reading time:** 20 minutes

---

### Examples

Located in `examples/` directory:

- **quick_search.py** - Basic search example
- **quick_folder_search.py** - Folder-filtered search
- **study_helper.py** - Interactive study tool
- **evaluate_rag.py** - RAG evaluation framework
- **bluebelt_study_helper.py** - AI Blue Belt study assistant

**Audience:** Users, developers  
**Usage:** `python examples/<script>.py`

---

## 📝 Reference

### Configuration

See `src/config.py` for all configuration options:

```python
# Core settings
VAULT_PATH = os.getenv("VAULT_PATH", "/vault")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:3b")

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
AGENTIC_CHUNKING_ENABLED = True
AGENTIC_TARGET_CHUNK_SIZE = 800
AGENTIC_MAX_CHUNK_SIZE = 1500

# Search
DEFAULT_SEARCH_LIMIT = 10
SEARCH_MODE = "advanced"  # or "vector" or "hybrid"
```

---

### API Reference

#### REST API Endpoints

**GET /**  
Serve web UI

**GET /api/stats**  
Get system statistics
```json
{
  "total_chunks": 671,
  "embedding_model": "nomic-embed-text",
  "chat_model": "llama3.2:3b",
  "search_mode": "advanced"
}
```

**POST /api/search**  
Search documents
```json
Request:
{
  "query": "What is RAG?",
  "limit": 10
}

Response:
[
  {
    "file_name": "RAG_basics.md",
    "content": "RAG stands for...",
    "score": 0.95,
    "metadata": {...}
  },
  ...
]
```

**POST /api/chat**  
RAG-based chat with streaming
```json
Request:
{
  "query": "Explain how RAG works",
  "history": []
}

Response: Server-Sent Events (SSE)
data: {"type": "chunk", "content": "RAG "}
data: {"type": "chunk", "content": "combines "}
data: {"type": "chunk", "content": "retrieval..."}
```

---

### MCP Tools

Available when running as MCP server:

| Tool | Description |
|------|-------------|
| `search_notes` | Semantic search with filters |
| `ask_vault` | RAG-based Q&A |
| `find_similar` | Similar document discovery |
| `find_linked` | Wikilink connections |
| `summarize_topic` | Topic summarization |
| `get_vault_stats` | Index statistics |

---

## 🚨 Troubleshooting

### Common Issues

**Issue:** Cannot connect to Ollama  
**Solution:** See [README.md - Troubleshooting](../README.md#-troubleshooting)

**Issue:** Index not found  
**Solution:** Run `python src/indexer.py`

**Issue:** Port 5555 in use  
**Solution:** Kill process or change port in `docker-compose.yml`

**Issue:** Playwright browser not found  
**Solution:** Run `playwright install --with-deps chromium`

**Full troubleshooting guide:** [README.md - Troubleshooting](../README.md#-troubleshooting)

---

## 📊 Performance Metrics

### Current Performance (October 2024)

```
Recall:      100% ✅ (finds all relevant documents)
Precision:   68%  ✅ (minimal false positives)
Latency:     74ms ⚡ (real-time search)
P95:         151ms ⚡ (95th percentile)

Scale:
  Files:     93
  Chunks:    671
  Memory:    360MB
  Disk:      156MB
```

### Component Impact

```
Feature               Recall    Precision  Latency
──────────────────────────────────────────────────
Agentic Chunking      +15%      +5%        -
Hybrid Search         +20%      -          +20ms
Query Expansion       +5%       -          +1ms
Knowledge Graph       +5%       -          +15ms
LLM Re-ranking        -         +10%       +2000ms
```

**Full analysis:** [COMPREHENSIVE_TEST_REPORT.md](../COMPREHENSIVE_TEST_REPORT.md)

---

## 🎓 Learning Path

### For Users

1. Read **README.md** (overview)
2. Follow **Quick Start** (5 minutes)
3. Try **examples/** (hands-on)
4. Read **RAG_DEEP_DIVE.md** (understand how it works)

### For Developers

1. Read **README.md** (overview)
2. Read **ARCHITECTURE.md** (system design)
3. Read **DEV_PRACTICES.md** (standards)
4. Study `src/` code (implementation)
5. Read **COMPREHENSIVE_TEST_REPORT.md** (quality)
6. Read **ROADMAP.md** (contribute!)

### For ML Engineers

1. Read **RAG_DEEP_DIVE.md** (techniques)
2. Read **ARCHITECTURE.md** (algorithms)
3. Study `src/advanced_search.py` (implementation)
4. Run **tests/test_rag_performance.py** (benchmarks)
5. Read **ROADMAP.md** (research ideas)

---

## 🤝 Contributing

**Want to contribute?**

1. Read **[DEV_PRACTICES.md](../DEV_PRACTICES.md)** - Development standards
2. Read **[ROADMAP.md](ROADMAP.md)** - See what's planned
3. Check **[GitHub Issues](https://github.com/sandbreak80/laptop_rag/issues)** - Find tasks
4. Open **[GitHub Discussion](https://github.com/sandbreak80/laptop_rag/discussions)** - Propose ideas

**Contribution areas:**
- 📝 Documentation improvements
- 🧪 More test coverage
- 🎨 UI/UX enhancements
- 🚀 Performance optimizations
- 🌐 Internationalization
- 📱 Mobile app development

---

## 📬 Support

### Get Help

- 📖 **Documentation** - Start here!
- 🐛 **Issues** - [Report bugs](https://github.com/sandbreak80/laptop_rag/issues)
- 💬 **Discussions** - [Ask questions](https://github.com/sandbreak80/laptop_rag/discussions)
- 📧 **Email** - maintainer@example.com

### Resources

- **GitHub** - https://github.com/sandbreak80/laptop_rag
- **Ollama** - https://ollama.ai
- **ChromaDB** - https://www.trychroma.com/
- **MCP** - https://modelcontextprotocol.io

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) file for details.

---

<p align="center">
  <strong>🎯 Built for Excellence</strong><br>
  <sub>100% recall, 96% code coverage, comprehensive documentation</sub>
</p>

<p align="center">
  <a href="../README.md">Home</a> •
  <a href="ARCHITECTURE.md">Architecture</a> •
  <a href="RAG_DEEP_DIVE.md">RAG Guide</a> •
  <a href="ROADMAP.md">Roadmap</a> •
  <a href="../COMPREHENSIVE_TEST_REPORT.md">Tests</a>
</p>

---

**Last Updated:** October 31, 2025

