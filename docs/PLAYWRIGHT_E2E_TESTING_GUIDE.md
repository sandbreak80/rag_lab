## Playwright E2E Testing Guide

**Complete guide for running end-to-end tests on the RAG Lab UI.**

---

## 🎯 What's Tested

### **Core Integration Tests**
✅ Homepage loads without errors
✅ Health endpoints (`/live`, `/ready`) accessible
✅ API routing through Nginx (same-origin `/api`)
✅ Query submission and response display
✅ Citations drawer with provenance badges
✅ Provenance badges (security status, recency)
✅ Metrics row (trace ID, tokens, cost, latency)
✅ JSON artifacts inspector
✅ No CORS errors
✅ OpenTelemetry headers forwarded

### **Error Handling Tests**
✅ API timeout handling
✅ Security degraded status

### **Golden Query Tests** (User Acceptance)
✅ Navigational: "Where is the Phase 2 quickstart?"
✅ Policy: "How to run acceptance probes?"
✅ Temporal: "What changed in Phase B today?"

### **Performance Tests**
✅ Page load < 3 seconds
✅ Query response < 10 seconds (cold)

---

## 🚀 Quick Start

### **Option 1: Docker (Recommended)**

```bash
# Run all tests in Docker
./scripts/run-e2e-tests.sh

# Run against custom URL
./scripts/run-e2e-tests.sh http://16.146.148.184:3000 docker

# Run specific test file
docker compose run --rm playwright \
  npx playwright test tests/e2e/test_rag_ui_integration.spec.ts

# Run with headed browsers (visible)
docker compose run --rm playwright \
  npx playwright test --headed

# Run in UI mode (interactive)
docker compose run --rm -p 9323:9323 playwright \
  npx playwright test --ui-host=0.0.0.0 --ui-port=9323
```

### **Option 2: Local (Playwright installed)**

```bash
# Install Playwright (first time)
npm install -D @playwright/test
npx playwright install --with-deps

# Run all tests
./scripts/run-e2e-tests.sh http://16.146.148.184:3000 local

# Or directly
BASE_URL=http://16.146.148.184:3000 npx playwright test

# Run specific browser
npx playwright test --project=chromium

# Run in UI mode (interactive debugging)
npx playwright test --ui

# Debug mode (step through)
npx playwright test --debug

# Run specific test
npx playwright test -g "should submit query"
```

---

## 📋 Test Scenarios

### **1. Homepage Load**
```typescript
test('should load homepage without errors', async ({ page }) => {
  await page.goto(BASE_URL);
  await expect(page).toHaveTitle(/Neural Vault|RAG Lab/);
  // No console errors
});
```

**What it checks:**
- Page loads successfully
- Title is correct
- No JavaScript console errors

---

### **2. Health Endpoints**
```typescript
test('should verify health endpoint accessibility', async ({ request }) => {
  const response = await request.get(`${BASE_URL}/live`);
  expect(response.status()).toBe(200);
});
```

**What it checks:**
- `/live` returns 200 + JSON
- `/ready` returns 200 + JSON
- Routing through Nginx works

---

### **3. API Same-Origin Routing**
```typescript
test('should make API request through same-origin /api route', async ({ request }) => {
  const response = await request.post(`${BASE_URL}/api/v1/rag/query`, {
    data: {
      query: 'What is RAG?',
      user_id: 'e2e_test_user',
      groups: []
    }
  });
  expect(response.status()).toBe(200);
  expect(contentType).toContain('application/json');
});
```

**What it checks:**
- API accessible at `/api/v1/rag/query`
- Returns JSON (not HTML 502 error)
- No CORS errors (same-origin)
- Response has correct structure (answer, citations, artifacts, etc.)

---

### **4. Query Submission**
```typescript
test('should submit query and display answer', async ({ page }) => {
  await page.fill('textarea', 'What is RAG?');
  await page.click('button[type="submit"]');
  await page.waitForSelector('text=/RAG|Retrieval/');
});
```

