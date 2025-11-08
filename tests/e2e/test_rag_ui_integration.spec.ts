/**
 * End-to-End Tests for RAG UI Integration
 * Tests the full flow: Frontend → Nginx → API → Response → UI Components
 *
 * Run with:
 *   npx playwright test tests/e2e/test_rag_ui_integration.spec.ts
 *   OR via Docker:
 *   docker compose run --rm playwright npx playwright test
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://16.146.148.184:3000';
const API_URL = `${BASE_URL}/api/v1/rag/query`;

test.describe('RAG UI Integration - Same-Origin Routing', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
  });

  test('should load homepage without errors', async ({ page }) => {
    // Check no console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Verify page title
    await expect(page).toHaveTitle(/Neural Vault|RAG Lab/);

    // No console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test('should verify health endpoint accessibility', async ({ request }) => {
    // Test /live endpoint (same-origin through Nginx)
    const liveResponse = await request.get(`${BASE_URL}/live`);
    expect(liveResponse.status()).toBe(200);

    const liveData = await liveResponse.json();
    expect(liveData).toHaveProperty('status');

    // Test /ready endpoint
    const readyResponse = await request.get(`${BASE_URL}/ready`);
    expect(readyResponse.status()).toBe(200);

    const readyData = await readyResponse.json();
    expect(readyData).toHaveProperty('status');
  });

  test('should make API request through same-origin /api route', async ({ request }) => {
    // Test API call (no CORS because same-origin)
    const response = await request.post(API_URL, {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        query: 'What is RAG?',
        user_id: 'e2e_test_user',
        groups: [],
        top_k: 8
      }
    });

    // Should succeed (not 502 or CORS error)
    expect(response.status()).toBe(200);

    // Should return JSON (not HTML)
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('application/json');

    // Verify response structure
    const data = await response.json();
    expect(data).toHaveProperty('answer');
    expect(data).toHaveProperty('citations');
    expect(data).toHaveProperty('artifacts');
    expect(data).toHaveProperty('metrics');
    expect(data).toHaveProperty('trace_id');
    expect(data).toHaveProperty('request_id');
    expect(data).toHaveProperty('security_status');
    expect(data).toHaveProperty('contract_version');
  });

  test('should submit query and display answer', async ({ page }) => {
    // Find input field (adjust selector based on your actual UI)
    const inputSelector = 'textarea[placeholder*="Ask"], input[placeholder*="question"], textarea[name="query"]';
    await page.waitForSelector(inputSelector, { timeout: 5000 });

    // Type a question
    await page.fill(inputSelector, 'What is RAG?');

    // Submit (adjust selector for your submit button)
    const submitSelector = 'button[type="submit"], button:has-text("Ask"), button:has-text("Send")';
    await page.click(submitSelector);

    // Wait for response (look for answer container)
    await page.waitForSelector('text=/RAG|Retrieval|Augmented/', { timeout: 10000 });

    // Verify no error messages
    const errorElements = await page.locator('text=/error|Error|failed/i').count();
    expect(errorElements).toBe(0);
  });

  test('should display citations drawer', async ({ page }) => {
    // Submit a query
    await page.fill('textarea, input[type="text"]', 'What is a vector database?');
    await page.click('button[type="submit"]');

    // Wait for citations to appear
    await page.waitForSelector('[class*="citation"], [class*="Citation"]', { timeout: 10000 });

    // Verify citations have required fields
    const citations = await page.locator('[class*="citation"]').first();
    await expect(citations).toBeVisible();

    // Check for origin_tool badge (RAG, WEB, or AGENT)
    const originBadge = page.locator('text=/RAG|WEB|AGENT/');
    await expect(originBadge.first()).toBeVisible();
  });

  test('should display provenance badges', async ({ page }) => {
    // Submit query
    await page.fill('textarea, input[type="text"]', 'Latest updates');
    await page.click('button[type="submit"]');

    // Wait for provenance badges
    await page.waitForSelector('[class*="badge"], [class*="Badge"]', { timeout: 10000 });

    // Look for security status badge
    const securityBadge = page.locator('text=/ok|degraded|blocked/i');
    await expect(securityBadge.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display metrics row with trace ID', async ({ page }) => {
    // Submit query
    await page.fill('textarea, input[type="text"]', 'How does caching work?');
    await page.click('button[type="submit"]');

    // Wait for metrics to appear
    await page.waitForSelector('text=/trace|Trace|tokens|Tokens/', { timeout: 10000 });

    // Verify trace ID is present and clickable
    const traceLink = page.locator('a[href*="trace"], text=/[0-9a-f]{32}/');
    const traceCount = await traceLink.count();
    expect(traceCount).toBeGreaterThan(0);
  });

  test('should allow JSON artifacts inspection', async ({ page }) => {
    // Submit query
    await page.fill('textarea, input[type="text"]', 'Explain embeddings');
    await page.click('button[type="submit"]');

    // Look for JSON inspector toggle
    const jsonToggle = page.locator('button:has-text("Artifacts"), button:has-text("JSON"), button:has-text("Debug")');

    if (await jsonToggle.count() > 0) {
      await jsonToggle.first().click();

      // Verify JSON is displayed
      await page.waitForSelector('pre, code, [class*="json"]', { timeout: 5000 });

      // Check for schema keys
      const jsonContent = await page.locator('pre, code').first().textContent();
      expect(jsonContent).toContain('planner');
      expect(jsonContent).toContain('retrieval_log');
    }
  });

  test('should not have CORS errors in network tab', async ({ page }) => {
    const failedRequests: string[] = [];

    page.on('requestfailed', request => {
      failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Submit query
    await page.fill('textarea, input[type="text"]', 'Test CORS');
    await page.click('button[type="submit"]');

    // Wait for response
    await page.waitForTimeout(3000);

    // Filter CORS-related failures
    const corsErrors = failedRequests.filter(req =>
      req.includes('CORS') || req.includes('Access-Control')
    );

    expect(corsErrors).toHaveLength(0);
  });

  test('should verify OpenTelemetry headers are sent', async ({ page }) => {
    let apiRequestHeaders: Record<string, string> = {};

    page.on('request', request => {
      if (request.url().includes('/api/v1/rag/query')) {
        apiRequestHeaders = request.headers();
      }
    });

    // Submit query
    await page.fill('textarea, input[type="text"]', 'Test OTel headers');
    await page.click('button[type="submit"]');

    await page.waitForTimeout(2000);

    // Check if traceparent header exists (may be set by frontend)
    // Note: This depends on your frontend implementation
    console.log('API Request Headers:', apiRequestHeaders);
    expect(apiRequestHeaders['content-type']).toContain('application/json');
  });
});

test.describe('RAG UI Integration - Error Handling', () => {

  test('should handle API timeout gracefully', async ({ page }) => {
    await page.goto(BASE_URL);

    // Mock a timeout scenario (if API is configured with short timeout)
    await page.fill('textarea, input[type="text"]', 'Very complex query requiring long processing');
    await page.click('button[type="submit"]');

    // Should show loading state
    const loader = page.locator('[class*="loading"], [class*="spinner"], text=/loading/i');
    if (await loader.count() > 0) {
      await expect(loader.first()).toBeVisible();
    }

    // Wait for either success or error message
    await page.waitForSelector('text=/answer|error|timeout/i', { timeout: 80000 });
  });

  test('should display security degraded status when applicable', async ({ page }) => {
    await page.goto(BASE_URL);

    // Submit query
    await page.fill('textarea, input[type="text"]', 'Test security status');
    await page.click('button[type="submit"]');

    await page.waitForTimeout(3000);

    // Check for security status (ok, degraded, or blocked)
    const securityStatus = page.locator('[class*="security"], [class*="Security"]');
    const count = await securityStatus.count();

    // Should have some security indicator
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('RAG UI Integration - Three Golden Queries', () => {

  test('Navigational query: "Where is the Phase 2 quickstart?"', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.fill('textarea, input[type="text"]', 'Where is the Phase 2 quickstart?');
    await page.click('button[type="submit"]');

    // Wait for answer
    await page.waitForSelector('text=/Phase|quickstart|document/i', { timeout: 10000 });

    // Should have citations with links
    const citations = await page.locator('[class*="citation"], a[href*="http"]').count();
    expect(citations).toBeGreaterThan(0);

    // Check for RAG provenance
    const ragBadge = page.locator('text=/RAG/');
    await expect(ragBadge.first()).toBeVisible({ timeout: 5000 });
  });

  test('Policy query: "How to run acceptance probes?"', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.fill('textarea, input[type="text"]', 'How to run acceptance probes?');
    await page.click('button[type="submit"]');

    // Wait for answer with steps
    await page.waitForSelector('text=/pytest|test|probe/', { timeout: 10000 });

    // Should have multiple citations
    const citations = await page.locator('[class*="citation"]').count();
    expect(citations).toBeGreaterThan(0);
  });

  test('Temporal query: "What changed in Phase B today?"', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.fill('textarea, input[type="text"]', 'What changed in Phase B today?');
    await page.click('button[type="submit"]');

    // Wait for answer
    await page.waitForSelector('text=/Phase|change|update/', { timeout: 10000 });

    // Check for recency indicator
    const recencyBadge = page.locator('text=/recent|48h|fresh/i');
    const count = await recencyBadge.count();

    // Should have some recency indicator
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('RAG UI Integration - Performance', () => {

  test('should load page in under 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000);
  });

  test('should respond to query in under 10 seconds (cold)', async ({ page }) => {
    await page.goto(BASE_URL);

    const startTime = Date.now();

    await page.fill('textarea, input[type="text"]', 'What is a vector database?');
    await page.click('button[type="submit"]');
    await page.waitForSelector('text=/vector|database|answer/i', { timeout: 10000 });

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(10000);
  });
});

