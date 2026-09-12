import { defineConfig, devices } from '@playwright/test';

/**
 * Clarere E2E — yerel Docker stack'ine karşı çalışır.
 * Ön koşul: `python launch.py` (frontend :4001, API Caddy üzerinden :8080).
 */
export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:4001',
    headless: true,
    viewport: { width: 1440, height: 900 },
    screenshot: 'only-on-failure',
    trace: 'off',
    actionTimeout: 30_000,
    navigationTimeout: 60_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  outputDir: './artifacts/test-results',
});
