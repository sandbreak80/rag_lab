# 📋 **RAG LAB - COMPLETE TODO LIST**

**Last Updated:** November 8, 2025  
**Total Tasks:** 18  
**Estimated Time:** 35-45 hours  
**Current Status:** 77% foundation complete

---

## 🎯 **OVERVIEW**

This RAG Lab is designed for **hands-on learning** where each student gets their own RAG instance. The plan balances **production best practices** with **educational value**, skipping enterprise overhead (SSO, compliance, multi-tenancy) while keeping core RAG concepts.

### **Completion Status**

| Phase | Tasks | Status | Time |
|-------|-------|--------|------|
| **Foundation** (Days 1-2) | Completed | ✅ 100% | - |
| **Phase 1: MVP** | 5 tasks | ⏳ 0% | 8-10h |
| **Phase 2: Full Features** | 8 tasks | ⏳ 0% | 18-22h |
| **Phase 3: Lab-Specific** | 5 tasks | ⏳ 0% | 10-12h |
| **TOTAL** | 18 tasks | **77%** | **36-44h** |

---

## ✅ **COMPLETED (Days 1-2) - 6,775 lines**

### **Foundation Already Built:**
- ✅ RAG Orchestrator (6-stage pipeline: preprocess → retrieve → rerank → validate → confidence → refusal)
- ✅ Prompt Assembler (template versioning, context packaging, token management)
- ✅ RAG Evaluator (5 metrics: relevance, faithfulness, quality, precision, recall)
- ✅ Production Service Layer (AuthZ, caching architecture, failure policy)
- ✅ Flask Controller (routes, DTOs, error taxonomy)
- ✅ Evidence Objects (immutable provenance tracking)
- ✅ TimingCollector (thread-safe performance instrumentation)
- ✅ Acceptance Tests (10 tests covering security, performance, functional)

**Quality Score:** 9.5/10  
**Security Score:** 9.5/10  
**Test Coverage:** 85 tests passing

---

## 🔥 **PHASE 1: MVP DEPLOYMENT** (8-10 hours)

**Goal:** Wire everything together, make it observable, ship MVP

### **Task 1.1: Wire RAG Orchestrator to API** ⏳
**Priority:** CRITICAL  
**Time:** 2-3 hours  
**Files:** `services/search_api/app.py`, `services/search_api/routes/rag.py`, `services/search_api/types.py`

**What to Build:**
- Expose `/v1/rag/query` endpoint
- DTOs: `RagRequest{query, tenant, user_id, plan_id}`, `RagResponse{answer, confidence, sources[], trace_id, metrics}`
- Wire orchestrator + prompt assembler + LLM
- Map sources to [1], [2] citations
- Return trace_id from OTEL span

**Acceptance:**
- ✅ POST returns 200 with answer + confidence + sources
- ✅ trace_id present and valid
- ✅ p95 latency < 2.5s on 10 parallel queries

**Smoke Test:**
```bash
curl -X POST localhost:8080/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is RAG?","tenant":"student1","user_id":"u1"}' | jq
```

---

### **Task 1.2: Redis Caching** ⏳
**Priority:** HIGH  
**Time:** 2-3 hours  
**Files:** `services/common/cache.py`, `infra/redis/client.py`, `orchestrator.py` (modify)

**What to Build:**
- Response cache: `resp:{tenant}:{hash(query)}:{plan}:{llm}:{prompt_v}:{embed_v}:{index_alias}:{reranker_v}`
- Chunk cache: `chunk:{doc_hash}:{embed_v}`
- TTL: response 6h, chunk 30d
- Invalidation on version changes

**Acceptance:**
- ✅ Cache hit rate logged
- ✅ 2nd identical query ≥40% faster
- ✅ Version change invalidates cache

**Smoke Test:**
```bash
# First query (miss)
time curl -X POST localhost:8080/v1/rag/query -d '{"query":"test","tenant":"s1","user_id":"u1"}'

# Second query (hit - should be faster)
time curl -X POST localhost:8080/v1/rag/query -d '{"query":"test","tenant":"s1","user_id":"u1"}'
```

