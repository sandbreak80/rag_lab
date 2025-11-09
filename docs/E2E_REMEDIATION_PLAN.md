# E2E Test Remediation Implementation Plan

**Status**: Step 1 Complete ✅, Steps 2-6 Ready for Implementation
**Branch**: `otel`
**Goal**: Achieve 12/12 Playwright E2E tests passing

---

## ✅ STEP 1 COMPLETE: OTel Collector Health & Dependencies

### Changes Made
```yaml
otel-collector:
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:13133/"]
    interval: 10s
    timeout: 3s
    retries: 5
    start_period: 5s
  ports:
    - "13133:13133"  # Health endpoint exposed
  environment:
    - GODEBUG=http2server=0

rag-api-v1:
  depends_on:
    otel-collector:
      condition: service_healthy
```

### Deploy
```bash
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel
docker compose up -d otel-collector rag-api-v1
```

**Expected Result**: `/ready` endpoint returns 200 instead of 503

---

## 📋 STEP 2: Add UI Components with data-testid Attributes

### File to Create/Update: `frontend/src/components/Chat.tsx`

```typescript
import React, { useState } from "react";
import { askRagV1 } from "../services/ragApiV1";

export default function Chat() {
  const [q, setQ] = useState("");
  const [resp, setResp] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function onSend() {
    setLoading(true);
    try {
      const r = await askRagV1({ query: q, user_id: "demo", groups: [], top_k: 8 });
      setResp(r);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div data-testid="chat-root">
      {/* Chat Input */}
      <textarea
        data-testid="chat-input"
        placeholder="Ask RAG…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      {/* Send Button */}
      <button
        data-testid="chat-send"
        onClick={onSend}
        disabled={loading || !q.trim()}
      >
        {loading ? "Sending…" : "Send"}
      </button>

      {/* Answer Display */}
      {resp?.answer && (
        <div data-testid="answer">
          {resp.answer}
        </div>
      )}

      {/* Provenance Badges */}
      {resp && (
        <div data-testid="provenance-badges">
          <span data-testid="badge-origin-tool">
            {resp?.provenance?.origin_tool || "RAG"}
          </span>
          <span data-testid="badge-security">
            {resp?.security_status || "ok"}
          </span>
          <span data-testid="badge-recency">
            {String(resp?.artifacts?.recency?.passed ?? false)}
          </span>
          <span data-testid="badge-acl">
            {resp?.artifacts?.retrieval_log?.acl_filtered_count ?? 0}
          </span>
        </div>
      )}

      {/* Metrics/Trace Row */}
      {resp?.trace_id && (
        <div data-testid="metrics-row">
          <span data-testid="trace-id">{resp.trace_id}</span>
          <span data-testid="tokens-in">{resp?.metrics?.tokens_in ?? 0}</span>
          <span data-testid="tokens-out">{resp?.metrics?.tokens_out ?? 0}</span>
          <span data-testid="cost-usd">{resp?.metrics?.cost_usd ?? 0}</span>
          <span data-testid="latency-ms">{resp?.metrics?.latency_ms ?? 0}</span>
        </div>
      )}

      {/* Citations Drawer */}
      {Array.isArray(resp?.citations) && resp.citations.length > 0 && (
        <details data-testid="citations-drawer">
          <summary data-testid="citations-open">
            Citations ({resp.citations.length})
          </summary>
          <ul>
            {resp.citations.map((c: any, i: number) => (
              <li key={i} data-testid="citation-item">
                <span data-testid="citation-origin">{c.origin_tool}</span> ·
                <a
                  data-testid="citation-link"
                  href={c.source_uri}
                  target="_blank"
                  rel="noreferrer"
                >
                  {c.doc_id}@{c.version}#{c.chunk_id}
                </a>
                <span data-testid="citation-range">
                  {JSON.stringify(c.char_range)}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* Guardrail Status */}
      {resp && (
        <div data-testid="guardrail-status">
          {resp.security_status || "ok"}
        </div>
      )}

      {/* JSON Artifacts Download */}
      {resp?.artifacts && (
        <button
          data-testid="json-inspector-download"
          onClick={() => {
            const blob = new Blob(
              [JSON.stringify(resp.artifacts, null, 2)],
              { type: "application/json" }
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "artifacts.json";
            a.click();
            URL.revokeObjectURL(url);
          }}
        >
          Download Artifacts (A–G)
        </button>
      )}
    </div>
  );
}
```

### Deploy
```bash
docker compose up -d --build frontend
```

---

## 📋 STEP 3: Update Nginx to Forward OTel Headers

### File to Update: `frontend/nginx.conf`

