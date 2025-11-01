# 🎓 Educational RAG Lab - Implementation Plan

**Goal:** Transform RAG Lab into an interactive learning experience
**Approach:** Hands-on experimentation with real-time metrics
**Timeline:** Implement in phases, test after each phase

---

## Implementation Phases

### ✅ Phase 0: Test Dataset Creation (FIRST - Foundation for metrics)
**Why first:** Metrics need ground truth to calculate precision/recall

**Deliverables:**
1. **Test Questions File** (`tests/evaluation_questions.json`)
   - 20 questions with expected relevant documents
   - Cover different query types (factual, conceptual, multi-hop)
   - Include ground truth answers

2. **Evaluation Script** (`src/evaluate_rag.py`)
   - Calculate precision, recall, MRR, NDCG
   - Run on test set or user queries
   - Return JSON results for UI display

**Example format:**
```json
{
  "questions": [
    {
      "id": "q1",
      "query": "What is vector search?",
      "relevant_docs": ["vector_search.md", "embeddings.md"],
      "expected_concepts": ["embeddings", "similarity", "cosine"],
      "difficulty": "basic"
    }
  ]
}
```

---

### Phase 1: Backend API Updates
**Goal:** Support configurable settings and return metrics

#### 1.1 Enhanced Search Endpoint
**File:** `services/search/app/service.py`

**New endpoint:** `POST /search_with_config`
```python
{
  "query": "vector embeddings",
  "config": {
    "use_query_expansion": true,
    "use_bm25": true,
    "use_hybrid": true,
    "use_graph": false,
    "use_reranking": false,
    "top_k": 10
  }
}

Response:
{
  "results": [...],
  "metrics": {
    "retrieval_time_ms": 45,
    "embedding_time_ms": 12,
    "bm25_time_ms": 18,
    "graph_time_ms": 0,
    "reranking_time_ms": 0,
    "total_time_ms": 75,
    "method_used": "hybrid"
  },
  "config_used": {...}
}
```

#### 1.2 Enhanced Chat Endpoint
**File:** `src/webapp.py`

**Update:** `POST /api/chat`
```python
{
  "message": "What are embeddings?",
  "llm_config": {
    "model": "llama3.2:3b",
    "temperature": 0.7,
    "max_tokens": 500,
    "context_window": 4000
  },
  "rag_config": {
    "use_query_expansion": true,
    "use_hybrid": true,
    "top_k": 5
  }
}

Response (streaming):
{
  "content": "...",
  "metadata": {
    "sources": [...],
    "metrics": {
      "total_latency_ms": 145,
      "retrieval_ms": 45,
      "llm_generation_ms": 100,
      "tokens_used": {
        "input": 450,
        "output": 120
      }
    }
  }
}
```

#### 1.3 New Evaluation Endpoint
**File:** `src/webapp.py`

**New endpoint:** `POST /api/evaluate`
```python
{
  "test_set_name": "default",  // or "custom"
  "config": {...}  // Same as search config
}

Response:
{
  "precision": 0.92,
  "recall": 0.88,
  "mrr": 0.85,
  "ndcg": 0.83,
  "coverage": 1.0,
  "avg_latency_ms": 145,
  "test_questions_count": 20,
  "breakdown": {
    "basic_questions": {
      "precision": 0.95,
      "recall": 0.90,
      "count": 10
    },
    "complex_questions": {
      "precision": 0.88,
      "recall": 0.85,
      "count": 10
    }
  }
}
```

---

### Phase 2: UI - Settings Panel
**Goal:** Let students configure RAG features

**File:** `src/templates/index.html`

**Layout:**
```
┌─────────────────────────────────────────┐
│  Header + Stats                         │
├─────────────┬───────────────────────────┤
│             │                           │
│  Settings   │   Main Chat Area         │
│  Panel      │                           │
│  (300px)    │   (Existing)             │
│             │                           │
│  [Collapse] │                           │
└─────────────┴───────────────────────────┘
```

**Settings Panel Components:**

