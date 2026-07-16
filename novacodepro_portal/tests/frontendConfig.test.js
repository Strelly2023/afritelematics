import assert from "node:assert/strict";
import test from "node:test";

import {
  createDefaultFrontendRuntimeConfig,
  loadFrontendRuntimeConfig,
  normalizeFrontendRuntimeConfig,
  resolveFrontendRuntimeConfigUrl,
} from "../src/platform/frontendConfig.js";

test("frontend runtime config falls back to build info defaults", () => {
  const config = createDefaultFrontendRuntimeConfig();
  assert.equal(config.environment, "production");
  assert.equal(config.enabledProducts.includes("novacodepro"), true);
  assert.equal(config.source, "build-info");
});

test("frontend runtime config normalizes runtime.json payloads", () => {
  const config = normalizeFrontendRuntimeConfig({
    environment: "public-pilot",
    region: "AU",
    releaseVersion: "2026.07.0",
    buildCommit: "ccc0329b7",
    apiBaseUrl: "https://api.afritechnology.com",
    authBaseUrl: "https://identity.afritechnology.com",
    websocketUrl: "wss://api.afritechnology.com/ws",
    enabledProducts: ["novacodepro", "solution-engineering"],
    defaultLocale: "en-AU",
    defaultTimezone: "Australia/Melbourne",
    maintenanceMode: false,
    source: "runtime.json",
  });

  assert.equal(config.environment, "public-pilot");
  assert.equal(config.apiBaseUrl, "https://api.afritechnology.com/");
  assert.equal(config.source, "runtime.json");
});

test("frontend runtime config loader prefers runtime.json when available", async () => {
  const originalFetch = global.fetch;
  const originalLocation = global.location;
  global.location = { origin: "https://novacodepro.afritechnology.com" };
  global.fetch = async () => ({
    ok: true,
    json: async () => ({
      environment: "staging",
      region: "AU",
      releaseVersion: "2026.07.1",
      buildCommit: "abc123",
      apiBaseUrl: "https://api.afritechnology.com",
      authBaseUrl: "https://identity.afritechnology.com",
      enabledProducts: ["novacodepro"],
      defaultLocale: "en-AU",
      defaultTimezone: "Australia/Melbourne",
      maintenanceMode: true,
    }),
  });

  try {
    const config = await loadFrontendRuntimeConfig();
    assert.equal(config.environment, "staging");
    assert.equal(config.maintenanceMode, true);
    assert.equal(config.source, "runtime.json");
    assert.equal(resolveFrontendRuntimeConfigUrl(), "https://novacodepro.afritechnology.com/config/runtime.json");
  } finally {
    global.fetch = originalFetch;
    global.location = originalLocation;
  }
});
