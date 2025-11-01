# 🚀 Quick Start Guide - Educational RAG Lab

Get up and running in **5 minutes**!

---

## Prerequisites

- Docker and Docker Compose installed
- Ollama running locally (port 11434)
- 8GB+ RAM available
- 10GB+ disk space

---

## Step 1: Clone Repository

```bash
git clone https://github.com/sandbreak80/rag_lab.git
cd rag_lab
```

---

## Step 2: Start All Services

```bash
docker-compose -f docker-compose.test.yml up -d
```

This starts 10 microservices:
- Web UI (5555)
- Search Service (8002)
- Vector DB (8005)
- Embedding Service (8006)
- Ingest Service (8001)
- Knowledge Graph (8007)
- Reranker (8008)
- Web Search (8009)
- SearXNG (8080)
- Ollama (external, 11434)

---

## Step 3: Wait for Initialization

```bash
# Wait 30 seconds for all services to start
sleep 30

# Check service health
curl http://localhost:5555/api/stats
```

You should see JSON with statistics.

---

## Step 4: Open the UI

```bash
open http://localhost:5555
```

Or visit: http://localhost:5555 in your browser

---

## Step 5: Follow the Lab Guide

1. Click the **📖 button** (bottom-right) to open the Lab Guide
2. Click the **⚙️ button** (bottom-left) to open Settings
3. Try the **"Balanced"** preset (recommended)
4. Ask a question in the chat input
5. Observe the **Metrics Dashboard** appear at the top

---

## 🎓 Learning Path

### For Students (3-4 hours)

1. **Interactive Lab Guide** (in UI, 📖 button)
   - 6 progressive sections
   - Hands-on activities
   - Checkpoint tracking

2. **Student Exercises** ([STUDENT_EXERCISES.md](docs/lab/STUDENT_EXERCISES.md))
   - 10 comprehensive exercises
   - Grading rubric (100 + 10 points)
   - Fill-in-the-blank questions

3. **Comprehensive Documentation** ([COMPREHENSIVE_DOCUMENTATION.md](docs/COMPREHENSIVE_DOCUMENTATION.md))
   - Complete technical reference
   - API documentation
   - Architecture details

---

## 🎯 Key Features to Try

### 1. Settings Panel (⚙️)
- **6 Presets**: Minimal → Production
- **6 Toggles**: Query Expansion, BM25, Hybrid, Graph, Reranker, Web Search
- **4 LLM Settings**: Model, Temperature, Max Tokens, Context Window

### 2. Metrics Dashboard (top)
- Real-time performance tracking
- Component-level latency breakdown
- Expandable detailed view

### 3. Comparison Mode (⚖️)
- Side-by-side config comparison
- Automatic winner determination
- Intelligent insights

### 4. Lab Guide (📖)
- 6 interactive sections
- Progress tracking
- Learning checkpoints

---

## 📊 Configuration Presets

| Preset | Latency | Quality | Use Case |
|--------|---------|---------|----------|
| Minimal | 40ms | 65% | Baseline |
| Fast | 60ms | 70% | High QPS |
| **Balanced** ⭐ | **120ms** | **87%** | **Recommended** |
| Quality | 250ms | 92% | Research |
| Maximum | 2500ms | 96% | Best quality |
| **Production** 🏆 | **300ms** | **94%** | **Deploy this!** |

**Start with "Balanced" for the best experience.**

---

## 🔧 Common Commands

### Check Service Health
```bash
curl http://localhost:5555/api/stats
curl http://localhost:8002/health
curl http://localhost:8009/health
```

### View Logs
```bash
docker logs rag-web-ui
docker logs rag-search-service
```

### Stop All Services
```bash
docker-compose -f docker-compose.test.yml down
```

### Reset Everything (Fresh Start)
```bash
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

---

## 📚 Next Steps

1. ✅ **Complete**: Quick Start (this guide)
2. 📖 **Read**: [Lab Guide](docs/lab/LAB_GUIDE.md) (also in UI)
3. ✏️ **Do**: [Student Exercises](docs/lab/STUDENT_EXERCISES.md) (3-4 hours)
4. 📖 **Study**: [Comprehensive Documentation](docs/COMPREHENSIVE_DOCUMENTATION.md)
5. 🚀 **Deploy**: [Deployment Guide](docs/deployment/DEPLOYMENT.md)

---

## ❓ Troubleshooting

### Services Won't Start
```bash
# Check Docker
docker ps

# Check Ollama
curl http://localhost:11434/api/tags
```

### UI Not Loading
```bash
# Check if port 5555 is in use
lsof -i :5555

# View logs
docker logs rag-web-ui
```

### No Search Results
1. Upload documents first (drag-and-drop in UI)
2. Build BM25 index (happens automatically)
3. Check Vector DB health: `curl http://localhost:8005/health`

### Web Search Not Working
```bash
# Check SearXNG
curl http://localhost:8080/search?q=test&format=json

# Check Web Search service
curl http://localhost:8009/health
```

---

## 💡 Quick Tips

- **Keyboard Shortcut**: Press `Enter` to send chat message
- **Settings Persist**: Your configuration is saved to browser localStorage
- **Lab Progress**: Progress tracking persists across sessions
- **Comparison Mode**: Automatically tracks last 2 queries for comparison
- **Mobile Responsive**: Works on phone, tablet, and desktop

---

## 🆘 Need Help?

- **GitHub Issues**: https://github.com/sandbreak80/rag_lab/issues
- **Documentation**: [docs/](docs/)
- **Lab Guide**: Click 📖 in UI
- **Quick Reference**: [CONTEXT_RECOVERY.md](CONTEXT_RECOVERY.md)

---

## 🎉 You're Ready!

**Open http://localhost:5555 and start learning!**

Click 📖 to open the Lab Guide and begin your RAG journey.

---

*Educational RAG Lab v1.0 - Built with ❤️ for education*

