const ROLE_WORKSPACE_SURFACES = [
  { id: "dashboard", label: "Role Dashboard", anchorId: "role-dashboard-window" },
  { id: "operations", label: "Operations Layer", anchorId: "role-operations-window" },
  { id: "studio", label: "AI Studio", anchorId: "role-ai-studio-window" },
  { id: "chat", label: "Governed Chat Workspace", anchorId: "role-chat-window" },
];

function toCountLabel(value, fallback = "0") {
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  return fallback;
}

function clampList(values, limit = 4) {
  return Array.isArray(values) ? values.slice(0, limit) : [];
}

function asPairList(items) {
  if (Array.isArray(items)) {
    return items
      .map((item) => {
        if (Array.isArray(item) && item.length >= 2) {
          return {
            label: String(item[0]),
            value: String(item[1]),
          };
        }
        if (item && typeof item === "object") {
          const label = item.label ?? item.name ?? item.title ?? item.id ?? "";
          const value = item.value ?? item.detail ?? item.status ?? item.count ?? "";
          if (label || value) {
            return {
              label: String(label),
              value: String(value),
            };
          }
        }
        return null;
      })
      .filter(Boolean);
  }
  if (items && typeof items === "object") {
    return Object.entries(items).map(([label, value]) => ({
      label: String(label),
      value: String(value),
    }));
  }
  return [];
}

