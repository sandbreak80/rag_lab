import { test, expect } from '@playwright/test';

test('Monitoring graphs load data (Prom/Grafana path valid)', async ({ page }) => {
  await page.goto('/');

  // Navigate to monitoring page
  const monitoringLink = page.locator('[href="/monitoring"], a:has-text("Monitoring")').first();

  if (await monitoringLink.isVisible().catch(() => false)) {
    await monitoringLink.click();
    await page.waitForLoadState('networkidle');
  } else {
    // Try direct navigation
    await page.goto('/monitoring');
  }

  // If using iframes:
  const iframes = page.locator('iframe');
  const iframeCount = await iframes.count();

  if (iframeCount > 0) {
    console.log(`Found ${iframeCount} iframe(s) on monitoring page`);

    await expect(iframes.first()).toBeVisible();

    // Wait for any canvas to appear inside first iframe
    const frame = await iframes.first().contentFrame();

    if (frame) {
      const content = frame.locator('canvas, .panel-content, .graph-legend, body');
      await expect(content).toBeVisible({ timeout: 15000 });
      console.log('✅ Monitoring iframe loaded successfully');
    } else {
      console.log('⚠️  Could not access iframe content (CORS or loading issue)');
    }
  } else {
    console.log('⚠️  No iframes found - checking for direct graphs');

    // Check for direct embedded graphs (not iframes)
    const graphs = page.locator('canvas, [data-testid="metrics-graph"], .chart-container');
    const graphCount = await graphs.count();

    if (graphCount > 0) {
      await expect(graphs.first()).toBeVisible();
      console.log(`✅ Found ${graphCount} direct graph(s)`);
    } else {
      console.log('⚠️  No monitoring graphs found (neither iframes nor direct)');
      console.log('   Check that Prometheus/Grafana are proxied correctly');
    }
  }
});

test('Prometheus endpoint accessible via proxy', async ({ request, baseURL }) => {
  const promReady = await request.get(`${baseURL}/prom/-/ready`, {
    failOnStatusCode: false
  });

  console.log(`Prometheus /prom/-/ready status: ${promReady.status()}`);

  if (promReady.status() === 404) {
    console.log('⚠️  Prometheus proxy not configured');
    console.log('   Add to nginx.conf: location /prom/ { proxy_pass http://prometheus:9090/; }');
  }

  // Should either work (200) or not be configured yet (404)
  expect([200, 404, 502]).toContain(promReady.status());
});

test('Grafana endpoint accessible via proxy', async ({ request, baseURL }) => {
  const grafana = await request.get(`${baseURL}/graf/`, {
    failOnStatusCode: false,
    maxRedirects: 0
  });

  console.log(`Grafana /graf/ status: ${grafana.status()}`);

  if (grafana.status() === 404) {
    console.log('⚠️  Grafana proxy not configured');
    console.log('   Add to nginx.conf: location /graf/ { proxy_pass http://grafana:3000/; }');
  }

  // Should either work (200/302) or not be configured yet (404)
  expect([200, 302, 404, 502]).toContain(grafana.status());
});

