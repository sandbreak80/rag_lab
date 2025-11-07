# Critical Analysis: Path to World-Class RAG Lab

**Date:** 2025-11-07  
**Status:** 🚨 CRITICAL - Strategic Direction  
**Author:** System Analysis  

---

## Executive Summary

**Current State:** Infrastructure-complete, behaviorally incomplete.  
**Gap:** Demo → Production-grade, auditable, teachable RAG workbench.  
**Core Issue:** The system has all the pieces but lacks **contract enforcement**, **provenance tracking**, and **measurement loops**.

**The Verdict:** "Pretty demo" → needs to become "measurable, auditable RAG workbench."

---

# Part 1: Deep Analysis

## 🎯 What We Built vs What We Need

### ✅ What's Working (Infrastructure Layer)

1. **Service Architecture** - All microservices operational
   - Vector DB, Knowledge Graph, Embedding Service
   - Chat Service, API Gateway, Auth
   - Web Search (SearXNG), Research Agent
   - Reranker, Security Guardrails
   
2. **Monitoring Stack** - Comprehensive observability
   - Prometheus + Grafana dashboards
   - GPU metrics (DCGM Exporter)
   - Container health monitoring
   - System metrics (CPU, Memory, Network)

3. **Feature Toggles** - UI for RAG presets
   - P1-FAST through P5-EXHAUSTIVE
   - Intelligence features (Query Decomposition, Self-RAG)
   - Data source selection

4. **Model Infrastructure**
   - 12 Ollama models (3B → 20B)
   - GPU acceleration working
   - Multiple embedding models

### ❌ What's Missing (Behavioral Layer)

This is the **CRITICAL GAP**. We have infrastructure but lack **behavioral guarantees**.

---

## 🔍 The 12 Failure Modes (Grouped by Theme)

### Theme 1: **CONTRACT ENFORCEMENT** (The Root Cause)
*"System allowed to answer narratively when schemas mandated"*

#### Failures:
- **#1: Planner & Intent Detection** - Ignores contract markers
- **#5: Contract & Artifact Compliance** - Missing all schemas A-G
- **#11: Preset Claims** - README numbers not reproducible

#### Why This Matters:
The system's **value proposition** is inspectability and teachability. Without enforced contracts, it's just a chatbot. Students can't learn "under the hood" if there's no hood to lift.

#### Root Cause:
**No sentinel blocking essay mode.** The LLM is allowed to bypass artifact requirements and just... answer.

---

### Theme 2: **PROVENANCE & AUDITABILITY**
*"Everything labeled RAG, no claim→source mapping"*

#### Failures:
- **#3: Retrieval Quality & Provenance** - Origin lost during merge
- **#4: Evidence Binding** - No per-claim citations
- **#12: Research Agent Integration** - Not visible in logs

#### Why This Matters:
**Hallucination risk** and **unteachability**. If a student asks "where did this come from?", the system can't answer. Claims without citations are worthless in academic/professional settings.

#### Root Cause:
Evidence objects are **mutable** and **not structured**. Provenance (`web`, `rag`, `research_agent`) is dropped during merge/rerank stages.

---

### Theme 3: **POLICY ENFORCEMENT**
*"No hard gates for recency, domains, budgets"*

#### Failures:
- **#2: Routing & Recency Policy** - Temporal asks ignored
- **#9: SLA & Budgets** - Unpredictable latency, no stage timings

#### Why This Matters:
**Wrong answers delivered with confidence.** If a user asks "what changed in MCP in the last 48 hours?" and gets stale docs, the system is **failing its core promise**.

#### Root Cause:
**No policy layer.** Routing is similarity-based only; no numeric thresholds, no recency gates, no SLA watchdog.

---

### Theme 4: **RETRIEVAL QUALITY**
*"Irrelevant domains, duplicates, weak dedup"*

