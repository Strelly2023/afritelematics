import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

test("NCP-008 operations API client exposes the governed control surface", () => {
  const source = readFileSync(new URL("../src/novacodepro/api/novacodeproNcp008Api.js", import.meta.url), "utf8");
  for (const token of [
    "overview",
    "listEnvironments",
    "listServices",
    "listAlerts",
    "listIncidents",
    "createAction",
    "evaluateSlo",
    "validateRecoveryPlan",
  ]) {
    assert.ok(source.includes(token), `expected API client source to include ${token}`);
  }
});

test("Runtime config advertises the operations studio feature flag", () => {
  const source = readFileSync(new URL("../public/config/runtime.json", import.meta.url), "utf8");
  assert.ok(source.includes('"operationsStudio": true'));
  assert.ok(source.includes('"/api/v1/operations"'));
});
