import { test, expect } from '@playwright/test';

test('chat completes under 10s (smoke)', async ({ page, baseURL }) => {
  await page.goto(baseURL!);
  await page.waitForLoadState('networkidle');

  const start = Date.now();

  // Submit quick query
  const input = page.locator('textarea, [data-testid="chat-input"], input[type="text"]').first();
  await input.fill('Quick answer check.');

  const sendBtn = page.locator('button:has-text("Send"), [data-testid="chat-send"], button[type="submit"]').first();
  await sendBtn.click();

  // Wait for answer with realistic timeout for LLM
  const answer = page.locator('[data-testid="chat-answer"], .answer, .response, .message').first();
  await expect(answer).toBeVisible({ timeout: 15000 });

  const elapsed = Date.now() - start;
  console.log(`E2E elapsed: ${elapsed}ms`);

  // Soft assertion - warn if over 6s but don't fail
  if (elapsed > 6000) {
    console.log(`⚠ Performance: ${elapsed}ms exceeds 6s target (soft check)`);
  } else {
    console.log(`✓ Performance: ${elapsed}ms under 6s target`);
  }

  // Hard fail only if > 10s (realistic for LLM-based RAG)
  expect(elapsed).toBeLessThan(10000);
});

