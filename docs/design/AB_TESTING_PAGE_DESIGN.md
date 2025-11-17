# A/B Testing Page - Comprehensive Design Document

**Last Updated:** November 17, 2025
**Status:** Design Phase
**Priority:** High - Core Lab Experience Feature

---

## 🎯 Overview

The A/B Testing page is a **critical educational tool** that allows students to:
- Compare different RAG configurations side-by-side
- Run standardized test prompts across presets
- Evaluate quality, performance, and accuracy metrics
- Use an auto-grader to objectively compare responses
- Visualize differences in responses, sources, and metrics

---

## 📋 Core Requirements

### 1. Standard Prompt Library (20 Prompts)

**Categories & Distribution:**

#### **Factual Queries (5 prompts)**
- Simple fact retrieval
- Single-answer questions
- Examples:
  - "What is RAG?"
  - "Explain the difference between vector search and keyword search"
  - "What is the context window limit for llama3.1:8b?"

#### **Analytical Queries (5 prompts)**
- Multi-step reasoning
- Comparison questions
- Examples:
  - "Compare and contrast naive RAG, advanced RAG, and agentic RAG systems"
  - "What are the trade-offs between using a 3B model vs 8B model for RAG?"
  - "Analyze the impact of chunk size on retrieval quality"

#### **Complex Multi-Hop Queries (4 prompts)**
- Require connecting multiple documents
- Knowledge graph traversal
- Examples:
  - "How does query expansion improve recall, and what are the latency costs?"
  - "Trace the data flow from document upload to final RAG response"
  - "What security measures are in place, and how do they affect response quality?"

#### **Temporal/Recency Queries (3 prompts)**
- Require recent information
- Test recency gate
- Examples:
  - "What are the latest developments in RAG architecture?"
  - "What recent research papers discuss agentic chunking?"
  - "What are the current best practices for production RAG systems?"

#### **Creative/Synthesis Queries (3 prompts)**
- Require synthesis of multiple concepts
- Creative problem-solving
- Examples:
  - "Design an optimal RAG pipeline for a customer support chatbot"
  - "How would you optimize this RAG system for a 16GB GPU?"
  - "Create a step-by-step guide for evaluating RAG quality"

**Prompt Metadata:**
```typescript
interface PromptLibraryItem {
  id: string;
  category: 'factual' | 'analytical' | 'multi-hop' | 'temporal' | 'creative';
  title: string;
  prompt: string;
  complexity: 'simple' | 'medium' | 'complex';
  expectedLength: 'short' | 'medium' | 'long';
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  expectedSources: number; // Expected number of sources
  expectedLatency: string; // e.g., "100-200ms"
}
```

---

## 🎨 Page Layout & Components

### **Main Layout Structure**

```
┌─────────────────────────────────────────────────────────────┐
│  A/B Testing Lab                                            │
│  Compare RAG configurations side-by-side                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Select Test Prompt                                 │
│  [Prompt Library Browser]                                    │
│  - Search/Filter by category, complexity, tags              │
│  - Preview prompt                                            │
│  - Custom prompt option                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Select Configurations to Compare                   │
│  ┌──────────────┐  vs  ┌──────────────┐                    │
│  │ Configuration A      │ Configuration B                   │
│  │ [Preset Selector]    │ [Preset Selector]                 │
│  │ OR                   │ OR                                │
│  │ [Custom Config]      │ [Custom Config]                   │
│  │                      │                                   │
│  │ [Show Details]       │ [Show Details]                    │
│  └──────────────┘      └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Run Test                                           │
│  [▶ Run A/B Test]  [⚙️ Advanced Options]                    │
│                                                              │
│  Options:                                                    │
│  - Run sequentially (one after another)                     │
│  - Run in parallel (simultaneous)                           │
│  - Auto-grade responses                                     │
│  - Save results to history                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  RESULTS: Side-by-Side Comparison                           │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ Configuration A      │  │ Configuration B      │        │
│  │                      │  │                      │        │
│  │ [Response]           │  │ [Response]           │        │
│  │ [Sources]            │  │ [Sources]            │        │
│  │ [Metrics]            │  │ [Metrics]            │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                              │
│  [Auto-Grader Results]                                      │
│  [Comparison Charts]                                        │
│  [Winner Indicator]                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Functionality

### **1. Prompt Library Component**

**Features:**
- Grid/list view of 20 prompts
- Filter by:
  - Category (factual, analytical, multi-hop, temporal, creative)
  - Complexity (simple, medium, complex)
  - Difficulty (beginner, intermediate, advanced)
  - Tags (RAG, models, architecture, etc.)
- Search functionality
- Preview modal with full prompt text
- "Use Custom Prompt" option
- Quick-select buttons for common prompts

**UI:**
```typescript
<PromptLibrary
  prompts={promptLibrary}
  onSelect={(prompt) => setSelectedPrompt(prompt)}
  selectedPrompt={selectedPrompt}
  showCustomOption={true}
