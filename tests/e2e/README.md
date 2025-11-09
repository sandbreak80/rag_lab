# RAG Lab E2E Test Suite

**Production-grade Playwright tests** for validating the full UI → Backend integration.

## 🎯 What We Test

This suite catches **real UI defects** that unit tests miss:

| Test | What It Catches | Common Failures |
|------|----------------|-----------------|
| **02_chat_sources** | Sources panel populated with valid links | Empty sources, missing `source_uri`, broken retrieval_log |
| **03_chat_perf_breakdown** | Performance timing data visible | "No timing data available", missing `metrics.breakdown` |
| **04_uploads** | Document upload endpoint works | 404 errors, missing nginx route, upload failures |
| **05_research_agent** | Agent UI responds correctly | Fetch errors, 404 endpoints, missing service |
| **06_monitoring** | Prom/Grafana graphs load | Empty iframes, CORS issues, missing proxy routes |
| **07_performance_budget** | Chat responds < 3.5s | LLM bottlenecks, slow vector search |
| **08_accessibility** | No critical a11y violations | Missing labels, poor contrast, keyboard nav issues |

## 📁 Structure

```
tests/e2e/
├── playwright.config.ts       # Playwright configuration
├── package.json                # npm dependencies
├── specs/                      # Test specifications
│   ├── 00_home.spec.ts
│   ├── 01_health.spec.ts
│   ├── 02_chat_sources.spec.ts
│   ├── 03_chat_perf_breakdown.spec.ts
│   ├── 04_uploads.spec.ts
│   ├── 05_research_agent.spec.ts
│   ├── 06_monitoring.spec.ts
│   ├── 07_performance_budget.spec.ts
│   └── 08_accessibility.spec.ts
├── fixtures/                   # Test data
│   └── sample.md
└── playwright-report/          # Generated after run
    ├── index.html
    └── results.xml
```

## 🚀 Quick Start

### **On AWS (Recommended)**

```bash
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel

# Run tests against Docker network
bash scripts/run_playwright_docker.sh

# View report
python3 -m http.server -d tests/e2e/playwright-report 8888
# Open: http://16.146.148.184:8888/
```

### **Locally**

```bash
# Start the stack
docker compose up -d

# Run tests
BASE_URL=http://localhost:3000 bash scripts/run_playwright_local.sh

# View report
cd tests/e2e && npx playwright show-report
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://frontend:3000` | Target URL (Docker network or localhost) |
| `PW_HEADLESS` | `1` | Set to `0` to see browser |
| `CI` | (unset) | Set to `true` for CI mode |

### Network Modes

**Docker Network** (for CI/AWS):
```bash
BASE_URL=http://frontend:3000 bash scripts/run_playwright_docker.sh
```

**Localhost** (for development):
```bash
BASE_URL=http://localhost:3000 bash scripts/run_playwright_local.sh
```

**External IP** (for manual testing):
```bash
BASE_URL=http://16.146.148.184:3000 PW_HEADLESS=0 bash scripts/run_playwright_local.sh
```

## 📊 Reports

After running tests, you'll get:

1. **HTML Report** (`playwright-report/index.html`)
   - Interactive UI
   - Screenshots of failures
   - Video recordings
   - Trace viewer

2. **JUnit XML** (`playwright-report/results.xml`)
   - For CI/CD integration
   - Compatible with Jenkins, GitLab CI, etc.

3. **Console Output**
   - Real-time test progress
   - Detailed error messages
   - Performance timings

## 🐛 Debugging

### View Tests in Headed Mode

```bash
PW_HEADLESS=0 bash scripts/run_playwright_local.sh
```

### Debug a Specific Test

```bash
cd tests/e2e
PW_HEADLESS=0 npx playwright test --debug specs/02_chat_sources.spec.ts
```

### Generate Code (Record Actions)

```bash
cd tests/e2e
npx playwright codegen http://localhost:3000
```

### View Trace

```bash
cd tests/e2e
npx playwright show-trace playwright-report/test-results/<test-name>/trace.zip
```

