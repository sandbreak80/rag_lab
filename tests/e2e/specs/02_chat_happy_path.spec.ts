import { test, expect } from '@playwright/test';

test('chat happy path', async ({ page, baseURL }) => {
  await page.goto(baseURL!);

  // Wait for page to be fully loaded
  await page.waitForLoadState('networkidle');

  // Find chat input (try multiple selectors)
  const input = page.locator('textarea, [data-testid="chat-input"], input[type="text"]').first();
  await expect(input).toBeVisible({ timeout: 10000 });

  // Fill and submit
  await input.fill('What is RAG?');

  // Find send button
  const sendBtn = page.locator('button:has-text("Send"), [data-testid="chat-send"], button[type="submit"]').first();
  await sendBtn.click();

  // Wait for answer (be flexible with selectors)
  const answer = page.locator('[data-testid="answer"], .answer, .response, .message').first();
  await expect(answer).toBeVisible({ timeout: 15000 });

  // Ensure no error messages
  const errorCount = await page.locator('[data-testid="error"], .error, .error-message').count();
  expect(errorCount).toBe(0);
});

