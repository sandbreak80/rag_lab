import { test, expect } from '@playwright/test';

test('nginx /api rewrite works (no CORS)', async ({ request, baseURL }) => {
  const r = await request.post(`${baseURL}/api/v1/rag/query`, {
    data: { query: 'test', user_id: 'e2e', groups: [] },
    headers: {
      'Content-Type': 'application/json'
    }
  });

  expect(r.status()).toBe(200);
  const json = await r.json();
  expect(json).toHaveProperty('answer');
  expect(json).toHaveProperty('trace_id');
  console.log(`✓ API routed correctly via Nginx, trace_id: ${json.trace_id}`);
});

test('no CORS errors in browser console', async ({ page, baseURL }) => {
  const consoleErrors: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  await page.goto(baseURL!);
  await page.waitForLoadState('networkidle');

  // Submit a query to trigger API call
  const input = page.locator('textarea, [data-testid="chat-input"], input[type="text"]').first();
  await input.fill('CORS test query');

  const sendBtn = page.locator('button:has-text("Send"), [data-testid="chat-send"], button[type="submit"]').first();
  await sendBtn.click();

  await page.waitForTimeout(3000);

  // Check for CORS errors
  const corsErrors = consoleErrors.filter(err => err.toLowerCase().includes('cors'));
  expect(corsErrors.length).toBe(0);

  if (corsErrors.length > 0) {
    console.log('❌ CORS errors found:', corsErrors);
  } else {
    console.log('✓ No CORS errors detected');
  }
});

