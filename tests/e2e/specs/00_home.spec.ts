import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page, baseURL }) => {
  await page.goto(baseURL!);
  await expect(page).toHaveTitle(/Neural Vault/i);
  await expect(page.locator('body')).toContainText(/Neural Vault|Educational RAG Lab|RAG Lab/i);
});

