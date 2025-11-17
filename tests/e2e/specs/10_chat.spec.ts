import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://16.146.148.184:3000';

test.describe('Chat Page', () => {
  test('should send message and receive answer with citations', async ({ page }) => {
    // Navigate to chat page
    await page.goto(BASE_URL);

    // Wait for page to be ready
    await page.waitForLoadState('networkidle');

    // Verify chat input is visible
    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible();

    // Type a query
    await chatInput.fill('What is RAG and how does it work?');

    // Click send button
    const sendButton = page.getByTestId('chat-send');
    await expect(sendButton).toBeVisible();

    // Wait for API response
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/v1/rag/query') && response.status() === 200,
      { timeout: 30000 }
    );

    await sendButton.click();

    // Wait for response
    const response = await responsePromise;
    const responseData = await response.json();

    // Verify response structure
    expect(responseData).toHaveProperty('answer');
    // API v1 returns 'citations' not 'sources'
    expect(responseData).toHaveProperty('citations');
    expect(responseData).toHaveProperty('artifacts');  // API returns artifacts not metadata

    // Wait for answer to appear in UI
    const answer = page.getByTestId('chat-answer');
    await expect(answer).toBeVisible({ timeout: 10000 });

    // Verify answer has content
    const answerText = await answer.textContent();
    expect(answerText).toBeTruthy();
    expect(answerText!.length).toBeGreaterThan(10);

    // Verify sources/citations are present
    const sources = page.getByTestId('chat-sources');
    await expect(sources).toBeVisible();

    // Verify at least one source item exists
    const sourceItem = page.locator('[data-testid^="chat-source-"]').first();
    await expect(sourceItem).toBeVisible();

    // Verify performance metrics are shown
    const perfBlock = page.getByTestId('chat-perf');
    await expect(perfBlock).toBeVisible();

    // Verify trace ID is present in API response
    expect(responseData).toHaveProperty('trace_id');
    expect(responseData.trace_id).toMatch(/[a-f0-9]{32}/); // 32-char hex trace ID

    // Verify metrics in API response
    expect(responseData).toHaveProperty('metrics');
    expect(responseData.metrics).toHaveProperty('latency_ms');
    expect(responseData.metrics.latency_ms).toBeGreaterThan(0);

    // Optional UI metrics checks (may not have test IDs yet)
    const traceIdElement = page.getByTestId('metrics-trace-id');
    if (await traceIdElement.isVisible().catch(() => false)) {
      const traceIdText = await traceIdElement.textContent();
      expect(traceIdText).toMatch(/[a-f0-9]{32}/);
    }

    const latencyElement = page.getByTestId('metrics-latency');
    if (await latencyElement.isVisible().catch(() => false)) {
      const latencyText = await latencyElement.textContent();
      expect(latencyText).toContain('ms');
    }
  });

  test('should handle empty query gracefully', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible();

    // Verify send button is disabled when input is empty
    const sendButton = page.getByTestId('chat-send');
    await expect(sendButton).toBeDisabled();

    // Verify button becomes enabled when text is entered
    await chatInput.fill('test');
    await expect(sendButton).toBeEnabled();

    // Clear input and verify button is disabled again
    await chatInput.clear();
    await expect(sendButton).toBeDisabled();
  });
});

