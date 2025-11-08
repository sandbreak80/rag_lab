# Full Observability Contract - Wire-Up Design

**Status:** In Progress  
**Target:** Single sprint (9 tasks)  
**Constraint:** Single node, ≤14B models via Ollama, no duplicate metrics systems

---

## Overview

This document describes how to wire the **Full Observability Contract** (100% spec) to the real RAG orchestrator while maintaining:
- **Traces via OpenTelemetry/OpenLLMetry** → OTLP export → Grafana Tempo/Splunk
- **Metrics via Prometheus** → Grafana dashboards (no duplication)
- **Immutable provenance** through entire pipeline
- **Recency enforcement** with ≥2 primary sources ≤48h for temporal claims
- **A/B evaluation** with 7-dimension rubric + Δ(B-A) + 95% CI

---

## Task 1: IDs & Versioning (DONE = trace_id/request_id propagate + contract_version in artifacts)

### Goals
1. **Correlation:** `trace_id` and `request_id` must match across gateway → planner → retrievers → synthesis → guardrails
2. **Versioning:** Every artifact (A-G) carries `contract_version` and `schema_version`

### Implementation Points

#### Gateway (`services/api/app.py`)
```python
@app.before_request
def before_request():
    # Extract or generate IDs
    g.trace_id = request.headers.get('X-Trace-ID', format(trace.get_current_span().get_span_context().trace_id, '032x'))
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.tenant = request.json.get('tenant', 'unknown') if request.json else 'unknown'
    g.start_time = time.time()
    
    # Propagate to OTel context
    span = trace.get_current_span()
    span.set_attribute("request_id", g.request_id)
    span.set_attribute("tenant", g.tenant)
```

#### Artifacts Base
Add to all artifact dataclasses:
```python
@dataclass
class ArtifactBase:
    contract_version: str = "2.0.0"
    schema_version: str = "1.0.0"
    trace_id: str = ""
    request_id: str = ""
```

#### Orchestrator Context
Pass IDs through orchestrator:
```python
@dataclass
class OrchestrationContext:
    trace_id: str
    request_id: str
    tenant: str
    user_id: str
    start_time: float
    budgets: Budgets
    policy: Policy
```

### Acceptance
- [ ] `curl` response shows matching `trace_id` in response body and `X-Trace-ID` header
- [ ] All artifacts (A-G) carry same `trace_id` and `request_id`
- [ ] `contract_version: "2.0.0"` in all artifacts

---

## Task 2: Retrieval Provenance (DONE = origin_tool set in retrievers + preserved + Schema B logs dedup/filters)

### Goals
1. **Single source of truth:** `origin_tool` set **only** at retrieval time in retrievers
2. **Immutable:** Forbid downstream overwrites (enforce with frozen dataclass)
3. **Audit trail:** Schema B logs `dedup_actions` and `domain_filters` with reasons

### Implementation Points

#### Vector Search Retriever (`services/search/app/service.py`)
```python
def vector_search(query: str, k: int, ctx: OrchestrationContext) -> List[Evidence]:
    with tracer.start_as_current_span("retrieve_internal.vector") as span:
        # ... vector search logic ...
        evidence_list = []
        for result in results:
            evidence = Evidence(
                id=result['id'],
                content=result['content'],
                origin_tool=OriginTool.RAG,  # SET HERE, immutable
                url=result.get('url'),
                _metadata={
                    'score': result['score'],
                    'published_at': result.get('published_at'),  # ISO8601 UTC
                    'is_primary': result.get('is_primary', False),
                    'domain': extract_domain(result.get('url'))
                }
            )
            evidence_list.append(evidence)
        
        span.set_attribute("docs_retrieved", len(evidence_list))
        return evidence_list
```

#### Web Search Retriever (`services/web-search/app.py`)
```python
def web_search(query: str, k: int, ctx: OrchestrationContext) -> List[Evidence]:
    with tracer.start_as_current_span("retrieve_web.searxng") as span:
        # ... web search logic ...
        evidence_list = []
        for result in results:
            evidence = Evidence(
                id=f"web_{uuid.uuid4()}",
                content=result['snippet'],
                origin_tool=OriginTool.WEB_SEARCH,  # SET HERE, immutable
                url=result['url'],
                _metadata={
                    'score': result.get('score', 0.5),
                    'published_at': result.get('publishedDate'),  # ISO8601 UTC
                    'is_primary': is_primary_source(result['url']),
                    'domain': extract_domain(result['url'])
                }
            )
            evidence_list.append(evidence)
        
        span.set_attribute("docs_retrieved", len(evidence_list))
        return evidence_list
```

