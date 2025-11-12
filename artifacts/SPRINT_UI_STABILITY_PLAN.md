# Sprint: UI & Stability Hardening

**Date:** 2025-11-12
**Branch:** otel
**Status:** 🎯 **READY TO EXECUTE**

---

## 🔍 **ROOT CAUSE ANALYSIS: Citations=0**

### Problem
RAG queries return `citations=[]` despite vector search working.

### Root Cause
**Vector database is EMPTY** - no documents have been uploaded to ChromaDB.

### Evidence
```json
{
  "documents": [],
  "total": 0,
  "message": "Document listing not yet implemented"
}
```

### Solution
**Upload sample documents** before testing RAG pipeline.

---

## 📋 **SPRINT TASKS**

### **Track C: Pipeline Regression Fix** (BLOCKING)

#### C1. Upload Sample Documents ⚠️ **CRITICAL**
**Tasks:**
1. Upload `sample_rag_basics.txt` (exists in repo)
2. Upload additional test documents
3. Verify documents are indexed in ChromaDB
4. Test RAG query returns citations

**Acceptance:**
- ≥3 documents uploaded
- RAG query returns ≥1 citation
- `evidence_map.citations` not empty

**Commands:**
```bash
# Upload sample document
curl -X POST http://localhost:3000/api/v1/documents \
  -F "file=@sample_rag_basics.txt" \
  -F "perms_tag=public" \
  -F "metadata={\"title\":\"RAG Basics\",\"author\":\"system\"}"

# Verify upload
curl http://localhost:3000/api/v1/documents

# Test query
curl -X POST http://localhost:3000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is RAG?","user_id":"test","groups":["public"]}'
```

**Artifacts:**
- `artifacts/c1-documents-uploaded.json`
- `artifacts/c1-rag-test-response.json`

---

#### C2. Threshold Tuning
**Tasks:**
1. Lower `RAG_EARLYSTOP_MIN_SCORE` from 0.60 → 0.40
2. Run 50-query canary test
3. Measure skip rate

**Acceptance:**
- Early-stop triggers >30% of queries
- Citations still present in responses

**Artifacts:**
- `artifacts/c2-early-stop-50q.json`
- `artifacts/c2-skip-rate-summary.txt`

---

### **Track A: UI Reliability**

#### A1. Research Page
**Tasks:**
1. Verify feature flag behavior (VITE_RESEARCH_ENABLED=false)
2. Test placeholder renders with `data-testid="research-disabled"`
3. Run Playwright spec

**Acceptance:**
- Page loads without console errors
- Playwright: 3/3 tests pass

**Artifacts:**
- `artifacts/a1-research-screenshot.png`
- `tests/e2e/playwright-report/index.html`

---

#### A2. Metrics / Monitoring Views
**Tasks:**
1. Verify all `data-testid` selectors present
2. Test Grafana link (direct, not iframe)
3. Verify Prometheus metrics load

**Acceptance:**
- 5/5 metrics tests green
- Grafana link resolves 200

**Artifacts:**
- `artifacts/a2-metrics-screenshot.png`
- `artifacts/a2-monitoring-screenshot.png`

---

#### A3. Settings & Layout
**Tasks:**
1. Test all toggles clickable (no z-index issues)
2. Verify theme toggle works
3. Verify OTel toggle (when enabled)

**Acceptance:**
- 3/3 settings tests pass
- No console errors

**Artifacts:**
- `artifacts/a3-settings-screenshot.png`

---

#### A4. Accessibility & Mount
**Tasks:**
1. Verify `data-testid="root-mounted"` present
2. Run Lighthouse accessibility audit
3. Fix any critical issues

**Acceptance:**
- Lighthouse accessibility ≥90
- No critical a11y violations

**Artifacts:**
- `artifacts/a4-lighthouse-report.json`

---

### **Track B: E2E & Regression Coverage**

#### B1. Full Playwright Suite
**Tasks:**
1. Run all specs (not just core)
2. Fix flaky tests (add waits, improve selectors)
3. Target ≥18/21 passing

**Acceptance:**
- ≥18/21 tests passing
- No timeout failures

**Artifacts:**
- `tests/e2e/playwright-report/index.html`
- `artifacts/b1-e2e-summary.json`

---

#### B2. Visual & Console Check
**Tasks:**
1. Capture screenshots of all 6 pages
2. Check browser console for errors
3. Store in `artifacts/ui-proof/`

**Acceptance:**
- No console errors on any page
- Screenshots committed

**Artifacts:**
- `artifacts/ui-proof/home.png`
- `artifacts/ui-proof/chat.png`
- `artifacts/ui-proof/documents.png`
- `artifacts/ui-proof/research.png`
- `artifacts/ui-proof/settings.png`
- `artifacts/ui-proof/metrics.png`
- `artifacts/ui-proof/monitoring.png`

---

#### B3. Frontend Telemetry
**Tasks:**
1. Set `VITE_ENABLE_OTEL=true` in staging
2. Make a request and verify trace
3. Check Tempo for frontend → backend trace

**Acceptance:**
- Trace visible in Tempo
- `rag-lab-frontend` → `rag-api` span chain

**Artifacts:**
- `artifacts/b3-tempo-trace-screenshot.png`
- `artifacts/b3-otel-verification.txt`

---

## ✅ **ACCEPTANCE CRITERIA**

1. ✅ **UI:** All 6 pages render without console errors
2. ✅ **E2E:** ≥18/21 tests passing
3. ✅ **RAG Pipeline:** citations >0 for vector queries
4. ✅ **Telemetry:** Frontend trace → backend trace confirmed
5. ✅ **Docs:** This file updated with all proof artifacts

---

## 📅 **EXECUTION ORDER**

**Day 1:**
1. C1: Upload sample documents (30 min)
2. C2: Threshold tuning (30 min)
3. A1-A4: UI reliability fixes (4 hours)

**Day 2:**
4. B1: Full E2E suite (3 hours)
5. B2: Visual & console check (2 hours)
6. B3: Telemetry validation (1 hour)

**Day 3:**
7. Final report & artifacts (2 hours)

---

## 🚀 **NEXT STEPS**

**IMMEDIATE:** Execute C1 (upload documents) to unblock RAG pipeline.

**Status:** Ready to begin execution.

