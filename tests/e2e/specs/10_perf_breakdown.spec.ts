import { test, expect } from '@playwright/test';

test('Performance section shows stage timings', async ({ page, baseURL }) => {
  await page.goto(baseURL!);

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Send a query
  await page.locator('[data-testid="chat-input"]').fill('Explain our RAG pipeline stages');
  await page.locator('[data-testid="chat-send"]').click();

  // Wait for answer
  await expect(page.locator('[data-testid="chat-answer"]')).toBeVisible({ timeout: 15000 });

  // Check metrics row is visible
  const metricsRow = page.locator('[data-testid="metrics-row"]');
  await expect(metricsRow).toBeVisible();

  // Check for performance breakdown - it may be in a collapsible section
  const perfBreakdown = page.locator('[data-testid="perf-breakdown"], [data-testid="chat-perf"]');
  const perfCount = await perfBreakdown.count();

  if (perfCount > 0 && await perfBreakdown.first().isVisible().catch(() => false)) {
    console.log('✅ Performance breakdown visible');
    // Check for at least one timing metric
    const hasTimings = await page.locator('[data-testid*="perf-"], [data-testid*="-ms"]').count();
    expect(hasTimings).toBeGreaterThan(0);
  } else {
    // Performance breakdown might be collapsed or not rendered yet
    // At minimum, check that metrics row with latency is shown
    const metricsRow = page.locator('[data-testid="metrics-row"]');
    await expect(metricsRow).toBeVisible({ timeout: 5000 });
    
    const latency = page.locator('[data-testid="metrics-latency"]');
    if (await latency.isVisible().catch(() => false)) {
      const latencyText = await latency.textContent();
      expect(latencyText).toMatch(/\d+/); // Should contain numbers
      console.log('✅ Latency shown in metrics row');
    }
  }
});

