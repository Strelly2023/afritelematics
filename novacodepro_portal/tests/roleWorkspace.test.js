import assert from "node:assert/strict";
import test from "node:test";

import { buildRoleWorkspaceModel } from "../src/platform/roleWorkspace.js";

const runtimeStub = {
  commandCenterSnapshots: [
    {
      enterpriseHealth: "98.9%",
      trustScore: "96.2%",
      riskScore: "Low",
      summary: "Enterprise signals are stable.",
    },
  ],
  approvalRoutes: [
    {
      subject: "Driver onboarding workflow",
      policyId: "POL-104",
      required: ["Product", "Compliance"],
    },
  ],
  evidenceBundles: [
    {
      summary: "Approved solution evidence bundle",
    },
  ],
  riskRegister: [
    {
      title: "Identity verification gap",
      score: 74,
    },
  ],
  solutionRequests: [
    {
      status: "draft",
    },
  ],
  knowledgeGraph: [{ id: "kg-1" }, { id: "kg-2" }],
  automationRuns: [{ id: "run-1" }],
  auditTrail: [
    {
      action: "solution.request.created",
      service: "NovaCodePro",
      at: "2026-07-13T10:00:00Z",
    },
  ],
};

test("role workspace model exposes the four operating windows", () => {
  const model = buildRoleWorkspaceModel({
    activeRole: {
      label: "Product Manager",
      domain: "Product and delivery",
      metrics: [
        ["Roadmap progress", "82%"],
        ["Feature status", "On track"],
        ["Backlog health", "Healthy"],
      ],
      actions: ["Create request", "Open review"],
      signals: [["Delivery", "Stable"]],
      agents: ["Product Agent", "Research Agent"],
    },
    runtime: runtimeStub,
    platformSummary: { platform_health: "healthy" },
    environment: "Production",
    activeTenant: { name: "NovaTech" },
    activeProject: { name: "NovaRide" },
    activeRequest: { title: "Driver onboarding workflow", status: "review" },
    activeStage: { label: "Architecture review" },
    workflowProgress: 75,
    authDisplayName: "Djuma",
    authDisplayRoleLabel: "Product Manager",
    selectedModeLabel: "Full solution",
    requestSummary: "Build a driver onboarding workflow.",
    suggestedTitle: "Driver onboarding workflow",
  });

  assert.equal(model.windows.length, 4);
  assert.deepEqual(
    model.windows.map((window) => window.id),
    ["dashboard", "operations", "studio", "chat"],
  );
  assert.match(model.windows[0].summary, /Product and delivery/);
  assert.match(model.windows[1].summary, /Real-time command/);
  assert.match(model.windows[2].summary, /governed creation surface/);
  assert.match(model.windows[3].summary, /Conversation/);
});

test("role workspace model carries role-specific dashboard and chat context", () => {
  const model = buildRoleWorkspaceModel({
    activeRole: {
      label: "Legal",
      domain: "Legal and compliance",
      metrics: [["Matters", "12 open"]],
      actions: ["Review contract", "Escalate risk"],
      signals: [["Contracts", "Awaiting review"]],
      agents: ["Legal Agent"],
    },
    runtime: runtimeStub,
    platformSummary: { platform_health: "healthy" },
    environment: "Staging",
    activeTenant: { name: "NovaTech" },
    activeProject: { name: "NovaCommerce" },
    activeRequest: { title: "Privacy policy review", status: "draft" },
    activeStage: { label: "Intent analysis" },
    workflowProgress: 25,
    authDisplayName: "Djuma",
    authDisplayRoleLabel: "Legal",
    selectedModeLabel: "Review",
    requestSummary: "Review the privacy policy.",
    suggestedTitle: "Privacy policy review",
  });

  assert.ok(model.windows[0].highlights.some((item) => item.includes("Review contract")));
  assert.ok(model.windows[1].actions.some((action) => action.label === "Investigate"));
  assert.ok(model.windows[2].metrics.some(([label]) => label === "Modes"));
  assert.ok(model.windows[3].highlights.some((item) => item.includes("Privacy policy review")));
});
