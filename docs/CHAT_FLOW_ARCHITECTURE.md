# RAG Lab - Chat Flow Architecture

**Last Updated:** November 17, 2025  
**Version:** 1.0

---

## 📋 Overview

This document describes the complete end-to-end flow of a chat query through the RAG Lab microservices architecture, from user input to final response.

---

## 🔄 Complete Chat Flow

### 1. Frontend Request Initiation

**Location:** `frontend/src/components/chat/ChatInterface.tsx`

```typescript
// User submits query
const chatMutation = useMutation({
  mutationFn: async (query: string) => {
    const requestId = uuidv4(); // Generate unique request ID
    return await api.sendMessage(query, config, signal, requestId);
  }
});
```

**Key Steps:**
- User types query in chat interface
- Frontend generates unique `request_id` (UUID)
- Frontend sends POST request to `/api/ask` via API Gateway
- Request includes: `query`, `top_k`, `web_search_enabled`, `use_graph`, `enable_research`, etc.

---

### 2. API Gateway (`api-gateway`)

**Location:** `services/api-gateway/app/service.py`

**Endpoint:** `POST /api/ask`

**Responsibilities:**
- Receives request from frontend
- Validates request format
- Forwards to RAG API v1 service (`rag-api-v1`)
- Adds timing metrics
- Detects hallucinated citations
- Enriches source metadata

**Flow:**
```
Frontend → API Gateway (/api/ask)
         ↓
    Validates & transforms request
         ↓
    Forwards to rag-api-v1:8000/v1/rag/query
         ↓
    Receives response
         ↓
    Adds gateway overhead metrics
         ↓
    Validates citations
         ↓
    Returns to frontend
```

---

### 3. RAG API v1 Service (`rag-api-v1`)

**Location:** `services/api/routes/rag.py`

**Endpoint:** `POST /v1/rag/query`

**9-Stage Pipeline:**

#### STAGE 0: IDs & Context
- Generates/validates `request_id`
- Creates OpenTelemetry trace
- Infers query intent (temporal, factual, analytical, etc.)

#### STAGE 1: AuthZ & ACL
- Builds ACL predicate based on user/groups/dept
- Filters documents by permission tags

#### STAGE 2: Retrieval (Parallel Hybrid Search)

**Parallel Tasks:**
1. **Vector Search** (`vector-db:8005`)
   - Generates query embedding via `embedding-service:8006`
   - Performs semantic similarity search
   - Returns top-k results with scores

2. **Knowledge Graph Search** (`knowledge-graph:8007`)
   - Expands query with related entities
   - Traverses graph relationships
   - Returns connected documents/entities

3. **Web Search** (`web-search:8008` via SearXNG)
   - Only if `web_search_enabled=true`
   - Searches external web sources
   - Returns top-k web results

4. **Research Agent Content** (via Vector DB)
   - Research documents are already in Vector DB
   - Identified by `document_id` starting with `research_`
   - Retrieved via normal vector search

**Result:** Combined list of results from all sources

#### STAGE 3: Recency Gate
- Evaluates if query requires recent information
- Filters out stale sources for temporal queries
- Research sources are always considered "fresh"

#### STAGE 4: Rerank (Weighted Scoring)

**Weighted Scoring:**
- **RAG/Research sources:** 1.0x (highest priority - trusted internal)
- **Knowledge Graph:** 0.9x (high priority - graph relationships)
- **Web Search:** 0.65x (lower priority - external, less reliable)

**Process:**
1. Apply source-type weights to scores
2. Sort by weighted score (descending)
3. Select top-k results for LLM context

#### STAGE 5: Synthesis (LLM Generation)

**Location:** `services/api/routes/rag.py` → `build_prompt_messages()`

**Prompt Construction:**
1. Load system prompt from `prompts.json`
2. Format with:
   - Source context (counts of RAG/Research/Web sources)
   - Citation instructions
   - Query-specific guidance
3. Build context from top-k results
4. Send to Ollama (`ollama:11434`)

**LLM Model:** `llama3.2:3b` (configurable)

**Response:** Generated answer with citations

#### STAGE 6: Guardrails

**Location:** `services/security-guardrails:8009`

- Validates answer for security violations
- Checks for PII, sensitive data
- Applies content filters
- Returns cleaned response if needed

#### STAGE 7: Response Assembly

**Components:**
- Answer text
- Sources array (all retrieved documents, not just cited)
- Citations (documents explicitly referenced by LLM)
- Metrics (timing, source distribution, etc.)
- Security warnings (if any)

#### STAGE 8: Redis Caching

**Location:** `services/api/routes/rag.py` → Redis storage

**Purpose:** Enable response retrieval after page refresh

**Process:**
1. Store complete `RagResponse` in Redis
2. Key: `request_id`
3. TTL: 30 minutes
4. Frontend polls `/v1/rag/response/{request_id}` to retrieve

#### STAGE 9: Return Response

**Response Format:**
```json
{
  "answer": "Generated answer text...",
  "sources": [
    {
      "id": "chunk_123",
      "content": "Source text...",
      "title": "Document Title",
      "score": 0.85,
      "origin_tool": "rag",
      "source_type": "rag",
      "cited": true,
      "doc_id": "research_https://..."
    }
  ],
  "citations": [...],
  "metrics": {
    "total_latency_ms": 1234,
    "retrieval_ms": 200,
    "llm_generation_ms": 1000,
    "source_distribution": {
      "rag": 10,
      "research": 5,
      "web": 5,
      "kg": 0
    }
  },
  "request_id": "abc123..."
}
```

