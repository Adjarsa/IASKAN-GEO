import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '/app/tests/e2e',
  outputDir: '/root/.emergent/automation_output/20260224_124053/test-results',
  timeout: 60000,
  retries: 0,
  workers: 1,
  reporter: [
    ['line'],
    ['json', { outputFile: '/root/.emergent/automation_output/20260224_124053/results.json' }],
  ],
  use: {
    baseURL: 'https://ai-visibility-hub-4.preview.emergentagent.com',
    screenshot: 'only-on-failure',
    trace: 'off',
    headless: true,
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
