import { createNovaTechIntegrationClient } from "./integrationClient.js";

const DEFAULT_TIMEOUT_MS = 12000;

function nowIso() {
  return new Date().toISOString();
}

export function createSolutionEngineeringClient({ baseUrl = "", session = {}, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const integrationClient = createNovaTechIntegrationClient({ baseUrl, session, timeoutMs, fetchImpl: globalThis.fetch });
  const request = (path, options = {}) => integrationClient.request(path, options);
  const safeGet = (path) => integrationClient.safeGet(path);
  const mutation = (path, body, options = {}) => integrationClient.mutation(path, body, options);

  return {
    request,
    getPlatformSummary: () => safeGet("/v1/solution-engineering"),
    listCustomers: () => safeGet("/v1/solution-engineering/customers"),
    createCustomer: (payload) => mutation("/v1/solution-engineering/customers", payload),
    listWorkspaces: () => safeGet("/v1/solution-engineering/workspaces"),
    listProjects: () => safeGet("/v1/solution-engineering/projects"),
    createProject: (payload) => mutation("/v1/solution-engineering/projects", payload),
    getProject: (projectId) => safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`),
    submitIdea: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/idea`, payload),
    runDiscovery: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/discovery`, payload),
    listRequirements: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).requirements || [],
    createRequirement: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/requirements`, payload),
    approveRequirements: (projectId) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/requirements/approve`, {}),
    getBlueprint: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).blueprint || null,
    generateBlueprint: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/blueprint`, payload),
    listBlueprintSections: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).blueprint?.sections || [],
    listDesigns: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).artifacts?.filter((item) => item.kind === "design") || [],
    createDesign: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/designs`, payload),
    getArchitecture: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).architecture || null,
    approveArchitecture: (projectId) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/architecture/approve`, {}),
    listPlans: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).artifacts?.filter((item) => item.kind === "plan") || [],
    createPlan: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/plans`, payload),
    startImplementation: (projectId) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/implement`, {}),
    listTests: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).artifacts?.filter((item) => item.kind === "test_execution") || [],
    createTest: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/tests`, payload),
    runSecurityReview: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/security-review`, payload),
    runComplianceReview: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/compliance-review`, payload),
    submitCustomerReview: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/customer-review`, payload),
    createRelease: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/release`, payload),
    approveRelease: (releaseId) => mutation(`/v1/solution-engineering/releases/${encodeURIComponent(releaseId)}/approve`, {}),
    deployRelease: (releaseId, payload) => mutation(`/v1/solution-engineering/releases/${encodeURIComponent(releaseId)}/deploy`, payload),
    acceptRelease: (releaseId, payload) => mutation(`/v1/solution-engineering/releases/${encodeURIComponent(releaseId)}/accept`, payload),
    getDigitalTwin: (projectId) => safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/digital-twin`),
    listKnowledge: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).knowledge || [],
    listEvidence: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).evidence || [],
    getTimeline: (projectId) => safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/timeline`),
    listSupportCases: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).support_cases || [],
    createSupportCase: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/support`, payload),
    listEnhancements: async (projectId) => (await safeGet(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}`)).enhancements || [],
    createEnhancement: (projectId, payload) => mutation(`/v1/solution-engineering/projects/${encodeURIComponent(projectId)}/enhancements`, payload),
    getStudio: () => request("/v1/solution-engineering/studio", { retrySafe: true, parse: "text" }),
    getWindows: () => safeGet("/v1/solution-engineering/windows"),
    getWorkflowFabricSummary: () => safeGet("/v1/workflow-fabric"),
    listWorkflowConnectors: () => safeGet("/v1/workflow-fabric/connectors"),
    getWorkflowMarketplace: () => safeGet("/v1/workflow-fabric/marketplace"),
    listWorkflows: () => safeGet("/v1/workflows"),
    createWorkflow: (payload) => mutation("/v1/workflows", payload),
    generateWorkflow: (payload) => mutation("/v1/workflows/generate", payload),
    getWorkflow: (workflowId) => safeGet(`/v1/workflows/${encodeURIComponent(workflowId)}`),
    validateWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/validate`, {}),
    compileWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/compile`, {}),
    reviewWorkflow: (workflowId, payload) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/review`, payload || {}),
    approveWorkflow: (workflowId, payload) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/approve`, payload || {}),
    deployWorkflow: (workflowId, payload) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/deploy`, payload || {}),
    executeWorkflow: (workflowId, payload) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/execute`, payload || {}),
    pauseWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/pause`, {}),
    resumeWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/resume`, {}),
    completeWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/complete`, {}),
    verifyWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/verify`, {}),
    generateWorkflowEvidence: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/evidence`, {}),
    archiveWorkflow: (workflowId) => mutation(`/v1/workflows/${encodeURIComponent(workflowId)}/archive`, {}),
    getWorkflowViews: (workflowId) => safeGet(`/v1/workflows/${encodeURIComponent(workflowId)}/views`),
    getWorkflowTimeline: (workflowId) => safeGet(`/v1/workflows/${encodeURIComponent(workflowId)}/timeline`),
    getWorkflowReplay: (workflowId) => safeGet(`/v1/workflows/${encodeURIComponent(workflowId)}/replay`),
    getWorkflowAnalytics: (workflowId) => safeGet(`/v1/workflows/${encodeURIComponent(workflowId)}/analytics`),
    getWorkflowEvidence: (workflowId) => safeGet(`/v1/workflows/${encodeURIComponent(workflowId)}/evidence`),
    createIdempotencyKey: () => integrationClient.createIdempotencyKey(),
    createCorrelationId: () => integrationClient.createCorrelationId(),
    nowIso,
  };
}

export { DEFAULT_TIMEOUT_MS };