/>
```

---

### **2. Configuration Selector (Dual)**

**Features:**
- Two side-by-side configuration selectors
- Each can select:
  - Quick Preset (Minimal, Fast, Balanced, Quality, Maximum, Production)
  - Custom configuration (full settings panel)
- "Copy from A to B" / "Swap" buttons
- Configuration preview card showing:
  - Model
  - Context window
  - Top-K
  - Enabled features
  - Expected latency

**UI:**
```typescript
<ConfigurationSelector
  label="Configuration A"
  value={configA}
  onChange={setConfigA}
  presets={presets}
  showCustom={true}
/>

<ConfigurationSelector
  label="Configuration B"
  value={configB}
  onChange={setConfigB}
  presets={presets}
  showCustom={true}
/>
```

---

### **3. Test Execution**

**Features:**
- Run both queries simultaneously or sequentially
- Progress indicators for each query
- Cancel button (stops both queries)
- Real-time metrics display as queries complete
- Error handling (if one fails, show partial results)

**API Calls:**
```typescript
// Parallel execution
const [resultA, resultB] = await Promise.all([
  api.sendMessage(prompt, configA, signalA, requestIdA),
  api.sendMessage(prompt, configB, signalB, requestIdB)
]);
```

---

### **4. Side-by-Side Results Display**

**Layout:**
- Split-screen view (50/50 or adjustable)
- Synchronized scrolling
- Diff highlighting (if enabled)
- Expandable sections:
  - Full response text
  - Sources list (with expandable content)
  - Metrics breakdown
  - Stage timings waterfall

**Components:**
```typescript
<ComparisonView>
  <ResultPanel
    config={configA}
    result={resultA}
    metrics={metricsA}
    sources={sourcesA}
    side="left"
  />
  <ResultPanel
    config={configB}
    result={resultB}
    metrics={metricsB}
    sources={sourcesB}
    side="right"
  />