export function buildRoleWorkspaceModel({
  activeRole,
  runtime,
  platformSummary,
  environment,
  activeTenant,
  activeProject,
  activeRequest,
  activeStage,
  workflowProgress,
  authDisplayName,
  authDisplayRoleLabel,
  selectedModeLabel,
  requestSummary,
  suggestedTitle,
}) {
  const healthScore = platformSummary?.platform_health === "healthy" ? "Healthy" : "Degraded";
  const commandSnapshot = runtime?.commandCenterSnapshots?.[0] ?? null;
  const latestApprovalRoute = runtime?.approvalRoutes?.[0] ?? null;
  const latestEvidenceBundle = runtime?.evidenceBundles?.[0] ?? null;
  const latestRiskItem = runtime?.riskRegister?.[0] ?? null;
  const activeSignals = asPairList(activeRole?.signals).slice(0, 4);
  const roleMetrics = asPairList(activeRole?.metrics);
  const quickActions = clampList(activeRole?.actions, 4);
  const operationalActions = [
    "Execute",
    "Escalate",
    "Pause",
    "Approve",
    "Investigate",
    "Open AI Studio",
  ];
  const studioModes = ["Code", "Document", "Architecture", "Data", "Workflow", "Agent", "Research", "Review", "Simulation"];
  const chatLifecycle = [
    "Ask",
    "Generate",
    "Review",
    "Approve",
    "Execute",
    "Verify",
    "Capture Evidence",
    "Learn",
  ];

  return {
    headerTitle: `${activeRole?.label || "Role"} operating environment`,
    headerSummary: `${authDisplayName} is operating in ${environment} with ${activeRole?.domain || "enterprise"} context and governed access.`,
    windows: [
      {
        id: "dashboard",
        anchorId: ROLE_WORKSPACE_SURFACES[0].anchorId,
        label: ROLE_WORKSPACE_SURFACES[0].label,
        status: healthScore,
        title: `${activeRole?.label || "Role"} dashboard`,
        summary: `Personalized home and decision surface for ${activeRole?.domain || "the active role"}.`,
        metrics: [
          ...roleMetrics.slice(0, 4),
          ["Environment", environment],
          ["Workspace", activeProject?.name || "NovaTech"],
          ["Tenant", activeTenant?.name || "NovaTech"],
          ["Session", authDisplayRoleLabel],
        ],
        highlights: [
          `Attention queue: ${quickActions[0] || "No open work"}`,
          `Active work: ${activeRequest?.title || suggestedTitle || "Ready for a new request"}`,
          `Workflow status: ${activeRequest?.status || "draft"} / ${workflowProgress || 0}%`,
          `Top signal: ${activeSignals[0]?.[0] ? `${activeSignals[0][0]} ${activeSignals[0][1]}` : "No active signal"}`,
        ],
        lists: [
          {
            label: "Pending approvals",
            rows: clampList(runtime?.approvalRoutes, 3).map((route) => ({
              title: route.subject,
              detail: `${route.policyId} · ${route.required?.join(", ") || "Review required"}`,
            })),
          },
          {
            label: "Recent activity",
            rows: clampList(runtime?.auditTrail, 3).map((entry) => ({
              title: entry.action,
              detail: `${entry.service} · ${entry.at}`,
            })),
          },
        ],
        actions: [
          { label: "Ask NovaAI", command: "Ask NovaAI" },
          { label: "Open Operations", command: "Open Operations" },
          { label: "Open AI Studio", command: "Open AI Studio" },
          { label: "Open Chat Workspace", command: "Open Chat Workspace" },
        ],
      },
      {
        id: "operations",
        anchorId: ROLE_WORKSPACE_SURFACES[1].anchorId,
        label: ROLE_WORKSPACE_SURFACES[1].label,
        status: commandSnapshot?.enterpriseHealth || "Live",
        title: `${activeRole?.label || "Role"} operations layer`,
        summary: `Real-time command, control, monitoring, and execution surface for ${activeRole?.domain || "the active role"}.`,
        metrics: [
          ["Health", commandSnapshot?.enterpriseHealth || healthScore],
          ["Trust", commandSnapshot?.trustScore || "Stable"],
          ["Risk", commandSnapshot?.riskScore || "Managed"],
          ["Controls", toCountLabel(runtime?.approvalRoutes?.length, "0")],
          ["Evidence", toCountLabel(runtime?.evidenceBundles?.length, "0")],
          [
            "Incidents",
            toCountLabel(runtime?.solutionRequests?.filter((request) => request.status !== "operating")?.length, "0"),
          ],
        ],
        highlights: [
          commandSnapshot?.summary || "Live operational signals are synchronized with the command center.",
          latestRiskItem ? `${latestRiskItem.title} · ${latestRiskItem.score}` : "No critical risk escalation detected.",
          latestApprovalRoute ? `${latestApprovalRoute.subject} · ${latestApprovalRoute.policyId}` : "No blocked approval path.",
          `Environment: ${environment} · Workspace: ${activeTenant?.name || "NovaTech"}`,
        ],
        lists: [
          {
            label: "Operational controls",
            rows: operationalActions.map((action) => ({
              title: action,
              detail: "Role-scoped action",
            })),
          },
          {
            label: "Live signals",
            rows: activeSignals.map(({ label, value }) => ({
              title: label,
              detail: value,
            })),
          },
        ],
        actions: operationalActions.map((label) => ({ label, command: label })),
      },
      {
        id: "studio",
        anchorId: ROLE_WORKSPACE_SURFACES[2].anchorId,
        label: ROLE_WORKSPACE_SURFACES[2].label,
        status: "Ready",
        title: `${activeRole?.label || "Role"} AI studio`,
        summary: "Code, documents, models, agents, workflows, files, tests, and architecture live in one governed creation surface.",
        metrics: [
          ["Modes", studioModes.length],
          ["Agents", toCountLabel(activeRole?.agents?.length, "0")],
          ["Knowledge", toCountLabel(runtime?.knowledgeGraph?.length, "0")],
          ["Workflows", toCountLabel(runtime?.solutionRequests?.length, "0")],
          ["Actions", toCountLabel(quickActions.length, "0")],
          ["Artifacts", toCountLabel(runtime?.automationRuns?.length, "0")],
        ],
        highlights: [
          `Selected mode: ${selectedModeLabel || "Full solution"}`,
          `Current project: ${activeProject?.name || suggestedTitle || "NovaCodePro solution"}`,
          `Environment: ${environment}`,
          `Role tools: ${clampList(activeRole?.agents, 4).join(", ") || "No agents assigned"}`,
        ],
        lists: [
          {
            label: "Studio modes",
            rows: studioModes.map((mode) => ({ title: mode, detail: "Supported" })),
          },
          {
            label: "Agent roster",
            rows: clampList(activeRole?.agents, 4).map((agent) => ({ title: agent, detail: "Assigned to this role" })),
          },
        ],
        actions: [
          { label: "Open Studio", command: "Open AI Studio" },
          { label: "Generate", command: "Generate" },
          { label: "Review", command: "Review" },
          { label: "Simulation", command: "Simulation" },
        ],
      },
      {
        id: "chat",
        anchorId: ROLE_WORKSPACE_SURFACES[3].anchorId,
        label: ROLE_WORKSPACE_SURFACES[3].label,
        status: "Governed",
        title: `${activeRole?.label || "Role"} governed chat`,
        summary: "Conversation, request composition, solution generation, review, approval, execution, and evidence capture.",
        metrics: [
          ["Request", activeRequest?.status || "draft"],
          ["Progress", `${workflowProgress || 0}%`],
          ["Approvals", toCountLabel(runtime?.approvalRoutes?.length, "0")],
          ["Evidence", toCountLabel(runtime?.evidenceBundles?.length, "0")],
          ["Stage", activeStage?.label || "Intent analysis"],
          ["Knowledge", toCountLabel(runtime?.knowledgeGraph?.length, "0")],
        ],
        highlights: [
          requestSummary || "Ask NovaCodePro to build, analyse, fix, test, secure, or deploy.",
          `Proposed title: ${suggestedTitle || "NovaCodePro solution request"}`,
          latestEvidenceBundle ? `Latest evidence: ${latestEvidenceBundle.summary}` : "Evidence capture will appear after approval.",
          "Conversation is governed by policy, approvals, and evidence.",
        ],
        lists: [
          {
            label: "Request lifecycle",
            rows: chatLifecycle.map((step) => ({ title: step, detail: "Governed stage" })),
          },
          {
            label: "Approval trail",
            rows: clampList(runtime?.approvalRoutes, 3).map((route) => ({
              title: route.subject,
              detail: `${route.policyId} · ${route.required?.join(", ") || "Approval required"}`,
            })),
          },
        ],
        actions: [
          { label: "Ask NovaCodePro", command: "Ask NovaCodePro" },
          { label: "Generate Solution", command: "Generate Solution" },
          { label: "Request Review", command: "Request Review" },
          { label: "Open Composer", command: "Open Composer" },
        ],
      },
    ],
  };
}
