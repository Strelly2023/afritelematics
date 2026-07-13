import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveWorkspaceLoginRoleFromPathname,
  resolveWorkspaceSlugFromLoginRole,
} from "../src/platform/workspaceRoutes.js";

test("developer workspace route resolves to developer login role", () => {
  assert.equal(resolveWorkspaceLoginRoleFromPathname("/novacodepro/workspace/developer"), "DEVELOPER");
});

test("admin workspace route resolves to admin login role", () => {
  assert.equal(resolveWorkspaceLoginRoleFromPathname("/novacodepro/workspace/admin"), "ADMIN");
});

test("login role resolves back to workspace slug", () => {
  assert.equal(resolveWorkspaceSlugFromLoginRole("DEVELOPER"), "developer");
  assert.equal(resolveWorkspaceSlugFromLoginRole("ADMIN"), "admin");
});

