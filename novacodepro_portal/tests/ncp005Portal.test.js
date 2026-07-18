import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP-005 routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP005Portal"));
  assert.ok(appSource.includes('"requirements", "knowledge"'));
});

test("NCP-005 portal source includes requirements and knowledge controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP005Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Requirements Manager + Knowledge Hub",
    "Create requirement",
    "Create knowledge document",
    "Knowledge search",
    "Traceability coverage",
    "Knowledge documents",
    "Traceability links",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NovaCodePro registry keeps the NCP-005 surface reachable for the right permissions", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/requirements", ["requirements.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/knowledge", ["knowledge.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/knowledge", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/requirements/req-1"), {
    path: "/novacodepro/requirements/req-1",
    appId: "requirements",
    section: "requirements",
    subRoute: "/req-1",
  });
});
