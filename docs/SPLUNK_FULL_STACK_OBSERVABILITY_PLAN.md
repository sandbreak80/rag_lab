# Splunk Full-Stack Observability Implementation Plan

**Project:** RAG Lab - Full Splunk Observability Integration
**Date:** 2025-11-07
**Status:** 🚀 READY TO IMPLEMENT
**Target Audience:** Splunk Sales Engineers & Solutions Engineers

---

## Executive Summary

**Current State:** Prometheus + Grafana for infrastructure monitoring (user-facing)
**Target State:** OpenTelemetry + Splunk Observability Cloud for complete full-stack observability (back-end)
**Purpose:** Demonstrate world-class observability for production RAG systems to Splunk customers

### The Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    DUAL OBSERVABILITY STACK                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FRONT-END (User-Facing Demo)                                   │
│  ├─ Prometheus + Grafana                                        │
│  ├─ GPU metrics, system metrics, container health               │
│  └─ Purpose: Teaching, visualization, student learning          │
│                                                                  │
│  BACK-END (Production Observability)                            │
│  ├─ OpenTelemetry + OpenLLMetry                                 │
│  ├─ Splunk Observability Cloud                                  │
│  ├─ Full distributed tracing, APM, RUM                          │
│  └─ Purpose: Production-grade monitoring, Splunk value prop     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight:** This isn't Prometheus OR Splunk - it's Prometheus AND Splunk, each serving different purposes in the teaching lab.

---

## Part 1: Strategic Context

### 🎯 Why This Matters

From the existing [SPLUNK_AI_PLATFORM_INTEGRATION.md](lab/SPLUNK_AI_PLATFORM_INTEGRATION.md):

> "Splunk is not just observability - it's the complete AI platform:
> - **Build models** → Splunk DSDL
> - **Deploy AI** → RAG Reference Architecture
> - **Optimize performance** → Splunk AI Toolkit
> - **Monitor everything** → Splunk Observability Cloud"

**This lab is the "Deploy AI" pillar** - and it needs world-class observability to demonstrate Splunk's value.

### 🏆 Value Proposition

**For Splunk SEs/SAs:**
1. **Demo Environment** - Show customers exactly how Splunk monitors production RAG
2. **Reference Architecture** - Copy this for customer POCs
3. **Hands-on Learning** - Understand RAG + Splunk observability deeply
4. **Sales Tool** - Generate pipeline with working demos

**For Splunk Customers:**
1. **Production Ready** - Not a toy, actually production-grade monitoring
2. **Complete Visibility** - Infrastructure + Application + Business metrics
3. **ROI Proof** - See cost savings, performance improvements, quality gains
4. **Best Practices** - Learn from a reference implementation

---

## Part 2: Architecture Analysis

### Current Architecture (Prometheus + Grafana)

**What's Working:**
- ✅ GPU monitoring (DCGM Exporter)
- ✅ System metrics (Node Exporter - CPU, memory, disk, network)
- ✅ Container health (cAdvisor + custom health-exporter)
- ✅ RAG metrics (chunks, documents, graph nodes/edges)
- ✅ Beautiful Grafana dashboards
- ✅ Real-time visualization

**What's Missing:**
- ❌ **Application tracing** - No request flow visibility
- ❌ **LLM call traces** - Can't see prompt → model → response
- ❌ **Provenance tracking** - Don't know which sources were used
- ❌ **Error context** - When things fail, limited debugging info
- ❌ **Business metrics** - No groundedness, hallucination detection
- ❌ **Cost tracking** - No per-query cost calculation
- ❌ **Latency breakdown** - Can't see per-stage waterfall

### Target Architecture (OpenTelemetry + Splunk)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAG Lab Services                             │
│  (31 microservices instrumented with OpenLLMetry)                   │
└────────────────┬────────────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
┌──────────────┐    ┌──────────────────────┐
│ Prometheus   │    │ OpenTelemetry        │
│ (Metrics)    │    │ Collector            │
│              │    │ (Traces + Metrics)   │
└──────┬───────┘    └──────┬───────────────┘
       │                   │
       │                   ├─→ Trace Pipeline
       │                   ├─→ Metrics Pipeline
       │                   └─→ Logs Pipeline
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────────────────────┐
│   Grafana    │    │ Splunk Observability Cloud   │
│ (Teaching)   │    │ (Production Monitoring)      │
│              │    │                              │
│ - GPU viz    │    │ - APM (Application)          │
│ - System viz │    │ - Infrastructure             │
│ - Containers │    │ - Real User Monitoring       │
└──────────────┘    │ - Log Observer               │
                    │ - Synthetics                 │
                    │ - Incident Intelligence      │
                    └──────────────────────────────┘
```

**Key Components:**

1. **OpenLLMetry SDK** - Instruments Python services
2. **OpenTelemetry Collector** - Aggregates/processes/exports telemetry
3. **Splunk Observability Cloud** - Backend SaaS platform
4. **Prometheus/Grafana** - Kept for teaching/visualization

---

## Part 3: Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### Task 1.1: OpenTelemetry Collector Setup

**Objective:** Central telemetry aggregation point

**Implementation:**

```yaml
# docker-compose.yml - Add OTel Collector

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: rag-otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./monitoring/otel/otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP HTTP receiver
      - "8888:8888"   # Prometheus metrics (collector self-monitoring)
      - "13133:13133" # Health check
    networks:
      - rag-network
    restart: unless-stopped
```

```yaml
# monitoring/otel/otel-collector-config.yaml

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  prometheus:
    config:
      scrape_configs:
        # Scrape Prometheus exporters (GPU, Node, cAdvisor)
        - job_name: 'dcgm-exporter'
          static_configs:
            - targets: ['dcgm-exporter:9400']

        - job_name: 'node-exporter'
          static_configs:
            - targets: ['node-exporter:9100']

        - job_name: 'cadvisor'
          static_configs:
            - targets: ['cadvisor:8080']

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  memory_limiter:
    check_interval: 1s
    limit_mib: 512

  resource:
    attributes:
      - key: deployment.environment
        value: production
        action: upsert
      - key: service.namespace
        value: rag-lab
        action: upsert
      - key: cloud.provider
        value: aws
        action: upsert
      - key: cloud.region
        value: us-west-2
        action: upsert

