import { test, expect } from '@playwright/test';

test.describe('Prompts Tab Navigation', () => {
  test('should display Prompts tab in navigation', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');
    
    // Wait for navigation to load
    await page.waitForSelector('nav', { timeout: 10000 });
    
    // Check if Prompts tab exists
    const promptsTab = page.locator('nav').getByRole('link', { name: /prompts/i });
    
    // Verify tab is visible
    await expect(promptsTab).toBeVisible({ timeout: 5000 });
    
    // Verify tab has correct text
    await expect(promptsTab).toContainText(/prompts/i);
  });

  test('should navigate to prompts page when clicked', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');
    
    // Wait for navigation
    await page.waitForSelector('nav', { timeout: 10000 });
    
    // Find and click Prompts tab
    const promptsTab = page.locator('nav').getByRole('link', { name: /prompts/i });
    await expect(promptsTab).toBeVisible();
    await promptsTab.click();
    
    // Verify URL changed
    await expect(page).toHaveURL(/.*\/prompts/, { timeout: 5000 });
    
    // Verify page loaded (check for prompts page content)
    await page.waitForSelector('h1', { timeout: 5000 });
    const heading = page.locator('h1');
    await expect(heading).toContainText(/system prompts/i);
  });

  test('should display prompt list on prompts page', async ({ page }) => {
    // Navigate directly to prompts page
    await page.goto('/prompts');
    
    // Wait for page to load
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // Verify heading
    const heading = page.locator('h1');
    await expect(heading).toContainText(/system prompts/i);
    
    // Verify prompt list exists (should have at least one prompt)
    const promptList = page.locator('text=/rag synthesis|query expansion|research/i');
    await expect(promptList.first()).toBeVisible({ timeout: 5000 });
  });

  test('should have Prompts tab in correct position', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');
    
    // Wait for navigation
    await page.waitForSelector('nav', { timeout: 10000 });
    
    // Get all navigation links
    const navLinks = page.locator('nav a');
    const linkTexts = await navLinks.allTextContents();
    
    // Find Prompts tab index
    const promptsIndex = linkTexts.findIndex(text => text.toLowerCase().includes('prompts'));
    
    // Verify Prompts tab exists
    expect(promptsIndex).toBeGreaterThan(-1);
    
    // Verify it's after Research Agent and before Settings (rough position check)
    const researchIndex = linkTexts.findIndex(text => text.toLowerCase().includes('research'));
    const settingsIndex = linkTexts.findIndex(text => text.toLowerCase().includes('settings'));
    
    if (researchIndex >= 0 && settingsIndex >= 0) {
      expect(promptsIndex).toBeGreaterThan(researchIndex);
      expect(promptsIndex).toBeLessThan(settingsIndex);
    }
  });
});