## 🔍 Troubleshooting

### Test: `02_chat_sources` fails with "expected at least one source item"

**Cause**: Backend not returning `artifacts.retrieval_log.items` or UI not rendering sources.

**Fix**:
1. Check API response: `curl -X POST http://localhost:3000/api/v1/rag/query -d '{"query":"test","user_id":"demo","groups":[]}'  | jq '.artifacts.retrieval_log'`
2. Verify UI component reads correct field from API response
3. Check `data-testid="source-item"` is present in DOM

---

### Test: `03_chat_perf_breakdown` fails with "No timing data available"

**Cause**: Backend not returning `metrics.breakdown` or UI not displaying it.

**Fix**:
1. Check API response: `curl ... | jq '.metrics.breakdown'`
2. Add to `services/api/routes/rag.py`:
   ```python
   metrics = {
       "latency_ms": total_ms,
       "breakdown": {
           "retrieve_ms": t1,
           "rerank_ms": t2,
           "synth_ms": t3,
           "web_ms": t4
       }
   }
   ```
3. Update UI to read `response.metrics.breakdown`

---

### Test: `04_uploads` fails with 404

**Cause**: Upload endpoint missing or nginx not proxying.

**Fix**:
1. Check endpoint: `curl -i -X POST http://localhost:3000/api/v1/documents`
2. Verify `services/api/routes/documents.py` exists and is registered in `app.py`
3. Check nginx.conf has:
   ```nginx
   location /api/ {
       rewrite ^/api/(.*)$ /$1 break;
       proxy_pass http://rag-api-v1:8080;
   }
   ```

---

### Test: `06_monitoring` fails - iframes empty

**Cause**: Prometheus/Grafana not proxied or CORS blocking.

**Fix**:
1. Add to `frontend/nginx.conf`:
   ```nginx
   location /prom/ {
       proxy_pass http://prometheus:9090/;
   }
   location /graf/ {
       proxy_pass http://grafana:3000/;
       add_header X-Frame-Options "SAMEORIGIN";
   }
   ```
2. Rebuild frontend: `docker compose up -d --build frontend`

---

### Test: `07_performance_budget` fails - exceeds 3.5s

**Cause**: LLM too slow, vector search inefficient, or no caching.

**Fix**:
1. Use faster model: `RAG_LLM_MODEL=llama3.2:3b` (not `qwen2.5:14b`)
2. Cap tokens: `RAG_LLM_MAX_TOKENS=300`
3. Enable caching (Redis)
4. Optimize vector search (reduce `top_k`)

## 📈 CI/CD Integration

### GitHub Actions

```.github/workflows/e2e.yml
name: E2E Tests

on: [push, workflow_dispatch]

jobs:
  e2e:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - name: Start stack
        run: docker compose up -d --build

      - name: Wait for ready
        run: |
          for i in {1..60}; do
            code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ready || true)
            if [ "$code" = "200" ]; then exit 0; fi
            sleep 2
          done
          echo "Services not ready"; exit 1

      - name: Run Playwright
        run: bash scripts/run_playwright_docker.sh

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: tests/e2e/playwright-report
```

## 🎓 Best Practices

1. **Always run tests in Docker network mode on CI** - more reliable
2. **Use data-testid attributes** - don't rely on text or CSS classes
3. **Check console errors** - they often reveal integration issues
4. **Keep tests focused** - one assertion per test when possible
5. **Add helpful console.log** - makes debugging failures faster
6. **Update tests when UI changes** - don't let them go stale

## 🔗 Related Documentation

- [Playwright Docs](https://playwright.dev)
- [E2E Implementation Plan](../docs/E2E_IMPLEMENTATION_COMPLETE.md)
- [UI Contract Backend Support](../docs/E2E_REMEDIATION_PLAN.md)
- [Deployment Guide](../docs/DEPLOYMENT_SUCCESS.md)

---

**Last Updated**: 2025-11-09
**Branch**: `otel`
**Status**: ✅ Ready for deployment
