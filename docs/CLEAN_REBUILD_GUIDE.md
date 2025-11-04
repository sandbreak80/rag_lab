# Clean Rebuild Guide - Ubuntu Server
## Complete From-Scratch Deployment & Validation

**Date:** November 4, 2025  
**Purpose:** Rebuild entire RAG Lab from scratch on Ubuntu server  
**Target:** AWS Ubuntu Server with NVIDIA GPU  
**Status:** Ready for Clean Deployment

---

## 🎯 Overview

This guide walks you through a **complete from-scratch rebuild** of the RAG Lab on your Ubuntu server, including:
- ✅ Stopping and removing all existing containers
- ✅ Cleaning Docker system (images, volumes, cache)
- ✅ Fresh code pull from GitHub
- ✅ Clean build with no cache
- ✅ Fresh Ollama model downloads
- ✅ End-to-end validation

**Use this when:**
- Starting fresh deployment
- Troubleshooting persistent issues
- Validating a new release
- Ensuring clean state

**Time Required:** 20-30 minutes

---

## 📋 Pre-Rebuild Checklist

### On Your Local Machine

**1. Ensure latest code is pushed to GitHub:**
```bash
cd ~/code_projects/rag_lab
git checkout main
git status  # Should show "nothing to commit, working tree clean"
git push origin main
```

**2. Verify commit hash:**
```bash
git log --oneline -1
# Should show: ccbe626 docs: Add comprehensive Ubuntu server deployment guide
```

---

## 🚀 Clean Rebuild Steps

### Step 1: Connect to Ubuntu Server

```bash
ssh ubuntu@<your-aws-server-ip>

# Or with key file:
ssh -i /path/to/your-key.pem ubuntu@<your-aws-server-ip>
```

---

### Step 2: Navigate to Project Directory

```bash
cd ~/rag_lab
pwd  # Should show: /home/ubuntu/rag_lab
```

---

### Step 3: Complete Docker Cleanup

**Stop all containers:**
```bash
docker compose down
```

**Remove all RAG Lab containers (if any stuck):**
```bash
docker ps -a | grep rag- | awk '{print $1}' | xargs -r docker rm -f
```

**Remove all RAG Lab images:**
```bash
docker images | grep rag- | awk '{print $3}' | xargs -r docker rmi -f
```

**Clean Docker system:**
```bash
# Remove unused images, containers, networks
docker system prune -af

# Optional: Remove volumes (WARNING: deletes all data!)
# Only do this if you want to start completely fresh
read -p "Remove all volumes? This deletes uploaded documents! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker volume prune -f
    echo "✅ Volumes removed"
else
    echo "⏭️  Keeping volumes"
fi
```

**Verify cleanup:**
```bash
docker ps -a  # Should show no rag- containers
docker images | grep rag-  # Should show no rag- images
docker volume ls  # Check volumes
```

---

### Step 4: Clean Code Pull

**Save any local changes (if needed):**
```bash
# Check for uncommitted changes
git status

# If you have local changes you want to keep:
git stash

# Or discard all local changes:
git reset --hard HEAD
git clean -fd
```

**Fetch and pull latest code:**
```bash
# Fetch latest from GitHub
git fetch origin

# Show what's new
echo "=== New commits ==="
git log --oneline HEAD..origin/main

# Pull latest main branch
git pull origin main

# Verify current commit
git log --oneline -1
# Should show: ccbe626 docs: Add comprehensive Ubuntu server deployment guide
```

---

### Step 5: Verify Configuration Files

**Check docker-compose.yml:**
```bash
ls -lh docker-compose.yml
# Should show recent modification date
```

**Check config.env:**
```bash
cat config.env | grep -E "CHAT_MODEL|EMBEDDING_MODEL|OLLAMA_BASE_URL"
```

**Expected output:**
```
CHAT_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://ollama:11434
```

**Verify GPU support in docker-compose.yml:**
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

### Step 6: Clean Build (No Cache)

**Build all services from scratch:**
```bash
echo "🔨 Building all services from scratch (this takes 5-10 minutes)..."
docker compose build --no-cache --progress=plain

# If you want to see detailed output:
# docker compose build --no-cache --progress=plain 2>&1 | tee build.log
```

**Expected output:**
```
[+] Building 300.5s (150/150) FINISHED
 => [rag-frontend internal] load build definition
 => [rag-api-gateway internal] load build definition
 => [rag-chat-service internal] load build definition
 ... (many more lines)
✅ Build complete
```

**Verify images were created:**
```bash
docker images | grep rag-
```

