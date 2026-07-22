import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const launcher = readFileSync(new URL("../scripts/dev-local.mjs", import.meta.url), "utf8");
const playwright = readFileSync(new URL("../playwright.config.js", import.meta.url), "utf8");

test("default development command launches a health-gated local API and Vite", () => {
  assert.equal(packageJson.scripts.dev, "node scripts/dev-local.mjs");
  assert.equal(packageJson.scripts["dev:frontend"], "vite --host 127.0.0.1");
  for (const token of ["afritech.api.app:app", "/health", "VITE_NOVACODEPRO_PROXY_TARGET", "waitForApi", "SIGINT", "SIGTERM"]) {
    assert.match(launcher, new RegExp(token.replaceAll("/", "\\/")));
  }
});

test("browser certification uses frontend-only mode because it owns its API server", () => {
  assert.match(playwright, /npm run dev:frontend/);
});
