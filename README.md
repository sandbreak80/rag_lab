# 🧪 RAG Lab: Complete Local AI + RAG System

**Production-ready local AI development environment with world-class RAG capabilities**

This is a **unified project** containing:
1. **Infrastructure Setup** - Ollama installation, model management, Obsidian integration
2. **World-Class RAG System** - Agentic chunking, hybrid search, knowledge graphs

---

## 🚀 Quick Start

### Step 1: Setup Infrastructure (One-Time, 30-60 min)

```bash
# Install Ollama, pull models, setup environment
./setup.sh
```

This installs:
- ✅ Ollama (local AI runtime)
- ✅ 8 AI models (Llama, Qwen, Gemma, DeepSeek)
- ✅ Obsidian Local REST API
- ✅ All dependencies

### Step 2: Start RAG System (2 minutes)

```bash
# Build and start Docker container
docker-compose build
docker-compose up -d

# Index your vault
docker-compose exec markdown-rag-mcp python src/indexer.py

# Start web UI
docker-compose exec markdown-rag-mcp make webapp
```

### Step 3: Use It!

Open **http://localhost:5555** and start asking questions about your notes!

---

## 📂 Project Structure

```
rag_lab/
├── setup.sh                    # Infrastructure setup script
├── cleanup.sh                  # Cleanup utilities
├── pull_models.sh              # Model management
│
├── src/                        # RAG system source code
│   ├── webapp.py              # Flask web UI
│   ├── advanced_search.py     # Advanced search orchestrator
│   ├── agentic_chunker.py     # LLM-powered chunking
│   ├── hybrid_search.py       # Vector + BM25 search
│   ├── knowledge_graph.py     # Relationship discovery
│   └── query_expansion.py     # Query enhancement
│
├── docs/                       # Complete documentation
│   ├── README.md              # Documentation index
│   ├── RAG_FEATURES.md        # How RAG works
│   ├── ARCHITECTURE.md        # System design
│   ├── PERFORMANCE.md         # Benchmarks
│   └── ROADMAP.md             # Future plans
│
├── tests/                      # 60 comprehensive tests
│   ├── test_parser.py
│   ├── test_search.py
│   ├── test_dependencies.py
│   └── test_rag_performance.py
│
├── docker-compose.yml          # Docker setup
├── Dockerfile                  # Container definition
├── Makefile                    # Helper commands
└── requirements.txt            # Python dependencies
```

---

## ✨ What You Get

### Infrastructure (setup.sh)
- 🤖 **Ollama** - Local AI runtime (no cloud needed)
- 📦 **8 AI Models** - Llama 3.2, Qwen 2.5, Gemma 2, DeepSeek, etc.
- 📝 **Obsidian Integration** - Local REST API for vault access
- 🔧 **Development Tools** - Python, Docker, testing frameworks

### RAG System (src/)
- 🧠 **Agentic Chunking** - LLM-powered semantic segmentation
- 🔍 **Hybrid Search** - Vector + BM25 + Reciprocal Rank Fusion
- 💬 **Query Expansion** - Context-aware term enhancement
- 🌐 **Knowledge Graph** - Wikilink relationship discovery
- 🎨 **Modern Web UI** - Streaming responses, markdown rendering
- 📊 **100% Recall** - Finds every relevant document
- ⚡ **74ms Latency** - Real-time search

---

## 📊 Performance

- ✅ **100% recall** (vs 70-80% target) - Exceeded by 25%
- ✅ **68% precision** (vs 60-70% target) - Within range
- ⚡ **74ms average latency** (vs 3000ms target) - 40x faster
- 🧪 **60 passing tests** (96% code coverage)
- 📦 **671 chunks indexed** from 93 files

---

## 📚 Documentation

Complete documentation is in the `docs/` folder:

- **[Getting Started](docs/README.md)** - Navigation and quick links
- **[RAG Features](docs/RAG_FEATURES.md)** - How it works (1,800 lines)
- **[Architecture](docs/ARCHITECTURE.md)** - System design (2,100 lines)
- **[Performance](docs/PERFORMANCE.md)** - Benchmarks (1,900 lines)
- **[Roadmap](docs/ROADMAP.md)** - Future plans (1,200 lines)

**Total:** 7,500+ lines of comprehensive documentation

---

## 🛠️ Usage

### Setup Commands

```bash
# First-time setup
./setup.sh

# Update models
./pull_models.sh

# Upgrade Ollama
./upgrade_ollama.sh

# Check for model updates
./check_model_updates.sh

# Cleanup
./cleanup.sh
```

### RAG Commands

```bash
# Start container
docker-compose up -d

# Index vault
make index

# Start web UI
make webapp

# Run tests
make test

# Search from CLI
python examples/quick_search.py
```

---

## 🎯 Use Cases

1. **Study Assistant** - Ask questions about your study notes
2. **Research Helper** - Find related documents and concepts
3. **Knowledge Management** - Discover connections in your vault
4. **Document Search** - Semantic search across all your markdown files
5. **AI Development** - Build on top of the RAG infrastructure

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **Ollama** - Local AI runtime
- **ChromaDB** - Vector database
- **Flask** - Web framework
- **NetworkX** - Graph library
- **Obsidian** - Note-taking inspiration

---

**Built with ❤️ for the local AI community**

🔗 **Repository:** https://github.com/sandbreak80/rag_lab