#### Failures:
- **#3: Retrieval Quality** - Asana/Indeed/CNN in results
- Domain contamination from SEO spam

#### Why This Matters:
**Garbage in, garbage out.** Even with perfect synthesis, bad sources = bad answers. Authority matters.

#### Root Cause:
**No domain filtering.** Web search returns everything; no allow/deny lists, no primary source preference.

---

### Theme 5: **VISIBILITY & MEASUREMENT**
*"Can't see decisions, can't measure improvements"*

#### Failures:
- **#7: Knowledge Graph & Agentic Chunking** - No structured logs
- **#10: A/B Mode** - Grader not wired in
- **#11: Preset Claims** - No benchmark corpus

#### Why This Matters:
**Can't improve what you can't measure.** Students can't compare presets if there are no scores. Lab loses its teaching value.

#### Root Cause:
**No measurement loop.** Grader exists but doesn't emit scores. KG/chunking run but don't log decisions.

---

### Theme 6: **ROBUSTNESS**
*"Error paths not handled, failures silent"*

#### Failures:
- **#6: Security Guardrails** - 400 error → silence
- Service failures not surfaced

#### Why This Matters:
**Silent failures are debugging nightmares.** Students can't learn from failures if failures are hidden.

#### Root Cause:
**No fallback/error reporting.** If a service fails, the system just... continues silently or crashes.

---

### Theme 7: **MODEL ROUTING**
*"One model per run, wrong model for wrong task"*

#### Failures:
- **#8: Auto Model Routing** - Not mapping subtasks → model classes

#### Why This Matters:
**SLA breaches or quality drops.** Using 14B for reranking is slow; using 3B for synthesis is low-quality.

#### Root Cause:
**No routing matrix.** Model selection is user-driven, not task-driven.

---

## 💡 Strategic Insights

### Insight 1: Infrastructure vs Behavior
We've been building **horizontally** (more services) when we need to build **vertically** (better contracts, provenance, measurement).

### Insight 2: Demo vs Workbench
A demo can be impressive without being **auditable**. A workbench must be **measurable** and **inspectable**.

### Insight 3: Teaching Value
The lab's unique value is **transparency**. Every RAG system can answer questions; ours should **show its work**.

### Insight 4: Production Readiness
"Production ready" requires **behavioral SLAs**, not just uptime. We need:
- Recency guarantees (temporal claims ≤48h)
- Provenance guarantees (every claim traceable)
- SLA guarantees (90s P95 latency)
- Quality guarantees (graded scores)

---

# Part 2: Strategic Plan

## 🎯 Vision: World-Class RAG Lab

**Definition:** A production-grade, auditable RAG workbench that:
1. **Teaches** - Shows decisions, not just results
2. **Measures** - Quantifies quality improvements
3. **Enforces** - Has behavioral SLAs, not just uptime
4. **Scales** - From laptop (16GB) to AWS GPU instances

---

## 🏗️ Architecture Principles

### Principle 1: **Contract-First**
Every request must specify **required artifacts**. System must emit them or fail with explanation.

### Principle 2: **Immutable Provenance**
Evidence objects set once, never mutated. Every claim traceable to source.

### Principle 3: **Policy-Driven**
Routing decisions based on **numeric thresholds**, not heuristics. Policies visible in logs.

### Principle 4: **Measurement Loop**
Every preset has **measured scores** on a **gold corpus**. A/B comparisons required.

### Principle 5: **Graceful Degradation**
Service failures emit fallback reports. System never goes silent.

---

## 📋 Implementation Priorities

### **Phase 1: Foundations (Weeks 1-2)** 🔴 CRITICAL

#### 1A: Contract Sentinel
**What:** Middleware that blocks essay mode.  
**How:** 
- Parse prompt for contract markers (schemas A-G, "Global Contract")
- If present, **require** artifact emission
- If stage fails, emit stub with `status: "missing"` + Failure Note

**Impact:** Forces system to respect its own contracts.

