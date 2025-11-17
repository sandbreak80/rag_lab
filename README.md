# 🎓 Educational RAG Lab

**An enterprise-grade RAG system for learning and experimentation - Built with modern AI architecture**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/status-production%20ready-success.svg)](docs/CURRENT_STATUS.md)
[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](CHANGELOG.md)

> 📘 **[Read Current Status](docs/CURRENT_STATUS.md)** | **[View Changelog](CHANGELOG.md)** - Latest features and improvements

---

## 🌟 What is This?

The Educational RAG Lab is a **production-ready reference architecture** for LLM deployments, designed for hands-on learning and customer demonstrations. It features:

- **20+ Microservices** - Complete production-grade RAG architecture
- **Modern React UI** - TypeScript, Tailwind CSS, real-time streaming
- **Performance Waterfall Chart** - Visualize RAG pipeline latency breakdown
- **Authentication System** - JWT-based user auth with security controls
- **Citation Validation** - Hallucination detection for accurate sourcing
- **Baseline Prompts** - Pre-built queries for performance testing
- **Configuration Toggles** - UI controls for all RAG features
- **Security Guardrails** - PII detection, rate limiting, input sanitization
- **Research Agent** - Autonomous AI paper discovery and ingestion
- **Weighted Scoring** - Prioritizes RAG/Research sources over web results
- **Prompt Editor** - View and edit system prompts via UI
- **Response Caching** - Redis-based caching for page refresh resilience
- **Comprehensive Documentation** - Architecture, deployment, testing guides

**Unique Value:**
> "This isn't just a RAG lab - it's a reference architecture for production LLM deployments, instrumented for Splunk from day one."

**Perfect for:**
- 🎯 **Splunk/Cisco Field Teams** - Architects, SEs, Sales Leaders
- 🎓 **Students** - Learning RAG, LLMs, and production AI
- 👨‍🏫 **Instructors** - Teaching enterprise AI deployment
- 🔬 **Researchers** - Experimenting with RAG configurations
- 👨‍💻 **Developers** - Building production RAG systems

---

## ☁️ AWS EC2 Deployment (Recommended for Production)

**Launch on GPU-enabled EC2 with automated setup:**

### With vLLM Support (g5.2xlarge - NVIDIA A10G)
```bash
cd aws/scripts
./setup-github-secret.sh  # One-time security setup
./launch-g5-vllm.sh        # Launch with vLLM + Ollama
```
- ✅ **vLLM** - 2x faster inference (Ampere GPU)
- ✅ 24GB VRAM - Larger models (13B+)
- ✅ Cost: ~$29/day running, ~$0.65/day stopped

### Ollama Only (g4dn.2xlarge - NVIDIA T4)
```bash
cd aws/scripts
./setup-github-secret.sh   # One-time security setup
./aws-launch-rag-lab.sh    # Launch with Ollama
```
- ✅ **Ollama** - Cost-effective development
- ✅ 16GB VRAM - Small/medium models (7B)
- ✅ Cost: ~$18/day running, ~$0.50/day stopped

**Features:**
- ✅ Automated deployment (10-20 minutes)
- ✅ Secure private repo access (AWS Secrets Manager)
- ✅ No SSH needed (AWS Session Manager)
- ✅ Stop when not using (save 97-98%!)

📘 **[AWS README](aws/README.md)** | **[GPU Compatibility Guide](aws/GPU_COMPATIBILITY_GUIDE.md)** | **[Security Best Practices](docs/deployment/AWS_SECURITY_BEST_PRACTICES.md)**

---

## 🚀 Quick Start (One Command!)

### Fresh Deployment (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/sandbreak80/rag_lab.git
cd rag_lab/scripts

# 2. Run the clean deployment script
./clean-deploy.sh
```

**This will:**
- ✅ Stop all containers & prune Docker
- ✅ Build fresh images (no cache)
- ✅ Start Ollama with GPU support
- ✅ Pull required models (llama3.1:8b + nomic-embed-text)
- ✅ **Prompt for 8 optional models** (for lab exercises)
- ✅ Start all 14 microservices
- ✅ Verify health checks

**Total time:** 15-30 minutes (depending on model downloads)

### Quick Start (Existing Install)

```bash
cd rag_lab/scripts
./build-and-start.sh
```

**No npm, Node.js, Python, or other host dependencies needed.** Everything runs in Docker.

**Time:** ~5-10 minutes (first run with model downloads)

### Access the Application

- **Frontend (React UI)**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Ollama**: http://localhost:11434
- **SearXNG (Web Search)**: http://localhost:8080

### Stop Everything

```bash
cd scripts
./stop.sh
```

### Clean Start (Fresh Install)

```bash
# Remove all data and rebuild
./build-and-start.sh --clean
```

### Docker Compose Commands

```bash
# View logs
docker compose logs -f

