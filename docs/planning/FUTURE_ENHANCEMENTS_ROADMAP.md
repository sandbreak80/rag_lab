# 🚀 Future Enhancements Roadmap

**Date:** November 5, 2025
**Status:** 📋 Planning & Architecture
**Context:** Strategic features for production-ready RAG system

---

## 📊 Phase 1: Intelligent Prompt Enhancement & Routing

### 1.1 Advanced Prompt Enhancement Service

**Current State:** Basic security guardrails + simple enhancement
**Goal:** Intelligent, agentic prompt optimization

#### Features:

**A. Agentic Prompt Categorization**
```python
# Automatically classify prompts by:
- Intent (question, instruction, creative, analytical, coding)
- Domain (technical, medical, legal, general)
- Complexity (simple, moderate, complex, expert)
- Required reasoning (factual, analytical, creative, multi-step)
- Output format (short answer, detailed, structured, code)
```

**B. Framework-Based Enhancement**
```python
# Apply standard prompting frameworks:
- Chain-of-Thought (CoT) for complex reasoning
- ReAct (Reasoning + Acting) for multi-step tasks
- Few-Shot learning for structured outputs
- Self-Consistency for improved accuracy
- Tree of Thoughts for exploration
```

**C. Model-Aware Optimization**
```python
# Match prompt to model capabilities:
- Small models (3B): Simple, focused prompts
- Medium models (7-8B): Moderate complexity, some CoT
- Large models (70B+): Full CoT, complex reasoning
- Consider context window limits
```

**D. Dynamic Complexity Adjustment**
```python
class PromptEnhancer:
    def enhance(self, query, model_info):
        # Classify prompt
        category = self.classify(query)
        complexity = self.assess_complexity(query)

        # Select framework
        if complexity == 'complex' and model_info.size >= '8B':
            # Apply Chain-of-Thought
            enhanced = f"""Let's approach this step-by-step:

1. First, let's understand: {query}
2. Consider relevant information
3. Reason through the solution
4. Provide a clear answer

{query}
"""
        elif category == 'coding':
            # Structured coding prompt
            enhanced = f"""Task: {query}

Requirements:
- Write clean, well-documented code
- Include error handling
- Provide usage examples

Code:"""
        else:
            # Simple enhancement
            enhanced = query

        return enhanced
```

**UI Toggle:**
```typescript
// Settings panel
<Toggle
  label="🧠 Intelligent Prompt Enhancement"
  description="Automatically optimize prompts for better results"
  enabled={config.usePromptEnhancement}
  onChange={togglePromptEnhancement}
/>
```

---

### 1.2 Intelligent Model Routing

**Goal:** Automatically select the best model for each query

#### Architecture:

```
User Query
    ↓
┌─────────────────────────────┐
│  Prompt Analyzer            │
│  - Category                 │
│  - Complexity               │
│  - Token estimate           │
│  - Latency requirement      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Model Router               │
│  - Available models         │
│  - Current load             │
│  - Performance metrics      │
└────────────┬────────────────┘
             ↓
        ┌────┴────┐
        │         │
    ┌───▼──┐  ┌──▼───┐
    │ 3B   │  │ 8B   │
    │Fast  │  │Smart │
    └──────┘  └──────┘
```

#### Decision Matrix:

```python
class ModelRouter:
    MODELS = {
        'llama3.2:3b': {
            'size': 3,
            'context': 8192,
            'speed': 'fast',
            'best_for': ['simple', 'factual', 'quick'],
            'cost': 'low'
        },
        'llama3.1:8b': {
            'size': 8,
            'context': 128000,
            'speed': 'moderate',
            'best_for': ['moderate', 'analytical', 'multi-step'],
            'cost': 'medium'
        },
        'llama3.1:70b': {
            'size': 70,
            'context': 128000,
            'speed': 'slow',
            'best_for': ['complex', 'expert', 'reasoning'],
            'cost': 'high'
        }
    }

    def select_model(self, query_info):
        """
        Select best model based on:
        - Query complexity
        - Token count
        - User preference (speed vs quality)
        - Current system load
        """
        complexity = query_info['complexity']
        tokens = query_info['estimated_tokens']
        user_pref = query_info['user_preference']  # 'speed' or 'quality'

        if user_pref == 'speed' or complexity == 'simple':
            return 'llama3.2:3b'
        elif complexity == 'moderate' or tokens < 4000:
            return 'llama3.1:8b'
        else:
            return 'llama3.1:8b'  # Default to 8B (70B if available)
```

