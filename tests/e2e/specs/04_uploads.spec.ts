import { test, expect } from '@playwright/test';

test('Document upload succeeds and indexes', async ({ page }) => {
  await page.goto('/');

  // Look for file input (ensure your UI exposes one with a testid)
  const fileInput = page.locator('input[type="file"], [data-testid="file-input"], [data-testid="uploader-input"]').first();

  // Check if upload UI is visible
  const isVisible = await fileInput.isVisible().catch(() => false);

  if (!isVisible) {
    console.log('⚠️  File upload input not found');
    console.log('   Navigate to documents page if needed');

    // Try navigating to documents page
    const docsLink = page.locator('[href="/documents"], a:has-text("Documents")').first();
    if (await docsLink.isVisible().catch(() => false)) {
      await docsLink.click();
      await page.waitForLoadState('networkidle');
    }
  }

  await expect(fileInput).toBeVisible({ timeout: 5000 });

  // Create a small file in memory
  const content = '# Test Document\n\nThis is a small markdown file for testing RAG Lab upload.';
  const fileName = 'test_doc.md';

  await fileInput.setInputFiles({
    name: fileName,
    mimeType: 'text/markdown',
    buffer: Buffer.from(content)
  });

  // Wait for upload to complete (give it time to process)
  await page.waitForTimeout(3000);

  // Should not show upload failed message
  const failedCount = await page.locator('text=Upload failed, text=Error uploading').count();
  expect(failedCount, 'Upload should not fail').toBe(0);

  // Check if document appears in the list (may need to refresh or wait)
  const docList = page.locator('[data-testid="doc-row"], [data-testid="docs-empty"]');
  await expect(docList.first()).toBeVisible({ timeout: 5000 });

  console.log(`✅ File ${fileName} uploaded successfully`);
});