**Files to Modify:**
- `services/chat-service/app/service.py` - Add contract parser
- `services/api-gateway/app/routes/chat.py` - Add middleware
- New: `services/common/contract_sentinel.py`

**Acceptance Test:**
```bash
# Prompt with contract marker but complex task
curl -X POST /api/ask \
  -d '{"query": "Latest MCP news [GLOBAL CONTRACT REQUIRED]", "preset": "P4-STRONG"}'

# PASS IF: Response includes schemas A-G (even if some are stubs)
# FAIL IF: Response is narrative essay
```

---

#### 1B: Immutable Evidence Object
**What:** Structured evidence with provenance.  
**How:**
```python
@dataclass(frozen=True)
class Evidence:
    origin_tool: Literal["web_search", "rag", "research_agent", "file", "api"]
    url: str
    domain: str
    published_at: Optional[datetime]
    is_primary: bool
    fetched_at: datetime
    content_snippet: str
    metadata: dict
```

- Set in retriever
- Pass through dedup/merge/rerank **unchanged**
- Reference in synthesis with `[#n]` tags

**Impact:** Every claim traceable.

**Files to Modify:**
- New: `services/common/evidence.py`
- `services/vector-db/app/service.py` - Emit Evidence
- `services/web-search/app/service.py` - Emit Evidence
- `services/research-agent/app/service.py` - Emit Evidence
- `services/chat-service/app/service.py` - Preserve Evidence through synthesis

**Acceptance Test:**
```python
# After query with web + RAG sources
evidence_map = response["artifacts"]["schema_c_evidence_map"]

# PASS IF:
# - Each evidence has origin_tool
# - origin_tool preserved from source
# - Claims have [#n] tags linking to evidence
```

---

#### 1C: Recency Gate
**What:** Hard policy for temporal queries.  
**How:**
- Tag subtasks with `requires_recency=true` (e.g., "latest", "recent", "≤48h")
- Router enforces:
  - `max_staleness_hours_news = 48`
  - `min_primary_sources = 2`
  - `min_internal_conf_before_web = 0.75`
- Block finalization if temporal claim lacks recent primary

**Impact:** No more stale answers to "latest" questions.

**Files to Modify:**
- `services/query-decomposition/app/service.py` - Tag temporal subtasks
- `services/model-router/app/service.py` - Add recency policy
- New: `services/common/routing_policy.py`

**Acceptance Test:**
```bash
# Prompt: "Latest MCP changes in last 48 hours"
# PASS IF:
# - Evidence Map has ≥1 URL with published_at ≤ 48h
# - Sources are primary (github.com, modelcontextprotocol.io)
# FAIL IF: Stale docs or secondary sources only
```

---

#### 1D: Domain Allow/Deny Lists
**What:** Filter out SEO spam, prefer primaries.  
**How:**
```python
ALLOW_DOMAINS = [
    "github.com", "arxiv.org", "docs.python.org",
    "modelcontextprotocol.io", "docs.trychroma.com",
    "pytorch.org", "tensorflow.org", # official docs
]

DENY_DOMAINS = [
    "asana.com", "indeed.com", "grammarly.com",
    "indeed.co.uk", # job sites
    "*.edu/~*", # personal pages (use exceptions for official)
]

DEPRIORITIZE = [
    "medium.com", "dev.to", # blogs (useful but not primary)
]
```

**Impact:** Higher quality sources.

**Files to Modify:**
- New: `services/common/domain_policy.py`
- `services/web-search/app/service.py` - Apply filters post-search

---

### **Phase 2: Visibility (Weeks 3-4)** 🟡 HIGH PRIORITY

#### 2A: Schema Emission (A-G)
**What:** Structured artifacts for every run.  
**How:**
- Schema A: Planner JSON
- Schema B: Retrieval Log (with timings, query counts)
- Schema C: Evidence Map (claim → evidence)
- Schema D: KG Log (disambiguations, hop edges)
- Schema E: Chunking Report (params, sample chunks)
- Schema F: Guardrail Report (flags, actions)
- Schema G: A/B Grading (7-dimension scores)

