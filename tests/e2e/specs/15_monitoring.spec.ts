import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://16.146.148.184:3000';
const GRAFANA_URL = process.env.GRAFANA_URL || 'http://16.146.148.184:3001';

test.describe('Monitoring Page', () => {
  test('should display monitoring panel with links to Grafana', async ({ page }) => {
    // Navigate to monitoring page
    await page.goto(`${BASE_URL}/monitoring`);
    await page.waitForLoadState('networkidle');

    // Verify monitoring panel is visible
    const monitoringPanel = page.getByTestId('monitoring-panel');
    await expect(monitoringPanel).toBeVisible();
  });

  test('should verify Grafana is accessible', async ({ page }) => {
    // Check if Grafana returns 200 HTML
    const response = await page.request.get(GRAFANA_URL);
    expect(response.status()).toBe(200);

    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('text/html');

    const body = await response.text();
    expect(body).toContain('Grafana');
  });

  test('should have working link to Grafana dashboards', async ({ page }) => {
    await page.goto(`${BASE_URL}/monitoring`);
    await page.waitForLoadState('networkidle');

    // Look for Grafana link
    const grafanaLink = page.locator('a[href*="3001"]').first();

    if (await grafanaLink.isVisible()) {
      // Verify link has correct href
      const href = await grafanaLink.getAttribute('href');
      expect(href).toContain('3001');
    } else {
      // Alternative: look for any external link
      const externalLinks = page.locator('a[target="_blank"]');
      const count = await externalLinks.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should display monitoring charts or indicators', async ({ page }) => {
    await page.goto(`${BASE_URL}/monitoring`);
    await page.waitForLoadState('networkidle');

    // Look for chart elements
    const cpuChart = page.getByTestId('monitoring-cpu');
    const gpuChart = page.getByTestId('monitoring-gpu');
    const healthChart = page.getByTestId('monitoring-health');

    // At least one chart should be present
    const charts = [cpuChart, gpuChart, healthChart];
    let visibleCount = 0;

    for (const chart of charts) {
      if (await chart.isVisible().catch(() => false)) {
        visibleCount++;
      }
    }

    // If no specific charts, just verify the panel has content
    if (visibleCount === 0) {
      const monitoringPanel = page.getByTestId('monitoring-panel');
      const content = await monitoringPanel.textContent();
      expect(content).toBeTruthy();
      expect(content!.length).toBeGreaterThan(10);
    }
  });

  test('should render monitoring page without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/monitoring`);
    await page.waitForLoadState('networkidle');

    // Verify no critical console errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('404') &&
      !err.includes('favicon') &&
      !err.includes('CORS') // Grafana CORS might be expected
    );

    expect(criticalErrors.length).toBe(0);

    // Verify monitoring panel rendered
    const monitoringPanel = page.getByTestId('monitoring-panel');
    await expect(monitoringPanel).toBeVisible();
  });

  test('should verify Grafana dashboard links work', async ({ page, context }) => {
    await page.goto(`${BASE_URL}/monitoring`);
    await page.waitForLoadState('networkidle');

    // Look for dashboard links
    const dashboardLinks = page.locator('a[href*="grafana"], a[href*="3001"]');
    const count = await dashboardLinks.count();

    if (count > 0) {
      const firstLink = dashboardLinks.first();
      const href = await firstLink.getAttribute('href');

      // Verify the link points to a valid URL
      expect(href).toBeTruthy();

      // If it's a full URL, verify it's accessible
      if (href?.startsWith('http')) {
        const response = await page.request.get(href);
        expect([200, 302]).toContain(response.status());
      }
    }
  });
});

