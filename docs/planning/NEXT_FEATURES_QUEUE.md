# Next Features Queue

**Status:** Not yet implemented  
**Priority order:** Based on effort/impact ratio

---

## 1. Metadata Filtering UI ⭐⭐⭐☆☆

### What it does
Let users filter RAG results by document attributes before search

### UI Design
```
Filters:
- Document Type: [✓ PDF] [✓ Word] [✓ PowerPoint] [✓ Markdown]
- Date Range: [Last 7 days ▼] [Last month] [Last year] [All time]
- Tags: [✓ AI] [✓ RAG] [✓ LLM] [✓ Enterprise]
- Source: [✓ Research Agent] [✓ Uploaded Docs] [✓ Web Search]
- Author: [Select author ▼]
```

### Implementation
1. Add filter component to frontend Chat tab
2. Pass filter params to search service
3. Apply ChromaDB metadata filters (`where` clause)
4. Display filtered document count

### Impact
- **Precision:** +5%
- **UX:** Much better control
- **Use case:** "Show me only research papers from last month"

### Effort
- **Time:** 2 hours
- **Complexity:** Low (we already have metadata)

### Files to modify
- `frontend/src/components/chat/ChatInterface.tsx` - Add filter UI
- `services/search/app/service.py` - Accept filter params
- `services/vector-db/app/service.py` - Apply ChromaDB where clause

---

## 2. Query Decomposition ⭐⭐⭐⭐☆

### What it does
Break complex questions into simpler sub-queries, search in parallel, synthesize results

### Example
**User query:**  
"Compare hybrid search performance vs vector-only and explain knowledge graphs"

**Decomposed:**
1. "hybrid search performance metrics"
2. "vector search performance comparison"
3. "what is a knowledge graph"

**Process:**
1. LLM decomposes query → 3 sub-queries
2. Search service runs 3 searches in parallel
3. LLM synthesizes combined answer

### Implementation
Create new microservice: `query-decomposer`

```python
# services/query-decomposer/app/service.py
@app.route('/decompose', methods=['POST'])
def decompose_query():
    query = request.json['query']
    
    # Use LLM to decompose
    sub_queries = llm_decompose(query)
    
    return {
        'original': query,
        'sub_queries': sub_queries,
        'strategy': 'parallel'  # or 'sequential'
    }
```

### Integration
1. Chat service calls decomposer
2. If complex (>2 concepts) → decompose
3. Parallel search for each sub-query
4. Combine results, deduplicate
5. Synthesize final answer

### Impact
- **Complex questions:** +18%
- **Hallucination:** -10% (more context)
- **Use case:** Multi-faceted research questions

### Effort
- **Time:** 4-6 hours
- **Complexity:** Medium

### Files to create
- `services/query-decomposer/` - New service
- `services/query-decomposer/app/service.py` - Decomposition logic
- `services/query-decomposer/requirements.txt` - Dependencies

### Files to modify
- `docker-compose.yml` - Add service
- `services/chat/app/service.py` - Integrate decomposition
- `services/search/app/service.py` - Handle sub-query batches

---

## 3. Self-RAG (Iterative Refinement) ⭐⭐⭐⭐☆

### What it does
LLM critiques its own retrieval quality and refines if needed

### Process Flow
```
1. User query → Initial retrieval
2. LLM critique: "Are these docs sufficient?"
   ├─ Yes → Generate answer
   └─ No → Refine query, retrieve again (up to 3 iterations)
3. Quality gate before final answer
```

### Example
**User:** "How does RAG handle real-time data?"

**Iteration 1:**
- Retrieve: General RAG papers
- Critique: "Missing real-time/streaming aspects"
- Refine: "RAG streaming data real-time updates"

**Iteration 2:**
- Retrieve: Better documents about streaming
- Critique: "Sufficient, covers real-time patterns"
- Answer: [Generate with confidence]

### Implementation
Add reflection loop to chat service:

```python
# services/chat/app/service.py
def self_rag_loop(query, max_iterations=3):
    for i in range(max_iterations):
        # Retrieve
        docs = search_service.search(query)
        
        # Critique
        critique = llm_critique(query, docs)
        
        if critique['sufficient']:
            return generate_answer(query, docs)
        
        # Refine query
        query = critique['refined_query']
    
    # Final attempt
    return generate_answer(query, docs)
```

### Impact
- **Complex handling:** +20%
- **Hallucination:** -15%
- **Confidence:** +25% (quality gate)
- **Use case:** Research-grade answers

### Effort
- **Time:** 8-10 hours
- **Complexity:** High

### Files to modify
- `services/chat/app/service.py` - Add reflection loop
- `services/chat/app/critic.py` - New critique logic
- `frontend/src/components/chat/` - Show iteration progress

---

## Implementation Priority

### Recommended Order

1. **Metadata Filtering UI** (2 hours)
   - Quick win, immediate value
   - Low risk, high user satisfaction

2. **Query Decomposition** (4-6 hours)
   - High impact on complex queries
   - Teaches advanced RAG concepts

3. **Self-RAG** (8-10 hours)
   - Cutting edge, research-grade
   - Wow factor for demonstrations

### Total Time: ~14-18 hours

---

## Dependencies

All features build on existing infrastructure:
- ✅ Prompt Classifier (intent detection)
- ✅ Prompt Enhancement (query rewriting)
- ✅ Model Router (complexity routing)
- ✅ Vector DB with metadata
- ✅ Multi-model Ollama setup

---

## References

- **Query Decomposition:** [Multi-Query RAG (LangChain)](https://blog.langchain.dev/query-construction/)
- **Self-RAG:** [Self-RAG Paper](https://arxiv.org/abs/2310.11511)
- **Metadata Filtering:** ChromaDB `where` clause docs