</ComparisonView>
```

---

### **5. Metrics Comparison Table**

**Metrics to Display:**

| Metric | Configuration A | Configuration B | Winner |
|--------|----------------|-----------------|--------|
| **Response Time** | 234ms | 456ms | ⚡ A (faster) |
| **Total Latency** | 234ms | 456ms | ⚡ A |
| **Tokens In** | 1,234 | 2,456 | - |
| **Tokens Out** | 456 | 789 | - |
| **Context Window Used** | 4,096 / 16,384 | 8,192 / 20,480 | - |
| **Sources Retrieved** | 10 | 15 | - |
| **Sources Cited** | 5 | 8 | - |
| **Source Diversity** | RAG: 7, Web: 3 | RAG: 10, Web: 5 | - |
| **Precision (estimated)** | 85% | 92% | ⭐ B |
| **Recall (estimated)** | 80% | 88% | ⭐ B |
| **Answer Length** | 234 words | 456 words | - |
| **Citations Count** | 5 | 8 | - |
| **GPU Utilization** | 45% | 78% | - |
| **Memory Used** | 8.2 GB | 12.5 GB | - |

**Visual Indicators:**
- Green highlight for "better" metric (context-dependent)
- Red highlight for "worse" metric
- Neutral for descriptive metrics
- Percentage difference calculation

---

### **6. Auto-Grader Component**

**Purpose:** Use local LLM to objectively compare two responses

**Grading Dimensions:**

1. **Answer Quality** (0-1.0)
   - Completeness
   - Accuracy
   - Clarity
   - Structure

2. **Relevance** (0-1.0)
   - How well answer addresses the prompt
   - Coverage of key points

3. **Faithfulness/Grounding** (0-1.0)
   - Citations present and accurate
   - Answer grounded in sources
   - No hallucinations

4. **Completeness** (0-1.0)
   - All aspects of prompt addressed
   - Depth of coverage

5. **Conciseness** (0-1.0)
   - Appropriate length
   - No redundancy

6. **Source Quality** (0-1.0)
   - Relevance of sources
   - Diversity of sources
   - Source ranking quality

**Grading Prompt:**
```typescript
const gradingPrompt = `
You are an expert RAG evaluator. Compare two responses to the same query.

Query: "${prompt}"

Response A:
${responseA}

Response B:
${responseB}

Sources A: ${sourcesA.length} sources
Sources B: ${sourcesB.length} sources

Evaluate each response on these dimensions (0.0-1.0):
1. Answer Quality: Completeness, accuracy, clarity, structure
2. Relevance: How well it addresses the query
3. Faithfulness: Grounded in sources, proper citations
4. Completeness: All aspects covered
5. Conciseness: Appropriate length
6. Source Quality: Relevance and diversity of sources

Return JSON:
{
  "response_a": {
    "answer_quality": 0.85,
    "relevance": 0.90,
    "faithfulness": 0.88,
    "completeness": 0.82,
    "conciseness": 0.90,
    "source_quality": 0.85,
    "overall_score": 0.87,
    "strengths": ["Clear structure", "Good citations"],
    "weaknesses": ["Missing some details"]
  },
  "response_b": { ... },
  "winner": "A" | "B" | "tie",
  "explanation": "Response A wins because..."
}
`;
```

**Display:**
- Side-by-side scores
- Radar chart comparing dimensions
- Overall winner indicator
- Detailed explanation
- Strengths/weaknesses for each response

---

### **7. Visualization Components**

#### **A. Metrics Comparison Chart**
- Bar chart comparing key metrics
- Toggleable metrics
- Color-coded (green = better, red = worse)

#### **B. Latency Waterfall Comparison**
- Side-by-side waterfall charts
- Stage-by-stage timing comparison
- Highlight differences

#### **C. Source Distribution Chart**
- Pie/bar chart showing source types
- RAG vs Web vs Research vs KG
- Comparison view

#### **D. Quality Radar Chart**
- Multi-dimensional quality comparison
- Auto-grader scores
- Visual comparison

#### **E. Token Usage Chart**
- Input vs output tokens
- Context window utilization
- Cost estimation (if applicable)

---

### **8. Test History & Results Management**

**Features:**
- Save test results
- View test history
- Re-run previous tests
- Export results (JSON, CSV)
- Compare multiple test runs
- Filter/search history

**Storage:**
- Local storage for recent tests
- Backend API for persistent storage
- Test result schema:
```typescript
interface ABTestResult {
  id: string;
  timestamp: Date;
  prompt: PromptLibraryItem;
  configA: RAGConfig;
  configB: RAGConfig;
  resultA: RagResponse;
  resultB: RagResponse;
  metricsA: QueryMetric;
  metricsB: QueryMetric;
  graderResult?: GraderResult;
  winner?: 'A' | 'B' | 'tie';
  notes?: string;
}
```

---

### **9. Batch Testing Mode**

**Features:**
- Run all 20 prompts with selected configurations
- Progress indicator
- Results table with summary metrics
- Export all results
- Identify best configuration per prompt type

**UI:**
```
[Batch Test Mode]
- Select Configuration A: [Balanced ▼]
- Select Configuration B: [Quality ▼]
- Select Prompts: [All] [Factual Only] [Custom Selection...]
- [▶ Run Batch Test (20 prompts)]

