import { createNovaTechIntegrationClient } from "../../platform/integrationClient.js";

export function createNovaCodeProNcp005Api({ baseUrl = "", session = {}, timeoutMs } = {}) {
  const client = createNovaTechIntegrationClient({ baseUrl, session, timeoutMs });
  const { request, safeGet, mutation, createCorrelationId, createIdempotencyKey } = client;

  return {
    createCorrelationId,
    createIdempotencyKey,
    listRequirementSets: (signal) => safeGet("/v1/novacodepro/requirement-sets", { signal }).then((body) => body?.requirement_sets || []),
    createRequirementSet: (payload) => mutation("/v1/novacodepro/requirement-sets", payload),
    getRequirementSet: (setId, signal) => request(`/v1/novacodepro/requirement-sets/${encodeURIComponent(setId)}`, { signal }),
    updateRequirementSet: (setId, payload) => mutation(`/v1/novacodepro/requirement-sets/${encodeURIComponent(setId)}`, payload, { method: "PATCH" }),
    archiveRequirementSet: (setId) => mutation(`/v1/novacodepro/requirement-sets/${encodeURIComponent(setId)}/archive`, {}),
    baselineRequirementSet: (setId, payload) => mutation(`/v1/novacodepro/requirement-sets/${encodeURIComponent(setId)}/baseline`, payload),
    listRequirements: (signal) => safeGet("/v1/novacodepro/requirements", { signal }).then((body) => body?.requirements || []),
    createRequirement: (payload) => mutation("/v1/novacodepro/requirements", payload),
    getRequirement: (requirementId, signal) => request(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}`, { signal }),
    updateRequirement: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}`, payload, { method: "PATCH" }),
    deleteRequirement: (requirementId) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}`, {}, { method: "DELETE" }),
    transitionRequirement: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/transition`, payload),
    listRequirementVersions: (requirementId, signal) => safeGet(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/versions`, { signal }).then((body) => body?.versions || []),
    listRequirementReviews: (requirementId, signal) => safeGet(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/reviews`, { signal }).then((body) => body?.reviews || []),
    createRequirementReview: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/reviews`, payload),
    completeRequirementReview: (requirementId, reviewId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/reviews/${encodeURIComponent(reviewId)}/complete`, payload),
    listRequirementApprovals: (requirementId, signal) => safeGet(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/approvals`, { signal }).then((body) => body?.approvals || []),
    createRequirementApproval: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/approvals`, payload),
    approveRequirementApproval: (requirementId, approvalId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/approvals/${encodeURIComponent(approvalId)}/approve`, payload),
    rejectRequirementApproval: (requirementId, approvalId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/approvals/${encodeURIComponent(approvalId)}/reject`, payload),
    requestChangesRequirementApproval: (requirementId, approvalId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/approvals/${encodeURIComponent(approvalId)}/request-changes`, payload),
    listAcceptanceCriteria: (requirementId, signal) => safeGet(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/acceptance-criteria`, { signal }).then((body) => body?.acceptance_criteria || []),
    createAcceptanceCriterion: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/acceptance-criteria`, payload),
    listRequirementComments: (requirementId, signal) => safeGet(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/comments`, { signal }).then((body) => body?.comments || []),
    addRequirementComment: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/comments`, payload),
    listRequirementRelationships: (requirementId, signal) => safeGet(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/relationships`, { signal }).then((body) => body?.relationships || []),
    addRequirementRelationship: (requirementId, payload) => mutation(`/v1/novacodepro/requirements/${encodeURIComponent(requirementId)}/relationships`, payload),
    listTraceabilityLinks: (signal) => safeGet("/v1/novacodepro/traceability/links", { signal }).then((body) => body?.links || []),
    createTraceabilityLink: (payload) => mutation("/v1/novacodepro/traceability/links", payload),
    getTraceabilityCoverage: (signal) => safeGet("/v1/novacodepro/traceability/coverage", { signal }),
    listKnowledgeSpaces: (signal) => safeGet("/v1/novacodepro/knowledge/spaces", { signal }).then((body) => body?.spaces || []),
    createKnowledgeSpace: (payload) => mutation("/v1/novacodepro/knowledge/spaces", payload),
    listKnowledgeDocuments: (signal, params = {}) => {
      const query = new URLSearchParams();
      if (params.space_id) query.set("space_id", params.space_id);
      if (params.content_type) query.set("content_type", params.content_type);
      const suffix = query.toString() ? `?${query.toString()}` : "";
      return safeGet(`/v1/novacodepro/knowledge/documents${suffix}`, { signal }).then((body) => body?.documents || []);
    },
    createKnowledgeDocument: (payload) => mutation("/v1/novacodepro/knowledge/documents", payload),
    getKnowledgeDocument: (documentId, signal) => request(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}`, { signal }),
    publishKnowledgeDocument: (documentId) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/publish`, {}),
    archiveKnowledgeDocument: (documentId) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/archive`, {}),
    listKnowledgeVersions: (documentId, signal) => safeGet(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/versions`, { signal }).then((body) => body?.versions || []),
    listKnowledgeReviews: (documentId, signal) => safeGet(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/reviews`, { signal }).then((body) => body?.reviews || []),
    createKnowledgeReview: (documentId, payload) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/reviews`, payload),
    listKnowledgeApprovals: (documentId, signal) => safeGet(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/approvals`, { signal }).then((body) => body?.approvals || []),
    createKnowledgeApproval: (documentId, payload) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/approvals`, payload),
    listKnowledgeComments: (documentId, signal) => safeGet(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/comments`, { signal }).then((body) => body?.comments || []),
    addKnowledgeComment: (documentId, payload) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/comments`, payload),
    listKnowledgeTags: (signal) => safeGet("/v1/novacodepro/knowledge/tags", { signal }).then((body) => body?.tags || []),
    createKnowledgeTag: (payload) => mutation("/v1/novacodepro/knowledge/tags", payload),
    addKnowledgeTag: (documentId, payload) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/tags`, payload),
    listKnowledgeRelationships: (documentId, signal) => safeGet(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/relationships`, { signal }).then((body) => body?.relationships || []),
    addKnowledgeRelationship: (documentId, payload) => mutation(`/v1/novacodepro/knowledge/documents/${encodeURIComponent(documentId)}/relationships`, payload),
    searchKnowledge: (payload) => mutation("/v1/novacodepro/knowledge/search", payload),
    answerKnowledge: (payload) => mutation("/v1/novacodepro/knowledge/answer", payload),
    retrieveKnowledge: (payload) => mutation("/v1/novacodepro/knowledge/retrieve", payload),
    listSearchHistory: (signal) => safeGet("/v1/novacodepro/knowledge/search/history", { signal }).then((body) => body?.searches || []),
  };
}