**Impact:** Full pipeline visibility.

**Files to Modify:**
- `services/chat-service/app/service.py` - Orchestrate schema emission
- Each service emits its schema component
- UI displays artifacts in expandable sections

---

#### 2B: Per-Stage Timings
**What:** Waterfall breakdown.  
**How:**
```python
{
  "decompose_ms": 120,
  "retrieve_rag_ms": 340,
  "retrieve_web_ms": 1200,
  "kg_expand_ms": 280,
  "rerank_ms": 160,
  "synthesize_v1_ms": 890,
  "refine_ms": 450,
  "guardrail_ms": 80,
  "total_ms": 3520
}
```

**Impact:** Students see where time goes.

**Files to Modify:**
- Add timing decorator to all service calls
- Include in Schema B (Retrieval Log)
- UI waterfall chart

---

#### 2C: KG & Chunking Logs
**What:** Structured decision logs.  
**How:**
- KG: `{"disambiguation": {"MCP": "Model Context Protocol", "edges": [...]}, "hops": 2}`
- Chunking: `{"params": {"max_tokens": 512}, "samples": [...]}`

**Impact:** Multi-hop visibility.

**Files to Modify:**
- `services/knowledge-graph/app/service.py` - Emit Schema D
- `services/ingest-service/app/service.py` - Emit Schema E during ingestion

---

### **Phase 3: Measurement (Weeks 5-6)** 🟢 MEDIUM PRIORITY

#### 3A: A/B Grader Integration
**What:** 7-dimension scoring.  
**How:**
```python
{
  "coverage": 0.85,      # Answered all subtasks?
  "grounding": 0.90,     # Claims have evidence?
  "recency": 0.75,       # Temporal claims fresh?
  "retrieval_quality": 0.88,  # Relevant sources?
  "decision_adherence": 1.0,  # Followed policies?
  "structure": 0.95,     # Artifacts present?
  "conciseness": 0.70,   # Token efficiency?
  "overall": 0.86,
  "delta_vs_baseline": +0.12,
  "ci_95": [0.08, 0.16]
}
```

**Impact:** Quantified improvements.

**Files to Modify:**
- New: `services/grader/app/service.py`
- `services/chat-service/app/service.py` - Call grader, emit Schema G
- UI displays scores in Settings tab

---

#### 3B: Gold Corpus
**What:** 10-20 Q&A pairs with gold facts & sources.  
**How:**
```json
{
  "question": "What is Model Context Protocol?",
  "gold_facts": [
    "MCP is a protocol for connecting LLMs to external tools",
    "Created by Anthropic",
    "Enables server-client architecture"
  ],
  "gold_sources": [
    "https://modelcontextprotocol.io/introduction",
    "https://github.com/anthropics/mcp"
  ]
}
```

**Impact:** Reproducible precision/recall.

**Files to Modify:**
- New: `tests/benchmark/gold_corpus.json`
- New: `tests/benchmark/run_benchmark.py`
- Update README with measured scores

---

#### 3C: Preset Validation
**What:** Tie each preset to measured metrics.  
**How:**
- Run gold corpus on each preset
- Measure: precision, recall, latency, token cost
- Update README table with real numbers

**Impact:** Claims become facts.

---

### **Phase 4: Robustness (Weeks 7-8)** 🔵 LOW PRIORITY (but needed)

#### 4A: Guardrail Fallback
**What:** Error path surfacing.  
**How:**
```python
try:
    guardrail_result = call_security_service(query)
except:
    guardrail_result = {
        "status": "service_error",
        "action": "quarantined",
        "reason": "security_service_400"
    }
```

**Impact:** No more silent failures.

---

