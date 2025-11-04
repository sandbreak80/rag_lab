# Connect React UI to Backend - Setup Guide

## Current Status
- ✅ React UI running on http://localhost:5173
- ❌ Docker not running - need to start backend services

---

## Step 1: Start Docker Desktop

**On Mac**:
1. Open **Docker Desktop** application
2. Wait for it to say "Docker Desktop is running"
3. You should see the Docker icon in your menu bar

---

## Step 2: Start Backend Services

Once Docker is running, execute:

```bash
cd /Users/bmstoner/code_projects/rag_lab

# Start core backend services
docker-compose -f docker-compose.test.yml up -d \
  web-api \
  vector-db \
  ingest-service \
  search-service \
  knowledge-graph \
  reranker \
  chat-service \
  embedding-service \
  docling-service
```

This will start:
- **web-api** (port 5555) - Flask API backend
- **vector-db** (port 8005) - ChromaDB for embeddings
- **ingest-service** (port 8001) - Document processing
- **search-service** (port 8002) - RAG search orchestration
- **knowledge-graph** (port 8007) - Entity relationships
- **reranker** (port 8006) - LLM reranking
- **chat-service** (port 8003) - Chat/generation
- **embedding-service** (port 8004) - Text embeddings
- **docling-service** (port 8008) - PDF processing

---

## Step 3: Verify Services Are Running

```bash
# Check all containers are up
docker-compose -f docker-compose.test.yml ps

# Test API Gateway
curl http://localhost:5555/health

# Test Vector DB
curl http://localhost:8005/api/v1/heartbeat

# Test Ingest Service
curl http://localhost:8001/health
```

---

## Step 4: Verify React UI Connection

The React dev server (port 5173) is already configured to proxy API requests:

```typescript
// frontend/vite.config.ts (already configured)
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5555',  // Routes to web-api container
      changeOrigin: true,
    },
  },
}
```

**How it works**:
- Browser → `http://localhost:5173/api/stats`
- Vite proxy → `http://localhost:5555/api/stats`
- Flask backend → Returns data
- React UI → Displays data

---

## Step 5: Test the Connection

1. **Open browser**: http://localhost:5173
2. **Check console**: The `/api/stats` 500 error should disappear!
3. **Header should show**: Chunks, Documents, Graph Nodes counts
4. **Try uploading**: Go to Documents tab, upload a file
5. **Try chatting**: Go to Chat tab, ask a question

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│  Browser: http://localhost:5173                 │
│  React UI (Vite Dev Server)                     │
└────────────────┬────────────────────────────────┘
                 │
                 │ /api/* requests proxied to:
                 ↓
┌─────────────────────────────────────────────────┐
│  Docker Container: web-api (port 5555)          │
│  Flask API Server                               │
└────────────────┬────────────────────────────────┘
                 │
                 │ Orchestrates microservices:
                 ↓
┌─────────────────────────────────────────────────┐
│  Docker Network: rag-network                    │
│                                                  │
│  ├─ vector-db:8005      (ChromaDB)             │
│  ├─ ingest-service:8001 (Document processing)  │
│  ├─ search-service:8002 (RAG orchestration)    │
│  ├─ chat-service:8003   (LLM generation)       │
│  ├─ embedding-service:8004 (Embeddings)        │
│  ├─ reranker:8006       (Result reranking)     │
│  ├─ knowledge-graph:8007 (Entity graph)        │
│  └─ docling-service:8008 (PDF parsing)         │
└─────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: "Cannot connect to the Docker daemon"
**Solution**: Start Docker Desktop application

### Issue: "Port 5555 already in use"
**Solution**: Kill existing process
```bash
lsof -ti:5555 | xargs kill -9
```

### Issue: Containers fail to start
**Solution**: Check logs
```bash
docker-compose -f docker-compose.test.yml logs web-api
docker-compose -f docker-compose.test.yml logs vector-db
```

### Issue: React UI still shows 500 error
**Solution**:
1. Verify web-api is running: `curl http://localhost:5555/health`
2. Check browser network tab to see actual error
3. Restart Vite dev server: `cd frontend && npm run dev`

---

## Quick Commands

```bash
# Start everything
docker-compose -f docker-compose.test.yml up -d

# Stop everything
docker-compose -f docker-compose.test.yml down

# Restart web-api
docker-compose -f docker-compose.test.yml restart web-api

# View logs
docker-compose -f docker-compose.test.yml logs -f web-api

# Check container status
docker-compose -f docker-compose.test.yml ps
```

---

## What You'll See When Connected

### Header Stats (working):
```
Model: llama3.2:3b | Chunks: 0 | Documents: 0 | Graph Nodes: 0
```

### Chat Tab:
- Can type questions
- Get RAG-powered responses
- See source citations

### Documents Tab:
- Upload PDF, MD, TXT files
- See processing status
- View ingested documents

### Settings Tab:
- Change model
- Toggle RAG features
- Adjust parameters

### Metrics Tab:
- View query history
- See performance stats
- Export CSV

---

## Next Steps

Once connected:
1. ✅ Upload some test documents
2. ✅ Ask questions in chat
3. ✅ Toggle RAG features in settings
4. ✅ Compare performance in metrics
5. ✅ Complete lab exercises

---

**Ready?** Start Docker Desktop and run the commands above! 🚀

