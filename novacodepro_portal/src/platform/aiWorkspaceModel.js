const DEFAULT_ROLE_SUGGESTIONS = {
  DEVELOPER: ["Generate implementation plan", "Review repository", "Fix failing tests", "Generate API"],
  ARCHITECT: ["Generate target architecture", "Create ADR", "Assess scalability", "Review service boundaries"],
  QA_ENGINEER: ["Generate regression suite", "Identify missing coverage", "Create acceptance tests", "Assess release readiness"],
  SECURITY_ENGINEER: ["Generate threat model", "Review authentication", "Analyze vulnerabilities", "Create remediation plan"],
  CUSTOMER: ["Turn my idea into a structured project", "Explain what requires my approval", "Show unresolved risks"],
};

function listify(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  if (value && typeof value === "object") {
    return Object.values(value).filter(Boolean);
  }
  return [];
}

function asText(value, fallback = "Unknown") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return fallback;
}

export function buildUniversalAIWorkspaceModel({
  session,
  role,
  roleLabel,
  workspace,
  project,
  tenant,
  organization,
  environment,
  route,
  modelLabel,
  statusLabel,
  connection,
  request,
  requestState,
  requestSummary,
  requestConfidence,
  requestIntent,
  requestOutcome,
  requestScope,
  requestTools,
  requestApprovals,
  requestQuestions,
  requestFiles,
  requestArtifacts,
  requestApprovalsState,
  executionState,
  knowledgeState,
  currentAgentTasks,
  conversations,
  savedPrompts,
  approvedSolutions,
  sharedConversations,
  recentRequests,
  suggestedPrompts,
  artifacts,
  timeline,
  approvals,
  evidence,
  knowledge,
  policies,
  standards,
  context,
  metrics,
  supportedActions,
  timelineFilters,
  onTimelineFilterChange,
} = {}) {
  const normalizedRequest = request || {};
  const requestLifecycleState = String(requestState || normalizedRequest.status || "IDLE").toUpperCase();
  const agents = listify(currentAgentTasks).map((agent, index) => ({
    id: agent.id || `agent-${index}`,
    name: agent.name || agent.title || "Agent",
    role: agent.role || agent.domain || "Agent",
    currentTask: agent.currentTask || agent.task || "Not connected",
    state: String(agent.state || agent.status || "NOT_CONNECTED").toUpperCase(),
    progress: typeof agent.progress === "number" ? agent.progress : null,
    startedAt: agent.startedAt || agent.started_at || null,
    completedAt: agent.completedAt || agent.completed_at || null,
    outputs: listify(agent.outputs || agent.artifacts || []),
    errors: listify(agent.errors || []),
    evidence: listify(agent.evidence || []),
    handoffTarget: agent.handoffTarget || agent.handoff_target || "",
  }));

  const artifactList = listify(artifacts || requestArtifacts || normalizedRequest.artifacts).map((artifact, index) => ({
    id: artifact.id || `artifact-${index}`,
    title: artifact.title || artifact.name || artifact.label || artifact.id || "Artifact",
    type: artifact.type || artifact.kind || artifact.artifact_type || "Artifact",
    version: artifact.version || artifact.revision || "1",
    status: artifact.status || artifact.review_status || artifact.stage || "Draft",
    owner: artifact.owner || artifact.created_by || "Not connected",
    generator: artifact.generator || artifact.generated_by || artifact.source || "Not connected",
    requirements: listify(artifact.requirements || artifact.requirement_ids || []),
    tests: listify(artifact.tests || artifact.test_ids || []),
    reviewStatus: artifact.reviewStatus || artifact.review_status || "Pending",
    approvalStatus: artifact.approvalStatus || artifact.approval_status || "Pending",
    evidence: listify(artifact.evidence || artifact.evidence_ids || []),
    updatedAt: artifact.updatedAt || artifact.updated_at || artifact.createdAt || artifact.created_at || null,
  }));

  const timelineItems = listify(timeline).map((event, index) => ({
    id: event.id || `timeline-${index}`,
    timestamp: event.timestamp || event.at || event.created_at || event.createdAt || null,
    actor: event.actor || event.user || "Unknown",
    agent: event.agent || event.agent_name || "System",
    tool: event.tool || event.service || "Not connected",
    status: event.status || event.state || requestLifecycleState,
    correlationId: event.correlationId || event.correlation_id || event.correlation || "",
    evidenceReference: event.evidenceReference || event.evidence || "",
    duration: event.duration || event.latency || event.elapsed || "",
    severity: event.severity || "info",
    summary: event.summary || event.action || event.title || "Event",
    error: event.error || "",
    artifact: event.artifact || "",
    stage: event.stage || "",
  }));

  const approvalList = listify(approvals || requestApprovals || normalizedRequest.approvals).map((approval, index) => ({
    id: approval.id || `approval-${index}`,
    type: approval.type || approval.gate || "Approval",
    project: approval.project || asText(project, "Project"),
    version: approval.version || "1",
    requestedBy: approval.requestedBy || approval.by || "Not connected",
    requestedAt: approval.requestedAt || approval.at || null,
    requiredRole: approval.requiredRole || approval.required_role || approval.role || "Required role",
    status: String(approval.status || "PENDING").toUpperCase(),
    dueDate: approval.dueDate || approval.due_at || "",
    riskLevel: approval.riskLevel || approval.risk_level || "unknown",
    evidence: listify(approval.evidence || approval.evidence_ids || []),
    comments: listify(approval.comments || []),
    policy: approval.policy || approval.policyId || approval.policy_id || "Not connected",
    signature: approval.signature || approval.signature_meta || "",
  }));

  const knowledgeList = listify(knowledge).map((item, index) => ({
    id: item.id || `knowledge-${index}`,
    title: item.title || item.name || item.label || "Knowledge",
    state: String(item.state || item.status || knowledgeState || "DRAFT").toUpperCase(),
    project: item.project || asText(project, ""),
    artifact: item.artifact || "",
    version: item.version || "1",
    evidence: listify(item.evidence || item.evidence_ids || []),
    supersededVersions: listify(item.supersededVersions || item.superseded_versions || []),
  }));

  const conversationItems = listify(conversations || recentRequests || []).map((conversation, index) => ({
    id: conversation.id || `conversation-${index}`,
    title: conversation.title || conversation.subject || conversation.request || "Conversation",
    project: conversation.project || asText(project, ""),
    role: conversation.role || roleLabel || role || "Role",
    status: String(conversation.status || requestLifecycleState).toUpperCase(),
    updatedAt: conversation.updatedAt || conversation.updated_at || conversation.createdAt || conversation.created_at || null,
    shared: Boolean(conversation.shared),
    approved: Boolean(conversation.approved || conversation.approvalStatus === "APPROVED"),
  }));

  const suggestionList = listify(suggestedPrompts || DEFAULT_ROLE_SUGGESTIONS[String(role || "").toUpperCase()] || DEFAULT_ROLE_SUGGESTIONS.CUSTOMER).map((item) =>
    typeof item === "string" ? { label: item, detail: "Send to NovaAI" } : item,
  );

  return {
    title: "Universal AI Workspace",
    breadcrumb: route || "Workspace",
    roleLabel: roleLabel || role || "Role",
    userLabel: session?.display_name || session?.email || "Signed in user",
    tenantLabel: tenant || session?.tenant_id || session?.tenant || "Unknown tenant",
    organizationLabel: organization || session?.organization || "Unknown organization",
    workspaceLabel: workspace || "NovaCodePro",
    environment: environment || "Production",
    modelLabel: modelLabel || "No model connected",
    statusLabel: statusLabel || (connection?.connected ? "Connected" : "Not connected"),
    connection: {
      connected: Boolean(connection?.connected),
      backend: Boolean(connection?.backend),
      runtime: Boolean(connection?.runtime ?? true),
      reason: connection?.reason || (connection?.connected ? "Connected" : "Not connected"),
      lastSyncedAt: connection?.lastSyncedAt || null,
    },
    request: {
      id: normalizedRequest.id || "",
      prompt: normalizedRequest.request || normalizedRequest.prompt || "",
      title: normalizedRequest.title || normalizedRequest.name || "Conversation",
      state: requestLifecycleState,
      summary: requestSummary || normalizedRequest.summary || "",
      confidence: requestConfidence ?? normalizedRequest.confidence ?? null,
      intent: requestIntent || normalizedRequest.intent || "Unknown",
      outcome: requestOutcome || normalizedRequest.outcome || "",
      scope: requestScope || normalizedRequest.scope || "",
      tools: listify(requestTools || normalizedRequest.tools || []),
      approvals: listify(requestApprovals || normalizedRequest.requiredApprovals || []),
      questions: listify(requestQuestions || normalizedRequest.questions || []),
      files: listify(requestFiles || normalizedRequest.files || []),
      approvalsState: requestApprovalsState || "NOT_REQUIRED",
    },
    executionState: executionState || "IDLE",
    knowledgeState: knowledgeState || "DRAFT",
    conversations: conversationItems,
    savedPrompts: listify(savedPrompts).map((item) => (typeof item === "string" ? { title: item } : item)),
    approvedSolutions: listify(approvedSolutions),
    sharedConversations: listify(sharedConversations),
    recentRequests: listify(recentRequests),
    suggestions: suggestionList,
    agents,
    artifacts: artifactList,
    timeline: timelineItems,
    approvals: approvalList,
    evidence: listify(evidence),
    knowledge: knowledgeList,
    policies: listify(policies),
    standards: listify(standards),
    context: context || {},
    metrics: metrics || {},
    timelineFilters: timelineFilters || {},
    onTimelineFilterChange,
    supportedActions: {
      ask: Boolean(supportedActions?.ask),
      plan: Boolean(supportedActions?.plan),
      generate: Boolean(supportedActions?.generate),
      analyze: Boolean(supportedActions?.analyze),
      review: Boolean(supportedActions?.review),
      compare: Boolean(supportedActions?.compare),
      createWorkflow: Boolean(supportedActions?.createWorkflow),
      cancel: Boolean(supportedActions?.cancel),
      approve: Boolean(supportedActions?.approve),
      reject: Boolean(supportedActions?.reject),
      requestChanges: Boolean(supportedActions?.requestChanges),
      execute: Boolean(supportedActions?.execute),
      verify: Boolean(supportedActions?.verify),
      publishKnowledge: Boolean(supportedActions?.publishKnowledge),
    },
  };
}
