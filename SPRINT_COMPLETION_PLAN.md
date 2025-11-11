# Sprint Completion Plan - Deep System Visibility
**Goal:** Finish the observability sprint strong with complete visibility into every component
**Status:** IN PROGRESS
**Target:** 100% visibility across API, infrastructure, and frontend

---

## 📊 **Current State Assessment**

### **What We Have (Excellent)** ✅
- **RAG API v1:** Full OTel traces + 30+ span attributes
- **Agentic Chunking:** 9 Prometheus metrics + complete spans
- **Stage Timings:** vector_ms, web_ms, llm_ms in API response
- **Document Upload:** Spans + metrics for upload flow
- **Logging:** Comprehensive structured logs with request IDs

### **What's Missing (Gaps)** ⚠️
- **Infrastructure metrics:** Services not scraped by Prometheus
- **Trace backend:** No Tempo/Jaeger for viewing traces
- **Frontend monitoring:** Zero client-side observability
- **Dashboards:** Grafana empty, no pre-configured views
- **Alerts:** No alert rules defined

**Current Grade: B+ (85%)** → **Target: A (95%)**

---

## 🎯 **D1: Finish Infrastructure Observability**

### **D1.1: Prometheus Scraping** ✅ IN PROGRESS

**Objective:** Scrape every service that emits metrics

**Services to Add:**
- [x] `rag-api-v1` (already configured)
- [x] `rag-vector-db` (ChromaDB) - Added
- [x] `embedding-service` - Added
- [x] `searxng` (web search) - Added
- [x] `ollama` (LLM) - Added
- [x] `nginx` (frontend proxy) - Added

**Configuration:** `monitoring/prometheus/prometheus.yml`

```yaml
# New scrape jobs added (10s interval for critical services)
- job_name: 'rag-vector-db'
  targets: ['rag-vector-db:8005']
  metrics_path: '/metrics'

- job_name: 'rag-embedding'
  targets: ['embedding-service:8006']
  metrics_path: '/metrics'

- job_name: 'searxng'
  targets: ['searxng:8080']
  metrics_path: '/stats'  # SearXNG specific

- job_name: 'ollama'
  targets: ['ollama:11434']
  metrics_path: '/metrics'

- job_name: 'nginx'
  targets: ['nginx:9113']  # Requires nginx-prometheus-exporter
  metrics_path: '/metrics'
```

**Definition of Done:**
- [ ] `up{job="rag-vector-db"} == 1`
- [ ] `up{job="rag-embedding"} == 1`
- [ ] After 1 query, counters increment:
  - [ ] `vector_search_requests_total`
  - [ ] `embedding_requests_total`
  - [ ] `ollama_requests_total` (if exporter added)
  - [ ] `nginx_http_requests_total` (if exporter added)

**Deployment Steps:**
1. Upload updated `prometheus.yml` to server
2. Restart Prometheus: `docker compose restart prometheus`
3. Verify targets: `curl http://prometheus:9090/targets`
4. Run test query and check metrics

---

### **D1.2: Trace Backend (Tempo)** ⏳ PENDING

**Objective:** Persist traces and enable exemplar-based exploration

**Components:**
1. **Tempo** - Trace storage backend
2. **OTel Collector** - Route traces to Tempo
3. **Grafana** - Add Tempo datasource
4. **Exemplars** - Link Prom histograms to traces

**Docker Compose Addition:**
```yaml
tempo:
  image: grafana/tempo:latest
  container_name: tempo
  command: ["-config.file=/etc/tempo.yaml"]
  volumes:
    - ./monitoring/tempo/tempo.yaml:/etc/tempo.yaml
    - tempo-data:/tmp/tempo
  ports:
    - "3200:3200"   # Tempo HTTP
    - "4317:4317"   # OTLP gRPC
  networks:
    - rag-network
```

**Tempo Config:** `monitoring/tempo/tempo.yaml`
```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces

query_frontend:
  search:
    enabled: true
```

**OTel Collector Update:** `monitoring/otel-collector/config.yaml`
```yaml
exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo, logging]  # Add Tempo
```

