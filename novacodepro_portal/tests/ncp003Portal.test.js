import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("NCP003 routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("NCP003Portal"));
  assert.ok(appSource.includes('"workspace", "projects", "requests"'));
});
test("NCP003 portal source includes project and request controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP003Portal.jsx", import.meta.url), "utf8");
  assert.ok(source.includes("Create project"));
  assert.ok(source.includes("Create request"));
  assert.ok(source.includes('data-testid="ncp003-authenticated-shell"'));
  assert.ok(source.includes('data-testid="workspace-home"'));
  assert.ok(source.includes('data-testid="projects-page"'));
  assert.ok(source.includes('data-testid="requests-page"'));
  assert.ok(source.includes("Archive project"));
  assert.ok(source.includes("Assign reviewer"));
  assert.ok(source.includes("Upload attachment"));
  assert.ok(source.includes("No milestones."));
});

test("NovaCodePro registry keeps the NCP003 surfaces reachable for the right permissions", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/workspace", ["workspace.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/projects", ["project.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/requests", ["request.create"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/security", ["workspace.read"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/requests"), {
    path: "/novacodepro/requests",
    appId: "requests",
    section: "requests",
    subRoute: "/",
  });
});
