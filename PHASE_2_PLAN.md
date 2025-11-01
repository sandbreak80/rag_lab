# 🚀 PHASE 2: AI EDUCATION & ADVANCED FEATURES

**Date:** November 1, 2025
**Status:** Planning
**Scope:** Major expansion of Educational RAG Lab

---

## 📋 User Requirements Analysis

### 1. AI Fundamentals Education
**Goal:** Teach core AI/RAG concepts within the lab

**Topics to Cover:**
- What is RAG (Retrieval Augmented Generation)?
- What is an LLM (Large Language Model)?
- Re-ranking and its purpose
- Temperature (creativity vs determinism)
- Context Window (input size limits)
- Tokens (text units)
- Precision (accuracy of positive predictions)
- Recall (coverage of relevant documents)
- Accuracy (is this a RAG metric? - need to clarify)
- Top-K (result count)
- Knowledge Graph (relationship networks)
- Query Expansion (synonym/related terms)
- BM25 (keyword search algorithm)
- Web Search (external data retrieval)

### 2. Metrics Dashboard Enhancement
**Goal:** Track ALL metrics across entire lab session with persistence

**Metrics to Track:**
- Prompt tokens (input size)
- Prompt processing time (ms)
- Inference time (LLM generation time)
- Web search time (external query latency)
- Overall time (end-to-end)
- Component breakdown (existing + new)
- Model performance comparisons
- Per-query stats
- Aggregate stats across session

**Storage:** LocalStorage or backend persistence

### 3. Model Management
**Goal:** Dynamic model discovery and comparison

**Requirements:**
- Query Ollama API for available models
- Populate model selector dynamically
- Show model metadata:
  - Size (parameters: 1B, 3B, 7B, etc.)
  - Context window (varies by model)
  - Best use cases
  - Performance characteristics

**Key Message:** "We're not the most powerful model, but our pipeline adds huge value"

### 4. Model Comparison Exercise
**Goal:** Comprehensive model performance analysis

**Comparison Dimensions:**
- Model size (1B vs 3B vs 7B vs 13B)
- Parameter count
- Context window size
- Instruction following ability
- Response quality
- Latency
- Token usage
- Best use cases per model
- Strengths and weaknesses

**Output:** "Huge takeaway from the lab"

### 5. UI Restructure - Multi-Tab Application
**Goal:** Scale beyond single page to organized tabs

**New Tab Structure:**
```
┌─────────────────────────────────────────────────────┐
│  [Chat] [Settings] [Lab Guide] [Metrics] [Upload]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│            Active Tab Content Here                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tabs:**
1. **Chat** - Main RAG Q&A interface (current main view)
2. **Settings** - Configuration panel (currently sidebar)
3. **Lab Guide** - Educational content (currently sidebar)
4. **Metrics** - Comprehensive metrics dashboard (NEW!)
5. **Upload** - Document upload interface (currently embedded)

**State Management:** Preserve state when switching tabs

### 6. Web Search Configuration
**Goal:** Adjustable SearXNG parameters for exercises

**Configurable Settings:**
- Number of results
- Search engines to use
- Categories (general, news, science, etc.)
- Time range (recent, all)
- Pages per document
- Language
- Safe search

### 7. Thinking Model Integration
**Goal:** Explore if we have overhead for additional reasoning model

**Questions:**
- Do we have compute overhead?
- What's a "thinking model"? (Chain-of-thought reasoning?)
- Should we add a reasoning step before retrieval?
- Should we add query refinement via smaller model?

### 8. Additional Ollama Models to Explore
**Goal:** Expand beyond llama3.2

**Potential Models:**
- **Code Models**: codellama, deepseek-coder
- **Instruction Models**: mistral, mixtral
- **Small Models**: tinyllama, phi-2
- **Large Models**: llama3:70b (if resources allow)
- **Specialized**: solar, openchat

---

## 🏗️ Architecture Changes Required

### A. Backend Changes

#### 1. New Metrics Service (Optional)
```
services/metrics/
├── app/
│   └── service.py
├── Dockerfile
└── requirements.txt
```

**OR** integrate into existing services

#### 2. Enhanced Endpoints

**Search Service (`/search_with_config`):**
- Add prompt_tokens count
- Add prompt_processing_time
- Add inference_time breakdown
- Add web_search_time detail

**Web Search Service:**
- Add configurable parameters
- Return page count per document
- Return engine breakdown

**New Ollama Wrapper Endpoint:**
- GET `/models` - List available models with metadata
- GET `/models/{name}` - Get model details

#### 3. Metrics Persistence

**Option A: LocalStorage (Client-side)**
```javascript
sessionMetrics = {
  queries: [
    {
      timestamp: "...",
      query: "...",
      model: "llama3.2:3b",
      config: {...},
      metrics: {...}
    }
  ],
  aggregates: {
    total_queries: 10,
    avg_latency: 150,
    total_tokens: 5000,
    ...
  }
}
```

**Option B: Backend Database**
- SQLite or JSON file
- Store per-session or per-user
- Export functionality

### B. Frontend Changes

#### 1. Tab Navigation System
```html
<div class="tab-bar">
  <button class="tab active" data-tab="chat">Chat</button>
  <button class="tab" data-tab="settings">Settings</button>
  <button class="tab" data-tab="lab">Lab Guide</button>
  <button class="tab" data-tab="metrics">Metrics</button>
  <button class="tab" data-tab="upload">Upload</button>
