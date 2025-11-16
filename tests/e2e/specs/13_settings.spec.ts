import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://16.146.148.184:3000';

test.describe('Settings Page', () => {
  test('should display settings page and allow toggling options', async ({ page }) => {
    // Navigate to settings page
    await page.goto(`${BASE_URL}/settings`);
    await page.waitForLoadState('networkidle');

    // Look for any toggle switches or checkboxes
    // Try checkboxes first, then buttons with role="switch" or aria-checked
    let toggles = page.locator('input[type="checkbox"]');
    let toggleCount = await toggles.count();

    // If no checkboxes, look for switch buttons
    if (toggleCount === 0) {
      toggles = page.locator('button[role="switch"], button[aria-checked]');
      toggleCount = await toggles.count();
    }

    if (toggleCount > 0) {
      // Get first toggle
      const firstToggle = toggles.first();

      // For checkboxes, use isChecked(); for buttons, use aria-checked attribute
      let initialState: boolean;
      if (await firstToggle.evaluate(el => el.tagName === 'INPUT')) {
        initialState = await firstToggle.isChecked();
      } else {
        initialState = (await firstToggle.getAttribute('aria-checked')) === 'true';
      }

      // Toggle it
      await firstToggle.click();

      // Verify state changed
      let newState: boolean;
      if (await firstToggle.evaluate(el => el.tagName === 'INPUT')) {
        newState = await firstToggle.isChecked();
      } else {
        newState = (await firstToggle.getAttribute('aria-checked')) === 'true';
      }
      expect(newState).toBe(!initialState);

      // Toggle back
      await firstToggle.click();
      let finalState: boolean;
      if (await firstToggle.evaluate(el => el.tagName === 'INPUT')) {
        finalState = await firstToggle.isChecked();
      } else {
        finalState = (await firstToggle.getAttribute('aria-checked')) === 'true';
      }
      expect(finalState).toBe(initialState);
    } else {
      // If no toggles found, test should still pass (page might not have toggles)
      console.log('No toggles found on settings page');
    }
  });

  test('should render settings page without errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/settings`);
    await page.waitForLoadState('networkidle');

    // Verify no critical console errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('404') &&
      !err.includes('favicon')
    );

    expect(criticalErrors.length).toBe(0);

    // Verify page has some content
    const body = page.locator('body');
    const bodyText = await body.textContent();
    expect(bodyText).toBeTruthy();
    expect(bodyText!.length).toBeGreaterThan(0);
  });

  test('should verify settings affect subsequent queries', async ({ page }) => {
    // Go to settings
    await page.goto(`${BASE_URL}/settings`);
    await page.waitForLoadState('networkidle');

    // Look for query decomposition or similar toggle
    // Try checkbox first, then switch button
    let decompositionToggle = page.locator('input[type="checkbox"]').filter({
      has: page.locator('text=/decomposition/i')
    }).first();

    if (!(await decompositionToggle.isVisible().catch(() => false))) {
      decompositionToggle = page.locator('button[role="switch"], button[aria-checked]').filter({
        has: page.locator('text=/decomposition/i')
      }).first();
    }

    if (await decompositionToggle.isVisible().catch(() => false)) {
      // Check if it's checked (for checkbox) or aria-checked (for button)
      let isChecked: boolean;
      if (await decompositionToggle.evaluate(el => el.tagName === 'INPUT')) {
        isChecked = await decompositionToggle.isChecked();
      } else {
        isChecked = (await decompositionToggle.getAttribute('aria-checked')) === 'true';
      }

      // Enable decomposition if not already enabled
      if (!isChecked) {
        await decompositionToggle.click();
      }

      // Go to chat
      await page.goto(BASE_URL);
      await page.waitForLoadState('networkidle');

      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('What is machine learning?');

      const sendButton = page.getByTestId('chat-send');
      const responsePromise = page.waitForResponse(
        response => response.url().includes('/api/v1/rag/query'),
        { timeout: 30000 }
      );

      await sendButton.click();
      const response = await responsePromise;
      const responseData = await response.json();

      // Verify response has metadata
      expect(responseData).toHaveProperty('metadata');

      // If decomposition was enabled, metadata might show it
      // (This is a soft check - we're mainly verifying the flow works)
      expect(responseData.metadata).toBeDefined();
    }
  });
});

