import assert from "node:assert/strict";
import test from "node:test";

import { createNovaCodeProNcp003Api } from "../src/novacodepro/api/novacodeproNcp003Api.js";

function jsonResponse(body, ok = true, status = 200) {
  return {
    ok,
    status,
    statusText: ok ? "OK" : "Bad Request",
    text: async () => JSON.stringify(body),
  };
}

test("NCP003 API client resolves workspace and project routes", async () => {
  const calls = [];
  const api = createNovaCodeProNcp003Api({
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      const pathname = new URL(url, "http://localhost").pathname;
      if (pathname === "/v1/novacodepro/workspaces") {
        return jsonResponse({ workspaces: [{ id: "enterprise-developer", name: "Developer Workspace" }] });
      }
      if (pathname.endsWith("/select")) {
        return jsonResponse({ session: { workspace_id: "enterprise-developer" }, claims: { workspace_id: "enterprise-developer" } });
      }
      if (pathname === "/v1/novacodepro/projects" && options.method === "POST") {
        return jsonResponse({ id: "project-1", name: "NovaCodePro", status: "DRAFT" });
      }
      if (pathname === "/v1/novacodepro/requests" && options.method === "POST") {
        return jsonResponse({ id: "request-1", title: "Request", status: "DRAFT" });
      }
      return jsonResponse({ ok: true });
    },
  });

  const workspaces = await api.listWorkspaces();
  assert.equal(workspaces[0].id, "enterprise-developer");

  const selected = await api.selectWorkspace("enterprise-developer");
  assert.equal(selected.session.workspace_id, "enterprise-developer");

  const project = await api.createProject({ workspace_id: "enterprise-developer", name: "NovaCodePro" }, "project-key");
  assert.equal(project.id, "project-1");

  const request = await api.createRequest({ workspace_id: "enterprise-developer", title: "Request" }, "request-key");
  assert.equal(request.id, "request-1");

  assert.equal(calls[0].url.endsWith("/v1/novacodepro/workspaces"), true);
  assert.equal(calls[1].options.method, "POST");
  assert.equal(calls[2].options.headers["Idempotency-Key"], "project-key");
  assert.equal(calls[3].options.headers["Idempotency-Key"], "request-key");
});
