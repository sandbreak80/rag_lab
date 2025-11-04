# 🚀 Quick Start Guide

## One-Command Deployment

```bash
cd scripts
./clean-deploy.sh
```

This will:
1. ✅ Stop all containers
2. ✅ Remove old RAG Lab images
3. ✅ Prune Docker system
4. ✅ Build fresh images (no cache)
5. ✅ Start Ollama with GPU support
6. ✅ Pull required models (llama3.1:8b + nomic-embed-text)
7. ✅ **Prompt for optional models** (8 additional models for lab exercises)
8. ✅ Start all services
9. ✅ Verify health checks

**Total time:** 15-30 minutes (depending on model downloads)

---

## 🎯 Access the Application

Once deployment completes:

- **Frontend UI:** http://localhost:3000
- **API Gateway:** http://localhost:8000
- **Ollama API:** http://localhost:11434

---

## 📦 Model Selection

### Required Models (Always Pulled)
- `llama3.1:8b` (4.7GB) - Default chat model, 128K context
- `nomic-embed-text` (274MB) - Reliable embedding model

### Optional Models (Prompt During Deploy)

**Small Models (Fast, Large Context):**
- `llama3.2:1b` (1GB) - Smallest, 128K context, 100+ tok/s
- `llama3.2:3b` (2GB) - Small, 128K context, 60 tok/s
- `gemma2:2b` (2GB) - Google efficient, high quality

**Medium Models (Production Sweet Spot):**
- `gemma2:9b` (5.5GB) - Google high-performance
- `mistral:7b` (4GB) - Fast alternative, 32K context

**Large Models (Best Quality):**
- `qwen2.5:14b` (9GB) - Best for 16GB GPU

**Embedding Alternatives:**
- `mxbai-embed-large` (335MB) - Best retrieval (may have errors)
- `all-minilm` (23MB) - Tiny, fast, demos

**Total download:** ~26GB if you pull all optional models

---

## 🔧 Common Commands

### Start/Stop

```bash
# Start all services
cd /path/to/rag_lab
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (DELETES ALL DATA)
docker compose down -v
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api-gateway
docker compose logs -f chat-service
docker compose logs -f ollama
```

### Pull Additional Models

```bash
# Interactive script
cd scripts
./pull-ollama-models.sh

# Manual
docker compose exec ollama ollama pull qwen2.5:14b
docker compose exec ollama ollama pull gemma2:9b
```

### Check Service Health

```bash
# All services
docker compose ps

# Ollama models
docker compose exec ollama ollama list

# API Gateway health
curl http://localhost:8000/health
```

---

## 🐛 Troubleshooting

### Frontend Not Loading

```bash
# Check nginx logs
docker compose logs frontend

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend
```

### Ollama Not Responding

```bash
# Check if Ollama is running
docker compose ps ollama

# Check GPU access
docker compose exec ollama nvidia-smi

# Restart Ollama
docker compose restart ollama
```

### Chat Service Errors

```bash
# Check logs
docker compose logs chat-service

# Verify Ollama models
docker compose exec ollama ollama list

# Restart chat service
docker compose restart chat-service
```

### Out of Memory Errors

```bash
# Check GPU memory
docker compose exec ollama nvidia-smi

# Switch to smaller model in UI (Settings tab)
# Or reduce context window in config.env
```

---

## 📚 Next Steps

1. **Upload Documents:** Go to Documents tab, upload PDFs
2. **Build Knowledge Graph:** Select algorithm, click "Rebuild KG"
3. **Chat:** Go to Chat tab, ask questions
4. **Explore Settings:** Try different models, toggle RAG features
5. **View Metrics:** Check Metrics tab for performance data
6. **Try Lab Exercises:** See [docs/lab/](./lab/) for hands-on exercises

---

## 🎓 Lab Exercises

- [Model Size vs Context Window](./lab/EXERCISE_MODEL_VS_CONTEXT.md)
- [Knowledge Graph Algorithms](./lab/EXERCISE_KG_ALGORITHMS.md)
- [RAG Feature Comparison](./lab/EXERCISE_RAG_FEATURES.md)

---

## 📖 Documentation

- [Model Selection Guide](./MODEL_SELECTION_GUIDE.md) - Choose the right model
- [GPU Setup](./deployment/GPU_SETUP.md) - NVIDIA GPU configuration
- [Ubuntu Deployment](./deployment/UBUNTU_DEPLOYMENT.md) - Server deployment
- [Architecture](./ARCHITECTURE.md) - System design
- [Security](./SECURITY_DEEP_DIVE.md) - Enterprise security features

---

## 🆘 Getting Help

1. **Check logs:** `docker compose logs -f [service-name]`
2. **Verify health:** `docker compose ps`
3. **Review docs:** See [docs/](./docs/) directory
4. **GitHub Issues:** Report bugs or ask questions

---

## 🎯 Splunk/Cisco Field Team

This lab is designed for:
- **Hands-on learning:** Compare RAG techniques
- **Customer demos:** Show enterprise AI capabilities
- **POC development:** Rapid prototyping
- **Training:** Understand LLM trade-offs

**Key teaching points:**
- Model size vs speed vs quality
- RAG vs fine-tuning
- Knowledge graphs for discovery
- Security considerations
- Cost/performance optimization

---

**Last Updated:** November 4, 2025  
**Version:** 2.0  
**GPU Target:** 16GB NVIDIA (RTX 4080, A4000, etc.)