# Restart a service
docker compose restart frontend

# Check service status
docker compose ps
```

---

## 📚 Documentation

- 🚀 **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running in minutes
- 🎯 **[Model Selection Guide](docs/MODEL_SELECTION_GUIDE.md)** - Choose the right model for your use case
- 🖥️ **[GPU Setup](docs/deployment/GPU_SETUP.md)** - NVIDIA GPU configuration
- 🐧 **[Ubuntu Deployment](docs/deployment/UBUNTU_DEPLOYMENT.md)** - Server deployment guide
- 📖 **[Complete Project Summary](docs/PROJECT_COMPLETE.md)** - Everything we built

---

## ✨ Key Features

### 🎛️ Interactive Settings Panel
- **6 Quick Presets**: Minimal → Fast → Balanced → Quality → Maximum → Production
- **6 RAG Toggles**: Query Expansion, BM25, Hybrid, Knowledge Graph, Re-ranking, Web Search
- **4 LLM Settings**: Model selection, Temperature, Max Tokens, Context Window
- **Real-time Preview**: See expected performance before running

### 📊 Real-time Metrics Dashboard
- **Component Breakdown**: See exactly where time is spent
- **Performance Tracking**: Latency, precision, recall estimates
- **Visual Indicators**: Color-coded status and percentage breakdowns
- **Expandable Details**: Deep dive into each component's performance

### ⚖️ A/B Comparison Mode
- **Side-by-side Comparison**: Test two configurations simultaneously
- **Automatic Winner**: System determines the better config
- **Intelligent Insights**: AI-generated analysis of differences
- **One-click Switch**: Apply either configuration instantly

### 📖 Progressive Lab Guide
- **6 Interactive Sections**: From beginner to advanced
- **Progress Tracking**: Save your learning progress
- **Hands-on Activities**: Learn by doing
- **Checkpoints**: Verify understanding at each step

---

## 📊 Configuration Presets

| Preset | Latency | Precision | Recall | Use Case |
|--------|---------|-----------|--------|----------|
| **Minimal** | 40ms | 65% | 55% | Baseline, speed tests |
| **Fast** | 60ms | 70% | 60% | High QPS, autocomplete |
| **Balanced** ⭐ | **120ms** | **87%** | **82%** | **Recommended for learning** |
| **Quality** | 250ms | 92% | 88% | Research, complex queries |
| **Maximum** | 2500ms | 96% | 92% | Best possible quality |
| **Production** 🏆 | **300ms** | **94%** | **90%** | **Deploy this!** |

---

## 🏗️ System Architecture

The RAG Lab is built as a **microservices architecture** with **20+ specialized services**:

### Core RAG Pipeline
```
User Query → Frontend (React) → Nginx → RAG API v1
                                         ↓
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
            Vector Search          Web Search         Knowledge Graph
            (Vector DB)          (SearXNG)            (NetworkX)
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         ↓
                              Weighted Scoring
                              (RAG: 1.0x, KG: 0.9x, Web: 0.65x)
                                         ↓
                              Re-ranking (optional)
                                         ↓
                              LLM Synthesis (Ollama)
                                         ↓
                              Response + Sources