#### Section 1: LLM Configuration
```html
<div class="settings-section">
  <h3>🤖 LLM Settings</h3>

  <label>Model</label>
  <select id="llm-model">
    <option value="llama3.2:1b">Llama 3.2 1B (Fast)</option>
    <option value="llama3.2:3b" selected>Llama 3.2 3B (Balanced)</option>
    <option value="llama3.2:8b">Llama 3.2 8B (Accurate)</option>
  </select>

  <label>Temperature: <span id="temp-value">0.7</span></label>
  <input type="range" id="temperature" min="0" max="1" step="0.1" value="0.7">

  <label>Max Tokens: <span id="tokens-value">500</span></label>
  <input type="range" id="max-tokens" min="100" max="2000" step="100" value="500">

  <label>Context Window: <span id="context-value">4000</span></label>
  <input type="range" id="context-window" min="1000" max="8000" step="1000" value="4000">
</div>
```

#### Section 2: RAG Pipeline Toggles
```html
<div class="settings-section">
  <h3>🔧 RAG Pipeline</h3>

  <div class="toggle-item">
    <input type="checkbox" id="use-query-expansion" checked>
    <label for="use-query-expansion">
      Query Expansion
      <span class="impact">+5% recall, +10ms</span>
      <span class="info-icon" title="Adds synonyms and related terms">ℹ️</span>
    </label>
  </div>

  <div class="toggle-item">
    <input type="checkbox" id="use-bm25" checked>
    <label for="use-bm25">
      BM25 Keyword Search
      <span class="impact">+15% recall, +30ms</span>
      <span class="info-icon" title="Statistical keyword matching">ℹ️</span>
    </label>
  </div>

  <div class="toggle-item">
    <input type="checkbox" id="use-hybrid" checked>
    <label for="use-hybrid">
      Hybrid Search (Vector + BM25)
      <span class="impact">+20% recall, +30ms</span>
      <span class="info-icon" title="Fuses semantic and keyword search">ℹ️</span>
    </label>
  </div>

  <div class="toggle-item">
    <input type="checkbox" id="use-graph">
    <label for="use-graph">
      Knowledge Graph
      <span class="impact">+5% recall, +50ms</span>
      <span class="info-icon" title="Finds related documents">ℹ️</span>
    </label>
  </div>

  <div class="toggle-item">
    <input type="checkbox" id="use-reranking">
    <label for="use-reranking">
      LLM Re-ranking
      <span class="impact">+10% precision, +2000ms</span>
      <span class="info-icon" title="Slow but very accurate">ℹ️</span>
    </label>
  </div>

  <label>Top-K Results: <span id="topk-value">5</span></label>
  <input type="range" id="top-k" min="1" max="20" step="1" value="5">
</div>
```

#### Section 3: Quick Presets
```html
<div class="settings-section">
  <h3>⚡ Quick Presets</h3>

  <button class="preset-btn" onclick="loadPreset('minimal')">
    Minimal (Everything OFF)
  </button>

  <button class="preset-btn" onclick="loadPreset('fast')">
    Fast (100ms)
  </button>

  <button class="preset-btn" onclick="loadPreset('balanced')">
    Balanced (200ms)
  </button>

  <button class="preset-btn" onclick="loadPreset('quality')">
    Max Quality (3s)
  </button>
</div>
```

---

### Phase 3: UI - Metrics Dashboard
**Goal:** Real-time performance visualization

**Layout:** Bottom expandable panel
```
┌─────────────────────────────────────────┐
│  Main Content                           │
├─────────────────────────────────────────┤
│  📊 Metrics  [Expand ▼]                 │
└─────────────────────────────────────────┘

When expanded:
┌─────────────────────────────────────────┐
│  📊 Metrics Dashboard                   │
├──────────────┬──────────────┬───────────┤
│  Retrieval   │  Generation  │ Quality   │
├──────────────┼──────────────┼───────────┤
│ Precision:92%│ Latency:145ms│ Score:8.5 │
│ Recall: 88%  │ Tokens: 1.2K │           │
│ MRR: 0.85    │              │           │
└──────────────┴──────────────┴───────────┘
```

