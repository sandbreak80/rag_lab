# 🚀 Implementation Plan: 4 World-Class Features

**Goal:** Transform RAG lab into world-class teaching tool
**Timeline:** 18-24 hours total (can be split across sessions)
**Status:** 📋 Planning Complete → Ready to Execute

---

## 📊 Overview

| # | Feature | Time | Priority | Dependencies |
|---|---------|------|----------|--------------|
| 1 | **Waterfall Chart** | 4-6h | CRITICAL | None (ready now!) |
| 2 | **Query Decomposition** | 4-6h | HIGH | Feature 1 complete |
| 3 | **Self-RAG** | 8-10h | HIGH | Feature 2 complete |
| 4 | **Metadata Filtering** | 2h | MEDIUM | Can do anytime |

**Total Time:** 18-24 hours
**Approach:** Sequential implementation with testing between each
**Result:** World-class RAG teaching lab

---

# 🎨 FEATURE 1: Response Time Waterfall Chart

**Time:** 4-6 hours
**Impact:** ⭐⭐⭐⭐⭐ (Core teaching tool)

## 1.1 Architecture Design

### Data Flow
```
User Query
    ↓
API Gateway (timing orchestration)
    ├─ Security Validation (time: t1)
    ├─ Prompt Enhancement (time: t2)
    ├─ Model Routing (time: t3)
    ↓
Chat Service
    ├─ Query Expansion (time: t4)
    ├─ Vector Search (time: t5)
    ├─ BM25 Search (time: t6)
    ├─ Hybrid Fusion (time: t7)
    ├─ Knowledge Graph (time: t8)
    ├─ Re-ranking (time: t9)
    ├─ Web Search (time: t10)
    ├─ LLM Inference (time: t11)
    ↓
Response + PerformanceMetrics
```

### Data Structure
```typescript
// frontend/src/types/metrics.ts
export interface PerformanceMetrics {
  // Pre-processing
  security_validation_ms?: number;
  prompt_enhancement_ms?: number;
  model_routing_ms?: number;

  // Search pipeline
  query_expansion_ms?: number;
  vector_search_ms?: number;
  bm25_search_ms?: number;
  hybrid_fusion_ms?: number;
  knowledge_graph_ms?: number;
  reranking_ms?: number;
  web_search_ms?: number;

  // Generation
  llm_inference_ms?: number;

  // Totals
  total_latency_ms: number;
  search_total_ms?: number;
  preprocessing_total_ms?: number;
}
```

## 1.2 Implementation Steps

### Step 1.1: Frontend - Add Dependencies (15 min)
```bash
cd frontend
npm install recharts @types/recharts
```

### Step 1.2: Frontend - Create Waterfall Component (2 hours)
**File:** `frontend/src/components/metrics/WaterfallChart.tsx`

