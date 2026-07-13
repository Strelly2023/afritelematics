import assert from "node:assert/strict";
import test from "node:test";

import { ENTERPRISE_ARCHITECTURE_FRAMEWORK, EROS_MANIFEST, NEAF_MODEL } from "../src/platform/runtime.js";
import { normalizeBootstrapResponse } from "../src/platform/bootstrap.js";

test("NEAF exposes five governed enterprise planes", () => {
  assert.equal(NEAF_MODEL.sequence.length, 5);
  assert.equal(NEAF_MODEL.planes[0].name, "Governance Plane");
  assert.equal(NEAF_MODEL.planes[1].platforms.includes("NovaDigitalTwin"), true);
  assert.equal(ENTERPRISE_ARCHITECTURE_FRAMEWORK.models.neaf.id, "neaf");
});

test("EROS exposes the optimize resilience lifecycle", () => {
  assert.equal(EROS_MANIFEST.lifecycle.at(-1), "Optimize");
  assert.equal(EROS_MANIFEST.runtimeServices.includes("Optimization Engine"), true);
});

test("bootstrap response normalizes canonical context fields", () => {
  const payload = normalizeBootstrapResponse({
    authenticated: true,
    user: { id: "usr-1" },
    organization: { id: "novatech" },
    tenant: { id: "novatech" },
    workspace: { id: "novatech-platform" },
    roles: ["ADMIN", "PLATFORM_ADMIN"],
    permissions: ["dashboard.read"],
    features: { dashboard: true },
    default_route: "/novacodepro/dashboard",
  });

  assert.equal(payload.authenticated, true);
  assert.equal(payload.roles[0], "ADMIN");
  assert.equal(payload.workspace.id, "novatech-platform");
  assert.equal(payload.default_route, "/novacodepro/dashboard");
});

test("bootstrap response rejects malformed identity context", () => {
  assert.throws(
    () =>
      normalizeBootstrapResponse({
        authenticated: true,
        organization: { id: "novatech" },
        tenant: { id: "novatech" },
        workspace: { id: "novatech-platform" },
        roles: ["ADMIN"],
      }),
    (error) => error.code === "MALFORMED_RESPONSE",
  );
});
