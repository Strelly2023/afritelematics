import assert from "node:assert/strict";
import test from "node:test";

import {
  buildNovaCodeProAppLauncher,
  findNovaCodeProAppByPath,
  isNovaCodeProRouteAccessible,
  listNovaCodeProApps,
  parseNovaCodeProRoute,
} from "../src/platform/appRegistry.js";
import { ROUTES } from "../src/platform/routes.js";

test("NovaCodePro registry exposes the governed workspace surfaces", () => {
  const apps = listNovaCodeProApps();
  assert.ok(apps.length >= 10);
  assert.equal(apps[0].id, "workspace");
  assert.ok(apps.some((app) => app.id === "requests"));
  assert.ok(apps.some((app) => app.id === "projects"));
  assert.ok(apps.some((app) => app.id === "ai"));
});

test("NovaCodePro launcher honours permissions and preview states", () => {
  const launcher = buildNovaCodeProAppLauncher(["workspace.read", "request.create", "project.read"]);
  const workspace = launcher.find((app) => app.id === "workspace");
  const security = launcher.find((app) => app.id === "security");
  assert.equal(workspace.accessible, true);
  assert.equal(security.accessible, false);
  assert.equal(security.status, "preview");
});

test("NovaCodePro route parsing resolves the launcher surfaces", () => {
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/workspace"), {
    path: "/novacodepro/workspace",
    appId: "workspace",
    section: "workspace",
    subRoute: "/",
  });
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/projects"), {
    path: "/novacodepro/projects",
    appId: "projects",
    section: "projects",
    subRoute: "/",
  });
  assert.equal(findNovaCodeProAppByPath("/novacodepro/requests").id, "requests");
  assert.equal(ROUTES.workspaceRoot, "/novacodepro/workspace");
  assert.equal(ROUTES.requestsRoot, "/novacodepro/requests");
});

test("NovaCodePro route access blocks forbidden apps", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/workspace", ["workspace.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/security", ["workspace.read"]), false);
});
