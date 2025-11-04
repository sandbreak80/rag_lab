# 🚀 RAG Lab Scripts

**Clean, simple scripts for running the Enterprise Agentic AI Platform.**

---

## 📋 Available Scripts

### 🏗️ Main Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| **`clean-deploy.sh`** | 🧹 **Clean slate deployment** - Removes everything & rebuilds | `./clean-deploy.sh` |
| **`build-and-start.sh`** | 🎯 **Quick setup** - Builds & starts (keeps existing images) | `./build-and-start.sh` |
| **`stop.sh`** | Stop all services | `./stop.sh` |
| **`pull-ollama-models.sh`** | Pull/update Ollama models | `./pull-ollama-models.sh` |
| **`reingest-system-docs.sh`** | Re-ingest project documentation | `./reingest-system-docs.sh` |

---

## 🎯 Quick Start (Ubuntu Server)

### First Time Setup (Clean Install)

```bash
# 1. Clone the repo
git clone https://github.com/sandbreak80/rag_lab.git
cd rag_lab/scripts

# 2. Run the clean deployment script
./clean-deploy.sh
```

This will:
- ✅ Stop any existing containers
- ✅ Remove old images
- ✅ Prune Docker system
- ✅ Build fresh images (no cache)
- ✅ Start Ollama with GPU
- ✅ Pull models (llama3.1:8b, mxbai-embed-large)
- ✅ Start all services
- ✅ Run health checks

**Time:** ~10-15 minutes (first run with model downloads)

### Quick Update (Keeps Existing Images)

```bash
cd ~/rag_lab
git pull origin main
cd scripts
./build-and-start.sh
```

Faster than clean deploy, but may use cached images.

**No npm, Node.js, Python, or other dependencies needed on host!**

---

## 📖 Detailed Command Reference

### 🧹 clean-deploy.sh (NEW!)

**Complete fresh start** - Removes everything and rebuilds from scratch.

```bash
# Clean deployment (removes all images, prunes system)
./clean-deploy.sh
```

**What it does:**
1. Stops all RAG Lab containers
2. Removes all RAG Lab Docker images
3. Prunes Docker system (unused images, networks, build cache)
4. Asks if you want to remove data volumes
5. Builds all images with --no-cache
6. Starts Ollama and waits for health check
7. Pulls models (llama3.1:8b, mxbai-embed-large)
8. Starts all services
9. Verifies all services are healthy

**Interactive prompts:**
- Confirmation before proceeding
- Option to keep or remove data volumes

**When to use:**
- ✅ Fresh install on new server
- ✅ After major updates
- ✅ When build cache causes issues
- ✅ When images are corrupted
- ✅ For troubleshooting

**Time:** ~10-15 minutes (includes model downloads)

**Warning:** This removes ALL Docker images and prunes the system!

---

### 🏗️ build-and-start.sh

**One-command deployment** - Builds everything and starts all services.

```bash
# Standard start (keeps existing data)
./build-and-start.sh

# Clean start (removes all volumes - fresh install)
./build-and-start.sh --clean
```

**What it does:**
1. Validates Docker & Docker Compose are installed
2. Stops existing containers
3. Builds Docker images (frontend build happens inside container)
4. Starts Ollama service
5. Waits for Ollama to be ready
6. Pulls LLM models (llama3.2:3b, nomic-embed-text)
7. Starts all services with dependencies
8. Shows service URLs

**Options:**
- `--clean` - Remove all data volumes (fresh start)

**Time:** ~5-10 minutes (first run with model downloads)

---

### 🛑 stop.sh

**Stop all services cleanly.**

```bash
# Stop all containers
./stop.sh

# Stop and remove volumes (clean slate)
./stop.sh --clean
```

**Options:**
- `--clean` - Remove all data volumes

---

### 🤖 pull-ollama-models.sh

**Pull or update Ollama models.**

```bash
# Pull required models (llama3.2:3b, nomic-embed-text)
./pull-ollama-models.sh

# Pull all models including test models
./pull-ollama-models.sh --all
```

**Required Models:**
- `llama3.2:3b` - Fast chat model
- `nomic-embed-text` - Embedding model

