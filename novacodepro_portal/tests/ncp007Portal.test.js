import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP-007 routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP007Portal"));
  assert.ok(appSource.includes('"development"'));
});

test("NCP-007 portal source includes governed development controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP007Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Development Studio",
    "Repository browser",
    "code generation",
    "validation, review, and approvals",
    "Commit proposal",
    "Evidence",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NovaCodePro registry keeps the development surface reachable for the right permissions", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/development", ["development.workspace.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/development", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/development/workspaces/ws-1"), {
    path: "/novacodepro/development/workspaces/ws-1",
    appId: "development",
    section: "development",
    subRoute: "/workspaces/ws-1",
  });
});
