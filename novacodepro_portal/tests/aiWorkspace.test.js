import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { buildUniversalAIWorkspaceModel } from "../src/platform/aiWorkspaceModel.js";
import { createAIWorkspaceClient, NotConnectedError } from "../src/platform/aiWorkspaceApi.js";

test("ai workspace model is role aware", () => {
  const model = buildUniversalAIWorkspaceModel({
    role: "DEVELOPER",
    roleLabel: "Developer",
    workspace: "Solution Studio",
    tenant: "tenant-a",
    organization: "org-a",
    environment: "Production",
    request: { title: "Portal", request: "Build the portal", status: "PLANNING", workflow: [], artifacts: [] },
  });

  assert.equal(model.roleLabel, "Developer");
  assert.equal(model.workspaceLabel, "Solution Studio");
  assert.ok(model.suggestions.some((item) => item.label.includes("Generate implementation plan")));
  assert.equal(model.connection.connected, false);
});

test("ai workspace component source includes the governed AI surface", () => {
  const source = readFileSync(new URL("../src/platform/aiWorkspace.jsx", import.meta.url), "utf8");
  assert.ok(source.includes("Universal AI Workspace"));
  assert.ok(source.includes("AIRequestComposer"));
  assert.ok(source.includes("AgentCollaborationPanel"));
  assert.ok(source.includes("ExecutionTimeline"));
});

test("ai workspace adapter fails closed when not connected", async () => {
  const client = createAIWorkspaceClient({ connected: false });
  await assert.rejects(() => client.submitAIRequest({ prompt: "Build it" }), (error) => {
    assert.ok(error instanceof NotConnectedError);
    assert.equal(error.code, "NOT_CONNECTED");
    return true;
  });
});
