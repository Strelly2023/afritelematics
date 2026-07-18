import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP-006B routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP006BPortal"));
  assert.ok(appSource.includes('"design"'));
});

test("NCP-006B portal source includes design studio controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP006BPortal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Governed Design Studio and Experience System",
    "Experience Workspace",
    "Experience Brief",
    "Journey Map",
    "Service Blueprint",
    "Design System",
    "Design Tokens",
    "Accessibility requirements",
    "Design traceability matrix",
    "Design handoff viewer",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NovaCodePro registry keeps the design surface reachable for the right permissions", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/design", ["design.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/design", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/design/briefs/brief-1"), {
    path: "/novacodepro/design/briefs/brief-1",
    appId: "design",
    section: "design",
    subRoute: "/briefs/brief-1",
  });
});
