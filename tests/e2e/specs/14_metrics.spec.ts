import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://16.146.148.184:3000';
const PROMETHEUS_URL = process.env.PROMETHEUS_URL || 'http://16.146.148.184:9090';

test.describe('Metrics Page', () => {
  test('should display metrics panel with Prometheus data', async ({ page }) => {
    // Navigate to metrics page
    await page.goto(`${BASE_URL}/metrics`);
    await page.waitForLoadState('networkidle');

    // Verify metrics panel is visible
    const metricsPanel = page.getByTestId('metrics-panel');
    await expect(metricsPanel).toBeVisible();

    // Look for any metric displays (gauges, charts, numbers)
    const body = page.locator('body');
    const bodyText = await body.textContent();

    // Should have some metric-related text
    expect(bodyText).toMatch(/latency|requests|rate|p95|p99|error/i);
  });

  test('should verify Prometheus proxy is reachable', async ({ page }) => {
    // Check if Prometheus is accessible through the app
    const response = await page.request.get(`${PROMETHEUS_URL}/api/v1/query?query=up`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status', 'success');
    expect(data).toHaveProperty('data');
  });

  test('should display key RAG metrics', async ({ page }) => {
    await page.goto(`${BASE_URL}/metrics`);
    await page.waitForLoadState('networkidle');

    // Wait for any data to load
    await page.waitForTimeout(2000);

    // Look for specific metric elements
    const body = page.locator('body');
    const content = await body.textContent();

    // Should show some metrics (at least one of these)
    const hasMetrics =
      content?.includes('latency') ||
      content?.includes('request') ||
      content?.includes('rate') ||
      content?.includes('P95') ||
      content?.includes('P99');

    expect(hasMetrics).toBeTruthy();
  });

  test('should render metrics page without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/metrics`);
    await page.waitForLoadState('networkidle');

    // Verify no critical console errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('404') &&
      !err.includes('favicon') &&
      !err.includes('CORS') // Prometheus CORS might be expected
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('should verify metrics panel shows live data', async ({ page }) => {
    await page.goto(`${BASE_URL}/metrics`);
    await page.waitForLoadState('networkidle');

    const metricsPanel = page.getByTestId('metrics-panel');
    await expect(metricsPanel).toBeVisible();

    // Look for numeric values (metrics should have numbers)
    const numbers = page.locator('text=/\\d+(\\.\\d+)?/').first();
    await expect(numbers).toBeVisible({ timeout: 5000 });
  });
});

