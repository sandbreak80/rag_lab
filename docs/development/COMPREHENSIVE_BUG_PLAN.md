# 🔍 Comprehensive Bug Assessment & Plan

## 📋 Bug List Analysis (24 issues identified)

### Category 1: UI Display Issues (8)
1. Model name in header not updating
2. Metrics tab shows placeholders
3. "All Folders" icon/link - unclear purpose
4. Documents tab doesn't show uploaded docs
5. Sources shown twice (in response + below)
6. Additional resources needs own page + expansion
7. Broken link: system architecture in resources
8. Lab guide too short/simple

### Category 2: Missing UI Components (3)
9. Q&A tab missing
10. Feedback tab missing
11. Settings incomplete for lab requirements

### Category 3: Missing Configuration UI (2)
12. Web search config missing
13. Reranker config incomplete

### Category 4: Functionality Validation (10)
14. Knowledge graph functionality
15. ChromaDB functionality
16. Reranker functionality
17. Web search functionality
18. Hybrid fusion functionality
19. Keyword search (BM25) functionality
20. Query expansion functionality
21. Entity extraction functionality
22. Agentic chunking functionality
23. Document ingestion pipeline
24. Vector embeddings functionality

---

## 🎯 Execution Plan

### PHASE 1: Backend Validation (30 min)
**Goal:** Confirm what's actually working vs broken

#### Tests to Write:
```python
# tests/test_backend_services.py
- test_chromadb_connection()
- test_chromadb_query()
- test_search_service_health()
- test_search_service_vector_search()
- test_search_service_bm25()
- test_search_service_hybrid()
- test_knowledge_graph_service()
- test_reranker_service()
- test_entity_extraction_service()
- test_web_search_service()
- test_query_expansion()
- test_ingest_pipeline()
```

**Output:** `BACKEND_VALIDATION_REPORT.md`

---

### PHASE 2: Critical Functionality Fixes (1 hour)
**Priority:** Fix broken backend integrations first

#### 2A: Web Search (15 min)
- [ ] Test web search service connectivity
- [ ] Validate SearXNG integration
- [ ] Add web search config to settings (docs count, pages per doc)
- [ ] Test end-to-end web search in chat

#### 2B: Reranker (15 min)
- [ ] Test reranker service
- [ ] Add reranker config to settings (top-k selection)
- [ ] Validate reranking in search results

#### 2C: Knowledge Graph (15 min)
- [ ] Test knowledge graph queries
- [ ] Validate entity extraction integration
- [ ] Test graph-enhanced search

#### 2D: Hybrid Search (15 min)
- [ ] Validate BM25 index exists
- [ ] Test keyword search
- [ ] Test hybrid fusion
- [ ] Verify alpha parameter works

---

### PHASE 3: UI Component Fixes (1 hour)

#### 3A: New Tabs (30 min)
- [ ] **Q&A Tab**: FAQ about RAG system, how to use lab
- [ ] **Feedback Tab**: Survey questions, rating system, comments
- [ ] Move "Additional Resources" to Resources tab

#### 3B: Settings Expansion (15 min)
Based on lab requirements, add:
- [ ] Agentic chunking toggle
- [ ] Entity extraction toggle
- [ ] Chunk size slider
- [ ] Overlap size slider
- [ ] Embedding model selector
- [ ] Web search: docs slider, pages slider
- [ ] Reranker: rerank top-k slider
- [ ] Knowledge graph: max hops slider

#### 3C: Header & Navigation (15 min)
- [ ] Fix model name display (bind to settings change)
- [ ] Remove or explain "All Folders" (or make functional)
- [ ] Add clear navigation labels

---

### PHASE 4: Content Expansion (1 hour)

#### 4A: Lab Guide Enhancement (45 min)
Reference existing docs:
- `docs/lab/AI_FUNDAMENTALS.md`
- `docs/lab/AI_FUNDAMENTALS_ADDENDUM.md`
- `docs/lab/MODEL_COMPARISON_EXERCISE.md`
- `docs/lab/LAB_GUIDE.md`

Expand to **15+ sections**:
1. Introduction & Lab Overview
2. What is RAG?
3. Vector Embeddings Explained
4. Semantic Search vs Keyword Search
5. Chunking Strategies
6. Agentic Chunking Deep Dive
7. Hybrid Search (Vector + BM25)
8. Query Expansion
9. Knowledge Graphs for RAG
10. LLM Re-ranking
11. Evaluation Metrics (Precision, Recall, MRR, NDCG)
12. Model Comparison Exercise
13. Production Optimization
14. Enterprise Value Propositions
15. Splunk Observability Integration

