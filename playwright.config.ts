import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for RAG Lab E2E Tests
 * 
 * Run tests:
 *   Local:     npx playwright test
 *   Docker:    docker compose run --rm playwright npx playwright test
 *   Headed:    npx playwright test --headed
 *   Debug:     npx playwright test --debug
 *   UI Mode:   npx playwright test --ui
 */

export default defineConfig({
  testDir: './tests/e2e',
  
  // Maximum time one test can run
  timeout: 90 * 1000,
  
  // Maximum time for expect() assertions
  expect: {
    timeout: 10000
  },

  // Run tests in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Parallel workers
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter config
  reporter: [
    ['html', { outputFolder: 'tests/e2e/playwright-report' }],
    ['json', { outputFile: 'tests/e2e/test-results.json' }],
    ['list']
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL from environment or default
    baseURL: process.env.BASE_URL || 'http://16.146.148.184:3000',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Timeout for each action (click, fill, etc.)
    actionTimeout: 15000,
    
    // Navigation timeout
    navigationTimeout: 30000,
  },

  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    },

    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
    },

    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
    },

    // Mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 13'] },
    },
  ],

  // Web server (if testing locally)
  // webServer: {
  //   command: 'docker compose up frontend rag-api-v1',
  //   url: 'http://localhost:3000',
  //   timeout: 120 * 1000,
  //   reuseExistingServer: !process.env.CI,
  // },
});

