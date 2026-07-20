import { createNovaTechIntegrationClient } from "../../platform/integrationClient.js";

const DEFAULT_TIMEOUT_MS = 12000;

export function createNovaCodeProProductFactoryApi({ baseUrl = "", session = {}, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const client = createNovaTechIntegrationClient({ baseUrl, session, timeoutMs, fetchImpl: globalThis.fetch });
  const request = (path, options = {}) => client.request(path, options);
  const safeGet = (path) => client.safeGet(path);
  const mutation = (path, body, options = {}) => client.mutation(path, body, options);

  return {
    request,
    getOverview: () => safeGet("/v1/product-factory"),
    getInventory: () => safeGet("/v1/product-factory/inventory"),
    getGaps: () => safeGet("/v1/product-factory/gaps"),
    listArchetypes: () => safeGet("/v1/product-factory/archetypes"),
    cloneArchetype: (archetypeId, payload) => mutation(`/v1/product-factory/archetypes/${encodeURIComponent(archetypeId)}/clone`, payload),
    publishArchetype: (archetypeId) => mutation(`/v1/product-factory/archetypes/${encodeURIComponent(archetypeId)}/publish`, {}),
    deprecateArchetype: (archetypeId) => mutation(`/v1/product-factory/archetypes/${encodeURIComponent(archetypeId)}/deprecate`, {}),
    listRequests: () => safeGet("/v1/product-factory/requests"),
    createRequest: (payload, idempotencyKey) => mutation("/v1/product-factory/requests", payload, { idempotencyKey }),
    getRequest: (requestId) => safeGet(`/v1/product-factory/requests/${encodeURIComponent(requestId)}`),
    submitRequest: (requestId, payload = {}) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/submit`, payload),
    reviewRequest: (requestId, payload = {}) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/review`, payload),
    approveRequest: (requestId, payload = {}) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/approve`, payload),
    rejectRequest: (requestId, payload = {}) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/reject`, payload),
    archiveRequest: (requestId) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/archive`, {}),
    convertRequestToProduct: (requestId) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/convert/product`, {}),
    convertRequestToProject: (requestId) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/convert/project`, {}),
    listBlueprints: () => safeGet("/v1/product-factory/blueprints"),
    createBlueprint: (requestId, payload) => mutation(`/v1/product-factory/requests/${encodeURIComponent(requestId)}/blueprints`, payload),
    getBlueprint: (blueprintId) => safeGet(`/v1/product-factory/blueprints/${encodeURIComponent(blueprintId)}`),
    approveBlueprint: (blueprintId, payload = {}) => mutation(`/v1/product-factory/blueprints/${encodeURIComponent(blueprintId)}/approve`, payload),
    amendBlueprint: (blueprintId, payload = {}) => mutation(`/v1/product-factory/blueprints/${encodeURIComponent(blueprintId)}/amend`, payload),
    listPhases: () => safeGet("/v1/product-factory/phases"),
    transitionPhase: (phaseId, payload) => mutation(`/v1/product-factory/phases/${encodeURIComponent(phaseId)}/transition`, payload),
    getTraceability: () => safeGet("/v1/product-factory/traceability"),
    listEvidence: () => safeGet("/v1/product-factory/evidence"),
    createEvidence: (payload) => mutation("/v1/product-factory/evidence", payload),
    listAudit: (limit = 100) => safeGet(`/v1/product-factory/audit?limit=${encodeURIComponent(limit)}`),
    listImprovements: () => safeGet("/v1/product-factory/improvement-backlog"),
    createImprovement: (payload) => mutation("/v1/product-factory/improvements", payload),
    createDemoProduct: () => mutation("/v1/product-factory/demo", {}),
    createGateDecision: (payload) => mutation("/v1/product-factory/gates", payload),
    listGates: () => safeGet("/v1/product-factory/gates"),
    createIdempotencyKey: () => client.createIdempotencyKey(),
    createCorrelationId: () => client.createCorrelationId(),
  };
}