```typescript
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts';
import { PerformanceMetrics } from '../../types/metrics';

interface WaterfallChartProps {
  metrics: PerformanceMetrics;
  height?: number;
}

export function WaterfallChart({ metrics, height = 400 }: WaterfallChartProps) {
  // Define color scheme for different stages
  const COLORS = {
    'Security Validation': '#10b981',      // green
    'Prompt Enhancement': '#3b82f6',      // blue
    'Model Routing': '#8b5cf6',           // purple
    'Query Expansion': '#f59e0b',         // amber
    'Vector Search': '#ef4444',           // red
    'BM25 Search': '#ec4899',             // pink
    'Hybrid Fusion': '#06b6d4',           // cyan
    'Knowledge Graph': '#84cc16',         // lime
    'Re-ranking': '#f97316',              // orange
    'Web Search': '#dc2626',              // dark red
    'LLM Inference': '#6366f1',           // indigo
  };

  // Build data array with cumulative timing
  const data: Array<{
    name: string;
    start: number;
    duration: number;
    percentage: string;
  }> = [];

  let cumulative = 0;

  const stages = [
    { name: 'Security Validation', ms: metrics.security_validation_ms },
    { name: 'Prompt Enhancement', ms: metrics.prompt_enhancement_ms },
    { name: 'Model Routing', ms: metrics.model_routing_ms },
    { name: 'Query Expansion', ms: metrics.query_expansion_ms },
    { name: 'Vector Search', ms: metrics.vector_search_ms },
    { name: 'BM25 Search', ms: metrics.bm25_search_ms },
    { name: 'Hybrid Fusion', ms: metrics.hybrid_fusion_ms },
    { name: 'Knowledge Graph', ms: metrics.knowledge_graph_ms },
    { name: 'Re-ranking', ms: metrics.reranking_ms },
    { name: 'Web Search', ms: metrics.web_search_ms },
    { name: 'LLM Inference', ms: metrics.llm_inference_ms },
  ];

  stages.forEach(stage => {
    if (stage.ms && stage.ms > 0) {
      const percentage = ((stage.ms / metrics.total_latency_ms) * 100).toFixed(2);
      data.push({
        name: stage.name,
        start: cumulative,
        duration: stage.ms,
        percentage: `${percentage}%`,
      });
      cumulative += stage.ms;
    }
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Performance Waterfall</h3>
        <div className="text-sm text-muted-foreground">
          Total: <span className="font-bold text-foreground">
            {(metrics.total_latency_ms / 1000).toFixed(2)}s
          </span>
        </div>
      </div>

      <BarChart
        width={800}
        height={height}
        data={data}
        layout="vertical"
        margin={{ top: 20, right: 30, left: 150, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" label={{ value: 'Time (ms)', position: 'bottom' }} />
        <YAxis type="category" dataKey="name" width={140} />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-background border border-border rounded p-2 shadow-lg">
                  <p className="font-semibold">{data.name}</p>
                  <p className="text-sm">Duration: {data.duration.toFixed(0)}ms</p>
                  <p className="text-sm">Percentage: {data.percentage}</p>
                  <p className="text-xs text-muted-foreground">
                    Start: {data.start.toFixed(0)}ms
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="duration" stackId="a">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
          ))}
        </Bar>
      </BarChart>

      {/* Stage Breakdown Table */}
      <div className="mt-4 space-y-2">
        <h4 className="text-sm font-semibold">Stage Breakdown</h4>
        <div className="grid grid-cols-3 gap-2 text-sm">
          {data.map((stage, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: COLORS[stage.name as keyof typeof COLORS] }}
              />
              <span className="text-muted-foreground">{stage.name}:</span>
              <span className="font-mono">{stage.duration.toFixed(0)}ms</span>
              <span className="text-xs text-muted-foreground">({stage.percentage})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Step 1.3: Backend - Collect Timings in API Gateway (1 hour)
**File:** `services/api-gateway/app/service.py`

Already partially done! Just need to ensure all timing is captured and passed through.

```python
# Verify these lines exist in the /api/ask endpoint:
timing_metrics = {
    'security_validation_ms': 0,
    'prompt_enhancement_ms': 0,
    'model_routing_ms': 0,
    'rate_limit_check_ms': 0,
    'api_gateway_overhead_ms': 0,
}

# ... collect timings throughout pipeline ...

# Pass to chat response
chat_response['metrics'].update(timing_metrics)
```

### Step 1.4: Backend - Collect Timings in Chat Service (1 hour)
**File:** `services/chat/app/service.py`

Add timing collection for search stages:

```python
import time

perf_metrics = {
    'query_expansion_ms': 0,
    'vector_search_ms': 0,
    'bm25_search_ms': 0,
    'hybrid_fusion_ms': 0,
    'knowledge_graph_ms': 0,
    'reranking_ms': 0,
    'web_search_ms': 0,
    'llm_inference_ms': 0,
    'total_latency_ms': 0,
}

# Example: Time each stage
start = time.time()
vector_results = search_service.vector_search(query)
perf_metrics['vector_search_ms'] = (time.time() - start) * 1000

# ... repeat for all stages ...
```

### Step 1.5: Frontend - Integrate into UI (1 hour)
**Files:**
- `frontend/src/components/metrics/MetricsPanel.tsx` - Add to Metrics tab
- `frontend/src/components/chat/ChatInterface.tsx` - Show inline after query

```typescript
// In ChatInterface.tsx
{message.metrics && (
  <div className="mt-4 border-t pt-4">
    <WaterfallChart metrics={message.metrics} height={300} />
  </div>
)}
```

### Step 1.6: Testing & Documentation (30 min)
- Test with different presets (Minimal, Fast, Maximum)
- Screenshot waterfall for lab guide
- Document insights (e.g., "Web search is 84% of Maximum time")

---

# 🧩 FEATURE 2: Query Decomposition

**Time:** 4-6 hours
**Impact:** +18% on complex questions

## 2.1 Architecture Design

### Flow
```
Complex Query: "Compare hybrid search vs vector-only AND explain knowledge graphs"
        ↓
    Decomposer (LLM analyzes complexity)
        ↓
    Decision: Complex? → Decompose
        ↓
