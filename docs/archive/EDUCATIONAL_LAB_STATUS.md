# 🎓 Educational RAG Lab - Current Status

**Last Updated:** November 1, 2025
**Status:** Phase 1-3 Complete ✅

## 🎯 Project Vision

Transform the RAG system into an interactive educational lab where students can:
- Experiment with different RAG configurations
- See real-time performance metrics
- Understand the tradeoffs between quality, speed, and resources
- Learn by doing with immediate visual feedback

---

## ✅ Completed Features

### Phase 1: Backend APIs (COMPLETE)
**Endpoints:**
- ✅ `/search_with_config` - Configurable search with detailed metrics
  - Returns per-component timing (expansion, vector, BM25, fusion, graph, reranking)
  - Percentage breakdown of latency
  - Result counts per method
- ✅ `/api/evaluate` - RAG evaluation on test dataset
  - Calculates Precision, Recall, MRR, NDCG
  - Uses 20-question test set
  - Per-difficulty breakdowns
- ✅ `/api/presets` - Configuration presets
  - Returns 6 optimized presets with expected metrics

**Configuration Presets:**
1. **Minimal** (Baseline) - Vector search only, ~40ms
2. **Fast** - Query expansion + vector, ~50ms
3. **Balanced** ⭐ - Hybrid search, ~120ms (RECOMMENDED)
4. **Quality** - All except reranking, ~250ms
5. **Maximum** - Everything ON, ~2500ms
6. **Production** 🏆 - Optimized for real-world, ~300ms (TAKE-HOME)

### Phase 2: Settings Panel (COMPLETE)
**UI Components:**
- ✅ Collapsible sidebar (320px, slides from left)
- ✅ 6 quick preset buttons
- ✅ RAG Pipeline Toggles:
  - Query Expansion (+5% recall, +10ms)
  - BM25 Keyword Search (+15% recall, +20ms)
  - Hybrid Fusion (+20% recall, +30ms)
  - Knowledge Graph (+5% recall, +50ms)
  - LLM Re-ranking (+10% precision, +2000ms)
- ✅ Search Parameters: Top-K slider (1-20)
- ✅ LLM Settings:
  - Model selection (1B/3B/8B)
  - Temperature (0-1)
  - Max Tokens (100-2000)
  - Context Window (1000-8000)
- ✅ Expected performance metrics preview
- ✅ Config persistence (localStorage)
- ✅ Beautiful glassmorphic design
- ✅ Mobile responsive

### Phase 3: Metrics Dashboard (COMPLETE)
**Display Components:**
- ✅ 4 Key Metrics Cards:
  - Total Latency (ms)
  - Results Found (count)
  - Search Method (hybrid/vector)
  - Precision (estimated %)
- ✅ Detailed Latency Breakdown:
  - Query Expansion (time + % of total)
  - Vector Search (time + %)
  - BM25 Search (time + %)
  - Fusion (time + %)
  - Knowledge Graph (time + %)
  - LLM Re-ranking (time + %)
- ✅ Component Status Indicators:
  - Green dot = Active
  - Gray dot = Inactive
  - Real-time updates
- ✅ Collapsible detailed view
- ✅ Smooth animations
- ✅ Real-time updates after each query

