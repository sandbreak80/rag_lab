# UI 502 Error - Root Cause Analysis & Fix

**Issue Reported:** http://16.146.148.184:3000/ shows:
- ❌ Chat response: 502 Error
- ❌ "Ollama not responding or no models available"
- ❌ "Error checking GPU status"

---

## 🔍 Root Cause Analysis

### Investigation Results:

**✅ Backend Services Status:**
```bash
# rag-api-v1 (NEW API)
curl http://16.146.148.184:8000/health
# Response: {"status":"healthy","live":true,"ready":true,"service":"rag-api","version":"1.0.0"}
# ✅ HEALTHY

# Ollama
curl http://16.146.148.184:11434/api/tags
# Response: 10 models loaded (llama3.1:8b, qwen2.5:14b, mistral:7b, etc.)
# ✅ HEALTHY
```

**❌ The Problem:**
The frontend container running on AWS still has the **OLD** `nginx.conf` that points to the non-existent `api-gateway:8000` service, causing 502 errors.

### Why This Happened:

1. **Code Updated in Repo** ✅
   - `frontend/nginx.conf` was updated to route to `rag-api-v1:8080`
   - Changes committed to `otel` branch
   - Code pushed to GitHub

2. **Frontend Container NOT Rebuilt** ❌
   - The running frontend container was built with OLD nginx.conf
   - It still tries to reach `api-gateway:8000` (doesn't exist)
   - Results in 502 Bad Gateway errors

3. **Backend Services Running Fine** ✅
   - `rag-api-v1` is healthy on port 8080 (internal)
   - `rag-api-v1` is accessible on port 8000 (external)
   - Ollama is healthy with 10 models loaded

---

## 🎯 The Fix

### What Needs to Happen:

**Rebuild the frontend container with the updated nginx.conf**

This will:
1. Pull latest code with updated `frontend/nginx.conf`
2. Rebuild frontend Docker image
3. Route `/api/*` → `rag-api-v1:8080` (correct)
4. Route health endpoints → `rag-api-v1:8080`
5. Eliminate 502 errors

---

## 🚀 How to Fix (Choose One Method)

### **Method 1: Automated Script (Recommended)**

```bash
# Run from local machine with SSH key
./scripts/fix-ui-emergency.sh
```

This script will:
- SSH to AWS instance
- Pull latest code
- Verify nginx config is correct
- Rebuild frontend (no cache)
- Start new frontend
- Test routing

### **Method 2: Manual Commands**

SSH to the AWS instance and run:

```bash
ssh -i your-key.pem ubuntu@16.146.148.184

# Pull latest code
cd /home/ubuntu/rag_lab
git pull origin otel

# Verify nginx config
grep "rag-api-v1:8080" frontend/nginx.conf
# Should see: proxy_pass http://rag-api-v1:8080;

# Rebuild frontend
docker compose stop frontend
docker compose rm -f frontend
docker compose build --no-cache frontend
docker compose up -d frontend

# Wait for startup
sleep 15

# Test
curl http://localhost:3000/live
# Should return: {"status":"alive","service":"rag-api","version":"1.0.0"}

# Test API
curl -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","user_id":"test","groups":[]}'
# Should return: JSON with answer, citations, etc.
```

### **Method 3: Quick Docker Commands**

If already SSH'd to the instance:

```bash
cd /home/ubuntu/rag_lab && \
git pull origin otel && \
docker compose up -d --build --force-recreate frontend
```

---

## ✅ Verification Steps

After deploying the fix:

### 1. Test Health Endpoint
```bash
curl http://16.146.148.184:3000/live
```

**Expected:**
```json
{
  "status": "alive",
  "service": "rag-api",
  "version": "1.0.0"
}
```

**NOT:**
```html
<!doctype html>...
```

### 2. Test API Endpoint
```bash
curl -X POST http://16.146.148.184:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"test","groups":[]}'
```

**Expected:** JSON response with `answer`, `citations`, `artifacts`, etc.

### 3. Test in Browser

Visit: http://16.146.148.184:3000

**Expected:**
- ✅ Homepage loads
- ✅ No 502 errors
- ✅ Chat works
- ✅ Ollama models listed
- ✅ GPU status shows correctly

**NOT:**
- ❌ 502 Bad Gateway
- ❌ "Ollama not responding"
- ❌ "Error checking GPU status"

---

## 📊 Before vs After

### **BEFORE (Current State - Broken)**

```
Browser → http://16.146.148.184:3000
   ↓
Frontend Container (OLD nginx.conf)
   ↓ tries to reach
api-gateway:8000 ❌ (doesn't exist)
   ↓
502 Bad Gateway Error
```

### **AFTER (Fixed)**

```
Browser → http://16.146.148.184:3000
   ↓
Frontend Container (NEW nginx.conf)
   ↓ proxies to
rag-api-v1:8080 ✅ (exists & healthy)
   ↓
200 OK with JSON response
```

---

## 🔧 Technical Details

### Current Frontend Nginx Config (on AWS - OLD)
```nginx
location /api/ {
    proxy_pass http://api-gateway:8000;  # ❌ Service doesn't exist
}
```

### Updated Frontend Nginx Config (in repo - NEW)
```nginx
location ~ ^/(live|ready|health)$ {
    proxy_pass http://rag-api-v1:8080;  # ✅ Correct
}

location /api/ {
    proxy_pass http://rag-api-v1:8080;  # ✅ Correct
    proxy_set_header traceparent $http_traceparent;
    proxy_set_header tracestate $http_tracestate;
}

location /metrics {
    proxy_pass http://rag-api-v1:8080/metrics;  # ✅ Correct
}
```

---

## 🐛 Why Ollama & GPU Errors Appear

The Ollama and GPU errors are **secondary effects** of the 502:

1. Frontend tries to check Ollama status via `/api/ollama/status`
2. Nginx routes to `api-gateway:8000` ❌
3. Gets 502 error
4. Frontend displays: "Ollama not responding"

**Reality:** Ollama IS responding fine on port 11434 with 10 models loaded!

Same for GPU status - the frontend can't reach the backend to get GPU info.

---

## 🎯 Why Backend Tests Passed But UI Failed

**Backend Tests:** Hit the API directly on port 8000
```bash
curl http://16.146.148.184:8000/v1/rag/query
# ✅ Works perfectly - that's what we tested
```

**UI:** Goes through frontend nginx on port 3000
```bash
Browser → http://16.146.148.184:3000 → Frontend Nginx → ❌ 502
```

**Lesson Learned:** Always test the ACTUAL user-facing URL, not just the internal services!

---

## 📋 Post-Fix Checklist

After running the fix script:

- [ ] Health endpoint returns JSON (not HTML)
- [ ] API endpoint returns RAG responses
- [ ] UI loads without 502 errors
- [ ] Chat functionality works
- [ ] Ollama models listed correctly
- [ ] GPU status displays correctly
- [ ] No console errors in browser
- [ ] Citations display with provenance
- [ ] Metrics accessible

---

## 🚀 Next Steps After Fix

1. **Verify UI Works**
   - Open http://16.146.148.184:3000
   - Ask a question in chat
   - Verify answer appears with citations

2. **Run Playwright E2E Tests**
   ```bash
   ./scripts/run-e2e-tests.sh http://16.146.148.184:3000
   ```

3. **Wire Frontend Components**
   - Follow `docs/FRONTEND_INTEGRATION_GUIDE.md`
   - Integrate new observability UI components

4. **Enable Full Observability**
   ```yaml
   RAG_ENABLE_OBS: "1"
   ```

5. **Flip Mocks Gradually**
   - Vector → Web → LLM
   - Test after each flip

---

## 📞 Support

If the fix doesn't work:

1. **Check Docker Logs:**
   ```bash
   docker compose logs frontend --tail 50
   docker compose logs rag-api-v1 --tail 50
   ```

2. **Verify Services Running:**
   ```bash
   docker compose ps
   ```

3. **Check Nginx Config in Container:**
   ```bash
   docker compose exec frontend cat /etc/nginx/conf.d/default.conf
   ```

4. **Restart All Services:**
   ```bash
   docker compose down
   docker compose up -d
   ```

---

**Summary:** The backend is healthy. The frontend just needs to be rebuilt with the updated nginx.conf. Run `./scripts/fix-ui-emergency.sh` to fix it!

