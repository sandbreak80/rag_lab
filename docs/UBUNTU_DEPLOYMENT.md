# Ubuntu Server Deployment Guide
## Deploy Latest RAG Lab to AWS Ubuntu Server

**Date:** November 4, 2025
**Target:** Ubuntu Server with NVIDIA GPU (AWS)
**Branch:** `main`
**Status:** Ready for Deployment

---

## 🎯 Overview

This guide walks you through deploying the latest RAG Lab code to your Ubuntu server running on AWS with NVIDIA GPU support.

### What's New in This Version

**Major Features:**
- ✅ **Learning Hub** - 100+ Q&A entries across 9 categories
- ✅ **Enhanced Metrics** - Detailed per-component timing + Ollama metrics
- ✅ **Model Expansion** - 10 Ollama models (2 required + 8 optional)
- ✅ **GPU Support** - NVIDIA GPU integration for Ollama
- ✅ **Web Sources** - Visual distinction for web search results
- ✅ **Improved Responses** - Enhanced prompts for detailed answers
- ✅ **Better UI/UX** - Preset selection indicators, fixed loading states

**Recent Commits (Last 8):**
1. `a710b74` - chore: Clean up devcontainer and update prompts
2. `6cedaab` - docs: Add session summary for Learning Hub development
3. `f7c20b9` - docs: Add comprehensive project status document
4. `ae6bddc` - docs: Learning Hub completion summary
5. `7fb1db8` - feat: Build Learning Hub UI components (Phase 3 Complete!)
6. `475760d` - docs: Add Q&A data completion summary
7. `a5889ff` - wip: Start Lab & QA redesign - Plan + Q&A data structure
8. `53798ec` - feat: Add detailed per-component timing metrics to waterfall chart

---

## 📋 Pre-Deployment Checklist

### On Your Local Machine

**1. Push Latest Code to GitHub:**
```bash
cd ~/code_projects/rag_lab
git checkout main
git push origin main
```

**2. Verify Commits:**
```bash
git log --oneline -10
# Should show commits up to a710b74
```

**3. Optional: Push Security Branch (for future):**
```bash
git push origin security
```

---

## 🚀 Deployment Steps

### Step 1: Connect to Ubuntu Server

```bash
# SSH into your AWS Ubuntu server
ssh ubuntu@<your-server-ip>

# Or if using key file:
ssh -i /path/to/your-key.pem ubuntu@<your-server-ip>
```

---

### Step 2: Navigate to Project Directory

```bash
cd ~/rag_lab
```

---

### Step 3: Stop Current Services

```bash
# Stop all running containers
docker compose down

# Optional: Clean up old images (saves space)
docker system prune -f
```

---

### Step 4: Pull Latest Code

```bash
# Fetch latest from GitHub
git fetch origin

# Check what's new
git log --oneline HEAD..origin/main

# Pull latest main branch
git pull origin main
```

**Expected Output:**
```
Updating <old-hash>..a710b74
Fast-forward
 frontend/src/components/learning/LearningHubPage.tsx | 245 ++++++++++++++++++
 frontend/src/components/learning/QACard.tsx | 89 +++++++
 frontend/src/components/learning/QADetailModal.tsx | 156 +++++++++++
 frontend/src/data/qaData.ts | 1500+ lines
 docs/PROJECT_STATUS.md | 200 ++++++++++++++
 ... (many more files)
```

---

### Step 5: Verify Configuration

**Check environment variables:**
```bash
cat config.env
```

**Should show:**
```bash
# Core Models
CHAT_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text

# Context & Generation
DEFAULT_CONTEXT_WINDOW=32768
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_K=5

# Search Configuration
DEFAULT_SEARCH_TYPE=hybrid
DEFAULT_TOP_N=5
DEFAULT_BM25_K1=1.5
DEFAULT_BM25_B=0.75

# Services
OLLAMA_BASE_URL=http://ollama:11434
```

**Verify GPU support is enabled:**
```bash
grep -A 10 "ollama:" docker-compose.yml | grep -A 5 "deploy:"
```

**Should show:**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

---

### Step 6: Build Fresh Images

```bash
# Build with no cache to ensure latest code
docker compose build --no-cache

# This will take 5-10 minutes
```

---

### Step 7: Start Services

```bash
# Start all services
docker compose up -d

# Watch logs
docker compose logs -f
```

**Wait for all services to be healthy (2-3 minutes):**
- ✅ `rag-ollama` - Ollama service
- ✅ `rag-chromadb` - Vector database
- ✅ `rag-frontend` - React UI
- ✅ `rag-api-gateway` - API Gateway
- ✅ All microservices (chat, search, ingest, etc.)

---

