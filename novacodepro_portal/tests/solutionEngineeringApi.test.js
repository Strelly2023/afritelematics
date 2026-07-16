import assert from "node:assert/strict";
import test from "node:test";

import { createSolutionEngineeringClient } from "../src/platform/solutionEngineeringApi.js";

test("solution engineering client sends authenticated tenant-scoped requests", async () => {
  const originalFetch = global.fetch;
  const requests = [];
  global.fetch = async (url, options) => {
    requests.push({ url, options });
    return {
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ ok: true, url }),
    };
  };

  const client = createSolutionEngineeringClient({
    baseUrl: "",
    session: {
      tenant_id: "tenant-a",
      organization: "org-a",
      active_role: "DEVELOPER",
    },
  });

  await client.getPlatformSummary();
  await client.createProject({
    tenant_id: "tenant-a",
    organization_id: "org-a",
    name: "Portal project",
    idea: "Build the customer solutions portal.",
  });
  await client.generateWorkflow({ prompt: "Design a workflow" });
  try {
    assert.equal(requests[0].url, "/v1/solution-engineering");
    assert.equal(requests[0].options.credentials, "include");
    assert.equal(requests[1].url, "/v1/solution-engineering/projects");
    assert.equal(requests[1].options.method, "POST");
    assert.equal(requests[1].options.headers["x-tenant-id"], "tenant-a");
    assert.equal(requests[1].options.headers["x-organization-id"], "org-a");
    assert.equal(requests[1].options.headers["x-role"], "DEVELOPER");
    assert.equal(requests[1].options.headers["x-idempotency-key"].startsWith("ncp-"), true);
    assert.equal(requests[2].url, "/v1/workflows/generate");
    assert.equal(requests[2].options.method, "POST");
  } finally {
    global.fetch = originalFetch;
  }
});

test("solution engineering client normalizes API errors", async () => {
  const originalFetch = global.fetch;
  global.fetch = async () => ({
    ok: false,
    status: 403,
    statusText: "Forbidden",
    text: async () => JSON.stringify({ detail: { code: "forbidden", message: "denied" } }),
  });

  const client = createSolutionEngineeringClient({ baseUrl: "", session: { tenant_id: "tenant-a", organization: "org-a" } });
  try {
    await assert.rejects(() => client.getProject("proj-1"), (error) => {
      assert.equal(error.status, 403);
      assert.equal(error.code, "FORBIDDEN");
      return true;
    });
  } finally {
    global.fetch = originalFetch;
  }
});