**What it checks:**
- Input field works
- Submit button works
- Answer appears
- No error messages

---

### **5. Citations Drawer**
```typescript
test('should display citations drawer', async ({ page }) => {
  // ... submit query
  await page.waitForSelector('[class*="citation"]');
  const originBadge = page.locator('text=/RAG|WEB|AGENT/');
  await expect(originBadge.first()).toBeVisible();
});
```

**What it checks:**
- Citations component renders
- Citations have `origin_tool` badges (RAG/WEB/AGENT)
- Links are clickable

---

### **6. Provenance Badges**
```typescript
test('should display provenance badges', async ({ page }) => {
  // ... submit query
  const securityBadge = page.locator('text=/ok|degraded|blocked/i');
  await expect(securityBadge.first()).toBeVisible();
});
```

**What it checks:**
- Security status badge visible (ok/degraded/blocked)
- Recency gate indicator
- ACL filtering indicator

---

### **7. Metrics Row**
```typescript
test('should display metrics row with trace ID', async ({ page }) => {
  // ... submit query
  const traceLink = page.locator('a[href*="trace"]');
  expect(await traceLink.count()).toBeGreaterThan(0);
});
```

**What it checks:**
- Trace ID displayed and clickable
- Token counts visible
- Cost and latency displayed
- A/B bucket indicator (if applicable)

---

### **8. JSON Artifacts Inspector**
```typescript
test('should allow JSON artifacts inspection', async ({ page }) => {
  // ... submit query
  await page.click('button:has-text("Artifacts")');
  const jsonContent = await page.locator('pre').first().textContent();
  expect(jsonContent).toContain('planner');
  expect(jsonContent).toContain('retrieval_log');
});
```

**What it checks:**
- JSON toggle button works
- All 7 schemas (A-G) present
- Download functionality

---

### **9. No CORS Errors**
```typescript
test('should not have CORS errors', async ({ page }) => {
  page.on('requestfailed', request => {
    // Collect failed requests
  });
  // ... submit query
  expect(corsErrors).toHaveLength(0);
});
```

**What it checks:**
- No `Access-Control-Allow-Origin` errors
- Same-origin routing working correctly

---

### **10. Three Golden Queries**

#### **A. Navigational**
```typescript
test('Navigational: Where is the Phase 2 quickstart?', async ({ page }) => {
  await page.fill('textarea', 'Where is the Phase 2 quickstart?');
  await page.click('button[type="submit"]');
  await page.waitForSelector('text=/Phase|quickstart/');
  // Should have citations with RAG provenance
});
```

#### **B. Policy**
```typescript
test('Policy: How to run acceptance probes?', async ({ page }) => {
  await page.fill('textarea', 'How to run acceptance probes?');
  await page.click('button[type="submit"]');
  await page.waitForSelector('text=/pytest|test/');
  // Should have multiple citations
});
```

#### **C. Temporal**
```typescript
test('Temporal: What changed in Phase B today?', async ({ page }) => {
  await page.fill('textarea', 'What changed in Phase B today?');
  await page.click('button[type="submit"]');
  await page.waitForSelector('text=/Phase|change/');
  // Should have recency indicator
});
```

---

## 🔧 Configuration

### **playwright.config.ts**

```typescript
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 90 * 1000,  // 90s per test

  use: {
    baseURL: process.env.BASE_URL || 'http://16.146.148.184:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: devices['Desktop Chrome'] },
    { name: 'firefox', use: devices['Desktop Firefox'] },
    { name: 'webkit', use: devices['Desktop Safari'] },
    { name: 'Mobile Chrome', use: devices['Pixel 5'] },
  ],
});
```

### **Environment Variables**

```bash
# Target URL (default: AWS instance)
export BASE_URL=http://16.146.148.184:3000

# CI mode (less verbose output)
export CI=true

# Headed mode (show browser)
export HEADED=true
```

