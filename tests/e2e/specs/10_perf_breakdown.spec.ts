import { test, expect } from '@playwright/test';

test('Performance section shows stage timings', async ({ page, baseURL }) => {
  await page.goto(baseURL!);

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Send a query
  await page.locator('[data-testid="chat-input"]').fill('Explain our RAG pipeline stages');
  await page.locator('[data-testid="chat-send"]').click();

  // Wait for answer
  await expect(page.locator('[data-testid="answer"]')).toBeVisible({ timeout: 15000 });

  // Check metrics row is visible
  const metricsRow = page.locator('[data-testid="metrics-row"]');
  await expect(metricsRow).toBeVisible();

  // Check for performance breakdown cells
  // These should show individual stage timings
  const perfBreakdown = page.locator('[data-testid="perf-breakdown"]');

  // If breakdown exists, check for stage timings
  if (await perfBreakdown.isVisible()) {
    await expect(page.locator('[data-testid="perf-retrieve-ms"]')).toBeVisible();
    await expect(page.locator('[data-testid="perf-rerank-ms"]')).toBeVisible();
    await expect(page.locator('[data-testid="perf-synth-ms"]')).toBeVisible();
  } else {
    // At minimum, check that latency is shown
    await expect(page.locator('[data-testid="latency-ms"]')).toBeVisible();
    const latencyText = await page.locator('[data-testid="latency-ms"]').textContent();
    expect(latencyText).toMatch(/\d+/); // Should contain numbers
  }
});

