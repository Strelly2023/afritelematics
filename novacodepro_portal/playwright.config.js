import { defineConfig, devices } from "@playwright/test";

const frontendBaseUrl = "http://127.0.0.1:15173";
const backendBaseUrl = "http://127.0.0.1:18002";

export default defineConfig({
  testDir: "./tests/browser",
  outputDir: "test-results/browser",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL: frontendBaseUrl,
    locale: "en-AU",
    timezoneId: "Australia/Melbourne",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "venv/bin/python -m uvicorn afritech.api.app:app --host 127.0.0.1 --port 18002",
      cwd: "..",
      url: `${backendBaseUrl}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        AFRITECH_ENV: "test",
        AFRITECH_JWT_SECRET: "novacodepro-browser-test-secret",
        AFRITECH_RUNTIME_ENVIRONMENT: "TEST",
        AFRIRIDE_DB_PATH: "/private/tmp/novacodepro-browser-certification.sqlite3",
        AFRITECH_MIGRATION_STATE_PATH: "/private/tmp/novacodepro-browser-migrations.json",
        NOVATECH_RUNTIME_CONTROL_SQLITE_PATH: "/private/tmp/novacodepro-browser-control.sqlite3",
        NOVATECH_EVIDENCE_ROOT: "/private/tmp/novacodepro-browser-evidence",
      },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 15173 --strictPort",
      cwd: ".",
      url: `${frontendBaseUrl}/novacodepro/`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        VITE_NOVACODEPRO_PROXY_TARGET: backendBaseUrl,
      },
    },
  ],
});
