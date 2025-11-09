import { test, expect } from '@playwright/test';

test('Sources panel shows retrieved docs', async ({ page, baseURL }) => {
  await page.goto(baseURL!);

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Send a query
  await page.locator('[data-testid="chat-input"]').fill('What is RAG?');
  await page.locator('[data-testid="chat-send"]').click();

  // Wait for answer
  await expect(page.locator('[data-testid="answer"]')).toBeVisible({ timeout: 15000 });

  // Check sources panel exists and has items
  const sourcesPanel = page.locator('[data-testid="sources-panel"]');
  await expect(sourcesPanel).toBeVisible({ timeout: 5000 });

  const sourceItems = page.locator('[data-testid="source-item"]');
  const count = await sourceItems.count();

  console.log(`Found ${count} source items`);
  expect(count).toBeGreaterThan(0);

  // Verify source items have required fields
  const firstSource = sourceItems.first();
  await expect(firstSource).toContainText(/doc_id|chunk_id|score/i);
});

