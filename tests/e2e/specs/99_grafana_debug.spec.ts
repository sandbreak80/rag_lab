import { test, expect } from '@playwright/test';

test('Debug Grafana endpoint', async ({ page, baseURL }) => {
  // When running in Docker, use internal service name instead of localhost
  let testUrl = baseURL || 'http://localhost:3000';
  if (testUrl.includes('localhost:3000') || testUrl.includes('127.0.0.1:3000')) {
    // Running in Docker - use internal service name
    testUrl = 'http://frontend:80';
    console.log(`\n🐳 Running in Docker - using internal service URL: ${testUrl}`);
  }

  const grafanaUrl = `${testUrl}/graf/`;

  console.log(`\n🔍 Testing Grafana URL: ${grafanaUrl}`);

  // Track all network requests
  const requests: string[] = [];
  const responses: Array<{ url: string; status: number }> = [];

  page.on('request', request => {
    requests.push(`${request.method()} ${request.url()}`);
  });

  page.on('response', response => {
    responses.push({ url: response.url(), status: response.status() });
    console.log(`  Response: ${response.status()} ${response.url()}`);
  });

  // Navigate to Grafana with redirect following
  console.log(`\n📥 Navigating to ${grafanaUrl}...`);
  const response = await page.goto(grafanaUrl, {
    waitUntil: 'domcontentloaded',
    timeout: 30000
  });

  console.log(`\n✅ Initial response status: ${response?.status()}`);
  console.log(`📍 Final URL after redirects: ${page.url()}`);

  // Wait for page to stabilize
  await page.waitForTimeout(3000);

  // Check page title
  const title = await page.title();
  console.log(`\n📄 Page title: "${title}"`);

  // Check page content
  const bodyText = await page.textContent('body');
  console.log(`\n📝 Page body length: ${bodyText?.length || 0} characters`);

  if (bodyText) {
    const preview = bodyText.substring(0, 300).replace(/\s+/g, ' ');
    console.log(`📝 Page body preview: ${preview}...`);
  }

  // Check for Grafana indicators
  const hasGrafana = bodyText?.toLowerCase().includes('grafana') || false;
  const hasLogin = bodyText?.toLowerCase().includes('login') || false;
  const hasDashboard = bodyText?.toLowerCase().includes('dashboard') || false;

  console.log(`\n🔍 Content checks:`);
  console.log(`  - Has "Grafana" text: ${hasGrafana}`);
  console.log(`  - Has "Login" text: ${hasLogin}`);
  console.log(`  - Has "Dashboard" text: ${hasDashboard}`);

  // Check for specific Grafana elements
  const grafanaElements = await page.locator('body').count();
  console.log(`\n🎯 Body element found: ${grafanaElements > 0}`);

  // Check for common Grafana selectors
  const loginForm = await page.locator('form, [class*="login"], [class*="signin"]').count();
  console.log(`  - Login form elements: ${loginForm}`);

  const grafanaLogo = await page.locator('[alt*="Grafana"], [class*="logo"], img[src*="grafana"]').count();
  console.log(`  - Grafana logo/images: ${grafanaLogo}`);

  // Check for errors in console
  const consoleErrors: string[] = [];
  const consoleWarnings: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    } else if (msg.type() === 'warning') {
      consoleWarnings.push(msg.text());
    }
  });

  console.log(`\n⚠️  Console errors: ${consoleErrors.length}`);
  consoleErrors.forEach(err => console.log(`  - ERROR: ${err}`));

  console.log(`\n⚠️  Console warnings: ${consoleWarnings.length}`);
  consoleWarnings.slice(0, 5).forEach(warn => console.log(`  - WARN: ${warn}`));

  // Check network requests
  console.log(`\n🌐 Network requests: ${requests.length}`);
  requests.slice(0, 10).forEach(req => console.log(`  - ${req}`));

  // Take screenshot for debugging
  try {
    await page.screenshot({
      path: 'test-results/grafana-debug.png',
      fullPage: true
    });
    console.log(`\n📸 Screenshot saved to test-results/grafana-debug.png`);
  } catch (e) {
    console.log(`\n❌ Failed to take screenshot: ${e}`);
  }

  // Summary
  console.log(`\n📊 Summary:`);
  console.log(`  - Final URL: ${page.url()}`);
  console.log(`  - Response status: ${response?.status()}`);
  console.log(`  - Page loaded: ${!!bodyText}`);
  console.log(`  - Looks like Grafana: ${hasGrafana || hasLogin || hasDashboard}`);

  // Basic check - page should load (even if it's a login page or redirect)
  expect(response?.status()).toBeOneOf([200, 301, 302]);

  // If we got redirected, the final URL should still be a Grafana URL
  if (page.url() !== grafanaUrl) {
    expect(page.url()).toMatch(/\/graf/);
  }
});