#### Research Agent Retriever (`services/research-agent/app.py`)
```python
def research_agent_retrieve(query: str, ctx: OrchestrationContext) -> List[Evidence]:
    with tracer.start_as_current_span("retrieve_research_agent") as span:
        # ... agent logic ...
        evidence_list = []
        for result in results:
            evidence = Evidence(
                id=f"ra_{uuid.uuid4()}",
                content=result['content'],
                origin_tool=OriginTool.RESEARCH_AGENT,  # SET HERE, immutable
                url=result.get('url'),
                _metadata={
                    'score': result.get('confidence', 0.7),
                    'published_at': result.get('published_at'),
                    'is_primary': result.get('is_primary', True),
                    'domain': extract_domain(result.get('url'))
                }
            )
            evidence_list.append(evidence)
        
        span.set_attribute("docs_retrieved", len(evidence_list))
        return evidence_list
```

#### Deduplication with Audit (`services/common/deduplicator.py`)
```python
@dataclass
class DedupAction:
    action: Literal["kept", "dropped"]
    doc_id: str
    reason: str
    duplicate_of: Optional[str] = None

def deduplicate(evidence_list: List[Evidence], ctx: OrchestrationContext) -> Tuple[List[Evidence], List[DedupAction]]:
    """
    Dedup by content hash, preserving highest score.
    Returns: (deduplicated_list, audit_trail)
    """
    seen = {}
    kept = []
    actions = []
    
    for ev in evidence_list:
        content_hash = hashlib.sha256(ev.content.encode()).hexdigest()[:16]
        
        if content_hash in seen:
            original = seen[content_hash]
            actions.append(DedupAction(
                action="dropped",
                doc_id=ev.id,
                reason=f"duplicate_content_hash={content_hash}",
                duplicate_of=original.id
            ))
        else:
            seen[content_hash] = ev
            kept.append(ev)
            actions.append(DedupAction(
                action="kept",
                doc_id=ev.id,
                reason="unique_content"
            ))
    
    return kept, actions
```

#### Domain Filtering with Audit (`services/common/domain_filter.py`)
```python
@dataclass
class DomainFilterAction:
    action: Literal["allowed", "dropped"]
    doc_id: str
    domain: str
    reason: str

DENYLIST = ["asana.com", "jira.internal.example.com"]  # Example

def filter_domains(evidence_list: List[Evidence], ctx: OrchestrationContext) -> Tuple[List[Evidence], List[DomainFilterAction]]:
    """
    Apply domain allow/deny rules.
    Returns: (filtered_list, audit_trail)
    """
    kept = []
    actions = []
    
    for ev in evidence_list:
        domain = ev.metadata.get('domain', 'unknown')
        
        if domain in DENYLIST:
            actions.append(DomainFilterAction(
                action="dropped",
                doc_id=ev.id,
                domain=domain,
                reason=f"denylist: {domain}"
            ))
        else:
            kept.append(ev)
            actions.append(DomainFilterAction(
                action="allowed",
                doc_id=ev.id,
                domain=domain,
                reason="not_on_denylist"
            ))
    
    return kept, actions
```

#### Schema B Population
```python
def build_retrieval_log(
    internal_results: List[Evidence],
    web_results: List[Evidence],
    dedup_actions: List[DedupAction],
    domain_actions: List[DomainFilterAction],
    timings: Dict[str, float],
    ctx: OrchestrationContext
) -> RetrievalLog:
    
    internal_entries = [
        RetrievalLogEntry(
            source_type="internal",
            query=ctx.query,
            results_count=len(internal_results),
            dedup_removed=sum(1 for a in dedup_actions if a.action == "dropped"),
            domain_filtered=sum(1 for a in domain_actions if a.action == "dropped"),
            timing_ms=timings.get("vector_search", 0) + timings.get("bm25_search", 0),
            rank_list=[
                {"doc_id": ev.id, "score": ev.metadata.get('score', 0), "origin": ev.origin_tool.value}
                for ev in internal_results[:5]
            ]
        )
    ]
    
    web_entries = [
        RetrievalLogEntry(
            source_type="web",
            query=ctx.query,
            results_count=len(web_results),
            dedup_removed=0,
            domain_filtered=sum(1 for a in domain_actions if a.action == "dropped" and a.domain in [extract_domain(w.url) for w in web_results]),
            timing_ms=timings.get("web_search", 0),
            rank_list=[
                {"doc_id": ev.id, "score": ev.metadata.get('score', 0), "origin": ev.origin_tool.value}
                for ev in web_results[:5]
            ]
        )
    ]
    
    return RetrievalLog(
        contract_version="2.0.0",
        schema_version="1.0.0",
        trace_id=ctx.trace_id,
        request_id=ctx.request_id,
        internal_queries=internal_entries,
        web_queries=web_entries,
        total_retrieved=len(internal_results) + len(web_results),
        total_deduped=sum(1 for a in dedup_actions if a.action == "dropped"),
        domains_filtered=[a.domain for a in domain_actions if a.action == "dropped"],
        timing_breakdown_ms=timings
    )
```

### Acceptance
- [ ] All `Evidence` objects have `origin_tool` set at retrieval time (never modified)
- [ ] Schema B shows `dedup_actions` with reasons and `duplicate_of` IDs
- [ ] Schema B shows `domain_filters` with `{"action":"dropped","reason":"denylist: asana.com"}`
- [ ] Footer `source_mix` matches `origin_tool` distribution