Sub-queries:
    1. "hybrid search performance"
    2. "vector search performance comparison"
    3. "what are knowledge graphs"
        ↓
    Parallel Search (3 searches simultaneously)
        ↓
    Result Fusion (deduplicate, merge)
        ↓
    LLM Synthesis (combine into coherent answer)
```

## 2.2 Implementation Steps

### Step 2.1: Create Query Decomposer Service (2 hours)
**New files:**
- `services/query-decomposer/app/service.py`
- `services/query-decomposer/requirements.txt`
- `services/query-decomposer/Dockerfile`

```python
# services/query-decomposer/app/service.py
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
MODEL = os.getenv('DECOMPOSER_MODEL', 'llama3.2:3b')  # Use fast model

@app.route('/decompose', methods=['POST'])
def decompose_query():
    """
    Decompose complex query into simpler sub-queries
    """
    data = request.json
    query = data.get('query', '')
    max_subqueries = data.get('max_subqueries', 3)

    # First: Assess if decomposition is needed
    complexity = assess_complexity(query)

    if complexity == 'simple':
        return jsonify({
            'original_query': query,
            'needs_decomposition': False,
            'sub_queries': [query],
            'strategy': 'single'
        })

    # Decompose using LLM
    decomposition_prompt = f"""Analyze this question and break it into 2-3 simpler sub-questions:

Question: "{query}"

Break this into separate, focused sub-questions. Each sub-question should be:
- Self-contained and clear
- Focused on one concept
- Searchable independently

Output format:
1. [sub-question 1]
2. [sub-question 2]
3. [sub-question 3]

Sub-questions:"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            'model': MODEL,
            'prompt': decomposition_prompt,
            'stream': False,
            'options': {'temperature': 0.3}
        }
    )

    if response.status_code != 200:
        return jsonify({'error': 'LLM decomposition failed'}), 500

    llm_output = response.json()['response']
    sub_queries = parse_subqueries(llm_output, max_subqueries)

    return jsonify({
        'original_query': query,
        'needs_decomposition': True,
        'sub_queries': sub_queries,
        'strategy': 'parallel',
        'complexity': complexity
    })

def assess_complexity(query: str) -> str:
    """Quick heuristic for complexity"""
    # Check for multiple concepts
    indicators = ['and', 'compare', 'contrast', 'both', 'also', 'additionally']
    has_multiple = any(ind in query.lower() for ind in indicators)

    # Check length
    word_count = len(query.split())

    if has_multiple or word_count > 20:
        return 'complex'
    return 'simple'

def parse_subqueries(llm_output: str, max_count: int) -> list:
    """Extract numbered sub-questions from LLM output"""
    lines = llm_output.strip().split('\n')
    sub_queries = []

    for line in lines:
        line = line.strip()
        # Match patterns like "1. question" or "- question"
        if line and (line[0].isdigit() or line.startswith('-')):
            # Remove numbering
            clean = line.lstrip('0123456789.-) ').strip()
            if len(clean) > 10:  # Minimum length for valid question
                sub_queries.append(clean)

        if len(sub_queries) >= max_count:
            break

    return sub_queries if sub_queries else [llm_output]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'query-decomposer'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8019, debug=False)
```

### Step 2.2: Update Docker Compose (15 min)
**File:** `docker-compose.yml`

```yaml
  query-decomposer:
    image: python:3.11-slim
    container_name: rag-query-decomposer
    ports:
      - "8019:8019"
    volumes:
      - ./services/query-decomposer/app:/app
    working_dir: /app
    environment:
      - SERVICE_PORT=8019
      - OLLAMA_BASE_URL=http://ollama:11434
      - DECOMPOSER_MODEL=llama3.2:3b
    command: bash -c "pip install -q flask requests && python service.py"
    depends_on:
      - ollama
    restart: unless-stopped
```

### Step 2.3: Integrate with Chat Service (2 hours)
**File:** `services/chat/app/service.py`

```python
DECOMPOSER_URL = os.getenv('DECOMPOSER_URL', 'http://query-decomposer:8019')

def handle_query_with_decomposition(query, config):
    """
    Check if query needs decomposition, execute accordingly
    """
    # Call decomposer
    decomp_response = requests.post(
        f"{DECOMPOSER_URL}/decompose",
        json={'query': query, 'max_subqueries': 3}
    )

    decomposition = decomp_response.json()

    if not decomposition['needs_decomposition']:
        # Simple query - normal flow
        return handle_single_query(query, config)

    # Complex query - parallel search
    sub_queries = decomposition['sub_queries']
    print(f"🧩 Decomposed into {len(sub_queries)} sub-queries")

    # Search all sub-queries in parallel (or sequentially for now)
    all_results = []
    for sub_q in sub_queries:
        results = search_service.search(sub_q, config)
        all_results.extend(results)

    # Deduplicate by content similarity
    unique_results = deduplicate_results(all_results)

    # Synthesize answer using all results
    synthesis_prompt = f"""Original question: {query}