**UI Control:**
```typescript
// Auto-model selection toggle
<Select
  label="🎯 Model Selection"
  options={[
    { value: 'auto', label: 'Auto-select (Recommended)' },
    { value: 'speed', label: 'Optimize for Speed (3B)' },
    { value: 'balance', label: 'Balance (8B)' },
    { value: 'quality', label: 'Optimize for Quality (70B)' },
    { value: 'manual', label: 'Manual Selection' }
  ]}
/>
```

---

## 📊 Phase 2: Granular Data Source Controls

### 2.1 Independent Source Toggles

**Goal:** User controls exactly what data sources feed their RAG queries

#### UI Design:

```typescript
// Settings > Data Sources
<SettingsSection title="📚 Data Sources">
  <Description>
    Control which knowledge sources are used for your queries
  </Description>

  <ToggleCard
    icon="📄"
    label="Vector Database (User Uploads)"
    description="Your uploaded documents and personal knowledge base"
    enabled={config.useVectorDB}
    stats={{ documents: 142, chunks: 5230 }}
    onChange={toggleVectorDB}
  />

  <ToggleCard
    icon="🔬"
    label="Research Agent Papers"
    description="Auto-discovered AI research papers from arXiv"
    enabled={config.useResearchContent}
    stats={{ papers: 45, lastUpdate: '2 hours ago' }}
    onChange={toggleResearchContent}
  />

  <ToggleCard
    icon="🌐"
    label="Web Search"
    description="Real-time web search for current information"
    enabled={config.useWebSearch}
    stats={{ maxResults: config.webSearchDocs }}
    onChange={toggleWebSearch}
  />

  <ToggleCard
    icon="🧠"
    label="Knowledge Graph"
    description="Entity relationships and connections"
    enabled={config.useGraph}
    stats={{ nodes: 1250, edges: 3400 }}
    onChange={toggleGraph}
  />
</SettingsSection>
```

#### Backend Implementation:

```python
# services/search-service/app/service.py

def search_with_sources(query, config):
    """
    Search across selected sources only
    """
    all_results = []

    # Vector DB (user uploads + research papers are in same DB)
    if config.get('use_vector_db', True):
        vector_results = vector_db.search(query, filters={
            'source_type': 'user_upload'  # Only user docs
        })
        all_results.extend(vector_results)

    # Research content (from research agent)
    if config.get('use_research_content', True):
        research_results = vector_db.search(query, filters={
            'source_type': 'arxiv',
            'ingestion_source': 'research-agent'
        })
        all_results.extend(research_results)

    # Web search
    if config.get('use_web_search', False):
        web_results = web_search_service.search(query)
        all_results.extend(web_results)

    # Knowledge graph
    if config.get('use_graph', False):
        graph_results = knowledge_graph.expand(query)
        all_results.extend(graph_results)

    return deduplicate_and_rank(all_results)
```

#### Metadata Filtering:

```python
# Vector DB already supports this!
# Just need to tag content appropriately

# When research agent ingests:
metadata = {
    'source_type': 'arxiv',
    'ingestion_source': 'research-agent',
    'auto_discovered': True,
    # ...
}

# When user uploads:
metadata = {
    'source_type': 'user_upload',
    'ingestion_source': 'user',
    'uploaded_by': user_id,
    # ...
}
```

---

## 🔧 Phase 3: Multi-User Scalability & LLM Architecture

### 3.1 How Ollama Handles Concurrent Users

**Current Behavior (Ollama):**

```python
# Ollama's concurrency model:
- Single model instance = Sequential processing
- Queue-based: Request 1 → Request 2 → Request 3
- Parallel processing: Only with multiple model instances
- Context caching helps speed up similar requests
```

**For 5-10 Concurrent Users:**

