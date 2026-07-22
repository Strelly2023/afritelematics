import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveWorkspaceLoginRoleFromPathname,
  resolveWorkspaceSlugFromLoginRole,
} from "../src/platform/workspaceRoutes.js";
import { ROUTES } from "../src/platform/routes.js";

test("developer workspace route resolves to developer login role", () => {
  assert.equal(
    resolveWorkspaceLoginRoleFromPathname("/novacodepro/workspace/developer/dashboard"),
    "DEVELOPER",
  );
});

test("admin workspace route resolves to admin login role", () => {
  assert.equal(resolveWorkspaceLoginRoleFromPathname("/novacodepro/workspace/admin/dashboard"), "ADMIN");
});

test("login role resolves back to workspace slug", () => {
  assert.equal(resolveWorkspaceSlugFromLoginRole("DEVELOPER"), "developer");
  assert.equal(resolveWorkspaceSlugFromLoginRole("ADMIN"), "admin");
  assert.equal(resolveWorkspaceSlugFromLoginRole("PLATFORM_ADMIN"), "admin");
});

test("canonical role workspace route is dashboard based", () => {
  assert.equal(ROUTES.login, "/novacodepro/login");
  assert.equal(ROUTES.dashboard, "/novacodepro/dashboard");
  assert.equal(ROUTES.logout, "/novacodepro/logout");
  assert.equal(ROUTES.strategyRoot, "/novacodepro/strategy");
  assert.equal(ROUTES.roleDashboard("ADMIN"), "/novacodepro/workspace/admin/dashboard");
  assert.equal(ROUTES.roleDashboard("DEVELOPER"), "/novacodepro/workspace/developer/dashboard");
});
