# OTel + OpenLLMetry Semantic Conventions (RAG Lab)

Spans (already present): ingest, index, retrieve, rerank, synthesize, guardrail

**Add attributes** (no payload logging):
- rag.request.contract_version
- rag.request.freshness_hours
- rag.request.intent
- rag.auth.perms_tag
- rag.retrieve.candidate_count
- rag.retrieve.acl_filtered_count
- rag.rerank.model
- rag.synth.model
- rag.synth.tokens_in
- rag.synth.tokens_out
- rag.guardrail.status  # ok|degraded|blocked
- rag.citations.count
- rag.citations.unique_documents
- rag.provenance.origin_tool_immutable  # true/false
- rag.abtest.bucket  # A|B when active

## Implementation Guide

### 1. Retrieve Span Enhancement
```python
with tracer.start_as_current_span("retrieve_internal.vector") as span:
    span.set_attribute("rag.request.contract_version", contract_version)
    span.set_attribute("rag.request.freshness_hours", freshness_hours)
    span.set_attribute("rag.request.intent", intent)
    span.set_attribute("rag.auth.perms_tag", perms_tag)
    span.set_attribute("rag.retrieve.candidate_count", len(candidates))
    span.set_attribute("rag.retrieve.acl_filtered_count", acl_filtered)
    span.set_attribute("rag.provenance.origin_tool_immutable", True)
```

### 2. Rerank Span Enhancement
```python
with tracer.start_as_current_span("rerank") as span:
    span.set_attribute("rag.rerank.model", "cross-encoder/ms-marco-MiniLM-L-12-v2")
    span.set_attribute("rag.retrieve.candidate_count", len(evidence_pre_rerank))
```

### 3. Synthesis Span Enhancement (OpenLLMetry)
```python
with tracer.start_as_current_span("synthesis_v1") as span:
    span.set_attribute("rag.synth.model", model_name)
    span.set_attribute("rag.synth.tokens_in", prompt_tokens)
    span.set_attribute("rag.synth.tokens_out", completion_tokens)
    span.set_attribute("llm.model.name", model_name)
    span.set_attribute("llm.model.provider", provider)
    span.set_attribute("llm.temperature", temperature)
    span.set_attribute("llm.max_tokens", max_tokens)
    span.set_attribute("llm.tokens.input", prompt_tokens)
    span.set_attribute("llm.tokens.output", completion_tokens)
    span.set_attribute("llm.tokens.total", prompt_tokens + completion_tokens)
    span.set_attribute("llm.cost.usd", cost)
```

### 4. Guardrail Span Enhancement
```python
with tracer.start_as_current_span("guardrails") as span:
    span.set_attribute("rag.guardrail.status", security_status)  # ok|degraded|blocked
```

### 5. Response Finalization
```python
# After all stages complete
span.set_attribute("rag.citations.count", len(citations))
span.set_attribute("rag.citations.unique_documents", len(set(c['doc_id'] for c in citations)))
span.set_attribute("rag.abtest.bucket", ab_test_setting)
```

## Grafana Query Examples

### P95 Latency by Intent
```promql
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket{rag_request_intent!=""}[5m])) by (le, rag_request_intent)
)
```

### ACL Filter Rate
```promql
sum(rate(rag_retrieve_acl_filtered_count_total[5m])) 
/ 
sum(rate(rag_retrieve_candidate_count_total[5m]))
```

### Guardrail Degradation Rate
```promql
sum(rate(rag_guardrail_status_total{status="degraded"}[5m]))
```

### Token Usage by Model
```promql
sum(rate(rag_synth_tokens_total[5m])) by (rag_synth_model)
```

### Provenance Immutability Check
```promql
count(rag_provenance_origin_tool_immutable == 0)
```

