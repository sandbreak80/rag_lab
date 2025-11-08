# Complete E2E Fix, Test, and Feature Flip Guide

**Goal:** Fix nginx routing, prove E2E works through port 3000, then progressively flip features.

---

## 🎯 Overview

### What We're Fixing:
- ❌ Frontend nginx routing to wrong service (api-gateway → rag-api-v1)
- ❌ Tests hitting backend directly (port 8000) instead of through frontend (port 3000)
- ❌ No E2E validation before declaring success

### What Success Looks Like:
- ✅ Frontend nginx routes `/api/*` → `rag-api-v1:8080`
- ✅ Health endpoints return JSON (not HTML)
- ✅ API calls through port 3000 work perfectly
- ✅ Full E2E tests pass
- ✅ Features flipped progressively with testing gates

---

## 📋 Step-by-Step Execution

### **Step 0: Pull Latest Code**

```bash
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel
```

### **Step 1: Verify Configuration**

**Check frontend nginx.conf:**
```bash
grep "rag-api-v1:8080" frontend/nginx.conf
# Should see: proxy_pass http://rag-api-v1:8080;
```

**Check docker-compose.yml:**
```bash
grep "NEXT_PUBLIC_RAG_API" docker-compose.yml
# Should see: NEXT_PUBLIC_RAG_API=/api
```

If either is missing, the files in the repo are correct - just need to rebuild.

### **Step 2: Rebuild Frontend with New Nginx Config**

```bash
# Stop and remove old containers
docker compose stop rag-api-v1 frontend
docker compose rm -f rag-api-v1 frontend

# Rebuild frontend (no cache to ensure new nginx.conf)
docker compose build --no-cache frontend

# Start services
docker compose up -d rag-api-v1 frontend

# Wait for startup
sleep 15
```

### **Step 3: Sanity Checks (Port 3000 - CRITICAL!)**

**Test 1: Homepage loads**
```bash
curl -sSf http://16.146.148.184:3000 | head -5
# Should see: <!doctype html>
```

**Test 2: Health endpoints return JSON (NOT HTML!)**
```bash
curl -sSf http://16.146.148.184:3000/live | jq
# Should see: {"status":"alive","service":"rag-api","version":"1.0.0"}
# NOT: <!doctype html>...

curl -sSf http://16.146.148.184:3000/ready | jq
# Should see: {"status":"ready",...}
```

**Test 3: API endpoint works**
```bash
curl -sSf -X POST http://16.146.148.184:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"demo","groups":[]}' | jq
  
# Should see: { "answer": "...", "citations": [...], ... }
# NOT: 502 Bad Gateway
```

### **Step 4: Run Frontend Integration Tests**

**Use the new test suite that hits port 3000:**

```bash
export FRONTEND=http://16.146.148.184:3000
python3 tests/frontend_integration/test_frontdoor.py
```

**Expected output:**
```
✅ Homepage loads: PASS
✅ Health /live: PASS
✅ Health /ready: PASS
✅ Health /health: PASS
✅ API via /api: PASS
✅ API - Answer: PASS
✅ API - Citations: PASS
✅ API - Trace ID: PASS
✅ CORS not needed: PASS
✅ Golden Query: PASS
✅ E2E Latency: PASS

🎉 ALL FRONTEND INTEGRATION TESTS PASSED!
```

---

## 🐛 Debugging (If Tests Fail)

### **Issue: Health endpoints return HTML**

**Symptom:**
```bash
curl http://16.146.148.184:3000/live
# Returns: <!doctype html>...
```

**Cause:** Nginx not proxying health endpoints correctly

**Fix:**
```bash
# Check if nginx can reach the API internally
docker compose exec frontend curl -sS http://rag-api-v1:8080/live

# Check DNS resolution
docker compose exec frontend getent hosts rag-api-v1

# Check nginx config in container
docker compose exec frontend cat /etc/nginx/conf.d/default.conf | grep rag-api-v1

# If config is wrong, rebuild
docker compose build --no-cache frontend
docker compose up -d frontend
```

### **Issue: API returns 502**

**Symptom:**
```bash
curl http://16.146.148.184:3000/api/v1/rag/query ...
# Returns: 502 Bad Gateway
```

**Cause:** Nginx can't reach `rag-api-v1:8080`

**Fix:**
```bash
# Check if rag-api-v1 is running
docker compose ps rag-api-v1

# Check logs
docker compose logs --tail 50 rag-api-v1

# Test direct access
curl http://localhost:8080/live

# Verify both services on same network
docker compose exec frontend ping -c 2 rag-api-v1

# Restart both services
docker compose restart frontend rag-api-v1
```

### **Issue: Still getting old behavior**

**Cause:** Docker cached the old frontend image

**Fix:**
```bash
# Nuclear option - remove everything and rebuild
docker compose down
docker system prune -f
docker compose build --no-cache
docker compose up -d
```

---

## 🚀 Step 5: Progressive Feature Flipping

**Once all E2E tests pass, flip features ONE AT A TIME:**