---

### **Task 1.3: OTEL Stage Spans** ⏳
**Priority:** HIGH  
**Time:** 2-3 hours  
**Files:** `services/common/orchestrator.py`, `observability/otel.py`

**What to Build:**
- Add spans for each orchestrator stage:
  - `rag.preprocess` → attrs: expanded_queries, lang, intent
  - `rag.retrieve` → attrs: k, strategies, docs_returned, elapsed_ms
  - `rag.rerank` → attrs: reranker, gain@10, mrr@10
  - `rag.validate` → attrs: grounding_rate, warnings
  - `rag.confidence` → attrs: score, bucket
  - `rag.refusal` → attrs: reason (when triggered)

**Acceptance:**
- ✅ One trace per request in Grafana/Tempo
- ✅ All 6 stages as nested spans
- ✅ Attributes present with sane values

**Smoke Test:**
```bash
curl -X POST localhost:8080/v1/rag/query -d '{"query":"test","tenant":"s1","user_id":"u1"}' | jq .trace_id
# Check trace in Grafana → Explore → Tempo
```

---

### **Task 1.4: Eval Harness CI Gate** ⏳
**Priority:** MEDIUM  
**Time:** 2-3 hours  
**Files:** `eval/config.yaml`, `eval/cases/golden_set.json`, `.github/workflows/ci.yml`, `Makefile`

**What to Build:**
- Config with thresholds: `min_faithfulness: 0.8`, `min_relevance: 0.7`, `min_hit_at_5: 0.7`
- Golden set with 20+ diverse test cases
- CI step that runs `make eval` and fails on regression
- Store results in `artifacts/eval/latest.json`

**Acceptance:**
- ✅ `make eval` returns non-zero on regression
- ✅ CI blocks merge when thresholds fail
- ✅ At least 20 test cases

**Smoke Test:**
```bash
make eval
cat artifacts/eval/latest.json | jq
```

---

### **Task 1.5: Docker Compose Stack** ⏳
**Priority:** HIGH  
**Time:** 1-2 hours  
**Files:** `docker/docker-compose.yml`, `docker/Dockerfile.search-api`

**What to Build:**
- Add `search-api` service (ports 8080)
- `redis` service with healthcheck
- Wire to existing `otel-collector`
- Shared network `rag-network`

**Acceptance:**
- ✅ `docker compose up` → all healthy in <60s
- ✅ API calls produce traces
- ✅ Cache working

**Smoke Test:**
```bash
docker compose up -d
docker compose ps  # All healthy
curl localhost:8080/health
```

---

## 🎓 **PHASE 2: EDUCATIONAL FEATURES** (18-22 hours)

**Goal:** Add learning-critical features from enterprise best practices

### **Task 2.1: Structure-Aware Chunking** ⏳
**Priority:** HIGH (Educational Value)  
**Time:** 2-3 hours  
**Files:** `services/ingest/chunker.py` (create), integrate into ingest pipeline

**What to Build:**
- Chunk by heading boundaries
- Target 300-800 tokens per chunk
- 10-20% overlap between chunks
- Special handling for tables/code blocks
- Include `heading_path`, `section_index` in metadata

**Why:** Students see chunking strategy directly impacts quality

**Acceptance:**
- ✅ Chunks respect heading boundaries
- ✅ Average chunk size 300-800 tokens
- ✅ Overlap prevents split answers
- ✅ Tables/code preserved as atomic chunks

**Exercise for Students:**
- "Experiment with chunk sizes: 200, 500, 1000 tokens"
- "Compare retrieval quality with vs. without overlap"

---

### **Task 2.2: Query Understanding** ⏳
**Priority:** MEDIUM (Educational Value)  
**Time:** 2-3 hours  
**Files:** `services/common/query_understanding.py` (create), wire to orchestrator