exporters:
  # Splunk Observability Cloud (Traces)
  sapm:
    access_token: ${SPLUNK_ACCESS_TOKEN}
    endpoint: https://ingest.${SPLUNK_REALM}.signalfx.com/v2/trace

  # Splunk Observability Cloud (Metrics)
  signalfx:
    access_token: ${SPLUNK_ACCESS_TOKEN}
    realm: ${SPLUNK_REALM}

  # Splunk Observability Cloud (Logs)
  splunk_hec:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://http-inputs.${SPLUNK_REALM}.signalfx.com:443/services/collector
    source: "otel"
    sourcetype: "otel"

  # Keep Prometheus for Grafana (teaching)
  prometheus:
    endpoint: "0.0.0.0:8889"

  # Debug output (optional)
  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [sapm, logging]

    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch, resource]
      exporters: [signalfx, prometheus]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [splunk_hec, logging]
```

**Environment Variables:**

```bash
# .env
SPLUNK_ACCESS_TOKEN=your_token_here
SPLUNK_REALM=us0  # or us1, eu0, etc.
SPLUNK_HEC_TOKEN=your_hec_token_here
```

---

#### Task 1.2: Instrument Core Services with OpenLLMetry

**Services to Instrument:**
1. `chat-service` (main orchestrator)
2. `vector-db` (ChromaDB)
3. `knowledge-graph` (NetworkX)
4. `web-search` (SearXNG wrapper)
5. `reranker` (LLM re-ranking)
6. `model-router` (model selection)
7. `embedding-service` (text embeddings)
8. `research-agent` (autonomous research)

**Example: chat-service**

```dockerfile
# services/chat-service/requirements.txt

# Existing dependencies
flask>=2.3.0
flask-cors>=4.0.0
requests>=2.31.0

# Add OpenTelemetry
traceloop-sdk>=0.47.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-flask>=0.41b0
opentelemetry-instrumentation-requests>=0.41b0
opentelemetry-exporter-otlp>=1.20.0
```

```python
# services/chat-service/app/service.py

from flask import Flask, request, jsonify
from traceloop.sdk import Traceloop
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import os

# Initialize Flask
app = Flask(__name__)

# Initialize OpenLLMetry/OpenTelemetry
Traceloop.init(
    app_name="rag-lab-chat-service",
    api_endpoint=f"http://otel-collector:4318",  # OTLP HTTP
    disable_batch=False,  # Enable batching for production
    # Resource attributes
    resource_attributes={
        "service.name": "rag-lab-chat-service",
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("DEPLOYMENT_ENV", "production"),
        "service.namespace": "rag-lab"
    }
)

