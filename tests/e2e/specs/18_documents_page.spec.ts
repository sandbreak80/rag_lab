import { test, expect } from '@playwright/test';

test.describe('Documents Page', () => {
  test('should load documents page without errors', async ({ page }) => {
    // Navigate to documents page
    await page.goto('/documents');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Wait a bit for any async errors
    await page.waitForTimeout(2000);

    // Check that page is still visible (not blank)
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // Check for error boundary
    const errorBoundary = page.locator('text=/Something went wrong/i');
    const hasError = await errorBoundary.count();

    if (hasError > 0) {
      const errorText = await errorBoundary.textContent();
      console.error('Error Boundary triggered:', errorText);
      throw new Error(`Error Boundary caught error: ${errorText}`);
    }

    // Check for console errors
    if (errors.length > 0) {
      console.error('Console errors:', errors);
      throw new Error(`Console errors detected: ${errors.join(', ')}`);
    }

    // Verify page content exists
    const documentsTitle = page.locator('text=/Your Documents/i');
    await expect(documentsTitle).toBeVisible({ timeout: 5000 });
  });

  test('should display document list or empty state', async ({ page }) => {
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');

    // Should either show documents or empty state
    const hasDocuments = await page.locator('[data-testid="doc-row"]').count();
    const hasEmptyState = await page.locator('text=/No documents yet/i').count();

    expect(hasDocuments > 0 || hasEmptyState > 0).toBeTruthy();
  });
});