I searched for:
{chr(10).join(f'{i+1}. {sq}' for i, sq in enumerate(sub_queries))}

Based on the retrieved documents, provide a comprehensive answer to the original question.

Retrieved information:
{format_results(unique_results)}

Answer:"""

    # Generate with LLM
    answer = generate_llm_response(synthesis_prompt, config)

    return {
        'answer': answer,
        'decomposition': decomposition,
        'sub_queries': sub_queries,
        'total_sources': len(unique_results),
        'sources': unique_results
    }
```

### Step 2.4: Frontend - Show Decomposition (1 hour)
**File:** `frontend/src/components/chat/MessageItem.tsx`

```typescript
{message.decomposition && (
  <div className="mt-2 p-3 bg-muted rounded-lg">
    <p className="text-sm font-semibold mb-2">🧩 Query Decomposition:</p>
    <ul className="text-sm space-y-1">
      {message.decomposition.sub_queries.map((sq, idx) => (
        <li key={idx} className="text-muted-foreground">
          {idx + 1}. {sq}
        </li>
      ))}
    </ul>
  </div>
)}
```

### Step 2.5: Testing (30 min)
Test with complex queries:
- "Compare hybrid search vs vector-only and explain knowledge graphs"
- "What are transformers and how do they differ from RNNs and LSTMs"
- "Explain RAG, its benefits, and when to use it vs fine-tuning"

---

# 🔄 FEATURE 3: Self-RAG (Iterative Refinement)

**Time:** 8-10 hours
**Impact:** +20% complex, -15% hallucination, ⭐⭐⭐⭐⭐ wow factor

## 3.1 Architecture Design

### Iteration Loop
```
User Query
    ↓
Iteration 1:
    ├─ Retrieve documents
    ├─ LLM Critique: "Are these sufficient?"
    ├─ Decision: Good? → Generate answer
    │           Bad?  → Refine query
    ↓
Iteration 2:
    ├─ Retrieve with refined query
    ├─ LLM Critique: "Better?"
    ├─ Decision: Good? → Generate answer
    │           Bad?  → Refine again
    ↓
Max 3 iterations → Final answer
```

## 3.2 Implementation Steps

### Step 3.1: Create Self-RAG Service (4 hours)
**New files:**
- `services/self-rag/app/service.py`
- `services/self-rag/app/critic.py`

```python
# services/self-rag/app/critic.py
import requests

class RAGCritic:
    """
    Critiques retrieval quality and suggests refinements
    """

    def __init__(self, llm_url, model='llama3.1:8b'):
        self.llm_url = llm_url
        self.model = model

    def critique_retrieval(self, query: str, documents: list) -> dict:
        """
        Assess if retrieved documents are sufficient to answer query

        Returns:
            {
                'sufficient': bool,
                'confidence': float,
                'reasoning': str,
                'refined_query': str (if not sufficient),
                'missing_aspects': list
            }
        """
        # Build critique prompt
        docs_summary = self._summarize_documents(documents)

        critique_prompt = f"""You are evaluating retrieval quality.