# Get tracer
tracer = trace.get_tracer(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with full tracing"""

    # Start root span
    with tracer.start_as_current_span("chat.process_query") as span:
        try:
            data = request.json
            query = data.get('query')
            settings = data.get('settings', {})

            # Add span attributes
            span.set_attribute("query.text", query)
            span.set_attribute("query.length", len(query))
            span.set_attribute("settings.preset", settings.get('preset', 'balanced'))

            # 1. Query decomposition (child span)
            with tracer.start_as_current_span("chat.decompose_query") as decompose_span:
                subtasks = decompose_query(query)
                decompose_span.set_attribute("subtasks.count", len(subtasks))

            # 2. Retrieval (child span)
            with tracer.start_as_current_span("chat.retrieve") as retrieve_span:
                # Vector DB
                with tracer.start_as_current_span("chat.retrieve.vector_db"):
                    rag_results = call_vector_db(query)
                    retrieve_span.set_attribute("retrieval.rag.count", len(rag_results))

                # Web search (if enabled)
                if settings.get('use_web_search'):
                    with tracer.start_as_current_span("chat.retrieve.web_search"):
                        web_results = call_web_search(query)
                        retrieve_span.set_attribute("retrieval.web.count", len(web_results))
                else:
                    web_results = []

                # Merge results
                all_results = merge_results(rag_results, web_results)
                retrieve_span.set_attribute("retrieval.total.count", len(all_results))

            # 3. Reranking (child span)
            if settings.get('use_reranking'):
                with tracer.start_as_current_span("chat.rerank") as rerank_span:
                    reranked = call_reranker(query, all_results)
                    rerank_span.set_attribute("rerank.input.count", len(all_results))
                    rerank_span.set_attribute("rerank.output.count", len(reranked))
            else:
                reranked = all_results

            # 4. LLM generation (child span)
            with tracer.start_as_current_span("chat.llm_generation") as llm_span:
                model_name = settings.get('model', 'llama3.3:70b')
                llm_span.set_attribute("llm.model", model_name)

                answer = call_llm(query, reranked, model_name)

                llm_span.set_attribute("llm.prompt.tokens", answer['prompt_tokens'])
                llm_span.set_attribute("llm.completion.tokens", answer['completion_tokens'])
                llm_span.set_attribute("llm.total.tokens", answer['total_tokens'])

            # 5. Calculate costs (child span)
            with tracer.start_as_current_span("chat.calculate_cost") as cost_span:
                cost = calculate_cost(answer['total_tokens'], model_name)
                cost_span.set_attribute("cost.total", cost)
                cost_span.set_attribute("cost.currency", "USD")

            # 6. Quality metrics (child span)
            with tracer.start_as_current_span("chat.quality_metrics") as quality_span:
                groundedness = calculate_groundedness(answer['text'], reranked)
                quality_span.set_attribute("quality.groundedness", groundedness)

            # Set final span attributes
            span.set_attribute("response.length", len(answer['text']))
            span.set_attribute("cost.total", cost)
            span.set_attribute("quality.groundedness", groundedness)
            span.set_status(Status(StatusCode.OK))

            return jsonify({
                "answer": answer['text'],
                "sources": reranked,
                "metrics": {
                    "tokens": answer['total_tokens'],
                    "cost": cost,
                    "groundedness": groundedness
                },
                "trace_id": span.get_span_context().trace_id.to_bytes(16, 'big').hex()
            })

        except Exception as e:
            # Record exception in span
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

#### Task 1.3: Instrument Vector DB Service

```python
# services/vector-db/app/service.py

from flask import Flask, request, jsonify
from traceloop.sdk import Traceloop
from opentelemetry import trace
import chromadb

app = Flask(__name__)

# Initialize OpenTelemetry
Traceloop.init(
    app_name="rag-lab-vector-db",
    api_endpoint="http://otel-collector:4318"
)

tracer = trace.get_tracer(__name__)

# ChromaDB client (automatically instrumented by OpenLLMetry)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("rag_documents")

@app.route('/search', methods=['POST'])
def search():
    """Search vector DB with tracing"""

    with tracer.start_as_current_span("vector_db.search") as span:
        try:
            data = request.json
            query = data.get('query')
            top_k = data.get('top_k', 10)

            span.set_attribute("db.system", "chromadb")
            span.set_attribute("db.operation", "query")
            span.set_attribute("db.collection", "rag_documents")
            span.set_attribute("vector_db.top_k", top_k)
            span.set_attribute("vector_db.query.length", len(query))

            # Query ChromaDB (auto-instrumented)
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )

            # Add result metrics
            span.set_attribute("vector_db.results.count", len(results['documents'][0]))
            span.set_attribute("vector_db.results.avg_distance",
                             sum(results['distances'][0]) / len(results['distances'][0]))

            return jsonify({
                "results": format_results(results),
                "count": len(results['documents'][0])
            })

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return jsonify({"error": str(e)}), 500
```

---

### Phase 2: Advanced Instrumentation (Week 3-4)

#### Task 2.1: Custom Spans for RAG-Specific Logic

```python
# services/common/tracing_utils.py

from opentelemetry import trace
from functools import wraps
import time

tracer = trace.get_tracer(__name__)

def trace_rag_component(component_name):
    """Decorator for RAG-specific tracing"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(f"rag.{component_name}.{func.__name__}") as span:
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    # Add custom attributes
                    span.set_attribute(f"rag.{component_name}.duration_ms",
                                     (time.time() - start_time) * 1000)

                    # Add result metadata
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if isinstance(value, (int, float, str, bool)):
                                span.set_attribute(f"rag.{component_name}.{key}", value)

                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper
    return decorator


# Usage in services
from common.tracing_utils import trace_rag_component

@trace_rag_component("chunking")
def chunk_document(document, chunk_size=512, overlap=50):
    """Chunk document with tracing"""
    chunks = []
    # ... chunking logic ...
    return {
        "chunks": chunks,
        "count": len(chunks),
        "avg_size": sum(len(c) for c in chunks) / len(chunks)
    }

@trace_rag_component("knowledge_graph")
def expand_query_with_kg(query, hops=2):
    """Expand query with knowledge graph"""
    entities = extract_entities(query)
    expanded = perform_graph_walk(entities, hops)
    return {
        "original_entities": len(entities),
        "expanded_entities": len(expanded),
        "hops": hops
    }
```

---

#### Task 2.2: Business Metrics & Custom Events

```python
# services/chat-service/app/metrics.py

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Initialize metrics
meter = metrics.get_meter(__name__)

# Create custom metrics
query_counter = meter.create_counter(
    "rag.queries.total",
    description="Total number of RAG queries processed"
)

query_latency = meter.create_histogram(
    "rag.query.duration",
    description="RAG query latency in milliseconds",
    unit="ms"
)

token_counter = meter.create_counter(
    "rag.tokens.total",
    description="Total tokens consumed",
    unit="tokens"
)

cost_counter = meter.create_counter(
    "rag.cost.total",
    description="Total cost in USD",
    unit="USD"
)

groundedness_gauge = meter.create_gauge(
    "rag.quality.groundedness",
    description="Answer groundedness score (0-1)"
)

# Usage in chat endpoint
def process_query(query, settings):
    start_time = time.time()

    try:
        # Process query...
        answer = generate_answer(query, settings)

        # Record metrics
        latency = (time.time() - start_time) * 1000

        query_counter.add(1, {
            "preset": settings.get('preset'),
            "model": settings.get('model'),
            "status": "success"
        })

        query_latency.record(latency, {
            "preset": settings.get('preset'),
            "model": settings.get('model')
        })

        token_counter.add(answer['total_tokens'], {
            "model": settings.get('model'),
            "type": "total"
        })

        cost_counter.add(answer['cost'], {
            "model": settings.get('model')
        })

        groundedness_gauge.set(answer['groundedness'], {
            "preset": settings.get('preset')
        })

        return answer

    except Exception as e:
        query_counter.add(1, {
            "preset": settings.get('preset'),
            "model": settings.get('model'),
            "status": "error",
            "error_type": type(e).__name__
        })
        raise
```

---

#### Task 2.3: Evidence Provenance Tracking

```python
# services/common/evidence_tracing.py

from opentelemetry import trace
from dataclasses import dataclass
from datetime import datetime

tracer = trace.get_tracer(__name__)

@dataclass
class EvidenceTrace:
    """Evidence with full OpenTelemetry tracing"""
    id: int
    origin_tool: str  # "web_search", "rag", "research_agent"
    url: str
    trace_id: str  # OpenTelemetry trace ID
    span_id: str   # OpenTelemetry span ID
    timestamp: datetime

    def to_otel_attributes(self):
        """Convert to OpenTelemetry span attributes"""
        return {
            "evidence.id": self.id,
            "evidence.origin_tool": self.origin_tool,
            "evidence.url": self.url,
            "evidence.trace_id": self.trace_id,
            "evidence.span_id": self.span_id,
            "evidence.timestamp": self.timestamp.isoformat()
        }

def create_evidence_with_trace(origin_tool, url, content):
    """Create evidence and link to current span"""

    span = trace.get_current_span()
    span_context = span.get_span_context()

    evidence = EvidenceTrace(
        id=generate_evidence_id(),
        origin_tool=origin_tool,
        url=url,
        trace_id=span_context.trace_id.to_bytes(16, 'big').hex(),
        span_id=span_context.span_id.to_bytes(8, 'big').hex(),
        timestamp=datetime.now()
    )

    # Add to span
    span.add_event("evidence_created", evidence.to_otel_attributes())

    return evidence

# Usage in retrievers
def web_search_with_trace(query):
    with tracer.start_as_current_span("web_search.execute") as span:
        results = perform_search(query)

        evidences = []
        for result in results:
            evidence = create_evidence_with_trace(
                origin_tool="web_search",
                url=result['url'],
                content=result['content']
            )
            evidences.append(evidence)

            # Add event for each evidence
            span.add_event("evidence_retrieved", {
                "evidence.id": evidence.id,
                "evidence.url": evidence.url,
                "evidence.relevance": result.get('relevance', 0.0)
            })

        return evidences
```

---

### Phase 3: Splunk Observability Cloud Configuration (Week 5)

#### Task 3.1: Splunk Setup

**1. Create Splunk Observability Cloud Account**
- Go to https://www.splunk.com/en_us/download/o11y-cloud-free-trial.html
- Sign up for free trial (50M traces/month)
- Note your realm (e.g., `us0`, `us1`, `eu0`)

**2. Generate Tokens**

```bash
# Access Token (for traces/metrics)
# Settings → Access Tokens → Create Token
# Scope: Ingest (SAPM, Metrics)

export SPLUNK_ACCESS_TOKEN="your_access_token_here"
export SPLUNK_REALM="us0"

# HEC Token (for logs)
# Settings → Data Management → Add Integration → HTTP Event Collector
export SPLUNK_HEC_TOKEN="your_hec_token_here"
```

**3. Update Environment**

```bash
# .env
SPLUNK_ACCESS_TOKEN=your_token
SPLUNK_REALM=us0
SPLUNK_HEC_TOKEN=your_hec_token

# Deploy
docker compose up -d otel-collector
```

---

#### Task 3.2: Create Splunk Dashboards

**Dashboard 1: RAG System Overview**

```yaml
# Splunk Dashboard (via UI or API)

Title: RAG Lab - System Overview

Panels:
  1. Request Rate (chart)
     - Metric: rag.queries.total (rate)
     - Group by: preset, model

  2. Latency Percentiles (chart)
     - Metric: rag.query.duration
     - Percentiles: p50, p95, p99
     - Group by: preset

  3. Error Rate (chart)
     - Metric: rag.queries.total
     - Filter: status=error
     - Group by: error_type

  4. Token Usage (chart)
     - Metric: rag.tokens.total
     - Group by: model

  5. Cost Tracking (chart)
     - Metric: rag.cost.total
     - Cumulative sum

  6. Groundedness Score (chart)
     - Metric: rag.quality.groundedness
     - Average over time

  7. Service Map (APM)
     - Shows: chat-service → vector-db → knowledge-graph → web-search
     - Latency on edges

  8. Top Errors (table)
     - Query: Error spans, group by error type
```

**Dashboard 2: Infrastructure Health**

```yaml
Title: RAG Lab - Infrastructure

Panels:
  1. GPU Utilization (chart)
     - Source: Prometheus (DCGM)
     - Metric: DCGM_FI_DEV_GPU_UTIL

  2. GPU Memory (chart)
     - Metric: DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL

  3. GPU Temperature (chart)
     - Metric: DCGM_FI_DEV_GPU_TEMP

  4. Container Health (table)
     - Source: cAdvisor via OTel Collector
     - Shows: CPU, Memory, Network I/O per container

  5. Node Metrics (chart)
     - CPU, Memory, Disk from Node Exporter
```

**Dashboard 3: Business Metrics**

```yaml
Title: RAG Lab - Business KPIs

Panels:
  1. Cost per Query (chart)
     - Calculated: rag.cost.total / rag.queries.total
     - Group by: preset, model

  2. Quality vs Speed (scatter)
     - X-axis: Latency
     - Y-axis: Groundedness
     - Group by: preset

  3. Token Efficiency (chart)
     - Calculated: tokens per character in answer
     - Shows model efficiency

  4. Preset Comparison (table)
     - Rows: Each preset (Minimal, Fast, Balanced, etc.)
     - Cols: Avg latency, Avg groundedness, Avg cost

  5. Retrieval Quality (chart)
     - Metrics: retrieval.rag.count, retrieval.web.count
     - Shows source distribution
```

---

#### Task 3.3: Configure Alerting

```yaml
# Splunk Alerting Rules

Alert 1: High Latency
  Condition: p95(rag.query.duration) > 5000ms for 5 minutes
  Action: Email, Slack
  Severity: Warning
  Message: "RAG query latency is high (p95 > 5s). Check service health."

Alert 2: Error Rate Spike
  Condition: rate(rag.queries.total{status="error"}) > 0.05 for 5 minutes
  Action: PagerDuty, Slack
  Severity: Critical
  Message: "RAG error rate > 5%. Investigate immediately."

Alert 3: Low Groundedness
  Condition: avg(rag.quality.groundedness) < 0.7 for 10 minutes
  Action: Email
  Severity: Warning
  Message: "RAG groundedness dropping. Check retrieval quality."

Alert 4: Cost Budget Exceeded
  Condition: sum(rag.cost.total) over 1 day > $10.00
  Action: Email
  Severity: Info
  Message: "Daily RAG cost exceeded $10. Review usage."

Alert 5: GPU Overheating
  Condition: DCGM_FI_DEV_GPU_TEMP > 85°C
  Action: PagerDuty
  Severity: Critical
  Message: "GPU temperature critical. Throttle or shutdown."
```

---

### Phase 4: Integration with Phase 1 (Contract & Provenance)

#### How OpenTelemetry Supports Phase 1 Goals

From [IMPLEMENTATION_PLAN_PHASE_1.md](IMPLEMENTATION_PLAN_PHASE_1.md):

**Phase 1 Task 1B: Immutable Evidence**
```python
# Link Evidence to OpenTelemetry traces

@dataclass(frozen=True)
class Evidence:
    id: int
    origin_tool: str
    url: str
    # ... other fields ...

    # NEW: OpenTelemetry integration
    trace_id: str  # Full trace ID
    span_id: str   # Span where evidence was created

    def get_trace_url(self, splunk_realm="us0"):
        """Generate Splunk APM deep link"""
        return f"https://app.{splunk_realm}.signalfx.com/#/apm/traces/{self.trace_id}"
```

**UI Display:**
```typescript
// frontend/src/components/EvidenceCard.tsx

function EvidenceCard({ evidence }) {
  return (
    <div className="evidence-card">
      <h4>[#{evidence.id}] {evidence.title}</h4>
      <p>{evidence.url}</p>
      <p>Origin: {evidence.origin_tool}</p>

      {/* Splunk deep link */}
      <a href={evidence.trace_url} target="_blank" className="trace-link">
        🔍 View in Splunk APM →
      </a>
    </div>
  )
}
```

**Value:** Students click evidence → see full distributed trace in Splunk → understand exactly how that piece of evidence was retrieved.

---

**Phase 1 Task 1C: Recency Gate**
```python
# Add recency gate to span attributes

def enforce_recency_gate(query, evidence_list, max_staleness_hours=48):
    with tracer.start_as_current_span("recency_gate.enforce") as span:
        span.set_attribute("recency_gate.enabled", True)
        span.set_attribute("recency_gate.max_staleness_hours", max_staleness_hours)

        fresh_evidence = [
            ev for ev in evidence_list
            if ev.is_fresh(max_staleness_hours)
        ]

        span.set_attribute("recency_gate.input.count", len(evidence_list))
        span.set_attribute("recency_gate.output.count", len(fresh_evidence))
        span.set_attribute("recency_gate.passed", len(fresh_evidence) >= 2)

        if len(fresh_evidence) < 2:
            span.add_event("recency_gate_failed", {
                "reason": f"Only {len(fresh_evidence)} fresh sources found, need 2"
            })
            span.set_status(Status(StatusCode.ERROR, "Recency gate failed"))
            raise RecencyGateException("Insufficient fresh sources")

        return fresh_evidence
```

**Splunk Query:**
```spl
| from span
| where span.name="recency_gate.enforce"
| stats count by recency_gate.passed
```

---

### Phase 5: Student Learning Integration (Week 6)

#### Task 5.1: Update Lab Guide

**Add to Lab Guide Section 6: "Production Observability"**

```markdown
## Section 6: Production Observability with Splunk

### Learning Objectives
- Understand the difference between teaching metrics (Grafana) and production observability (Splunk)
- Learn how distributed tracing works in RAG systems
- See how OpenTelemetry instruments microservices
- Explore Splunk Observability Cloud dashboards

### Activity 1: Compare Prometheus vs OpenTelemetry

**Prometheus/Grafana (What you see):**
- Infrastructure metrics (GPU, CPU, Memory)
- Service health (up/down)
- Basic RAG metrics (chunks, nodes)

**OpenTelemetry/Splunk (Production grade):**
- Distributed traces (request flow)
- Per-query latency breakdown
- Evidence provenance (which span retrieved which source)
- Business metrics (cost, groundedness)

**Exercise:**
1. Run a query in the UI
2. Note the trace ID in the response
3. Open Grafana → See system metrics
4. Open Splunk APM → Paste trace ID → See full waterfall

### Activity 2: Trace a Query End-to-End

**Steps:**
1. Submit query: "What is the capital of France?"
2. Copy trace ID from response
3. Open Splunk APM: `https://app.us0.signalfx.com/#/apm`
4. Paste trace ID in search
5. Observe waterfall:
   ```
   chat.process_query (250ms)
     ├─ chat.decompose_query (10ms)
     ├─ chat.retrieve (100ms)
     │  ├─ chat.retrieve.vector_db (60ms)
     │  └─ chat.retrieve.web_search (40ms)
     ├─ chat.rerank (30ms)
     └─ chat.llm_generation (110ms)
   ```

**Questions:**
1. Which stage took the longest?
2. How many sources were retrieved from vector DB vs web?
3. What was the LLM token count?
4. What was the cost of this query?

### Activity 3: Investigate an Error

**Scenario:** Trigger an error by submitting invalid query

**Steps:**
1. Submit: `{"query": null}`  (intentionally invalid)
2. Note error response
3. Copy trace ID
4. Open Splunk APM → Find failed span (red)
5. Click span → See exception details
6. View stack trace
7. Identify root cause

**Discussion:**
- How does distributed tracing help debug production issues?
- What would this look like with just logs?
- How does Splunk correlate logs, traces, and metrics?
```

---

#### Task 5.2: Create Demo Script for SEs

```markdown
# Demo Script: Splunk Observability for RAG Systems

**Duration:** 15-20 minutes
**Audience:** Customers evaluating observability solutions

## Setup (Before Demo)
- [ ] RAG Lab running on AWS
- [ ] Splunk Observability Cloud configured
- [ ] Grafana dashboard open (Tab 1)
- [ ] Splunk APM open (Tab 2)
- [ ] Splunk Infrastructure open (Tab 3)
- [ ] Sample trace ID ready

## Act 1: The Problem (2 min)

**Narrative:**
"You're running a production RAG system serving customer support. You need to answer:
- Is the system healthy?
- Where is latency coming from?
- Which sources are being used?
- What's the cost per query?
- Are answers grounded in facts?

Traditional monitoring (logs, basic metrics) can't answer these questions for AI systems."

## Act 2: Infrastructure Monitoring (3 min)

**Tab 1: Grafana**

"This is what most teams start with - infrastructure metrics:
- GPU at 45% utilization
- 31 containers running
- System healthy

But this doesn't tell us about the AI application itself."

**Tab 3: Splunk Infrastructure**

"Splunk pulls the same infrastructure data, but adds:
- Automatic service discovery
- Correlation with application traces
- Alerting tied to business impact"

## Act 3: Application Tracing (5 min)

**Tab 2: Splunk APM**

"Now let's trace an actual user query."

**[Submit query in UI]**

"Watch as the request flows through:
1. Chat service receives query
2. Decomposes into subtasks
3. Retrieves from vector DB (60ms)
4. Searches web (40ms)
5. Reranks with LLM (30ms)
6. Generates answer (110ms)

Total: 250ms, well within our 300ms SLA."

**[Click on vector_db span]**

"Here we see:
- 10 chunks retrieved
- Average distance: 0.42
- ChromaDB query time: 58ms
- Linked to evidence IDs [#1, #2, #3...]"

**[Click on llm_generation span]**

"And the LLM call:
- Model: llama3.3:70b
- Prompt tokens: 450
- Completion tokens: 150
- Total cost: $0.0005"

## Act 4: Business Metrics (3 min)

**[Open Splunk Dashboard: Business KPIs]**

"Now let's look at the business metrics:
- Average cost per query: $0.0004
- Average latency: 280ms
- Average groundedness: 0.91 (91% grounded)

If we run 1M queries/month:
- Cost: $400/month
- 98% meet 300ms SLA
- 95% have >0.8 groundedness"

**[Show preset comparison table]**

"Different presets have different trade-offs:
- Fast: 60ms, 0.70 groundedness, $0.0001/query
- Balanced: 120ms, 0.87 groundedness, $0.0003/query
- Quality: 250ms, 0.94 groundedness, $0.0008/query

You can tune for cost, speed, or quality."

## Act 5: Troubleshooting (4 min)

**[Trigger error scenario]**

"Let's see what happens when something breaks."

**[Submit malformed query]**

"The query fails. In logs, you'd see an error message. In Splunk APM:"

**[Show failed trace]**

"We immediately see:
- Which service threw the exception
- The full stack trace
- Which upstream requests succeeded
- Correlated logs at that exact moment
- Similar errors in the past hour

Time to resolution: 2 minutes vs 2 hours."

## Act 6: Alerting & SLOs (2 min)

**[Show alert configuration]**

"We've set up alerts for:
- Latency > 5s (p95)
- Error rate > 5%
- Groundedness < 0.7
- Daily cost > $10

These tie directly to business outcomes, not just infrastructure."

## Closing (1 min)

"This is what AI observability looks like in production:
- Infrastructure + Application + Business metrics
- Distributed tracing for every request
- Cost and quality tracking
- Proactive alerting

And this is all out of the box with Splunk Observability Cloud + OpenTelemetry."

**Questions?**
```

---

### Phase 6: Documentation & Rollout (Week 7-8)

#### Documentation to Create

1. **SPLUNK_OBSERVABILITY_SETUP.md**
   - Step-by-step Splunk account setup
   - Token generation
   - OpenTelemetry Collector configuration
   - Dashboard creation

2. **OPENTELEMETRY_INSTRUMENTATION_GUIDE.md**
   - How to instrument new services
   - Custom span creation
   - Custom metrics
   - Best practices

3. **TROUBLESHOOTING_WITH_SPLUNK.md**
   - Common scenarios (high latency, errors, low quality)
   - How to use Splunk APM for debugging
   - Sample queries

4. **SPLUNK_DEMO_GUIDE.md**
   - Demo script (from Phase 5.2)
   - FAQs
   - Customer objection handling

---

## Part 4: Alignment with Existing Value Proposition

### From SPLUNK_AI_PLATFORM_INTEGRATION.md

**Section 4A: MLTK Integration**
- ✅ OpenTelemetry exports metrics to Splunk HEC
- ✅ MLTK can then analyze those metrics (forecasting, anomaly detection)
- ✅ Same metrics used for both real-time dashboards and ML-driven optimization

**Section 4B: DSDL Integration**
- ✅ Custom models (embeddings, re-rankers) instrumented automatically
- ✅ DSDL training runs tracked as spans
- ✅ Model deployment events logged

**Section 4C: Unified Platform Story**
- ✅ "Experiment (DSDL) → Deploy (RAG Lab) → Optimize (MLTK) → Monitor (Observability)"
- ✅ All instrumented with OpenTelemetry from day one
- ✅ Single pane of glass (Splunk)

---

## Part 5: Success Metrics

### Technical Metrics

**Instrumentation Coverage:**
- [ ] 100% of critical services instrumented (8/8)
- [ ] 100% of API endpoints traced
- [ ] 100% of LLM calls tracked
- [ ] 100% of database queries monitored

**Telemetry Quality:**
- [ ] <1% trace sampling (capture everything for lab)
- [ ] <100ms added latency from instrumentation
- [ ] <5% CPU overhead from OpenTelemetry
- [ ] 99.9% trace delivery to Splunk

**Observability Goals:**
- [ ] <30s mean time to detect (MTTD) for errors
- [ ] <5min mean time to understand (MTTU) root cause
- [ ] <15min mean time to resolution (MTTR)

### Business Metrics

**Field Enablement:**
- [ ] 100% of SEs can demo Splunk observability
- [ ] 50+ customer demos using this stack (Year 1)
- [ ] 10+ POCs leveraging this reference architecture

**Customer Success:**
- [ ] 10+ Fortune 500 companies adopt pattern
- [ ] 40-60% LLM cost reduction (via optimization insights)
- [ ] 99%+ SLA compliance (via proactive alerting)

---

## Part 6: Budget & Resources

### Infrastructure Costs

**Splunk Observability Cloud:**
- Free tier: 50M traces/month (sufficient for lab)
- Standard tier: ~$55/host/month (if needed)
- Enterprise tier: Custom pricing

**Current Estimate:**
- Lab usage: ~30K traces/month (1K requests/day)
- Cost: $0 (within free tier)

**AWS Costs:**
- OpenTelemetry Collector: Negligible (<5% CPU overhead)
- Network egress: ~$5/month (telemetry data)

### Human Resources

**Engineering (Implementation):**
- Week 1-2: 40 hours (OTel Collector + Core instrumentation)
- Week 3-4: 40 hours (Advanced instrumentation)
- Week 5: 20 hours (Splunk configuration)
- Week 6: 20 hours (Integration with Phase 1)
- Week 7-8: 40 hours (Documentation + Rollout)
- **Total: 160 hours (~4 weeks, 1 engineer)**

**Field Enablement:**
- Demo script creation: 8 hours
- Dashboard templates: 16 hours
- Training materials: 16 hours
- Pilot delivery: 40 hours
- **Total: 80 hours (2 weeks, 1 SE)**

---

## Part 7: Risks & Mitigation

### Risk 1: Performance Overhead

**Risk:** OpenTelemetry adds latency to every request

**Mitigation:**
- Use batch exporting (not per-request)
- Async trace submission
- Memory-limited processor
- Benchmark: <5ms p99 overhead

**Test:**
```bash
# Baseline (no instrumentation)
ab -n 1000 -c 10 http://localhost:8000/api/ask

# With OpenTelemetry
ab -n 1000 -c 10 http://localhost:8000/api/ask

# Compare p50, p95, p99
```

### Risk 2: Cost Overrun (Splunk Free Tier)

**Risk:** Exceed 50M traces/month free tier

**Current Math:**
- 1K requests/day × 30 days = 30K requests/month
- ~1 trace per request = 30K traces/month
- **Well within limit (50M)**

**If scaled:**
- 10K requests/day = 300K traces/month (still within free tier)
- 100K requests/day = 3M traces/month (still within free tier)

**Mitigation:**
- Tail sampling (only keep interesting traces)
- Rate limiting for demo/test environments

### Risk 3: Complexity (Too Many Tools)

**Risk:** Students confused by Prometheus + OpenTelemetry + Splunk

**Mitigation:**
- Clear separation of concerns in docs
- Grafana = "Teaching visualization"
- Splunk = "Production observability"
- Explain WHY both are valuable

**Training:**
- Lab Section 6 addresses this explicitly
- Demo script shows both side-by-side

### Risk 4: Splunk Account Management

**Risk:** Token rotation, account expiration, multi-user access

**Mitigation:**
- Document token rotation process
- Use AWS Secrets Manager for tokens
- Create shared team account (not personal)

---

## Part 8: Rollout Plan

### Week 1-2: Core Implementation
- [ ] Day 1-2: OpenTelemetry Collector setup
- [ ] Day 3-5: Instrument chat-service, vector-db, knowledge-graph
- [ ] Day 6-7: Instrument remaining services
- [ ] Day 8-10: Test end-to-end tracing

### Week 3-4: Advanced Features
- [ ] Day 11-13: Custom spans (chunking, KG, recency gate)
- [ ] Day 14-16: Business metrics (cost, groundedness)
- [ ] Day 17-18: Evidence provenance tracing
- [ ] Day 19-20: Integration testing

### Week 5: Splunk Configuration
- [ ] Day 21: Create Splunk account, generate tokens
- [ ] Day 22: Deploy OTel Collector with Splunk exporters
- [ ] Day 23: Create dashboards (System, Business, Infrastructure)
- [ ] Day 24: Configure alerting rules
- [ ] Day 25: Validation testing

### Week 6: Phase 1 Integration
- [ ] Day 26-27: Link Evidence to traces
- [ ] Day 28-29: Add recency gate tracing
- [ ] Day 30: Contract enforcement tracing

### Week 7: Documentation
- [ ] Day 31-32: Setup guide
- [ ] Day 33: Instrumentation guide
- [ ] Day 34: Troubleshooting guide
- [ ] Day 35: Demo script

### Week 8: Rollout
- [ ] Day 36-37: Internal pilot (5 SEs)
- [ ] Day 38: Feedback incorporation
- [ ] Day 39: Full field rollout announcement
- [ ] Day 40: First customer demo

---

## Part 9: Next Steps (Immediate)

### This Week
1. **Decision:** Approve this plan
2. **Access:** Request Splunk Observability Cloud trial account
3. **Branch:** Create `feature/splunk-observability` branch
4. **Kickoff:** Schedule engineering kickoff meeting

### Next Week
1. **Implement:** Start Phase 1 (OTel Collector + Core instrumentation)
2. **Test:** Validate trace flow from services → Collector → Splunk
3. **Document:** Begin setup guide (parallel to implementation)

---

## Part 10: Summary

### What We're Building

```
Dual-Stack Observability:
├─ Grafana (Teaching Layer)
│  ├─ GPU/System/Container metrics
│  ├─ Visual dashboards for students
│  └─ Real-time monitoring during labs
│
└─ Splunk Observability Cloud (Production Layer)
   ├─ Distributed tracing (OpenTelemetry)
   ├─ Application performance monitoring
   ├─ Business metrics (cost, quality)
   ├─ Infrastructure correlation
   └─ Alerting & incident management
```

### Why It Matters

1. **For Students:** See both "learning" and "production" observability
2. **For SEs:** Demo world-class AI observability to customers
3. **For Splunk:** Reference architecture for RAG + Splunk Observability
4. **For Customers:** Copy this exact pattern for their RAG deployments

### The Value Proposition

> "This RAG Lab demonstrates the complete AI platform:
> - **Build:** DSDL (custom models)
> - **Deploy:** RAG Reference Architecture (this lab)
> - **Optimize:** AI Toolkit (ML-driven tuning)
> - **Monitor:** Observability Cloud (end-to-end visibility)
>
> And it's all instrumented with OpenTelemetry from day one,
> giving you observability that scales from prototype to production."

---

## Appendix A: OpenLLMetry Coverage

### What OpenLLMetry Instruments Automatically

From [OpenLLMetry GitHub](https://github.com/traceloop/openllmetry):

**LLM Providers:**
- ✅ Ollama (our primary LLM)
- ✅ OpenAI (for comparison)
- ✅ Anthropic, Cohere, Mistral, etc.

**Vector Databases:**
- ✅ ChromaDB (our vector DB)
- ✅ Pinecone, Qdrant, Weaviate, Milvus

**Frameworks:**
- ✅ LangChain (if we add it)
- ✅ LlamaIndex (if we add it)
- ✅ CrewAI, Haystack

**Protocol:**
- ✅ MCP (Model Context Protocol) - We're using this!

**What This Means:**
- Minimal code changes
- Automatic span creation for LLM calls
- Automatic metrics (tokens, latency, cost)
- Standardized semantic conventions

---

## Appendix B: Sample Splunk Queries

### Query 1: Top 10 Slowest Queries

```spl
| from span
| where span.name="chat.process_query"
| stats avg(duration) as avg_ms, max(duration) as max_ms, count by query.text
| sort - avg_ms
| head 10
| table query.text avg_ms max_ms count
```

### Query 2: Cost by Model

```spl
| from span
| where span.name="chat.llm_generation"
| stats sum(llm.cost) as total_cost, count as queries by llm.model
| eval cost_per_query = total_cost / queries
| table llm.model total_cost queries cost_per_query
| sort - total_cost
```

### Query 3: Groundedness Over Time

```spl
| from span
| where span.name="chat.process_query"
| timechart avg(quality.groundedness) as avg_groundedness by settings.preset
```

### Query 4: Evidence Origin Distribution

```spl
| from span_event
| where event.name="evidence_created"
| stats count by evidence.origin_tool
| pie count by evidence.origin_tool
```

### Query 5: Failed Traces

```spl
| from span
| where span.status="error"
| stats count by error.type
| sort - count
| table error.type count
```

---

## Appendix C: Comparison Matrix

### Prometheus/Grafana vs Splunk Observability

| Feature | Prometheus + Grafana | Splunk Observability | Winner |
|---------|---------------------|---------------------|--------|
| **Infrastructure Metrics** | ✅ Excellent | ✅ Excellent | Tie |
| **Custom Metrics** | ✅ Excellent | ✅ Excellent | Tie |
| **Visualization** | ✅ Excellent | ✅ Excellent | Tie |
| **Open Source** | ✅ Yes | ❌ No (SaaS) | Prometheus |
| **Distributed Tracing** | ⚠️ Requires Tempo | ✅ Native | Splunk |
| **APM** | ❌ No | ✅ Yes | Splunk |
| **Log Correlation** | ⚠️ Requires Loki | ✅ Native | Splunk |
| **Automatic Service Discovery** | ⚠️ Limited | ✅ Excellent | Splunk |
| **Alerting** | ✅ Alertmanager | ✅ Native + AI | Splunk |
| **Business Metrics** | ⚠️ Manual | ✅ First-class | Splunk |
| **ML-driven Insights** | ❌ No | ✅ Yes (MLTK) | Splunk |
| **Cost** | ✅ Free | 💰 Paid (free tier available) | Prometheus |
| **Learning Curve** | ⚠️ Medium | ⚠️ Medium | Tie |
| **Cloud-Native** | ✅ Yes | ✅ Yes | Tie |

**Conclusion:** Use BOTH
- Prometheus/Grafana for teaching visualization
- Splunk Observability for production-grade monitoring

---

## Appendix D: References

### Documentation
- [OpenTelemetry](https://opentelemetry.io/)
- [OpenLLMetry](https://github.com/traceloop/openllmetry)
- [Splunk Observability Cloud](https://docs.splunk.com/Observability)
- [Splunk OpenTelemetry Collector](https://docs.splunk.com/Observability/gdi/opentelemetry/opentelemetry.html)

### Splunk Blogs
- [LLM Observability Explained](https://www.splunk.com/en_us/blog/learn/llm-observability.html)
- [End-to-End LLM Observability with RAG](https://www.splunk.com/en_us/blog/artificial-intelligence/how-we-built-end-to-end-llm-observability-with-splunk-and-rag.html)
- [Instrumenting LLM Apps with OpenLLMetry](https://lantern.splunk.com/Observability_Use_Cases/Monitor_Business/Instrumenting_LLM_applications_with_OpenLLMetry_and_Splunk)

### Internal Docs
- [SPLUNK_AI_PLATFORM_INTEGRATION.md](lab/SPLUNK_AI_PLATFORM_INTEGRATION.md)
- [CRITICAL_ANALYSIS_WORLD_CLASS_RAG.md](CRITICAL_ANALYSIS_WORLD_CLASS_RAG.md)
- [IMPLEMENTATION_PLAN_PHASE_1.md](IMPLEMENTATION_PLAN_PHASE_1.md)

---

**Status:** 🚀 READY FOR APPROVAL & IMPLEMENTATION
**Next Review:** After Week 2 (Core Implementation Complete)
**Owner:** AI Enablement Team
**Stakeholders:** Product (Observability), Engineering, Field Enablement, Customers

---

**Let's build world-class observability for world-class RAG.** 🎯



