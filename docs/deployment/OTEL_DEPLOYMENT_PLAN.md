# OpenTelemetry Integration Deployment Plan
**Project:** RAG Lab - Enterprise Observability
**Branch:** `otel`
**Timeline:** Week 1 (5 days)
**Status:** 🚦 READY TO START

---

## 📋 Executive Summary

### Objectives
1. **Fix critical bugs** blocking demo credibility (provenance, streaming, waterfall)
2. **Add enterprise observability** via OpenTelemetry + OpenLLMetry
3. **Maintain existing Prometheus/Grafana** stack (no disruption)
4. **Enable Splunk export** for enterprise customers

### Success Criteria
- ✅ All web sources correctly tagged with `origin_tool="web_search"`
- ✅ Conversations survive page refresh/navigation
- ✅ Waterfall shows all component timings (including KG)
- ✅ Distributed traces visible in OTel Collector
- ✅ LLM spans include token counts and model info
- ✅ Grafana dashboards link to traces via exemplars
- ✅ Zero regression in existing functionality
- ✅ All tests pass before merge

---

## 🎯 Phase Breakdown

### **Phase 1: Critical Bug Fixes (Days 1-2)**
**Goal:** Eliminate demo-breaking issues

**Tier 0 - Blockers**
- Provenance immutability
- Waterfall completeness
- Basic UX polish

### **Phase 2: Observability Foundation (Days 3-4)**
**Goal:** Add OTEL without disrupting existing monitoring

**Tier 1 - Infrastructure**
- OTel Collector deployment
- Service instrumentation
- OpenLLMetry integration

### **Phase 3: Resilience & Documentation (Day 5)**
**Goal:** Production-ready deployment

**Tier 2 - Hardening**
- Conversation persistence
- Documentation
- Testing & validation

---

## 📅 Day-by-Day Execution Plan

## **DAY 1: Provenance Immutability** 🔴 CRITICAL

### Morning (4 hours)

#### Task 1.1: Define Evidence Schema with Immutable Provenance
**File:** `services/common/evidence.py` (NEW)

**Implementation:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum

class OriginTool(str, Enum):
    """Source origin types - immutable after creation"""
    RAG = "rag"
    WEB_SEARCH = "web_search"
    RESEARCH_AGENT = "research_agent"

@dataclass(frozen=True)  # Immutable
class Evidence:
    """
    Immutable evidence object with guaranteed provenance.
    Once created, origin_tool cannot be changed.
    """
    # Core identification
    id: str
    content: str
    origin_tool: OriginTool  # IMMUTABLE

    # Source metadata
    url: Optional[str] = None
    domain: Optional[str] = None
    title: Optional[str] = None

    # Temporal metadata
    published_at: Optional[datetime] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    # Quality metadata
    is_primary: bool = False  # Primary vs secondary source
    score: float = 0.0

    # RAG-specific metadata
    doc_id: Optional[str] = None
    chunk_id: Optional[str] = None

    def to_dict(self):
        """Serialize to dict for API responses"""
        return {
            'id': self.id,
            'content': self.content,
            'origin_tool': self.origin_tool.value,
            'url': self.url,
            'domain': self.domain,
            'title': self.title,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'fetched_at': self.fetched_at.isoformat(),
            'is_primary': self.is_primary,
            'score': self.score,
            'doc_id': self.doc_id,
            'chunk_id': self.chunk_id,
        }
```

**Tests:** `tests/test_evidence.py`
```python
import pytest
from services.common.evidence import Evidence, OriginTool
from datetime import datetime

def test_evidence_immutability():
    """Evidence objects cannot be modified after creation"""
    evidence = Evidence(
        id="test-1",
        content="Test content",
        origin_tool=OriginTool.WEB_SEARCH,
        url="https://example.com"
    )

    # Should raise FrozenInstanceError
    with pytest.raises(Exception):
        evidence.origin_tool = OriginTool.RAG

def test_evidence_origin_preserved():
    """Origin tool is always preserved"""
    evidence = Evidence(
        id="test-2",
        content="Web content",
        origin_tool=OriginTool.WEB_SEARCH
    )

    serialized = evidence.to_dict()
    assert serialized['origin_tool'] == 'web_search'
```

**Acceptance:**
- ✅ Evidence class is immutable (frozen dataclass)
- ✅ origin_tool cannot be changed after creation
- ✅ Tests pass

---

#### Task 1.2: Update Search Service to Use Evidence Objects
**File:** `services/search/app/service.py` (MODIFY)

**Changes:**
1. Import Evidence class
2. Convert search results to Evidence objects at creation
3. Never overwrite origin_tool in merge/rerank
4. Pass Evidence objects through pipeline

**Implementation Steps:**
```python
# Add to imports
from services.common.evidence import Evidence, OriginTool

# In vector search function
def vector_search(query: str) -> List[Evidence]:
    """Returns Evidence objects with origin_tool=RAG"""
    results = vector_db_client.search(query)

    return [
        Evidence(
            id=f"rag-{result['id']}",
            content=result['content'],
            origin_tool=OriginTool.RAG,  # Set once, never changed
            doc_id=result['metadata'].get('doc_id'),
            chunk_id=result['id'],
            score=result['score'],
            title=result['metadata'].get('title'),
        )
        for result in results
    ]

# In web search function
def web_search(query: str) -> List[Evidence]:
    """Returns Evidence objects with origin_tool=WEB_SEARCH"""
    results = web_search_client.search(query)

    return [
        Evidence(
            id=f"web-{idx}",
            content=result['content'],
            origin_tool=OriginTool.WEB_SEARCH,  # Set once, never changed
            url=result['url'],
            domain=extract_domain(result['url']),
            title=result['title'],
            published_at=parse_date(result.get('published')),
            is_primary=is_primary_source(result['url']),
            score=result['score'],
        )
        for idx, result in enumerate(results)
    ]

# In merge function - preserve origin
def merge_results(rag_results: List[Evidence], web_results: List[Evidence]) -> List[Evidence]:
    """Merge results while preserving origin_tool"""
    all_results = rag_results + web_results

    # Deduplicate by content similarity
    deduped = deduplicate(all_results)

    # When deduplicating, KEEP the Evidence object, don't create new one
    # This preserves origin_tool
    return sorted(deduped, key=lambda e: e.score, reverse=True)
```

**Tests:** `tests/integration/test_search_provenance.py`
```python
def test_web_results_tagged_correctly():
    """Web search results have origin_tool=web_search"""
    response = requests.post(
        'http://localhost:8002/search',
        json={
            'query': 'latest AI news',
            'enable_web_search': True
        }
    )

    sources = response.json()['sources']
    web_sources = [s for s in sources if 'http' in s.get('url', '')]

    for source in web_sources:
        assert source['origin_tool'] == 'web_search', \
            f"Web source {source['url']} not tagged correctly"

def test_rag_results_tagged_correctly():
    """RAG results have origin_tool=rag"""
    response = requests.post(
        'http://localhost:8002/search',
        json={'query': 'test query', 'enable_web_search': False}
    )

    sources = response.json()['sources']
    for source in sources:
        assert source['origin_tool'] == 'rag'

