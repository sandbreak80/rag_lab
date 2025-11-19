import { test, expect } from '@playwright/test';

test.describe('Version Check', () => {
  test('should display correct version in bottom right corner', async ({ page }) => {
    // Navigate to homepage on AWS
    await page.goto('http://16.146.36.90:3000/');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Wait for version footer to be visible
    await page.waitForSelector('text=/UI: v/', { timeout: 10000 });

    // Take screenshot of the page
    await page.screenshot({
      path: 'tests/e2e/version-check-screenshot.png',
      fullPage: true
    });

    // Find the version footer element
    const versionFooter = page.locator('text=/UI: v/').first();

    // Verify it's visible
    await expect(versionFooter).toBeVisible();

    // Get the version text
    const versionText = await versionFooter.textContent();
    console.log('Version displayed on page:', versionText);

    // Extract version number
    const versionMatch = versionText?.match(/UI: v([\d.]+(?:-[a-z-]+)?)/i);
    const displayedVersion = versionMatch ? versionMatch[1] : null;

    console.log('Extracted version:', displayedVersion);

    // Verify version is displayed
    expect(displayedVersion).not.toBeNull();
    expect(displayedVersion).toBeTruthy();

    // Verify version matches expected version (2.2.0-ab-testing)
    const expectedVersion = '2.2.0-ab-testing';
    expect(displayedVersion).toBe(expectedVersion);

    // Take a close-up screenshot of the version footer area
    const footerElement = page.locator('div').filter({ hasText: /UI: v/ }).first();
    await footerElement.screenshot({
      path: 'tests/e2e/version-footer-closeup.png'
    });

    // Log the full version text for verification
    const fullFooterText = await footerElement.textContent();
    console.log('Full footer text:', fullFooterText);
  });
});