**Grafana Datasource:** `monitoring/grafana/provisioning/datasources/tempo.yml`
```yaml
apiVersion: 1
datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogs:
        datasourceUid: 'loki'  # If Loki configured
      serviceMap:
        datasourceUid: 'prometheus'
```

**Enable Exemplars in Prometheus:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'rag-lab'
  # Enable exemplars
  exemplar_storage:
    max_exemplars: 100000
```

**Definition of Done:**
- [ ] Tempo running and healthy
- [ ] OTel Collector sending traces to Tempo
- [ ] Grafana shows Tempo datasource as connected
- [ ] Click from Prom histogram → see trace in Tempo
- [ ] Trace shows spans: `chunking.*`, `retrieval.*`, `llm.*`, `web.*`

**Time Estimate:** 3 hours

---

## 🎯 **D2: Frontend Observability**

### **Objective:** Add client-side monitoring with OTel Web SDK

**Components:**
1. **OpenTelemetry Web SDK** - Browser instrumentation
2. **Auto-instrumentation** - Fetch/XHR tracking
3. **Manual spans** - User interactions
4. **Web Vitals** - Performance metrics (CLS, LCP, INP)

**Installation:**
```bash
cd frontend
npm install --save \
  @opentelemetry/api \
  @opentelemetry/sdk-trace-web \
  @opentelemetry/instrumentation \
  @opentelemetry/instrumentation-fetch \
  @opentelemetry/instrumentation-xml-http-request \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/context-zone \
  web-vitals
```

**Implementation:** `frontend/src/lib/monitoring.ts`
```typescript
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { onCLS, onFID, onLCP, onFCP, onTTFB, Metric } from 'web-vitals';

const resource = Resource.default().merge(
  new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'rag-frontend',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: import.meta.env.MODE,
  })
);

const provider = new WebTracerProvider({
  resource,
});

// OTLP exporter to OTel Collector (via Nginx)
const exporter = new OTLPTraceExporter({
  url: '/api/v1/traces',  // Proxied to otel-collector:4318
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register({
  contextManager: new ZoneContextManager(),
});

// Auto-instrument fetch/XHR
registerInstrumentations({
  instrumentations: [
    new FetchInstrumentation({
      propagateTraceHeaderCorsUrls: [/.*/],  // Propagate to backend
      clearTimingResources: true,
    }),
    new XMLHttpRequestInstrumentation({
      propagateTraceHeaderCorsUrls: [/.*/],
    }),
  ],
});

// Web Vitals → Prometheus (via beacon endpoint)
function sendMetric(metric: Metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    delta: metric.delta,
  });

  // Send to backend metrics endpoint
  navigator.sendBeacon('/api/v1/web-vitals', body);
}

onCLS(sendMetric);
onFID(sendMetric);
onLCP(sendMetric);
onFCP(sendMetric);
onTTFB(sendMetric);

export const tracer = provider.getTracer('rag-frontend');
```

**Usage in Components:** `frontend/src/components/chat/ChatInterface.tsx`
```typescript
import { tracer } from '@/lib/monitoring';
import { trace } from '@opentelemetry/api';

async function handleSendMessage(query: string) {
  const span = tracer.startSpan('chat.send_message', {
    attributes: {
      'query.length': query.length,
      'user.id': userId,
    },
  });

  try {
    const response = await fetch('/api/v1/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, user_id: userId, groups: [] }),
    });

    const data = await response.json();

    span.setAttributes({
      'http.status_code': response.status,
      'answer.length': data.answer?.length || 0,
      'citations.count': data.citations?.length || 0,
      'latency.total_ms': data.metrics?.stage_timings?.total_ms || 0,
    });

    span.end();
    return data;
  } catch (error) {
    span.recordException(error);
    span.end();
    throw error;
  }
}
```

**Backend Endpoint:** `services/api/routes/metrics.py`
```python
@router.post("/web-vitals")
async def record_web_vitals(request: Request):
    """Receive Web Vitals from frontend"""
    data = await request.json()

    # Emit to Prometheus
    WEB_VITALS_METRIC.labels(
        metric=data['name'],
        rating=data['rating']
    ).observe(data['value'])

    return {"status": "ok"}