**Metrics Display:**

#### Tab 1: Current Query Metrics
```html
<div class="metrics-tab" id="current-metrics">
  <div class="metric-card">
    <h4>Retrieval Performance</h4>
    <div class="metric-value">
      <span class="big-number">45ms</span>
      <span class="label">Retrieval Time</span>
    </div>
    <div class="metric-breakdown">
      <div>Vector: 20ms</div>
      <div>BM25: 15ms</div>
      <div>Fusion: 10ms</div>
    </div>
  </div>

  <div class="metric-card">
    <h4>Generation</h4>
    <div class="metric-value">
      <span class="big-number">100ms</span>
      <span class="label">LLM Time</span>
    </div>
    <div class="metric-breakdown">
      <div>Input tokens: 450</div>
      <div>Output tokens: 120</div>
    </div>
  </div>

  <div class="metric-card">
    <h4>Total Latency</h4>
    <div class="metric-value">
      <span class="big-number" id="total-latency">145ms</span>
      <span class="label">End-to-end</span>
    </div>
  </div>
</div>
```

#### Tab 2: Evaluation Metrics (Test Set)
```html
<div class="metrics-tab" id="eval-metrics" style="display:none">
  <button onclick="runEvaluation()">🧪 Run Evaluation on Test Set</button>

  <div id="eval-results">
    <div class="metric-grid">
      <div class="metric-box">
        <div class="metric-label">Precision</div>
        <div class="metric-number">92%</div>
        <div class="metric-bar" style="width: 92%"></div>
      </div>

      <div class="metric-box">
        <div class="metric-label">Recall</div>
        <div class="metric-number">88%</div>
        <div class="metric-bar" style="width: 88%"></div>
      </div>

      <div class="metric-box">
        <div class="metric-label">MRR</div>
        <div class="metric-number">0.85</div>
        <div class="metric-bar" style="width: 85%"></div>
      </div>

      <div class="metric-box">
        <div class="metric-label">NDCG</div>
        <div class="metric-number">0.83</div>
        <div class="metric-bar" style="width: 83%"></div>
      </div>
    </div>

    <div class="test-summary">
      Tested on 20 questions | Avg latency: 145ms
    </div>
  </div>
</div>
```

#### Tab 3: Pipeline Visualization
```html
<div class="metrics-tab" id="pipeline-viz" style="display:none">
  <div class="pipeline-flow">
    <div class="pipeline-step active">
      <div class="step-name">Query Expansion</div>
      <div class="step-time">10ms</div>
    </div>
    →
    <div class="pipeline-step active">
      <div class="step-name">Vector Search</div>
      <div class="step-time">20ms</div>
    </div>
    →
    <div class="pipeline-step active">
      <div class="step-name">BM25 Search</div>
      <div class="step-time">15ms</div>
    </div>
    →
    <div class="pipeline-step inactive">
      <div class="step-name">Knowledge Graph</div>
      <div class="step-time">0ms (OFF)</div>
    </div>
    →
    <div class="pipeline-step inactive">
      <div class="step-name">Re-ranking</div>
      <div class="step-time">0ms (OFF)</div>
    </div>
    →
    <div class="pipeline-step active">
      <div class="step-name">LLM Generation</div>
      <div class="step-time">100ms</div>
    </div>
  </div>
</div>
```

---

### Phase 4: Comparison Mode
**Goal:** A/B test different configurations

**Feature:** Side-by-side comparison

**UI:**
```
┌──────────────────────┬──────────────────────┐
│  Configuration A     │  Configuration B     │
├──────────────────────┼──────────────────────┤
│  Settings:           │  Settings:           │
│  • Query Exp: ON     │  • Query Exp: ON     │
│  • Re-ranking: OFF   │  • Re-ranking: ON    │
│                      │                      │
│  Results:            │  Results:            │
│  [Answer A]          │  [Answer B]          │
│                      │                      │
│  Metrics:            │  Metrics:            │
│  Latency: 145ms      │  Latency: 2145ms     │
│  Precision: 92%      │  Precision: 97%      │
└──────────────────────┴──────────────────────┘
      ↓ Delta: +5% precision for +2000ms
```