```

### Service Categories

**Core RAG Services (4):**
- Vector DB (8005) - ChromaDB embeddings storage
- Embedding Service (8006) - Text-to-vector conversion
- Search Service (8002) - Hybrid search orchestration
- Chat Service (8003) - Conversational interface

**Document Processing (2):**
- Docling Service (8004) - PDF parsing
- Ingest Service (8001) - Document ingestion pipeline

**Advanced RAG (2):**
- Knowledge Graph (8007) - Document relationships
- Reranker (8008) - LLM-based result ranking

**Web Search (2):**
- SearXNG (8080) - Meta-search engine
- Web Search Service (8009) - RAG integration

**Intelligence Layer (6):**
- Research Agent (8015) - Auto-discovery of AI papers
- Prompt Classifier (8017) - Query categorization
- Prompt Enhancement (8012) - Framework-based rewriting
- Model Router (8018) - Intelligent model selection
- Query Decomposer (8019) - Complex query breakdown
- Self-RAG (8020) - Quality-aware retrieval

**API & Frontend (2):**
- RAG API v1 (8080) - Modern FastAPI with observability
- Frontend (3000) - React + TypeScript UI

**Security (2):**
- Security Guardrails (8013) - PII/toxicity detection
- Auth Service (8014) - JWT authentication

**Observability Stack (8):**
- OpenTelemetry Collector - Trace/metric collection
- Prometheus (9090) - Metrics database
- Grafana (3001) - Visualization
- Tempo (3200) - Distributed tracing
- Loki (3100) - Log aggregation
- Promtail - Log shipper
- cAdvisor (9080) - Container metrics
- Node Exporter (9100) - System metrics

**Supporting Services (2):**
- Redis - Response caching & rate limiting
- Metrics Store (8011) - Historical metrics

📖 **Complete Services Reference**: [docs/INFRASTRUCTURE_SERVICES_REFERENCE.md](docs/INFRASTRUCTURE_SERVICES_REFERENCE.md)  
📖 **Full Architecture Documentation**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🎓 Learning Path

### 1. Interactive Lab Guide (1-2 hours)

Built into the UI (📖 button) with 6 progressive sections:
1. Getting Started - Understand the interface
2. Your First Query - Execute searches
3. Understanding Metrics - Read performance data
4. Configuration Experiments - A/B testing
5. Advanced Features - Graph, re-ranking, web search
6. Production Configuration - Deploy-ready system

### 2. Student Exercises (3-4 hours)

10 comprehensive exercises with grading rubric:
- Exercise 1: Baseline Performance
- Exercise 2: Hybrid Search Benefits
- Exercise 3: Performance Profiling
- Exercise 4: Re-ranking Trade-offs
- Exercise 5: Web Search Integration
- Exercise 6: Configuration Optimization
- Exercise 7: A/B Testing
- Exercise 8: Production Deployment
- Exercise 9: Cost Analysis
- Exercise 10: Final Challenge

📖 **Student Exercises**: [docs/lab/STUDENT_EXERCISES.md](docs/lab/STUDENT_EXERCISES.md)

### 3. Technical Deep Dive

Complete system documentation:
- Architecture and design patterns
- API reference for all endpoints
- Performance benchmarks
- Deployment guides
- Development practices

📖 **Comprehensive Documentation**: [docs/COMPREHENSIVE_DOCUMENTATION.md](docs/COMPREHENSIVE_DOCUMENTATION.md)

---

## 🛠️ Technology Stack

### Backend
- **API Framework**: FastAPI (RAG API v1), Flask (legacy services)
- **Language**: Python 3.11
- **Vector Database**: ChromaDB
- **LLM**: Ollama (llama3.1:8b, llama3.2:3b, and more)
- **Search**: Hybrid (Vector + BM25) with Reciprocal Rank Fusion
- **Knowledge Graph**: NetworkX
- **Web Search**: SearXNG (meta-search engine)
- **Document Processing**: Docling (PDF parsing), PyPDF (fallback)
- **Caching**: Redis (response caching, rate limiting)
- **Observability**: OpenTelemetry, Prometheus, Grafana, Tempo, Loki

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Routing**: React Router
- **UI Components**: Radix UI, Lucide Icons
- **Web Server**: Nginx (production build)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Docker Compose (20+ services)
- **Networking**: Docker bridge network
- **Data Persistence**: Docker volumes (14 volumes)
- **GPU Support**: NVIDIA GPU (CUDA) for Ollama

---

## 📦 What's Included

```
rag_lab/
├── docs/                          # Documentation
│   ├── lab/                       # Student learning materials
│   │   ├── QUICK_START.md         # 5-minute setup
│   │   ├── LAB_GUIDE.md           # Interactive guide
│   │   ├── STUDENT_EXERCISES.md   # 10 exercises
│   │   └── LAB_OBJECTIVES.md      # Learning goals
│   ├── development/               # Developer docs
│   ├── deployment/                # Deployment guides
│   └── COMPREHENSIVE_DOCUMENTATION.md
├── services/                      # 10 microservices
│   ├── search/                    # Hybrid search orchestration
│   ├── vector-db/                 # ChromaDB wrapper
│   ├── ingest/                    # Document processing
│   ├── knowledge-graph/           # Graph service
│   ├── reranker/                  # LLM re-ranking
│   ├── web-search/                # SearXNG wrapper
│   └── ...
├── src/                           # Web UI
│   ├── webapp.py                  # Flask server
│   ├── templates/                 # HTML templates
│   └── static/                    # CSS, JavaScript
├── config/                        # Configuration
│   ├── presets.json               # 6 presets
│   └── searxng/                   # SearXNG config
├── tests/                         # Integration tests
│   └── test_integration.py        # 20+ tests (no mocks)
├── docker-compose.test.yml        # Orchestration
└── README.md                      # This file
```

---

## 🧪 Testing

Run the integration test suite (no mocks, real services):

```bash
# Services must be running
docker-compose -f docker-compose.test.yml up -d

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pytest requests