Results Table:
| Prompt | Winner | A Latency | B Latency | A Quality | B Quality | ... |
```

---

## 📊 Metrics & Quality Measures

### **Performance Metrics**
- Total latency (ms)
- Stage timings breakdown:
  - Query expansion
  - Vector search
  - BM25 search
  - Hybrid fusion
  - Knowledge graph
  - Web search
  - Reranking
  - LLM generation
- Tokens per second
- GPU utilization
- Memory usage

### **Quality Metrics**
- **Precision** (estimated): % of top results that are relevant
- **Recall** (estimated): % of relevant docs retrieved
- **F1 Score**: Harmonic mean of precision and recall
- **MRR** (Mean Reciprocal Rank): Quality of first result
- **NDCG** (Normalized Discounted Cumulative Gain): Ranking quality
- **Answer Relevance**: LLM-as-judge score
- **Faithfulness**: Groundedness in sources
- **Citation Accuracy**: % of citations that are valid

### **Source Metrics**
- Total sources retrieved
- Sources cited by LLM
- Source diversity (RAG/Web/Research/KG ratio)
- Source score distribution
- Source recency (for temporal queries)

### **Response Metrics**
- Answer length (words, tokens)
- Citation count
- Citation coverage (% of claims cited)
- Response structure quality
- Completeness score

---

## 🔌 Backend API Requirements

### **New Endpoints Needed:**

#### **1. Prompt Library API**
```typescript
GET /v1/ab-testing/prompts
Response: {
  prompts: PromptLibraryItem[]
}

GET /v1/ab-testing/prompts/{id}
Response: PromptLibraryItem
```

#### **2. A/B Test Execution API**
```typescript
POST /v1/ab-testing/run
Body: {
  prompt: string,
  config_a: RAGConfig,
  config_b: RAGConfig,
  run_parallel: boolean,
  auto_grade: boolean
}
Response: {
  test_id: string,
  result_a: RagResponse,
  result_b: RagResponse,
  metrics_a: QueryMetric,
  metrics_b: QueryMetric,
  grader_result?: GraderResult
}
```

#### **3. Auto-Grader API**
```typescript
POST /v1/ab-testing/grade
Body: {
  prompt: string,
  response_a: string,
  response_b: string,
  sources_a: Source[],
  sources_b: Source[],
  config_a: RAGConfig,
  config_b: RAGConfig
}
Response: {
  response_a_scores: DimensionScores,
  response_b_scores: DimensionScores,
  winner: 'A' | 'B' | 'tie',
  explanation: string,
  strengths_a: string[],
  weaknesses_a: string[],
  strengths_b: string[],
  weaknesses_b: string[]
}
```

#### **4. Test History API**
```typescript
GET /v1/ab-testing/history
Query params: ?limit=20&offset=0
Response: {
  tests: ABTestResult[],
  total: number
}

POST /v1/ab-testing/save
Body: ABTestResult
Response: { id: string }