**Should show fresh images with "seconds ago" or "minutes ago":**
```
REPOSITORY          TAG       IMAGE ID       CREATED          SIZE
rag-frontend        latest    <hash>         2 minutes ago    200MB
rag-api-gateway     latest    <hash>         3 minutes ago    150MB
... (all services)
```

---

### Step 7: Start All Services

**Start services in detached mode:**
```bash
echo "🚀 Starting all services..."
docker compose up -d
```

**Watch logs to see services starting:**
```bash
docker compose logs -f
# Press Ctrl+C to stop watching (services keep running)
```

**Wait for services to be healthy (2-3 minutes):**
```bash
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service status
docker compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
rag-ollama             Up (healthy)        0.0.0.0:11434->11434/tcp
rag-chromadb           Up (healthy)        0.0.0.0:8001->8000/tcp
rag-frontend           Up                  0.0.0.0:3000->80/tcp
rag-api-gateway        Up (healthy)        0.0.0.0:8000->8000/tcp
rag-chat-service       Up (healthy)        0.0.0.0:8003->8003/tcp
rag-ingest-service     Up (healthy)        0.0.0.0:8004->8004/tcp
rag-vector-db          Up (healthy)        0.0.0.0:8005->8005/tcp
rag-docling-service    Up (healthy)        0.0.0.0:8006->8006/tcp
rag-knowledge-graph    Up (healthy)        0.0.0.0:8007->8007/tcp
rag-metrics-store      Up (healthy)        0.0.0.0:8008->8008/tcp
rag-reranker           Up (healthy)        0.0.0.0:8009->8009/tcp
rag-search-service     Up (healthy)        0.0.0.0:8010->8010/tcp
rag-web-search         Up (healthy)        0.0.0.0:8011->8011/tcp
```

**If any service is not healthy:**
```bash
# Check logs for that service
docker compose logs <service-name>

# Restart if needed
docker compose restart <service-name>
```

---

### Step 8: Pull Required Ollama Models

**Pull the two required models:**
```bash
echo "📦 Pulling required Ollama models (this takes 5-10 minutes)..."

# Pull chat model (llama3.1:8b - ~4.7GB)
echo "Pulling llama3.1:8b..."
docker compose exec ollama ollama pull llama3.1:8b

# Pull embedding model (nomic-embed-text - ~274MB)
echo "Pulling nomic-embed-text..."
docker compose exec ollama ollama pull nomic-embed-text

echo "✅ Required models downloaded"
```

**Verify models are available:**
```bash
docker compose exec ollama ollama list
```

**Expected output:**
```
NAME                    ID              SIZE    MODIFIED
llama3.1:8b            <hash>          4.7 GB  X seconds ago
nomic-embed-text       <hash>          274 MB  X seconds ago
```

---

### Step 9: Optional - Pull Additional Models

**For lab exercises, pull optional models:**
```bash
echo "📦 Optional Models for Lab Exercises"
echo "These are useful for comparing model performance:"
echo "  - llama3.2:1b (tiny, fast)"
echo "  - llama3.2:3b (small, balanced)"
echo "  - gemma2:2b (small, Google)"
echo "  - gemma2:9b (medium, high quality)"
echo "  - mistral:7b (medium, popular)"
echo "  - qwen2.5:14b (large, high quality)"
echo "  - mxbai-embed-large (alternative embedding)"
echo "  - all-minilm (lightweight embedding)"
echo ""
read -p "Pull optional models? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pulling optional models (this takes 10-20 minutes)..."
    
    # Small models (fast)
    docker compose exec ollama ollama pull llama3.2:1b
    docker compose exec ollama ollama pull llama3.2:3b
    docker compose exec ollama ollama pull gemma2:2b
    
    # Medium models
    docker compose exec ollama ollama pull gemma2:9b
    docker compose exec ollama ollama pull mistral:7b
    
    # Large models
    docker compose exec ollama ollama pull qwen2.5:14b
    
    # Alternative embeddings
    docker compose exec ollama ollama pull mxbai-embed-large
    docker compose exec ollama ollama pull all-minilm
    
    echo "✅ Optional models downloaded"
else
    echo "⏭️  Skipping optional models (you can pull them later)"
fi
```

---

## ✅ End-to-End Validation

### Validation 1: Service Health Checks

**Check all services are healthy:**
```bash
echo "=== Service Health Checks ==="

# API Gateway
curl -s http://localhost:8000/health | jq '.'

# Chat Service
curl -s http://localhost:8003/health | jq '.'

# Vector DB
curl -s http://localhost:8005/health | jq '.'

# Knowledge Graph
curl -s http://localhost:8007/health | jq '.'

# Reranker
curl -s http://localhost:8009/health | jq '.'

# Web Search
curl -s http://localhost:8011/health | jq '.'

echo "✅ All health checks passed"
```