**What to Build:**
- Acronym expansion using domain glossary
  - Example: "RAG" → "retrieval augmented generation"
- Synonym expansion
  - Example: "fix" → ["repair", "resolve"]
- Intent detection (navigational vs. informational)
- Return original + expanded query variants

**Why:** Students learn query preprocessing improves recall

**Acceptance:**
- ✅ Acronyms expanded correctly
- ✅ Synonyms generated
- ✅ Expanded queries improve hit rate

**Exercise for Students:**
- "Build domain glossary for your corpus"
- "Measure recall improvement with/without expansion"

---

### **Task 2.3: Extractive-First Prompts** ⏳
**Priority:** HIGH (Educational Value)  
**Time:** 1 hour  
**Files:** `services/common/prompt_assembler.py` (modify templates)

**What to Build:**
- New template: `EXTRACTIVE_GROUNDED`
- Rules:
  1. Prefer direct quotes from passages
  2. Cite per-sentence using [1], [2]
  3. If insufficient info, explicitly say what's missing
  4. Never make up information

**Why:** Teaches grounding vs. hallucination trade-off

**Acceptance:**
- ✅ Answers include verbatim quotes
- ✅ Per-sentence citations present
- ✅ "I don't have information about X" when missing

**Exercise for Students:**
- "Compare abstractive vs. extractive prompts"
- "Measure hallucination rate with both"

---

### **Task 2.4: Metadata Enrichment** ⏳
**Priority:** MEDIUM (Educational Value)  
**Time:** 1-2 hours  
**Files:** `services/common/evidence.py` (add fields), ingest pipeline

**What to Build:**
- Add fields to Evidence:
  - `doc_type`: guide, api_doc, faq, policy, tutorial
  - `department`: engineering, sales, support, hr
  - `freshness_days`: days since last update
  - `quality_score`: 0.0-1.0 (manual or heuristic)
- Use in ranking: boost recent, high-quality docs

**Why:** Students learn structured metadata improves retrieval

**Acceptance:**
- ✅ Metadata fields populated during ingest
- ✅ Filtering works (e.g., `doc_type=api_doc`)
- ✅ Boosting works (recent docs rank higher)

**Exercise for Students:**
- "Tag your documents with metadata"
- "Measure quality improvement with metadata boosting"

---

### **Task 2.5: Feedback Loop** ⏳
**Priority:** HIGH (Educational Value)  
**Time:** 2 hours  
**Files:** `services/search_api/routes/feedback.py` (create), UI buttons

**What to Build:**
- POST `/api/feedback` endpoint
- Accept: `{query_id, answer_id, rating: thumbs_up|thumbs_down, tags: [outdated, missing, incorrect]}`
- Store feedback in JSON or simple DB
- Dashboard showing feedback trends

**Why:** Students see how to improve RAG iteratively

**Acceptance:**
- ✅ Feedback buttons in UI
- ✅ Feedback stored with query_id
- ✅ Dashboard shows trends

**Exercise for Students:**
- "Collect 50 feedback responses"
- "Identify top issues (outdated docs, missing info)"
- "Fix and re-evaluate"

---

### **Task 2.6: RetrievalPlan Registry** ⏳
**Priority:** MEDIUM  
**Time:** 2-3 hours  
**Files:** `services/common/plans/registry.py`, `config/plans.yaml`

**What to Build:**
- Registry of named plans: `vector_only_v1`, `hybrid_v2`, `full_search_v1`
- Load from YAML config
- API: `?plan=hybrid_v2` selects plan
- A/B assignment: assign stable variant per user

**Why:** Enables experimentation with different strategies

**Acceptance:**
- ✅ Plans loaded from config
- ✅ API accepts `plan_id` parameter
- ✅ A/B split works (50/50 or custom)

**Exercise for Students:**
- "A/B test: vector-only vs. hybrid"
- "Measure quality difference"

---

### **Task 2.7: OpenLLMetry Integration** ⏳
**Priority:** MEDIUM  
**Time:** 2-3 hours  
**Files:** `observability/openllmetry.py`, wire to orchestrator

