# Phase 1: Parallel Retrieval Implementation

**Sprint:** Performance + Retrieval Quality  
**Date:** 2025-11-12  
**Status:** ✅ **IMPLEMENTATION COMPLETE** (Pending full-stack validation)

---

## 🎯 **Objective**

Reduce RAG response latency by parallelizing vector search and web search operations using `asyncio.gather()`.

**Target:** Reduce retrieval time from sequential (vector_ms + web_ms) to parallel (max(vector_ms, web_ms))

---

## ✅ **Implementation Summary**

### **Code Changes**

**File:** `services/api/routes/rag.py`

**Before (Sequential):**
```python
# Vector search (blocks)
vector_results, vector_stats = await vector.search(...)  # ~2-4s
# Web search (blocks, waits for vector to finish)
web_results = await web.search(...)  # ~1-3s
# Total: vector_ms + web_ms = 3-7s
```

**After (Parallel):**
```python
# Define parallel tasks
async def vector_search_task():
    with tracer.start_as_current_span("retrieve_internal.vector"):
        t_start = time.perf_counter()
        results, stats = await vector.search(...)
        t_end = time.perf_counter()
        return results, stats, int((t_end - t_start) * 1000)

async def web_search_task():
    with tracer.start_as_current_span("retrieve_web.searxng"):
        t_start = time.perf_counter()
        results = await web.search(...)
        t_end = time.perf_counter()
        return results, int((t_end - t_start) * 1000)

# Execute in parallel
import asyncio
(vector_results, vector_stats, vector_ms), (web_results, web_ms) = await asyncio.gather(
    vector_search_task(),
    web_search_task()
)

# Total: max(vector_ms, web_ms) = 2-4s (best case)
```

### **Key Features**

1. ✅ **Concurrent Execution:** Vector and web search run simultaneously
2. ✅ **Individual Timing:** Each search tracks its own duration
3. ✅ **Parallel Timing:** New `retrieve_parallel_ms` metric shows actual wall-clock time
4. ✅ **OpenTelemetry Spans:** Traces show sibling spans (parallel execution)
5. ✅ **Backward Compatible:** All existing metrics preserved

### **Metrics Output**

```json
{
  "metrics": {
    "stage_timings": {
      "vector_ms": 3200,
      "web_ms": 1800,
      "retrieve_parallel_ms": 3250,
      "total_ms": 8500
    }
  }
}
```

**Expected Speedup:**
- Sequential: `vector_ms + web_ms = 3200 + 1800 = 5000ms`
- Parallel: `retrieve_parallel_ms = 3250ms` (max of the two)
- **Speedup:** `5000 / 3250 = 1.54x` (~35% faster)

---

## 🔍 **Observability**

### **Tempo Traces**

Parallel execution will show:
```
rag.query (8500ms)
├─ retrieve_internal.vector (3200ms)  ← Sibling span
└─ retrieve_web.searxng (1800ms)      ← Sibling span (runs concurrently)
```

**Before:** Sequential spans (one after another)  
**After:** Sibling spans (overlapping time ranges)

### **Prometheus Metrics**

New metric added to `stage_timings`:
- `retrieve_parallel_ms`: Actual wall-clock time for parallel retrieval

Existing metrics unchanged:
- `vector_ms`: Time spent in vector search
- `web_ms`: Time spent in web search

---

## 📊 **Expected Performance Impact**

| Scenario | Sequential (ms) | Parallel (ms) | Speedup | Time Saved |
|----------|----------------|---------------|---------|------------|
| **Fast vector, slow web** | 2000 + 3000 = 5000 | 3050 | 1.64x | 1950ms (~2s) |
| **Slow vector, fast web** | 4000 + 1500 = 5500 | 4050 | 1.36x | 1450ms (~1.5s) |
| **Both slow** | 4000 + 3000 = 7000 | 4050 | 1.73x | 2950ms (~3s) |
| **Both fast** | 1500 + 1000 = 2500 | 1550 | 1.61x | 950ms (~1s) |