**Expected:** Each should return `{"status": "healthy"}` or similar

---

### Validation 2: Ollama Service

**Check Ollama is running:**
```bash
echo "=== Ollama Validation ==="

# List models
curl -s http://localhost:11434/api/tags | jq '.models[] | {name: .name, size: .size}'

# Test generation
curl -s http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Say hello in one word",
  "stream": false
}' | jq '.response'

echo "✅ Ollama working"
```

---

### Validation 3: GPU Utilization

**Check GPU is being used:**
```bash
echo "=== GPU Validation ==="

# Check nvidia-smi
nvidia-smi

# Should show:
# - Ollama process using GPU
# - GPU memory allocated
# - GPU utilization when running queries

echo "✅ GPU detected and available"
```

---

### Validation 4: Frontend Access

**Check frontend is accessible:**
```bash
echo "=== Frontend Validation ==="

# Check frontend is serving
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Should return: 200

echo "✅ Frontend accessible at http://localhost:3000"
```

**Open in browser:**
```
http://<your-server-ip>:3000
```

**Verify you see:**
- ✅ RAG Lab interface loads
- ✅ Navigation tabs: Chat, Learning Hub, Lab, Settings, Metrics, Prompt Logs
- ✅ No console errors (F12 → Console)

---

### Validation 5: Model Selection

**In the UI, go to Settings:**
1. Click "Settings" tab
2. Scroll to "Chat Model"
3. Verify dropdown shows:
   - ✅ llama3.1:8b (selected)
   - ✅ nomic-embed-text (in embedding models)
   - ✅ Any optional models you pulled

---

### Validation 6: Learning Hub

**Test the new Learning Hub:**
1. Click "Learning Hub" tab
2. Verify you see:
   - ✅ Search bar at top
   - ✅ Category filters (All, RAG Fundamentals, Vector Search, etc.)
   - ✅ Difficulty filters (All, Beginner, Intermediate, Advanced)
   - ✅ Q&A cards displayed (should show 100+ total)
3. Test search:
   - Type "vector" in search
   - Verify results filter
4. Test filters:
   - Click "RAG Fundamentals" category
   - Click "Beginner" difficulty
   - Verify results update
5. Test Q&A card:
   - Click on any card
   - Verify modal opens with full details
   - Check for: question, answer, code examples, related questions

**Expected:** All features work smoothly

---

### Validation 7: Chat Functionality

**Test basic chat:**
1. Go to "Chat" tab
2. Type: "What is RAG?"
3. Click "Send" or press Enter
4. Verify:
   - ✅ Loading indicator appears
   - ✅ Response appears (detailed answer)
   - ✅ Sources shown below answer
   - ✅ Metrics displayed (timing, tokens, etc.)

---

### Validation 8: Enhanced Metrics

**Test detailed metrics:**
1. In Chat tab, after getting a response
2. Scroll down to metrics section
3. Verify waterfall chart shows:
   - ✅ Query Expansion
   - ✅ Vector Search
   - ✅ BM25 Search
   - ✅ Fusion
   - ✅ Knowledge Graph (if enabled)
   - ✅ Reranking (if enabled)
   - ✅ Web Search (if enabled)
   - ✅ LLM: Prompt Eval
   - ✅ LLM: Token Generation
   - ✅ Search Service
   - ✅ Chat Service Overhead
4. Verify metrics show:
   - ✅ Tokens generated
   - ✅ Tokens per second
   - ✅ Total latency

---

### Validation 9: RAG Configuration

**Test RAG toggles:**
1. In Chat tab, expand "RAG Configuration"
2. Test each toggle:
   - ✅ Query Expansion
   - ✅ Vector Search
   - ✅ BM25 Search
   - ✅ Hybrid Search (Fusion)
   - ✅ Knowledge Graph Enhancement
   - ✅ LLM Re-ranking
   - ✅ Web Search
3. For each toggle:
   - Turn it OFF
   - Ask a question
   - Verify that component is NOT in metrics
   - Turn it back ON
   - Ask another question
   - Verify component IS in metrics

---

### Validation 10: Web Search

**Test web search functionality:**
1. In Chat, enable "Web Search" toggle
2. Ask: "What's the latest news about AI?"
3. Verify:
   - ✅ Response includes web information
   - ✅ Sources section shows web sources with:
     - Globe icon (🌐)
     - Blue color
     - Clickable URLs
     - Search engine name (e.g., "google")
