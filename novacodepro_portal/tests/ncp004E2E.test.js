import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("NCP-004 portal surface exposes governed AI lifecycle controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP004Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "/novacodepro/ai",
    "/novacodepro/ai/executions",
    "client.generateRequirements",
    "client.generatePlan",
    "client.requestApproval",
    "client.execute",
    "client.verifyExecution",
    "client.rollbackExecution",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});
