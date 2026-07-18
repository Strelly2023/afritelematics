import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

test("NCP-006B design portal exposes protected states and route labels", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP006BPortal.jsx", import.meta.url), "utf8");
  for (const token of [
    "loading",
    "version_conflict",
    "review_required",
    "approval_required",
    "ready_for_implementation",
    "AI_provider_unavailable",
    "design_drift_source_unavailable",
    "/novacodepro/design/workspaces",
    "/novacodepro/design/traceability",
    "/novacodepro/design/handoffs",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});
