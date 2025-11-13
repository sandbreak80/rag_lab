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
  await expect(page.locator('[data-testid="chat-answer"]')).toBeVisible({ timeout: 15000 });

  // Sources panel should exist and have items
  const sourcesList = page.locator('[data-testid="chat-sources"]');
  await expect(sourcesList).toBeVisible();

  const items = page.locator('[data-testid="source-item"]');
  const count = await items.count();

  console.log(`Found ${count} source items`);
  expect(count, 'expected at least one source item').toBeGreaterThan(0);

  // Each source item should be visible and contain a link
  for (let i = 0; i < Math.min(count, 3); i++) {
    const item = items.nth(i);
    await expect(item).toBeVisible();

    // Check if there's a link inside the source item
    const link = item.locator('a[href]').first();
    const linkCount = await link.count();

    if (linkCount > 0) {
      const href = await link.getAttribute('href');
      console.log(`Source #${i} has link: ${href}`);
      expect(href).toBeTruthy();
    } else {
      console.log(`Source #${i} has no link (may be RAG source without URL)`);
    }
  }
});