---

## 📊 Reports

### **HTML Report**
```bash
# After test run
npx playwright show-report tests/e2e/playwright-report

# Or open directly
open tests/e2e/playwright-report/index.html
```

### **JSON Report**
```bash
cat tests/e2e/test-results.json | jq
```

### **Screenshots & Videos**
Located in `tests/e2e/test-results/`
- Screenshots: Taken on failure
- Videos: Recorded on failure
- Traces: Playwright trace viewer

---

## 🐛 Debugging

### **Interactive UI Mode**
```bash
npx playwright test --ui
```
- See all tests
- Run/pause/step through
- Inspect DOM
- Time travel debugging

### **Debug Mode**
```bash
npx playwright test --debug
```
- Stops at first test
- Opens Playwright Inspector
- Step through actions
- Evaluate selectors

### **Headed Mode**
```bash
npx playwright test --headed
```
- See browser windows
- Watch tests execute
- Useful for selector debugging

### **Slow Motion**
```bash
npx playwright test --headed --slow-mo=1000
```
- Slows down actions by 1000ms
- See what's happening

### **Specific Test**
```bash
npx playwright test -g "should submit query"
```
- Run only matching tests

---

## 🚨 Troubleshooting

### **Issue: Tests timing out**

**Cause:** Frontend/API not running or slow
**Fix:**
```bash
# Ensure services are up
docker compose ps frontend rag-api-v1

# Check logs
docker compose logs frontend --tail 50
docker compose logs rag-api-v1 --tail 50

# Restart if needed
docker compose up -d --build frontend rag-api-v1
```

### **Issue: Element not found**

**Cause:** UI structure changed or selector wrong
**Fix:**
```bash
# Use codegen to get correct selectors
npx playwright codegen http://16.146.148.184:3000
```

### **Issue: CORS errors in tests**

**Cause:** Nginx routing not working
**Fix:**
1. Check `frontend/nginx.conf` has `/api/` proxy
2. Redeploy frontend: `docker compose up -d --build frontend`
3. Verify: `curl http://localhost:3000/api/live`

### **Issue: API returns 502**

**Cause:** `rag-api-v1` not running
**Fix:**
```bash
docker compose ps rag-api-v1
docker compose logs rag-api-v1
docker compose up -d rag-api-v1
```

### **Issue: Docker container fails to start**

**Cause:** Node modules conflict
**Fix:**
```bash
# Clean and rebuild
docker compose down playwright
docker compose build --no-cache playwright
docker compose run --rm playwright npx playwright test
```

---

## ✅ Success Criteria

Before declaring UI integration complete:

- [ ] All 20+ tests pass in Chromium
- [ ] All tests pass in Firefox and WebKit
- [ ] No CORS errors in any test
- [ ] No console errors in any test
- [ ] Three golden queries return valid answers
- [ ] Citations display with provenance
- [ ] Metrics row shows trace ID
- [ ] Page load < 3s
- [ ] Query response < 10s

---

## 🔄 CI Integration

### **GitHub Actions**
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker compose up -d frontend rag-api-v1
      - name: Wait for ready
        run: sleep 20
      - name: Run Playwright tests
        run: ./scripts/run-e2e-tests.sh http://localhost:3000 docker
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

---

## 📚 Resources

- **Playwright Docs**: https://playwright.dev
- **Test File**: `tests/e2e/test_rag_ui_integration.spec.ts`
- **Config**: `playwright.config.ts`
- **Run Script**: `scripts/run-e2e-tests.sh`
- **Docker Compose**: Playwright service with `--profile testing`

---

## 🎯 Next Steps

After tests pass:
1. Enable observability (`RAG_ENABLE_OBS=1`)
2. Flip mocks to real backends (vector → web → LLM)
3. Re-run tests after each flip (gate with 20/20 passing)
4. Add tests to CI pipeline
5. Run load tests (`locust`)
6. Production deployment!

