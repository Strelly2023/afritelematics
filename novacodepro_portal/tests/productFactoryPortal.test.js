import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { ROUTES } from "../src/platform/routes.js";
import { createNovaCodeProProductFactoryApi } from "../src/novacodepro/api/novacodeproProductFactoryApi.js";
import { isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "../src/platform/appRegistry.js";

test("Product Factory routes are wired into the main app shell", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(appSource.includes("ProductFactoryPortal"));
  assert.ok(appSource.includes('"product-factory"'));
});

test("Product Factory portal source includes governed lifecycle controls", () => {
  const source = readFileSync(new URL("../src/novacodepro/ProductFactoryPortal.jsx", import.meta.url), "utf8");
  for (const token of [
    "Product Factory",
    "Seed demo product",
    "Traceability matrix",
    "Requirements",
    "Lifecycle",
    "Workflows",
    "Releases",
    "Reports",
    "Search",
    "Cross-Product",
    "Migrations",
    "PRR",
    "Gate decision",
    "Improvement backlog",
    "Seed demo product",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

test("NovaCodePro registry keeps the Product Factory surface reachable for workspace users", () => {
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/product-factory", ["workspace.read"]), true);
  assert.equal(isNovaCodeProRouteAccessible("/novacodepro/product-factory", ["request.create"]), false);
  assert.deepEqual(parseNovaCodeProRoute("/novacodepro/product-factory/requests"), {
    path: "/novacodepro/product-factory/requests",
    appId: "product-factory",
    section: "product-factory",
    subRoute: "/requests",
  });
  assert.equal(ROUTES.productFactoryRoot, "/novacodepro/product-factory");
});

test("Product Factory API client targets governed product-factory routes", async () => {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input, init) => {
    calls.push({ input: String(input), init });
    return new Response(JSON.stringify({ summary: { requests: 1 }, blueprints: [], archetypes: [], phases: [], gates: [], improvements: [], audit: [], evidence: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };
  try {
    const client = createNovaCodeProProductFactoryApi({
      baseUrl: "https://example.test/api",
      session: { tenant_id: "novatech", active_role: "ADMIN" },
      timeoutMs: 1000,
    });
    await client.getOverview();
    await client.createRequest({ product_name: "NovaFactory", status: "Draft" }, "idempotency-key");
    await client.createDemoProduct();
  } finally {
    globalThis.fetch = originalFetch;
  }
  assert.ok(calls.some((call) => call.input.includes("/v1/product-factory")));
  assert.ok(calls.some((call) => call.init?.method === "POST"));
});
