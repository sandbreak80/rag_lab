import { test, expect } from '@playwright/test';
import path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://16.146.148.184:3000';

test.describe('Documents Page', () => {
  test('should upload document and verify it appears in RAG citations', async ({ page }) => {
    // Navigate to documents page
    await page.goto(`${BASE_URL}/documents`);
    await page.waitForLoadState('networkidle');

    // Verify upload zone is visible
    const uploadZone = page.getByTestId('upload-zone');
    await expect(uploadZone).toBeVisible();

    // Get the file input
    const fileInput = page.getByTestId('upload-input');

    // Upload test file
    const testFilePath = path.join(__dirname, '../fixtures/sample_rag_basics.txt');
    await fileInput.setInputFiles(testFilePath);

    // Wait for upload to complete
    await page.waitForResponse(
      response => response.url().includes('/api/v1/documents') && response.status() === 200,
      { timeout: 15000 }
    );

    // Verify upload success (check for uploaded item or success message)
    const uploadList = page.getByTestId('upload-list');
    await expect(uploadList).toBeVisible({ timeout: 5000 });

    // Wait a bit for indexing to complete
    await page.waitForTimeout(3000);

    // Now go to chat and query about the uploaded content
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible();

    // Query about content from the uploaded file
    await chatInput.fill('What is retrieval augmented generation?');

    const sendButton = page.getByTestId('chat-send');

    // Wait for RAG query response
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/v1/rag/query') && response.status() === 200,
      { timeout: 30000 }
    );

    await sendButton.click();
    const response = await responsePromise;
    const responseData = await response.json();

    // Verify we got sources from RAG
    expect(responseData).toHaveProperty('sources');
    expect(responseData.sources).toBeDefined();
    expect(responseData.sources.length).toBeGreaterThan(0);

    // Check if any source is from our uploaded document
    const hasRagSource = responseData.sources.some((source: any) =>
      source.origin_tool === 'rag' || source.content.includes('retrieval')
    );
    expect(hasRagSource).toBeTruthy();

    // Verify answer appears
    const answer = page.getByTestId('chat-answer');
    await expect(answer).toBeVisible({ timeout: 10000 });

    // Verify citations are shown
    const sources = page.getByTestId('chat-sources');
    await expect(sources).toBeVisible();

    // Verify at least one citation badge
    const sourceItem = page.locator('[data-testid^="chat-source-"]').first();
    await expect(sourceItem).toBeVisible();
  });

  test('should show upload zone on documents page', async ({ page }) => {
    await page.goto(`${BASE_URL}/documents`);
    await page.waitForLoadState('networkidle');

    // Verify upload zone exists
    const uploadZone = page.getByTestId('upload-zone');
    await expect(uploadZone).toBeVisible();

    // Verify file input exists
    const fileInput = page.getByTestId('upload-input');
    await expect(fileInput).toBeAttached();
  });
});