def test_merge_preserves_origin():
    """Merging results preserves origin_tool"""
    response = requests.post(
        'http://localhost:8002/search',
        json={
            'query': 'test query',
            'enable_web_search': True,
            'enable_vector_search': True
        }
    )

    sources = response.json()['sources']

    # Should have both types
    origins = {s['origin_tool'] for s in sources}
    assert 'web_search' in origins or 'rag' in origins

    # No source should have origin changed
    for source in sources:
        assert source['origin_tool'] in ['web_search', 'rag', 'research_agent']
```

**Acceptance:**
- ✅ All search results are Evidence objects
- ✅ origin_tool set at creation
- ✅ Merge/rerank never changes origin_tool
- ✅ Integration tests pass

---

### Afternoon (4 hours)

#### Task 1.3: Update Frontend to Display Source Breakdown
**File:** `frontend/src/components/chat/SourceCard.tsx` (MODIFY)

**Changes:**
1. Display origin_tool badge
2. Color-code by origin type
3. Show published_at for temporal queries

```typescript
// Add origin badge
const OriginBadge = ({ origin }: { origin: string }) => {
  const badgeConfig = {
    web_search: { color: 'bg-blue-500', icon: '🌐', label: 'Web' },
    rag: { color: 'bg-green-500', icon: '📚', label: 'RAG' },
    research_agent: { color: 'bg-purple-500', icon: '🔬', label: 'Research' },
  };

  const config = badgeConfig[origin] || badgeConfig.rag;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-white ${config.color}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
};

// Update SourceCard component
export function SourceCard({ source }: { source: Source }) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-semibold">{source.title}</h4>
        <OriginBadge origin={source.origin_tool} />
      </div>

      {source.published_at && (
        <p className="text-sm text-muted-foreground mb-2">
          📅 Published: {new Date(source.published_at).toLocaleDateString()}
        </p>
      )}

      {source.url && (
        <a href={source.url} target="_blank" rel="noopener noreferrer"
           className="text-sm text-blue-600 hover:underline">
          {source.domain || source.url}
        </a>
      )}

      <p className="text-sm mt-2">{source.content.slice(0, 200)}...</p>
    </div>
  );
}
```

**File:** `frontend/src/components/chat/MessageItem.tsx` (MODIFY)

**Add source breakdown footer:**
```typescript
// Add after sources display
{message.sources && message.sources.length > 0 && (
  <div className="mt-3 pt-3 border-t">
    <SourceBreakdown sources={message.sources} />
  </div>
)}
```

**File:** `frontend/src/components/chat/SourceBreakdown.tsx` (NEW)
```typescript
import { Source } from '../../types/chat';

interface SourceBreakdownProps {
  sources: Source[];
}

