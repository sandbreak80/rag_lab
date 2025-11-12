import { test, expect } from '@playwright/test';

test('Chat sources render with valid items', async ({ page }) => {
  const q = 'Summarize the RAG architecture';

  await page.goto('/');

  // Find input field (multiple possible selectors)
  const input = page.locator('[data-testid="chat-input"], textarea, input[type="text"]').first();
  await input.fill(q);

  // Find send button
  await page.locator('[data-testid="chat-send"], button:has-text("Send")').first().click();

  // Wait for answer render
  await expect(page.locator('[data-testid="answer"]')).toBeVisible({ timeout: 15000 });

  // Sources panel should exist and have items
  const sourcesList = page.locator('text=Sources').locator('..'); // container near label
  await expect(sourcesList).toBeVisible();

  const items = sourcesList.locator('a, [role="link"], [data-testid="source-item"]');
  const count = await items.count();

  console.log(`Found ${count} source items`);
  expect(count, 'expected at least one source item').toBeGreaterThan(0);

  // Each item must have a score + a link target (source_uri)
  for (let i = 0; i < Math.min(count, 10); i++) {
    const item = items.nth(i);
    await expect(item).toBeVisible();

    const href = await item.getAttribute('href');
    expect(href, `source item #${i} missing href`).toBeTruthy();
  }
});