**JavaScript:**
```javascript
function compareConfigs(configA, configB, query) {
  // Run query with both configs
  Promise.all([
    runQueryWithConfig(query, configA),
    runQueryWithConfig(query, configB)
  ]).then(([resultA, resultB]) => {
    displayComparison(resultA, resultB);
    highlightDifferences(resultA, resultB);
  });
}
```

---

### Phase 5: Educational Tooltips & Help
**Goal:** Self-documenting UI

**Features:**
1. **Hover tooltips** on every setting
2. **Learn More** links to documentation
3. **What's This?** explanations
4. **Expected Impact** badges

**Example:**
```html
<div class="setting-item" data-tooltip="Adds synonyms and related terms to your query. Good for technical jargon.">
  <input type="checkbox" id="query-expansion">
  <label>Query Expansion</label>
  <span class="expected-impact">+5% recall, +10ms</span>
  <a href="#docs-query-expansion" class="learn-more">Learn More</a>
</div>
```

---

## Implementation Order

### Week 1: Foundation
- [ ] Create test dataset (20 questions)
- [ ] Build evaluation script
- [ ] Test evaluation locally

### Week 2: Backend
- [ ] Update search endpoint with config support
- [ ] Add metrics tracking to search
- [ ] Create evaluation API endpoint
- [ ] Update chat endpoint with config

### Week 3: UI - Settings
- [ ] Design and implement settings panel
- [ ] Add LLM configuration controls
- [ ] Add RAG pipeline toggles
- [ ] Create preset configurations

### Week 4: UI - Metrics
- [ ] Build metrics dashboard
- [ ] Implement real-time metric updates
- [ ] Add pipeline visualization
- [ ] Create evaluation UI

### Week 5: Polish
- [ ] Add comparison mode
- [ ] Write educational tooltips
- [ ] Create user guide
- [ ] Test with beta users

### Week 6: Lab Materials
- [ ] Write instructor guide
- [ ] Create student workbook
- [ ] Record demo videos
- [ ] Prepare for launch

---

## Technical Decisions

### Metrics Calculation Strategy
**Approach:** Hybrid (real-time + test set)

1. **Real-time metrics** (every query):
   - Latency (always available)
   - Token usage
   - Pipeline breakdown

2. **Test set evaluation** (on-demand):
   - Precision, recall, MRR, NDCG
   - Run when user clicks "Evaluate"
   - Cache results per configuration

**Rationale:** Balance accuracy and performance

### State Management
**Approach:** localStorage + URL params

```javascript
// Save config
localStorage.setItem('rag_config', JSON.stringify(config));

// Load on page reload
const savedConfig = JSON.parse(localStorage.getItem('rag_config'));

// Share via URL
window.location.hash = btoa(JSON.stringify(config));
```

**Rationale:** Students can share configurations

### Performance Optimization
**Strategy:** Progressive enhancement

1. Basic mode: No metrics (fastest)
2. Metrics mode: Latency only
3. Full evaluation: All metrics (on-demand)

**Rationale:** Don't slow down basic usage

---

## Success Criteria

### Technical:
- [ ] All settings work correctly
- [ ] Metrics update in real-time (<100ms)
- [ ] Evaluation completes in <30 seconds
- [ ] UI remains responsive during evaluation
- [ ] Works on laptops (8GB RAM)

### Educational:
- [ ] Students understand each setting
- [ ] Can explain trade-offs
- [ ] Successfully optimize for their use case
- [ ] Leave with working configuration

### User Experience:
- [ ] UI is intuitive (no training needed)
- [ ] Settings changes are immediate
- [ ] Comparison mode is helpful
- [ ] Metrics are understandable

---

**Ready to implement! Let's build an amazing educational experience! 🚀**