```
Scenario A: Single 8B Model
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User 1: ████████ (8s) → Done
User 2:         ████████ (8s) → Done
User 3:                 ████████ → Done

Total wait: Up to 24 seconds for User 3!
❌ Poor experience
```

```
Scenario B: Multiple Model Instances
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User 1: ████████ (8s) → Done ✓
User 2: ████████ (8s) → Done ✓  (parallel!)
User 3: ████████ (8s) → Done ✓  (parallel!)

Max wait: 8-16 seconds
✅ Much better!
```

**Ollama Limitations:**
- ❌ Each model instance loads full model into VRAM
- ❌ 8B model = ~5GB VRAM per instance
- ❌ Can only run 2-3 instances on typical GPU (24GB VRAM)

---

### 3.2 Alternative: llama.cpp + vLLM

**llama.cpp:**
- ✅ More efficient memory usage
- ✅ Better CPU inference
- ✅ Quantization support (4-bit, 8-bit)
- ❌ More complex setup

**vLLM:**
- ✅ **PagedAttention** (much more efficient VRAM use)
- ✅ Continuous batching (process multiple requests together)
- ✅ Can serve 5-10 users with single model instance
- ✅ Production-grade performance
- ❌ GPU-only
- ❌ More complex setup

**Comparison:**

| Solution | VRAM Usage | Concurrent Users | Setup Complexity |
|----------|------------|------------------|------------------|
| Ollama (single) | 5GB | 1 (queued) | Easy ⭐⭐⭐ |
| Ollama (3x) | 15GB | 3 | Easy ⭐⭐⭐ |
| llama.cpp | 3GB | 2-3 (better CPU) | Medium ⭐⭐ |
| **vLLM** | **5GB** | **10-20** | Medium ⭐⭐ |

**Recommendation for 5-10 users:**
**→ Migrate to vLLM** (best performance/VRAM ratio)

---

### 3.3 Multi-Container LLM Architecture

**Proposed Architecture:**

```
┌─────────────────────────────────────────────────────┐
│               LLM Container 1                       │
│          "Background Processing"                    │
│                                                     │
│  - Document ingestion (chunking)                   │
│  - Embedding generation                            │
│  - Agentic chunking                                │
│  - Prompt classification                           │
│  - Prompt enhancement                              │
│                                                     │
│  Model: llama3.2:3b (small, fast, efficient)      │
│  VRAM: ~2GB                                        │
│  Priority: Low (background tasks)                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│               LLM Container 2                       │
│           "User Inference"                          │
│                                                     │
│  - User chat queries                               │
│  - RAG responses                                   │
│  - Real-time inference                             │
│                                                     │
│  Model: llama3.1:8b (smart, accurate)             │
│  VRAM: ~5GB                                        │
│  Priority: High (user-facing)                      │
│  Instances: 2-3 for concurrency                   │
└─────────────────────────────────────────────────────┘
```

**Benefits:**

✅ **Performance Isolation**
- Background tasks don't slow down user queries
- User queries always get priority

✅ **Resource Optimization**
- Small model (3B) for simple tasks
- Large model (8B) reserved for user inference

✅ **Better Concurrency**
- Multiple instances of user-facing model
- Background model can process in parallel

✅ **Cost Efficiency**
- Don't waste 8B model on simple tasks
- 3B model is 3x faster for chunking/classification

**VRAM Calculation:**
```
Background: 3B model × 1 instance =  2GB
User:       8B model × 2 instances = 10GB
                           Total  = 12GB

Fits on: RTX 3090 (24GB), RTX 4090 (24GB), A10 (24GB)
```

**vs Single Model:**
```
Current: 8B model × 1 instance = 5GB
         All tasks queue behind user queries
         Poor user experience with 5-10 concurrent users
```

**Docker Compose Implementation:**

