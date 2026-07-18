import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP-004 routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP004Portal"));
  assert.ok(appSource.includes('"ai"'));
});

test("NCP-004 portal source includes governed execution controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP004Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Governed NovaAI orchestration",
    "Start NovaAI execution",
    "Generate plan",
    "Request approval",
    "Replay",
    "Clarifications",
    "Verification and evidence",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NovaCodePro registry keeps the NCP-004 surface reachable for the right permissions", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/ai", ["ai.request"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/ai/executions/exec-1", ["ai.request"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/ai", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/ai/executions/exec-1"), {
    path: "/novacodepro/ai/executions/exec-1",
    appId: "ai",
    section: "ai",
    subRoute: "/executions/exec-1",
  });
});
