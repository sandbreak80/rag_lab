# 🚀 Deployment Quick Start

## For Ubuntu Server Clean Rebuild

### Option 1: Automated Script (Recommended)

```bash
# SSH to Ubuntu server
ssh ubuntu@<your-server-ip>

# Navigate to project
cd ~/rag_lab

# Pull latest code
git pull origin main

# Run automated clean rebuild
./scripts/clean-rebuild.sh

# Follow prompts:
# - Remove volumes? (y/N) - Choose based on if you want to keep data
# - Pull optional models? (y/N) - Choose y for full lab experience

# Wait 20-30 minutes for completion
```

**What it does:**
- ✅ Stops all containers
- ✅ Removes all RAG images
- ✅ Cleans Docker system
- ✅ Pulls latest code
- ✅ Builds from scratch (no cache)
- ✅ Starts all services
- ✅ Pulls required models
- ✅ Runs validation tests
- ✅ Shows summary

---

### Option 2: Manual Step-by-Step

```bash
# 1. Connect
ssh ubuntu@<your-server-ip>
cd ~/rag_lab

# 2. Clean up
docker compose down
docker system prune -af
# Optional: docker volume prune -f

# 3. Pull code
git pull origin main

# 4. Build
docker compose build --no-cache

# 5. Start
docker compose up -d

# 6. Pull models
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text

# 7. Verify
docker compose ps
curl http://localhost:8000/health
nvidia-smi
```

---

### Quick Validation

```bash
# Check all services
docker compose ps

# Check GPU
nvidia-smi

# Test API
curl http://localhost:8000/health

# Test Ollama
curl http://localhost:11434/api/tags

# Access UI
http://<your-server-ip>:3000
```

---

### What's New in This Deployment

- ✅ **Learning Hub** - 100+ Q&A entries
- ✅ **Enhanced Metrics** - Detailed timing breakdown
- ✅ **Model Expansion** - 10 models available
- ✅ **GPU Support** - NVIDIA acceleration
- ✅ **Web Sources** - Visual distinction
- ✅ **Better Responses** - Enhanced prompts

---

### Troubleshooting

**Service won't start:**
```bash
docker compose logs <service-name>
docker compose restart <service-name>
```

**Models not loading:**
```bash
docker compose exec ollama ollama list
docker compose exec ollama ollama pull llama3.1:8b
```

**GPU not detected:**
```bash
nvidia-smi
docker compose restart ollama
```

**Frontend blank:**
```bash
docker compose logs frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

---

### Full Documentation

- **Clean Rebuild Guide:** `docs/CLEAN_REBUILD_GUIDE.md` (1000+ lines)
- **Ubuntu Deployment:** `docs/UBUNTU_DEPLOYMENT.md`
- **Quick Start:** `docs/QUICK_START.md`

---

### Support

**Check logs:**
```bash
docker compose logs -f
docker compose logs <service-name>
```

**Rollback if needed:**
```bash
git log --oneline -10  # Find previous commit
git reset --hard <commit-hash>
docker compose build --no-cache
docker compose up -d
```

---

**Commit to deploy:** `2754f55`
**Time required:** 20-30 minutes
**Status:** ✅ Ready for deployment

