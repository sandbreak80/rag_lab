import { defineConfig, devices } from '@playwright/test';

// Default BASE_URL depends on where tests are run:
// - From Docker network: http://frontend:80 (internal container port)
// - From host: http://localhost:3000 (host-mapped port)
// Override by setting BASE_URL environment variable
const BASE_URL = process.env.BASE_URL || 'http://frontend:80';
const HEADLESS = process.env.PW_HEADLESS !== '0';

export default defineConfig({
  testDir: './specs',
  timeout: 60_000,
  expect: { timeout: 10_000 },

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'playwright-report/results.xml' }]
  ],

  use: {
    baseURL: BASE_URL,
    headless: HEADLESS,
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  workers: 2,
});
