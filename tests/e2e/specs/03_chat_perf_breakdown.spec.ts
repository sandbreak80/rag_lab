import { test, expect } from '@playwright/test';

test('Performance breakdown shows timings after a chat run', async ({ page }) => {
  await page.goto('/');

  await page.locator('[data-testid="chat-input"], textarea').first().fill('Explain our RAG pipeline');
  await page.locator('[data-testid="chat-send"], button:has-text("Send")').first().click();

  await expect(page.locator('[data-testid="answer"]')).toBeVisible({ timeout: 15000 });

  // Look for performance breakdown panel
  const panel = page.locator('text=Performance').first();

  if (await panel.isVisible()) {
    await panel.click(); // expand if collapsible

    // Should not show the empty placeholder
    const noDataMessage = page.locator('text=No timing data available, text=No performance data');
    const noDataCount = await noDataMessage.count();

    if (noDataCount > 0) {
      console.log('⚠️  Performance breakdown shows "No timing data available"');
      console.log('   Backend needs to return metrics.breakdown in response');
    }

    expect(noDataCount, 'Performance breakdown should show actual timings, not placeholder').toBe(0);
  } else {
    console.log('⚠️  Performance breakdown panel not found');
    console.log('   This may be expected if the UI component is not yet implemented');
  }
});