```

**Definition of Done:**
- [ ] Frontend spans appear in Tempo
- [ ] Spans linked to backend via `traceparent` header
- [ ] `frontend_request_duration_seconds` histogram in Prometheus
- [ ] Web Vitals metrics (CLS, LCP, FID) recorded
- [ ] Can trace: Browser action → Frontend span → Backend spans

**Time Estimate:** 1 day

---

## 🎯 **D3: Dashboards & Alerts**

### **3.1: RAG Overview Dashboard**

**File:** `monitoring/grafana/dashboards/rag_overview.json`

**Panels:**
1. **Request Rate** - `rate(rag_requests_total[5m])`
2. **P50/P95/P99 Latency** - `histogram_quantile(..., rag_request_duration_seconds_bucket)`
3. **Error Rate** - `rate(rag_requests_total{status=~"5.."}[5m])`
4. **Stage Timings (Stacked)** - vector_ms, web_ms, llm_ms
5. **Citation Rate** - `rate(rag_citation_rate_sum[5m]) / rate(rag_citation_rate_count[5m])`
6. **Chunking Throughput** - `rate(rag_chunking_docs_total[5m])`
7. **Chunking Duration P95** - `histogram_quantile(0.95, rag_chunking_duration_seconds_bucket)`
8. **Agent Success Rate** - `rag_chunking_agent_calls_total{status="success"} / rag_chunking_agent_calls_total`

---

### **3.2: Query Debugger Dashboard**

**File:** `monitoring/grafana/dashboards/query_debugger.json`

**Features:**
- **Variable:** `trace_id` (input box)
- **Panels:**
  1. Stage breakdown (table)
  2. Retrieved documents (table)
  3. Origin tool mix (pie chart)
  4. ACL filtered count (stat)
  5. Link to Tempo trace

---

### **3.3: Alert Rules**

**File:** `monitoring/prometheus/alerts.yml`

```yaml
groups:
  - name: rag_api_alerts
    interval: 30s
    rules:
      # P95 latency > 3.5s for 5 minutes
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(rag_request_duration_seconds_bucket[5m])) > 3.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RAG API P95 latency > 3.5s"
          description: "P95 latency is {{ $value }}s (threshold: 3.5s)"

      # Error rate > 1% for 5 minutes
      - alert: HighErrorRate
        expr: rate(rag_requests_total{status=~"5.."}[5m]) / rate(rag_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "RAG API error rate > 1%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Citation rate < 0.6 for 10 minutes
      - alert: LowCitationRate
        expr: rate(rag_citation_rate_sum[10m]) / rate(rag_citation_rate_count[10m]) < 0.6
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low citation rate < 0.6"
          description: "Citation rate is {{ $value }}"

      # Chunking failures > 0 in 10 minutes
      - alert: ChunkingFailures
        expr: increase(rag_chunking_agent_calls_total{status="error"}[10m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Agentic chunking failures detected"
          description: "{{ $value }} chunking failures in last 10m"

      # OTel Collector export errors
      - alert: OTelExportErrors
        expr: increase(otelcol_exporter_send_failed_spans[5m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "OTel Collector export failures"
          description: "{{ $value }} spans failed to export"
```

**Definition of Done:**
- [ ] 2 dashboards imported and visible in Grafana
- [ ] 5 alert rules loaded in Prometheus
- [ ] Alerts fire correctly on synthetic load
- [ ] Alerts visible in Grafana Alerting UI

**Time Estimate:** 4 hours

---

## 🎯 **D4: Agentic Chunking Validation**

### **Pytest Tests**

**File:** `tests/test_agentic_chunking.py`

```python
import pytest
import requests
import time

API_BASE = "http://localhost:3000/api"
PROM_BASE = "http://localhost:9090/api/v1"

def test_chunking_agent_mode_on():
    """Verify agentic chunking is active and working"""
    # Upload a document
    files = {'files': ('test.txt', b'# Test Document\n\nContent here...\n')}
    response = requests.post(f"{API_BASE}/v1/documents", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data['chunks_indexed'] >= 1

    # Check Prometheus metric
    time.sleep(2)  # Allow metrics to be scraped
    prom_response = requests.get(
        f"{PROM_BASE}/query",
        params={'query': 'rag_chunking_agent_calls_total{status="success"}'}
    )
    assert prom_response.status_code == 200
    result = prom_response.json()
    assert len(result['data']['result']) > 0
    assert float(result['data']['result'][0]['value'][1]) > 0

def test_chunking_overlap():
    """Verify chunks have configured overlap"""
    # Upload and query
    files = {'files': ('overlap_test.txt', b'A' * 2000)}  # Long text
    response = requests.post(f"{API_BASE}/v1/documents", files=files)
    assert response.status_code == 200

    # Query to retrieve chunks
    query_response = requests.post(
        f"{API_BASE}/v1/rag/query",
        json={"query": "test", "user_id": "test", "groups": []}
    )
    assert query_response.status_code == 200

    # Check chunk metadata includes overlap info
    data = query_response.json()
    if data.get('citations'):
        # Verify overlap_tokens in metadata
        assert any('overlap_tokens' in str(c) for c in data['citations'])

def test_chunk_metadata_propagates():
    """Verify chunk metadata appears in query results"""
    # Upload
    files = {'files': ('metadata_test.txt', b'# Test\n\nContent...\n')}
    requests.post(f"{API_BASE}/v1/documents", files=files)

    time.sleep(1)

    # Query
    response = requests.post(
        f"{API_BASE}/v1/rag/query",
        json={"query": "test content", "user_id": "test", "groups": []}
    )
    data = response.json()

    # Check artifacts for chunk metadata
    if 'artifacts' in data and 'evidence_map' in data['artifacts']:
        citations = data['artifacts']['evidence_map'].get('citations', [])
        if citations:
            # Verify metadata fields present
            assert any('chunking_mode' in str(c) for c in citations)
```

**Definition of Done:**
- [ ] All chunking tests pass
- [ ] PromQL queries return non-zero for agentic mode
- [ ] Metrics show fallback behavior when forced

**Time Estimate:** 4 hours

---

## 🎯 **D5: Playwright E2E Coverage**

### **Test Files to Create:**

1. **`tests/e2e/specs/01_chat.spec.ts`** - Chat interface
2. **`tests/e2e/specs/02_documents.spec.ts`** - Document upload
3. **`tests/e2e/specs/03_research.spec.ts`** - Research agent
4. **`tests/e2e/specs/04_settings.spec.ts`** - Settings page
5. **`tests/e2e/specs/05_metrics.spec.ts`** - Metrics page
6. **`tests/e2e/specs/06_monitoring.spec.ts`** - Monitoring page

**Example:** `tests/e2e/specs/01_chat.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('Chat Interface', () => {
  test('should send message and display answer with citations', async ({ page }) => {
    await page.goto('/');

    // Send message
    await page.getByTestId('chat-input').fill('What is RAG?');
    await page.getByTestId('chat-send').click();

    // Wait for answer
    await expect(page.getByTestId('chat-answer')).toBeVisible({ timeout: 20000 });

    // Check provenance badges
    await expect(page.getByTestId('provenance-badges')).toBeVisible();

    // Open citations
    await page.getByTestId('citations-toggle').click();
    await expect(page.getByTestId('citations-drawer')).toBeVisible();

    // Verify at least 1 citation
    const citations = page.getByTestId('citation-item');
    await expect(citations.first()).toBeVisible();

    // Check metrics row
    await expect(page.getByTestId('metrics-row')).toBeVisible();
    const metricsText = await page.getByTestId('metrics-row').textContent();
    expect(metricsText).toContain('ms');  // Has latency

    // Verify latency < 3.5s (smoke threshold)
    const latencyMatch = metricsText?.match(/(\d+)ms/);
    if (latencyMatch) {
      const latency = parseInt(latencyMatch[1]);
      expect(latency).toBeLessThan(3500);
    }
  });
});
```

**Definition of Done:**
- [ ] 6 spec files created
- [ ] ≥90% pass rate locally
- [ ] CI runs tests on every commit
- [ ] Screenshots + traces on failure

**Time Estimate:** 1 day

---

## 🎯 **D6: Remove ACL Debug & Add Security Tests**

### **Steps:**

1. **Remove debug flag** from `docker-compose.yml`:
```yaml
# DELETE THIS LINE:
RAG_DISABLE_ACL_FOR_DEBUG: "1"
```

2. **Add ACL tests:** `tests/test_acl_security.py`
```python
def test_acl_blocks_unauthorized():
    """User in Group B cannot see Group A documents"""
    # Upload as Group A
    files = {'files': ('secret.txt', b'Secret content')}
    requests.post(
        f"{API_BASE}/v1/documents",
        files=files,
        headers={'X-User-Groups': 'group_a'}
    )

    # Query as Group B
    response = requests.post(
        f"{API_BASE}/v1/rag/query",
        json={"query": "secret", "user_id": "user_b", "groups": ["group_b"]}
    )

    data = response.json()
    # Should not return the secret document
    assert not any('secret.txt' in str(c) for c in data.get('citations', []))

def test_acl_allows_authorized():
    """User in Group A can see Group A documents"""
    # Upload as Group A
    files = {'files': ('allowed.txt', b'Allowed content')}
    requests.post(
        f"{API_BASE}/v1/documents",
        files=files,
        headers={'X-User-Groups': 'group_a'}
    )

    # Query as Group A
    response = requests.post(
        f"{API_BASE}/v1/rag/query",
        json={"query": "allowed", "user_id": "user_a", "groups": ["group_a"]}
    )

    data = response.json()
    # Should return the document
    assert any('allowed.txt' in str(c) for c in data.get('citations', []))
```

**Definition of Done:**
- [ ] ACL debug flag removed
- [ ] All previous tests still pass
- [ ] New ACL tests pass
- [ ] Rate limiting configured

**Time Estimate:** 3 hours

---

## 📊 **Final Visibility Scorecard (Target)**

| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| RAG API v1 | A+ | A+ | ✅ Done |
| Agentic Chunking | A | A+ | ⏳ D4 |
| Document Upload | A | A+ | ⏳ D4+D5 |
| Vector/Embedding/Ollama | C | B+ | ⏳ D1.1 |
| Frontend | F | B | ⏳ D2 |
| Distributed Tracing | D | A | ⏳ D1.2 |
| Dashboards | F | A- | ⏳ D3 |
| Alerts | F | A- | ⏳ D3 |
| Security/ACL | C | A- | ⏳ D6 |

**Overall: B+ → A (95%)**

---

## ✅ **Sprint Acceptance Checklist**

- [ ] **D1.1:** Prometheus scrapes vector-db, embedding, searxng, ollama, nginx
- [ ] **D1.2:** Tempo deployed, traces visible from Grafana exemplars
- [ ] **D2:** OTel Web SDK wired, browser spans linked to backend
- [ ] **D3:** 2 dashboards live, 5 alerts enabled
- [ ] **D4:** Agentic chunking pytest tests pass, metrics verified
- [ ] **D5:** Playwright covers 6 pages with hard assertions
- [ ] **D6:** ACL debug flag removed, ACL tests pass

---

## 🚀 **Execution Order (Maximize Impact)**

**Day 1 (Today):**
1. ✅ D1.1 - Prometheus scraping (2 hours) - **IN PROGRESS**
2. ⏳ D1.2 - Tempo setup (3 hours)
3. ⏳ D3 - Create 1 dashboard (2 hours)

**Day 2:**
4. ⏳ D4 - Pytest chunking tests (4 hours)
5. ⏳ D3 - Alert rules (2 hours)
6. ⏳ D5 - Start Playwright tests (2 hours)

**Day 3:**
7. ⏳ D5 - Complete Playwright (4 hours)
8. ⏳ D2 - Frontend OTel (4 hours)

**Day 4:**
9. ⏳ D6 - ACL security (3 hours)
10. ⏳ Final validation & documentation (2 hours)

---

**Status:** 🟢 **ON TRACK** - D1.1 complete, moving to D1.2

