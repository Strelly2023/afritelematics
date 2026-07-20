import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const frontendBaseUrl = process.env.PW_FRONTEND_BASE_URL || "http://127.0.0.1:4173";
const backendBaseUrl = process.env.PW_BACKEND_BASE_URL || "http://127.0.0.1:8001";
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const skipBackendWebServer = process.env.PLAYWRIGHT_SKIP_BACKEND === "1";

export default defineConfig({
  testDir: "./tests/browser",
  outputDir: "test-results/browser",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report" }],
    ["junit", { outputFile: "test-results/browser-junit.xml" }],
  ],
  use: {
    baseURL: frontendBaseUrl,
    locale: "en-AU",
    timezoneId: "Australia/Melbourne",
    viewport: { width: 1440, height: 1024 },
    colorScheme: "light",
    reducedMotion: "reduce",
    trace: "on-first-retry",
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
    ...(skipBackendWebServer
      ? []
      : [
          {
            command:
              "bash -lc 'mkdir -p /private/tmp/novaride-browser-certification/evidence && python -m uvicorn afritech.api.app:app --host 127.0.0.1 --port 8001'",
            cwd: "../..",
            url: `${backendBaseUrl}/health`,
            reuseExistingServer: !process.env.CI,
            timeout: 120_000,
            env: {
              PYTHONPATH: repoRoot,
              AFRITECH_ENV: "test",
              AFRITECH_JWT_SECRET: "novaride-browser-test-secret",
              AFRITECH_RUNTIME_ENVIRONMENT: "TEST",
              AFRIRIDE_DB_PATH: "/private/tmp/novaride-browser-certification.sqlite3",
              AFRITECH_MIGRATION_STATE_PATH: "/private/tmp/novaride-browser-migrations.json",
              NOVATECH_RUNTIME_CONTROL_SQLITE_PATH: "/private/tmp/novaride-browser-control.sqlite3",
              NOVATECH_EVIDENCE_ROOT: "/private/tmp/novaride-browser-certification/evidence",
              NOVARIDE_ENVIRONMENT: "test",
              NOVARIDE_REGION: "AU",
              NOVARIDE_TENANT: "novaride-tenant",
              NOVARIDE_PAYMENT_MODE: "sandbox_or_controlled_pilot",
            },
          },
        ]),
    {
      command: "npm run build && npx vite preview --host 127.0.0.1 --port 4173 --strictPort",
      cwd: ".",
      url: frontendBaseUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        VITE_NOVARIDE_OPERATIONS_BASE_URL: `${backendBaseUrl}/v1/novaride/operations`,
        VITE_NOVARIDE_AUTH_BASE_URL: backendBaseUrl,
        VITE_NOVARIDE_OPERATIONS_LIVE_MAP_ENABLED: "true",
        VITE_NOVARIDE_OPERATIONS_REFUND_EXECUTION_ENABLED: "true",
        VITE_NOVARIDE_OPERATIONS_PRODUCTION_ACTIONS_ENABLED: "true",
      },
    },
  ],
});
