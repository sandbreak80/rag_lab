import { test, expect } from '@playwright/test';

test('Load Grafana login page', async ({ page, baseURL }) => {
  // Test Grafana on direct port 3001 (bypasses proxy redirect loop)
  // Use the external IP from environment or default to the known instance IP
  const baseHost = process.env.EXTERNAL_HOST || '16.146.36.90';
  const grafanaUrl = `http://${baseHost}:3001`;

  console.log(`\n🌐 Testing Grafana on direct port: ${grafanaUrl}`);

  // Track all network requests
  const requests: string[] = [];
  const responses: Array<{ url: string; status: number }> = [];

  page.on('request', request => {
    requests.push(`${request.method()} ${request.url()}`);
  });

  page.on('response', response => {
    responses.push({ url: response.url(), status: response.status() });
    if (response.status() >= 400) {
      console.log(`  ❌ Response: ${response.status()} ${response.url()}`);
    } else {
      console.log(`  ✅ Response: ${response.status()} ${response.url()}`);
    }
  });

  // Navigate to Grafana
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
    const preview = bodyText.substring(0, 500).replace(/\s+/g, ' ');
    console.log(`📝 Page body preview: ${preview}...`);
  }

  // Check for Grafana indicators
  const hasGrafana = bodyText?.toLowerCase().includes('grafana') || false;
  const hasLogin = bodyText?.toLowerCase().includes('login') || false;
  const hasUsername = bodyText?.toLowerCase().includes('username') || false;
  const hasPassword = bodyText?.toLowerCase().includes('password') || false;
  const hasSignIn = bodyText?.toLowerCase().includes('sign in') || false;

  console.log(`\n🔍 Content checks:`);
  console.log(`  - Has "Grafana" text: ${hasGrafana}`);
  console.log(`  - Has "Login" text: ${hasLogin}`);
  console.log(`  - Has "Username" text: ${hasUsername}`);
  console.log(`  - Has "Password" text: ${hasPassword}`);
  console.log(`  - Has "Sign In" text: ${hasSignIn}`);

  // Check for login form elements
  const loginForm = await page.locator('form, [class*="login"], [class*="signin"], input[type="password"]').count();
  console.log(`\n🎯 Login form elements found: ${loginForm}`);

  const usernameInput = await page.locator('input[name="user"], input[type="text"], input[placeholder*="user"], input[placeholder*="email"]').count();
  console.log(`  - Username input fields: ${usernameInput}`);

  const passwordInput = await page.locator('input[type="password"]').count();
  console.log(`  - Password input fields: ${passwordInput}`);

  const submitButton = await page.locator('button[type="submit"], button:has-text("Sign"), button:has-text("Login")').count();
  console.log(`  - Submit buttons: ${submitButton}`);

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
  consoleErrors.slice(0, 10).forEach(err => console.log(`  - ERROR: ${err}`));

  console.log(`\n⚠️  Console warnings: ${consoleWarnings.length}`);
  consoleWarnings.slice(0, 5).forEach(warn => console.log(`  - WARN: ${warn}`));

  // Check network requests
  console.log(`\n🌐 Network requests: ${requests.length}`);
  requests.slice(0, 15).forEach(req => console.log(`  - ${req}`));

  // Check for failed requests
  const failedRequests = responses.filter(r => r.status >= 400);
  if (failedRequests.length > 0) {
    console.log(`\n❌ Failed requests: ${failedRequests.length}`);
    failedRequests.forEach(req => console.log(`  - ${req.status} ${req.url}`));
  }

  // Take screenshot for debugging
  try {
    await page.screenshot({
      path: 'test-results/grafana-login-debug.png',
      fullPage: true
    });
    console.log(`\n📸 Screenshot saved to test-results/grafana-login-debug.png`);
  } catch (e) {
    console.log(`\n❌ Failed to take screenshot: ${e}`);
  }

  // Summary
  console.log(`\n📊 Summary:`);
  console.log(`  - Final URL: ${page.url()}`);
  console.log(`  - Response status: ${response?.status()}`);
  console.log(`  - Page loaded: ${!!bodyText}`);
  console.log(`  - Looks like Grafana login: ${hasGrafana && (hasLogin || hasUsername || hasPassword)}`);
  console.log(`  - Has login form: ${loginForm > 0 || (usernameInput > 0 && passwordInput > 0)}`);

  // Assertions
  const status = response?.status() || 0;
  expect([200, 301, 302]).toContain(status);

  // Page should have loaded successfully
  expect(status).toBe(200);

  // Should have Grafana content
  expect(hasGrafana).toBe(true);

  // Should have login form elements
  expect(loginForm > 0 || (usernameInput > 0 && passwordInput > 0)).toBe(true);
});