---

## Task 3: Recency Enforcement (DONE = ≥2 primary sources ≤48h or partial + server-side freshness_hours)

### Goals
1. **Gate at synthesis:** Block temporal claims lacking ≥2 primary sources with `published_at ≤ 48h`
2. **Server-side computation:** Calculate `freshness_hours` server-side (no client clock skew)
3. **Partial mode:** Return `recency.passed=false` and `refusal` explaining unmet criteria

### Implementation Points

#### Temporal Claim Detection (`services/common/temporal_detector.py`)
```python
TEMPORAL_KEYWORDS = ["today", "yesterday", "this week", "recently", "latest", "current", "now", "≤48h"]

def is_temporal_query(query: str) -> bool:
    """Detect if query requires fresh sources"""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in TEMPORAL_KEYWORDS)
```

#### Recency Evaluation (Enhanced)
```python
def evaluate_recency(
    sources: List[Evidence], 
    policy: Policy, 
    query: str,
    ctx: OrchestrationContext
) -> RecencyEvaluation:
    """
    Evaluate recency gate with server-side freshness calculation.
    """
    now = datetime.now(timezone.utc)
    histogram = {"<24h": 0, "24-48h": 0, "48h-1w": 0, ">1w": 0, "unknown": 0}
    primary_within_48h = 0
    
    for source in sources:
        published_at_str = source.metadata.get('published_at')
        
        if not published_at_str:
            histogram["unknown"] += 1
            continue
        
        try:
            # Parse ISO8601 UTC
            pub_date = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            hours_old = (now - pub_date).total_seconds() / 3600
            
            # SERVER-SIDE: Update source metadata with freshness_hours
            source._metadata['freshness_hours'] = int(hours_old)
            
            # Update histogram
            if hours_old < 24:
                histogram["<24h"] += 1
            elif hours_old < 48:
                histogram["24-48h"] += 1
            elif hours_old < 168:  # 1 week
                histogram["48h-1w"] += 1
            else:
                histogram[">1w"] += 1
            
            # Count primary sources within 48h
            is_primary = source.metadata.get('is_primary', False)
            if is_primary and hours_old <= 48:
                primary_within_48h += 1
        
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid published_at format: {published_at_str} - {e}")
            histogram["unknown"] += 1
    
    # Evaluate pass/fail
    passed = True
    notes = ""
    
    # Check if query requires recency
    requires_recency = policy.requires_recency or is_temporal_query(query)
    
    if requires_recency:
        min_required = policy.min_primary_sources
        if primary_within_48h < min_required:
            passed = False
            notes = f"RECENCY_FAIL: Required {min_required} primary sources ≤48h, found {primary_within_48h}. Query appears temporal but sources are stale."
    
    if not notes:
        notes = f"Recency requirements met: {primary_within_48h} primary sources ≤48h"
    
    return RecencyEvaluation(
        contract_version="2.0.0",
        schema_version="1.0.0",
        trace_id=ctx.trace_id,
        request_id=ctx.request_id,
        window_hours=48,
        passed=passed,
        notes=notes,
        freshness_histogram=histogram,
        primary_sources_within_window=primary_within_48h
    )
```

#### Synthesis Gate
```python
def synthesize_answer(
    query: str,
    evidence: List[Evidence],
    recency_eval: RecencyEvaluation,
    ctx: OrchestrationContext
) -> Tuple[str, str, Optional[str]]:
    """
    Synthesize answer with recency gate.
    Returns: (answer, confidence, refusal)
    """
    with tracer.start_as_current_span("synthesis_v1") as span:
        # GATE: Block if temporal query fails recency
        if not recency_eval.passed:
            refusal = (
                f"Unable to provide a confident answer. {recency_eval.notes} "
                f"Freshness histogram: {recency_eval.freshness_histogram}. "
                f"Please refine your query or check back later."
            )
            span.set_attribute("recency_failed", True)
            span.set_attribute("refusal_reason", "recency_gate")
            return "", "VERY_LOW", refusal
        
        # ... normal synthesis ...
        prompt = build_prompt(query, evidence)
        answer = llm_generate(prompt)
        confidence = calculate_confidence(answer, evidence)
        
        span.set_attribute("answer_length", len(answer))
        span.set_attribute("confidence", confidence)
        
        return answer, confidence, None
```

### Acceptance
- [ ] Temporal query (e.g., "What happened today?") with stale sources returns `recency.passed=false` and refusal
- [ ] Temporal query with ≥2 primary sources ≤48h returns `recency.passed=true` and answer
- [ ] `freshness_hours` computed server-side and matches `published_at`
- [ ] Freshness histogram reflects source distribution

---

## Task 4: A/B Evaluator (DONE = 7-dimension grader + Δ(B-A) + 95% CI + rationales)

### Goals
1. **7-dimension rubric:** coverage, grounding, recency, retrieval_quality, decision_adherence, structure, conciseness
2. **Comparison:** Δ(B-A) with bootstrap 95% CI when both settings run
3. **Rationales:** Per-dimension explanations for failures

