import { test, expect } from '@playwright/test';

test('Chat P95 under 3.5s (smoke)', async ({ page }) => {
  await page.goto('/');

  const start = Date.now();

  await page.locator('[data-testid="chat-input"], textarea').first().fill('Give me a 2-sentence overview of our RAG system.');
  await page.locator('[data-testid="chat-send"], button:has-text("Send")').first().click();

  await expect(page.locator('[data-testid="answer"]')).toBeVisible({ timeout: 15000 });

  const elapsed = Date.now() - start;

  console.log(`⏱️  Chat response time: ${elapsed}ms`);

  expect(elapsed, `elapsed ${elapsed}ms exceeds 3500ms target`).toBeLessThan(3500);

  if (elapsed < 1000) {
    console.log('✅ Excellent performance (<1s)');
  } else if (elapsed < 2000) {
    console.log('✅ Good performance (<2s)');
  } else if (elapsed < 3500) {
    console.log('⚠️  Acceptable performance but close to budget (< 3.5s)');
  }
});