#### 4B: SLA Watchdog
**What:** Budget tracking.  
**How:**
- Track accumulated time
- If >80s, skip refine, finalize with caveat
- Emit `sla_breach: true` in logs

**Impact:** Predictable latency.

---

#### 4C: Model Routing Matrix
**What:** Task → model class mapping.  
**How:**
```python
ROUTING_MATRIX = {
    "decompose": "3b-8b",
    "query_enhancement": "3b-8b",
    "rerank": "3b-8b",
    "synthesize_v1": "7b-14b",
    "refine": "14b-20b",  # Only if time budget allows
}
```

**Impact:** Right model for right task.

---

## 🚀 Deployment Strategy

### Stage 1: Local Development (Week 1)
- Implement on `security` branch
- Test with torture prompts
- Commit frequently with clear messages

### Stage 2: AWS Integration (Week 2)
- Deploy to g4dn.2xlarge
- Run benchmark suite
- Collect performance data

### Stage 3: Documentation (Week 3)
- Update README with measured scores
- Create student guides for artifacts
- Add "How to Read Artifacts" tutorial

### Stage 4: Validation (Week 4)
- Run acceptance tests (list provided in feedback)
- Fix failures
- Iterate until all pass

---

## 📊 Success Metrics

### Tier 1: Must-Have (Phase 1)
- [ ] All torture prompts emit schemas A-G
- [ ] Every claim has `[#n]` → evidence
- [ ] Temporal queries have ≤48h sources
- [ ] Domain deny list blocks Asana/Indeed

### Tier 2: Should-Have (Phase 2)
- [ ] Waterfall chart shows per-stage timings
- [ ] KG logs show disambiguation
- [ ] Chunking report shows sample chunks

### Tier 3: Nice-to-Have (Phase 3)
- [ ] A/B scores on all presets
- [ ] Gold corpus precision/recall ≥0.85
- [ ] README table has measured numbers

---

## 🎓 Teaching Value Unlocked

After these changes, students will:

1. **See decisions** - Why this source? Why this model? Why this timing?
2. **Measure improvements** - Preset A vs B: +12% coverage, +0.2s latency
3. **Trust results** - Every claim has citation, every temporal query fresh
4. **Learn from failures** - Guardrail blocks shown, service errors surfaced
5. **Understand tradeoffs** - Small model fast, large model quality

---

## 🔄 Continuous Improvement Loop

```
┌─────────────┐
│ Torture     │
│ Prompts     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Run System  │
│ (Emit       │
│ Artifacts)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Grade       │
│ (Schema G)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Identify    │
│ Gaps        │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Adjust      │
│ Policies    │
└──────┬──────┘
       │
       └───────► (repeat)
```

---

## 🎯 The Bottom Line

**Current:** Infrastructure-complete, pretty demo  
**After Phase 1-2:** Production-grade, auditable workbench  
**After Phase 3-4:** World-class, measurable RAG lab  

**Timeline:** 8 weeks to world-class  
**Effort:** ~200-300 hours of focused development  
**ROI:** Demo → Teaching platform → Publishable research

---

## 📝 Next Steps (This Week)

1. **Review this analysis** - Discuss with team/stakeholders
2. **Prioritize Phase 1** - Contract Sentinel + Evidence + Recency
3. **Create feature branches** - One per Phase 1 component
4. **Set up gold corpus** - Start with 5 Q&A pairs, expand to 20
5. **Run first acceptance test** - Temporal enforcement

---

## 🔗 References

- Original Feedback: (torture prompt analysis)
- Project README: `/docs/README.md`
- Dev Notes: `/docs/dev_notes/prompts.txt`
- Monitoring: Grafana @ http://54.190.74.93:3001/

---

**Status:** 🚨 AWAITING APPROVAL TO PROCEED  
**Next Review:** After Phase 1A implementation  
**Contact:** AI Assistant | RAG Lab Development Team

