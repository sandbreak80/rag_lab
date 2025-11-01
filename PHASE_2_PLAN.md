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

| Phase | Hours | Priority |
|-------|-------|----------|
| 2A: AI Fundamentals Docs | 2-3 | HIGH |
| 2B: Ollama Model API | 1-2 | HIGH |
| 2C: Enhanced Metrics | 2-3 | HIGH |
| 2D: Multi-Tab UI | 3-4 | MEDIUM |
| 2E: Metrics Dashboard | 3-4 | HIGH |
| 2F: Web Search Config | 1-2 | MEDIUM |
| 2G: Model Comparison | 2-3 | MEDIUM |
| 2H: Testing & Docs | 2-3 | HIGH |
| **TOTAL** | **17-24 hours** | |

---

## 🎯 Deliverables

### Documentation
- ✅ This planning document (PHASE_2_PLAN.md)
- ⏳ docs/lab/AI_FUNDAMENTALS.md (12 sections)
- ⏳ docs/lab/MODEL_COMPARISON_EXERCISE.md
- ⏳ docs/lab/METRICS_GUIDE.md
- ⏳ Updated existing lab docs

### Code
- ⏳ Multi-tab UI (HTML/CSS/JS)
- ⏳ Metrics dashboard tab
- ⏳ Enhanced metrics collection
- ⏳ Ollama model API wrapper
- ⏳ Web search configuration
- ⏳ Model comparison interface (optional)

### Features
- ⏳ Dynamic model selector (from Ollama API)
- ⏳ Comprehensive metrics tracking
- ⏳ Session-wide metrics aggregation
- ⏳ Metrics export (CSV/JSON)
- ⏳ Web search customization
- ⏳ Model comparison exercise

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

## 📋 Next Steps

1. **Get approval on plan**
2. **Start with Phase 2A** (AI Fundamentals Docs)
3. **Then Phase 2B & 2C** (Backend enhancements)
4. **Then Phase 2D & 2E** (UI restructure + metrics)
5. **Finally 2F, 2G, 2H** (Additional features + testing)

---

**Status:** ⏳ AWAITING APPROVAL TO PROCEED

**Questions for User:**
1. Does this plan address all requirements?
2. Any priorities to adjust?
3. Should we do this in phases or all at once?
4. Any specific models you want to focus on?
5. Approve to start with Phase 2A (documentation)?