**Optional Test Models:**
- `llama3.2:1b` - Tiny model for testing
- `llama3.1:8b` - Larger model for comparison
- `llama3.2:latest` - Latest version

---

### 📚 reingest-system-docs.sh

**Re-ingest project documentation into the RAG system.**

Useful after updating documentation or changing chunking strategies.

```bash
./reingest-system-docs.sh
```

---

## 🌐 Service URLs

After running `build-and-start.sh`, access services at:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main React UI |
| **API Gateway** | http://localhost:8000 | Backend API |
| **Ollama** | http://localhost:11434 | LLM service |
| **SearXNG** | http://localhost:8080 | Web search |

### Microservices (Internal)

These services are accessed through the API Gateway:

- Vector DB: `http://localhost:8005`
- Embedding: `http://localhost:8006`
- Knowledge Graph: `http://localhost:8007`
- Search: `http://localhost:8002`
- Chat: `http://localhost:8003`
- Ingest: `http://localhost:8001`
- Docling: `http://localhost:8004`
- Reranker: `http://localhost:8008`
- Web Search: `http://localhost:8009`
- Metrics Store: `http://localhost:8011`

---

## 🔧 Troubleshooting

### Docker Compose Not Found

If you see `docker-compose not found`:

**Modern Docker (Recommended):**
```bash
docker compose version
```

The scripts now use `docker compose` (without dash) by default.

**Legacy Docker:**
If you have old `docker-compose` standalone:
```bash
sudo apt update
sudo apt install docker-compose-plugin
```

### Ollama Models Fail to Pull

If Ollama can't pull models:

```bash
# Check Ollama is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Manually pull a model
docker compose exec ollama ollama pull llama3.2:3b
```

### Services Won't Start

```bash
# Check service status
docker compose ps

# Check logs for a specific service
docker compose logs vector-db
docker compose logs frontend

# Restart a specific service
docker compose restart vector-db
```

### Port Conflicts

If ports are already in use:

```bash
# Find what's using the port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

### Fresh Start (Nuclear Option)

If everything is broken:

```bash
# Stop everything and remove all data
./stop.sh --clean

# Rebuild from scratch
./build-and-start.sh --clean
```

---

## 🐳 Docker Compose Commands

For manual control:

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f frontend

# Restart a service
docker compose restart frontend

# Rebuild a service
docker compose build frontend
docker compose up -d frontend

# Check service status
docker compose ps

# Remove everything including volumes
docker compose down -v
```

---

## 📦 What Gets Built

### Docker Images

- `rag_lab-frontend` - React UI (Vite + Nginx)
- `python:3.11-slim` - Used by all backend services
- `ollama/ollama:latest` - LLM inference engine
- `searxng/searxng:latest` - Web search engine

### Volumes (Data Persistence)

- `chromadb-data` - Vector embeddings
- `bm25-indices` - Keyword search indices
- `knowledge-graph` - Graph relationships
- `uploads` - Uploaded documents
- `metrics-data` - Performance metrics
- `ollama-models` - LLM models

---

## 🎓 Educational Use

This setup is designed for **Splunk/Cisco field teams** to learn:
- RAG architecture and microservices
- LLM integration and observability
- Security considerations for LLMs
- Prompt engineering and optimization
- Performance tuning and monitoring

See `docs/lab/` for hands-on exercises.

---

## 🔐 Production Notes

**This is an educational lab environment.**

For production deployment:
- Add authentication and authorization
- Implement rate limiting
- Enable SSL/TLS
- Set up proper monitoring (Prometheus/Grafana)
- Configure resource limits
- Implement security controls (see `docs/SECURITY_ENHANCEMENT_PLAN.md`)

---

## 📚 Documentation

- **Architecture:** `docs/ARCHITECTURE.md`
- **Security:** `docs/SECURITY_ENHANCEMENT_PLAN.md`
- **Lab Exercises:** `docs/lab/`
- **Project Status:** `docs/PROJECT_COMPLETE.md`

---

**Questions?** See the main README or open an issue on GitHub.