**Average expected speedup:** **1.5-1.7x** (33-41% faster retrieval)

---

## 🧪 **Validation Plan**

### **Prerequisites**

Full stack must be running:
- ✅ `rag-api-v1` (with parallel retrieval code)
- ✅ `rag-vector-db` (ChromaDB)
- ✅ `rag-searxng` (web search)
- ✅ `rag-ollama` (LLM)
- ✅ `frontend` (Nginx proxy)

### **Test Script**

```bash
# Run 5 test queries
for i in {1..5}; do
  curl -X POST http://localhost:3000/api/v1/rag/query \
    -H "Content-Type: application/json" \
    -d '{"query":"What is machine learning?","user_id":"test","groups":["public"]}' \
    | jq '.metrics.stage_timings'
done
```

### **Success Criteria**

1. ✅ `retrieve_parallel_ms` < `vector_ms + web_ms`
2. ✅ Speedup ≥ 1.3x (30% improvement)
3. ✅ Tempo shows sibling spans for vector + web
4. ✅ No errors or timeouts
5. ✅ API behavior unchanged (same results)

---

## 🚧 **Current Status**

### **✅ Completed**

- [x] Parallel retrieval implementation (`asyncio.gather`)
- [x] Individual timing tracking (vector_ms, web_ms)
- [x] Parallel timing tracking (retrieve_parallel_ms)
- [x] OpenTelemetry span instrumentation
- [x] Code built and deployed to Docker image

### **⏳ Pending**

- [ ] Full stack deployment (Ollama port conflict blocking)
- [ ] Performance validation with real queries
- [ ] Tempo trace verification (sibling spans)
- [ ] Prometheus metrics validation

### **🔧 Infrastructure Issues**

```
Error: ports are not available: exposing port TCP 0.0.0.0:11434 -> 127.0.0.1:0: 
listen tcp 0.0.0.0:11434: bind: address already in use
```

**Resolution:** Requires stopping conflicting Ollama instance or remapping ports.

---

## 📝 **Next Steps**

### **Immediate (Phase 1 Completion)**

1. **Resolve Ollama port conflict**
   - Stop host Ollama: `brew services stop ollama`
   - OR remap port in `docker-compose.yml`

2. **Start full stack**
   ```bash
   docker compose up -d
   docker compose ps  # Verify all services healthy
   ```

3. **Run performance tests**
   ```bash
   python3 test_performance.py
   ```

4. **Verify Tempo traces**
   - Open Grafana: http://localhost:3001
   - Navigate to Tempo datasource
   - Search for `rag.query` traces
   - Confirm sibling spans for vector + web

5. **Document results**
   - Capture actual speedup metrics
   - Screenshot Tempo trace showing parallel execution
   - Update this document with proof artifacts

### **Phase 1.2 (SearxNG Optimization)**

Once parallel retrieval is validated:
- Add timeout to web search (600-1200ms)
- Limit search depth (`num_results=5`)
- Stream results to caller

---

## 🎯 **Success Metrics (To Be Measured)**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **P50 latency reduction** | ≥30% | TBD | ⏳ Pending |
| **P95 latency reduction** | ≥25% | TBD | ⏳ Pending |
| **Parallel speedup** | ≥1.3x | TBD | ⏳ Pending |
| **Error rate** | 0% | TBD | ⏳ Pending |
| **Trace visibility** | Sibling spans | TBD | ⏳ Pending |

---

## 📚 **References**

- **Code:** `services/api/routes/rag.py` (lines 131-173)
- **Test Script:** `test_performance.py`
- **Sprint Plan:** User-provided Phase 1 specification
- **Branch:** `otel`

---

**Implementation Status:** ✅ **COMPLETE**  
**Validation Status:** ⏳ **PENDING FULL STACK**  
**Ready for Merge:** ⚠️ **AFTER VALIDATION**

---

*Last Updated: 2025-11-12 01:22 UTC*

