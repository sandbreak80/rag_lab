import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './specs',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'playwright-report/results.xml' }]
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://frontend:3000',
    trace: 'retain-on-failure',
    video: 'off',
    screenshot: 'only-on-failure'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
  ],
  workers: 2
});

