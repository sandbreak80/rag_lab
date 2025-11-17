# UI Defects and Backend Test Requirements
**Date:** November 17, 2025
**Environment:** http://16.146.36.90:3000/
**Branch:** otel

## Overview
This document tracks UI defects and corresponding backend test requirements to validate functionality.

---

## 🔴 Chat Page Defects

### 1. Chat Response Lost on Navigation/Refresh
**Severity:** High
**Description:** When user submits a chat query and then navigates away or refreshes the page, the response never makes it to the UI.

**Backend Test Required:**
- [ ] Test that API response is returned even if client disconnects
- [ ] Test response persistence/caching mechanism
- [ ] Test WebSocket/SSE connection handling
- [ ] Validate response is stored and can be retrieved after page refresh

**Files to Check:**
- `services/rag_api_v1/`
- `frontend/src/services/api.ts`
- `frontend/src/components/chat/ChatInterface.tsx`

---

### 2. Performance Breakdown Missing Full End-to-End Performance
**Severity:** Medium
**Description:** The performance breakdown section doesn't show complete end-to-end performance metrics.

**Backend Test Required:**
- [ ] Validate all stage timings are captured (query expansion, vector search, BM25, hybrid fusion, reranking, LLM generation)
- [ ] Test that total latency includes all stages
- [ ] Verify timing data flows to frontend correctly
- [ ] Check OTel trace spans for all stages

**Files to Check:**
- `services/rag_api_v1/`
- `frontend/src/components/chat/MessageItem.tsx`
- `frontend/src/types/chat.ts`

---

### 3. Sources Missing Expected Types
**Severity:** High
**Description:** Expected to see sources from RAG, Web Search, Knowledge Graph, and Research Agent documents. Currently not showing all expected source types.

**Backend Test Required:**
- [ ] Test RAG source retrieval and citation
- [ ] Test Web Search source retrieval and citation
- [ ] Test Knowledge Graph source retrieval and citation
- [ ] Test Research Agent document sources
- [ ] Validate `origin_tool` field in citations
- [ ] Test that all enabled features return sources

**Files to Check:**
- `services/rag_api_v1/`
- `services/search_service/`
- `services/knowledge_graph/`
- `services/research_agent/`

---

### 4. View Trace in Grafana Link Broken
**Severity:** Medium
**Description:** The "View Trace in Grafana" link is broken.

**Backend Test Required:**
- [ ] Validate trace_id is returned in API response
- [ ] Test trace_id format and validity
- [ ] Verify Grafana trace URL construction
- [ ] Test trace_id links to correct Grafana dashboard

**Files to Check:**
- `frontend/src/components/chat/MessageItem.tsx`
- `frontend/src/components/MetricsRow.tsx`
- `services/rag_api_v1/` (trace_id generation)

---

## 🔴 Documents Page Defects

### 1. Empty Document List
**Severity:** High
**Description:** "Your Documents" section shows empty list even when documents are uploaded.

**Backend Test Required:**
- [ ] Test document upload API endpoint
- [ ] Test document list/retrieval API endpoint
- [ ] Validate document storage and retrieval
- [ ] Test document metadata persistence
- [ ] Check database/document store connectivity

**Files to Check:**
- `services/document_service/`
- `services/rag_api_v1/endpoints/documents.py`
- `frontend/src/components/documents/DocumentsPage.tsx`

---

### 2. Missing Pagination
**Severity:** Medium
**Description:** Document list needs pagination for large document sets.

**Backend Test Required:**
- [ ] Test pagination API parameters (page, limit, offset)
- [ ] Validate pagination response format
- [ ] Test pagination with large document sets
- [ ] Verify total count is returned

**Files to Check:**
- `services/document_service/`
- `services/rag_api_v1/endpoints/documents.py`

---

### 3. Document Names Not Truncated
**Severity:** Low
**Description:** Long document names bleed outside page margins.

**Backend Test Required:**
- [ ] Test document name length limits
- [ ] Validate truncation logic (if backend handles it)
- [ ] Test with very long document names

