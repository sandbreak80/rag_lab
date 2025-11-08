# Playwright E2E Tests for RAG Lab

## Overview

Comprehensive end-to-end tests that validate the user-facing UI at `http://16.146.148.184:3000`, exercising all features impacted by Phase B/C backend changes.

## Test Coverage

### Test Suites

1. **00_home.spec.ts** - Homepage loads correctly
2. **01_health_via_frontend.spec.ts** - Health endpoints return JSON
3. **02_chat_happy_path.spec.ts** - Chat completes successfully
4. **03_provenance_and_citations.spec.ts** - Provenance badges and citations visible
5. **04_metrics_and_trace.spec.ts** - Trace ID, tokens, cost displayed
6. **05_json_artifacts_download.spec.ts** - Artifacts A-G downloadable
7. **06_guardrail_degradation.spec.ts** - Graceful fallback on errors
8. **07_nginx_rewrite_and_cors.spec.ts** - API routing and CORS validation
9. **08_perf_smoke.spec.ts** - Response time < 3.5s (smoke test)

## Running Tests

### Via Docker (Recommended)

```bash
# From project root
bash scripts/run_e2e.sh
```

### Locally (Requires Node.js)

```bash
cd tests/e2e
npm install
npm test
```

### On AWS Instance

```bash
ssh ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel
bash scripts/run_e2e.sh
```

## Test Configuration

### Environment Variables

- `BASE_URL` - Frontend URL (default: `http://frontend:3000`)
- `CI` - CI mode (default: `true`)

### Flexible Selectors

Tests use multiple fallback selectors to accommodate UI variations:
- `data-testid` attributes (preferred)
- Class names
- Text content
- Element types

## Reports

After running tests, reports are available at:

- **HTML Report**: `tests/e2e/playwright-report/index.html`
- **JUnit XML**: `tests/e2e/playwright-report/results.xml`

## Pass/Fail Criteria

All 8+ test specs must pass for merge approval:

- ✅ Homepage renders
- ✅ Health endpoints return JSON
- ✅ Chat returns answer (no errors)
- ✅ Provenance/citations visible
- ✅ Trace ID and metrics present
- ✅ Artifacts downloadable
- ✅ Guardrail fallback works
- ✅ Nginx routing (no CORS)
- ✅ Performance < 3.5s (soft check)

## Adding New Tests

1. Create `tests/e2e/specs/NN_test_name.spec.ts`
2. Import from `@playwright/test`
3. Use flexible selectors with fallbacks
4. Add console logging for debugging
5. Run locally to verify

## Troubleshooting

### Tests Fail to Find Elements

- Check if UI uses different selectors
- Add `data-testid` attributes to components
- Use `page.locator().count()` to debug visibility

### Timeouts

- Increase `timeout` in `playwright.config.ts`
- Add `await page.waitForTimeout(ms)` for async operations
- Check backend services are healthy

### CORS Errors

- Verify Nginx config forwards headers
- Check `frontend/nginx.conf` has correct proxy settings
- Ensure same-origin routing is configured

## CI Integration

Add to GitHub Actions:

```yaml
- name: Run E2E Tests
  run: bash scripts/run_e2e.sh
  
- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: tests/e2e/playwright-report/
```

## Notes

- Tests run inside Docker network (`http://frontend:3000`)
- All real backends enabled (no mocks)
- Tests validate Phase B/C observability features
- Graceful degradation on missing UI elements

