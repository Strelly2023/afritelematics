import assert from "node:assert/strict";
import test from "node:test";

import {
  SOLUTION_NAV_GROUP,
  buildSolutionProjectPath,
  parseSolutionRoute,
  solutionNavigationForRole,
  solutionRoleCanAccessSection,
} from "../src/platform/solutionRoutes.js";
import { ROUTES } from "../src/platform/routes.js";

test("solution routes preserve the /novacodepro base path", () => {
  assert.equal(ROUTES.solutionRoot, "/novacodepro/solutions");
  assert.equal(ROUTES.solutionCustomers, "/novacodepro/solutions/customers");
  assert.equal(buildSolutionProjectPath("proj-1", "requirements"), "/novacodepro/solutions/projects/proj-1/requirements");
});

test("solution route parser resolves landing and project routes", () => {
  assert.deepEqual(parseSolutionRoute("/novacodepro/solutions"), {
    kind: "landing",
    section: "overview",
    path: "/novacodepro/solutions",
  });
  assert.deepEqual(parseSolutionRoute("/novacodepro/solutions/customers"), {
    kind: "landing",
    section: "customers",
    path: "/novacodepro/solutions/customers",
  });
  assert.deepEqual(parseSolutionRoute("/novacodepro/solutions/projects/proj-7/architecture"), {
    kind: "project",
    projectId: "proj-7",
    section: "architecture",
    path: "/novacodepro/solutions/projects/proj-7/architecture",
  });
});

test("solution navigation is role aware and excludes unauthorized sections", () => {
  const customerNav = solutionNavigationForRole("CUSTOMER");
  const builderNav = solutionNavigationForRole("DEVELOPER");
  const adminNav = solutionNavigationForRole("ADMIN");

  assert.ok(customerNav.some((item) => item.id === "approvals"));
  assert.ok(customerNav.every((item) => item.id !== "engineering"));
  assert.ok(builderNav.some((item) => item.id === "engineering"));
  assert.ok(builderNav.every((item) => item.id !== "security"));
  assert.equal(adminNav.length, SOLUTION_NAV_GROUP.length);
  assert.equal(solutionRoleCanAccessSection("CUSTOMER", "architecture"), false);
  assert.equal(solutionRoleCanAccessSection("ADMIN", "evidence"), true);
});