export function SourceBreakdown({ sources }: SourceBreakdownProps) {
  const breakdown = sources.reduce((acc, source) => {
    const origin = source.origin_tool || 'rag';
    acc[origin] = (acc[origin] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="flex flex-wrap gap-2 text-sm">
      <span className="text-muted-foreground">Sources:</span>
      {breakdown.web_search && (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded">
          🌐 Web: {breakdown.web_search}
        </span>
      )}
      {breakdown.rag && (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded">
          📚 RAG: {breakdown.rag}
        </span>
      )}
      {breakdown.research_agent && (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded">
          🔬 Research: {breakdown.research_agent}
        </span>
      )}
    </div>
  );
}
```

**Acceptance:**
- ✅ Sources show origin badge
- ✅ Footer shows count by origin type
- ✅ Web sources show published date
- ✅ Visual distinction between source types

---

#### Task 1.4: Add Provenance Validator
**File:** `services/common/validators.py` (NEW)

```python
from typing import List
from services.common.evidence import Evidence, OriginTool

class ProvenanceValidator:
    """Validates provenance integrity across pipeline"""

    def __init__(self):
        self.violations = []

    def validate(self, evidence_list: List[Evidence]) -> bool:
        """
        Validates evidence list for provenance integrity.
        Returns True if valid, False if violations found.
        """
        self.violations = []

        for evidence in evidence_list:
            # Check 1: origin_tool is set
            if not evidence.origin_tool:
                self.violations.append({
                    'id': evidence.id,
                    'error': 'missing_origin_tool',
                    'message': 'Evidence missing origin_tool'
                })

            # Check 2: Web sources have URLs
            if evidence.origin_tool == OriginTool.WEB_SEARCH:
                if not evidence.url:
                    self.violations.append({
                        'id': evidence.id,
                        'error': 'web_source_no_url',
                        'message': 'Web source missing URL'
                    })

                if not evidence.domain:
                    self.violations.append({
                        'id': evidence.id,
                        'error': 'web_source_no_domain',
                        'message': 'Web source missing domain'
                    })

            # Check 3: RAG sources have doc_id
            if evidence.origin_tool == OriginTool.RAG:
                if not evidence.doc_id:
                    self.violations.append({
                        'id': evidence.id,
                        'error': 'rag_source_no_doc_id',
                        'message': 'RAG source missing doc_id'
                    })

        return len(self.violations) == 0

    def get_report(self) -> dict:
        """Return validation report"""
        return {
            'valid': len(self.violations) == 0,
            'violations': self.violations,
            'total_checked': len(self.violations)
        }
```

**Integration:** Add to search service response
```python
# In search service
validator = ProvenanceValidator()
if not validator.validate(evidence_list):
    logger.warning(f"Provenance violations: {validator.get_report()}")
    # Include in response for debugging
    response['provenance_report'] = validator.get_report()
```

**Acceptance:**
- ✅ Validator catches missing origin_tool
- ✅ Validator catches web sources without URLs
- ✅ Violations logged and reported
- ✅ Tests pass

---

### End of Day 1 Checklist
- [ ] Evidence schema defined and immutable
- [ ] Search service uses Evidence objects
- [ ] Frontend displays origin badges
- [ ] Source breakdown shows counts
- [ ] Provenance validator implemented
- [ ] All tests pass
- [ ] Commit + push to otel branch

---

## **DAY 2: Waterfall Completeness & UX Polish** ✅

### Morning (4 hours)

#### Task 2.1: Add Timing Instrumentation to All Services
**Goal:** Every service reports start/stop times for operations

**File:** `services/common/timing.py` (NEW)
```python
import time
from contextlib import contextmanager
from typing import Dict, Optional

class TimingCollector:
    """Collect timing data across service calls"""

    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}

    @contextmanager
    def measure(self, operation: str):
        """Context manager for timing operations"""
        start = time.time()
        self.start_times[operation] = start

        try:
            yield
        finally:
            duration = (time.time() - start) * 1000  # ms
            self.timings[operation] = duration

    def get_timings(self) -> Dict[str, float]:
        """Get all recorded timings"""
        return self.timings.copy()

    def reset(self):
        """Clear all timings"""
        self.timings.clear()
        self.start_times.clear()
```

**Usage in services:**
```python
from services.common.timing import TimingCollector

def search(query: str, config: dict) -> dict:
    timer = TimingCollector()

    with timer.measure('total'):
        # Vector search
        if config.get('enable_vector_search'):
            with timer.measure('vector_search'):
                vector_results = vector_search(query)

        # Web search
        if config.get('enable_web_search'):
            with timer.measure('web_search'):
                web_results = web_search(query)

        # Knowledge graph
        if config.get('enable_knowledge_graph'):
            with timer.measure('kg_expand'):
                kg_results = kg_expand(vector_results)

        # Reranking
        if config.get('enable_reranking'):
            with timer.measure('rerank'):
                results = rerank(all_results, query)

    return {
        'results': results,
        'timings': timer.get_timings()
    }
```

**Files to modify:**
- `services/search/app/service.py` - Add timing to search operations
- `services/knowledge-graph/app/service.py` - Add timing to KG operations
- `services/reranker/app/service.py` - Add timing to rerank
- `services/chat/app/service.py` - Add timing to LLM calls
- `services/web-search/app/service.py` - Add timing to web search

**Acceptance:**
- ✅ Each service returns `timings` dict
- ✅ KG timing is no longer 0ms
- ✅ Timings propagate to API gateway

---

#### Task 2.2: Aggregate Timings in API Gateway
**File:** `services/api-gateway/app/service.py` (MODIFY)

```python
def aggregate_timings(responses: List[dict]) -> dict:
    """Aggregate timings from multiple service calls"""
    aggregated = {}

    for response in responses:
        if 'timings' in response:
            for key, value in response['timings'].items():
                if key in aggregated:
                    # If duplicate keys, sum them
                    aggregated[key] += value
                else:
                    aggregated[key] = value

    return aggregated

# In ask endpoint
@app.route('/api/ask', methods=['POST'])
def ask():
    gateway_timer = TimingCollector()

    with gateway_timer.measure('total_request'):
        # Call search service
        with gateway_timer.measure('search_service'):
            search_response = call_search_service(query, config)

        # Call chat service
        with gateway_timer.measure('chat_service'):
            chat_response = call_chat_service(query, context, config)

    # Aggregate all timings
    all_timings = gateway_timer.get_timings()
    if 'timings' in search_response:
        all_timings.update(search_response['timings'])
    if 'timings' in chat_response:
        all_timings.update(chat_response['timings'])

    return {
        'answer': chat_response['answer'],
        'sources': search_response['sources'],
        'metrics': {
            'timings': all_timings,
            'total_ms': all_timings.get('total_request', 0)
        }
    }
```

**Acceptance:**
- ✅ API gateway aggregates timings from all services
- ✅ Response includes complete timing breakdown
- ✅ No timing data is lost

---

### Afternoon (4 hours)

#### Task 2.3: Update Frontend Waterfall Chart
**File:** `frontend/src/components/metrics/WaterfallChart.tsx` (MODIFY)

```typescript
interface WaterfallData {
  total_request: number;
  search_service: number;
  vector_search?: number;
  bm25_search?: number;
  kg_expand?: number;
  rerank?: number;
  web_search?: number;
  chat_service: number;
  llm_generation?: number;
}

export function WaterfallChart({ timings }: { timings: WaterfallData }) {
  const stages = [
    { key: 'vector_search', label: 'Vector Search', color: 'bg-blue-500' },
    { key: 'bm25_search', label: 'BM25 Search', color: 'bg-cyan-500' },
    { key: 'kg_expand', label: 'Knowledge Graph', color: 'bg-purple-500' },
    { key: 'rerank', label: 'Reranking', color: 'bg-orange-500' },
    { key: 'web_search', label: 'Web Search', color: 'bg-green-500' },
    { key: 'llm_generation', label: 'LLM Generation', color: 'bg-red-500' },
  ];

  const totalTime = timings.total_request || 0;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Performance Breakdown</h3>

      {stages.map(stage => {
        const duration = timings[stage.key as keyof WaterfallData] || 0;
        if (duration === 0) return null;

        const percentage = totalTime > 0 ? (duration / totalTime) * 100 : 0;

        return (
          <div key={stage.key} className="flex items-center gap-2">
            <div className="w-32 text-sm text-muted-foreground">
              {stage.label}
            </div>
            <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
              <div
                className={`h-full ${stage.color} flex items-center px-2`}
                style={{ width: `${Math.max(percentage, 5)}%` }}
              >
                <span className="text-xs font-medium text-white">
                  {duration.toFixed(0)}ms
                </span>
              </div>
            </div>
            <div className="w-12 text-sm text-right text-muted-foreground">
              {percentage.toFixed(1)}%
            </div>
          </div>
        );
      })}

      <div className="pt-2 border-t flex justify-between text-sm">
        <span className="font-semibold">Total</span>
        <span className="font-semibold">{totalTime.toFixed(0)}ms</span>
      </div>
    </div>
  );
}
```

**Acceptance:**
- ✅ Waterfall shows all enabled stages
- ✅ KG timing visible when enabled
- ✅ Percentages add up correctly
- ✅ No 0ms stages shown

---

#### Task 2.4: UX Polish (Preset Highlight, Copy Buttons, KG Reset)

**File:** `frontend/src/stores/configStore.ts` (VERIFY)
- Ensure `currentPreset` saved to localStorage
- Verify preset state persists across refresh

**File:** `frontend/src/components/chat/MessageItem.tsx` (ADD)
```typescript
// Add copy button to prompt
<div className="flex items-start justify-between gap-2">
  <div className="flex-1">
    <ReactMarkdown>{message.content}</ReactMarkdown>
  </div>
  <Button
    variant="ghost"
    size="sm"
    onClick={() => {
      navigator.clipboard.writeText(message.content);
      toast.success('Copied to clipboard');
    }}
    aria-label="Copy prompt as markdown"
  >
    <Copy className="h-4 w-4" />
  </Button>
</div>
```

**File:** `services/knowledge-graph/app/service.py` (MODIFY)
```python
# Add version tracking
kg_version = 0

@app.route('/reset', methods=['POST'])
def reset_graph():
    global kg_version
    global knowledge_graph

    knowledge_graph = nx.DiGraph()
    kg_version += 1  # Increment version

    # Save to disk
    save_graph()

    return jsonify({
        'message': 'Knowledge graph reset',
        'version': kg_version,
        'nodes': 0,
        'edges': 0
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'version': kg_version,
        'nodes': knowledge_graph.number_of_nodes(),
        'edges': knowledge_graph.number_of_edges(),
    })
```

**File:** `frontend/src/stores/kgStore.ts` (NEW)
```typescript
interface KGStore {
  version: number;
  nodeCount: number;
  edgeCount: number;
  setStats: (stats: { version: number; nodes: number; edges: number }) => void;
}