GET /v1/ab-testing/results/{test_id}
Response: ABTestResult
```

#### **5. Batch Testing API**
```typescript
POST /v1/ab-testing/batch
Body: {
  prompt_ids: string[],
  config_a: RAGConfig,
  config_b: RAGConfig
}
Response: {
  batch_id: string,
  results: ABTestResult[],
  summary: {
    total_tests: number,
    a_wins: number,
    b_wins: number,
    ties: number,
    avg_latency_a: number,
    avg_latency_b: number,
    avg_quality_a: number,
    avg_quality_b: number
  }
}
```

---

## 🎨 UI Components Needed

### **New Components:**

1. **`PromptLibraryBrowser.tsx`**
   - Grid/list view
   - Filters and search
   - Preview modal
   - Custom prompt input

2. **`ConfigurationSelector.tsx`**
   - Preset selector
   - Custom config expander
   - Configuration preview card

3. **`ABTestRunner.tsx`**
   - Test execution controls
   - Progress indicators
   - Error handling

4. **`ComparisonView.tsx`**
   - Split-screen layout
   - Synchronized scrolling
   - Diff highlighting

5. **`MetricsComparisonTable.tsx`**
   - Side-by-side metrics
   - Winner indicators
   - Percentage differences

6. **`AutoGraderResults.tsx`**
   - Score display
   - Radar chart
   - Detailed explanation
   - Strengths/weaknesses

7. **`ComparisonCharts.tsx`**
   - Latency waterfall
   - Source distribution
   - Quality radar
   - Token usage

8. **`TestHistory.tsx`**
   - History list
   - Filter/search
   - Re-run functionality
   - Export options

9. **`BatchTestRunner.tsx`**
   - Batch configuration
   - Progress tracking
   - Results table
   - Summary statistics

---

## 📁 File Structure

```
frontend/src/
├── pages/
│   └── ABTestingPage.tsx          # Main page component
├── components/
│   └── ab-testing/
│       ├── PromptLibraryBrowser.tsx
│       ├── ConfigurationSelector.tsx
│       ├── ABTestRunner.tsx
│       ├── ComparisonView.tsx
│       ├── ResultPanel.tsx
│       ├── MetricsComparisonTable.tsx
│       ├── AutoGraderResults.tsx
│       ├── ComparisonCharts.tsx
│       ├── TestHistory.tsx
│       ├── BatchTestRunner.tsx
│       └── PromptCard.tsx
├── data/
│   └── promptLibrary.ts            # 20 standard prompts
├── services/
│   └── api.ts                      # Add AB testing endpoints
└── types/
    └── abTesting.ts                # TypeScript interfaces

services/api/
├── routes/
│   └── ab_testing.py               # New route file
├── models.py                       # Add AB testing models
└── pipeline/
    └── auto_grader.py              # Enhanced auto-grader
```

---

## 🔍 Additional Features & Considerations

### **1. Advanced Comparison Options**
- **Diff View**: Highlight differences between responses
- **Source Overlap**: Show which sources are shared vs unique
- **Citation Comparison**: Compare citation patterns
- **Token-Level Analysis**: Compare token usage patterns

### **2. Export & Reporting**
- Export results as JSON
- Export comparison as PDF report
- CSV export for batch results
- Shareable test result links

### **3. Preset Recommendations**
- "Best for Speed" recommendation
- "Best for Quality" recommendation
- "Best Balance" recommendation
- Based on test results

### **4. Learning Mode**
- Explanations of why one config won
- Tips for optimization
- Links to relevant documentation
- Suggested next tests

### **5. Performance Optimization**
- Cache prompt library
- Lazy load results
- Virtual scrolling for long responses
- Debounced auto-grading

### **6. Accessibility**
- Keyboard navigation
- Screen reader support
- High contrast mode
- Adjustable font sizes

---

## 🚀 Implementation Phases

### **Phase 1: MVP (Core Functionality)**
- ✅ Prompt library (20 prompts)
- ✅ Configuration selector (presets only)
- ✅ Basic A/B test execution
- ✅ Side-by-side results display
- ✅ Basic metrics comparison table

### **Phase 2: Auto-Grader**
- ✅ Auto-grader API endpoint
- ✅ LLM-based grading
- ✅ Score display
- ✅ Winner determination

### **Phase 3: Visualizations**
- ✅ Comparison charts
- ✅ Waterfall charts
- ✅ Source distribution
- ✅ Quality radar

### **Phase 4: Advanced Features**
- ✅ Batch testing
- ✅ Test history
- ✅ Export functionality
- ✅ Custom prompts

### **Phase 5: Polish**
- ✅ Diff highlighting
- ✅ Advanced filters
- ✅ Performance optimization
- ✅ Documentation

---

## 🎓 Educational Value

### **Learning Objectives:**
1. **Understand Trade-offs**: See speed vs quality trade-offs in action
2. **Configuration Impact**: Learn how settings affect results
3. **Quality Metrics**: Understand precision, recall, faithfulness
4. **Model Comparison**: See how different models perform
5. **Optimization**: Learn to optimize for specific use cases

### **Lab Exercises:**
1. "Compare Minimal vs Maximum preset - what's the quality difference?"
2. "Find the optimal preset for factual queries"
3. "Which model performs best for analytical questions?"
4. "How does context window size affect response quality?"
5. "Run batch test: Which preset wins overall?"

---

## 📝 Data Models

### **TypeScript Interfaces:**

```typescript
// Prompt Library
interface PromptLibraryItem {
  id: string;
  category: 'factual' | 'analytical' | 'multi-hop' | 'temporal' | 'creative';
  title: string;
  prompt: string;
  complexity: 'simple' | 'medium' | 'complex';
  expectedLength: 'short' | 'medium' | 'long';
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  expectedSources: number;
  expectedLatency: string;
}