# Run tests
pytest tests/test_integration.py -v
```

20+ integration tests covering:
- Service health checks
- Configurable search with all presets
- Web search integration
- Knowledge graph
- LLM re-ranking
- End-to-end RAG flow
- Metrics accuracy

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](docs/lab/QUICK_START.md) | Get running in 5 minutes |
| [Lab Guide](docs/lab/LAB_GUIDE.md) | Interactive learning guide |
| [Student Exercises](docs/lab/STUDENT_EXERCISES.md) | 10 hands-on exercises |
| [Comprehensive Docs](docs/COMPREHENSIVE_DOCUMENTATION.md) | Complete technical reference |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [API Reference](docs/COMPREHENSIVE_DOCUMENTATION.md#api-reference) | All endpoints |
| [Deployment](docs/deployment/DEPLOYMENT.md) | Production deployment |
| [Context Recovery](CONTEXT_RECOVERY.md) | Quick reference |
| [Project Report](PROJECT_COMPLETION_REPORT.md) | Final status |

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- How to submit issues
- Pull request process
- Development setup
- Coding standards

---

## 📋 Requirements

- **Docker** and **Docker Compose**
- **Ollama** running locally (port 11434)
- **8GB+ RAM** (recommended)
- **10GB+ disk space**
- **Python 3.8+** (for testing)

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
docker ps
docker logs rag-web-ui
```

### Ollama Connection Failed
```bash
curl http://localhost:11434/api/tags
```

### No Search Results
Upload documents first via the UI (drag-and-drop).

### Web Search Timeout
Check SearXNG: `curl http://localhost:8080/search?q=test&format=json`

📖 **Full Troubleshooting Guide**: [docs/COMPREHENSIVE_DOCUMENTATION.md#troubleshooting](docs/COMPREHENSIVE_DOCUMENTATION.md#troubleshooting)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

**TL;DR**: Free to use, modify, and deploy. Including commercially.

---

## 🙏 Acknowledgments

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Ollama](https://ollama.ai/) - Local LLM
- [SearXNG](https://github.com/searxng/searxng) - Metasearch engine
- [Docling](https://github.com/DS4SD/docling) - Document processing
- [NetworkX](https://networkx.org/) - Knowledge graph
- [Rank-BM25](https://github.com/dorianbrown/rank_bm25) - Keyword search

---

## 📞 Support & Community

- **Issues**: [GitHub Issues](https://github.com/sandbreak80/rag_lab/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sandbreak80/rag_lab/discussions)
- **Documentation**: [docs/](docs/)
- **Email**: [Your Contact]

---

## 🎯 Project Status

✅ **Production Ready** (v1.0.0)

- ✅ All 10 microservices operational
- ✅ All 6 presets tested
- ✅ Complete documentation (40,000+ words)
- ✅ Student exercises ready
- ✅ Integration tests passing
- ✅ Web search integrated
- ✅ A/B comparison working
- ✅ Lab guide complete

---

## 🚀 Next Steps

1. **Quick Start**: [docs/lab/QUICK_START.md](docs/lab/QUICK_START.md)
2. **Open UI**: http://localhost:5555
3. **Follow Lab Guide**: Click 📖 button in UI
4. **Complete Exercises**: [docs/lab/STUDENT_EXERCISES.md](docs/lab/STUDENT_EXERCISES.md)
5. **Deploy**: Use Production preset 🏆

---

## ⭐ Star this repo if you find it useful!

Built with ❤️ for education

**Educational RAG Lab v1.0.0** - Interactive Learning Environment for RAG Systems