export const useKGStore = create<KGStore>((set) => ({
  version: 0,
  nodeCount: 0,
  edgeCount: 0,
  setStats: (stats) => set({
    version: stats.version,
    nodeCount: stats.nodes,
    edgeCount: stats.edges,
  }),
}));
```

**Acceptance:**
- ✅ Preset highlight persists across navigation
- ✅ Copy buttons work for prompt and response
- ✅ KG stats update immediately after reset
- ✅ Research agent reflects new KG version

---

### End of Day 2 Checklist
- [ ] All services emit timing data
- [ ] KG timing visible in waterfall
- [ ] Frontend displays complete waterfall
- [ ] Copy buttons work
- [ ] Preset state persists
- [ ] KG reset invalidates caches
- [ ] All tests pass
- [ ] Commit + push

---

## **DAY 3: OpenTelemetry Foundation** 🔭

### Morning (4 hours)

#### Task 3.1: Deploy OTel Collector Container
**File:** `docker-compose.yml` (ADD)

```yaml
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: rag-otel-collector
    networks:
      - rag-network
    ports:
      - "4317:4317"  # OTLP gRPC receiver
      - "4318:4318"  # OTLP HTTP receiver
      - "8888:8888"  # Prometheus metrics from collector
      - "8889:8889"  # Prometheus exporter for services
    volumes:
      - ./monitoring/otel/otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro
    command: ["--config=/etc/otelcol-contrib/config.yaml"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:13133/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**File:** `monitoring/otel/otel-collector-config.yaml` (NEW)

```yaml
receivers:
  # Receive traces and metrics from services
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins:
            - "http://localhost:3000"
            - "http://localhost:8000"

  # Scrape Prometheus metrics from services
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 15s
          static_configs:
            - targets: ['localhost:8888']

processors:
  # Add resource attributes
  resource:
    attributes:
      - key: service.namespace
        value: "rag-lab"
        action: insert
      - key: deployment.environment
        value: "development"
        action: insert

  # Batch traces and metrics
  batch:
    timeout: 10s
    send_batch_size: 1024

  # Sample traces (optional, for high volume)
  probabilistic_sampler:
    sampling_percentage: 100  # 100% for dev, lower for prod

exporters:
  # Export to Prometheus (for Grafana)
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: "otel"
    send_timestamps: true
    metric_expiration: 5m

  # Export to Splunk (optional, configure when needed)
  splunk_hec:
    # Disabled by default, configure when Splunk available
    endpoint: "${SPLUNK_HEC_ENDPOINT}"
    token: "${SPLUNK_HEC_TOKEN}"
    source: "otel"
    sourcetype: "otel"
    index: "rag_lab"
    max_content_length_traces: 2097152
    disable_compression: false
    timeout: 10s

  # Debug logging (for development)
  logging:
    loglevel: info
    sampling_initial: 5
    sampling_thereafter: 200

  # Jaeger for trace visualization (optional)
  jaeger:
    endpoint: "jaeger:14250"
    tls:
      insecure: true

service:
  pipelines:
    # Traces pipeline
    traces:
      receivers: [otlp]
      processors: [resource, batch, probabilistic_sampler]
      exporters: [logging, prometheus]  # Add splunk_hec when ready

    # Metrics pipeline
    metrics:
      receivers: [otlp, prometheus]
      processors: [resource, batch]
      exporters: [prometheus, logging]  # Add splunk_hec when ready

  extensions:
    health_check:
      endpoint: :13133
    pprof:
      endpoint: :1777
    zpages:
      endpoint: :55679

extensions: [health_check, pprof, zpages]
```

**File:** `config.env` (ADD)
```bash
# OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
OTEL_SERVICE_NAME=rag-lab
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=none
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

# Splunk Configuration (optional, configure when needed)
# SPLUNK_HEC_ENDPOINT=https://your-splunk.com:8088/services/collector
# SPLUNK_HEC_TOKEN=your-token-here
```

**Acceptance:**
- ✅ OTel Collector container starts
- ✅ Health check passes
- ✅ Ports 4317, 4318, 8889 accessible
- ✅ Configuration valid

---

#### Task 3.2: Instrument API Gateway with OTEL
**File:** `services/api-gateway/requirements.txt` (ADD)

```txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-flask==0.42b0
opentelemetry-instrumentation-requests==0.42b0
opentelemetry-exporter-otlp==1.21.0
```

**File:** `services/api-gateway/app/service.py` (MODIFY)

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace import Status, StatusCode

# Initialize OpenTelemetry
resource = Resource.create({
    "service.name": "api-gateway",
    "service.version": os.getenv("VERSION", "1.3.0"),
    "deployment.environment": os.getenv("ENVIRONMENT", "development"),
})

# Set up tracer provider
trace_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces"),
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Get tracer
tracer = trace.get_tracer(__name__)

# Auto-instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Add trace context to all responses
@app.after_request
def add_trace_id(response):
    span = trace.get_current_span()
    if span:
        trace_id = format(span.get_span_context().trace_id, '032x')
        response.headers['X-Trace-Id'] = trace_id
    return response

# Use spans in endpoint
@app.route('/api/ask', methods=['POST'])
def ask():
    with tracer.start_as_current_span("ask_endpoint") as span:
        try:
            data = request.json
            query = data.get('query')

            # Add span attributes
            span.set_attribute("query.length", len(query))
            span.set_attribute("query.hash", hashlib.md5(query.encode()).hexdigest()[:8])

            # Call search service with tracing
            with tracer.start_as_current_span("search_service_call"):
                search_response = call_search_service(query, config)
                span.set_attribute("search.sources_found", len(search_response.get('sources', [])))

            # Call chat service with tracing
            with tracer.start_as_current_span("chat_service_call"):
                chat_response = call_chat_service(query, context, config)
                span.set_attribute("chat.tokens_generated", chat_response.get('tokens', 0))

            span.set_status(Status(StatusCode.OK))
            return jsonify(response)

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
```

**Acceptance:**
- ✅ API Gateway sends traces to collector
- ✅ Flask requests auto-instrumented
- ✅ HTTP requests auto-instrumented
- ✅ Custom spans for service calls
- ✅ Trace IDs in response headers

---

### Afternoon (4 hours)

#### Task 3.3: Instrument Search Service
**File:** `services/search/requirements.txt` (ADD)

```txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-flask==0.42b0
opentelemetry-instrumentation-requests==0.42b0
opentelemetry-exporter-otlp==1.21.0
```

**File:** `services/search/app/service.py` (MODIFY)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import Status, StatusCode

# Initialize tracer (similar to gateway)
resource = Resource.create({
    "service.name": "search-service",
    "service.version": os.getenv("VERSION", "1.3.0"),
})
trace_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces"),
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

FlaskInstrumentor().instrument_app(app)

@app.route('/search', methods=['POST'])
def search():
    with tracer.start_as_current_span("search_operation") as span:
        config = request.json

        span.set_attribute("config.enable_vector", config.get('enable_vector_search', False))
        span.set_attribute("config.enable_web", config.get('enable_web_search', False))
        span.set_attribute("config.enable_kg", config.get('enable_knowledge_graph', False))

        results = []

        # Vector search
        if config.get('enable_vector_search'):
            with tracer.start_as_current_span("vector_search") as vs_span:
                vector_results = perform_vector_search(query)
                vs_span.set_attribute("results.count", len(vector_results))
                results.extend(vector_results)

        # Web search
        if config.get('enable_web_search'):
            with tracer.start_as_current_span("web_search") as ws_span:
                web_results = perform_web_search(query)
                ws_span.set_attribute("results.count", len(web_results))
                results.extend(web_results)

        # Knowledge graph expansion
        if config.get('enable_knowledge_graph'):
            with tracer.start_as_current_span("kg_expand") as kg_span:
                kg_results = expand_with_kg(results)
                kg_span.set_attribute("kg.nodes_added", len(kg_results) - len(results))
                results = kg_results

        span.set_attribute("results.total", len(results))
        span.set_status(Status(StatusCode.OK))

        return jsonify({'sources': results})
```

**Acceptance:**
- ✅ Search service sends traces
- ✅ Nested spans for each operation
- ✅ Span attributes capture config and results
- ✅ Traces link to gateway span (parent)

---

#### Task 3.4: Update Prometheus to Scrape OTel Collector
**File:** `monitoring/prometheus/prometheus.yml` (MODIFY)

```yaml
scrape_configs:
  # Existing scrape configs...

  # Add OTel Collector metrics
  - job_name: 'otel-collector'
    scrape_interval: 15s
    static_configs:
      - targets: ['otel-collector:8889']
        labels:
          service: 'otel-collector'

  # Add OTel-instrumented services (if they expose /metrics)
  - job_name: 'otel-services'
    scrape_interval: 15s
    static_configs:
      - targets:
        - 'api-gateway:8000'
        - 'search-service:8002'
        labels:
          otel_instrumented: 'true'
```

**File:** `monitoring/grafana/datasources/otel.yml` (NEW)

```yaml
apiVersion: 1

datasources:
  - name: OTel Traces
    type: jaeger
    access: proxy
    url: http://otel-collector:16686
    isDefault: false
    editable: true
```

**Acceptance:**
- ✅ Prometheus scrapes OTel collector
- ✅ OTEL metrics visible in Prometheus
- ✅ Grafana can query OTEL metrics
- ✅ No disruption to existing metrics

---

### End of Day 3 Checklist
- [ ] OTel Collector deployed and healthy
- [ ] API Gateway instrumented
- [ ] Search Service instrumented
- [ ] Traces visible in collector logs
- [ ] Prometheus scrapes OTEL metrics
- [ ] No errors in service logs
- [ ] All tests pass
- [ ] Commit + push

---

## **DAY 4: OpenLLMetry + LLM Spans** 🤖

### Morning (4 hours)

#### Task 4.1: Install OpenLLMetry
**File:** `services/chat/requirements.txt` (ADD)

```txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-flask==0.42b0
opentelemetry-exporter-otlp==1.21.0
traceloop-sdk==0.21.0  # OpenLLMetry
```

**File:** `services/chat/app/service.py` (MODIFY)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow, task

# Initialize OpenTelemetry
resource = Resource.create({
    "service.name": "chat-service",
    "service.version": os.getenv("VERSION", "1.3.0"),
})
trace_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces"),
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Initialize OpenLLMetry
Traceloop.init(
    app_name="rag-chat-service",
    disable_batch=False,
    exporter=otlp_exporter,
)

tracer = trace.get_tracer(__name__)

# Decorate LLM functions
@task(name="ollama_generate")
def call_ollama(prompt: str, model: str, config: dict) -> dict:
    """Call Ollama with OpenLLMetry tracking"""

    # OpenLLMetry will auto-capture this
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "temperature": config.get('temperature', 0.7),
            "max_tokens": config.get('max_tokens', 2000),
            "stream": False,
        }
    )

    result = response.json()

    # Manually add custom attributes
    span = trace.get_current_span()
    span.set_attribute("llm.provider", "ollama")
    span.set_attribute("llm.model", model)
    span.set_attribute("llm.temperature", config.get('temperature', 0.7))
    span.set_attribute("llm.max_tokens", config.get('max_tokens', 2000))
    span.set_attribute("llm.prompt_tokens", result.get('prompt_eval_count', 0))
    span.set_attribute("llm.completion_tokens", result.get('eval_count', 0))
    span.set_attribute("llm.total_tokens",
                      result.get('prompt_eval_count', 0) + result.get('eval_count', 0))

    # Calculate estimated cost (for education)
    prompt_tokens = result.get('prompt_eval_count', 0)
    completion_tokens = result.get('eval_count', 0)
    estimated_cost = calculate_cost(model, prompt_tokens, completion_tokens)
    span.set_attribute("llm.estimated_cost_usd", estimated_cost)

    # Add prompt hash for deduplication analysis
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    span.set_attribute("llm.prompt_hash", prompt_hash)

    return result

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost for educational purposes (Ollama is free, but show what it would cost)"""
    # Pricing per 1M tokens (simulated)
    pricing = {
        'llama3.1:8b': {'input': 0.10, 'output': 0.30},
        'llama3.2:3b': {'input': 0.05, 'output': 0.15},
        'qwen2.5:14b': {'input': 0.15, 'output': 0.45},
    }

    model_pricing = pricing.get(model, {'input': 0.10, 'output': 0.30})

    input_cost = (prompt_tokens / 1_000_000) * model_pricing['input']
    output_cost = (completion_tokens / 1_000_000) * model_pricing['output']

    return round(input_cost + output_cost, 6)

@workflow(name="rag_generation")
def generate_answer(query: str, context: List[Evidence], config: dict) -> dict:
    """Generate answer with RAG context"""

    # Build prompt
    prompt = build_rag_prompt(query, context)

    # Call LLM (OpenLLMetry will track this as a child span)
    model = config.get('chat_model', 'llama3.1:8b')
    result = call_ollama(prompt, model, config)

    return {
        'answer': result['response'],
        'model_used': model,
        'tokens': {
            'prompt': result.get('prompt_eval_count', 0),
            'completion': result.get('eval_count', 0),
            'total': result.get('prompt_eval_count', 0) + result.get('eval_count', 0),
        },
        'estimated_cost_usd': calculate_cost(
            model,
            result.get('prompt_eval_count', 0),
            result.get('eval_count', 0)
        )
    }
```

**Acceptance:**
- ✅ LLM calls create spans with OpenLLMetry attributes
- ✅ Token counts visible in spans
- ✅ Model name and provider tracked
- ✅ Estimated cost calculated
- ✅ Prompt hashes for deduplication

---

### Afternoon (4 hours)

#### Task 4.2: Add LLM Spans to Model Router
**File:** `services/model-router/app/service.py` (MODIFY)

Similar instrumentation to chat service, tracking model selection decisions.

**File:** `services/model-router/requirements.txt` (ADD)
```txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
traceloop-sdk==0.21.0
```

#### Task 4.3: Create Grafana Dashboard for Traces
**File:** `monitoring/grafana/dashboards/otel-traces.json` (NEW)

```json
{
  "dashboard": {
    "title": "RAG Lab - Distributed Traces",
    "panels": [
      {
        "title": "Request Traces",
        "type": "traces",
        "datasource": "OTel Traces",
        "targets": [
          {
            "query": "service.name=\"api-gateway\""
          }
        ]
      },
      {
        "title": "LLM Token Usage",
        "type": "timeseries",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(llm_total_tokens[5m])"
          }
        ]
      },
      {
        "title": "LLM Cost by Model",
        "type": "piechart",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "sum by (llm_model) (llm_estimated_cost_usd)"
          }
        ]
      },
      {
        "title": "Trace Latency Percentiles",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(trace_duration_seconds_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(trace_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(trace_duration_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      }
    ]
  }
}
```

#### Task 4.4: Add Exemplars to Link Grafana → Traces
**File:** `services/common/metrics.py` (MODIFY)

```python
from prometheus_client import Histogram, Counter
from opentelemetry import trace

# Create histogram with exemplars
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
)

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record request with trace exemplar"""
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, '032x')

    # Add exemplar (trace ID)
    request_duration.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).observe(duration, exemplar={'trace_id': trace_id})
