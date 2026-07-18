import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP-008 portal is wired into the app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP008Portal"));
  assert.ok(appSource.includes('"operations"'));
});

test("NCP-008 portal source includes governed runtime operations controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP008Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Operations Studio",
    "Observability",
    "Post-Incident Reviews",
    "Request operational action",
    "Declare incident",
    "Recovery plans",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NCP-008 operations route is reachable with the correct permission", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/operations", ["operations.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/operations", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/operations/services/service-1"), {
    path: "/novacodepro/operations/services/service-1",
    appId: "operations",
    section: "operations",
    subRoute: "/services/service-1",
  });
});