</div>

<div class="tab-content">
  <div id="chat-tab" class="tab-pane active">...</div>
  <div id="settings-tab" class="tab-pane">...</div>
  <div id="lab-tab" class="tab-pane">...</div>
  <div id="metrics-tab" class="tab-pane">...</div>
  <div id="upload-tab" class="tab-pane">...</div>
</div>
```

#### 2. Metrics Tab - Comprehensive Dashboard
```
┌─────────────────────────────────────────────────┐
│  Session Overview                               │
│  - Total Queries: 15                           │
│  - Total Tokens: 12,450                        │
│  - Avg Latency: 185ms                          │
│  - Active Model: llama3.2:3b                   │
├─────────────────────────────────────────────────┤
│  Per-Query History (Table)                     │
│  | Query | Model | Latency | Tokens | Config | │
│  |-------|-------|---------|--------|--------|  │
│  | ...   | ...   | ...     | ...    | ...    |  │
├─────────────────────────────────────────────────┤
│  Visualizations                                 │
│  - Latency over time (chart)                   │
│  - Token usage (bar chart)                     │
│  - Component breakdown (pie chart)             │
├─────────────────────────────────────────────────┤
│  Export Data                                    │
│  [Download CSV] [Download JSON] [Clear Data]   │
└─────────────────────────────────────────────────┘
```

#### 3. Settings Tab Enhancements
```
┌─────────────────────────────────────────────────┐
│  Model Selection                                │
│  ┌────────────────────────────────────────────┐ │
│  │ Model: [Dynamic Dropdown from Ollama API]  │ │
│  │                                             │ │
│  │ Selected: llama3.2:3b                      │ │
│  │ Size: 3B parameters                        │ │
│  │ Context: 2048 tokens                       │ │
│  │ Best for: General purpose                  │ │
│  └────────────────────────────────────────────┘ │
│                                                 │
│  Web Search Configuration                       │
│  - Results: [5-50 slider]                      │
│  - Engines: [☑ Google ☑ DDG ☐ Bing]          │
│  - Categories: [general, news, science]        │
└─────────────────────────────────────────────────┘
```

#### 4. Educational Content Pages

**New: AI Fundamentals Tab (or section in Lab Guide)**
```
docs/lab/AI_FUNDAMENTALS.md

Sections:
1. What is RAG?
2. Large Language Models (LLMs)
3. Embeddings & Vector Search
4. Keyword Search (BM25)
5. Hybrid Search & Fusion
6. Re-ranking Strategies
7. Knowledge Graphs
8. Query Expansion
9. Web Search Integration
10. Model Parameters (temperature, top-k, context window)
11. Evaluation Metrics (precision, recall, F1)
12. Tokens & Token Economics
```

---

## 📚 Documentation Updates Required

### 1. New Documents to Create

**docs/lab/AI_FUNDAMENTALS.md** (NEW!)
- Complete glossary of AI/RAG terms
- Visual diagrams
- Simple explanations
- Code examples
- Interactive exercises

**docs/lab/MODEL_COMPARISON_EXERCISE.md** (NEW!)
- Exercise 11: Compare 3+ models
- Fill-in-the-blank comparison table
- Performance analysis questions
- Best use case recommendations

**docs/lab/METRICS_GUIDE.md** (NEW!)
- How to read the metrics dashboard
- What each metric means
- How to export and analyze data
- Tips for optimization

### 2. Documents to Update

**docs/lab/LAB_GUIDE.md**
- Add references to AI Fundamentals
- Add section on metrics tracking
- Add model comparison section
- Update with new tab navigation

**docs/lab/STUDENT_EXERCISES.md**
- Add Exercise 11: Model Comparison
- Add Exercise 12: Web Search Configuration
- Add Exercise 13: Metrics Analysis
- Update existing exercises with AI fundamentals references

**docs/COMPREHENSIVE_DOCUMENTATION.md**
- Document new metrics endpoints
- Document model API
- Document tab navigation
- Document metrics persistence

**README.md**
- Update feature list
- Add AI education highlight
- Mention model comparison
- Update architecture diagram

---

## 🎯 Implementation Plan

### Phase 2A: AI Fundamentals Documentation (2-3 hours)
**Priority:** HIGH - Foundation for everything else

1. Create `docs/lab/AI_FUNDAMENTALS.md`
   - Write all 12 sections
   - Include diagrams
   - Add interactive elements
   - Reference from other docs

2. Create `docs/lab/MODEL_COMPARISON_EXERCISE.md`
   - Design comparison table
   - Create evaluation criteria
   - Write questions

3. Create `docs/lab/METRICS_GUIDE.md`
   - Explain each metric
   - Show examples
   - Export instructions

4. Update existing lab docs with cross-references

### Phase 2B: Ollama Model API Integration (1-2 hours)
**Priority:** HIGH - Required for dynamic model selection

1. Create endpoint: GET `/api/ollama/models`
   - Query Ollama: `GET http://ollama:11434/api/tags`
   - Parse model list
   - Enrich with metadata (size, context, use case)
   - Return structured JSON

