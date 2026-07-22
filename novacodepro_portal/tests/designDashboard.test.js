import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/design/DesignDashboard.jsx", import.meta.url), "utf8");

test("authenticated dashboard uses governed live service clients", () => {
  assert.match(source, /createNovaCodeProNcp003Api/);
  assert.match(source, /createNovaCodeProNcp006bApi/);
  assert.match(source, /listWorkspaces/);
  assert.match(source, /listWorkspaceApprovals/);
  assert.doesNotMatch(source, /mockProjects|demoProjects|fixtureProjects/);
});

test("dashboard exposes the governed design lifecycle and resilient states", () => {
  for (const destination of ["AI Designer", "Research", "User Personas", "Journey Maps", "Wireframes", "Accessibility", "Developer Handoff", "Approvals", "Export"]) assert.match(source, new RegExp(destination));
  assert.match(source, /state === "loading"/);
  assert.match(source, /state === "error"/);
  assert.match(source, /No projects yet/);
});