#### 4B: Additional Resources Page (15 min)
Create dedicated Resources tab with:
- Fix system architecture link
- Add Splunk blog posts
- Add external RAG resources
- Add model documentation links
- Add research papers

---

### PHASE 5: Display Fixes (30 min)

#### 5A: Documents Tab (15 min)
- [ ] Show list of uploaded documents
- [ ] Filter out system/lab docs
- [ ] Show: filename, date, chunks, status
- [ ] Add delete functionality

#### 5B: Metrics Tab (10 min)
- [ ] Replace placeholders with real metrics
- [ ] Pull from `/api/stats` endpoint
- [ ] Show: latency, token count, cost estimates
- [ ] Add historical graph

#### 5C: Chat Interface (5 min)
- [ ] Remove duplicate sources from response
- [ ] Keep only sources section below response

---

### PHASE 6: Comprehensive Testing (1 hour)

#### 6A: Unit Tests (20 min)
```bash
tests/unit/
  test_search_service.py
  test_ingest_service.py
  test_knowledge_graph_service.py
  test_reranker_service.py
  test_web_search_service.py
  test_entity_extraction.py
```

#### 6B: Integration Tests (20 min)
```bash
tests/integration/
  test_end_to_end_search.py
  test_upload_and_query.py
  test_hybrid_search_flow.py
  test_web_search_integration.py
  test_knowledge_graph_integration.py
```

#### 6C: Playwright Tests (20 min)
```bash
tests/playwright/
  test_all_tabs.py
  test_settings_changes.py
  test_upload_workflow.py
  test_query_workflow.py
  test_feedback_submission.py
```

---

## 📊 Revised Bug Priority

### 🔥 CRITICAL (Fix First):
1. Validate all backend services (tests)
2. Web search not working
3. Reranker functionality validation
4. Knowledge graph validation
5. Hybrid search validation

### ⚠️ HIGH (Fix Second):
6. Lab guide expansion (use existing docs!)
7. Settings expansion
8. Q&A tab
9. Feedback tab
10. Documents tab showing files

### 📝 MEDIUM (Fix Third):
11. Metrics tab real data
12. Additional resources page
13. Model name in header
14. Sources duplication
15. Web search config UI
16. Reranker config UI

### 🎨 LOW (Fix Last):
17. "All Folders" clarification
18. Fix broken architecture link
19. UI polish

---

## 🧪 Testing Strategy

### Test Order:
1. **Backend Services** (validate functionality)
2. **Integration** (validate service communication)
3. **UI Functionality** (validate user workflows)
4. **End-to-End** (validate complete scenarios)

### Test Types:
- **Unit**: Each service independently
- **Integration**: Service-to-service (no mocks)
- **Playwright**: User interactions
- **E2E**: Full workflows (upload → query → feedback)

---

## 📦 Deliverables

1. **Test Suite**
   - 20+ unit tests
   - 10+ integration tests
   - 10+ Playwright tests

2. **Bug Fixes**
   - All 24 issues addressed
   - Validated with tests

3. **Documentation**
   - Test results report
   - Backend validation report
   - Updated lab guide (15+ sections)
   - Updated additional resources

4. **Enhanced UI**
   - 7 tabs total (Chat, Documents, Q&A, Settings, Metrics, Lab, Resources, Feedback)
   - Expanded settings (15+ controls)
   - Real metrics display
   - Working document list

---

## ⏱️ Time Estimate
- **Assessment & Planning**: 15 min (done)
- **Backend Validation**: 30 min
- **Critical Fixes**: 1 hour
- **UI Components**: 1 hour
- **Content**: 1 hour
- **Testing**: 1 hour
- **Bug Fixes from Tests**: 30 min
- **Final Validation**: 30 min

**Total**: ~5.5 hours of focused work

---

## 🚀 Ready to Execute

**Start with:** Backend validation tests
**Reason:** Need to know what's working before fixing UI
**Next:** Fix critical backend integrations
**Then:** Expand UI and content
**Finally:** Comprehensive testing

This approach ensures:
- ✅ We fix real problems, not assumed ones
- ✅ Tests validate fixes
- ✅ No guessing about functionality
- ✅ Systematic, reproducible process

**Ready to begin Phase 1: Backend Validation?**