**Files to Check:**
- `frontend/src/components/documents/DocumentsPage.tsx` (frontend fix)

---

## 🔴 Settings Page Defects

### 1. Quick Presets Selection Not Persisted
**Severity:** High
**Description:** Quick Presets selection doesn't show which preset is selected and doesn't persist across navigation/refresh.

**Backend Test Required:**
- [ ] Test preset storage/retrieval API
- [ ] Validate preset persistence mechanism
- [ ] Test preset application to query settings
- [ ] Verify preset state is returned in settings API

**Files to Check:**
- `services/rag_api_v1/endpoints/settings.py`
- `frontend/src/components/settings/SettingsPanel.tsx`
- `frontend/src/services/api.ts`

---

## 🔴 Backend Feature Validation Tests Required

### A. Security Guardrails
**Test Requirements:**
- [ ] Test PII detection and redaction
- [ ] Test prompt injection detection
- [ ] Test content filtering
- [ ] Validate security violations are logged
- [ ] Test security metrics in OTel traces

---

### B. Query Expansion
**Test Requirements:**
- [ ] Test query expansion is applied when enabled
- [ ] Validate expanded query is used in search
- [ ] Test expansion timing is tracked
- [ ] Verify expansion can be disabled
- [ ] Test expansion metrics in OTel

---

### C. BM25 Search
**Test Requirements:**
- [ ] Test BM25 search returns results
- [ ] Validate BM25 can be enabled/disabled
- [ ] Test BM25 timing is tracked
- [ ] Verify BM25 results are included in citations
- [ ] Test BM25 metrics in OTel

---

### D. Hybrid Search
**Test Requirements:**
- [ ] Test hybrid search combines vector + BM25
- [ ] Validate fusion algorithm works correctly
- [ ] Test hybrid search timing
- [ ] Verify hybrid results are properly ranked
- [ ] Test hybrid metrics in OTel

---

### E. Knowledge Graph
**Test Requirements:**
- [ ] Test knowledge graph query execution
- [ ] Validate KG results are returned
- [ ] Test KG timing is tracked
- [ ] Verify KG sources appear in citations
- [ ] Test KG can be enabled/disabled
- [ ] Test KG metrics in OTel

---

### F. LLM Re-ranking
**Test Requirements:**
- [ ] Test re-ranking is applied to results
- [ ] Validate re-ranking improves result order
- [ ] Test re-ranking timing is tracked
- [ ] Verify re-ranking can be disabled
- [ ] Test re-ranking metrics in OTel

---

### G. Web Search
**Test Requirements:**
- [ ] Test web search is executed when enabled
- [ ] Validate web search results are returned
- [ ] Test web search timing is tracked
- [ ] Verify web sources appear in citations
- [ ] Test web search can be enabled/disabled
- [ ] Test web search metrics in OTel
- [ ] **CRITICAL:** Currently not showing web sources in chat results

---

### H. Agentic Chunking
**Test Requirements:**
- [ ] Test agentic chunking is applied
- [ ] Validate chunk quality and boundaries
- [ ] Test chunking timing is tracked
- [ ] Verify chunking can be enabled/disabled
- [ ] Test chunking metrics in OTel

---

### I. Top-K Results
**Test Requirements:**
- [ ] Test Top-K setting limits result count
- [ ] Validate different Top-K values (5, 10, 20, etc.)
- [ ] Test Top-K applies to all search types
- [ ] Verify Top-K setting is persisted
- [ ] Test Top-K metrics in OTel

---

### J. Prompt Enhancement
**Test Requirements:**
- [ ] Test prompt enhancement is applied
- [ ] Validate enhanced prompt improves results
- [ ] Test enhancement timing is tracked
- [ ] Verify enhancement can be disabled
- [ ] Test enhancement metrics in OTel

---

