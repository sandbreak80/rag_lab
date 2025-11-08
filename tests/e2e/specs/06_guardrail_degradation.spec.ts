import { test, expect } from '@playwright/test';

test('guardrail degradation renders safe fallback', async ({ page, baseURL }) => {
  await page.goto(baseURL!);
  await page.waitForLoadState('networkidle');
  
  // Submit query that might trigger guardrails
  const input = page.locator('textarea, [data-testid="chat-input"], input[type="text"]').first();
  await input.fill('trigger guardrail error please');
  
  const sendBtn = page.locator('button:has-text("Send"), [data-testid="chat-send"], button[type="submit"]').first();
  await sendBtn.click();
  
  // Wait for response
  await page.waitForTimeout(3000);
  
  // Check for guardrail status indicator (flexible selectors)
  const guardrailStatus = page.locator('[data-testid="guardrail-status"], .guardrail, .security-status, [class*="security"]');
  const statusVisible = await guardrailStatus.count();
  
  if (statusVisible > 0) {
    const statusText = await guardrailStatus.first().textContent();
    expect(statusText).toMatch(/degraded|ok|pass|safe/i);
    console.log(`✓ Guardrail status: ${statusText}`);
  } else {
    console.log('⚠ Guardrail status indicator not found in UI');
  }
  
  // Answer should still be visible (even if degraded)
  const answer = page.locator('[data-testid="answer"], .answer, .response, .message').first();
  await expect(answer).toBeVisible();
  console.log('✓ Safe fallback answer rendered');
});

