import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP-006A routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP006APortal"));
  assert.ok(appSource.includes('"architecture"'));
});

test("NCP-006A portal source includes architecture governance controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP006APortal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Governed Architecture Foundation",
    "Architecture Workspace",
    "Architecture Models",
    "Validation Center",
    "Fitness Center",
    "Review Center",
    "Approval Center",
    "Traceability Bridge",
    "Impact Viewer",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NovaCodePro registry keeps the architecture surface reachable for the right permissions", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/architecture", ["architecture.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/architecture", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/architecture/models/model-1"), {
    path: "/novacodepro/architecture/models/model-1",
    appId: "architecture",
    section: "architecture",
    subRoute: "/models/model-1",
  });
});