4. Click on a web source URL
5. Verify it opens in new tab

---

### Validation 11: Document Upload

**Test document ingestion:**
```bash
# Create a test document
cat > /tmp/test_rag.txt << 'EOF'
# RAG Test Document

This is a test document for validating the RAG system.

RAG stands for Retrieval Augmented Generation.
It combines document retrieval with language model generation.

Key components:
1. Vector database for semantic search
2. BM25 for keyword search
3. Knowledge graph for relationships
4. LLM for answer generation
EOF

# Upload via API
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/tmp/test_rag.txt" \
  -F "tags=test,validation"

# Should return: {"status": "success", "message": "File uploaded successfully"}
```

**In UI:**
1. Go to Chat tab
2. Ask: "What does the test document say about RAG?"
3. Verify:
   - ✅ Response references the test document
   - ✅ Sources include "test_rag.txt"
   - ✅ Answer contains information from the document

---

### Validation 12: Configuration Presets

**Test quick presets:**
1. In Chat tab, scroll to "Quick Presets"
2. Click "Speed Optimized"
3. Verify:
   - ✅ Banner shows "Currently Active: Speed Optimized"
   - ✅ Card has ring border and checkmark
4. Click "Quality Optimized"
5. Verify:
   - ✅ Banner updates to "Quality Optimized"
   - ✅ Different card now highlighted
6. Ask a question
7. Verify preset settings are applied

---

### Validation 13: Prompt Logs

**Test prompt logging:**
1. Go to "Prompt Logs" tab
2. Verify you see:
   - ✅ Table with recent queries
   - ✅ Columns: Timestamp, Query, Model, Tokens, Latency, Config
3. Click "View Details" on a log entry
4. Verify modal shows:
   - ✅ Full query
   - ✅ Full response
   - ✅ All metrics
   - ✅ Configuration used
5. Test "Export to Splunk Format" button
6. Verify JSON is copied to clipboard

---

### Validation 14: Performance Benchmarks

**Run performance test:**
```bash
echo "=== Performance Benchmark ==="

# Test 5 queries and measure latency
for i in {1..5}; do
  echo "Query $i..."
  START=$(date +%s.%N)
  
  curl -s -X POST http://localhost:8000/api/ask \
    -H "Content-Type: application/json" \
    -d '{
      "query": "What is RAG?",
      "config": {
        "use_vector_search": true,
        "use_bm25": true,
        "use_reranking": true
      }
    }' > /dev/null
  
  END=$(date +%s.%N)
  LATENCY=$(echo "$END - $START" | bc)
  echo "  Latency: ${LATENCY}s"
done

echo "✅ Performance test complete"
```

**Expected latency (with GPU):**
- First query: 3-5 seconds (cold start)
- Subsequent queries: 2-4 seconds

---

### Validation 15: GPU Performance

**Monitor GPU during query:**
```bash
# In one terminal, watch GPU usage
watch -n 1 nvidia-smi

# In another terminal (or UI), send a query
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain RAG in detail with examples",
    "config": {"use_vector_search": true}
  }'
```

**Expected GPU behavior:**
- ✅ GPU memory increases during LLM generation
- ✅ GPU utilization spikes to 80-100%
- ✅ Tokens/second: 40-60 (with GPU) vs 5-10 (CPU only)

---

## 📊 Validation Checklist

**Copy this checklist and mark off as you validate:**

```
CLEAN REBUILD VALIDATION CHECKLIST
===================================

Pre-Rebuild:
- [ ] Latest code pushed to GitHub
- [ ] SSH access to Ubuntu server verified

Docker Cleanup:
- [ ] All containers stopped
- [ ] All RAG images removed
- [ ] Docker system pruned
- [ ] Volumes handled (kept or removed)

Code & Build:
- [ ] Latest code pulled from GitHub
- [ ] Commit hash verified (ccbe626)
- [ ] Configuration files verified
- [ ] GPU support enabled in docker-compose.yml
- [ ] Clean build completed (no cache)
- [ ] All images created successfully

Services:
- [ ] All services started
- [ ] All services healthy
- [ ] Ollama models pulled (required)
- [ ] Optional models pulled (if desired)

Validation Tests:
- [ ] 1. Service health checks (all pass)
- [ ] 2. Ollama service (working)
- [ ] 3. GPU utilization (detected and used)
- [ ] 4. Frontend access (loads correctly)
- [ ] 5. Model selection (models available)
- [ ] 6. Learning Hub (100+ Q&A, search, filters)
- [ ] 7. Chat functionality (responses work)
- [ ] 8. Enhanced metrics (detailed waterfall)
- [ ] 9. RAG configuration (all toggles work)
- [ ] 10. Web search (results with globe icons)
- [ ] 11. Document upload (ingestion works)
- [ ] 12. Configuration presets (apply correctly)
- [ ] 13. Prompt logs (logging and export)
- [ ] 14. Performance benchmarks (2-5s latency)
- [ ] 15. GPU performance (40-60 tok/s)

Final Status:
- [ ] All validations passed
- [ ] No errors in logs
- [ ] System ready for use

Deployment Status: SUCCESS / FAILED
Deployed By: _______________
Date: _______________
Time Taken: _______________
```

