import assert from "node:assert/strict";
import test from "node:test";

import {
  buildIntegrationCacheKey,
  createProductMutationDefinition,
  createProductQueryDefinition,
} from "../src/platform/integrationDefinitions.js";

test("product query definitions normalize required metadata", () => {
  const query = createProductQueryDefinition({
    queryId: "novaride.get-ride.v1",
    productCode: "novaride",
    endpoint: "/v1/novaride/rides/:rideId",
    method: "get",
    cachePolicy: "novaride-live-ride",
    retryPolicy: "standard-read",
    requiredPermissions: ["novaride:ride:read"],
  });

  assert.equal(query.method, "GET");
  assert.equal(query.requiredPermissions[0], "novaride:ride:read");
});

test("product mutation definitions preserve idempotency requirements", () => {
  const mutation = createProductMutationDefinition({
    mutationId: "novaride.request-ride.v1",
    productCode: "novaride",
    endpoint: "/v1/novaride/rides",
    method: "post",
    requiredPermissions: ["novaride:ride:create"],
  });

  assert.equal(mutation.method, "POST");
  assert.equal(mutation.idempotencyRequired, true);
});

test("integration cache keys remain tenant aware", () => {
  assert.equal(
    buildIntegrationCacheKey({
      productCode: "novapay",
      tenantId: "tenant-b",
      resource: "wallet",
      resourceId: "wallet-1",
    }),
    "novapay:tenant-b:wallet:wallet-1:v1",
  );
});

