# Testing Gaps Analysis - Feature Timing & Observability

**Date:** November 17, 2025
**Status:** In Progress

## Overview

Analysis of missing functionality in our testing suite, specifically around:
1. Feature functionality validation (A-R)
2. Timing data tracking per feature
3. OpenTelemetry integration
4. Prometheus metrics
5. Grafana trace links

---

## Current Test Coverage

### ✅ What We Have

1. **Basic Feature Tests** (`test_backend_features_comprehensive.py`)
   - Tests all 18 features (A-R)
   - Validates functionality (answer + sources)
   - Checks for timing data presence (basic)
   - Checks for trace_id presence

2. **Timing Data Structure**
   - `stage_timings` dict in response
   - Includes: `vector_ms`, `web_ms`, `kg_ms`, `llm_ms`, `total_ms`
   - Available in `metrics.stage_timings` and `artifacts.stage_timings`

3. **OpenTelemetry Spans**
   - Major stages have OTel spans
   - Spans include attributes for observability
   - Trace IDs are generated

---

## ❌ Missing Functionality

### 1. Per-Feature Timing Tracking

**Problem:** Individual features (A-R) don't have their own timing entries in `stage_timings`.

**Current State:**
- Only tracks: `vector_ms`, `web_ms`, `kg_ms`, `llm_ms`, `total_ms`
- Missing: `query_expansion_ms`, `bm25_ms`, `hybrid_ms`, `reranking_ms`, `chunking_ms`, etc.

**Impact:**
- Can't see which features are slow
- Can't optimize individual features
- Performance breakdown in UI is incomplete
- Grafana dashboards can't show per-feature metrics

**Required Changes:**
- Add timing tracking for each feature in `rag.py`
- Update `stage_timings` to include per-feature timings
- Ensure timings are in OTel span attributes
- Ensure timings are in Prometheus metrics

### 2. OpenTelemetry Span Attributes

**Problem:** Per-feature timings are not in OTel span attributes.

**Current State:**
- OTel spans exist for major stages
- Attributes include: `rag.retrieve.candidate_count`, `rag.synth.model`, etc.
- Missing: Per-feature timing attributes

**Impact:**
- Can't query OTel traces for feature-specific performance
- Grafana can't show per-feature breakdowns
- Distributed tracing doesn't show feature-level details

**Required Changes:**
- Add `rag.feature.{feature_name}.duration_ms` attributes to spans
- Add `rag.feature.{feature_name}.enabled` attributes
- Ensure all features set appropriate span attributes

### 3. Prometheus Metrics

**Problem:** Per-feature timings are not in Prometheus metrics.

**Current State:**
- Prometheus metrics exist for: `rag_requests_total`, `rag_llm_tokens_total`, etc.
- Missing: Per-feature timing histograms

**Impact:**
- Can't create Grafana dashboards for per-feature performance
- Can't set up alerts for slow features
- Can't track feature usage over time

**Required Changes:**
- Add `rag_feature_duration_seconds` histogram with `feature` label
- Add `rag_feature_enabled_total` counter with `feature` label
- Export metrics for all features (A-R)

### 4. Test Validation

**Problem:** Tests don't validate that timing data is complete and correct.

**Current State:**
- Tests check if timing data exists
- Tests don't validate specific timing keys
- Tests don't validate timing values are reasonable

**Impact:**
- Broken features might not be detected
- Timing data might be missing but tests pass
- Can't ensure observability is working

**Required Changes:**
- Enhanced test suite (`test_backend_features_with_timing.py`)
- Validate expected timing keys for each feature
- Validate timing values are > 0 and reasonable
- Validate trace_id is present (for Grafana links)

---

## Feature-to-Timing Mapping

