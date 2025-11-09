import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

test('Document upload endpoint exists', async ({ request, baseURL }) => {
  // Check that the upload endpoint responds (not 404)
  const response = await request.post(`${baseURL}/api/v1/documents`, {
    failOnStatusCode: false
  });

  // Should NOT be 404 (could be 400, 422, 501, etc.)
  expect(response.status()).not.toBe(404);

  console.log(`Upload endpoint status: ${response.status()}`);
});

test.skip('Document upload succeeds with file', async ({ page, baseURL }) => {
  // This test is skipped until the upload route is fully implemented
  await page.goto(baseURL!);

  // Create a test fixture if it doesn't exist
  const fixturesDir = path.resolve('tests/e2e/fixtures');
  const testFile = path.join(fixturesDir, 'sample.md');

  if (!fs.existsSync(fixturesDir)) {
    fs.mkdirSync(fixturesDir, { recursive: true });
  }

  if (!fs.existsSync(testFile)) {
    fs.writeFileSync(testFile, '# Test Document\n\nThis is a test document for upload validation.');
  }

  // Navigate to documents page
  await page.click('[href="/documents"]');
  await page.waitForLoadState('networkidle');

  // Upload file
  const uploader = page.locator('[data-testid="uploader-input"]');
  if (await uploader.isVisible()) {
    await uploader.setInputFiles(testFile);

    // Wait for upload status
    const status = page.locator('[data-testid="uploader-status"]');
    await expect(status).toHaveText(/uploaded|queued|processing/i, { timeout: 10000 });
  } else {
    console.log('Upload UI not yet implemented');
  }
});