```yaml
services:
  # Background processing LLM
  ollama-background:
    image: ollama/ollama:latest
    container_name: rag-ollama-background
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_MODELS=llama3.2:3b
    ports:
      - "11435:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # User-facing LLM (primary)
  ollama-inference-1:
    image: ollama/ollama:latest
    container_name: rag-ollama-inference-1
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_MODELS=llama3.1:8b
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # User-facing LLM (secondary) - for concurrency
  ollama-inference-2:
    image: ollama/ollama:latest
    container_name: rag-ollama-inference-2
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_MODELS=llama3.1:8b
    ports:
      - "11436:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Load balancer for inference containers
  ollama-loadbalancer:
    image: nginx:alpine
    container_name: rag-ollama-lb
    volumes:
      - ./config/ollama-lb.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "11400:80"
    depends_on:
      - ollama-inference-1
      - ollama-inference-2
```

**Load Balancer Config:**
```nginx
# config/ollama-lb.conf
upstream ollama_inference {
    least_conn;  # Route to least busy instance
    server ollama-inference-1:11434;
    server ollama-inference-2:11434;
}

server {
    listen 80;
    location / {
        proxy_pass http://ollama_inference;
    }
}
```

---

## 📊 Performance Projections

### Current (Single Ollama 8B):
```
Concurrent Users: 1-2
Avg Response Time: 8-10s
Queue Time: 0-30s
Throughput: ~6 queries/min
User Experience: ⚠️ Poor under load
```

### With Multi-Container (2× 8B + 1× 3B):
```
Concurrent Users: 5-10
Avg Response Time: 8-10s
Queue Time: 0-5s
Throughput: ~15 queries/min
User Experience: ✅ Good
```

### With vLLM (Single 8B with batching):
```
Concurrent Users: 10-20
Avg Response Time: 6-8s (faster!)
Queue Time: ~0s (continuous batching)
Throughput: ~30 queries/min
User Experience: ✅ Excellent
```

---

## 📋 Implementation TODOs

### Phase 1: Prompt Enhancement (2-3 days)
- [ ] Design prompt categorization taxonomy
- [ ] Implement classification model/rules
- [ ] Build framework-based enhancement
- [ ] Add model-aware optimization
- [ ] UI toggle in settings
- [ ] Testing & validation

### Phase 2: Model Routing (2-3 days)
- [ ] Design routing algorithm
- [ ] Implement complexity assessment
- [ ] Add load balancing logic
- [ ] UI model selection controls
- [ ] Performance monitoring
- [ ] A/B testing framework

### Phase 3: Data Source Controls (1-2 days)
- [ ] Update search service with source filtering
- [ ] Add UI toggles for each source
- [ ] Implement metadata-based filtering
- [ ] Add source statistics display
- [ ] Testing

### Phase 4: Multi-LLM Architecture (3-5 days)
- [ ] Set up multi-container Ollama
- [ ] Configure load balancer
- [ ] Route background vs user tasks
- [ ] Performance testing
- [ ] Documentation

### Phase 5: vLLM Migration (Optional, 2-3 days)
- [ ] Research vLLM setup
- [ ] Create vLLM Docker container
- [ ] Migration testing
- [ ] Performance comparison
- [ ] Rollout plan

---

## 📖 Documentation Requirements

All considerations from past 24 hours to document:

1. ✅ **Security hardening** (`SECURITY_HARDENING_INTERNET_FACING.md`)
2. ✅ **Research agent architecture** (`RESEARCH_AGENT_ARCHITECTURE.md`)
3. ✅ **Metadata best practices** (`RESEARCH_AGENT_METADATA_BEST_PRACTICES.md`)
4. ✅ **Scraping stack** (`RESEARCH_AGENT_SCRAPING_STACK.md`)
5. ✅ **This roadmap** (`FUTURE_ENHANCEMENTS_ROADMAP.md`)
6. ⏳ **LLM scaling guide** (TO CREATE)
7. ⏳ **Multi-user deployment** (TO CREATE)
8. ⏳ **Performance optimization** (TO CREATE)

---

## 🎯 Priority Recommendation

**Immediate (This Week):**
1. Complete Research Agent (almost done!)
2. Add data source toggles (quick win)

**Next Week:**
1. Multi-container LLM setup
2. Basic prompt enhancement

**Month 1:**
1. Intelligent model routing
2. vLLM migration for better concurrency

**Month 2:**
1. Advanced prompt frameworks
2. Production hardening
3. Comprehensive testing

---

**Status:** 📋 Roadmap complete! Ready for implementation prioritization.