2. Create endpoint: GET `/api/ollama/models/{name}`
   - Query Ollama: `POST http://ollama:11434/api/show`
   - Return detailed model info

3. Update `src/webapp.py` with new endpoints

### Phase 2C: Enhanced Metrics Collection (2-3 hours)
**Priority:** HIGH - Core requirement

1. Update Search Service
   - Add token counting (prompt tokens)
   - Add timing breakdowns (prompt processing, inference)
   - Return in `/search_with_config` response

2. Update Web Search Service
   - Add detailed timing
   - Add page count per doc
   - Add engine breakdown

3. Client-side metrics aggregation
   - Store all queries in localStorage
   - Calculate aggregates
   - Persist across sessions

### Phase 2D: Multi-Tab UI Restructure (3-4 hours)
**Priority:** MEDIUM - Major UX change

1. Create tab navigation system
   - HTML structure
   - CSS styling (tabs, tab-bar, tab-content)
   - JavaScript tab switching
   - State preservation

2. Reorganize existing content into tabs
   - Chat tab (current main view)
   - Settings tab (current sidebar)
   - Lab Guide tab (current sidebar)
   - Upload tab (current embedded)

3. Create new Metrics tab
   - Session overview
   - Query history table
   - Visualizations (charts)
   - Export functionality

4. Update all navigation (remove sidebar toggles)

### Phase 2E: Metrics Dashboard (3-4 hours)
**Priority:** HIGH - Key feature

1. Design Metrics tab layout
   - Session overview cards
   - Query history table
   - Charts (latency, tokens, components)

2. Implement metrics tracking
   - Track every query
   - Store to localStorage
   - Calculate aggregates

3. Implement visualizations
   - Chart.js or similar library
   - Latency over time
   - Token usage
   - Component breakdown

4. Implement export
   - CSV export
   - JSON export
   - Clear data button

### Phase 2F: Web Search Configuration (1-2 hours)
**Priority:** MEDIUM

1. Update Settings tab
   - Add Web Search section
   - Result count slider
   - Engine checkboxes
   - Category dropdown

2. Update Web Search Service
   - Accept configuration parameters
   - Pass to SearXNG
   - Return detailed results

3. Update UI to pass web search config

### Phase 2G: Model Comparison Exercise (2-3 hours)
**Priority:** MEDIUM

1. Create comparison interface (optional)
   - Select 2-3 models
   - Run same query on all
   - Display side-by-side results
   - Show performance metrics

2. Update exercises with comparison activity

### Phase 2H: Testing & Documentation (2-3 hours)
**Priority:** HIGH

1. Test all new features
2. Update integration tests
3. Update documentation
4. Create screenshots
5. Update README

### Phase 2I: Infrastructure Monitoring Dashboards (3-5 hours)
**Priority:** MEDIUM (Future State - Roadmap)
**Integration:** Splunk Observability Cloud + Splunk AI/LLM Monitoring

**Note:** This is a future enhancement, documented for roadmap

**Splunk Integration Strategy:**

Future state will use **Splunk Observability Cloud** and **Splunk AI/LLM Observability** to monitor the entire RAG stack:

