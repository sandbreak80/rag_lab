// Complete Q&A Data - Troubleshooting and Advanced
// Part 4 (Final) of comprehensive Q&A knowledge base

import { QAItem } from './qaData';

export const QA_DATA_COMPLETE: QAItem[] = [
  // ============================================================================
  // TROUBLESHOOTING (15 Q&A)
  // ============================================================================
  {
    id: 'trouble-1',
    question: 'The UI is not loading. What should I check?',
    answer: `**Troubleshooting Steps:**

**1. Check Docker Containers**
\`\`\`bash
docker compose ps
\`\`\`
- All services should show "Up"
- If any show "Exit" or "Restarting", check logs

**2. Check Frontend Container**
\`\`\`bash
docker compose logs frontend
\`\`\`
- Look for nginx errors
- Common: "host not found in upstream"

**3. Check API Gateway**
\`\`\`bash
docker compose logs api-gateway
\`\`\`
- Should show "Running on http://0.0.0.0:8000"

**4. Check Browser Console**
- Open DevTools (F12)
- Look for network errors (red)
- Common: CORS errors, 502 Bad Gateway

**5. Rebuild Frontend**
\`\`\`bash
docker compose build frontend
docker compose up -d frontend
\`\`\`

**6. Access UI**
- Go to http://localhost:3000
- NOT port 5173 or 80

**Still Broken?** Run \`./scripts/clean-deploy.sh\` for fresh build.`,
    category: 'troubleshooting',
    tags: ['ui', 'frontend', 'docker'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['trouble-2', 'trouble-3'],
  },
  {
    id: 'trouble-2',
    question: 'Ollama is not responding. How do I fix it?',
    answer: `**Symptoms:**
- "Ollama not responding" in Settings
- No models in dropdown
- 500 errors when asking questions

**Troubleshooting:**

**1. Check Ollama Container**
\`\`\`bash
docker compose ps ollama
\`\`\`
- Should show "Up" and "healthy"

**2. Check Ollama Logs**
\`\`\`bash
docker compose logs ollama
\`\`\`
- Look for errors
- Should show "[GIN]" HTTP logs

**3. Test Ollama Directly**
\`\`\`bash
curl http://localhost:11434/api/tags
\`\`\`
- Should return JSON with model list

**4. Check GPU (if using)**
\`\`\`bash
nvidia-smi
\`\`\`
- Should show ollama process
- Check GPU memory usage

**5. Restart Ollama**
\`\`\`bash
docker compose restart ollama
\`\`\`
- Wait 30 seconds for startup

**6. Pull Models**
\`\`\`bash
./scripts/pull-ollama-models.sh
\`\`\`

**Still Broken?** Check docker-compose.yml GPU config.`,
    category: 'troubleshooting',
    tags: ['ollama', 'models', 'gpu'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['trouble-5', 'gs-3'],
  },
  {
    id: 'trouble-3',
    question: 'I am getting 500 errors. Where do I look?',
    answer: `**500 Internal Server Error:** Something crashed on the backend.

**Step-by-Step Debugging:**

**1. Identify Which Service**
- Open browser DevTools (F12)
- Go to Network tab
- Find the red (failed) request
- Look at URL: \`http://localhost:3000/api/...\`
- Note the endpoint (e.g., \`/api/ask\`)

**2. Check API Gateway Logs**
\`\`\`bash
docker compose logs api-gateway | tail -50
\`\`\`
- Shows which backend service it forwarded to
- Look for error messages

**3. Check Backend Service**
\`\`\`bash
# If error is from /api/ask:
docker compose logs chat-service | tail -50

# If error is from /api/search:
docker compose logs search-service | tail -50
\`\`\`

**4. Common Errors**
- **"model not found":** Pull model with \`pull-ollama-models.sh\`
- **"No module named X":** Missing Python dependency
- **"Connection refused":** Service not running
- **"Out of memory":** GPU/RAM exhausted

**5. Restart Affected Service**
\`\`\`bash
docker compose restart chat-service
\`\`\`

**Still Broken?** Share logs in GitHub issue.`,
    category: 'troubleshooting',
    tags: ['errors', '500', 'debugging'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['trouble-1', 'trouble-4'],
  },
  {
    id: 'trouble-4',
    question: 'Search is returning no results. Why?',
    answer: `**Possible Causes:**

**1. No Documents Uploaded**
- Go to Documents tab
- Check if documents are listed
- If empty, upload documents

**2. Vector DB Not Initialized**
\`\`\`bash
docker compose logs vector-db
\`\`\`
- Should show "ChromaDB initialized"
- If not, restart: \`docker compose restart vector-db\`

**3. Documents Not Embedded**
- After upload, wait for processing
- Check ingest-service logs:
\`\`\`bash
docker compose logs ingest-service
\`\`\`

**4. Query Too Specific**
- Try broader query
- Example: "AI" instead of "transformer architecture in GPT-4"

**5. Wrong Search Config**
- Check Settings → RAG Configuration
- Ensure top_k > 0
- Ensure at least one search method enabled (vector or BM25)

**6. Metadata Filters Too Restrictive**
- Check Settings → Metadata Filters
- Clear filters and try again

**Debug:**
\`\`\`bash
# Check document count
curl http://localhost:8000/api/documents
\`\`\`

**Still No Results?** Try "Reset KG" and re-upload documents.`,
    category: 'troubleshooting',
    tags: ['search', 'no-results', 'debugging'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['trouble-3', 'gs-8'],
  },
  {
    id: 'trouble-5',
    question: 'GPU is not being used. How do I enable it?',
    answer: `**Prerequisites:**
- NVIDIA GPU (not AMD or Intel)
- NVIDIA drivers installed
- nvidia-container-toolkit installed

**Verify GPU Setup:**

**1. Check nvidia-smi**
\`\`\`bash
nvidia-smi
\`\`\`
- Should show GPU name, driver version
- If "command not found", install NVIDIA drivers

**2. Check Docker GPU Support**
\`\`\`bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
\`\`\`
- Should show GPU info
- If error, install nvidia-container-toolkit

**3. Check docker-compose.yml**
\`\`\`yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
\`\`\`
- Ensure this section is uncommented

**4. Restart Ollama**
\`\`\`bash
docker compose down
docker compose up -d
\`\`\`

**5. Verify GPU Usage**
\`\`\`bash
nvidia-smi
\`\`\`
- Should show "ollama" process
- GPU memory should be used (e.g., 8GB)

**Full Guide:** See docs/deployment/GPU_SETUP.md`,
    category: 'troubleshooting',
    tags: ['gpu', 'nvidia', 'performance'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['model-9', 'trouble-2'],
    externalLinks: [
      { title: 'GPU Setup Guide', url: '/docs/deployment/GPU_SETUP.md' }
    ],
  },
  {
    id: 'trouble-6',
    question: 'Docker containers keep restarting. What is wrong?',
    answer: `**Common Causes:**

**1. Port Conflicts**
- Another service using the same port
- Check: \`lsof -i :3000\` (or other port)
- Fix: Stop conflicting service or change port

**2. Out of Memory**
- Docker running out of RAM
- Check: \`docker stats\`
- Fix: Increase Docker memory limit (Docker Desktop → Settings)

**3. Missing Dependencies**
- Python package not installed
- Check service logs for "ModuleNotFoundError"
- Fix: Rebuild image with \`docker compose build\`

**4. Configuration Error**
- Invalid config.env
- Check logs for "KeyError" or "ValueError"
- Fix: Verify config.env matches expected format

**5. Volume Permission Issues**
- Docker can't write to volume
- Check: \`docker compose logs | grep "Permission denied"\`
- Fix: \`chmod 777 data/\` (development only!)

**Debug:**
\`\`\`bash
# Watch all container statuses
watch docker compose ps

# Check specific service
docker compose logs --tail=100 <service-name>
\`\`\`

**Nuclear Option:** \`./scripts/clean-deploy.sh\` (removes all data!)`,
    category: 'troubleshooting',
    tags: ['docker', 'containers', 'restart'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['trouble-1', 'trouble-7'],
  },
  {
    id: 'trouble-7',
    question: 'How do I completely reset the lab?',
    answer: `**Complete Reset (Nuclear Option):**

**1. Stop All Containers**
\`\`\`bash
docker compose down
\`\`\`

**2. Remove All Data Volumes**
\`\`\`bash
docker volume rm rag_lab_chroma_data
docker volume rm rag_lab_ollama_data
docker volume rm rag_lab_metrics_data
docker volume rm rag_lab_vault_data
docker volume rm rag_lab_indices_data
\`\`\`

**3. Remove All Images**
\`\`\`bash
docker compose down --rmi all
\`\`\`

**4. Prune Docker System**
\`\`\`bash
docker system prune -af --volumes
\`\`\`

**5. Fresh Build**
\`\`\`bash
./scripts/clean-deploy.sh
\`\`\`

**Or Use Script:**
\`\`\`bash
./scripts/clean-deploy.sh
# Select "yes" when prompted to remove volumes
\`\`\`

**What Gets Deleted:**
- All uploaded documents
- All embeddings
- Knowledge graph
- Chat history (if not in localStorage)
- Ollama models (need to re-pull)
- All metrics

**What Stays:**
- Source code
- Configuration files
- Docker images (unless removed)

**Use When:**
- Stuck in broken state
- Testing fresh deployment
- Switching major versions`,
    category: 'troubleshooting',
    tags: ['reset', 'clean', 'fresh-start'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['trouble-6', 'gs-2'],
  },
  {
    id: 'trouble-8',
    question: 'Responses are very slow. How do I speed them up?',
    answer: `**Speed Optimization:**

**1. Use Fast Preset**
- Settings → Quick Presets → Fast
- ~60ms latency (vs 1500ms default)

**2. Disable Expensive Features**
- Settings → RAG Configuration
- Turn OFF:
  - Re-ranking (-2000ms)
  - Web Search (-800ms)
  - Knowledge Graph (-50ms)

**3. Use Smaller Model**
- Settings → Model Selection
- Try: llama3.2:3b (60-80 tok/s)
- vs llama3.1:8b (40-60 tok/s)

**4. Reduce top_k**
- Settings → RAG Configuration
- Change from 10 to 5
- Saves ~20ms

**5. Enable GPU**
- See trouble-5 for GPU setup
- 10x faster than CPU

**6. Reduce Context Window**
- Settings → Advanced → Context Window
- Change from 16000 to 4000
- Faster processing

**7. Check System Resources**
\`\`\`bash
# CPU usage
top

# GPU usage
nvidia-smi

# Disk I/O
iostat
\`\`\`

**Expected Latency:**
- Fast preset + GPU: 60-100ms
- Balanced + GPU: 120-200ms
- Quality + GPU: 1500-2000ms`,
    category: 'troubleshooting',
    tags: ['performance', 'speed', 'optimization'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['perf-6', 'trouble-5'],
  },
  {
    id: 'trouble-9',
    question: 'LLM responses are inaccurate or hallucinating. Why?',
    answer: `**Causes of Hallucinations:**

**1. No Relevant Documents**
- RAG can't find relevant context
- LLM makes up answer
- Fix: Upload better documents

**2. Context Window Too Small**
- Important info gets truncated
- LLM only sees partial context
- Fix: Increase context window (Settings)

**3. Temperature Too High**
- More creative = more hallucinations
- Fix: Lower temperature (edit chat service)

**4. Model Too Small**
- 1B/3B models less accurate
- Fix: Use larger model (8B+)

**5. Prompt Not Restrictive Enough**
- LLM ignores provided context
- Fix: Already optimized in this lab

**6. Query Too Broad**
- "Tell me about AI" → too general
- Fix: Ask specific questions

**How to Verify:**
1. Check sources in response
2. If sources are relevant, model is hallucinating
3. If sources are irrelevant, search is failing

**Best Practices:**
- Use Quality or Production preset
- Enable all search features
- Use 8B+ model
- Ask specific questions
- Verify sources`,
    category: 'troubleshooting',
    tags: ['accuracy', 'hallucinations', 'quality'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['perf-7', 'rag-8'],
  },
  {
    id: 'trouble-10',
    question: 'Knowledge graph shows 0 nodes. How do I fix it?',
    answer: `**Causes:**

**1. No Documents Uploaded**
- Upload documents first
- Then rebuild KG

**2. KG Not Built**
- Go to Documents tab
- Select algorithm (e.g., Wikilinks)
- Click "Rebuild KG"

**3. Build Failed**
- Check knowledge-graph service logs:
\`\`\`bash
docker compose logs knowledge-graph
\`\`\`
- Look for errors

**4. Vector DB Empty**
- KG needs documents from vector DB
- Check vector-db logs:
\`\`\`bash
docker compose logs vector-db
\`\`\`

**5. Algorithm Not Supported**
- Some algorithms need specific data
- Try Wikilinks (most reliable)

**Step-by-Step Fix:**

1. **Upload Documents**
   - Documents tab → Upload files

2. **Wait for Processing**
   - Check ingest-service logs
   - Should see "Document processed"

3. **Rebuild KG**
   - Documents tab → Select "Wikilinks"
   - Click "Rebuild KG"
   - Wait 5-10 seconds

4. **Verify**
   - Should show "X graph nodes"
   - If still 0, check logs

**Expected Node Count:** ~1 node per document (for Wikilinks)`,
    category: 'troubleshooting',
    tags: ['knowledge-graph', 'debugging'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-5', 'trouble-4'],
  },
  {
    id: 'trouble-11',
    question: 'Web search is not working. What should I check?',
    answer: `**Troubleshooting Web Search:**

**1. Check SearXNG Container**
\`\`\`bash
docker compose ps searxng
\`\`\`
- Should show "Up"

**2. Check SearXNG Logs**
\`\`\`bash
docker compose logs searxng
\`\`\`
- Look for errors

**3. Test SearXNG Directly**
\`\`\`bash
curl "http://localhost:8080/search?q=test&format=json"
\`\`\`
- Should return JSON results

**4. Check Web Search Service**
\`\`\`bash
docker compose logs web-search
\`\`\`
- Should show "Running on port 8010"

**5. Enable Web Search in UI**
- Settings → RAG Configuration
- Toggle "Web Search" ON
- Or use Quality/Maximum preset

**6. Check Network**
- SearXNG needs internet access
- Test: \`ping google.com\` from host

**7. Restart Services**
\`\`\`bash
docker compose restart searxng web-search
\`\`\`

**Common Issues:**
- Firewall blocking outbound requests
- SearXNG rate limited by search engines
- Network timeout (increase timeout in web-search service)

**Still Not Working?** Disable web search and use RAG-only mode.`,
    category: 'troubleshooting',
    tags: ['web-search', 'searxng', 'network'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-10', 'trouble-3'],
  },
  {
    id: 'trouble-12',
    question: 'File upload is failing. Why?',
    answer: `**Common Upload Issues:**

**1. File Too Large**
- Max size: 100MB (default)
- Fix: Edit nginx.conf \`client_max_body_size\`

**2. Unsupported File Type**
- Supported: .md, .txt, .pdf, .docx
- Fix: Convert file or add support

**3. Docling Service Down**
\`\`\`bash
docker compose logs docling
\`\`\`
- Should show "Running on port 8006"
- Restart if needed

**4. Ingest Service Down**
\`\`\`bash
docker compose logs ingest-service
\`\`\`
- Should show "Running on port 8004"

**5. Out of Disk Space**
\`\`\`bash
df -h
\`\`\`
- Check available space
- Clean up if needed

**6. Permission Issues**
- Docker can't write to volume
- Fix: \`chmod 777 data/vault\` (dev only!)

**7. Network Timeout**
- Large files take time
- Wait longer or increase timeout

**Debug:**
\`\`\`bash
# Check upload endpoint
curl -X POST http://localhost:8000/api/upload \\
  -F "file=@test.txt"
\`\`\`

**Workaround:** Manually copy files to \`data/vault/\` and restart ingest-service.`,
    category: 'troubleshooting',
    tags: ['upload', 'files', 'documents'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['gs-8', 'trouble-3'],
  },
  {
    id: 'trouble-13',
    question: 'Metrics are not being tracked. Where are they?',
    answer: `**Troubleshooting Metrics:**

**1. Check Metrics Store Service**
\`\`\`bash
docker compose logs metrics-store
\`\`\`
- Should show "Running on port 8011"
- Should show "Database initialized"

**2. Check Database File**
\`\`\`bash
ls -lh data/metrics/metrics.db
\`\`\`
- Should exist and have size > 0

**3. Ask a Question**
- Go to Chat tab
- Ask any question
- Wait for response

**4. Check Metrics Tab**
- Should show new query
- If empty, metrics not being saved

**5. Check Browser Console**
- F12 → Console
- Look for errors when asking questions

**6. Restart Metrics Store**
\`\`\`bash
docker compose restart metrics-store
\`\`\`

**7. Check API Gateway**
\`\`\`bash
docker compose logs api-gateway | grep metrics
\`\`\`
- Should show POST requests to metrics-store

**Manual Test:**
\`\`\`bash
curl -X POST http://localhost:8000/api/metrics \\
  -H "Content-Type: application/json" \\
  -d '{"query": "test", "latency_ms": 100}'
\`\`\`

**Still Not Working?** Delete metrics.db and restart metrics-store.`,
    category: 'troubleshooting',
    tags: ['metrics', 'tracking', 'database'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['gs-6', 'trouble-3'],
  },
  {
    id: 'trouble-14',
    question: 'Chat history is not persisting. Why?',
    answer: `**Chat History Storage:**

This lab stores chat history in **browser localStorage** (not backend).

**Causes of Lost History:**

**1. Browser Cache Cleared**
- Clearing cache deletes localStorage
- Fix: Don't clear cache, or export chat first

**2. Different Browser/Device**
- localStorage is per-browser
- Fix: Use same browser, or implement backend storage

**3. Incognito/Private Mode**
- localStorage cleared on close
- Fix: Use normal browsing mode

**4. localStorage Full**
- Browsers limit localStorage (5-10MB)
- Fix: Clear old chats or export to CSV

**5. Browser Bug**
- Rare, but possible
- Fix: Try different browser

**How to Verify:**
1. Open DevTools (F12)
2. Go to Application → Local Storage
3. Check for \`rag_chat_messages\` key
4. Should contain JSON array

**Export Chat:**
- Metrics tab → Export to CSV
- Saves all queries and responses

**Future Enhancement:** Add backend chat persistence (database).`,
    category: 'troubleshooting',
    tags: ['chat', 'persistence', 'localstorage'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['gs-5'],
  },
  {
    id: 'trouble-15',
    question: 'Where can I get help if I am still stuck?',
    answer: `**Getting Help:**

**1. Check Documentation**
- \`README.md\` - Project overview
- \`docs/QUICK_START.md\` - Getting started
- \`docs/deployment/\` - Deployment guides
- \`docs/lab/\` - Lab exercises

**2. Check Logs**
\`\`\`bash
# All services
docker compose logs

# Specific service
docker compose logs <service-name>

# Follow logs
docker compose logs -f
\`\`\`

**3. Search GitHub Issues**
- [GitHub Issues](https://github.com/yourusername/rag_lab/issues)
- Someone may have had same problem

**4. Create GitHub Issue**
- Include:
  - Error message
  - Steps to reproduce
  - Logs (relevant parts)
  - System info (OS, Docker version, GPU)

**5. Community Support**
- Discord: [link]
- Slack: [link]
- Reddit: r/LocalLLaMA

**6. Splunk/Cisco Support**
- Internal Slack channels
- Field team support

**7. Debug Mode**
- Set \`DEBUG=true\` in config.env
- Restart services
- More verbose logging

**Pro Tip:** Include \`docker compose logs\` output when asking for help!`,
    category: 'troubleshooting',
    tags: ['help', 'support', 'community'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['trouble-1', 'trouble-3'],
  },

  // ============================================================================
  // ADVANCED (10 Q&A)
  // ============================================================================
  {
    id: 'adv-1',
    question: 'How do I add a new microservice?',
    answer: `**Adding a New Microservice:**

**1. Create Service Directory**
\`\`\`bash
mkdir -p services/my-service/app
cd services/my-service
\`\`\`

**2. Create Flask App**
\`\`\`python
# app/service.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/my-endpoint', methods=['POST'])
def my_endpoint():
    data = request.json
    # Your logic here
    return jsonify({'result': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8012)
\`\`\`

**3. Create Dockerfile**
\`\`\`dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["python", "app/service.py"]
\`\`\`

**4. Add to docker-compose.yml**
\`\`\`yaml
my-service:
  build: ./services/my-service
  ports:
    - "8012:8012"
  networks:
    - rag-network
  env_file:
    - config.env
\`\`\`

**5. Add Route to API Gateway**
\`\`\`python
# services/api-gateway/app/service.py
@app.route('/api/my-endpoint', methods=['POST'])
def my_endpoint():
    response = requests.post(
        'http://my-service:8012/my-endpoint',
        json=request.json
    )
    return jsonify(response.json())
\`\`\`

**6. Build and Start**
\`\`\`bash
docker compose build my-service
docker compose up -d my-service
\`\`\``,
    category: 'advanced',
    tags: ['microservices', 'architecture', 'development'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['adv-2'],
  },
  {
    id: 'adv-2',
    question: 'How does the microservices architecture work?',
    answer: `**Architecture Overview:**

\`\`\`
Frontend (React)
    ↓
API Gateway (Flask)
    ↓
┌─────────────────────────────────────┐
│  Backend Microservices (Flask)      │
│  ├─ vector-db (ChromaDB)            │
│  ├─ embedding (Ollama)              │
│  ├─ search (Vector + BM25 + Fusion) │
│  ├─ chat (LLM generation)           │
│  ├─ ingest (Document processing)    │
│  ├─ docling (PDF/DOCX parsing)      │
│  ├─ knowledge-graph (NetworkX)      │
│  ├─ reranker (LLM re-ranking)       │
│  ├─ web-search (SearXNG proxy)      │
│  └─ metrics-store (SQLite)          │
└─────────────────────────────────────┘
    ↓
External Services
    ├─ Ollama (LLM inference)
    └─ SearXNG (Web search)
\`\`\`

**Communication:**
- Frontend → API Gateway: HTTP/JSON (port 3000)
- API Gateway → Services: HTTP/JSON (internal network)
- Services → Services: HTTP/JSON (internal network)

**Benefits:**
- Independent scaling
- Fault isolation
- Technology flexibility
- Easy testing

**Trade-offs:**
- Network latency
- More complex deployment
- Distributed debugging

**This Lab:** 11 microservices + 2 external services`,
    category: 'advanced',
    tags: ['architecture', 'microservices', 'design'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['adv-1', 'adv-3'],
  },
  {
    id: 'adv-3',
    question: 'How do I scale this for production?',
    answer: `**Production Scaling Strategies:**

**1. Horizontal Scaling (Replicas)**
\`\`\`yaml
# docker-compose.yml
search-service:
  deploy:
    replicas: 3  # 3 instances
\`\`\`

**2. Load Balancing**
- Add nginx/traefik in front of API Gateway
- Round-robin to multiple API Gateway instances
- Sticky sessions for chat (if needed)

**3. Database Scaling**
- **Vector DB:** ChromaDB → Pinecone/Weaviate (managed)
- **Metrics:** SQLite → PostgreSQL/TimescaleDB
- **Chat History:** Add Redis for session storage

**4. Caching**
- Redis for embeddings cache
- CDN for static assets
- Query result caching (5-60 min TTL)

**5. Async Processing**
- RabbitMQ/Kafka for document ingestion
- Background workers for embedding
- Webhooks for completion notifications

**6. Monitoring**
- Prometheus for metrics
- Grafana for dashboards
- Jaeger for distributed tracing
- ELK stack for log aggregation

**7. Infrastructure**
- Kubernetes for orchestration
- Auto-scaling based on CPU/memory
- Multi-region deployment
- CDN for global distribution

**Expected Capacity:**
- Single instance: 10-50 QPS
- 3 replicas: 30-150 QPS
- 10 replicas: 100-500 QPS

**This Lab:** Single-instance development setup. See docs for production architecture.`,
    category: 'advanced',
    tags: ['scaling', 'production', 'deployment'],
    difficulty: 'advanced',
    estimatedReadTime: 4,
    relatedQuestions: ['adv-2', 'perf-8'],
  },
  {
    id: 'adv-4',
    question: 'Can I use a different vector database?',
    answer: `**Yes!** This lab uses ChromaDB, but you can swap it.

**Popular Alternatives:**

**1. Pinecone** (Managed, Cloud)
- Pros: Fully managed, scales to billions
- Cons: Costs money, cloud-only
- Use: Production, high scale

**2. Weaviate** (Open Source)
- Pros: Advanced features, GraphQL API
- Cons: More complex setup
- Use: Hybrid search, multi-tenancy

**3. Qdrant** (Open Source)
- Pros: Fast, Rust-based, filtering
- Cons: Newer, smaller community
- Use: High performance, filtering

**4. Milvus** (Open Source)
- Pros: Distributed, GPU support
- Cons: Complex, resource-heavy
- Use: Very large scale (> 100M vectors)

**5. FAISS** (Library, not DB)
- Pros: Fastest, Facebook-built
- Cons: No persistence, in-memory only
- Use: Research, benchmarking

**How to Swap:**

1. **Replace vector-db service** in docker-compose.yml
2. **Update vector-db API** (services/vector-db/app/service.py)
3. **Keep same API contract** (add, search, delete endpoints)
4. **Update connection** in other services

**This Lab:** ChromaDB is simple, local, and perfect for learning!`,
    category: 'advanced',
    tags: ['vector-db', 'alternatives', 'customization'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['rag-3', 'adv-5'],
  },
  {
    id: 'adv-5',
    question: 'How do I implement custom re-ranking?',
    answer: `**Custom Re-ranking Strategies:**

**1. LLM-based (Current)**
- Send query + docs to LLM
- Ask LLM to score relevance
- Pros: High quality
- Cons: Very slow (2000ms)

**2. Cross-encoder (Better)**
\`\`\`python
from sentence_transformers import CrossEncoder

model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

def rerank(query, docs):
    pairs = [[query, doc['content']] for doc in docs]
    scores = model.predict(pairs)
    return sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
\`\`\`
- Pros: Fast (50-100ms), accurate
- Cons: Needs GPU

**3. BM25 Re-ranking**
\`\`\`python
from rank_bm25 import BM25Okapi

def rerank(query, docs):
    corpus = [doc['content'].split() for doc in docs]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.split())
    return sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
\`\`\`
- Pros: Very fast (10ms), no GPU
- Cons: Less accurate than cross-encoder

**4. Hybrid Re-ranking**
- Combine multiple scores
- Weighted average or RRF
- Best of all worlds

**Implementation:**
1. Edit \`services/reranker/app/service.py\`
2. Add new re-ranking method
3. Expose via API
4. Update UI to select method

**Recommendation:** Use cross-encoder for production (50ms, 95% quality)`,
    category: 'advanced',
    tags: ['reranking', 'algorithms', 'customization'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['search-9', 'adv-6'],
    codeExample: `# Cross-encoder re-ranking
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
    
    def rerank(self, query: str, docs: List[Dict]) -> List[Dict]:
        pairs = [[query, doc['content']] for doc in docs]
        scores = self.model.predict(pairs)
        
        # Sort by score (descending)
        ranked = sorted(
            zip(docs, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [doc for doc, score in ranked]`,
  },
  {
    id: 'adv-6',
    question: 'How do I add custom metadata filters?',
    answer: `**Custom Metadata Filtering:**

**1. Add Metadata to Documents**
\`\`\`python
# When ingesting documents
metadata = {
    'filename': 'doc.pdf',
    'author': 'John Doe',
    'department': 'Engineering',
    'classification': 'confidential',
    'tags': ['ai', 'ml', 'tutorial'],
    'created_at': '2025-01-01',
}
\`\`\`

**2. Store in Vector DB**
\`\`\`python
# services/vector-db/app/service.py
collection.add(
    documents=[content],
    metadatas=[metadata],
    ids=[doc_id]
)
\`\`\`

**3. Filter in Search**
\`\`\`python
# services/search/app/service.py
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k,
    where={
        'department': 'Engineering',
        'classification': {'$ne': 'confidential'}
    }
)
\`\`\`

**4. Add UI Controls**
\`\`\`typescript
// frontend/src/components/settings/MetadataFilters.tsx
<select onChange={handleDepartmentChange}>
  <option value="">All Departments</option>
  <option value="Engineering">Engineering</option>
  <option value="Sales">Sales</option>
</select>
\`\`\`

**5. Pass to Backend**
\`\`\`typescript
// frontend/src/services/api.ts
const response = await axios.post('/api/search', {
  query,
  filters: {
    department: 'Engineering',
    tags: ['ai', 'ml']
  }
});
\`\`\`

**ChromaDB Filter Operators:**
- \`$eq\`: equals
- \`$ne\`: not equals
- \`$gt\`, \`$gte\`: greater than
- \`$lt\`, \`$lte\`: less than
- \`$in\`: in array
- \`$nin\`: not in array

**This Lab:** Metadata filters UI exists, backend filtering ready to implement!`,
    category: 'advanced',
    tags: ['metadata', 'filtering', 'customization'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['search-4', 'adv-7'],
  },
  {
    id: 'adv-7',
    question: 'How do I add support for new file types?',
    answer: `**Adding New File Type Support:**

**1. Identify Parser**
- PDF/DOCX: Docling (already supported)
- CSV: pandas
- JSON: json library
- HTML: BeautifulSoup
- Images: OCR (tesseract)

**2. Add Parser to Docling Service**
\`\`\`python
# services/docling/app/service.py

@app.route('/parse', methods=['POST'])
def parse_document():
    file = request.files['file']
    file_ext = file.filename.split('.')[-1]
    
    if file_ext == 'csv':
        return parse_csv(file)
    elif file_ext == 'json':
        return parse_json(file)
    elif file_ext == 'html':
        return parse_html(file)
    # ... existing parsers
\`\`\`

**3. Implement Parser**
\`\`\`python
import pandas as pd

def parse_csv(file):
    df = pd.read_csv(file)
    # Convert to text
    text = df.to_string()
    return jsonify({
        'content': text,
        'metadata': {
            'rows': len(df),
            'columns': list(df.columns)
        }
    })
\`\`\`

**4. Update Frontend**
\`\`\`typescript
// frontend/src/components/documents/DocumentUpload.tsx
const ACCEPTED_FILE_TYPES = [
  '.md', '.txt', '.pdf', '.docx',
  '.csv', '.json', '.html'  // New types
];
\`\`\`

**5. Test**
\`\`\`bash
curl -X POST http://localhost:8000/api/upload \\
  -F "file=@test.csv"
\`\`\`

**Example: CSV Parser**
\`\`\`python
import pandas as pd

def parse_csv(file_path):
    df = pd.read_csv(file_path)
    
    # Convert to markdown table
    markdown = df.to_markdown()
    
    return {
        'content': markdown,
        'metadata': {
            'type': 'csv',
            'rows': len(df),
            'columns': list(df.columns)
        }
    }
\`\`\`

**This Lab:** Supports .md, .txt, .pdf, .docx. Easy to extend!`,
    category: 'advanced',
    tags: ['file-types', 'parsing', 'customization'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['gs-8', 'adv-8'],
  },
  {
    id: 'adv-8',
    question: 'How do I implement agentic workflows?',
    answer: `**Agentic AI:** LLM that can use tools and make decisions.

**Example: Research Agent**

**1. Define Tools**
\`\`\`python
tools = [
    {
        'name': 'search_documents',
        'description': 'Search internal documents',
        'parameters': {'query': 'string'}
    },
    {
        'name': 'web_search',
        'description': 'Search the web',
        'parameters': {'query': 'string'}
    },
    {
        'name': 'calculate',
        'description': 'Perform calculations',
        'parameters': {'expression': 'string'}
    }
]
\`\`\`

**2. Agent Loop**
\`\`\`python
def agent_loop(user_query):
    messages = [{'role': 'user', 'content': user_query}]
    
    for i in range(max_iterations):
        # LLM decides next action
        response = llm.chat(messages, tools=tools)
        
        if response.tool_calls:
            # Execute tool
            for tool_call in response.tool_calls:
                result = execute_tool(tool_call)
                messages.append({
                    'role': 'tool',
                    'content': result
                })
        else:
            # Final answer
            return response.content
\`\`\`

**3. Tool Execution**
\`\`\`python
def execute_tool(tool_call):
    if tool_call.name == 'search_documents':
        return search_service.search(tool_call.args['query'])
    elif tool_call.name == 'web_search':
        return web_search_service.search(tool_call.args['query'])
    elif tool_call.name == 'calculate':
        return eval(tool_call.args['expression'])
\`\`\`

**Example Query:**
\`\`\`
User: "What is the revenue growth of our top competitor?"

Agent:
1. search_documents("competitor revenue") → No results
2. web_search("competitor Q4 2024 revenue") → $500M
3. web_search("competitor Q4 2023 revenue") → $400M
4. calculate("(500 - 400) / 400 * 100") → 25%
5. Final answer: "25% year-over-year growth"
\`\`\`

**This Lab:** Foundation for agentic AI. Tools already exist (search, web, etc.)!`,
    category: 'advanced',
    tags: ['agentic-ai', 'agents', 'tools'],
    difficulty: 'advanced',
    estimatedReadTime: 4,
    relatedQuestions: ['adv-9', 'adv-10'],
  },
  {
    id: 'adv-9',
    question: 'How do I implement multi-modal RAG (images, audio)?',
    answer: `**Multi-Modal RAG:** Handle images, audio, video alongside text.

**Architecture:**

**1. Image RAG**
\`\`\`python
# Extract text from images (OCR)
from PIL import Image
import pytesseract

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Or use vision model
def describe_image(image_path):
    # Use LLaVA, CLIP, or GPT-4V
    description = vision_model.describe(image_path)
    return description
\`\`\`

**2. Audio RAG**
\`\`\`python
# Transcribe audio
import whisper

model = whisper.load_model("base")

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]
\`\`\`

**3. Multi-Modal Embeddings**
\`\`\`python
# CLIP embeddings (text + images)
from transformers import CLIPModel, CLIPProcessor

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def embed_image(image):
    inputs = processor(images=image, return_tensors="pt")
    embeddings = model.get_image_features(**inputs)
    return embeddings

def embed_text(text):
    inputs = processor(text=text, return_tensors="pt")
    embeddings = model.get_text_features(**inputs)
    return embeddings

# Search images with text query
query_embedding = embed_text("a cat")
image_embeddings = [embed_image(img) for img in images]
# Find most similar
\`\`\`

**4. Implementation Steps**
1. Add OCR/transcription to docling service
2. Use multi-modal embedding model
3. Store embeddings in vector DB
4. Update search to handle multi-modal queries

**This Lab:** Text-only currently. Multi-modal is a great extension project!`,
    category: 'advanced',
    tags: ['multi-modal', 'images', 'audio'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['adv-7', 'adv-10'],
  },
  {
    id: 'adv-10',
    question: 'What are the next frontiers in RAG?',
    answer: `**Emerging RAG Trends (2025+):**

**1. Agentic RAG** 🔥
- LLMs that use tools autonomously
- Multi-step reasoning
- Self-correction
- This lab: Foundation ready!

**2. Multi-Modal RAG**
- Images, audio, video, code
- Unified embeddings (CLIP, ImageBind)
- Cross-modal search

**3. Graph RAG** 🔥
- Knowledge graphs as first-class citizens
- Multi-hop reasoning
- Entity-centric retrieval
- This lab: Already implemented!

**4. Adaptive RAG**
- Dynamic feature selection
- Query-specific optimization
- Cost-aware routing

**5. Federated RAG**
- Search across multiple organizations
- Privacy-preserving retrieval
- Secure multi-party computation

**6. Real-Time RAG**
- Sub-100ms latency
- Streaming responses
- Incremental indexing

**7. Personalized RAG**
- User-specific embeddings
- Adaptive ranking
- Privacy-preserving personalization

**8. Explainable RAG**
- Source attribution
- Confidence scores
- Reasoning traces
- This lab: Already shows sources!

**9. Self-Improving RAG**
- Learn from user feedback
- Automatic query expansion
- Dynamic re-ranking

**10. Enterprise RAG**
- Multi-tenancy
- RBAC, audit logs
- Compliance (GDPR, HIPAA)
- This lab: Security features planned!

**This Lab:** Covers 40% of emerging trends. Perfect foundation for experimentation!`,
    category: 'advanced',
    tags: ['future', 'trends', 'research'],
    difficulty: 'advanced',
    estimatedReadTime: 4,
    relatedQuestions: ['adv-8', 'adv-9'],
  },
];

export default QA_DATA_COMPLETE;