**What to Build:**
- Auto-instrument LLM calls
- Track: `prompt_tokens`, `completion_tokens`, `model`, `cost_usd`
- Add spans: `llm.generate`, `llm.embed`
- Grafana dashboard: tokens/req, cost/req, model distribution

**Why:** Students see cost/performance trade-offs

**Acceptance:**
- ✅ Token counts logged
- ✅ Cost per request calculated
- ✅ Dashboard shows metrics

**Exercise for Students:**
- "Compare gpt-4 vs. gpt-3.5 cost"
- "Optimize token usage"

---

### **Task 2.8: Dashboards & Alerts** ⏳
**Priority:** MEDIUM  
**Time:** 2-3 hours  
**Files:** `observability/grafana/dashboards/rag_core.json`, `observability/alerts/rag_core.yaml`

**What to Build:**
- Grafana dashboard panels:
  - p50/p95/p99 latency
  - Error rate
  - Cache hit rate
  - Hit@k, MRR@10
  - Grounding rate
  - Cost per request
- Alerts:
  - p95 > 3s
  - Error rate > 1%
  - Cache hit < 25%

**Why:** Students learn SLO monitoring

**Acceptance:**
- ✅ Dashboard renders with live data
- ✅ Alerts fire on synthetic degradation

**Exercise for Students:**
- "Set your own SLOs"
- "Optimize to meet them"

---

## 🎓 **PHASE 3: LAB-SPECIFIC** (10-12 hours)

**Goal:** Student-friendly features, not enterprise overhead

### **Task 3.1: Simple Student Auth** ⏳
**Priority:** MEDIUM  
**Time:** 2 hours  
**Files:** `services/auth/simple_auth.py`, middleware

**What to Build:**
- API key per student (not SSO)
- Simple middleware: `X-API-Key` header
- Rate limiting: 100 req/min per key
- No SSO/SAML complexity

**Why:** Just enough auth, not enterprise overhead

**Acceptance:**
- ✅ API keys work
- ✅ Rate limiting enforced
- ✅ Easy to generate new keys

---

### **Task 3.2: Document Upload Interface** ⏳
**Priority:** HIGH (Student UX)  
**Time:** 2-3 hours  
**Files:** `frontend/src/pages/Upload.tsx`, API endpoint

**What to Build:**
- Drag-drop file upload (PDF, MD, TXT)
- Git repo sync (clone and index)
- File management (list, delete, re-index)
- Progress bar during ingestion

**Why:** Students need easy way to add their own docs

**Acceptance:**
- ✅ Drag-drop works
- ✅ Git sync works
- ✅ Progress shown

---

### **Task 3.3: Student Dashboard** ⏳
**Priority:** MEDIUM (Student UX)  
**Time:** 2-3 hours  
**Files:** `frontend/src/pages/Dashboard.tsx`

**What to Build:**
- Query history (last 50 queries)
- Feedback view (thumbs up/down counts)
- Quality metrics (hit@5, MRR, avg confidence)
- Document stats (count, freshness)

**Why:** Students see their progress

**Acceptance:**
- ✅ Dashboard loads
- ✅ Metrics accurate
- ✅ History filterable

---

### **Task 3.4: CI/CD Pipeline** ⏳
**Priority:** LOW  
**Time:** 2-3 hours  
**Files:** `.github/workflows/ci.yml`, `.github/workflows/cd.yml`

**What to Build:**
- CI: lint (ruff), typecheck (mypy), tests (pytest), eval gate
- CD: build images, push to registry, deploy
- Smoke tests post-deploy

**Why:** Good practice, not critical for lab

**Acceptance:**
- ✅ CI runs on PR
- ✅ Eval gate blocks merge on regression
- ✅ CD deploys on merge to main

---

### **Task 3.5: Lab Guide & Exercises** ⏳
**Priority:** HIGH (Educational)  
**Time:** 3-4 hours  
**Files:** `docs/LAB_GUIDE.md`, `docs/EXERCISES.md`