| Feature | Expected Timing Key | Current Status |
|---------|-------------------|----------------|
| A. Security Guardrails | `guardrails_ms` | ❌ Missing |
| B. Query Expansion | `query_expansion_ms` | ❌ Missing |
| C. BM25 Search | `bm25_ms` | ❌ Missing |
| D. Hybrid Search | `hybrid_ms` | ❌ Missing |
| E. Knowledge Graph | `kg_ms` | ✅ Present |
| F. LLM Re-ranking | `reranking_ms` | ❌ Missing |
| G. Web Search | `web_ms` | ✅ Present |
| H. Agentic Chunking | `chunking_ms` | ❌ Missing |
| I. Top-K Results | N/A (affects other timings) | ✅ Present |
| J. Prompt Enhancement | `prompt_enhancement_ms` | ❌ Missing |
| K. Auto Model Routing | `model_routing_ms` | ❌ Missing |
| L. Query Decomposition | `decomposition_ms` | ❌ Missing |
| M. Self-RAG | `self_rag_ms` | ❌ Missing |
| N. Show Reasoning | `reasoning_ms` | ❌ Missing |
| O. Vector Database | `vector_ms` | ✅ Present |
| P. Research Agent | `research_ms` | ❌ Missing |
| Q. Web Search | `web_ms` | ✅ Present (duplicate) |
| R. Knowledge Graph | `kg_ms` | ✅ Present (duplicate) |

**Summary:** Only 4/18 features have dedicated timing tracking.

---

## UI Defects Related to Testing

### 1. Chat - Performance Breakdown Incomplete
**Root Cause:** Missing per-feature timings in `stage_timings`
**Fix:** Add timing tracking for all features (A-R)

### 2. Chat - View Trace in Grafana Broken Link
**Root Cause:** Missing or invalid `trace_id` in response
**Fix:** Ensure `trace_id` is always present and valid

### 3. Settings - Feature Toggles Not Validated
**Root Cause:** No backend tests validate feature toggles work
**Fix:** Enhanced test suite validates each toggle

---

## Implementation Plan

### Phase 1: Add Timing Tracking (Priority: HIGH)

1. **Update `rag.py` to track per-feature timings**
   - Add timing for each feature as it executes
   - Store in `stage_timings` dict
   - Include in response `metrics.stage_timings`

2. **Update OTel spans**
   - Add `rag.feature.{feature_name}.duration_ms` attributes
   - Add `rag.feature.{feature_name}.enabled` attributes

3. **Update Prometheus metrics**
   - Add `rag_feature_duration_seconds` histogram
   - Add `rag_feature_enabled_total` counter

### Phase 2: Enhanced Testing (Priority: HIGH)

1. **Create `test_backend_features_with_timing.py`**
   - Validate functionality
   - Validate timing data presence
   - Validate timing keys for each feature
   - Validate trace_id presence

2. **Update existing tests**
   - Add timing validation to comprehensive tests
   - Add trace_id validation

### Phase 3: Documentation (Priority: MEDIUM)

1. **Document timing structure**
   - Which features have timings
   - How to access timings in UI
   - How to query timings in Grafana

2. **Document test coverage**
   - What tests validate
   - How to run tests
   - How to interpret results

---

## Next Steps

1. ✅ Create enhanced test suite (`test_backend_features_with_timing.py`)
2. ⏳ Add per-feature timing tracking to `rag.py`
3. ⏳ Add OTel span attributes for each feature
4. ⏳ Add Prometheus metrics for each feature
5. ⏳ Run tests and validate all features have timing data
6. ⏳ Update UI to display per-feature timings
7. ⏳ Create Grafana dashboards for per-feature metrics

---

## Files to Update

1. `services/api/routes/rag.py` - Add per-feature timing tracking
2. `services/api/app.py` - Add Prometheus metrics
3. `tests/test_backend_features_with_timing.py` - Enhanced test suite
4. `frontend/src/components/chat/MessageItem.tsx` - Display per-feature timings
5. `frontend/src/components/metrics/MetricsPage.tsx` - Display per-feature metrics

---

## References

- [UI Defects List](../UI_DEFECTS_NOV_17_2025.md)
- [Backend Feature Tests](../../tests/test_backend_features_comprehensive.py)
- [RAG API Routes](../../services/api/routes/rag.py)