**Integration:**
- ✅ Chat function calls `/search_with_config` before `/api/chat`
- ✅ Captures detailed metrics automatically
- ✅ Updates dashboard in real-time
- ✅ Dashboard hidden until first query

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      WEB UI (Flask)                          │
│  - Settings Panel (left)  - Chat Interface (center)         │
│  - Metrics Dashboard (top) - Lab Guide (right) [planned]    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─ /api/presets ────────────┐
                              ├─ /api/evaluate ───────────┤
                              └─ /api/chat ───────────────┤
                                        │                  │
                    ┌───────────────────┘                  │
                    │                                      │
         ┌──────────▼──────────┐              ┌───────────▼─────────┐
         │  Search Service     │              │   Chat Service      │
         │  (Configurable)     │              │   (Ollama)          │
         │                     │              └─────────────────────┘
         │ /search_with_config │
         │ - Returns metrics   │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼─────┐      ┌───────▼────────┐
    │ Vector   │      │ BM25           │
    │ Search   │      │ Keyword        │
    └──────────┘      └────────────────┘
         │                     │
         └──────────┬──────────┘
                    │
           Reciprocal Rank Fusion
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼──────┐      ┌──────▼─────┐
    │ Knowledge │      │ LLM        │
    │ Graph     │      │ Reranker   │
    └───────────┘      └────────────┘
```

---

## 📊 Test Results

**Services Status:**
- ✅ Web UI: http://localhost:5555
- ✅ Search Service: http://localhost:8002
- ✅ Vector DB: http://localhost:8005
- ✅ Ingest Service: http://localhost:8001
- ✅ Ollama: http://localhost:11434

**API Tests:**
- ✅ `/api/presets` returns 6 configurations
- ✅ `/search_with_config` returns detailed metrics
- ✅ Settings panel loads and saves config
- ✅ Metrics dashboard updates in real-time

---

## 🚀 Next Steps

### Phase 4: Comparison Mode (Pending)
- Side-by-side comparison of two configurations
- A/B testing interface
- Diff highlighting for metrics

### Phase 5: Lab Guide (Pending)
- Interactive tutorial panel (right side)
- Progressive content as features are used
- Checkboxes for completion tracking
- Tips and best practices

### Phase 6: Web Search Integration (Pending)
- SearXNG container deployment
- Web search toggle in settings
- Display # of web docs and pages returned
- JSON API integration

---

## 🎓 Educational Value

**Students Learn:**
1. **RAG Architecture** - See all components in action
2. **Performance Tradeoffs** - Quality vs Speed vs Cost
3. **Configuration Impact** - Real metrics for each feature
4. **Best Practices** - Production-ready presets
5. **Hands-on Experience** - Interactive experimentation

**Metrics Taught:**
- Latency (ms) - Response time
- Precision (%) - Relevant results ratio
- Recall (%) - Coverage of all relevant docs
- MRR - Mean Reciprocal Rank
- NDCG - Normalized Discounted Cumulative Gain

---

## 📝 Implementation Notes

**Technologies:**
- Backend: Python, Flask
- Frontend: Vanilla JS, HTML5, CSS3
- Vector DB: ChromaDB
- LLM: Ollama (Llama 3.2)
- Search: BM25 + Vector Hybrid
- Containers: Docker Compose

**Design Philosophy:**
- Single-page application
- No heavy frameworks (educational transparency)
- Beautiful, modern UI (glassmorphism)
- Mobile responsive
- Real-time feedback
- Educational tooltips and badges

**Performance:**
- Minimal preset: ~40ms
- Fast preset: ~60ms
- Balanced preset: ~120ms
- Quality preset: ~250ms
- Maximum preset: ~2500ms
- Production preset: ~300ms

---

## 🎯 Success Criteria

- [x] Students can change settings and see immediate impact
- [x] Metrics are clear, accurate, and educational
- [x] UI is beautiful and intuitive
- [x] System is performant enough for real-time experimentation
- [ ] Lab guide provides step-by-step learning path
- [ ] Web search integration shows external data retrieval
- [ ] Comparison mode enables A/B testing

---

## 💡 Future Enhancements

1. **Advanced Evaluation Metrics**
   - Faithfulness scoring
   - Answer relevance
   - Hallucination detection

2. **Cost Tracking**
   - Token usage
   - API calls
   - Compute time

3. **Batch Testing**
   - Run full test suite
   - Generate reports
   - Performance graphs

4. **Export/Share**
   - Save configurations
   - Export results
   - Share with classmates

---

**Built with ❤️ for education**