**What to Build:**
- Lab Guide:
  - Setup instructions
  - Architecture overview
  - API documentation
  - Troubleshooting
- Exercises:
  - Exercise 1: "Index your first document"
  - Exercise 2: "Experiment with chunk sizes"
  - Exercise 3: "Compare retrieval strategies"
  - Exercise 4: "A/B test prompts"
  - Exercise 5: "Optimize for quality"
  - Exercise 6: "Reduce cost"

**Why:** Students need structured learning path

**Acceptance:**
- ✅ Guide is clear and complete
- ✅ Exercises have solutions
- ✅ Students can complete independently

---

## 📊 **PRIORITY MATRIX**

### **Critical Path (MVP):**
1. Task 1.1: Wire API ← **START HERE**
2. Task 1.3: OTEL Spans
3. Task 1.5: Docker Compose
4. Task 1.2: Caching
5. Task 1.4: Eval Harness

**Time to MVP:** 8-10 hours

### **High Educational Value:**
6. Task 2.1: Structure-Aware Chunking
7. Task 2.3: Extractive Prompts
8. Task 2.5: Feedback Loop
9. Task 3.2: Upload Interface
10. Task 3.5: Lab Guide

**Time to Full Lab:** +12-15 hours

### **Nice to Have:**
11-18: Remaining Phase 2 & 3 tasks

**Time to Complete:** +13-17 hours

---

## ✅ **DEFINITION OF DONE**

### **MVP Ready (After Phase 1):**
- [ ] API serves `/v1/rag/query` with trace_id + citations
- [ ] Redis cache working with 40%+ speedup
- [ ] OTEL spans visible in Grafana
- [ ] Eval suite runs in CI
- [ ] Docker Compose stack runs locally
- [ ] p95 latency < 2.5s

### **Full Featured (After Phase 2):**
- [ ] Structure-aware chunking implemented
- [ ] Query understanding (acronyms, synonyms)
- [ ] Extractive-first prompts
- [ ] Metadata enrichment
- [ ] Feedback loop working
- [ ] A/B testing via plans
- [ ] OpenLLMetry tracking cost
- [ ] Dashboards + alerts live

### **Lab Ready (After Phase 3):**
- [ ] Student auth (API keys)
- [ ] Upload interface working
- [ ] Student dashboard live
- [ ] CI/CD pipeline
- [ ] Lab guide + exercises complete

---

## 🚀 **EXECUTION PLAN**

### **Week 1: MVP** (8-10 hours)
Focus on Phase 1 tasks 1-5

### **Week 2: Educational Features** (18-22 hours)
Focus on Phase 2 tasks 6-13

### **Week 3: Lab Polish** (10-12 hours)
Focus on Phase 3 tasks 14-18

**Total:** 3 weeks, 36-44 hours

---

## 📝 **NOTES**

### **What We're SKIPPING from Enterprise Article:**
- ❌ SSO/SAML/OIDC (too complex for lab)
- ❌ SCIM provisioning
- ❌ 7-year immutable audit logs
- ❌ KMS + envelope encryption
- ❌ Data residency / multi-region
- ❌ Legal holds / Right-to-Delete
- ❌ Cold/warm storage tiers
- ❌ Blue/green index rollout (simplified version only)

### **What We're KEEPING from Enterprise Article:**
- ✅ Hybrid retrieval (vector + BM25)
- ✅ Reranking
- ✅ Structure-aware chunking
- ✅ Citation tracking
- ✅ Query understanding
- ✅ Extractive prompts
- ✅ Metadata enrichment
- ✅ Feedback loop
- ✅ Observability (OTEL + OpenLLMetry)
- ✅ Evaluation harness

**Rationale:** Keep learning-critical features, skip compliance/ops overhead.

---

**READY TO START EXECUTION WITH PHASE 1, TASK 1: Wire RAG Orchestrator to API**