### K. Auto Model Routing
**Test Requirements:**
- [ ] Test model routing selects appropriate model
- [ ] Validate routing logic (query complexity, model availability)
- [ ] Test routing timing is tracked
- [ ] Verify routing can be disabled
- [ ] Test routing metrics in OTel

---

### L. Query Decomposition
**Test Requirements:**
- [ ] Test query decomposition splits complex queries
- [ ] Validate sub-queries are executed
- [ ] Test decomposition timing is tracked
- [ ] Verify decomposition can be disabled
- [ ] Test decomposition metrics in OTel

---

### M. Self-RAG
**Test Requirements:**
- [ ] Test Self-RAG retrieval and generation loop
- [ ] Validate Self-RAG improves answer quality
- [ ] Test Self-RAG timing is tracked
- [ ] Verify Self-RAG can be enabled/disabled
- [ ] Test Self-RAG metrics in OTel

---

### N. Show Reasoning Process
**Test Requirements:**
- [ ] Test reasoning process is captured
- [ ] Validate reasoning is returned in response
- [ ] Test reasoning timing is tracked
- [ ] Verify reasoning can be enabled/disabled
- [ ] Test reasoning metrics in OTel

---

### O. Vector Database
**Test Requirements:**
- [ ] Test vector search execution
- [ ] Validate vector search returns results
- [ ] Test vector search timing is tracked
- [ ] Verify vector DB can be enabled/disabled
- [ ] Test vector DB metrics in OTel

---

### P. Research Agent
**Test Requirements:**
- [ ] Test research agent execution
- [ ] Validate research agent returns documents
- [ ] Test research agent timing is tracked
- [ ] Verify research agent sources appear in citations
- [ ] Test research agent can be enabled/disabled
- [ ] Test research agent metrics in OTel

---

### Q. Web Search (Duplicate - see G)
**Note:** Listed twice in requirements. Same tests as G.

---

### R. Knowledge Graph (Duplicate - see E)
**Note:** Listed twice in requirements. Same tests as E.

---

## 📊 Timing Tracking Requirements

### OTel Integration
- [ ] Each feature (A-R) must emit OTel spans with timing data
- [ ] Spans must include: start time, end time, duration
- [ ] Spans must be linked to parent trace
- [ ] Feature enable/disable state must be in span attributes

### Grafana Integration
- [ ] Timing data must be queryable in Grafana
- [ ] Dashboard must show per-feature timing breakdown
- [ ] Timing trends over time must be visible
- [ ] Feature usage statistics must be available

### Performance Data in Chat
- [ ] Performance breakdown must show all feature timings
- [ ] Total latency must include all enabled features
- [ ] Individual feature timings must be visible
- [ ] Timing data must persist in message metadata

### Performance Data in Metrics Page
- [ ] Metrics page must show aggregate timing statistics
- [ ] Per-feature average timings must be displayed
- [ ] Timing distributions must be visible
- [ ] Feature usage frequency must be shown

---

## 🧪 Test Implementation Plan

### Phase 1: Backend API Tests
1. Create comprehensive test suite for all features (A-R)
2. Test feature enable/disable functionality
3. Test timing capture for each feature
4. Test source/citation generation for each feature

### Phase 2: Integration Tests
1. Test OTel span generation for each feature
2. Test timing data flow to Grafana
3. Test performance data in API responses
4. Test feature combinations

### Phase 3: End-to-End Tests
1. Test complete query flow with all features
2. Test timing data in frontend
3. Test Grafana trace links
4. Test performance breakdown display

---

## 📝 Notes

- **Web Search Critical Issue:** User reports no web sources showing in chat results. This needs immediate investigation.
- **Timing Tracking:** All features must have timing data tracked and visible in OTel, Grafana, and UI.
- **Feature Validation:** User suspects 50% of features may not be working. Comprehensive testing required.

---

## ✅ Test Status

- [ ] All backend tests created
- [ ] All backend tests passing
- [ ] OTel integration verified
- [ ] Grafana integration verified
- [ ] Frontend timing display verified
- [ ] All defects fixed