Original Question: "{query}"

Retrieved Documents Summary:
{docs_summary}

Task: Assess if these documents contain sufficient information to answer the question.

Consider:
1. Do documents cover all aspects of the question?
2. Is the information relevant and specific?
3. Are key concepts addressed?
4. Is additional information needed?

Respond in this format:
SUFFICIENT: Yes/No
CONFIDENCE: 0.0-1.0
REASONING: [Brief explanation]
MISSING: [List any missing aspects, or "None"]
REFINED_QUERY: [If not sufficient, suggest a better search query]

Assessment:"""

        response = requests.post(
            f"{self.llm_url}/api/generate",
            json={
                'model': self.model,
                'prompt': critique_prompt,
                'stream': False,
                'options': {'temperature': 0.2}  # Lower temp for consistency
            }
        )

        llm_output = response.json()['response']

        # Parse structured output
        return self._parse_critique(llm_output, query)

    def _summarize_documents(self, documents: list) -> str:
        """Create concise summary of retrieved documents"""
        summaries = []
        for i, doc in enumerate(documents[:5], 1):  # Top 5 only
            title = doc.get('metadata', {}).get('title', 'Unknown')
            content_preview = doc.get('content', '')[:200]
            summaries.append(f"{i}. [{title}]: {content_preview}...")
        return '\n'.join(summaries)

    def _parse_critique(self, llm_output: str, original_query: str) -> dict:
        """Parse LLM critique output"""
        lines = llm_output.split('\n')
        result = {
            'sufficient': False,
            'confidence': 0.5,
            'reasoning': '',
            'refined_query': original_query,
            'missing_aspects': []
        }

        for line in lines:
            line = line.strip()
            if line.startswith('SUFFICIENT:'):
                result['sufficient'] = 'yes' in line.lower()
            elif line.startswith('CONFIDENCE:'):
                try:
                    result['confidence'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('REASONING:'):
                result['reasoning'] = line.split(':', 1)[1].strip()
            elif line.startswith('MISSING:'):
                missing = line.split(':', 1)[1].strip()
                if missing.lower() not in ['none', 'n/a']:
                    result['missing_aspects'] = [missing]
            elif line.startswith('REFINED_QUERY:'):
                result['refined_query'] = line.split(':', 1)[1].strip()

        return result


# services/self-rag/app/service.py
from flask import Flask, request, jsonify
from critic import RAGCritic
import requests
import os

app = Flask(__name__)

OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
SEARCH_URL = os.getenv('SEARCH_SERVICE_URL', 'http://search-service:8002')
CHAT_URL = os.getenv('CHAT_SERVICE_URL', 'http://chat-service:8003')

critic = RAGCritic(OLLAMA_URL)

@app.route('/self-rag', methods=['POST'])
def self_rag_query():
    """
    Execute Self-RAG iteration loop
    """
    data = request.json
    query = data.get('query', '')
    config = data.get('config', {})
    max_iterations = data.get('max_iterations', 3)

    iterations = []
    current_query = query

    for iteration in range(max_iterations):
        print(f"🔄 Self-RAG Iteration {iteration + 1}")

        # Step 1: Retrieve documents
        search_response = requests.post(
            f"{SEARCH_URL}/search",
            json={'query': current_query, 'top_k': 10, **config}
        )
        documents = search_response.json().get('results', [])

        # Step 2: Critique retrieval
        critique = critic.critique_retrieval(current_query, documents)

        iteration_data = {
            'iteration': iteration + 1,
            'query': current_query,
            'documents_retrieved': len(documents),
            'critique': critique
        }
        iterations.append(iteration_data)

        # Step 3: Decision
        if critique['sufficient'] or critique['confidence'] > 0.7:
            print(f"✅ Retrieval sufficient (confidence: {critique['confidence']:.2f})")
            break

        # Step 4: Refine query for next iteration
        current_query = critique['refined_query']
        print(f"🔧 Refining query: {current_query}")

    # Final generation with best documents
    final_response = requests.post(
        f"{CHAT_URL}/chat",
        json={
            'query': query,
            'documents': documents,
            'config': config
        }
    )

    return jsonify({
        'answer': final_response.json().get('answer', ''),
        'iterations': iterations,
        'total_iterations': len(iterations),
        'final_confidence': iterations[-1]['critique']['confidence'],
        'sources': documents
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'self-rag'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8020, debug=False)
```

### Step 3.2: Update Docker Compose (15 min)
Add self-rag service to docker-compose.yml (port 8020)

### Step 3.3: Integration & UI (2 hours)
- Add toggle in settings: "🔄 Self-RAG (Iterative Refinement)"
- Show iteration progress in chat
- Display critique reasoning

### Step 3.4: Testing & Optimization (2 hours)
- Test with ambiguous queries
- Tune confidence thresholds
- Optimize iteration count

---

# 🎛️ FEATURE 4: Metadata Filtering UI

**Time:** 2 hours
**Impact:** +5% precision, better UX

## 4.1 Implementation Steps

### Step 4.1: Frontend Filter Component (1 hour)
**File:** `frontend/src/components/chat/MetadataFilters.tsx`

```typescript
export function MetadataFilters() {
  const [filters, setFilters] = useState({
    documentTypes: ['pdf', 'markdown', 'docx'],
    dateRange: 'all',
    sources: ['user_upload', 'research_agent', 'web_search'],
    tags: []
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>🎛️ Filter Results</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Document Type */}
        <div>
          <Label>Document Type</Label>
          <div className="flex gap-2">
            {['PDF', 'Markdown', 'Word', 'PowerPoint'].map(type => (
              <Toggle key={type} aria-label={type}>
                {type}
              </Toggle>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div>
          <Label>Date Range</Label>
          <Select value={filters.dateRange} onValueChange={(v) => setFilters({...filters, dateRange: v})}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Time</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
              <SelectItem value="90d">Last 3 Months</SelectItem>
              <SelectItem value="1y">Last Year</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Source */}
        <div>
          <Label>Source</Label>
          <div className="space-y-2">
            {[
              { id: 'user_upload', label: '📄 Uploaded Documents', count: 127 },
              { id: 'research_agent', label: '🔬 Research Papers', count: 78 },
              { id: 'web_search', label: '🌐 Web Search', count: 0 }
            ].map(source => (
              <div key={source.id} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={filters.sources.includes(source.id)}
                    onCheckedChange={(checked) => {
                      // Toggle source
                    }}
                  />
                  <Label>{source.label}</Label>
                </div>
                <span className="text-sm text-muted-foreground">
                  ({source.count})
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Step 4.2: Backend Filtering (1 hour)
**File:** `services/search/app/service.py`

```python
def apply_metadata_filters(query, filters):
    """
    Apply ChromaDB metadata filters
    """
    where_clause = {}

    # Document type filter
    if filters.get('document_types'):
        where_clause['file_type'] = {'$in': filters['document_types']}

    # Date range filter
    if filters.get('date_range') and filters['date_range'] != 'all':
        cutoff_date = get_cutoff_date(filters['date_range'])
        where_clause['upload_date'] = {'$gte': cutoff_date}

    # Source filter
    if filters.get('sources'):
        where_clause['source_type'] = {'$in': filters['sources']}

    # Search with filters
    results = vector_db.query(
        query_embeddings=embed(query),
        n_results=top_k,
        where=where_clause
    )

    return results
```

---

# 📋 Execution Checklist

## Pre-Implementation
- [ ] Review all 4 feature designs
- [ ] Confirm dependencies installed (recharts, etc.)
- [ ] Backup current working state
- [ ] Create feature branch: `git checkout -b features/waterfall-decomp-selfrag-filters`

## Feature 1: Waterfall Chart ✅
- [ ] Install recharts
- [ ] Create WaterfallChart.tsx component
- [ ] Update PerformanceMetrics types
- [ ] Ensure API Gateway captures all timing
- [ ] Ensure Chat Service captures all timing
- [ ] Add to MetricsPanel
- [ ] Add inline to ChatInterface
- [ ] Test with Minimal preset
- [ ] Test with Maximum preset
- [ ] Screenshot for documentation
- [ ] Document insights

## Feature 2: Query Decomposition ✅
- [ ] Create query-decomposer service
- [ ] Add to docker-compose.yml
- [ ] Implement decomposition logic
- [ ] Add complexity assessment
- [ ] Integrate with chat service
- [ ] Add parallel search execution
- [ ] Implement result fusion
- [ ] Add UI display for sub-queries
- [ ] Test with complex queries
- [ ] Document examples

## Feature 3: Self-RAG ✅
- [ ] Create self-rag service
- [ ] Implement RAGCritic class
- [ ] Add critique logic
- [ ] Add refinement logic
- [ ] Add iteration loop
- [ ] Add to docker-compose.yml
- [ ] Integrate with chat service
- [ ] Add UI toggle for Self-RAG
- [ ] Show iteration progress
- [ ] Display critique reasoning
- [ ] Test and tune confidence thresholds
- [ ] Document behavior

## Feature 4: Metadata Filtering ✅
- [ ] Create MetadataFilters component
- [ ] Add document type filters
- [ ] Add date range filters
- [ ] Add source filters
- [ ] Add tag filters
- [ ] Update search service filtering
- [ ] Test filters combination
- [ ] Show filtered document count
- [ ] Document usage

## Post-Implementation
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create demo video/screenshots
- [ ] Update lab guide
- [ ] Git commit & push
- [ ] Celebrate! 🎉

---

# 🎯 Success Criteria

## Feature 1 Success
- ✅ Waterfall chart displays all pipeline stages
- ✅ Timing accurate within 10ms
- ✅ Works with all presets
- ✅ Color-coded by stage
- ✅ Shows percentage breakdown
- ✅ Inline and in Metrics tab

## Feature 2 Success
- ✅ Complex queries decomposed into 2-3 sub-queries
- ✅ Simple queries bypass decomposition
- ✅ Parallel search executes correctly
- ✅ Results deduplicated and merged
- ✅ Final answer synthesizes all results
- ✅ UI shows decomposition clearly

## Feature 3 Success
- ✅ Iteration loop executes (1-3 iterations)
- ✅ Critique assesses retrieval quality
- ✅ Query refinement improves results
- ✅ Stops when sufficient confidence reached
- ✅ UI shows iteration progress
- ✅ Final confidence score displayed

## Feature 4 Success
- ✅ All filter types working
- ✅ Filters combine correctly (AND logic)
- ✅ Document count updates in real-time
- ✅ Clear button resets all filters
- ✅ Filtered results accurate

---

# 📊 Expected Impact

## After All 4 Features:

### Educational Value
- ⭐⭐⭐⭐⭐ **Waterfall:** Core teaching tool (visualize trade-offs)
- ⭐⭐⭐⭐☆ **Decomposition:** Advanced RAG patterns
- ⭐⭐⭐⭐☆ **Self-RAG:** Cutting-edge quality
- ⭐⭐⭐☆☆ **Filters:** Practical UX

### Lab Quality
- **Before:** Good RAG demo
- **After:** World-class teaching lab with cutting-edge features

### Impressiveness
- Unique waterfall visualization
- Agentic behavior (decomposition + self-rag)
- Production-ready filtering
- **Result:** Conference-quality demo

---

# ⏱️ Timeline

| Day | Time | Features | Total Hours |
|-----|------|----------|-------------|
| **Day 1** | 4-6h | Feature 1: Waterfall Chart | 4-6h |
| **Day 2** | 4-6h | Feature 2: Query Decomposition | 8-12h |
| **Day 3** | 4-5h | Feature 3: Self-RAG (Part 1) | 12-17h |
| **Day 4** | 4-5h | Feature 3: Self-RAG (Part 2) | 16-22h |
| **Day 5** | 2h | Feature 4: Metadata Filtering | 18-24h |

**Total:** 18-24 hours over 5 days (or longer if split across sessions)

---

# 🚀 Ready to Execute!

**Status:** 📋 **PLAN COMPLETE** → Ready to implement

**Next Step:** Start with Feature 1 (Waterfall Chart)

**Expected Outcome:** World-class RAG teaching lab with:
- ✅ Core teaching visualization (Waterfall)
- ✅ Advanced intelligence (Decomposition)
- ✅ Cutting-edge quality (Self-RAG)
- ✅ Professional UX (Metadata Filters)

Let's build something amazing! 🎉