```

**Acceptance:**
- ✅ Grafana dashboard shows traces
- ✅ LLM metrics visible (tokens, cost)
- ✅ Latency percentiles displayed
- ✅ Exemplars link metrics to traces
- ✅ Click metric in Grafana → view trace

---

### End of Day 4 Checklist
- [ ] OpenLLMetry installed
- [ ] LLM calls create spans with token counts
- [ ] Model selection traced
- [ ] Grafana dashboard for traces
- [ ] Exemplars link metrics → traces
- [ ] Cost estimation visible
- [ ] All tests pass
- [ ] Commit + push

---

## **DAY 5: Conversation Persistence & Documentation** 💾

### Morning (4 hours)

#### Task 5.1: Add Conversation Database
**File:** `services/api-gateway/app/db.py` (NEW)

```python
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json

class ConversationDB:
    """SQLite database for conversation persistence"""

    def __init__(self, db_path: str = '/data/conversations.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    metadata TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    sources TEXT,
                    metrics TEXT,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversation_messages
                ON messages(conversation_id, timestamp)
            ''')

            conn.commit()

    def create_conversation(self, conversation_id: str, user_id: str) -> dict:
        """Create new conversation"""
        now = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO conversations (conversation_id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)',
                (conversation_id, user_id, now, now)
            )
            conn.commit()

        return {
            'conversation_id': conversation_id,
            'created_at': now.isoformat(),
        }

    def add_message(self, conversation_id: str, message: dict) -> dict:
        """Add message to conversation"""
        now = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO messages
                (message_id, conversation_id, role, content, sources, metrics, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                message['id'],
                conversation_id,
                message['role'],
                message['content'],
                json.dumps(message.get('sources', [])),
                json.dumps(message.get('metrics', {})),
                now
            ))

            # Update conversation updated_at
            conn.execute(
                'UPDATE conversations SET updated_at = ? WHERE conversation_id = ?',
                (now, conversation_id)
            )

            conn.commit()

        return message

    def get_messages(self, conversation_id: str, after_message_id: Optional[str] = None) -> List[dict]:
        """Get messages for conversation, optionally after a specific message"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if after_message_id:
                # Get timestamp of reference message
                cursor.execute(
                    'SELECT timestamp FROM messages WHERE message_id = ?',
                    (after_message_id,)
                )
                ref_timestamp = cursor.fetchone()
                if not ref_timestamp:
                    return []

                # Get messages after that timestamp
                cursor.execute('''
                    SELECT * FROM messages
                    WHERE conversation_id = ? AND timestamp > ?
                    ORDER BY timestamp ASC
                ''', (conversation_id, ref_timestamp['timestamp']))
            else:
                # Get all messages
                cursor.execute('''
                    SELECT * FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                ''', (conversation_id,))

            rows = cursor.fetchall()

            return [
                {
                    'id': row['message_id'],
                    'role': row['role'],
                    'content': row['content'],
                    'sources': json.loads(row['sources']) if row['sources'] else [],
                    'metrics': json.loads(row['metrics']) if row['metrics'] else {},
                    'timestamp': row['timestamp'],
                }
                for row in rows
            ]
```

**File:** `docker-compose.yml` (MODIFY)
```yaml
  api-gateway:
    volumes:
      # ... existing volumes ...
      - conversations-data:/data  # Add this

volumes:
  # ... existing volumes ...
  conversations-data:  # Add this
```

**Acceptance:**
- ✅ Database schema created
- ✅ Conversations can be created
- ✅ Messages can be added
- ✅ Messages can be retrieved
- ✅ After_message_id filtering works

---

#### Task 5.2: Add Polling Endpoint
**File:** `services/api-gateway/app/routes/conversations.py` (NEW)

```python
from flask import Blueprint, request, jsonify
from services.api-gateway.app.db import ConversationDB
import uuid

conversations_bp = Blueprint('conversations', __name__)
db = ConversationDB()

@conversations_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    data = request.json
    user_id = data.get('user_id', 'anonymous')

    conversation_id = str(uuid.uuid4())
    conversation = db.create_conversation(conversation_id, user_id)

    return jsonify(conversation), 201

@conversations_bp.route('/conversations/<conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    """Get messages for a conversation, with optional polling"""
    after_message_id = request.args.get('after')

    messages = db.get_messages(conversation_id, after_message_id)

    return jsonify({
        'conversation_id': conversation_id,
        'messages': messages,
        'count': len(messages),
    })

@conversations_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
def add_message(conversation_id):
    """Add a message to a conversation"""
    data = request.json

    message = {
        'id': str(uuid.uuid4()),
        'role': data['role'],
        'content': data['content'],
        'sources': data.get('sources', []),
        'metrics': data.get('metrics', {}),
    }

    db.add_message(conversation_id, message)

    return jsonify(message), 201
```

**File:** `services/api-gateway/app/service.py` (MODIFY)
```python
from services.api-gateway.app.routes.conversations import conversations_bp

app.register_blueprint(conversations_bp, url_prefix='/api')
```

**Acceptance:**
- ✅ Can create conversation
- ✅ Can add messages
- ✅ Can poll for new messages
- ✅ Polling with after_message_id works

---

### Afternoon (4 hours)

#### Task 5.3: Update Frontend to Use Polling
**File:** `frontend/src/hooks/useConversationPolling.ts` (NEW)

```typescript
import { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { ChatMessage } from '../types/chat';

export function useConversationPolling(conversationId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isPolling, setIsPolling] = useState(false);
  const lastMessageIdRef = useRef<string | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const pollForMessages = async () => {
    if (!conversationId) return;

    try {
      const params = lastMessageIdRef.current
        ? { after: lastMessageIdRef.current }
        : {};

      const response = await api.getConversationMessages(conversationId, params);

      if (response.messages.length > 0) {
        setMessages(prev => [...prev, ...response.messages]);
        lastMessageIdRef.current = response.messages[response.messages.length - 1].id;
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  };

  const startPolling = () => {
    if (pollIntervalRef.current) return;

    setIsPolling(true);
    pollIntervalRef.current = setInterval(pollForMessages, 2000);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  };

  // Load initial messages and start polling
  useEffect(() => {
    if (!conversationId) return;

    const loadInitialMessages = async () => {
      const response = await api.getConversationMessages(conversationId);
      setMessages(response.messages);

      if (response.messages.length > 0) {
        lastMessageIdRef.current = response.messages[response.messages.length - 1].id;
      }

      startPolling();
    };

    loadInitialMessages();

    return () => stopPolling();
  }, [conversationId]);

  return {
    messages,
    isPolling,
    startPolling,
    stopPolling,
    setMessages,
  };
}
```

**File:** `frontend/src/components/chat/ChatInterface.tsx` (MODIFY)

```typescript
import { useConversationPolling } from '../../hooks/useConversationPolling';

export function ChatInterface() {
  const [conversationId, setConversationId] = useState<string | null>(() => {
    return localStorage.getItem('current_conversation_id');
  });

  const { messages, isPolling, startPolling, stopPolling, setMessages } =
    useConversationPolling(conversationId);

  // Create conversation on mount if none exists
  useEffect(() => {
    if (!conversationId) {
      const createConversation = async () => {
        const response = await api.createConversation();
        setConversationId(response.conversation_id);
        localStorage.setItem('current_conversation_id', response.conversation_id);
      };
      createConversation();
    }
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!conversationId) return;

    // Add user message
    await api.addMessage(conversationId, {
      role: 'user',
      content,
    });

    // Backend will process and add assistant response
    // Polling will pick it up
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <h2>Chat</h2>
        <div className="flex items-center gap-2">
          {isPolling && (
            <span className="text-sm text-muted-foreground">
              🔄 Polling for updates...
            </span>
          )}
        </div>
      </div>

      <MessageList messages={messages} />
      <InputBar onSend={handleSendMessage} />
    </div>
  );
}
```

**Acceptance:**
- ✅ Frontend creates conversation on mount
- ✅ Polling starts automatically
- ✅ New messages appear without refresh
- ✅ Page refresh resumes polling
- ✅ No duplicate messages

---

#### Task 5.4: Documentation

**File:** `docs/deployment/OTEL_IMPLEMENTATION_GUIDE.md` (NEW)

```markdown
# OpenTelemetry Implementation Guide

## Overview
RAG Lab uses OpenTelemetry for distributed tracing and LLM observability.

## Architecture
- **OTel Collector**: Central telemetry hub
- **Instrumented Services**: API Gateway, Search, Chat
- **Exporters**: Prometheus (metrics), Splunk (traces)
- **OpenLLMetry**: LLM-specific instrumentation

## Key Components

### 1. Trace Collection
All HTTP requests generate traces with:
- Request context (method, endpoint, status)
- Timing information
- Custom attributes (query, config)
- Error details

### 2. LLM Spans
LLM calls include:
- `llm.provider`: "ollama" or "vllm"
- `llm.model`: Model name
- `llm.prompt_tokens`: Input token count
- `llm.completion_tokens`: Output token count
- `llm.total_tokens`: Total tokens
- `llm.estimated_cost_usd`: Cost estimate
- `llm.prompt_hash`: Prompt deduplication

### 3. Service Mesh
Traces flow: Frontend → API Gateway → Search → Vector DB
                                   ↓
                                  Chat → Ollama

## Configuration

### Environment Variables
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
OTEL_SERVICE_NAME=rag-lab
OTEL_TRACES_EXPORTER=otlp
```

### Splunk Export
To enable Splunk:
1. Set environment variables:
```bash
SPLUNK_HEC_ENDPOINT=https://your-splunk.com:8088/services/collector
SPLUNK_HEC_TOKEN=your-token
```

2. Update `otel-collector-config.yaml`:
```yaml
exporters:
  splunk_hec:
    endpoint: "${SPLUNK_HEC_ENDPOINT}"
    token: "${SPLUNK_HEC_TOKEN}"

service:
  pipelines:
    traces:
      exporters: [splunk_hec, prometheus, logging]
```

## Viewing Traces

### Grafana
1. Navigate to http://localhost:3001
2. Select "OTel Traces" datasource
3. Query by service name or trace ID

### Trace ID in Response
Every API response includes `X-Trace-Id` header:
```bash
curl -i http://localhost:8000/api/ask
X-Trace-Id: 5f9c8d7e6a5b4c3d2e1f0a9b8c7d6e5f
```

## Best Practices

### 1. Span Naming
- Use descriptive names: `search_operation`, not `func1`
- Include operation type: `db_query_users`, not `query`

### 2. Attributes
- Add context: `query.length`, `config.enable_web`
- Avoid PII: Hash queries, don't log full text
- Use consistent keys: `llm.model` not `model_name`

### 3. Error Handling
```python
try:
    result = risky_operation()
    span.set_status(Status(StatusCode.OK))
except Exception as e:
    span.set_status(Status(StatusCode.ERROR, str(e)))
    span.record_exception(e)
    raise
```

## Troubleshooting

### No Traces in Collector
1. Check service logs for OTLP errors
2. Verify OTEL_EXPORTER_OTLP_ENDPOINT
3. Check collector health: `curl http://localhost:13133`

### High Cardinality Warnings
Reduce attribute values:
- Don't use full query text (use hash)
- Limit enum values (group rare cases)

### Performance Impact
- Sampling: Set to 10% in production
- Batch size: Increase to 1024 for high volume
- Async export: Always use BatchSpanProcessor

## Cost Analysis
Token tracking enables cost analysis:
```sql
SELECT
  llm.model,
  SUM(llm.prompt_tokens) as total_input,
  SUM(llm.completion_tokens) as total_output,
  SUM(llm.estimated_cost_usd) as total_cost
FROM traces
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY llm.model
```
```

**File:** `docs/deployment/CONVERSATION_PERSISTENCE.md` (NEW)

See implementation details for conversation persistence...

**File:** `README.md` (UPDATE)

Add section:
```markdown
## 🔭 Observability

RAG Lab includes enterprise-grade observability:

### Distributed Tracing
- **OpenTelemetry**: Full request traces across all services
- **OpenLLMetry**: LLM-specific instrumentation with token counts
- **Trace IDs**: Every response includes trace ID for debugging

### Metrics
- **Prometheus**: Time-series metrics (latency, throughput, errors)
- **Grafana**: Pre-built dashboards for RAG pipeline visualization
- **Exemplars**: Click metric → view trace

### LLM Visibility
- Token usage per request
- Model performance comparison
- Cost estimation (educational)
- Prompt deduplication analysis

### Splunk Integration
Export traces to Splunk for enterprise compliance:
```bash
export SPLUNK_HEC_ENDPOINT=https://your-splunk.com:8088
export SPLUNK_HEC_TOKEN=your-token
docker compose up -d
```

See [OTEL Implementation Guide](docs/deployment/OTEL_IMPLEMENTATION_GUIDE.md) for details.
```

**Acceptance:**
- ✅ Complete OTEL implementation guide
- ✅ Conversation persistence documented
- ✅ README updated with observability section
- ✅ Troubleshooting guide included

---

### End of Day 5 Checklist
- [ ] Conversation database implemented
- [ ] Polling endpoint working
- [ ] Frontend uses polling
- [ ] Page refresh preserves conversation
- [ ] Documentation complete
- [ ] All tests pass
- [ ] Commit + push
- [ ] Create PR for review

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test each component independently
pytest tests/test_evidence.py
pytest tests/test_timing.py
pytest tests/test_conversation_db.py
```

### Integration Tests
```bash
# Test full pipeline
pytest tests/integration/test_search_provenance.py
pytest tests/integration/test_otel_traces.py
pytest tests/integration/test_conversation_polling.py
```

### Manual Testing Checklist

**Provenance:**
- [ ] Web search query shows `origin_tool="web_search"`
- [ ] RAG query shows `origin_tool="rag"`
- [ ] Mixed query shows both types
- [ ] Footer shows correct counts

**Waterfall:**
- [ ] All enabled stages show timing
- [ ] KG timing > 0ms when enabled
- [ ] Total ≈ sum of stages

**OTEL:**
- [ ] Traces visible in collector logs
- [ ] Prometheus scrapes OTEL metrics
- [ ] Grafana shows traces
- [ ] Trace IDs in response headers

**OpenLLMetry:**
- [ ] LLM spans have token counts
- [ ] Model name in span
- [ ] Cost estimate present
- [ ] Prompt hash for deduplication

**Conversations:**
- [ ] Create conversation works
- [ ] Messages persist across refresh
- [ ] Polling retrieves new messages
- [ ] No duplicate messages

### Performance Tests
```bash
# Load test with 100 concurrent requests
locust -f tests/load/locustfile.py --host http://localhost:8000
```

**Acceptance Criteria:**
- p95 latency < 5s for simple queries
- p99 latency < 10s for complex queries
- Zero errors under load
- OTEL overhead < 5% latency increase

---

## 📦 Pull Request Strategy

### PR #1: Provenance Fix (Day 1)
**Title:** `Fix provenance tracking - make origin_tool immutable`

**Description:**
- Introduces immutable Evidence class
- Updates search service to use Evidence
- Adds provenance validator
- Frontend displays source breakdown

**Files Changed:** ~8 files
**Tests:** 5 new tests
**Risk:** LOW - Isolated change

### PR #2: Waterfall & UX (Day 2)
**Title:** `Complete waterfall timing + UX polish`

**Description:**
- Adds timing instrumentation to all services
- KG timing now visible
- Copy buttons for markdown
- KG reset invalidates caches

**Files Changed:** ~10 files
**Tests:** 3 new tests
**Risk:** LOW - UI improvements

### PR #3: OTEL Foundation (Day 3)
**Title:** `Add OpenTelemetry distributed tracing`

**Description:**
- Deploys OTel Collector
- Instruments API Gateway and Search
- Prometheus integration
- Basic trace collection

**Files Changed:** ~12 files (config, docker-compose, 2 services)
**Tests:** 2 new tests
**Risk:** MEDIUM - New infrastructure

### PR #4: OpenLLMetry (Day 4)
**Title:** `Add LLM observability with OpenLLMetry`

**Description:**
- LLM spans with token counts
- Cost estimation
- Model performance tracking
- Grafana dashboard

**Files Changed:** ~6 files
**Tests:** 3 new tests
**Risk:** LOW - Additive only

### PR #5: Conversation Persistence (Day 5)
**Title:** `Add conversation persistence with polling`

**Description:**
- SQLite database for conversations
- Polling endpoint
- Frontend polling hook
- Survives page refresh

**Files Changed:** ~8 files
**Tests:** 4 new tests
**Risk:** MEDIUM - Changes chat flow

---

## 🚀 Deployment Process

### Pre-Deployment Checklist
- [ ] All PRs reviewed and approved
- [ ] All tests passing (unit + integration)
- [ ] Load tests completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped (1.3.0 → 1.4.0)

### Deployment Steps

#### 1. Merge to Main
```bash
git checkout main
git pull origin main
git merge otel --no-ff
git push origin main
```

#### 2. Tag Release
```bash
git tag -a v1.4.0 -m "OpenTelemetry integration + bug fixes"
git push origin v1.4.0
```

#### 3. Deploy to Development
```bash
# Stop existing containers
docker compose down

# Pull latest code
git pull origin main

# Rebuild images
docker compose build --no-cache

# Start services
docker compose up -d

# Verify health
docker compose ps
./scripts/health-check.sh
```

#### 4. Smoke Tests
```bash
# Test provenance
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"Latest AI news", "enable_web_search":true}'

# Test traces
curl http://localhost:8889/metrics | grep trace

# Test conversation persistence
# Refresh page during query → should resume
```

#### 5. Deploy to Production
```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d

# Monitor logs
docker compose -f docker-compose.prod.yml logs -f
```

### Rollback Plan

If deployment fails:

```bash
# Quick rollback
git revert HEAD
docker compose down
docker compose up -d

# Or checkout previous version
git checkout v1.3.0
docker compose build
docker compose up -d
```

**Rollback Triggers:**
- Any service fails health check
- >10% increase in p99 latency
- Errors in OTEL collector
- Frontend errors in console

---

## 📊 Success Metrics

### Week 1 Targets

**Correctness:**
- ✅ 100% provenance accuracy (all web sources tagged)
- ✅ 0% conversation loss on refresh
- ✅ 100% waterfall completeness (all stages timed)

**Observability:**
- ✅ >90% trace coverage (requests with traces)
- ✅ 100% LLM calls have token counts
- ✅ Grafana → trace exemplar links work

**Performance:**
- ✅ OTEL overhead < 5% latency increase
- ✅ Polling overhead < 10 req/sec per user
- ✅ p95 latency < 5s

**Quality:**
- ✅ 100% test pass rate
- ✅ 0 linter errors
- ✅ 0 console errors in frontend

---

## 📚 Additional Documentation

### Files to Read
- `docs/deployment/OTEL_IMPLEMENTATION_GUIDE.md` - OTEL setup
- `docs/deployment/CONVERSATION_PERSISTENCE.md` - Persistence design
- `docs/architecture/OBSERVABILITY.md` - Observability architecture
- `docs/testing/INTEGRATION_TESTS.md` - Test strategy

### External Resources
- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenLLMetry Guide](https://www.traceloop.com/docs/openllmetry/getting-started-python)
- [Prometheus Exemplars](https://prometheus.io/docs/prometheus/latest/feature_flags/#exemplars-storage)

---

## 🎯 Week 2 Preview

If Week 1 completes successfully, Week 2 focuses on:

1. **Contract Sentinel** (2 days)
   - Emit artifacts A-G
   - Schema validation
   - Stubs for missing data

2. **A/B Grader** (1 day)
   - 7-dimension scoring
   - Comparison UI
   - Statistical significance

3. **Query Decomposition** (2 days)
   - Planner emits sub-queries
   - Self-RAG refinement
   - Evidence aggregation

4. **Documents Pagination** (1 day)
   - Server-side pagination
   - Title truncation
   - Performance optimization

---

**Status:** 🟢 READY TO EXECUTE
**Confidence:** HIGH (realistic scope, clear tasks)
**Risk Level:** MEDIUM (new infrastructure, but isolated changes)

---

**Last Updated:** 2025-11-08
**Document Owner:** RAG Lab Development Team
**Reviewers:** [Pending]