### **Automated Approach (Recommended):**

```bash
./scripts/flip-features-progressive.sh
```

This script will:
1. Flip each feature
2. Run tests after each flip
3. Stop if any test fails
4. Provide rollback instructions

### **Manual Approach:**

**Flip 1: Enable Observability**
```bash
# Update docker-compose.yml
# Change: RAG_ENABLE_OBS: "0"
# To:     RAG_ENABLE_OBS: "1"

docker compose up -d rag-api-v1
sleep 10

# Test
python3 tests/frontend_integration/test_frontdoor.py
```

**Flip 2: Real Vector Search**
```bash
# Change: RAG_USE_MOCK_VECTOR: "1"
# To:     RAG_USE_MOCK_VECTOR: "0"

docker compose up -d rag-api-v1
sleep 10

# Test
python3 tests/frontend_integration/test_frontdoor.py
```

**Flip 3: Real Web Search**
```bash
# Change: RAG_USE_MOCK_WEB: "1"
# To:     RAG_USE_MOCK_WEB: "0"

docker compose up -d rag-api-v1
sleep 10

# Test
python3 tests/frontend_integration/test_frontdoor.py
```

**Flip 4: Real LLM**
```bash
# Change: RAG_USE_MOCK_LLM: "1"
# To:     RAG_USE_MOCK_LLM: "0"

docker compose up -d rag-api-v1
sleep 10

# Test
python3 tests/frontend_integration/test_frontdoor.py
```

**CRITICAL:** Run tests after EACH flip. If any fail, rollback that flag and debug.

---

## ✅ Final Validation

After all features are flipped:

### **1. Run Full Test Suite**
```bash
# Frontend integration
export FRONTEND=http://16.146.148.184:3000
python3 tests/frontend_integration/test_frontdoor.py

# Acceptance tests (through frontend)
export RAG_API=http://16.146.148.184:3000/api
python3 -m pytest tests/test_acceptance_full_contract.py -v
```

### **2. Manual Browser Test**

Open: http://16.146.148.184:3000

**Test:**
1. Ask: "What is RAG?"
2. Verify: Answer appears (no 502 error)
3. Check: Citations display
4. Verify: Ollama models listed
5. Check: GPU status shows
6. Verify: No console errors

### **3. Performance Check**
```bash
# Should be <10s
time curl -X POST http://16.146.148.184:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","user_id":"perf","groups":[]}'
```

### **4. Metrics Check**
```bash
curl http://16.146.148.184:3000/metrics | grep gqs
# Should see: gqs_p95_latency_seconds, gqs_citation_rate, etc.
```

---

## 📊 Success Criteria

| Test | Target | How to Verify |
|------|--------|---------------|
| Frontend loads | 200 OK | `curl http://16.146.148.184:3000` |
| Health = JSON | Not HTML | `curl .../live \| jq` |
| API works | No 502 | `curl .../api/v1/rag/query` |
| E2E tests | 11/11 pass | `python3 tests/frontend_integration/test_frontdoor.py` |
| Acceptance | 8/8 pass | `pytest tests/test_acceptance_full_contract.py` |
| Browser works | No errors | Manual test in browser |
| Features flipped | All 4 | Check docker-compose.yml |

---

## 🔧 Quick Reference Commands

```bash
# Fix and test (all-in-one)
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel
./scripts/fix-and-test-e2e.sh

# Just rebuild frontend
docker compose up -d --build --force-recreate frontend

# Test frontend integration
export FRONTEND=http://16.146.148.184:3000
python3 tests/frontend_integration/test_frontdoor.py

# Flip features progressively
./scripts/flip-features-progressive.sh

# Check service status
docker compose ps
docker compose logs frontend --tail 50
docker compose logs rag-api-v1 --tail 50

# Emergency rollback
docker compose down
git checkout main
docker compose up -d
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `scripts/fix-and-test-e2e.sh` | Automated fix and sanity checks |
| `tests/frontend_integration/test_frontdoor.py` | Test port 3000 (full stack) |
| `scripts/flip-features-progressive.sh` | Progressive feature flipping with gates |
| `docs/COMPLETE_E2E_GUIDE.md` | This guide |

---

## 🎯 Timeline

| Phase | Time | Description |
|-------|------|-------------|
| Step 0-2 | 5 min | Pull code, rebuild frontend |
| Step 3 | 2 min | Sanity checks |
| Step 4 | 5 min | Run E2E tests |
| Step 5 | 30 min | Flip features (one at a time) |
| Validation | 10 min | Final checks |
| **Total** | **~50 min** | From broken UI to production-ready |

---

## 🚨 Rollback Plan

If anything breaks:

```bash
# Rollback feature flag
# Edit docker-compose.yml, change flag back to "1" or "0"
docker compose up -d rag-api-v1

# Rollback code
git checkout HEAD~1
docker compose up -d --build

# Nuclear rollback
docker compose down
git checkout main
docker compose up -d
```

---

**Ready to execute! Start with Step 0 and work through sequentially.** 🚀

