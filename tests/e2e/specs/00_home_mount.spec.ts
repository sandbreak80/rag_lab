import { test, expect } from '@playwright/test';

test('app mounts and logs no fatal errors', async ({ page }) => {
  const messages: string[] = [];
  const errors: string[] = [];
  
  // Capture all console messages
  page.on('console', (msg) => {
    const text = `${msg.type()}: ${msg.text()}`;
    messages.push(text);
    if (msg.type() === 'error') {
      errors.push(text);
    }
  });

  // Navigate to homepage
  const baseURL = process.env.BASE_URL || 'http://localhost:3000';
  await page.goto(baseURL);

  // Wait for root to be mounted (with extended timeout)
  try {
    await page.waitForSelector('[data-testid="root-mounted"]', { timeout: 15000 });
    console.log('✅ React mounted successfully');
  } catch (e) {
    console.log('❌ React failed to mount');
    console.log('Console messages:', messages);
    console.log('Errors:', errors);
    throw e;
  }

  // Log all console messages for debugging
  console.log('=== Console Messages ===');
  messages.forEach(m => console.log(m));

  // Check for fatal errors
  const fatalErrors = errors.filter(e => 
    !e.includes('[OTEL') && 
    !e.includes('[WEBVITALS') &&
    !e.includes('DevTools')
  );

  if (fatalErrors.length > 0) {
    console.log('=== Fatal Errors ===');
    fatalErrors.forEach(e => console.log(e));
  }

  expect(fatalErrors).toHaveLength(0);
});