// A/B Test Result
interface ABTestResult {
  id: string;
  timestamp: Date;
  prompt: PromptLibraryItem;
  configA: RAGConfig;
  configB: RAGConfig;
  resultA: RagResponse;
  resultB: RagResponse;
  metricsA: QueryMetric;
  metricsB: QueryMetric;
  graderResult?: GraderResult;
  winner?: 'A' | 'B' | 'tie';
  notes?: string;
}

// Auto-Grader Result
interface GraderResult {
  responseA: {
    scores: DimensionScores;
    overallScore: number;
    strengths: string[];
    weaknesses: string[];
  };
  responseB: {
    scores: DimensionScores;
    overallScore: number;
    strengths: string[];
    weaknesses: string[];
  };
  winner: 'A' | 'B' | 'tie';
  explanation: string;
}

interface DimensionScores {
  answerQuality: number;
  relevance: number;
  faithfulness: number;
  completeness: number;
  conciseness: number;
  sourceQuality: number;
}
```

---

## 🔧 Technical Considerations

### **1. Auto-Grader Implementation**
- Use local LLM (llama3.1:8b or llama3.2:3b)
- Structured output (JSON mode)
- Fallback to heuristic scoring if LLM fails
- Cache grading results for same prompt/response pairs

### **2. Performance**
- Parallel query execution (if supported)
- Streaming responses (if available)
- Progressive rendering
- Lazy loading of heavy components

### **3. Error Handling**
- Graceful degradation if one query fails
- Retry logic
- Clear error messages
- Partial results display

### **4. State Management**
- Use Zustand store for test state
- Persist test history
- Cache prompt library
- Manage loading states

---

## 🎯 Success Criteria

### **Functional Requirements:**
- ✅ 20 diverse prompts in library
- ✅ Side-by-side configuration selection
- ✅ Parallel/sequential test execution
- ✅ Comprehensive metrics comparison
- ✅ Auto-grader with 6 dimensions
- ✅ Visual comparison charts
- ✅ Test history and export

### **Performance Requirements:**
- Page load < 2 seconds
- Test execution < 30 seconds (for both)
- Auto-grading < 10 seconds
- Smooth scrolling and interactions

### **Educational Requirements:**
- Clear winner indication
- Explanatory text for metrics
- Learning tips and recommendations
- Links to documentation

---

## 📚 Related Documentation

- [Chat Flow Architecture](./CHAT_FLOW_ARCHITECTURE.md)
- [Infrastructure & Services Reference](./INFRASTRUCTURE_SERVICES_REFERENCE.md)
- [Model Selection Guide](../features/MODEL_SELECTION_GUIDE.md)
- [RAG Quality Metrics](../lab/AI_FUNDAMENTALS.md#rag-quality-metrics)

---

**Next Steps:**
1. Review and approve design
2. Create prompt library (20 prompts)
3. Implement backend API endpoints
4. Build frontend components
5. Integrate auto-grader
6. Add visualizations
7. Test and refine

---

**Last Updated:** November 17, 2025