References:
- [LLM Observability Explained: Prevent Hallucinations, Manage Drift, Control Costs](https://www.splunk.com/en_us/blog/learn/llm-observability.html)
- [How We Built End-to-End LLM Observability with Splunk and RAG](https://www.splunk.com/en_us/blog/artificial-intelligence/how-we-built-end-to-end-llm-observability-with-splunk-and-rag.html)

**Key Splunk LLM Observability Signals:**

1. **Trust (Groundedness)**
   - Groundedness Score: Alignment with trusted documents
   - Factuality Check Rate: Frequency of verification
   - Moderation Flags: Response quality checks
   - **Our RAG Pipeline**: Source attribution, document citations

2. **Cost (Cost-per-Answer)**
   - Cost-per-Answer: Average cost per response
   - Token Utilization Rate: Input/output token analysis
   - Budget Adherence: Spending vs. budget
   - **Our Tracking**: Prompt tokens, completion tokens, inference time

3. **User Experience (p95 Latency)**
   - p95 Latency: 95th percentile response times
   - Error Rate: Failures and timeouts
   - User Feedback Scores: Satisfaction ratings
   - **Our Metrics**: Component-level latency breakdown

**Splunk Monitoring for RAG Pipeline:**

```
User Query → Prompt Processing → Document Retrieval →
Context Assembly → Generation → Quality Validation
     ↓              ↓                ↓                ↓
 [Splunk APM] [Splunk Logs] [Splunk Metrics] [Splunk AI Observability]
```

**What Splunk Tracks:**

**Phase 1: Pre-Processing**
- Prompt engineering effectiveness
- Query expansion quality
- Input validation

**Phase 2: Retrieval (RAG-specific)**
- Vector search latency
- BM25 search performance
- Hybrid fusion effectiveness
- Retrieved document relevance
- Top-K result quality

**Phase 3: Context Assembly**
- Chunk selection quality
- Context window utilization
- Token budget management

**Phase 4: Generation**
- LLM inference time
- Token generation rate (tokens/s)
- Model performance by size (1B vs 3B vs 8B)
- GPU utilization

**Phase 5: Post-Processing**
- Re-ranking latency
- Knowledge graph enhancement
- Final response assembly

**Phase 6: Quality Validation**
- Hallucination detection
- Groundedness scoring
- Source verification
- Moderation checks

**Splunk Integration Points:**

```python
# OpenTelemetry instrumentation for Splunk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure Splunk endpoint
tracer_provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(
    endpoint="https://ingest.us0.signalfx.com",
    headers={"X-SF-TOKEN": "YOUR_SPLUNK_TOKEN"}
)
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)

# Instrument RAG pipeline
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("rag_query") as span:
    span.set_attribute("query", query_text)
    span.set_attribute("user_id", user_id)

    with tracer.start_as_current_span("retrieval"):
        # Vector + BM25 search
        span.set_attribute("retrieval.method", "hybrid")
        span.set_attribute("retrieval.top_k", top_k)
        results = search(query)
        span.set_attribute("retrieval.results_count", len(results))

    with tracer.start_as_current_span("generation"):
        span.set_attribute("llm.model", "llama3.2:3b")
        span.set_attribute("llm.temperature", 0.5)
        response = llm.generate(context)
        span.set_attribute("llm.prompt_tokens", prompt_tokens)
        span.set_attribute("llm.completion_tokens", completion_tokens)
        span.set_attribute("llm.total_tokens", total_tokens)

    with tracer.start_as_current_span("quality_check"):
        groundedness_score = check_groundedness(response, results)
        span.set_attribute("quality.groundedness", groundedness_score)
```

**Splunk Dashboards for RAG:**

1. **LLM Performance Dashboard**
   - Query volume over time
   - p50, p95, p99 latency
   - Error rates
   - Cost per query
   - Token usage trends

2. **RAG Pipeline Health**
   - Retrieval accuracy (precision/recall)
   - Hybrid search effectiveness
   - Re-ranking impact
   - Knowledge graph coverage
   - BM25 index freshness

3. **Model Comparison**
   - 1B vs 3B vs 8B performance
   - Quality vs latency trade-offs
   - Cost per model
   - GPU utilization by model

4. **Groundedness & Trust**
   - Hallucination rate
   - Source citation accuracy
   - Moderation flags
   - User feedback correlation

5. **Cost Optimization**
   - Token usage by component
   - Most expensive queries
   - Optimization opportunities
   - Budget tracking

**Enterprise Value Proposition:**

*"Monitor your entire RAG pipeline with Splunk - from query to answer. Track groundedness, control costs, and ensure every response is trustworthy. See exactly where latency occurs and optimize each component independently."*

**Splunk Integration Benefits:**

✅ **End-to-end visibility**: Query → Retrieval → Generation → Response
✅ **RAG-specific metrics**: Retrieval quality, groundedness, source accuracy
✅ **Cost tracking**: Token usage, model costs, infrastructure spend
✅ **Performance optimization**: Identify bottlenecks in hybrid search, reranking
✅ **Compliance**: Audit trails, data lineage, response provenance
✅ **Alerting**: Anomaly detection, hallucination spikes, cost overruns

**Demo Value:**

This lab becomes a **live demonstration** of:
- How to build production RAG systems
- How to instrument RAG with Splunk
- What to monitor in RAG pipelines
- How Splunk provides LLM observability

**Field Team Messaging:**

*"This isn't just a RAG lab - it's a reference architecture for production LLM deployments. Every component is instrumented for Splunk, showing customers exactly what to monitor when they deploy AI at scale."*

**Implementation Priority:**

- **Phase 2I (Infrastructure Monitoring)**: Build basic metrics collection
- **Phase 2I+ (Splunk Integration)**: Add OpenTelemetry + Splunk exporters
- **Production**: Full Splunk Observability Cloud integration

This positions the lab as a **Splunk AI Observability showcase**!

1. **System Monitoring Service**
   - Create `services/system-monitor/`
   - Collect system metrics (CPU, RAM, disk, network)
   - Endpoints: `/api/system/stats`, `/api/system/history`
   - Use `psutil` library (cross-platform)
   - 10-minute rolling window

2. **Docker Stats Service**
   - Create `services/docker-monitor/`
   - Execute `docker stats --no-stream` periodically
   - Parse output to JSON
   - Endpoints: `/api/docker/stats`, `/api/docker/history`
   - Per-container breakdown

3. **GPU Monitoring Service**
   - Create `services/gpu-monitor/`
   - **NVIDIA Path** (AWS Lab):
     - Execute `nvidia-smi --query-gpu=...`
     - Parse XML/CSV output
     - Track utilization, memory, temp, power
   - **Mac M2 Path** (Leave-behind):
     - Use `ioreg` or Metal API
     - Track GPU/Neural Engine activity
     - Platform detection (Darwin = Mac)
   - Endpoints: `/api/gpu/stats`, `/api/gpu/history`

4. **Infrastructure Dashboard Tab**
   - New tab: "System" or "Infrastructure"
   - Three panels:
     1. System Performance (CPU, RAM charts)
     2. Docker Stats (per-container table + charts)
     3. GPU Monitoring (utilization, memory)
   - Live updates (WebSocket or polling)
   - 10-minute time window with scrubbing
   - Export data functionality

5. **Tokens/s Tracking**
   - Add to Ollama calls
   - Track generation speed
   - Display in metrics
   - Compare across hardware (AWS vs Mac M2)

6. **Hardware Comparison Feature**
   - Save metrics tagged with hardware
   - "Lab Machine (AWS GPU)" vs "Local Machine (Mac M2)"
   - Side-by-side comparison
   - Show: tokens/s, latency, resource usage

**Libraries Required:**
- `psutil` - Cross-platform system metrics
- `nvidia-ml-py3` - NVIDIA GPU monitoring (optional)
- `subprocess` - Execute docker stats
- Chart.js or similar - Visualization

**Platform Detection:**
```python
import platform
if platform.system() == "Darwin":
    # Mac M2 - use Metal/ioreg
    monitor = MacGPUMonitor()
elif shutil.which("nvidia-smi"):
    # NVIDIA GPU available
    monitor = NvidiaGPUMonitor()
else:
    # No GPU monitoring
    monitor = NoGPUMonitor()
```

**WebSocket for Live Updates:**
- Real-time streaming of metrics
- No page refresh needed
- Smooth chart updates

---

### 9. Infrastructure Monitoring Dashboards (Future State)
**Goal:** Show students how hard the system is working to run RAG

**Three System Dashboards:**

1. **System Performance Dashboard** (like `top`)
   - CPU usage per core (live graphs)
   - Memory usage (RAM)
   - Disk I/O
   - Network I/O
   - System load average
   - Process-level stats
   - **Time Window:** Past 10 minutes, dynamic/live
   - **Update Frequency:** 1-2 second refresh

2. **Docker Stats Dashboard**
   - Per-container metrics:
     - CPU %
     - Memory usage / limit
     - Network I/O
     - Block I/O
     - PIDs count
   - All 10 microservices visible
   - Visual graphs (line charts for trends)
   - **Command:** `docker stats --no-stream` (repeated)
   - **Time Window:** Past 10 minutes

3. **GPU Monitoring Dashboard**
   - GPU utilization %
   - GPU memory usage
   - GPU temperature
   - Power draw
   - Processes using GPU (embedding, inference)
   - **Tools:** `nvidia-smi` (NVIDIA) or Metal Performance HUD (Mac M2)
   - **Platforms:**
     - AWS Lab: NVIDIA GPU (`nvidia-smi`)
     - Leave-behind: Mac M2/M3 (Metal API)
   - **Time Window:** Past 10 minutes

**Key Value Proposition:**
"See exactly how hard your system is working to deliver RAG responses"

**Comparison Feature:**
- Show tokens/s on AWS GPU vs Mac M2
- Compare resource usage
- Demonstrate: "This is what you need to run RAG at scale"
- Students understand hardware requirements

**Platform Support:**
- ✅ **AWS Lab Machines**: NVIDIA GPU instances
- ✅ **Leave-behind Lab**: Mac M2/M3/M4 (no GPU, but Metal acceleration)
- ❌ **Windows**: Not supported (per user requirement)

### 10. Tokens per Second Tracking
**Goal:** Show inference speed across different hardware

**Metrics to Add:**
- Tokens per second (tokens/s) during generation
- Total tokens generated
- Prompt processing speed
- Hardware comparison (AWS GPU vs Mac M2)

---

## 🤔 Open Questions & Decisions

### Q1: Accuracy as a RAG Metric?
**Answer:** Accuracy is typically for classification tasks. For RAG, we use:
- **Precision**: Of retrieved docs, how many are relevant?
- **Recall**: Of all relevant docs, how many did we retrieve?
- **F1 Score**: Harmonic mean of precision and recall
- **MRR (Mean Reciprocal Rank)**: Position of first relevant result
- **NDCG**: Ranking quality metric

**Decision:** Clarify in AI Fundamentals that "accuracy" isn't standard for RAG; use precision/recall/F1.

### Q2: Thinking Model Overhead?
**Question:** Do we have compute overhead for additional model?

**Analysis:**
- Current: 1 LLM call per query (for answer generation)
- Embeddings: Separate model (nomic-embed-text)
- Thinking model would add: Chain-of-thought reasoning before retrieval

**Options:**
1. **Query Refinement**: Small model (1B) refines query before search
2. **Chain-of-Thought**: Small model generates reasoning steps
3. **Dual LLM**: One for search, one for answer (expensive)

**Recommendation:** Add optional "Query Refinement" step using small model (tinyllama or phi-2) to demonstrate value of pipeline over single large model.

### Q3: Which Additional Models?
**Recommendation:**
- **Keep Current**: llama3.2:1b, 3b, 8b
- **Add for Comparison**:
  - `mistral:7b` - Strong instruction following
  - `phi-2:2.7b` - Microsoft's small model
  - `tinyllama:1.1b` - Smallest viable model
  - `codellama:7b` - Code-focused (if relevant)

**Rationale:** Show variety of sizes and specializations

### Q4: Tab State Management?
**Decision:** Use JavaScript state object:
```javascript
appState = {
  currentTab: 'chat',
  chatHistory: [...],
  settingsConfig: {...},
  metricsData: {...},
  labProgress: {...}
}
```
Persist to localStorage on tab switch.

### Q5: Backend vs Client-side Metrics?
**Recommendation:** **Client-side (localStorage)** for Phase 2
- Simpler implementation
- No database needed
- Per-browser session
- Easy export

**Future:** Add backend persistence for multi-user deployments

---

## 📊 Estimated Effort

| Phase | Hours | Priority | Status |
|-------|-------|----------|--------|
| 2A: AI Fundamentals Docs | 2-3 | HIGH | Phase 2 |
| 2B: Ollama Model API | 1-2 | HIGH | Phase 2 |
| 2C: Enhanced Metrics | 2-3 | HIGH | Phase 2 |
| 2D: Multi-Tab UI | 3-4 | MEDIUM | Phase 2 |
| 2E: Metrics Dashboard | 3-4 | HIGH | Phase 2 |
| 2F: Web Search Config | 1-2 | MEDIUM | Phase 2 |
| 2G: Model Comparison | 2-3 | MEDIUM | Phase 2 |
| 2H: Testing & Docs | 2-3 | HIGH | Phase 2 |
| **Phase 2 Subtotal** | **17-24 hrs** | | |
| | | | |
| 2I: Infrastructure Monitoring | 3-5 | MEDIUM | **Future/Roadmap** |
| **TOTAL (with monitoring)** | **20-29 hours** | | |

---

## 🎯 Deliverables

### Documentation
- ✅ This planning document (PHASE_2_PLAN.md)
- ⏳ docs/lab/AI_FUNDAMENTALS.md (12 sections)
- ⏳ docs/lab/MODEL_COMPARISON_EXERCISE.md
- ⏳ docs/lab/METRICS_GUIDE.md
- ⏳ Updated existing lab docs

### Code (Phase 2)
- ⏳ Multi-tab UI (HTML/CSS/JS)
- ⏳ Metrics dashboard tab
- ⏳ Enhanced metrics collection
- ⏳ Ollama model API wrapper
- ⏳ Web search configuration
- ⏳ Model comparison interface (optional)

### Code (Future/Roadmap - Phase 2I)
- ⏳ System monitoring service (CPU, RAM, disk, network)
- ⏳ Docker stats monitoring service
- ⏳ GPU monitoring service (NVIDIA + Mac M2 Metal)
- ⏳ Infrastructure dashboard tab with live charts
- ⏳ Tokens/s tracking and comparison
- ⏳ Hardware comparison feature (AWS vs Mac M2)

### Features (Phase 2)
- ⏳ Dynamic model selector (from Ollama API)
- ⏳ Comprehensive metrics tracking
- ⏳ Session-wide metrics aggregation
- ⏳ Metrics export (CSV/JSON)
- ⏳ Web search customization
- ⏳ Model comparison exercise

### Features (Future/Roadmap - Phase 2I)
- ⏳ Live system performance monitoring (CPU, RAM, disk, network)
- ⏳ Per-container Docker stats with charts
- ⏳ GPU utilization tracking (NVIDIA + Mac M2)
- ⏳ Tokens per second measurement
- ⏳ Hardware comparison (AWS GPU vs Mac M2)
- ⏳ Infrastructure dashboard tab with 10-min rolling window
- ⏳ Real-time updates via WebSocket

---

## 🚀 Success Criteria

1. **Educational Value**
   - Students understand all AI/RAG fundamentals
   - Clear explanations with examples
   - Interactive exercises reinforce learning

2. **Metrics Transparency**
   - All performance metrics visible
   - Historical tracking across session
   - Easy export for analysis

3. **Model Understanding**
   - Students can compare models effectively
   - Understand size vs performance trade-offs
   - See "pipeline value > model power"

4. **Professional UI**
   - Clean tab navigation
   - No loss of state
   - Intuitive organization

5. **Scalability**
   - Code supports future enhancements
   - Well-documented
   - Maintainable

---

## 🗺️ Roadmap Summary

### **Phase 2: Core Education & Advanced Features** (17-24 hours)
**Timeline:** Immediate implementation
- AI Fundamentals documentation
- Enhanced metrics tracking
- Multi-tab UI restructure
- Comprehensive metrics dashboard
- Dynamic model management
- Model comparison exercises
- Web search configuration

### **Phase 2I: Infrastructure Monitoring** (3-5 hours)
**Timeline:** Future enhancement (documented for roadmap)
**Status:** Deferred until Phase 2 complete

**Why Separate?**
- Phase 2 provides immediate educational value
- Infrastructure monitoring is observability/advanced feature
- Allows Phase 2 to be completed and tested first
- Can be added as v1.1 or v1.2 release

**Infrastructure Monitoring Includes:**
1. System Performance Dashboard (CPU, RAM, disk, network)
2. Docker Stats Dashboard (per-container resource usage)
3. GPU Monitoring Dashboard (NVIDIA + Mac M2 Metal)
4. Tokens/s tracking across hardware
5. Hardware comparison (AWS GPU vs Mac M2)
6. Live charts with 10-minute rolling window

**Platform Support Matrix:**

| Platform | GPU Support | Monitoring Method | Status |
|----------|-------------|-------------------|--------|
| **AWS Lab (NVIDIA)** | ✅ NVIDIA GPU | `nvidia-smi` | Primary target |
| **Mac M2/M3 Leave-behind** | ✅ Metal/Neural Engine | `ioreg` / Metal API | Primary target |
| **Mac Intel** | ❌ No GPU | CPU only | Supported |
| **Linux (NVIDIA)** | ✅ NVIDIA GPU | `nvidia-smi` | Supported |
| **Windows** | ❌ Not supported | - | Not supported per user |

---

## 📋 Next Steps

### Immediate (Phase 2):
1. ✅ **Plan approved** (this document)
2. ⏳ **Start with Phase 2A** (AI Fundamentals Docs)
3. ⏳ **Then Phase 2B & 2C** (Backend enhancements)
4. ⏳ **Then Phase 2D & 2E** (UI restructure + metrics)
5. ⏳ **Finally 2F, 2G, 2H** (Additional features + testing)

### Future (Phase 2I - Roadmap):
6. 📋 **Infrastructure Monitoring** (after Phase 2 complete)
   - System monitoring service
   - Docker stats service
   - GPU monitoring service (NVIDIA + Mac M2)
   - Infrastructure dashboard tab
   - Hardware comparison feature

---

**Status:** ⏳ AWAITING APPROVAL TO PROCEED WITH PHASE 2

**Questions for User:**
1. ✅ **Infrastructure monitoring added to roadmap** - Agree to defer to Phase 2I?
2. Does Phase 2 plan address all immediate requirements?
3. Any priorities to adjust?
4. Should we do Phase 2 in phases or all at once?
5. Any specific models you want to focus on?
6. **Approve to start with Phase 2A (AI Fundamentals documentation)?**

---

## 🎯 Key Decisions Made

1. **Infrastructure monitoring = Future state** (Phase 2I, documented in roadmap)
2. **Platform support:** AWS NVIDIA + Mac M2 (no Windows)
3. **Tokens/s tracking:** Added to metrics system
4. **Hardware comparison:** Show AWS GPU vs Mac M2 performance
5. **Live monitoring:** 10-minute rolling window with dynamic graphs
6. **Multi-tab UI:** Will include future "Infrastructure" tab slot

This ensures Phase 2 delivers immediate educational value while documenting the infrastructure monitoring vision for future implementation.


---

### Phase 4: Splunk AI Platform Integration (Long-term Vision)
**Timeline:** Post-Phase 3 Lab Framework
**Status:** Strategic roadmap

**Integration with Splunk AI Ecosystem:**

References:
- [Splunk AI Toolkit](https://splunkbase.splunk.com/app/2890) - formerly MLTK
- [Splunk App for Data Science and Deep Learning](https://splunkbase.splunk.com/app/4607) - formerly DLTK

**Strategic Vision:**

Position the RAG Reference Architecture Lab as a **bridge between Splunk's existing AI platforms** and modern LLM/RAG deployments.

**Phase 4A: Splunk AI Toolkit Integration**

**Splunk AI Toolkit (MLTK) + RAG Lab:**
- Export RAG metrics to Splunk SPL for ML analysis
- Use MLTK assistants for RAG optimization:
  - **Predict Numeric Fields**: Predict query latency based on config
  - **Detect Numeric Outliers**: Identify anomalous response times
  - **Forecast Time Series**: Forecast token usage, cost trends
  - **Cluster Numeric Events**: Cluster similar queries for optimization
  - **Smart Prediction**: Predict which RAG config for given query

**RAG Metrics → Splunk SPL Pipeline:**
```spl
| makeresults 
| eval query="sample query", latency_ms=250, tokens=1500, 
       groundedness=0.94, cost=0.0005, config="balanced"
| collect index=rag_metrics
| timechart avg(latency_ms) by config
| predict latency_ms algorithm=LLP future_timespan=24h
```

**Generative AI Integration (MLTK 5.6+):**
- MLTK supports LLM integration in search pipelines
- Our RAG lab becomes the **reference implementation**
- Show customers: "This is how you monitor LLMs in Splunk"

**Value Proposition:**
*"The RAG Lab isn't separate from Splunk AI Toolkit - it's the next evolution. Use MLTK to analyze and optimize your RAG pipeline."*

---

**Phase 4B: Data Science & Deep Learning App Integration**

**DSDL + RAG Lab:**
- Leverage DSDL's Jupyter Lab Notebooks for RAG experimentation
- Use prebuilt containers (TensorFlow, PyTorch) for custom embeddings
- GPU acceleration for embedding generation at scale
- Classical ML for RAG optimization (which chunking strategy? which config?)

**Use Cases:**
1. **Custom Embedding Models**: Train domain-specific embeddings in DSDL, deploy in RAG
2. **Query Classification**: Use DSDL to classify query types → route to optimal RAG config
3. **Relevance Scoring**: Train custom re-ranker models in DSDL
4. **Anomaly Detection**: Detect unusual query patterns, potential attacks
5. **NLP Preprocessing**: Advanced text preprocessing before RAG retrieval

**Architecture:**
```
User Query → DSDL Query Classifier → 
    If factual: RAG Pipeline (our lab)
    If analytical: MLTK (forecasting, clustering)
    If creative: Direct LLM
→ Splunk Observability Cloud monitors all
```

**Integration Points:**

1. **Splunk AI Toolkit** ← RAG Metrics
   - Forecast token costs
   - Detect latency anomalies
   - Predict optimal config
   - Cluster query types

2. **DSDL** ← RAG Experiments
   - Custom embedding models
   - Query classifiers
   - Relevance scorers
   - Advanced NLP

3. **RAG Lab** ← Monitored by Observability
   - Production LLM deployment
   - Reference architecture
   - Field enablement platform

4. **Splunk Observability** → Monitors Everything
   - LLM observability (our focus)
   - ML model monitoring (MLTK/DSDL)
   - Full-stack visibility

---

**Phase 4C: Unified Splunk AI Platform Story**

**Customer Narrative:**

*"Splunk provides a complete AI platform - not just observability:*

**1. Build Models (DSDL)**
- Jupyter notebooks, TensorFlow, PyTorch
- Train custom classifiers, embeddings, NLP models
- GPU-accelerated training

**2. Deploy & Monitor LLMs (RAG Lab)**
- Production RAG architecture
- Groundedness, cost, latency tracking
- Hybrid search, knowledge graphs, re-ranking

**3. Analyze & Optimize (MLTK)**
- Forecast costs, predict latency
- Detect anomalies, cluster queries
- Optimize configurations with ML

**4. Observe Everything (Observability Cloud)**
- End-to-end visibility
- RAG-specific metrics
- Cost optimization
- Compliance & audit

*This is the only platform that covers the entire AI lifecycle."*

---

**Phase 4D: Field Enablement Expansion**

**Lab Series Concept:**

**Lab 1:** RAG Reference Architecture (current lab)
- Build production RAG
- Monitor with Splunk Observability
- 4-5 hours hands-on

**Lab 2:** Advanced RAG with MLTK
- Export metrics to Splunk
- Use MLTK assistants for optimization
- Forecast costs, detect anomalies
- 3-4 hours hands-on

**Lab 3:** Custom Models with DSDL
- Train custom embeddings
- Build query classifiers
- Deploy to RAG pipeline
- 4-5 hours hands-on

**Lab 4:** Production AI Platform
- Integrate all three (RAG + MLTK + DSDL)
- Complete customer deployment
- End-to-end monitoring
- 6-8 hours hands-on

**Certification Path:**
- Level 1: RAG Fundamentals (Lab 1) ✅
- Level 2: RAG Optimization (Lab 1 + 2)
- Level 3: Advanced AI (Lab 1 + 2 + 3)
- Level 4: AI Architect (All labs + deployment)

---

**Phase 4E: Product Integration Roadmap**

**Short-term (3-6 months):**
- Export RAG metrics to Splunk format
- Document MLTK integration patterns
- Create sample SPL queries for RAG analysis

**Medium-term (6-12 months):**
- Pre-built MLTK dashboards for RAG
- DSDL notebook templates for RAG
- Splunk app for RAG monitoring

**Long-term (12-24 months):**
- Native Splunk RAG capabilities
- Unified AI platform (MLTK + DSDL + RAG + Observability)
- Splunk as the enterprise AI platform

---

**Enterprise Value Proposition:**

**For Customers:**
*"You don't need to stitch together 5 vendors for AI:*
- *Build models: Splunk DSDL*
- *Deploy LLMs: Splunk RAG Reference Architecture*
- *Optimize: Splunk AI Toolkit*
- *Monitor: Splunk Observability Cloud*

*One platform. One vendor. Complete AI lifecycle."*

**For Splunk Field Teams:**
*"You're not just selling observability - you're selling the complete AI platform. This lab is the entry point."*

**For Splunk Leadership:**
*"We're positioning Splunk as THE enterprise AI platform - from data science to production deployment to monitoring. Our competitors can't match this breadth."*

---

**Success Metrics (Phase 4):**

- ✅ MLTK adoption increase (% of RAG customers also using MLTK)
- ✅ DSDL adoption increase (custom model training)
- ✅ Unified platform deals (RAG + MLTK + DSDL + Observability)
- ✅ Customer success stories (AI lifecycle on Splunk)
- ✅ Competitive wins against "AI platform" vendors

---

**Next Steps (Documented for Future):**

1. Complete Phase 2 (Current Lab Enhancement)
2. Build Phase 3 (Lab Development Framework)
3. Engage with Splunk AI Toolkit product team
4. Engage with DSDL product team
5. Design unified AI platform roadmap
6. Execute Phase 4 integration

---

**Status:** Long-term vision documented  
**Owner:** AI Enablement + Product teams  
**Timeline:** 12-24 months  
**Strategic Importance:** 🔥 HIGH - Platform differentiation

This positions Splunk as the ONLY vendor with a complete AI platform for enterprises.

