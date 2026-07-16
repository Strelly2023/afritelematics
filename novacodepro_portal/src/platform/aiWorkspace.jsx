import React from "react";

export const AI_REQUEST_STATES = [
  "IDLE",
  "REQUESTED",
  "ANALYZING",
  "CLARIFICATION_REQUIRED",
  "PLANNING",
  "READY_TO_GENERATE",
  "GENERATING",
  "DRAFT_READY",
  "IN_REVIEW",
  "CHANGES_REQUESTED",
  "APPROVAL_PENDING",
  "APPROVED",
  "EXECUTION_READY",
  "EXECUTING",
  "VERIFYING",
  "VERIFIED",
  "SAVED",
  "FAILED",
  "CANCELLED",
  "SUPERSEDED",
];

const DEFAULT_ROLE_SUGGESTIONS = {
  DEVELOPER: ["Generate implementation plan", "Review repository", "Fix failing tests", "Generate API"],
  ARCHITECT: ["Generate target architecture", "Create ADR", "Assess scalability", "Review service boundaries"],
  QA_ENGINEER: ["Generate regression suite", "Identify missing coverage", "Create acceptance tests", "Assess release readiness"],
  SECURITY_ENGINEER: ["Generate threat model", "Review authentication", "Analyze vulnerabilities", "Create remediation plan"],
  CUSTOMER: ["Turn my idea into a structured project", "Explain what requires my approval", "Show unresolved risks"],
};

