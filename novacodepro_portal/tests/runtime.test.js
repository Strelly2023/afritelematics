import assert from "node:assert/strict";
import test from "node:test";

import {
  COMPLETION_STANDARD,
  createPlatformRuntime,
  ENTERPRISE_ARCHITECTURE_FRAMEWORK,
  EROS_MANIFEST,
  NEAF_MODEL,
  OPERATIONAL_READINESS_PROGRAM,
  UX_OPERATING_SYSTEM,
  UXOS_RUNTIME_SERVICES,
} from "../src/platform/runtime.js";
import { normalizeBootstrapResponse } from "../src/platform/bootstrap.js";

test("NEAF exposes five governed enterprise planes", () => {
  assert.equal(NEAF_MODEL.sequence.length, 5);
  assert.equal(NEAF_MODEL.planes[0].name, "Governance Plane");
  assert.equal(NEAF_MODEL.planes[1].platforms.includes("NovaDigitalTwin"), true);
  assert.equal(ENTERPRISE_ARCHITECTURE_FRAMEWORK.models.neaf.id, "neaf");
  assert.equal(ENTERPRISE_ARCHITECTURE_FRAMEWORK.models.nera.layers.length, 10);
  assert.equal(ENTERPRISE_ARCHITECTURE_FRAMEWORK.models.nedtm.id, "nedtm");
  assert.equal(ENTERPRISE_ARCHITECTURE_FRAMEWORK.models.ndtm.aliasFor, "nedtm");
});

test("EROS exposes the optimize resilience lifecycle", () => {
  assert.equal(EROS_MANIFEST.lifecycle.at(-1), "Optimize");
  assert.equal(EROS_MANIFEST.runtimeServices.includes("Optimization Engine"), true);
  assert.equal(EROS_MANIFEST.recoveryValidation.includes("Business Validation"), true);
});

test("UX operating system exposes governed design-to-operations lifecycle", () => {
  assert.equal(UX_OPERATING_SYSTEM.name, "NovaCodePro Enterprise UX Operating System");
  assert.equal(UX_OPERATING_SYSTEM.lifecycle.includes("Production Readiness Review"), true);
  assert.equal(UX_OPERATING_SYSTEM.stateModel.at(-1), "GENERAL_AVAILABILITY");
  assert.equal(UX_OPERATING_SYSTEM.governance.gaAllowed, false);
});

test("runtime manages UX artifacts, evidence, and readiness without GA approval", () => {
  const runtime = createPlatformRuntime();
  const artifact = runtime.createUxArtifact({
    artifact: "Runtime UX artifact",
    artifactType: "wireframe",
    studio: "Wireframe Studio",
  });
  const evidence = runtime.attachUxEvidence(artifact.id, "runtime-ux-evidence.yaml");
  const readiness = runtime.assessUxReleaseReadiness();

  assert.equal(artifact.approvalState, "DRAFT");
  assert.equal(evidence.status, "EVIDENCE_CAPTURED");
  assert.equal(readiness.gaAllowed, false);
  assert.equal(runtime.getState().uxArtifacts[0].artifact, "Runtime UX artifact");
});

test("runtime records UXOS service fabric work as evidence-pending", () => {
  const runtime = createPlatformRuntime();
  const record = runtime.recordUxosService("ux_design_sync", {
    subject: "Figma rider workspace sync",
    provider: "Figma",
  });

  assert.equal(UXOS_RUNTIME_SERVICES.includes("Design Integration Service"), true);
  assert.equal(record.operationalComplete, false);
  assert.equal(record.gaAllowed, false);
  assert.equal(runtime.getState().uxosServiceRecords[0].kind, "ux_design_sync");
});

test("completion standard keeps repository, operational, and governance states separate", () => {
  const runtime = createPlatformRuntime();
  const repositoryOnly = runtime.evaluateCompletionState({
    repositoryComplete: true,
    operationalVerified: false,
    governanceApproved: false,
  });

  assert.equal(COMPLETION_STANDARD.levels.at(-1), "General Availability");
  assert.equal(runtime.getState().completionDashboard.rows.find((row) => row.domain === "UXOS Services").repository, true);
  assert.equal(runtime.getState().completionDashboard.rows.find((row) => row.domain === "GA Promotion").repository, false);
  assert.equal(repositoryOnly.level, "Repository Complete");
  assert.equal(repositoryOnly.gaAllowed, false);
  assert.equal(repositoryOnly.realPaymentsEnabled, false);
});

test("completion standard requires all gates and executive authorization for GA", () => {
  const runtime = createPlatformRuntime();
  const gates = Object.fromEntries(COMPLETION_STANDARD.productionReadyGates.map((gate) => [gate, true]));
  const productionReady = runtime.evaluateCompletionState({
    repositoryComplete: true,
    operationalVerified: true,
    governanceApproved: true,
    productionReadyGates: gates,
    executiveAuthorized: false,
  });
  const ga = runtime.evaluateCompletionState({
    repositoryComplete: true,
    operationalVerified: true,
    governanceApproved: true,
    productionReadyGates: gates,
    executiveAuthorized: true,
  });

  assert.equal(productionReady.level, "Production Ready");
  assert.equal(productionReady.gaAllowed, false);
  assert.equal(ga.level, "General Availability");
  assert.equal(ga.gaAllowed, true);
  assert.equal(ga.realPaymentsEnabled, false);
});

test("operational readiness program separates GA from production payment activation", () => {
  const runtime = createPlatformRuntime();
  const evidence = {
    designSync: "PASS",
    visualRegression: "PASS",
    accessibility: "PASS",
    openTelemetry: "PASS",
    analytics: "PASS",
    digitalUxTwin: "PASS",
    automatedPrr: "PASS",
  };
  const approvals = {
    ux: "APPROVED",
    engineering: "APPROVED",
    security: "APPROVED",
    operations: "APPROVED",
    compliance: "APPROVED",
    prr: "APPROVED",
    executive: "APPROVED",
  };
  const gaOnly = runtime.evaluateOperationalReadiness({ evidence, approvals });
  const payments = runtime.evaluateOperationalReadiness({
    evidence,
    approvals,
    paymentEvidence: {
      sandboxCertification: "PASS",
      webhookVerification: "PASS",
      reconciliationValidation: "PASS",
      fraudControls: "PASS",
      failoverTesting: "PASS",
    },
  });

  assert.equal(OPERATIONAL_READINESS_PROGRAM.maturityLayers.at(-1), "Production Operation");
  assert.equal(OPERATIONAL_READINESS_PROGRAM.paymentActivation.providers.includes("Mobile Money Providers"), true);
  assert.equal(OPERATIONAL_READINESS_PROGRAM.integrationFabric.operations.includes("OpenTelemetry"), true);
  assert.equal(OPERATIONAL_READINESS_PROGRAM.readinessMatrix.find((row) => row.capability === "Production Payments").repository, false);
  assert.equal(gaOnly.gaAllowed, true);
  assert.equal(gaOnly.realPaymentsEnabled, false);
  assert.equal(payments.gaAllowed, true);
  assert.equal(payments.realPaymentsEnabled, true);
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
