# Running E2E Tests - Quick Reference

## ✅ **Correct Approach: Run on AWS Instance**

The E2E tests are designed to run **on the AWS instance** where the application is deployed.

### **Why Run on AWS?**
- ✅ Application is already deployed there
- ✅ All services are running (frontend, API, Ollama, vector DB, etc.)
- ✅ Tests use `network_mode: "host"` to access local services
- ✅ `BASE_URL` points to `http://16.146.148.184:3000`
- ✅ Docker test container can access everything

---

## 🚀 **How to Run (Step by Step)**

### **1. SSH to AWS Instance**
```bash
ssh ubuntu@16.146.148.184
```

### **2. Navigate to Repository**
```bash
cd /home/ubuntu/rag_lab
```

### **3. Run the Test Script**
```bash
bash scripts/run_e2e_tests.sh
```

**The script will**:
1. Pull latest code from `otel` branch
2. Rebuild and deploy `rag-api-v1` + `frontend`
3. Wait for services to be healthy (30s)
4. Run sanity checks (`/ready`, `/live`)
5. Execute Playwright E2E tests in Docker container
6. Generate HTML + JUnit reports
7. Show test summary

---

## 📊 **View Test Results**

### **Option 1: View HTML Report (Recommended)**
```bash
# On AWS instance
cd /home/ubuntu/rag_lab
python3 -m http.server -d tests/e2e/playwright-report 8888 &

# Then on your local machine, open:
# http://16.146.148.184:8888/
```

**Features**:
- Interactive test results
- Screenshots of failures
- Video recordings (if any failures)
- Trace viewer for debugging
- Network logs

### **Option 2: View JUnit XML (CI/CD)**
```bash
cat tests/e2e/playwright-report/results.xml
```

### **Option 3: Check Console Output**
The script shows a summary:
```
Test Summary:
  Total: 16
  Failures: 3
  Errors: 0
```

---

## 📁 **Test Infrastructure**

### **Docker Test Container**
- **Location**: `tests/e2e/docker-compose.e2e.yml`
- **Image**: `mcr.microsoft.com/playwright:v1.48.0-jammy`
- **Network**: `host` mode (accesses local services)
- **Target**: `http://16.146.148.184:3000`

### **Test Specs (16 total)**
```
tests/e2e/specs/
├── 00_home.spec.ts                    # Homepage loads
├── 01_health_via_frontend.spec.ts     # Health endpoints
├── 02_chat_happy_path.spec.ts         # Chat functionality
├── 02_chat_sources.spec.ts            # Sources panel
├── 03_chat_perf_breakdown.spec.ts     # Performance data
├── 03_provenance_and_citations.spec.ts # Provenance badges
├── 04_metrics_and_trace.spec.ts       # Metrics row
├── 04_uploads.spec.ts                 # Document upload
├── 05_json_artifacts_download.spec.ts # JSON download
├── 05_research_agent.spec.ts          # Research agent
├── 06_guardrail_degradation.spec.ts   # Guardrails
├── 06_monitoring.spec.ts              # Monitoring graphs
├── 07_nginx_rewrite_and_cors.spec.ts  # Nginx routing
├── 07_performance_budget.spec.ts      # < 3.5s SLO
├── 08_accessibility.spec.ts           # A11y scanning
└── 08_perf_smoke.spec.ts              # Performance smoke
```

---

## 🐛 **Troubleshooting**

### **Issue**: Tests fail to start

**Check**:
```bash
# Are services running?
docker ps | grep -E "frontend|rag-api"

# Are they healthy?
curl http://localhost:3000/ready
curl http://localhost:3000/live
```

**Fix**:
```bash
docker compose up -d --build rag-api-v1 frontend
sleep 30
```

---

### **Issue**: "Failed to pull image"

**Check**:
```bash
docker pull mcr.microsoft.com/playwright:v1.48.0-jammy
```

**Fix**: Internet connectivity issue or Docker Hub rate limit. Wait and retry.

---

### **Issue**: Tests timeout

**Cause**: Services taking too long to respond (LLM slow, vector search slow)

**Fix**:
1. Check if faster model is configured:
   ```bash
   docker logs rag-api-v1 | grep "RAG_LLM_MODEL"
   # Should show: llama3.2:3b
   ```
2. Increase timeout in `playwright.config.ts`:
   ```typescript
   timeout: 90_000, // 90 seconds
   ```

---

### **Issue**: Blank monitoring graphs

**Check**:
```bash
curl http://localhost:3000/prom/-/ready
curl http://localhost:3000/graf/
```

**Fix**: Ensure Prometheus/Grafana proxies are configured in `frontend/nginx.conf`

---

## 🔄 **Re-running Tests**

### **Quick Re-run** (no rebuild)
```bash
cd /home/ubuntu/rag_lab
docker compose -f tests/e2e/docker-compose.e2e.yml up --abort-on-container-exit
```

### **Full Re-run** (with rebuild)
```bash
cd /home/ubuntu/rag_lab
bash scripts/run_e2e_tests.sh
```

### **Run Specific Test**
```bash
cd /home/ubuntu/rag_lab/tests/e2e
docker run --rm \
  --network host \
  -v $PWD:/workspace/tests/e2e \
  -w /workspace/tests/e2e \
  -e BASE_URL=http://16.146.148.184:3000 \
  mcr.microsoft.com/playwright:v1.48.0-jammy \
  bash -c "npm install && npx playwright test specs/02_chat_sources.spec.ts"
```

---

## 📈 **Expected Results**

### **First Run (Expected Failures)**
Some tests may fail initially because:
- ❌ Sources panel empty (backend not returning `retrieval_log`)
- ❌ Performance breakdown missing (backend not returning `metrics.breakdown`)
- ❌ Document upload UI not yet implemented
- ❌ Research agent UI not yet implemented
- ❌ Monitoring graphs not yet wired

**This is GOOD!** The tests are **catching real defects**.

### **After Fixes**
- ✅ All 16 tests should pass
- ✅ P95 latency < 3.5s
- ✅ No accessibility violations
- ✅ All endpoints return 200

---

## 📝 **Next Steps After Running Tests**

1. **Review HTML report** to see which tests failed
2. **Check screenshots** to see exact UI state at failure
3. **Fix issues** based on test error messages
4. **Re-run tests** to verify fixes
5. **Iterate** until all tests pass

---

## 🎯 **Summary**

| Question | Answer |
|----------|--------|
| **Where to run?** | AWS instance (`ubuntu@16.146.148.184`) |
| **How to run?** | `bash scripts/run_e2e_tests.sh` |
| **How long?** | ~2-5 minutes (depends on LLM speed) |
| **What gets tested?** | 16 E2E specs covering all pages + contracts |
| **Reports?** | `tests/e2e/playwright-report/index.html` |
| **View reports?** | `python3 -m http.server 8888` |

---

**Ready to run?**
```bash
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
bash scripts/run_e2e_tests.sh
```

