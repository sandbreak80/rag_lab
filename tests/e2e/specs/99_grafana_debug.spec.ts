import { test, expect } from '@playwright/test';

test('Debug Grafana endpoint', async ({ page, baseURL }) => {
  const grafanaUrl = `${baseURL}/graf/`;
  
  console.log(`Testing Grafana URL: ${grafanaUrl}`);
  
  // Navigate to Grafana
  const response = await page.goto(grafanaUrl, { waitUntil: 'networkidle', timeout: 30000 });
  
  console.log(`Response status: ${response?.status()}`);
  console.log(`Final URL: ${page.url()}`);
  
  // Check if we got redirected
  if (page.url() !== grafanaUrl) {
    console.log(`Redirected from ${grafanaUrl} to ${page.url()}`);
  }
  
  // Wait a bit for page to load
  await page.waitForTimeout(2000);
  
  // Check page content
  const bodyText = await page.textContent('body');
  console.log(`Page body length: ${bodyText?.length || 0}`);
  console.log(`Page body preview: ${bodyText?.substring(0, 200)}`);
  
  // Check for Grafana indicators
  const hasGrafana = bodyText?.toLowerCase().includes('grafana') || false;
  const hasLogin = bodyText?.toLowerCase().includes('login') || false;
  
  console.log(`Has Grafana text: ${hasGrafana}`);
  console.log(`Has Login text: ${hasLogin}`);
  
  // Take screenshot for debugging
  await page.screenshot({ path: 'test-results/grafana-debug.png', fullPage: true });
  
  // Check for errors in console
  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  
  console.log(`Console errors: ${consoleErrors.length}`);
  consoleErrors.forEach(err => console.log(`  - ${err}`));
  
  // Basic check - page should load (even if it's a login page)
  expect(response?.status()).toBeOneOf([200, 301, 302]);
});