---

## 🎯 Success Criteria

**Deployment is successful when:**
- ✅ All 13 services running and healthy
- ✅ Frontend loads without errors
- ✅ Learning Hub shows 100+ Q&A entries
- ✅ Chat returns detailed responses
- ✅ Metrics show detailed timing breakdown
- ✅ Web search returns results with visual distinction
- ✅ GPU is utilized (40-60 tok/s)
- ✅ All 15 validation tests pass
- ✅ No errors in any service logs

---

## 🆘 Troubleshooting

### Issue: Service Won't Start

**Symptoms:** Container shows "Exited" status

**Debug:**
```bash
# Check logs
docker compose logs <service-name>

# Check if port is in use
sudo lsof -i :<port-number>

# Restart service
docker compose restart <service-name>

# If still failing, rebuild just that service
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

---

### Issue: Models Not Pulling

**Symptoms:** "Failed to pull model" error

**Debug:**
```bash
# Check Ollama is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Try pulling manually
docker compose exec ollama ollama pull llama3.1:8b

# If network issue, check connectivity
docker compose exec ollama curl -I https://ollama.ai
```

---

### Issue: GPU Not Detected

**Symptoms:** nvidia-smi shows no processes, slow inference

**Debug:**
```bash
# Check nvidia-container-toolkit
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, reinstall toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Restart Ollama
docker compose restart ollama
```

---

### Issue: Frontend Shows Blank Page

**Symptoms:** Browser shows white screen or "Cannot GET /"

**Debug:**
```bash
# Check frontend logs
docker compose logs frontend

# Check Nginx config
docker compose exec frontend cat /etc/nginx/conf.d/default.conf

# Rebuild frontend
docker compose build --no-cache frontend
docker compose up -d frontend

# Check browser console (F12)
# Look for API connection errors
```

---

### Issue: Slow Performance

**Symptoms:** Responses take > 10 seconds

**Debug:**
```bash
# Check if GPU is being used
nvidia-smi

# Check system resources
docker stats

# Check disk space
df -h

# Check if models are loaded
docker compose exec ollama ollama list

# Monitor during query
docker compose logs -f chat-service
```

---

## 📝 Post-Validation Notes

**Record your findings:**

```
DEPLOYMENT NOTES
================

Deployment Date: _______________
Server: _______________
Commit: ccbe626

Build Time: _______________ minutes
Model Download Time: _______________ minutes
Total Time: _______________ minutes

Performance Metrics:
- LLM Tokens/Second: _______________
- Average Response Time: _______________
- GPU Utilization: _______________%
- Memory Usage: _______________

Issues Encountered:
- _______________
- _______________

Resolution:
- _______________
- _______________

Final Status: ✅ SUCCESS / ❌ FAILED

Notes:
_______________________________________________
_______________________________________________
_______________________________________________
```

---

## 🎉 Next Steps After Validation

1. **✅ System is validated and ready for use**
2. **Upload your documents** for RAG testing
3. **Try different models** to compare performance
4. **Test with real queries** from your use case
5. **Monitor GPU usage** over time
6. **Collect user feedback** on new features
7. **Plan next enhancements** (security branch?)

---

## 📚 Additional Resources

**Documentation:**
- [Ubuntu Deployment Guide](./UBUNTU_DEPLOYMENT.md)
- [Quick Start Guide](./QUICK_START.md)
- [Model Selection Guide](./MODEL_SELECTION_GUIDE.md)
- [GPU Setup Guide](./deployment/GPU_SETUP.md)

**Scripts:**
- `scripts/clean-deploy.sh` - Automated clean deployment
- `scripts/pull-ollama-models.sh` - Pull all models
- `scripts/health-check.sh` - Verify all services

---

**Clean Rebuild Guide Version:** 1.0  
**Last Updated:** November 4, 2025  
**Status:** Ready for Use

**Good luck with your clean rebuild!** 🚀

