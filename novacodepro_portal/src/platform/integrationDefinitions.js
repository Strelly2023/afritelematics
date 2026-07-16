export function createProductQueryDefinition(definition) {
  const normalized = {
    queryId: String(definition.queryId || ""),
    productCode: String(definition.productCode || ""),
    endpoint: String(definition.endpoint || ""),
    method: String(definition.method || "GET").toUpperCase(),
    cachePolicy: String(definition.cachePolicy || "no-cache"),
    retryPolicy: String(definition.retryPolicy || "no-retry"),
    requiredPermissions: Array.isArray(definition.requiredPermissions) ? definition.requiredPermissions.map(String) : [],
    featureFlag: definition.featureFlag ? String(definition.featureFlag) : undefined,
    freshness: String(definition.freshness || "EVENTUAL"),
    parseResponse: definition.parseResponse || ((value) => value),
  };
  if (!normalized.queryId || !normalized.productCode || !normalized.endpoint) {
    throw new Error("Product query definition requires queryId, productCode, and endpoint.");
  }
  return normalized;
}

export function createProductMutationDefinition(definition) {
  const normalized = {
    mutationId: String(definition.mutationId || ""),
    productCode: String(definition.productCode || ""),
    endpoint: String(definition.endpoint || ""),
    method: String(definition.method || "POST").toUpperCase(),
    idempotencyRequired: Boolean(definition.idempotencyRequired ?? true),
    offlineAllowed: Boolean(definition.offlineAllowed ?? false),
    invalidateQueries: Array.isArray(definition.invalidateQueries) ? definition.invalidateQueries.map(String) : [],
    optimisticUpdate: Boolean(definition.optimisticUpdate ?? false),
    requiredPermissions: Array.isArray(definition.requiredPermissions) ? definition.requiredPermissions.map(String) : [],
    featureFlag: definition.featureFlag ? String(definition.featureFlag) : undefined,
    parseResponse: definition.parseResponse || ((value) => value),
  };
  if (!normalized.mutationId || !normalized.productCode || !normalized.endpoint) {
    throw new Error("Product mutation definition requires mutationId, productCode, and endpoint.");
  }
  return normalized;
}

export function buildIntegrationCacheKey({ productCode, tenantId, resource, resourceId, version = "v1", locale = "" }) {
  return [productCode, tenantId, resource, resourceId, version, locale].filter(Boolean).join(":");
}

