# Manual Validation Guide - UI Hardening Sprint

**AWS Instance:** http://16.146.148.184:3000
**Date:** 2025-11-12
**Branch:** otel (commit: 52aa462)

---

## ✅ PRE-VALIDATION CHECKLIST

- [x] All containers rebuilt with latest code
- [x] Frontend: rag_lab-frontend (Built 2025-11-12)
- [x] Backend: rag-api-v1:latest (Built 2025-11-12)
- [x] Services: All running and healthy
- [x] Endpoints: Responding correctly

---

## 🧪 VALIDATION TEST SCENARIOS

### UI-001: Chat Sources Merge (RAG + Web)

**What to Test:**
- Chat page shows sources from both RAG and Web search
- Sources have distinct badges (RAG vs Web)

**Steps:**
1. Navigate to http://16.146.148.184:3000
2. Enter query: "What is RAG and how does it work?"
3. Wait for response
4. Scroll to "Sources" section below answer

**Expected Results:**
- ✅ See multiple sources listed
- ✅ Some sources labeled "RAG" (from vector DB)
- ✅ Some sources labeled "Web" (from SearXNG)
- ✅ Each source has: title, snippet, score

**Testids:** `source-item`, `data-origin="rag"`, `data-origin="web"`

---

### UI-002: Performance Breakdown (Full Stack Timings)

**What to Test:**
- Chat response shows detailed timing breakdown
- All stages visible: vector, web, llm, total

**Steps:**
1. On chat page, submit any query
2. Wait for response
3. Look for "Performance" or timing section

**Expected Results:**
- ✅ See timing breakdown with vector, web, llm, total times

**Testids:** `perf-breakdown`

---

### UI-003: Document Upload

**What to Test:**
- File upload works without 422 errors
- Success message shows chunks indexed

**Steps:**
1. Navigate to http://16.146.148.184:3000/documents
2. Click upload area or drag a .txt file
3. Select a text file (>100 characters)
4. Wait for upload to complete

**Expected Results:**
- ✅ Upload succeeds (no 422 error)
- ✅ Success message: "Uploaded 1 files, X chunks indexed"

**Testids:** `upload-zone`, `upload-input`, `upload-error`

---

### UI-004: Research Sources in Chat

**What to Test:**
- Research sources appear with distinct styling
- Purple Sparkles icon for research results

**Steps:**
1. On chat page, submit query with research enabled
2. Check sources section for research results

**Expected Results:**
- ✅ See "Research" labeled sources
- ✅ Purple Sparkles icon next to research sources

**Testids:** `source-item` with `data-origin="research"`

---

### UI-005: Metrics Page Performance Breakdown

**What to Test:**
- Metrics page shows full stack timings
- All timing fields visible (not just LLM)

**Steps:**
1. Navigate to http://16.146.148.184:3000/metrics
2. Look for "Stage Timings" section
3. Verify all timing metrics are displayed

**Expected Results:**
- ✅ See timing cards for: Vector, Web, LLM, Total, Parallel, Skipped

**Testids:** `metrics-vector-ms`, `metrics-web-ms`, `metrics-llm-ms`, `metrics-total-ms`, `metrics-retrieve-parallel-ms`, `metrics-web-skipped-badge`

---

### UI-006: Monitoring Grafana Link

**What to Test:**
- Grafana link points to correct dashboard

**Steps:**
1. Navigate to http://16.146.148.184:3000/monitoring
2. Look for "Open Grafana" button/link
3. Click the link

**Expected Results:**
- ✅ Link opens Grafana dashboard at port 3001

**Testids:** `grafana-link`

---

### UI-007: Prompt Logs Tokens

**What to Test:**
- Prompt logs show non-zero token counts

**Steps:**
1. Submit queries on chat page
2. Navigate to prompt logs page
3. Check token columns

**Expected Results:**
- ✅ Token counts visible (not 0)
- ✅ Input tokens: typically 400-800
- ✅ Output tokens: typically 100-300

**Testids:** `promptlog-row`, `promptlog-model`, `promptlog-tokens-total`, `promptlog-tokens-in`, `promptlog-tokens-out`

---

### UI-008: Settings Testability

**What to Test:**
- Settings page has all toggles and sliders
- Backend endpoint returns current settings

**Steps:**
1. Navigate to http://16.146.148.184:3000/settings
2. Verify all controls are present

**Expected Results:**
- ✅ Temperature, Context, Top-K sliders visible
- ✅ Toggles for Prompt Enhancement, Vector DB, Web Search

**Testids:** `settings-temperature`, `settings-context`, `settings-topk`, `settings-prompt-enhancement`, `settings-vector-db`, `settings-web-search`

---

## 📊 BACKEND API VALIDATION

### Quick API Health Check (from AWS):

```bash
# Health endpoint
curl http://localhost:3000/api/health

# Settings GET
curl http://localhost:3000/api/v1/settings

# RAG Query
curl -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"Test","user_id":"demo","groups":["public"]}'

# Document Upload
curl -X POST http://localhost:3000/api/v1/documents \
  -F "files=@test_upload_long.txt" \
  -F "perms_tag=public"
```

---

## ✅ VALIDATION CHECKLIST

### UI Tests:
- [ ] UI-001: Chat shows RAG + Web sources
- [ ] UI-002: Performance breakdown visible
- [ ] UI-003: Document upload succeeds
- [ ] UI-004: Research sources render
- [ ] UI-005: Metrics page shows all timings
- [ ] UI-006: Grafana link works
- [ ] UI-007: Prompt logs show tokens
- [ ] UI-008: Settings page complete

### API Tests:
- [ ] GET /api/health → 200
- [ ] GET /api/v1/settings → 200
- [ ] POST /api/v1/rag/query → 200
- [ ] POST /api/v1/documents → 201

### Browser Tests:
- [ ] No console errors
- [ ] All testids present
- [ ] Pages load correctly

---

## 🎯 SUCCESS CRITERIA

**Sprint validated when:**
1. ✅ All 8 UI issues manually verified
2. ✅ All API endpoints return expected responses
3. ✅ No console errors in browser
4. ✅ All testids present

---

**Validation Date:** _____________
**Validated By:** _____________
**Status:** [ ] PASS  [ ] FAIL


