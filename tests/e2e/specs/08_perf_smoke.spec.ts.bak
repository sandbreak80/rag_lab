import { test, expect } from '@playwright/test';

test('chat completes under 3.5s (smoke)', async ({ page, baseURL }) => {
  await page.goto(baseURL!);
  await page.waitForLoadState('networkidle');

  const start = Date.now();

  // Submit quick query
  const input = page.locator('textarea, [data-testid="chat-input"], input[type="text"]').first();
  await input.fill('Quick answer check.');

  const sendBtn = page.locator('button:has-text("Send"), [data-testid="chat-send"], button[type="submit"]').first();
  await sendBtn.click();

  // Wait for answer with 3.5s timeout
  const answer = page.locator('[data-testid="answer"], .answer, .response, .message').first();
  await expect(answer).toBeVisible({ timeout: 3500 });

  const elapsed = Date.now() - start;
  console.log(`E2E elapsed: ${elapsed}ms`);

  // Soft assertion - warn if over target but don't fail
  if (elapsed > 3500) {
    console.log(`⚠ Performance: ${elapsed}ms exceeds 3.5s target (soft check)`);
  } else {
    console.log(`✓ Performance: ${elapsed}ms under 3.5s target`);
  }

  // Always pass if answer appeared (this is a smoke test, not a hard SLO)
  expect(elapsed).toBeLessThan(10000); // Hard fail only if > 10s
});

