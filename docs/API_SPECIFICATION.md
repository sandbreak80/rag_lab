# RAG Lab API v1 - External Integration Specification

**Version:** 2.5.0-chunk-display  
**Base URL:** `http://16.146.36.90:3000/api/v1` (via nginx) or `http://16.146.36.90:8080/v1` (direct)  
**Protocol:** HTTP REST API  
**Format:** JSON  
**Authentication:** Currently none (configure for production)

---

## Table of Contents

1. [Overview](#overview)
2. [Base URL & Routing](#base-url--routing)
3. [Core Endpoints](#core-endpoints)
4. [Request/Response Models](#requestresponse-models)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Rate Limits](#rate-limits)

---

## Overview

The RAG Lab API v1 provides a complete Retrieval-Augmented Generation (RAG) system with:
- Document ingestion and storage
- Semantic search with multiple strategies (vector, BM25, hybrid, knowledge graph)
- LLM-powered question answering
- A/B testing capabilities
- Full observability (traces, metrics, logs)

---

## Base URL & Routing

### Via Nginx (Recommended)
```
Base URL: http://16.146.36.90:3000/api/v1
```

### Direct Access
```
Base URL: http://16.146.36.90:8080/v1
```

**Note:** Nginx routes `/api/v1/*` → `rag-api-v1:8080/v1/*`

---

## Core Endpoints

### 1. RAG Query (Main Endpoint)

**POST** `/v1/rag/query`

Execute a RAG query with full observability.

#### Request Body

```json
{
  "query": "What is the refund policy for enterprise customers?",
  "user_id": "user_123",
  "groups": ["sales", "tier2_support"],
  "dept": "customer_success",
  "top_k": 8,
  "max_tokens": 2000,
  "context_window": 8192,
  "model": "qwen2.5:14b",
  "temperature": 0.7,
  "use_hybrid": true,
  "use_reranking": true,
  "use_web_search": true,
  "web_search_docs": 10,
  "use_graph": false,
  "enable_research": false,
  "request_id": "optional-client-request-id"
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | User's natural language query |
| `user_id` | string | ✅ | - | User identifier for AuthZ |
| `groups` | string[] | ❌ | `[]` | User's group memberships |
| `dept` | string | ❌ | `null` | User's department |
| `top_k` | integer | ❌ | `8` | Number of results to return (1-50) |
| `max_tokens` | integer | ❌ | `512` | Max tokens for LLM response (100-32768) |
| `context_window` | integer | ❌ | `4096` | Total context window size (1024-32768) |
| `model` | string | ❌ | `null` | LLM model (e.g., "qwen2.5:14b", "llama3.1:8b") |
| `temperature` | float | ❌ | `null` | LLM temperature (0.0-2.0) |
| `use_hybrid` | boolean | ❌ | `false` | Enable hybrid search (vector + BM25) |
| `use_reranking` | boolean | ❌ | `false` | Enable reranking |
| `use_web_search` | boolean | ❌ | `true` | Enable web search |
| `web_search_docs` | integer | ❌ | `20` | Number of web search results (1-50) |
| `use_graph` | boolean | ❌ | `false` | Enable knowledge graph search |
| `use_query_expansion` | boolean | ❌ | `false` | Enable query expansion |
| `use_bm25` | boolean | ❌ | `false` | Enable BM25 keyword search |
| `enable_research` | boolean | ❌ | `false` | Enable research agent sources |
| `request_id` | string | ❌ | `null` | Client-provided request ID for correlation |

#### Response

```json
{
  "answer": "Our enterprise refund policy allows...",
  "citations": [
    {
      "doc_id": "policy_v2.3",
      "version": "2.3",
      "chunk_id": "chunk_42",
      "char_range": [120, 456],
      "source_uri": "https://docs.example.com/policies/refunds"
    }
  ],
  "sources": [
    {
      "doc_id": "policy_v2.3",
      "chunk_id": "chunk_42",
      "score": 0.95,
      "origin_tool": "rag",
      "source_type": "rag",
      "content": "Full chunk content here...",
      "title": "Refund Policy",
      "url": "https://docs.example.com/policies/refunds",
      "cited": true,
      "rank": 1
    }
  ],
  "artifacts": {
    "planner": {
      "route": "hybrid",
      "budgets_applied": {}
    },
    "retrieval_log": {
      "total_retrieved": 15,
      "acl_filtered_count": 3,
      "timing_ms": 45.2
    },
    "stage_timings": {
      "acl_ms": 2.1,
      "embedding_ms": 15.3,
      "vector_db_ms": 25.4,
      "web_ms": 120.5,
      "rerank_ms": 45.2,
      "llm_ms": 2340.8,
      "prompt_size": {
        "system_prompt_tokens": 450,
        "user_query_tokens": 25,
        "retrieved_docs_tokens": 3200,
        "prompt_tokens_estimated": 3675,
        "context_window": 8192,
        "max_tokens": 2000,
        "available_for_response": 4517,
        "prompt_utilization_pct": 44.9,
        "prompt_fits": true
      }
    }
  },
  "metrics": {
    "latency_ms": 2547.3,
    "tokens_in": 3675,
    "tokens_out": 512,
    "model": "qwen2.5:14b",
    "cost_usd": 0.000234,
    "total_tokens": 4187
  },
  "security_status": "ok",
  "request_id": "req_abc123",
  "trace_id": "trace_xyz789",
  "contract_version": "1.0.0"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated answer text |
| `citations` | array | Sentence-level citations with doc_id, chunk_id, char_range |
| `sources` | array | All retrieved sources with full chunk content |
| `artifacts` | object | Pipeline artifacts (planner, retrieval_log, stage_timings) |
| `metrics` | object | Performance metrics (latency, tokens, cost) |
| `security_status` | string | "ok", "degraded", or "blocked" |
| `request_id` | string | Request correlation ID |
| `trace_id` | string | Distributed trace ID |
| `contract_version` | string | API contract version |

---

### 2. Get Query Response (Async)

**GET** `/v1/rag/response/{request_id}`

Retrieve a previously submitted query response (if using async pattern).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `request_id` | string | Request ID from initial query |

#### Response

Same as `/v1/rag/query` response.

---

### 3. Upload Documents

**POST** `/v1/documents`

Upload and ingest documents into the knowledge base.

#### Request (multipart/form-data)

```
Content-Type: multipart/form-data

files: [File, File, ...]
perms_tag: "public" | "secret" | "confidential"
metadata: (optional JSON string)
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `files` | File[] | ✅ | One or more files to upload |
| `perms_tag` | string | ❌ | Permission tag for ACL (default: "public") |
| `metadata` | string | ❌ | Optional JSON metadata |

#### Response

```json
{
  "document_ids": ["doc_123", "doc_456"],
  "chunks_created": 42,
  "status": "success",
  "message": "Documents ingested successfully"
}
```

---

### 4. List Documents

**GET** `/v1/documents`

List all documents in the knowledge base.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | ❌ | Max results (default: 100) |
| `offset` | integer | ❌ | Pagination offset (default: 0) |

#### Response

```json
{
  "documents": [
    {
      "doc_id": "doc_123",
      "file_name": "policy.pdf",
      "chunk_count": 15,
      "created_at": "2025-11-19T10:00:00Z",
      "metadata": {}
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

---

### 5. A/B Testing

#### 5.1. Get Prompt Library

**GET** `/v1/ab-testing/prompts`

Get available test prompts.

#### Response

```json
[
  {
    "id": "prompt_1",
    "title": "Simple Factual Question",
    "prompt": "What is RAG?",
    "category": "factual",
    "complexity": "simple",
    "expectedSources": 3
  }
]
```

#### 5.2. Run A/B Test

**POST** `/v1/ab-testing/run`

Start an A/B test comparing two configurations.

#### Request Body

```json
{
  "prompt": "What are the differences between Graph RAG, Recursive RAG, and Naive RAG?",
  "config_a": {
    "model": "qwen2.5:14b",
    "temperature": 0.7,
    "maxTokens": 2000,
    "contextWindow": 8192,
    "topK": 10,
    "useHybrid": true,
    "useReranking": true
  },
  "config_b": {
    "model": "llama3.1:8b",
    "temperature": 0.5,
    "maxTokens": 1500,
    "contextWindow": 4096,
    "topK": 8,
    "useHybrid": false,
    "useReranking": false
  },
  "run_parallel": false,
  "auto_grade": true
}
```

#### Response

```json
{
  "test_id": "test_abc123",
  "status": "running",
  "message": "A/B test started. Poll /result/{test_id} for results."
}
```

#### 5.3. Get A/B Test Result

**GET** `/v1/ab-testing/result/{test_id}`

Get A/B test results (poll this endpoint after starting a test).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_id` | string | Test ID from `/run` response |

#### Response

```json
{
  "test_id": "test_abc123",
  "prompt": "What are the differences...",
  "result_a": {
    "answer": "Configuration A response...",
    "sources": [...],
    "metrics": {...}
  },
  "result_b": {
    "answer": "Configuration B response...",
    "sources": [...],
    "metrics": {...}
  },
  "metrics_a": {...},
  "metrics_b": {...},
  "grader_result": {
    "response_a": {
      "overall_score": 0.85,
      "scores": {
        "answer_quality": 0.9,
        "relevance": 0.85,
        "faithfulness": 0.8
      }
    },
    "response_b": {
      "overall_score": 0.78,
      "scores": {...}
    },
    "winner": "A"
  },
  "status": "graded"
}
```

#### 5.4. Grade A/B Test

**POST** `/v1/ab-testing/grade/{test_id}`

Trigger auto-grading for an existing A/B test result.

---

### 6. Health & Info

#### 6.1. Health Check

**GET** `/health`

Check API health status.

#### Response

```json
{
  "status": "healthy",
  "service": "rag-api-v1",
  "version": "2.5.0-chunk-display"
}
```

#### 6.2. Version Info

**GET** `/version`

Get API version information.

#### Response

```json
{
  "service": "rag-api-v1",
  "version": "2.5.0-chunk-display",
  "build_date": "2025-11-17",
  "status": "healthy"
}
```

#### 6.3. API Info

**GET** `/`

Get API information and available endpoints.

---

## Request/Response Models

### Source Object

```typescript
interface Source {
  doc_id: string;           // Document identifier
  chunk_id: string;         // Chunk identifier
  score: number;            // Relevance score (0.0-1.0)
  origin_tool: string;      // "rag" | "web_search" | "research"
  source_type: string;      // "rag" | "web" | "research"
  content: string;          // Full chunk content
  title: string;            // Document title
  url: string;              // Source URL (if web source)
  cited: boolean;           // Whether LLM cited this source
  rank: number;             // Rank in results (1-based)
}
```

### Metrics Object

```typescript
interface Metrics {
  latency_ms: number;       // Total latency in milliseconds
  tokens_in: number;        // Input tokens
  tokens_out: number;       // Output tokens
  total_tokens: number;     // Total tokens
  model: string;            // LLM model used
  cost_usd: number;         // Estimated cost in USD
}
```

### Stage Timings Object

```typescript
interface StageTimings {
  acl_ms: number;           // Authorization latency
  embedding_ms: number;     // Embedding generation latency
  vector_db_ms: number;     // Vector search latency
  web_ms: number;           // Web search latency
  rerank_ms: number;        // Reranking latency
  llm_ms: number;           // LLM generation latency
  prompt_size: {
    system_prompt_tokens: number;
    user_query_tokens: number;
    retrieved_docs_tokens: number;
    prompt_tokens_estimated: number;
    context_window: number;
    max_tokens: number;
    available_for_response: number;
    prompt_utilization_pct: number;
    prompt_fits: boolean;
  };
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created (document upload) |
| `400` | Bad Request (invalid parameters) |
| `404` | Not Found (resource doesn't exist) |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

### Common Errors

**400 Bad Request**
```json
{
  "detail": "Invalid query parameter: top_k must be between 1 and 50"
}
```

**500 Internal Server Error**
```json
{
  "detail": "LLM service returned an error (HTTP 500): Model loading failed"
}
```

---

## Examples

### Python Example

```python
import requests

BASE_URL = "http://16.146.36.90:3000/api/v1"

# RAG Query
response = requests.post(
    f"{BASE_URL}/rag/query",
    json={
        "query": "What is RAG?",
        "user_id": "presentation_app",
        "groups": [],
        "top_k": 10,
        "max_tokens": 2000,
        "use_hybrid": True,
        "use_reranking": True
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])}")
print(f"Latency: {result['metrics']['latency_ms']}ms")

# Access full chunk content
for source in result['sources']:
    print(f"\nSource: {source['doc_id']}")
    print(f"Score: {source['score']}")
    print(f"Content: {source['content'][:200]}...")  # First 200 chars
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = "http://16.146.36.90:3000/api/v1";

async function queryRAG(query: string) {
  const response = await fetch(`${BASE_URL}/rag/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      user_id: 'presentation_app',
      groups: [],
      top_k: 10,
      max_tokens: 2000,
      use_hybrid: true,
      use_reranking: true
    })
  });

  const result = await response.json();
  return result;
}

// Usage
const result = await queryRAG("What is RAG?");
console.log(result.answer);
console.log(`Found ${result.sources.length} sources`);
```

### cURL Example

```bash
curl -X POST http://16.146.36.90:3000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "user_id": "presentation_app",
    "groups": [],
    "top_k": 10,
    "max_tokens": 2000,
    "use_hybrid": true,
    "use_reranking": true
  }'
```

---

## Rate Limits

Currently no rate limits enforced. Configure for production use.

**Recommended limits:**
- Authenticated users: 100 requests/minute
- Unauthenticated: 10 requests/minute

---

## Available Models

| Model | Size | Use Case | Context Window |
|-------|------|----------|----------------|
| `qwen2.5:14b` | 14B | High quality, complex queries | Up to 32K |
| `llama3.1:8b` | 8B | Balanced quality/speed | Up to 128K |
| `llama3.2:3b` | 3B | Fast responses | Up to 128K |
| `gemma2:9b` | 9B | General purpose | Up to 8K |
| `mistral:7b` | 7B | Fast, efficient | Up to 32K |

---

## Configuration Presets

The API supports configuration presets. Use these common configurations:

### Minimal
```json
{
  "model": "llama3.2:3b",
  "max_tokens": 750,
  "context_window": 4096,
  "top_k": 5,
  "use_hybrid": false,
  "use_reranking": false
}
```

### Fast
```json
{
  "model": "llama3.2:3b",
  "max_tokens": 600,
  "context_window": 4096,
  "top_k": 5,
  "use_hybrid": false,
  "use_reranking": false
}
```

### Balanced
```json
{
  "model": "llama3.1:8b",
  "max_tokens": 2000,
  "context_window": 8192,
  "top_k": 10,
  "use_hybrid": true,
  "use_reranking": true
}
```

### Quality
```json
{
  "model": "qwen2.5:14b",
  "max_tokens": 2500,
  "context_window": 20480,
  "top_k": 15,
  "use_hybrid": true,
  "use_reranking": true,
  "use_web_search": true
}
```

### Maximum
```json
{
  "model": "qwen2.5:14b",
  "max_tokens": 3500,
  "context_window": 24576,
  "top_k": 20,
  "use_hybrid": true,
  "use_reranking": true,
  "use_web_search": true,
  "use_graph": true
}
```

---

## Integration Checklist

- [ ] Determine base URL (nginx vs direct)
- [ ] Set up error handling for 400/500 responses
- [ ] Implement request ID tracking for correlation
- [ ] Handle async responses if needed (poll `/response/{request_id}`)
- [ ] Parse `sources` array for full chunk content
- [ ] Use `metrics` for performance monitoring
- [ ] Check `security_status` for guardrail violations
- [ ] Handle rate limits when implemented

---

## Support

- **API Docs:** `http://16.146.36.90:3000/api/v1/docs` (Swagger UI)
- **Health Check:** `http://16.146.36.90:3000/api/v1/health`
- **Version:** `http://16.146.36.90:3000/api/v1/version`

---

**Last Updated:** November 19, 2025  
**API Version:** 2.5.0-chunk-display  
**Contract Version:** 1.0.0