---

### 4. Frontend Response Handling

**Location:** `frontend/src/components/chat/ChatInterface.tsx`

**Process:**
1. Receives response from API Gateway
2. Stores `request_id` in `sessionStorage` (for polling)
3. Adds message to chat store
4. Displays answer with sources
5. If request times out, starts polling for response

**Polling Mechanism:**
```typescript
// Poll for response if request timed out
useEffect(() => {
  if (pendingRequestIds.length > 0) {
    const interval = setInterval(async () => {
      for (const requestId of pendingRequestIds) {
        const response = await api.getResponse(requestId);
        if (response) {
          // Response found in Redis, add to chat
          addMessage(response);
          removePendingRequestId(requestId);
        }
      }
    }, 2000); // Poll every 2 seconds
    
    return () => clearInterval(interval);
  }
}, [pendingRequestIds]);
```

---

## 🔍 Detailed Service Interactions

### Vector Search Flow

```
rag-api-v1
  ↓ POST /embed
embedding-service:8006
  ↓ Returns embedding vector
rag-api-v1
  ↓ POST /search (with embedding)
vector-db:8005
  ↓ Returns top-k results
rag-api-v1
```

### Knowledge Graph Flow

```
rag-api-v1
  ↓ POST /expand (with query)
knowledge-graph:8007
  ↓ Returns related entities & documents
rag-api-v1
```

### Web Search Flow

```
rag-api-v1
  ↓ POST /search (with query)
web-search:8008
  ↓ Forwards to SearXNG
SearXNG (external)
  ↓ Returns web results
web-search:8008
  ↓ Returns formatted results
rag-api-v1
```

### LLM Generation Flow

```
rag-api-v1
  ↓ Builds prompt with context
  ↓ POST /api/generate
ollama:11434
  ↓ Streams tokens
rag-api-v1
  ↓ Assembles complete response
```

---

## 📊 Data Flow Diagram

```
┌─────────────┐
│   Frontend  │
│  (React)    │
└──────┬──────┘
       │ POST /api/ask
       │ {query, top_k, config...}
       ↓
┌──────────────────┐
│  API Gateway     │
│  (Flask)         │
└──────┬───────────┘
       │ POST /v1/rag/query
       ↓
┌──────────────────┐
│  RAG API v1      │
│  (FastAPI)       │
└──────┬───────────┘
       │
       ├─→ Embedding Service → Vector DB (semantic search)
       ├─→ Knowledge Graph (entity expansion)
       ├─→ Web Search (external sources)
       │
       ↓ (top-k results)
       │
       ├─→ Recency Gate (filter stale)
       ├─→ Weighted Rerank (prioritize RAG/Research)
       │
       ↓ (final context)
       │
       ├─→ Build Prompt
       ├─→ Ollama (LLM generation)
       ├─→ Security Guardrails
       │
       ↓
       │ Store in Redis (request_id)
       │
       ↓
┌──────────────────┐
│  API Gateway     │
│  (adds metrics)  │
└──────┬───────────┘
       │
       ↓
┌─────────────┐
│   Frontend  │
│  (displays) │
└─────────────┘
```

---

## 🔑 Key Concepts

### Request ID
- Generated by frontend (UUID)
- Used for Redis caching
- Enables response retrieval after page refresh
- Stored in `sessionStorage` for polling

### Source Types
- **RAG:** Documents from vector database (uploaded/ingested)
- **Research:** Auto-discovered research articles (stored in vector DB with `research_` prefix)
- **Web:** External web search results
- **KG:** Knowledge graph entities/relationships

### Weighted Scoring
- Prioritizes internal sources (RAG/Research) over external (Web)
- Ensures quality, trusted sources appear first
- Applied during reranking stage

### Redis Caching
- Stores complete response for 30 minutes
- Key: `request_id`
- Enables retrieval after timeout/page refresh
- Frontend polls `/v1/rag/response/{request_id}`

### Session Storage
- Stores `pendingRequestIds` across page refreshes
- Stores `messages` for conversation persistence
- Cleared when tab closes (unlike `localStorage`)

---

## ⚡ Performance Characteristics

### Typical Latencies (Balanced Preset)

- **Query Processing:** ~50ms
- **Vector Search:** ~200ms
- **Knowledge Graph:** ~100ms
- **Web Search:** ~2-5s (if enabled)
- **Reranking:** ~50ms
- **LLM Generation:** ~1-3s (for 500 tokens)
- **Total:** ~2-5s (without web search), ~5-10s (with web search)

### Maximum Preset Latencies

- **Web Search:** ~30-60s (20 docs × 5 pages)
- **LLM Generation:** ~5-15 minutes (1500 tokens, 20 context chunks)
- **Total:** ~10-20 minutes

---

## 🛡️ Security & Guardrails

1. **Input Validation:** API Gateway validates request format
2. **ACL Filtering:** Documents filtered by user permissions
3. **Security Guardrails:** Answer validated for PII/sensitive data
4. **Citation Validation:** Detects hallucinated citations
5. **Query Sanitization:** Removes potentially harmful content

---

## 📝 Related Documentation

- [Infrastructure & Services Reference](./INFRASTRUCTURE_SERVICES_REFERENCE.md)
- [Architecture Overview](./architecture/ARCHITECTURE.md)
- [Security Integration](./security/SECURITY_INTEGRATION.md)

---

**Last Updated:** November 17, 2025