Add at the top (before `server` block):
```nginx
map $http_traceparent $traceparent { default $http_traceparent; }
map $http_tracestate  $tracestate  { default $http_tracestate;  }
```

Update `/api/` location block:
```nginx
location /api/ {
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header traceparent $traceparent;
  proxy_set_header tracestate $tracestate;
  proxy_http_version 1.1;

  # Strip /api prefix
  rewrite ^/api/(.*)$ /$1 break;
  proxy_pass http://rag-api-v1:8080;

  # No caching for JSON responses
  add_header Cache-Control "no-store";
}
```

### Deploy
```bash
docker compose up -d --build frontend
```

---

## 📋 STEP 4: Add Dependency Checks to /ready Endpoint

### File to Create: `services/api/routes/health.py`

```python
import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Dict

router = APIRouter()

def tcp_probe(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quick TCP connection check"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def http_probe(url: str, timeout: float = 1.0) -> bool:
    """Quick HTTP GET check"""
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500
    except:
        return False

@router.get("/live")
def liveness():
    """Always returns 200 if process is running"""
    return {"status": "alive"}

@router.get("/ready")
def readiness():
    """Returns 200 only when all dependencies are healthy"""
    deps = {
        "vector_db": tcp_probe("vector-db", 8005),
        "searxng": http_probe("http://searxng:8080/"),
        "ollama": http_probe("http://ollama:11434/api/tags"),
        "otel_collector": http_probe("http://otel-collector:13133/"),
    }

    all_ok = all(deps.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(
        {
            "status": "ready" if all_ok else "degraded",
            "dependencies": deps
        },
        status_code=status_code
    )

@router.get("/health")
def health():
    """Combined health check"""
    deps = {
        "vector_db": tcp_probe("vector-db", 8005),
        "searxng": http_probe("http://searxng:8080/"),
        "ollama": http_probe("http://ollama:11434/api/tags"),
        "otel_collector": http_probe("http://otel-collector:13133/"),
    }

    all_ok = all(deps.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "dependencies": deps
    }
```

### Update: `services/api/app.py`

```python
from routes import health

app.include_router(health.router, tags=["health"])
```

### Deploy
```bash
docker compose up -d --build rag-api-v1
```

---

## 📋 STEP 5: Performance Optimization (Optional but Recommended)

### Update: `docker-compose.yml`

Add to `rag-api-v1` environment:
```yaml
environment:
  # ... existing vars ...
  RAG_LLM_MODEL: "llama3.2:3b"  # Faster model
  RAG_LLM_MAX_TOKENS: "256"      # Cap tokens for tests
```

### Deploy
```bash
docker compose up -d rag-api-v1
```

---

## 📋 STEP 6: Run E2E Tests and Validate

### Commands
```bash
# Pull latest
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel

# Sanity check endpoints
curl -s http://16.146.148.184:3000/live | jq
curl -s http://16.146.148.184:3000/ready | jq
curl -s -X POST http://16.146.148.184:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"demo","groups":[]}' | jq

# Run E2E test suite
bash scripts/run_e2e.sh
```

### Success Criteria
- ✅ `/ready` returns 200 with all deps healthy
- ✅ 12/12 Playwright tests pass
- ✅ HTML + JUnit reports generated
- ✅ P95 latency < 3.5s (with fast model)
- ✅ Citations/provenance/metrics visible in UI
- ✅ JSON artifacts downloadable
- ✅ Nginx forwards traceparent/tracestate

---

## 📦 Files to Create/Modify Summary

### New Files
1. `services/api/routes/health.py` - Dependency health checks
2. `frontend/src/components/Chat.tsx` - UI with data-testids

### Modified Files
1. `docker-compose.yml` - ✅ OTel healthcheck (done)
2. `frontend/nginx.conf` - OTel header forwarding
3. `services/api/app.py` - Include health router

---

## 🚀 Quick Deploy Script

```bash
#!/bin/bash
set -euo pipefail

echo "Deploying E2E Test Fixes..."

# Step 1: Already deployed (OTel Collector)
echo "✅ Step 1: OTel Collector health (completed)"

# Step 2-4: Deploy API and Frontend changes
echo "Building and deploying services..."
docker compose up -d --build rag-api-v1 frontend

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Step 5: Sanity checks
echo "Running sanity checks..."
curl -sf http://localhost:3000/live | jq
curl -sf http://localhost:3000/ready | jq

# Step 6: Run E2E tests
echo "Running E2E test suite..."
bash scripts/run_e2e.sh

echo "✅ E2E Test Fixes Deployed!"
```

---

**Next Action**: Implement Steps 2-6 to achieve 12/12 passing tests.