const DEFAULT_STATE_LABELS = {
  IDLE: "Idle",
  REQUESTED: "Requested",
  ANALYZING: "Analyzing",
  CLARIFICATION_REQUIRED: "Clarification required",
  PLANNING: "Planning",
  READY_TO_GENERATE: "Ready to generate",
  GENERATING: "Generating",
  DRAFT_READY: "Draft ready",
  IN_REVIEW: "In review",
  CHANGES_REQUESTED: "Changes requested",
  APPROVAL_PENDING: "Approval pending",
  APPROVED: "Approved",
  EXECUTION_READY: "Execution ready",
  EXECUTING: "Executing",
  VERIFYING: "Verifying",
  VERIFIED: "Verified",
  SAVED: "Saved",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
  SUPERSEDED: "Superseded",
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

function formatDate(value) {
  if (!value) {
    return "Not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function statusTone(status) {
  const value = String(status || "").toUpperCase();
  if (["APPROVED", "VERIFIED", "SAVED", "COMPLETED", "PUBLISHED", "RUNNING"].includes(value)) return "success";
  if (["REQUESTED", "ANALYZING", "PLANNING", "APPROVAL_PENDING", "EXECUTING", "VERIFYING", "IN_REVIEW"].includes(value)) {
    return "info";
  }
  if (["CLARIFICATION_REQUIRED", "CHANGES_REQUESTED", "FAILED", "BLOCKED", "REJECTED"].includes(value)) {
    return "warning";
  }
  if (["CANCELLED", "SUPERSEDED", "EXPIRED", "RETIRED"].includes(value)) return "neutral";
  return "neutral";
}

function badge({ label, value, tone = "neutral" }) {
  return (
    <span className={`ai-badge tone-${tone}`}>
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
  );
}

function Panel({ label, title, description, actions, children, tone = "neutral" }) {
  return (
    <section className={`ai-panel tone-${tone}`}>
      <div className="ai-panel-head">
        <div>
          <p className="section-label">{label}</p>
          <h3>{title}</h3>
          {description ? <p className="studio-note">{description}</p> : null}
        </div>
        {actions ? <div className="ai-panel-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

function EmptyPanel({ title, message }) {
  return (
    <div className="solution-empty ai-empty">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}

function renderPairList(items) {
  const pairs = listify(items);
  if (!pairs.length) {
    return <EmptyPanel title="Not connected" message="The backend capability does not yet exist or no records were returned." />;
  }
  return (
    <div className="ai-list">
      {pairs.map((item, index) => {
        if (Array.isArray(item)) {
          const [label, value] = item;
          return (
            <div className="ai-list-row" key={`${label}-${index}`}>
              <strong>{label}</strong>
              <span>{value}</span>
            </div>
          );
        }
        if (typeof item === "string" || typeof item === "number") {
          return (
            <div className="ai-list-row" key={`${item}-${index}`}>
              <strong>{String(item)}</strong>
              <span>Not connected</span>
            </div>
          );
        }
        return (
          <div className="ai-list-row" key={item.id || item.title || index}>
            <strong>{item.title || item.name || item.label || item.id}</strong>
            <span>{item.detail || item.value || item.status || item.stage || "Not connected"}</span>
          </div>
        );
      })}
    </div>
  );
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
    project: approval.project || project?.name || "Project",
    version: approval.version || project?.version || "1",
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
    project: item.project || project?.name || "",
    artifact: item.artifact || "",
    version: item.version || "1",
    evidence: listify(item.evidence || item.evidence_ids || []),
    supersededVersions: listify(item.supersededVersions || item.superseded_versions || []),
  }));

  const conversationItems = listify(conversations || recentRequests || []).map((conversation, index) => ({
    id: conversation.id || `conversation-${index}`,
    title: conversation.title || conversation.subject || conversation.request || "Conversation",
    project: conversation.project || project?.name || "",
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
    timelineFilters: input.timelineFilters || {},
    onTimelineFilterChange: input.onTimelineFilterChange,
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

export function AIRequestComposer({
  model,
  value,
  onChange,
  attachments = [],
  onAttachmentUpload,
  onRemoveAttachment,
  selectedMode,
  onModeChange,
  selectedAgents = [],
  onToggleAgent,
  selectedContextSources = [],
  onToggleContextSource,
  selectedProjectArtifact,
  selectedIncident,
  selectedRequirement,
  selectedToolContext,
  onAction,
  highRisk = false,
}) {
  const mode = selectedMode || "ask";
  const actionHandlers = onAction || {};
  return (
    <Panel
      label="AI composer"
      title="Ask NovaAI"
      description="Text, transcript, files, repositories, and selected artifacts become a governed request."
      tone={highRisk ? "warning" : "neutral"}
      actions={
        model?.request?.state ? badge({ label: "State", value: DEFAULT_STATE_LABELS[model.request.state] || model.request.state, tone: statusTone(model.request.state) }) : null
      }
    >
      {highRisk ? <div className="ai-warning">High-risk requests require review and approval before execution.</div> : null}
      <div className="ai-composer-meta">
        {badge({ label: "Project", value: asText(model?.context?.project || model?.request?.title || "Not connected") })}
        {badge({ label: "Role", value: asText(model?.roleLabel) })}
        {badge({ label: "Tenant", value: asText(model?.tenantLabel) })}
        {badge({ label: "Environment", value: asText(model?.environment) })}
        {badge({ label: "Tool", value: asText(selectedToolContext || "Chat") })}
      </div>
      <label className="ai-composer-field">
        <span>Request</span>
        <textarea
          rows="5"
          value={value}
          onChange={(event) => onChange?.(event.target.value)}
          placeholder="Describe the outcome, the constraints, and the artifact you want NovaAI to generate."
        />
      </label>
      <div className="ai-composer-toolbar">
        {[
          ["Ask", "ask"],
          ["Plan", "plan"],
          ["Generate", "generate"],
          ["Analyze", "analyze"],
          ["Review", "review"],
          ["Compare", "compare"],
          ["Create Workflow", "createWorkflow"],
          ["Cancel", "cancel"],
        ].map(([label, key]) => {
          const supported = Boolean(model?.supportedActions?.[key] || actionHandlers[key]);
          return (
            <button
              key={key}
              type="button"
              className="toolbar-chip"
              disabled={!supported}
              title={supported ? label : "Not connected"}
              onClick={() => actionHandlers[key]?.(mode)}
            >
              {label}
            </button>
          );
        })}
      </div>
      <div className="ai-composer-support">
        <label className="field">
          <span>Mode</span>
          <select value={mode} onChange={(event) => onModeChange?.(event.target.value)}>
            {["ask", "plan", "generate", "analyze", "review", "compare"].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Project artifact</span>
          <input value={selectedProjectArtifact || ""} readOnly placeholder="Selected artifact" />
        </label>
        <label className="field">
          <span>Requirement</span>
          <input value={selectedRequirement || ""} readOnly placeholder="Selected requirement" />
        </label>
        <label className="field">
          <span>Incident</span>
          <input value={selectedIncident || ""} readOnly placeholder="Selected incident" />
        </label>
      </div>
      <div className="ai-attachment-grid">
        <div>
          <p className="section-label">Attachments</p>
          <div className="ai-attachment-list">
            {attachments.length ? (
              attachments.map((attachment) => (
                <div className="ai-attachment-row" key={attachment.id}>
                  <strong>{attachment.name || attachment.title}</strong>
                  <span>{attachment.type || attachment.kind || "File"}</span>
                  {onRemoveAttachment ? (
                    <button type="button" className="toolbar-chip" onClick={() => onRemoveAttachment(attachment.id)}>
                      Remove
                    </button>
                  ) : null}
                </div>
              ))
            ) : (
              <EmptyPanel title="No attachments" message="Upload documents, images, code, or repository metadata." />
            )}
          </div>
        </div>
        <div>
          <p className="section-label">Context sources</p>
          <div className="chip-cloud">
            {["Conversation", "Project", "Repository", "Selected artifact", "Knowledge", "Policies"].map((source) => (
              <button
                type="button"
                key={source}
                className={selectedContextSources.includes(source) ? "context-chip active" : "context-chip"}
                onClick={() => onToggleContextSource?.(source)}
              >
                {source}
              </button>
            ))}
          </div>
          <p className="section-label">Agents</p>
          <div className="chip-cloud">
            {(model?.agents || []).map((agent) => (
              <button
                type="button"
                key={agent.id}
                className={selectedAgents.includes(agent.name) ? "context-chip active" : "context-chip"}
                onClick={() => onToggleAgent?.(agent.name)}
              >
                {agent.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Panel>
  );
}

export function AIUnderstandingPanel({ model, onConfirmInterpretation, onCorrectInterpretation, onAddContext, onRequestClarification, onRegeneratePlan }) {
  return (
    <Panel
      label="Understanding"
      title="AI understanding"
      description="Intent, scope, affected systems, agents, tools, approvals, and risk."
      actions={badge({ label: "Confidence", value: model?.request?.confidence ?? "Unknown", tone: model?.request?.confidence ? "info" : "neutral" })}
    >
      <div className="ai-detail-list">
        {[
          ["Intent", model?.request?.intent],
          ["Project", model?.context?.project || model?.request?.title],
          ["Workspace", model?.workspaceLabel],
          ["Environment", model?.environment],
          ["Requested outcome", model?.request?.outcome],
          ["Estimated scope", model?.request?.scope],
          ["Required tools", listify(model?.request?.tools).join(", ") || "Not assessed"],
          ["Required approvals", listify(model?.request?.approvals).join(", ") || "Not assessed"],
          ["Risk level", model?.context?.riskLevel || "Not assessed"],
          ["Compliance impact", model?.context?.complianceImpact || "Not assessed"],
          ["Unresolved questions", listify(model?.request?.questions).join(" | ") || "None"],
        ].map(([label, value]) => (
          <div className="ai-list-row" key={label}>
            <strong>{label}</strong>
            <span>{asText(value, "Unknown")}</span>
          </div>
        ))}
      </div>
      <div className="ai-panel-actions compact">
        <button type="button" className="toolbar-chip" onClick={onConfirmInterpretation}>Confirm</button>
        <button type="button" className="toolbar-chip" onClick={onCorrectInterpretation}>Correct</button>
        <button type="button" className="toolbar-chip" onClick={onAddContext}>Add context</button>
        <button type="button" className="toolbar-chip" onClick={onRequestClarification}>Clarify</button>
        <button type="button" className="toolbar-chip" onClick={onRegeneratePlan}>Regenerate plan</button>
      </div>
    </Panel>
  );
}

export function AgentCollaborationPanel({ model, onInspectWork, onPause, onCancel, onRetry, onReassign, onRequestReview, onOpenOutput, onOpenEvidence }) {
  return (
    <Panel label="Agents" title="Multi-agent collaboration" description="Specialist agents, tasks, outputs, and handoffs." >
      <div className="ai-agent-list">
        {model?.agents?.length ? (
          model.agents.map((agent) => (
            <article className="ai-agent-card" key={agent.id}>
              <div className="ai-agent-head">
                <div>
                  <strong>{agent.name}</strong>
                  <p className="studio-note">{agent.role}</p>
                </div>
                {badge({ label: "State", value: agent.state, tone: statusTone(agent.state) })}
              </div>
              <div className="ai-progress" aria-label={`${agent.name} progress`}>
                <span style={{ width: `${Math.max(0, Math.min(100, agent.progress ?? 0))}%` }} />
              </div>
              <div className="ai-detail-list compact">
                {[
                  ["Task", agent.currentTask],
                  ["Started", formatDate(agent.startedAt)],
                  ["Completed", formatDate(agent.completedAt)],
                  ["Handoff", agent.handoffTarget || "Not connected"],
                ].map(([label, value]) => (
                  <div className="ai-list-row" key={`${agent.id}-${label}`}>
                    <strong>{label}</strong>
                    <span>{asText(value)}</span>
                  </div>
                ))}
              </div>
              <div className="ai-panel-actions compact">
                <button type="button" className="toolbar-chip" onClick={() => onInspectWork?.(agent)}>Inspect</button>
                <button type="button" className="toolbar-chip" onClick={() => onPause?.(agent)}>Pause</button>
                <button type="button" className="toolbar-chip" onClick={() => onCancel?.(agent)}>Cancel</button>
                <button type="button" className="toolbar-chip" onClick={() => onRetry?.(agent)}>Retry</button>
                <button type="button" className="toolbar-chip" onClick={() => onReassign?.(agent)}>Reassign</button>
                <button type="button" className="toolbar-chip" onClick={() => onRequestReview?.(agent)}>Review</button>
                <button type="button" className="toolbar-chip" onClick={() => onOpenOutput?.(agent)}>Output</button>
                <button type="button" className="toolbar-chip" onClick={() => onOpenEvidence?.(agent)}>Evidence</button>
              </div>
            </article>
          ))
        ) : (
          <EmptyPanel title="Not connected" message="Agent orchestration data has not been returned yet." />
        )}
      </div>
    </Panel>
  );
}

export function ExecutionTimeline({ model, filters = {}, onFilterChange }) {
  const events = model?.timeline || [];
  const visible = events.filter((event) => {
    if (filters.agent && !String(event.agent || "").toLowerCase().includes(String(filters.agent).toLowerCase())) return false;
    if (filters.tool && !String(event.tool || "").toLowerCase().includes(String(filters.tool).toLowerCase())) return false;
    if (filters.artifact && !String(event.artifact || "").toLowerCase().includes(String(filters.artifact).toLowerCase())) return false;
    if (filters.stage && !String(event.stage || "").toLowerCase().includes(String(filters.stage).toLowerCase())) return false;
    if (filters.severity && String(event.severity || "").toLowerCase() !== String(filters.severity).toLowerCase()) return false;
    return true;
  });
  return (
    <Panel label="Timeline" title="Execution timeline" description="Request, plan, execution, verification, evidence, and knowledge." >
      <div className="ai-filter-row">
        {[
          ["agent", "Agent"],
          ["tool", "Tool"],
          ["artifact", "Artifact"],
          ["stage", "Stage"],
          ["severity", "Severity"],
        ].map(([key, label]) => (
          <label className="field compact" key={key}>
            <span>{label}</span>
            <input
              value={filters[key] || ""}
              onChange={(event) => onFilterChange?.({ ...filters, [key]: event.target.value })}
              placeholder={`Filter by ${label.toLowerCase()}`}
            />
          </label>
        ))}
      </div>
      <div className="ai-timeline">
        {visible.length ? (
          visible.map((event) => (
            <article className="ai-timeline-item" key={event.id}>
              <strong>{event.summary}</strong>
              <p className="studio-note">
                {formatDate(event.timestamp)} · {event.actor} · {event.agent} · {event.tool}
              </p>
              <div className="chip-cloud">
                {badge({ label: "Status", value: event.status, tone: statusTone(event.status) })}
                {event.correlationId ? badge({ label: "Correlation", value: event.correlationId }) : null}
                {event.evidenceReference ? badge({ label: "Evidence", value: event.evidenceReference }) : null}
                {event.duration ? badge({ label: "Duration", value: event.duration }) : null}
              </div>
              {event.error ? <p className="ai-error">{event.error}</p> : null}
            </article>
          ))
        ) : (
          <EmptyPanel title="No timeline events" message="The backend has not returned execution events for this workspace." />
        )}
      </div>
    </Panel>
  );
}

export function ArtifactExplorer({ model, onOpen, onCompare, onReview, onComment, onRequestChanges, onApprove, onReject, onRegenerate, onExport, onOpenSpecialized }) {
  return (
    <Panel label="Artifacts" title="Artifact explorer" description="Requirements, architecture, design, code, tests, security, evidence, and knowledge." >
      <div className="ai-artifact-grid">
        {model?.artifacts?.length ? (
          model.artifacts.map((artifact) => (
            <article className="ai-artifact-card" key={artifact.id}>
              <div className="ai-agent-head">
                <div>
                  <strong>{artifact.title}</strong>
                  <p className="studio-note">
                    {artifact.type} · v{artifact.version} · {artifact.owner}
                  </p>
                </div>
                {badge({ label: "Status", value: artifact.status, tone: statusTone(artifact.status) })}
              </div>
              <div className="ai-detail-list compact">
                {[
                  ["Generator", artifact.generator],
                  ["Review", artifact.reviewStatus],
                  ["Approval", artifact.approvalStatus],
                  ["Updated", formatDate(artifact.updatedAt)],
                ].map(([label, value]) => (
                  <div className="ai-list-row" key={`${artifact.id}-${label}`}>
                    <strong>{label}</strong>
                    <span>{asText(value, "Not connected")}</span>
                  </div>
                ))}
              </div>
              <div className="chip-cloud">
                {artifact.requirements.slice(0, 3).map((item) => (
                  <span className="context-chip" key={`${artifact.id}-req-${item}`}>{item}</span>
                ))}
                {artifact.tests.slice(0, 3).map((item) => (
                  <span className="context-chip" key={`${artifact.id}-test-${item}`}>{item}</span>
                ))}
              </div>
              <div className="ai-panel-actions compact">
                <button type="button" className="toolbar-chip" onClick={() => onOpen?.(artifact)}>Open</button>
                <button type="button" className="toolbar-chip" onClick={() => onCompare?.(artifact)}>Compare</button>
                <button type="button" className="toolbar-chip" onClick={() => onReview?.(artifact)}>Review</button>
                <button type="button" className="toolbar-chip" onClick={() => onComment?.(artifact)}>Comment</button>
                <button type="button" className="toolbar-chip" onClick={() => onRequestChanges?.(artifact)}>Request changes</button>
                <button type="button" className="toolbar-chip" onClick={() => onApprove?.(artifact)}>Approve</button>
                <button type="button" className="toolbar-chip" onClick={() => onReject?.(artifact)}>Reject</button>
                <button type="button" className="toolbar-chip" onClick={() => onRegenerate?.(artifact)}>Regenerate</button>
                <button type="button" className="toolbar-chip" onClick={() => onExport?.(artifact)}>Export</button>
                <button type="button" className="toolbar-chip" onClick={() => onOpenSpecialized?.(artifact)}>Open specialized tool</button>
              </div>
            </article>
          ))
        ) : (
          <EmptyPanel title="Not connected" message="No artifact records were returned by the backend." />
        )}
      </div>
    </Panel>
  );
}

export function SolutionReviewWorkspace({ model, sections = [], onApprove, onReject, onRequestChanges, onEditDirectly, onAskFollowUp, onSendToReviewer, onCompareVersion, onOpenEvidence }) {
  return (
    <Panel label="Review" title="Solution review workspace" description="Section-level review of request, plan, artifacts, risks, and rollback." >
      <div className="ai-detail-list">
        {[
          ["Request summary", model?.request?.summary],
          ["Plan summary", model?.context?.planSummary],
          ["Affected artifacts", listify(model?.artifacts).length],
          ["Files changed", model?.context?.filesChanged || "Not connected"],
          ["APIs changed", model?.context?.apisChanged || "Not connected"],
          ["Migrations", model?.context?.migrations || "Not connected"],
          ["Tests added", model?.context?.testsAdded || "Not connected"],
          ["Security result", model?.context?.securityResult || "Not assessed"],
          ["Compliance result", model?.context?.complianceResult || "Not assessed"],
          ["Rollback plan", model?.context?.rollbackPlan || "Not connected"],
        ].map(([label, value]) => (
          <div className="ai-list-row" key={label}>
            <strong>{label}</strong>
            <span>{asText(value, "Unknown")}</span>
          </div>
        ))}
      </div>
      <div className="chip-cloud">
        {listify(sections).length ? sections.map((section) => <span className="context-chip" key={section}>{section}</span>) : <span className="context-chip">Section-level review</span>}
      </div>
      <div className="ai-panel-actions compact">
        <button type="button" className="toolbar-chip" onClick={onApprove}>Approve</button>
        <button type="button" className="toolbar-chip" onClick={onReject}>Reject</button>
        <button type="button" className="toolbar-chip" onClick={onRequestChanges}>Request changes</button>
        <button type="button" className="toolbar-chip" onClick={onEditDirectly}>Edit directly</button>
        <button type="button" className="toolbar-chip" onClick={onAskFollowUp}>Ask follow-up</button>
        <button type="button" className="toolbar-chip" onClick={onSendToReviewer}>Send to reviewer</button>
        <button type="button" className="toolbar-chip" onClick={onCompareVersion}>Compare version</button>
        <button type="button" className="toolbar-chip" onClick={onOpenEvidence}>Open evidence</button>
      </div>
    </Panel>
  );
}

export function ApprovalWorkspace({ model, onApprove, onReject, onRequestChanges, onDelegate, onOpenArtifact, onOpenPolicy, onOpenEvidence }) {
  return (
    <Panel label="Approvals" title="Approval workspace" description="Required approvals, policy basis, comments, signatures, and evidence." >
      {renderPairList(model?.approvals)}
      <div className="ai-panel-actions compact">
        <button type="button" className="toolbar-chip" onClick={onApprove}>Approve</button>
        <button type="button" className="toolbar-chip" onClick={onReject}>Reject</button>
        <button type="button" className="toolbar-chip" onClick={onRequestChanges}>Request changes</button>
        <button type="button" className="toolbar-chip" onClick={onDelegate}>Delegate</button>
        <button type="button" className="toolbar-chip" onClick={onOpenArtifact}>Open related artifact</button>
        <button type="button" className="toolbar-chip" onClick={onOpenPolicy}>Open policy</button>
        <button type="button" className="toolbar-chip" onClick={onOpenEvidence}>Open evidence</button>
      </div>
    </Panel>
  );
}

export function ExecutionMonitor({ model, onPause, onResume, onCancel, onRetryFailedStep, onOpenLogs, onOpenTraces, onOpenEvidence, onRollback }) {
  const stages = listify(model?.context?.executionStages || model?.executionStages || []);
  const total = stages.length || 1;
  const completed = stages.filter((item) => String(item.status || "").toUpperCase() === "COMPLETED").length;
  const progress = Math.round((completed / total) * 100);
  return (
    <Panel label="Execution" title="Execution monitor" description="Authoritative execution progress, logs, traces, metrics, and evidence." >
      <div className="ai-progress" aria-label="Overall execution progress">
        <span style={{ width: `${progress}%` }} />
      </div>
      <div className="ai-detail-list">
        {[
          ["Overall progress", `${progress}%`],
          ["Current step", model?.context?.currentStep || "Not connected"],
          ["Queued steps", model?.context?.queuedSteps || "Not connected"],
          ["Failed steps", model?.context?.failedSteps || "0"],
          ["Cancelled steps", model?.context?.cancelledSteps || "0"],
          ["Retries", model?.context?.retries || "0"],
          ["Estimated remaining", model?.context?.estimatedRemaining || "Not connected"],
        ].map(([label, value]) => (
          <div className="ai-list-row" key={label}>
            <strong>{label}</strong>
            <span>{asText(value)}</span>
          </div>
        ))}
      </div>
      <div className="ai-panel-actions compact">
        <button type="button" className="toolbar-chip" onClick={onPause}>Pause</button>
        <button type="button" className="toolbar-chip" onClick={onResume}>Resume</button>
        <button type="button" className="toolbar-chip" onClick={onCancel}>Cancel</button>
        <button type="button" className="toolbar-chip" onClick={onRetryFailedStep}>Retry failed step</button>
        <button type="button" className="toolbar-chip" onClick={onOpenLogs}>Open logs</button>
        <button type="button" className="toolbar-chip" onClick={onOpenTraces}>Open traces</button>
        <button type="button" className="toolbar-chip" onClick={onOpenEvidence}>Open evidence</button>
        <button type="button" className="toolbar-chip" onClick={onRollback}>Rollback</button>
      </div>
      <div className="ai-list">
        {stages.length ? stages.map((stage) => (
          <div className="ai-list-row" key={stage.id || stage.label}>
            <strong>{stage.label || stage.name}</strong>
            <span>{stage.status || "Queued"}</span>
          </div>
        )) : <EmptyPanel title="Not connected" message="Execution steps are not available yet." />}
      </div>
    </Panel>
  );
}

export function KnowledgeCapturePanel({ model, onView, onPublish, onCompare, onSupersede, onLinkProject, onCreateTemplate, onOpenEvidence }) {
  return (
    <Panel label="Knowledge" title="Knowledge capture" description="Approved knowledge, templates, evidence, and superseded versions." >
      {renderPairList(model?.knowledge)}
      <div className="ai-panel-actions compact">
        <button type="button" className="toolbar-chip" onClick={onView}>View</button>
        <button type="button" className="toolbar-chip" onClick={onPublish}>Publish</button>
        <button type="button" className="toolbar-chip" onClick={onCompare}>Compare</button>
        <button type="button" className="toolbar-chip" onClick={onSupersede}>Supersede</button>
        <button type="button" className="toolbar-chip" onClick={onLinkProject}>Link to project</button>
        <button type="button" className="toolbar-chip" onClick={onCreateTemplate}>Create template</button>
        <button type="button" className="toolbar-chip" onClick={onOpenEvidence}>Open evidence</button>
      </div>
    </Panel>
  );
}

export function WorkspaceContextPanel({ model }) {
  return (
    <Panel label="Context" title="Workspace context" description="Identity, project, tenant, artifacts, policies, and approvals." >
      <div className="ai-detail-list">
        {[
          ["Organization", model?.organizationLabel],
          ["Tenant", model?.tenantLabel],
          ["Customer", model?.context?.customer || "Unknown"],
          ["Project", model?.context?.project || model?.request?.title || "Unknown"],
          ["Workspace", model?.workspaceLabel],
          ["Environment", model?.environment],
          ["Repository", model?.context?.repository || "Not connected"],
          ["Branch", model?.context?.branch || "Not connected"],
          ["Commit", model?.context?.commit || "Not connected"],
          ["Current route", model?.breadcrumb || "Not connected"],
          ["Lifecycle state", model?.request?.state],
          ["Active artifact", model?.context?.activeArtifact || "Not connected"],
          ["Knowledge count", listify(model?.knowledge).length],
          ["Memory count", listify(model?.conversations).length],
          ["Policies", listify(model?.policies).length],
          ["Standards", listify(model?.standards).length],
          ["Risk level", model?.context?.riskLevel || "Not assessed"],
          ["Pending approvals", listify(model?.approvals).length],
        ].map(([label, value]) => (
          <div className="ai-list-row" key={label}>
            <strong>{label}</strong>
            <span>{asText(value)}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

export function AISuggestionsPanel({ model, onChooseSuggestion }) {
  return (
    <Panel label="Suggestions" title="AI suggestions" description="Role-aware and context-aware prompts." >
      <div className="chip-cloud">
        {listify(model?.suggestions).length ? model.suggestions.map((suggestion, index) => {
          const text = typeof suggestion === "string" ? suggestion : suggestion.label || suggestion.title || `Suggestion ${index + 1}`;
          return (
            <button type="button" key={`${text}-${index}`} className="context-chip" onClick={() => onChooseSuggestion?.(text)}>
              {text}
            </button>
          );
        }) : <EmptyPanel title="Not connected" message="No role-aware suggestions are available yet." />}
      </div>
    </Panel>
  );
}

export function UniversalAIWorkspace({
  model,
  requestValue,
  onRequestChange,
  attachments,
  onAttachmentUpload,
  onRemoveAttachment,
  selectedMode,
  onModeChange,
  selectedAgents,
  onToggleAgent,
  selectedContextSources,
  onToggleContextSource,
  selectedProjectArtifact,
  selectedIncident,
  selectedRequirement,
  selectedToolContext,
  onAction = {},
  onChooseSuggestion,
  timelineFilters = {},
  onTimelineFilterChange,
}) {
  const liveModel = model || buildUniversalAIWorkspaceModel();
  return (
    <section className="ai-workspace" aria-label="Universal AI workspace">
      <header className="ai-workspace-header">
        <div>
          <p className="section-label">AI-native workspace</p>
          <h2>{liveModel.title}</h2>
          <p className="studio-note">{liveModel.breadcrumb}</p>
        </div>
        <div className="ai-header-badges">
          {badge({ label: "User", value: liveModel.userLabel })}
          {badge({ label: "Project", value: liveModel.context?.project || liveModel.request?.title || "Not connected" })}
          {badge({ label: "Workspace", value: liveModel.workspaceLabel })}
          {badge({ label: "Status", value: liveModel.statusLabel, tone: liveModel.connection.connected ? "success" : "warning" })}
          {badge({ label: "State", value: DEFAULT_STATE_LABELS[liveModel.request.state] || liveModel.request.state, tone: statusTone(liveModel.request.state) })}
        </div>
      </header>

      {!liveModel.connection.connected ? (
        <div className="ai-banner" role="status">
          Backend AI capability not connected. Read-only context, local drafts, and governed navigation remain available.
        </div>
      ) : null}

      <div className="ai-workspace-grid">
        <div className="ai-rail left">
          <Panel label="Conversations" title="Conversation history" description="Conversation list, saved prompts, shared conversations, and recent requests.">
            <div className="ai-list">
              {(liveModel.conversations || []).slice(0, 6).map((conversation) => (
                <button type="button" className="ai-list-button" key={conversation.id}>
                  <strong>{conversation.title}</strong>
                  <span>{conversation.project || "No project"} · {conversation.status}</span>
                </button>
              ))}
              {!liveModel.conversations?.length ? <EmptyPanel title="No conversations" message="No conversation history was returned for this workspace." /> : null}
            </div>
          </Panel>
          <Panel label="Saved prompts" title="Prompt library" description="Approved prompts and reusable request patterns.">
            {renderPairList(liveModel.savedPrompts)}
          </Panel>
          <Panel label="Solutions" title="Approved solutions" description="Approved solution objects and shared conversations.">
            {renderPairList(liveModel.approvedSolutions.length ? liveModel.approvedSolutions : liveModel.sharedConversations)}
          </Panel>
        </div>

        <div className="ai-main">
          <Panel
            label="Conversation"
            title={liveModel.request.title}
            description={liveModel.request.summary || "Live request transcript and generated output."}
            actions={
              <div className="chip-cloud">
                {badge({ label: "Lifecycle", value: DEFAULT_STATE_LABELS[liveModel.request.state] || liveModel.request.state, tone: statusTone(liveModel.request.state) })}
                {badge({ label: "Approval", value: liveModel.request.approvalsState || "NOT_REQUIRED" })}
                {badge({ label: "Execution", value: liveModel.executionState || "IDLE" })}
                {badge({ label: "Knowledge", value: liveModel.knowledgeState || "DRAFT" })}
              </div>
            }
          >
            <div className="ai-transcript">
              <article className="ai-message user">
                <strong>User request</strong>
                <p>{liveModel.request.prompt || "No request submitted yet."}</p>
              </article>
              <article className="ai-message ai">
                <strong>NovaAI response</strong>
                <p>{liveModel.request.outcome || liveModel.request.summary || "No backend AI response is connected yet."}</p>
              </article>
              <article className="ai-message ai">
                <strong>Structured plan</strong>
                <p>{liveModel.context?.planSummary || "Not connected."}</p>
              </article>
            </div>
          </Panel>

          <div className="ai-secondary-grid">
            <ArtifactExplorer
              model={liveModel}
              onOpen={onAction.openArtifact}
              onCompare={onAction.compareArtifact}
              onReview={onAction.reviewArtifact}
              onComment={onAction.commentArtifact}
              onRequestChanges={onAction.requestChangesArtifact}
              onApprove={onAction.approveArtifact}
              onReject={onAction.rejectArtifact}
              onRegenerate={onAction.regenerateArtifact}
              onExport={onAction.exportArtifact}
              onOpenSpecialized={onAction.openSpecializedTool}
            />
            <SolutionReviewWorkspace
              model={liveModel}
              sections={["requirements", "architecture", "ui/ux", "backend", "frontend", "database", "tests", "security", "deployment", "documentation"]}
              onApprove={onAction.approveReview}
              onReject={onAction.rejectReview}
              onRequestChanges={onAction.requestReviewChanges}
              onEditDirectly={onAction.editReview}
              onAskFollowUp={onAction.askFollowUp}
              onSendToReviewer={onAction.sendToReviewer}
              onCompareVersion={onAction.compareReviewVersion}
              onOpenEvidence={onAction.openEvidence}
            />
            <ApprovalWorkspace
              model={liveModel}
              onApprove={onAction.approve}
              onReject={onAction.reject}
              onRequestChanges={onAction.requestChanges}
              onDelegate={onAction.delegate}
              onOpenArtifact={onAction.openRelatedArtifact}
              onOpenPolicy={onAction.openPolicy}
              onOpenEvidence={onAction.openEvidence}
            />
            <ExecutionMonitor
              model={liveModel}
              onPause={onAction.pauseExecution}
              onResume={onAction.resumeExecution}
              onCancel={onAction.cancelExecution}
              onRetryFailedStep={onAction.retryFailedStep}
              onOpenLogs={onAction.openLogs}
              onOpenTraces={onAction.openTraces}
              onOpenEvidence={onAction.openEvidence}
              onRollback={onAction.rollbackExecution}
            />
            <KnowledgeCapturePanel
              model={liveModel}
              onView={onAction.viewKnowledge}
              onPublish={onAction.publishKnowledge}
              onCompare={onAction.compareKnowledge}
              onSupersede={onAction.supersedeKnowledge}
              onLinkProject={onAction.linkKnowledgeToProject}
              onCreateTemplate={onAction.createTemplate}
              onOpenEvidence={onAction.openEvidence}
            />
          </div>
        </div>

        <div className="ai-rail right">
          <AIUnderstandingPanel
            model={liveModel}
            onConfirmInterpretation={onAction.confirmInterpretation}
            onCorrectInterpretation={onAction.correctInterpretation}
            onAddContext={onAction.addContext}
            onRequestClarification={onAction.requestClarification}
            onRegeneratePlan={onAction.regeneratePlan}
          />
          <WorkspaceContextPanel model={liveModel} />
          <AgentCollaborationPanel
            model={liveModel}
            onInspectWork={onAction.inspectAgentWork}
            onPause={onAction.pauseAgent}
            onCancel={onAction.cancelAgent}
            onRetry={onAction.retryAgent}
            onReassign={onAction.reassignAgent}
            onRequestReview={onAction.requestAgentReview}
            onOpenOutput={onAction.openAgentOutput}
            onOpenEvidence={onAction.openAgentEvidence}
          />
          <AISuggestionsPanel model={liveModel} onChooseSuggestion={onChooseSuggestion} />
          <ExecutionTimeline
            model={liveModel}
            filters={timelineFilters}
            onFilterChange={onTimelineFilterChange}
          />
        </div>
      </div>

      <div className="ai-composer-wrap">
        <AIRequestComposer
          model={liveModel}
          value={requestValue}
          onChange={onRequestChange}
          attachments={attachments}
          onAttachmentUpload={onAttachmentUpload}
          onRemoveAttachment={onRemoveAttachment}
          selectedMode={selectedMode}
          onModeChange={onModeChange}
          selectedAgents={selectedAgents}
          onToggleAgent={onToggleAgent}
          selectedContextSources={selectedContextSources}
          onToggleContextSource={onToggleContextSource}
          selectedProjectArtifact={selectedProjectArtifact}
          selectedIncident={selectedIncident}
          selectedRequirement={selectedRequirement}
          selectedToolContext={selectedToolContext}
          onAction={onAction}
          highRisk={String(liveModel.context?.riskLevel || "").toLowerCase() === "high" || String(liveModel.context?.riskLevel || "").toLowerCase() === "critical"}
        />
      </div>
    </section>
  );
}