### Step 8: Pull Required Ollama Models

```bash
# Pull required models (this will take 5-10 minutes)
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

**Verify models:**
```bash
docker compose exec ollama ollama list
```

**Expected Output:**
```
NAME                    ID              SIZE    MODIFIED
llama3.1:8b            <hash>          4.7 GB  X seconds ago
nomic-embed-text       <hash>          274 MB  X seconds ago
```

---

### Step 9: Optional - Pull Additional Models

**For lab exercises, pull optional models:**
```bash
# Small models (fast inference)
docker compose exec ollama ollama pull llama3.2:1b
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull gemma2:2b

# Medium models (balanced)
docker compose exec ollama ollama pull gemma2:9b
docker compose exec ollama ollama pull mistral:7b

# Large models (high quality)
docker compose exec ollama ollama pull qwen2.5:14b

# Alternative embedding models
docker compose exec ollama ollama pull mxbai-embed-large
docker compose exec ollama ollama pull all-minilm
```

**Note:** Each model takes 2-10 minutes to download depending on size.

---

### Step 10: Verify Deployment

**1. Check all containers are running:**
```bash
docker compose ps
```

**Expected Output:**
```
NAME                    STATUS              PORTS
rag-ollama             Up (healthy)        0.0.0.0:11434->11434/tcp
rag-chromadb           Up (healthy)        0.0.0.0:8001->8000/tcp
rag-frontend           Up                  0.0.0.0:3000->80/tcp
rag-api-gateway        Up (healthy)        0.0.0.0:8000->8000/tcp
rag-chat-service       Up (healthy)        0.0.0.0:8003->8003/tcp
... (all other services)
```

**2. Check GPU is being used:**
```bash
nvidia-smi
```

**Should show Ollama process using GPU memory.**

**3. Test API Gateway:**
```bash
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy"}`

**4. Test Ollama:**
```bash
curl http://localhost:11434/api/tags
```

**Should list all pulled models.**

---

### Step 11: Access the Application

**Open in browser:**
```
http://<your-server-ip>:3000
```

**Test the new features:**
1. ✅ **Learning Hub** - Navigate to "Learning Hub" tab
   - Search for topics
   - Filter by category and difficulty
   - Click on Q&A cards to see details

2. ✅ **Enhanced Metrics** - Go to Chat tab
   - Ask a question
   - Check the waterfall chart
   - Verify you see detailed timing metrics

3. ✅ **Web Sources** - In Chat tab
   - Enable "Web Search" in settings
   - Ask a question
   - Verify web sources show with globe icon

4. ✅ **Model Selection** - In Settings
   - Change chat model
   - Verify new models are available

---

## 🔧 Troubleshooting

### Issue: Frontend Not Loading

**Symptoms:** Browser shows "Cannot connect" or blank page

**Solution:**
```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

---

### Issue: Models Not Loading

**Symptoms:** "Failed to load models" in UI

**Solution:**
```bash
# Check Ollama is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Verify models are pulled
docker compose exec ollama ollama list

# If empty, pull models again
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

---

### Issue: GPU Not Being Used

**Symptoms:** Slow inference, nvidia-smi shows no GPU usage

**Solution:**
```bash
# Check GPU support is enabled in docker-compose.yml
grep -A 10 "ollama:" docker-compose.yml | grep -A 5 "deploy:"

# Restart Ollama
docker compose restart ollama

# Check nvidia-container-toolkit is installed
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

### Issue: Services Failing to Start

**Symptoms:** Some containers show "Exited" status

**Solution:**
```bash
# Check which service is failing
docker compose ps

# Check logs for that service
docker compose logs <service-name>

# Common fixes:
# 1. Port already in use
sudo lsof -i :<port-number>

# 2. Out of memory
free -h

# 3. Missing dependencies
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

---

### Issue: Web Search Not Working

**Symptoms:** Web search toggle enabled but no web results

**Solution:**
```bash
# Check web-search service is running
docker compose ps web-search

# Check logs
docker compose logs web-search

# Restart service
docker compose restart web-search
```

---

## 📊 Post-Deployment Verification

### Run Health Checks

```bash
# Check all service health
curl http://localhost:8000/health

# Check individual services
curl http://localhost:8003/health  # chat-service
curl http://localhost:8005/health  # vector-db
curl http://localhost:8007/health  # knowledge-graph
curl http://localhost:8009/health  # reranker
curl http://localhost:8011/health  # web-search
```

---

### Test Core Functionality

**1. Document Upload:**
```bash
# Upload a test document
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/test.pdf"
```

**2. Chat Query:**
```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "config": {
      "use_vector_search": true,
      "use_bm25": true,
      "use_reranking": true
    }
  }'
```

