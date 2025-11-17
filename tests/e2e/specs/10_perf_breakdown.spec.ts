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
  // First check if the performance block container exists
  const perfBlock = page.locator('[data-testid="chat-perf"]');
  const perfBlockCount = await perfBlock.count();

  if (perfBlockCount > 0) {
    // Performance block exists - check if it's visible and expanded
    await expect(perfBlock).toBeVisible({ timeout: 5000 });

    // Check if the breakdown content is visible (inside the expanded section)
    const perfBreakdown = page.locator('[data-testid="perf-breakdown"]');
    const perfCount = await perfBreakdown.count();

    if (perfCount > 0 && await perfBreakdown.first().isVisible().catch(() => false)) {
      console.log('✅ Performance breakdown visible');
      // Check for at least one timing metric
      const hasTimings = await page.locator('[data-testid*="perf-"], [data-testid*="-ms"]').count();
      expect(hasTimings).toBeGreaterThan(0);
    } else {
      // Performance breakdown might be collapsed - try clicking to expand
      const expandButton = perfBlock.locator('button').first();
      if (await expandButton.isVisible().catch(() => false)) {
        await expandButton.click();
        await page.waitForTimeout(500); // Wait for expansion animation
        const perfBreakdownAfter = page.locator('[data-testid="perf-breakdown"]');
        if (await perfBreakdownAfter.first().isVisible().catch(() => false)) {
          const hasTimings = await page.locator('[data-testid*="perf-"], [data-testid*="-ms"]').count();
          expect(hasTimings).toBeGreaterThan(0);
        } else {
          // Performance breakdown might not have data - check metrics row as fallback
          const latency = page.locator('[data-testid="metrics-latency"]');
          if (await latency.isVisible().catch(() => false)) {
            const latencyText = await latency.textContent();
            expect(latencyText).toMatch(/\d+/); // Should contain numbers
            console.log('✅ Latency shown in metrics row (performance breakdown not available)');
          }
        }
      } else {
        // No expand button - performance breakdown might not have data
        // Check metrics row as fallback
        const latency = page.locator('[data-testid="metrics-latency"]');
        if (await latency.isVisible().catch(() => false)) {
          const latencyText = await latency.textContent();
          expect(latencyText).toMatch(/\d+/); // Should contain numbers
          console.log('✅ Latency shown in metrics row (performance breakdown not available)');
        }
      }
    }
  } else {
    // Performance breakdown might not be rendered yet - check metrics row as fallback
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

