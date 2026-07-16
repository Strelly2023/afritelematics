import assert from "node:assert/strict";
import test from "node:test";

import { buildIntegrationCacheKey, createNovaTechIntegrationClient } from "../src/platform/integrationClient.js";

test("integration client injects shared tenant and correlation headers", async () => {
  const originalFetch = global.fetch;
  const requests = [];
  global.fetch = async (url, options) => {
    requests.push({ url, options });
    return {
      ok: true,
      status: 200,
      headers: new Headers(),
      text: async () => JSON.stringify({ ok: true }),
      json: async () => ({ ok: true }),
    };
  };

  try {
    const client = createNovaTechIntegrationClient({
      baseUrl: "",
      session: {
        tenant_id: "tenant-a",
        organization: "org-a",
        active_role: "DEVELOPER",
      },
    });
    const result = await client.request("/v1/novaride/rides", {
      method: "POST",
      body: { rideId: "ride-1" },
      purpose: "ride_booking",
      idempotencyKey: "idem-1",
      correlationId: "corr-1",
    });

    assert.equal(requests[0].options.headers["x-tenant-id"], "tenant-a");
    assert.equal(requests[0].options.headers["x-correlation-id"], "corr-1");
    assert.equal(requests[0].options.headers["x-idempotency-key"], "idem-1");
    assert.equal(requests[0].options.headers["x-purpose"], "ride_booking");
    assert.equal(result.ok, true);
  } finally {
    global.fetch = originalFetch;
  }
});

test("integration cache keys include product and tenant context", () => {
  assert.equal(
    buildIntegrationCacheKey({
      productCode: "novaride",
      tenantId: "tenant-a",
      resource: "ride",
      resourceId: "ride-1",
      version: "v1",
      locale: "en-AU",
    }),
    "novaride:tenant-a:ride:ride-1:v1:en-AU",
  );
});