**3. Model List:**
```bash
# Get available models
curl http://localhost:8000/api/models
```

---

### Monitor Performance

**1. Check container resource usage:**
```bash
docker stats
```

**2. Check GPU usage:**
```bash
watch -n 1 nvidia-smi
```

**3. Check disk usage:**
```bash
df -h
docker system df
```

---

## 🔄 Rollback Procedure (If Needed)

If something goes wrong, you can rollback to the previous version:

```bash
# Stop current services
docker compose down

# Check previous commits
git log --oneline -20

# Rollback to previous commit (replace <commit-hash>)
git reset --hard <previous-commit-hash>

# Rebuild and restart
docker compose build --no-cache
docker compose up -d

# Pull models again if needed
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

---

## 📈 Performance Benchmarks

### Expected Performance (with GPU)

**LLM Inference (llama3.1:8b):**
- Tokens per second: 40-60 tok/s (with GPU)
- Response latency: 2-5 seconds (typical query)

**Embedding (nomic-embed-text):**
- Embedding latency: 50-100ms per document
- Batch processing: 10-20 docs/second

**RAG Pipeline:**
- Total latency: 2-10 seconds
- Vector search: 50-200ms
- BM25 search: 20-100ms
- Reranking: 100-500ms
- Knowledge graph: 50-200ms
- Web search: 1-3 seconds (if enabled)

---

## 🎯 Success Criteria

**Deployment is successful when:**
- ✅ All containers are running and healthy
- ✅ Frontend loads at http://<server-ip>:3000
- ✅ Learning Hub shows 100+ Q&A entries
- ✅ Chat works with detailed responses
- ✅ Waterfall chart shows detailed metrics
- ✅ Web search returns results (when enabled)
- ✅ GPU is being utilized (nvidia-smi shows usage)
- ✅ Models load in UI settings

---

## 📝 Deployment Log Template

Keep a log of your deployment:

```
DEPLOYMENT LOG
==============
Date: November 4, 2025
Server: <your-server-ip>
Branch: main
Commit: a710b74

Pre-Deployment:
- [ ] Code pushed to GitHub
- [ ] SSH access verified
- [ ] Backup taken (if needed)

Deployment Steps:
- [ ] Connected to server
- [ ] Stopped old services
- [ ] Pulled latest code
- [ ] Built new images
- [ ] Started services
- [ ] Pulled Ollama models
- [ ] Verified all services healthy

Post-Deployment:
- [ ] Frontend accessible
- [ ] Learning Hub working
- [ ] Chat working
- [ ] Metrics working
- [ ] GPU being used
- [ ] All health checks passing

Issues Encountered:
- None / <describe issues and solutions>

Performance Notes:
- LLM tok/s: <value>
- Average response time: <value>
- GPU utilization: <value>

Deployment Status: SUCCESS / FAILED
Deployed By: <your-name>
```

---

## 🔐 Security Notes

**For Production Deployment:**
1. ⚠️ **No authentication** - Currently no API authentication
2. ⚠️ **No rate limiting** - Anyone can make unlimited requests
3. ⚠️ **No HTTPS** - Traffic is not encrypted
4. ⚠️ **No PII protection** - No PII detection/redaction

**Recommendations:**
- Use AWS security groups to restrict access
- Set up NGINX reverse proxy with SSL
- Implement rate limiting at load balancer
- For production use, implement security features from `security` branch

---

## 📚 Additional Resources

**Documentation:**
- [Quick Start Guide](./QUICK_START.md)
- [Model Selection Guide](./MODEL_SELECTION_GUIDE.md)
- [GPU Setup Guide](./deployment/GPU_SETUP.md)
- [Project Status](./PROJECT_STATUS.md)

**Scripts:**
- `scripts/clean-deploy.sh` - Fresh deployment script
- `scripts/pull-ollama-models.sh` - Pull all models
- `scripts/health-check.sh` - Verify all services

**Monitoring:**
- Metrics endpoint: http://localhost:8000/api/metrics
- Prometheus: (not yet configured)
- Grafana: (not yet configured)

---

## 🎉 Next Steps After Deployment

1. **Test all features** - Go through Learning Hub, Chat, Settings
2. **Upload documents** - Add your own documents for RAG
3. **Try different models** - Compare llama3.1:8b vs llama3.2:3b
4. **Monitor performance** - Watch GPU usage and response times
5. **Provide feedback** - Note any issues or improvements
6. **Plan security implementation** - Review `security` branch for next phase

---

**Deployment Guide Version:** 1.0
**Last Updated:** November 4, 2025
**Status:** Ready for Use

**Good luck with your deployment!** 🚀