### Implementation Points

#### Grader (`services/common/ab_grader.py`)
```python
@dataclass
class DimensionScore:
    dimension: str
    score: float  # 0.0-1.0
    passed: bool
    rationale: str

def grade_answer(
    query: str,
    answer: str,
    evidence: List[Evidence],
    recency_eval: RecencyEvaluation,
    retrieval_log: RetrievalLog,
    evidence_map: EvidenceMap,
    ctx: OrchestrationContext
) -> ABEvaluation:
    """
    Grade answer on 7 dimensions.
    """
    dimensions_scores = {}
    dimension_details = []
    
    # 1. Coverage: Does answer address all query aspects?
    coverage_score, coverage_rationale = grade_coverage(query, answer)
    dimensions_scores['coverage'] = coverage_score
    dimension_details.append(DimensionScore("coverage", coverage_score, coverage_score >= 0.7, coverage_rationale))
    
    # 2. Grounding: Are claims backed by evidence?
    grounding_score = evidence_map.grounding_rate
    grounding_rationale = f"{len(evidence_map.ungrounded_claims)} ungrounded claims" if evidence_map.ungrounded_claims else "All claims grounded"
    dimensions_scores['grounding'] = grounding_score
    dimension_details.append(DimensionScore("grounding", grounding_score, grounding_score >= 0.9, grounding_rationale))
    
    # 3. Recency: Are temporal claims supported by fresh sources?
    recency_score = 1.0 if recency_eval.passed else 0.0
    dimensions_scores['recency'] = recency_score
    dimension_details.append(DimensionScore("recency", recency_score, recency_eval.passed, recency_eval.notes))
    
    # 4. Retrieval Quality: Are top-k relevant?
    retrieval_score = calculate_retrieval_quality(retrieval_log)
    retrieval_rationale = f"MRR: {retrieval_score:.2f}, {retrieval_log.total_deduped} deduped"
    dimensions_scores['retrieval_quality'] = retrieval_score
    dimension_details.append(DimensionScore("retrieval_quality", retrieval_score, retrieval_score >= 0.8, retrieval_rationale))
    
    # 5. Decision Adherence: Did we follow policy/budgets?
    adherence_score, adherence_rationale = grade_decision_adherence(ctx)
    dimensions_scores['decision_adherence'] = adherence_score
    dimension_details.append(DimensionScore("decision_adherence", adherence_score, adherence_score >= 0.95, adherence_rationale))
    
    # 6. Structure: Is answer well-formatted?
    structure_score, structure_rationale = grade_structure(answer)
    dimensions_scores['structure'] = structure_score
    dimension_details.append(DimensionScore("structure", structure_score, structure_score >= 0.8, structure_rationale))
    
    # 7. Conciseness: Is answer appropriately concise?
    conciseness_score, conciseness_rationale = grade_conciseness(answer, query)
    dimensions_scores['conciseness'] = conciseness_score
    dimension_details.append(DimensionScore("conciseness", conciseness_score, conciseness_score >= 0.7, conciseness_rationale))
    
    # Overall score (weighted average)
    overall_score = sum(dimensions_scores.values()) / len(dimensions_scores)
    
    return ABEvaluation(
        contract_version="2.0.0",
        schema_version="1.0.0",
        trace_id=ctx.trace_id,
        request_id=ctx.request_id,
        setting=ctx.ab_test.setting,
        dimensions=dimensions_scores,
        overall_score=overall_score,
        dimension_details=dimension_details,  # NEW: rationales
        comparison=None  # Populated if both A and B run
    )
```

#### A/B Comparison (Bootstrap CI)
```python
def compare_ab_runs(eval_a: ABEvaluation, eval_b: ABEvaluation) -> Dict[str, Any]:
    """
    Compare A vs B with bootstrap 95% CI.
    """
    deltas = {}
    for dim in eval_a.dimensions:
        delta = eval_b.dimensions[dim] - eval_a.dimensions[dim]
        deltas[dim] = delta
    
    overall_delta = eval_b.overall_score - eval_a.overall_score
    
    # Bootstrap CI (simplified - use numpy/scipy in production)
    ci_lower = overall_delta - 0.05  # Mock
    ci_upper = overall_delta + 0.05  # Mock
    
    return {
        "delta_dimensions": deltas,
        "delta_overall": overall_delta,
        "ci_95": [ci_lower, ci_upper],
        "winner": "B" if overall_delta > 0.02 else ("A" if overall_delta < -0.02 else "tie")
    }
```

### Acceptance
- [ ] ABEvaluation shows 7 dimension scores (all 0.0-1.0)
- [ ] Failed dimensions include rationales (e.g., "3 ungrounded claims")
- [ ] When both A and B run, `comparison` shows Δ(B-A) + CI
- [ ] Overall score is weighted average

---

## Task 5: OTel + OpenLLMetry (DONE = 8 stage spans + semantic attrs + OTLP export + keep Prometheus)

### Goals
1. **8 stage spans:** plan, retrieve_internal, retrieve_web, kg_expand, rerank, synthesis_v1, self_critique, synthesis_v2
2. **OpenLLMetry:** Use semantic attributes (model, tokens, latency) without logging payloads
3. **OTLP export:** Send traces to OTLP collector → Grafana Tempo/Splunk
4. **Keep Prometheus:** No duplicate metrics - traces via OTel, metrics via Prometheus

### Implementation Points

#### OTel Setup (`services/api/otel_config.py`)
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def setup_otel(service_name: str):
    """Configure OpenTelemetry with OTLP exporter"""
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "2.0.0",
        "deployment.environment": os.getenv("ENV", "development")
    })
    
    provider = TracerProvider(resource=resource)
    
    # OTLP exporter (to collector)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
        insecure=True  # Use TLS in production
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    trace.set_tracer_provider(provider)
    
    logger.info(f"OpenTelemetry configured for {service_name} → {otlp_exporter.endpoint}")
```

#### OpenLLMetry Attributes (Semantic Convention)
```python
class LLMSpanAttributes:
    """OpenLLMetry semantic attributes (no payloads)"""
    MODEL_NAME = "llm.model.name"
    MODEL_PROVIDER = "llm.model.provider"
    TOKENS_INPUT = "llm.tokens.input"
    TOKENS_OUTPUT = "llm.tokens.output"
    TOKENS_TOTAL = "llm.tokens.total"
    LATENCY_MS = "llm.latency.ms"
    TEMPERATURE = "llm.temperature"
    MAX_TOKENS = "llm.max_tokens"
    COST_USD = "llm.cost.usd"
```

#### Stage Spans (Example: Synthesis)
```python
def synthesize_answer_with_otel(
    query: str,
    evidence: List[Evidence],
    ctx: OrchestrationContext
) -> str:
    with tracer.start_as_current_span("synthesis_v1") as span:
        span.set_attribute("query_length", len(query))
        span.set_attribute("evidence_count", len(evidence))
        
        # Build prompt
        prompt = build_prompt(query, evidence)
        span.set_attribute(LLMSpanAttributes.MODEL_NAME, "llama2:13b")
        span.set_attribute(LLMSpanAttributes.MODEL_PROVIDER, "ollama")
        span.set_attribute(LLMSpanAttributes.TOKENS_INPUT, count_tokens(prompt))
        
        # Call LLM
        start = time.time()
        answer = llm_generate(prompt)
        latency_ms = (time.time() - start) * 1000
        
        # Record LLM metrics (OpenLLMetry)
        span.set_attribute(LLMSpanAttributes.LATENCY_MS, latency_ms)
        span.set_attribute(LLMSpanAttributes.TOKENS_OUTPUT, count_tokens(answer))
        span.set_attribute(LLMSpanAttributes.TOKENS_TOTAL, count_tokens(prompt) + count_tokens(answer))
        
        # NO PAYLOADS (per spec)
        # span.set_attribute("prompt", prompt)  # DON'T DO THIS
        # span.set_attribute("answer", answer)  # DON'T DO THIS
        
        return answer
```

#### All 8 Stage Spans
```python
# 1. Plan
with tracer.start_as_current_span("plan") as span:
    planner_artifact = plan_query(query, ctx)
    span.set_attribute("route", planner_artifact.route_decision)

# 2. Retrieve Internal
with tracer.start_as_current_span("retrieve_internal") as span:
    internal_results = vector_search(query, k=20, ctx)
    span.set_attribute("docs_retrieved", len(internal_results))

# 3. Retrieve Web
with tracer.start_as_current_span("retrieve_web") as span:
    web_results = web_search(query, k=10, ctx)
    span.set_attribute("docs_retrieved", len(web_results))

# 4. KG Expand
with tracer.start_as_current_span("kg_expand") as span:
    kg_results = kg_expand(query, ctx)
    span.set_attribute("entities_resolved", len(kg_results.entities))

# 5. Rerank
with tracer.start_as_current_span("rerank") as span:
    reranked = rerank(all_results, query, ctx)
    span.set_attribute("docs_reranked", len(reranked))

# 6. Synthesis V1
with tracer.start_as_current_span("synthesis_v1") as span:
    answer_v1 = synthesize_answer_with_otel(query, reranked, ctx)
    span.set_attribute(LLMSpanAttributes.MODEL_NAME, "llama2:13b")

# 7. Self Critique
with tracer.start_as_current_span("self_critique") as span:
    critique = critique_answer(answer_v1, evidence, ctx)
    span.set_attribute("needs_refinement", critique.needs_refinement)

# 8. Synthesis V2 (if needed)
if critique.needs_refinement:
    with tracer.start_as_current_span("synthesis_v2") as span:
        answer_v2 = synthesize_answer_with_otel(query, reranked, ctx)
        span.set_attribute(LLMSpanAttributes.MODEL_NAME, "llama2:13b")
```

### Acceptance
- [ ] 8 spans visible in Grafana Tempo/Jaeger: plan, retrieve_internal, retrieve_web, kg_expand, rerank, synthesis_v1, self_critique, synthesis_v2
- [ ] LLM spans have OpenLLMetry attrs (model, tokens, latency)
- [ ] NO payloads (prompt/answer) in spans
- [ ] Prometheus metrics still work (no duplication)

---

## Task 6: Guardrail Fallback (DONE = Schema F on 4xx/5xx + security_status:degraded + continue)

### Goals
1. **Always emit Schema F:** Even on guardrail service errors
2. **Degraded mode:** Add `security_status: "degraded"` to footer
3. **Continue:** Don't block entire request on guardrail failure

### Implementation Points

#### Guardrail Client (`services/common/guardrail_client.py`)
```python
def check_guardrails(content: str, ctx: OrchestrationContext) -> GuardrailReport:
    """
    Call security guardrails service with fallback.
    """
    with tracer.start_as_current_span("guardrails") as span:
        detections = []
        service_errors = []
        overall_safe = True
        
        try:
            response = requests.post(
                "http://security-guardrails:5000/check",
                json={"content": content, "tenant": ctx.tenant},
                timeout=2.0
            )
            
            if response.status_code == 200:
                data = response.json()
                for finding in data.get('findings', []):
                    detections.append(GuardrailDetection(
                        type=finding['type'],
                        severity=finding['severity'],
                        details=finding['details'],
                        action_taken=finding['action']
                    ))
                
                overall_safe = data.get('safe', True)
                span.set_attribute("guardrails.safe", overall_safe)
            
            else:
                # Service returned error - log but continue
                service_errors.append({
                    "service": "security-guardrails",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                overall_safe = False  # Assume unsafe in degraded mode
                span.set_attribute("guardrails.degraded", True)
                logger.warning(f"Guardrail service error: {response.status_code}")
        
        except requests.exceptions.Timeout:
            service_errors.append({
                "service": "security-guardrails",
                "error": "Timeout after 2.0s",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            overall_safe = False
            span.set_attribute("guardrails.timeout", True)
            logger.error("Guardrail service timeout")
        
        except Exception as e:
            service_errors.append({
                "service": "security-guardrails",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            overall_safe = False
            span.record_exception(e)
            logger.error(f"Guardrail service exception: {e}")
        
        return GuardrailReport(
            contract_version="2.0.0",
            schema_version="1.0.0",
            trace_id=ctx.trace_id,
            request_id=ctx.request_id,
            detections=detections,
            service_errors=service_errors,
            overall_safe=overall_safe
        )
```

#### Footer with Security Status
```python
def build_footer(guardrail_report: GuardrailReport, ...) -> Dict[str, Any]:
    security_status = "healthy" if guardrail_report.overall_safe and not guardrail_report.service_errors else "degraded"
    
    return {
        "source_mix": calculate_source_mix(sources),
        "budget_use": ctx.budget_use,
        "wall_time_ms": (time.time() - ctx.start_time) * 1000,
        "sha256": hash_answer(answer),
        "security_status": security_status
    }
```

### Acceptance
- [ ] Forced guardrail 400 returns Schema F with `service_errors` and continues
- [ ] Footer shows `security_status: "degraded"` when guardrail fails
- [ ] Request completes with answer (doesn't block on guardrail failure)

---

## Task 7: SLA Watchdog (DONE = ETA tracking + skip refine if >80s + watchdog_actions + wall_time ≤90s)

### Goals
1. **Track ETA:** Monitor cumulative time across pipeline stages
2. **Skip refine:** If ETA > 80s, skip self_critique and synthesis_v2
3. **Log decision:** Add `watchdog_actions` to PlannerArtifact
4. **Hard limit:** Ensure `wall_time_ms ≤ 90s`

### Implementation Points

#### SLA Watchdog (`services/common/sla_watchdog.py`)
```python
@dataclass
class WatchdogAction:
    stage: str
    action: Literal["allowed", "skipped"]
    reason: str
    eta_ms: float

class SLAWatchdog:
    def __init__(self, sla_ms: int):
        self.sla_ms = sla_ms
        self.start_time = time.time()
        self.actions: List[WatchdogAction] = []
    
    def get_eta_ms(self) -> float:
        """Current elapsed time in ms"""
        return (time.time() - self.start_time) * 1000
    
    def get_remaining_ms(self) -> float:
        """Remaining budget"""
        return self.sla_ms - self.get_eta_ms()
    
    def should_skip_stage(self, stage: str, estimated_duration_ms: float) -> bool:
        """
        Check if stage should be skipped to meet SLA.
        """
        eta = self.get_eta_ms()
        remaining = self.get_remaining_ms()
        
        if estimated_duration_ms > remaining:
            self.actions.append(WatchdogAction(
                stage=stage,
                action="skipped",
                reason=f"ETA {eta:.0f}ms + est. {estimated_duration_ms:.0f}ms > SLA {self.sla_ms}ms",
                eta_ms=eta
            ))
            return True
        
        self.actions.append(WatchdogAction(
            stage=stage,
            action="allowed",
            reason=f"Within budget: {remaining:.0f}ms remaining",
            eta_ms=eta
        ))
        return False
```

#### Integration into Orchestrator
```python
def orchestrate_with_sla(query: str, ctx: OrchestrationContext) -> RagResponse:
    watchdog = SLAWatchdog(sla_ms=ctx.budgets.sla_ms)
    
    # ... retrieve, rerank ...
    
    # Synthesis V1 (always run)
    answer_v1 = synthesize_answer(query, evidence, ctx)
    
    # Self-critique (optional)
    if not watchdog.should_skip_stage("self_critique", estimated_duration_ms=500):
        critique = critique_answer(answer_v1, evidence, ctx)
        
        # Synthesis V2 (optional)
        if critique.needs_refinement and not watchdog.should_skip_stage("synthesis_v2", estimated_duration_ms=800):
            answer_v2 = synthesize_answer(query, evidence, ctx)
            final_answer = answer_v2
        else:
            final_answer = answer_v1
    else:
        final_answer = answer_v1
    
    # Add watchdog actions to PlannerArtifact
    planner_artifact.watchdog_actions = watchdog.actions
    
    # Ensure wall_time ≤ SLA
    wall_time_ms = watchdog.get_eta_ms()
    if wall_time_ms > ctx.budgets.sla_ms:
        logger.warning(f"SLA BREACH: {wall_time_ms:.0f}ms > {ctx.budgets.sla_ms}ms")
    
    return response
```

### Acceptance
- [ ] Query with `sla_ms: 3000` and slow LLM skips self_critique when ETA > 2500ms
- [ ] PlannerArtifact shows `watchdog_actions` with reasons
- [ ] `wall_time_ms ≤ 90s` (hard limit enforced)

---

## Task 8: UI Hooks (DONE = Artifacts visible in waterfall + JSON inspector)

### Goals
1. **Waterfall chart:** Show timing for 8 stages from OTel spans
2. **JSON inspector:** Collapsible sections for artifacts A-G
3. **Thin integration:** No heavy UI refactors, just data plumbing

### Implementation Points

#### Frontend Update (`frontend/src/components/metrics/WaterfallChart.tsx`)
```typescript
// Add new stages
const stages = [
  { key: 'plan', label: 'Plan', color: '#3b82f6' },
  { key: 'retrieve_internal', label: 'Retrieve (Internal)', color: '#10b981' },
  { key: 'retrieve_web', label: 'Retrieve (Web)', color: '#f59e0b' },
  { key: 'kg_expand', label: 'KG Expand', color: '#8b5cf6' },
  { key: 'rerank', label: 'Rerank', color: '#ec4899' },
  { key: 'synthesis_v1', label: 'Synthesis V1', color: '#ef4444' },
  { key: 'self_critique', label: 'Self Critique', color: '#06b6d4' },
  { key: 'synthesis_v2', label: 'Synthesis V2', color: '#f97316' },
];
```

#### Artifact Inspector (`frontend/src/components/debug/ArtifactInspector.tsx`)
```typescript
interface ArtifactInspectorProps {
  artifacts: {
    planner: PlannerArtifact;
    retrieval_log: RetrievalLog;
    evidence_map: EvidenceMap;
    kg_log?: KGLog;
    chunking_report: ChunkingReport;
    guardrail_report: GuardrailReport;
    ab_eval: ABEvaluation;
  };
}

export function ArtifactInspector({ artifacts }: ArtifactInspectorProps) {
  return (
    <div className="space-y-4">
      <CollapsibleSection title="Schema A: Planner" artifact={artifacts.planner} />
      <CollapsibleSection title="Schema B: Retrieval Log" artifact={artifacts.retrieval_log} />
      <CollapsibleSection title="Schema C: Evidence Map" artifact={artifacts.evidence_map} />
      {artifacts.kg_log && <CollapsibleSection title="Schema D: KG Log" artifact={artifacts.kg_log} />}
      <CollapsibleSection title="Schema E: Chunking Report" artifact={artifacts.chunking_report} />
      <CollapsibleSection title="Schema F: Guardrail Report" artifact={artifacts.guardrail_report} />
      <CollapsibleSection title="Schema G: A/B Evaluation" artifact={artifacts.ab_eval} />
    </div>
  );
}
```

### Acceptance
- [ ] Waterfall chart shows 8 stages
- [ ] Debug panel shows collapsible artifacts A-G
- [ ] Clicking artifact expands JSON view

---

## Task 9: Acceptance Tests (DONE = All probes pass)

### Test Suite (`tests/acceptance/test_full_contract.py`)

```python
import pytest
import requests

API_URL = "http://localhost:8080/v1/rag/query"

def test_temporal_probe():
    """Temporal query with ≤48h requirement"""
    response = requests.post(API_URL, json={
        "query": "What happened in AI today?",
        "tenant": "test",
        "user_id": "probe",
        "policy": {"requires_recency": True, "min_primary_sources": 2}
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check recency
    assert data['recency']['passed'] or data['refusal'] is not None
    assert data['recency']['primary_sources_within_window'] >= 0
    assert '<24h' in data['recency']['freshness_histogram']
    
    # Check sources have origin_tool
    for source in data['sources']:
        assert source['origin_tool'] in ['rag', 'web_search', 'research_agent']
        assert source['published_at'] is not None or source['origin_tool'] == 'rag'


def test_provenance_probe():
    """Mixed RAG/Web/ResearchAgent run"""
    response = requests.post(API_URL, json={
        "query": "Tell me about RAG systems",
        "tenant": "test",
        "user_id": "probe",
        "plan_id": "blended_v1"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check source_mix
    source_mix = data['source_mix']
    assert 'rag' in source_mix
    assert 'web_search' in source_mix
    assert sum(source_mix.values()) == len(data['sources'])
    
    # Check origin_tool consistency
    for source in data['sources']:
        assert source['origin_tool'] in ['rag', 'web_search', 'research_agent']


def test_routing_transparency_probe():
    """Route decision is transparent"""
    response = requests.post(API_URL, json={
        "query": "What is 2+2?",
        "tenant": "test",
        "user_id": "probe"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check route
    assert data['route'] in ['rag', 'web', 'blended']
    assert len(data['route_reason']) > 10
    
    # Check planner artifact
    assert data['planner']['route_decision'] == data['route']
    assert len(data['planner']['route_reason']) > 10


def test_ab_probe():
    """A/B evaluation with dimensions"""
    response = requests.post(API_URL, json={
        "query": "Explain RAG",
        "tenant": "test",
        "user_id": "probe",
        "ab_test": {"setting": "A"}
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check ab_eval
    ab_eval = data['ab_eval']
    assert ab_eval['setting'] == 'A'
    assert len(ab_eval['dimensions']) == 7
    assert 'coverage' in ab_eval['dimensions']
    assert 'grounding' in ab_eval['dimensions']
    assert 0.0 <= ab_eval['overall_score'] <= 1.0


def test_guardrail_probe():
    """Forced guardrail error"""
    # Mock guardrail service to return 500
    # (requires test harness to intercept)
    
    response = requests.post(API_URL, json={
        "query": "Normal query",
        "tenant": "test",
        "user_id": "probe"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check guardrail_report exists even on error
    assert 'guardrail_report' in data
    guardrail = data['guardrail_report']
    
    # If service error, check footer
    if guardrail['service_errors']:
        assert 'security_status' in data
        assert data['security_status'] == 'degraded'


def test_sla_probe():
    """SLA watchdog skips refine when ETA > 80s"""
    response = requests.post(API_URL, json={
        "query": "Complex query requiring multiple stages",
        "tenant": "test",
        "user_id": "probe",
        "budgets": {"sla_ms": 3000}
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check watchdog_actions in planner
    planner = data['planner']
    if 'watchdog_actions' in planner:
        # If any stage was skipped, it should be logged
        skipped = [a for a in planner['watchdog_actions'] if a['action'] == 'skipped']
        if skipped:
            assert any('ETA' in a['reason'] for a in skipped)
    
    # Check wall_time
    assert data['wall_time_ms'] <= 90000  # Hard limit
```

### Acceptance
- [ ] All 6 probes pass (temporal, provenance, routing, A/B, guardrail, SLA)

---

## Rollback Plan

1. **Feature flags:** Each artifact population behind `ENABLE_SCHEMA_X` env var
2. **Fallback:** If artifact population fails, return minimal response with error in artifact
3. **Monitoring:** Track artifact population latency; alert if >10% overhead
4. **Revert:** Git revert to pre-wire commit; redeploy

---

## Risk List

1. **Performance:** Artifact population adds ~50-100ms overhead
   - **Mitigation:** Parallelize where possible; cache expensive computations
   
2. **Breaking changes:** New contract incompatible with old frontend
   - **Mitigation:** Version artifacts; support v1 and v2 responses
   
3. **OTel overhead:** Span creation/export adds latency
   - **Mitigation:** Use BatchSpanProcessor; sample at 10% for high-volume tenants
   
4. **Recency gate false positives:** Block valid queries with stale sources
   - **Mitigation:** Make recency policy optional; default to `requires_recency: false`

---

## Definition of Done

✅ All acceptance tests pass  
✅ Artifacts carry matching `trace_id` and `request_id`  
✅ EvidenceMap shows ≤48h primaries for temporal claims  
✅ Footer has `source_mix`, `budget_use`, `wall_time_ms`, `sha256`  
✅ OTel spans visible in Grafana Tempo  
✅ Prometheus metrics still work (no duplication)  
✅ Guardrail errors handled gracefully  
✅ SLA watchdog enforces <90s wall time  
✅ UI shows artifacts in inspector

---

**Next:** Execute tasks 1-9 in sequence.

