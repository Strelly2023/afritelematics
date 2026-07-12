import {
  AGENT_MARKETPLACE,
  AUTOMATION_TEMPLATES,
  COLLABORATION_THREADS,
  DEVELOPER_SURFACES,
  INTEGRATIONS,
  KNOWLEDGE_GRAPH,
  PLATFORM_CENTERS,
  PROJECTS,
  SERVICE_CATALOG,
  SOLUTION_TEMPLATES,
  TENANTS,
  WORKFLOW_SEQUENCE,
  WORKFLOW_STAGES,
} from "./catalog.js";

const STORAGE_KEY = "novacodepro.platform.runtime.v1";

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function nowIso() {
  return new Date().toISOString();
}

function createAuditEvent({ actor, action, service, subject, evidence, detail }) {
  return {
    id: `audit-${Math.random().toString(36).slice(2, 10)}`,
    at: nowIso(),
    actor,
    action,
    service,
    subject,
    evidence,
    detail,
  };
}

function buildStageState(stage, index, activeIndex = 0) {
  const status = index < activeIndex ? "completed" : index === activeIndex ? "in_progress" : "pending";
  return {
    ...stage,
    status,
    evidence: status === "completed" ? [stage.output, stage.api] : [],
    approvals: stage.kind === "human" ? [] : undefined,
  };
}

function templateFromRequest(requestText) {
  const normalized = requestText.toLowerCase();
  return (
    SOLUTION_TEMPLATES.find((template) => normalized.includes(template.domain)) ??
    SOLUTION_TEMPLATES[0]
  );
}

function createRequest(payload) {
  const template = payload.template ?? templateFromRequest(payload.request);
  const createdAt = nowIso();
  const workflow = WORKFLOW_STAGES.map((stage, index) => buildStageState(stage, index, 0));
  workflow[0].status = "in_progress";

  return {
    id: `req-${Math.random().toString(36).slice(2, 10)}`,
    title: payload.title || template.title,
    request: payload.request || template.request,
    domain: payload.domain || template.domain,
    industry: payload.industry || template.domain,
    country: payload.country || "Australia",
    budget: payload.budget || "$0",
    timeline: payload.timeline || "TBD",
    stakeholders: payload.stakeholders || "",
    region: payload.region || "Australia",
    compliance: payload.compliance || "enterprise",
    surfaces: payload.surfaces?.length ? payload.surfaces : template.surfaces,
    templateId: template.id,
    stageIndex: 0,
    status: "active",
    createdAt,
    updatedAt: createdAt,
    approvals: [],
    artifacts: [
      {
        id: `art-${Math.random().toString(36).slice(2, 10)}`,
        kind: "intent-brief",
        title: "Intent brief",
        stage: "Intent Analysis",
        createdAt,
      },
    ],
    workflow,
    evidenceTrail: [],
  };
}

function seedState() {
  const first = createRequest({
    title: "Ride-hailing platform for Melbourne",
    request: "Build a ride-hailing platform for Melbourne.",
    domain: "mobility",
    region: "Australia",
    surfaces: ["Rider app", "Driver app", "Operations dashboard", "Admin portal"],
    compliance: "high",
    template: SOLUTION_TEMPLATES[0],
  });

  return {
    activeRoleId: "platform-admin",
    environment: "Production",
    selectedWorkspace: "Solution Studio",
    selectedRequestId: first.id,
    activeTenantId: TENANTS[0].id,
    activeProjectId: PROJECTS[0].id,
    activeThreadId: COLLABORATION_THREADS[0].id,
    selectedKnowledgeNodeId: KNOWLEDGE_GRAPH[0].id,
    search: "",
    installedAgents: ["banking-agent", "healthcare-agent", "ride-hailing-agent"],
    connectedIntegrations: INTEGRATIONS.filter((integration) => integration.status === "connected").map(
      (integration) => integration.id,
    ),
    tenants: TENANTS,
    projects: PROJECTS,
    collaborationThreads: COLLABORATION_THREADS.map((thread, index) => ({
      ...thread,
      messages: [
        {
          id: `msg-${index + 1}`,
          author: "NovaCodePro",
          body: thread.message,
          at: createdAtMinus(index + 10),
        },
      ],
    })),
    knowledgeGraph: KNOWLEDGE_GRAPH,
    automationRuns: [],
    solutionRequests: [
      first,
      {
        ...createRequest({
          title: "Healthcare management system",
          request: "Build a hospital management system.",
          domain: "healthcare",
          region: "Australia",
          compliance: "very high",
          template: SOLUTION_TEMPLATES[1],
        }),
        stageIndex: 4,
        status: "review",
        workflow: WORKFLOW_STAGES.map((stage, index) => buildStageState(stage, index, 4)),
        approvals: [
          {
            id: "approval-architecture",
            gate: "Architecture Approval",
            by: "NovaTech Governance",
            at: createdAtMinus(1),
            evidence: "Architecture approved after controlled review.",
          },
        ],
        artifacts: [
          {
            id: "art-business",
            kind: "requirements",
            title: "Business requirements",
            stage: "Business Analysis",
            createdAt: createdAtMinus(2),
          },
          {
            id: "art-architecture",
            kind: "architecture",
            title: "Approved architecture",
            stage: "Architecture Approval",
            createdAt: createdAtMinus(1),
          },
        ],
      },
    ],
    auditTrail: [
      createAuditEvent({
        actor: "NovaID",
        action: "solution.request.created",
        service: "Solution Orchestrator Engine",
        subject: "Ride-hailing platform for Melbourne",
        evidence: "Intent brief stored in local solution repository.",
        detail: "Seeded solution request for enterprise demo.",
      }),
      createAuditEvent({
        actor: "NovaID",
        action: "solution.architecture.approved",
        service: "Human Review & Governance Engine",
        subject: "Healthcare management system",
        evidence: "Architecture approval recorded with governance evidence.",
        detail: "Seeded workflow at architecture approval gate.",
      }),
    ],
    commandHistory: [],
    developerSurfaces: DEVELOPER_SURFACES,
  };
}

function createdAtMinus(minutes) {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

function loadState() {
  const base = seedState();
  if (typeof localStorage === "undefined") {
    return base;
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return base;
    }
    const parsed = JSON.parse(raw);
    return {
      ...base,
      ...parsed,
      solutionRequests: parsed.solutionRequests ?? base.solutionRequests,
      auditTrail: parsed.auditTrail ?? base.auditTrail,
      commandHistory: parsed.commandHistory ?? base.commandHistory,
      tenants: parsed.tenants ?? base.tenants,
      projects: parsed.projects ?? base.projects,
      collaborationThreads: parsed.collaborationThreads ?? base.collaborationThreads,
      knowledgeGraph: parsed.knowledgeGraph ?? base.knowledgeGraph,
      automationRuns: parsed.automationRuns ?? base.automationRuns,
      connectedIntegrations: parsed.connectedIntegrations ?? base.connectedIntegrations,
      installedAgents: parsed.installedAgents ?? base.installedAgents,
      developerSurfaces: parsed.developerSurfaces ?? base.developerSurfaces,
    };
  } catch {
    return base;
  }
}

function saveState(state) {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function nextWorkflowIndex(request) {
  const current = request.stageIndex;
  return Math.min(current + 1, WORKFLOW_SEQUENCE.length - 1);
}

function withUpdatedRequest(state, requestId, updater) {
  const solutionRequests = state.solutionRequests.map((request) =>
    request.id === requestId ? updater(request) : request,
  );
  const selectedRequestId = state.selectedRequestId || requestId;
  return { ...state, solutionRequests, selectedRequestId };
}

function createRuntime() {
  let state = loadState();
  const listeners = new Set();

  function emit(event) {
    if (event) {
      state = {
        ...state,
        auditTrail: [event, ...state.auditTrail].slice(0, 200),
      };
    }
    saveState(state);
    listeners.forEach((listener) => listener());
  }

  function appendAudit(payload) {
    return createAuditEvent(payload);
  }

  function setState(nextState) {
    state = nextState;
    saveState(state);
    listeners.forEach((listener) => listener());
  }

function createSolution(payload) {
    const request = createRequest(payload);
    const event = appendAudit({
      actor: "NovaID",
      action: "solution.request.created",
      service: "Solution Orchestrator Engine",
      subject: request.title,
      evidence: request.request,
      detail: "Solution request entered through Solution Studio.",
    });
    setState({
      ...state,
      solutionRequests: [request, ...state.solutionRequests],
      selectedRequestId: request.id,
      commandHistory: [request.request, ...state.commandHistory].slice(0, 30),
    });
    emit(event);
    return request;
  }

  function selectRequest(requestId) {
    setState({
      ...state,
      selectedRequestId: requestId,
    });
  }

  function switchTenant(tenantId) {
    const tenantProjects = state.projects.filter((project) => project.tenantId === tenantId);
    setState({
      ...state,
      activeTenantId: tenantId,
      activeProjectId: tenantProjects[0]?.id ?? state.activeProjectId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workspace.tenant.switched",
        service: "Tenant Manager",
        subject: tenantId,
        evidence: `Tenant switched to ${tenantId}.`,
        detail: "Workspace context updated for the selected tenant.",
      }),
    );
  }

  function selectProject(projectId) {
    setState({
      ...state,
      activeProjectId: projectId,
    });
    const project = state.projects.find((item) => item.id === projectId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "project.selected",
        service: "Project Workspace",
        subject: project?.name || projectId,
        evidence: project?.solution || "Project selected from workspace catalog.",
        detail: "Project context activated in NovaCodePro.",
      }),
    );
  }

  function switchRole(roleId) {
    setState({
      ...state,
      activeRoleId: roleId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workspace.role.switched",
        service: "Identity & Access",
        subject: roleId,
        evidence: `Role set to ${roleId}.`,
        detail: "Role-aware workspace assembly updated.",
      }),
    );
  }

  function setEnvironment(environment) {
    setState({
      ...state,
      environment,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workspace.environment.switched",
        service: "Environment Control",
        subject: environment,
        evidence: `Environment switched to ${environment}.`,
        detail: "Runtime context updated.",
      }),
    );
  }

  function installAgent(agentId) {
    if (state.installedAgents.includes(agentId)) {
      return;
    }
    setState({
      ...state,
      installedAgents: [agentId, ...state.installedAgents],
    });
    const agent = AGENT_MARKETPLACE.find((item) => item.id === agentId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "agent.installed",
        service: "Plugin Marketplace",
        subject: agent?.title || agentId,
        evidence: agent?.api || "No API metadata",
        detail: "Agent enabled in the active enterprise workspace.",
      }),
    );
  }

  function installIntegration(integrationId) {
    if (state.connectedIntegrations.includes(integrationId)) {
      return;
    }
    const integration = INTEGRATIONS.find((item) => item.id === integrationId);
    setState({
      ...state,
      connectedIntegrations: [integrationId, ...state.connectedIntegrations],
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "integration.connected",
        service: "Integration Hub",
        subject: integration?.name || integrationId,
        evidence: integration?.purpose || "Integration enabled.",
        detail: "External service connected to the enterprise platform.",
      }),
    );
  }

  function createProject(payload) {
    const project = {
      id: `project-${Math.random().toString(36).slice(2, 10)}`,
      name: payload.name,
      tenantId: payload.tenantId || state.activeTenantId,
      status: payload.status || "Discovery",
      owner: payload.owner || "NovaCodePro",
      solution: payload.solution || "Generated solution",
      region: payload.region || "Australia",
      budget: payload.budget || "$0",
    };
    setState({
      ...state,
      projects: [project, ...state.projects],
      activeProjectId: project.id,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "project.created",
        service: "Project Workspace",
        subject: project.name,
        evidence: project.solution,
        detail: "Project created through NovaCodePro governance flow.",
      }),
    );
  }

  function postComment(threadId, body) {
    const thread = state.collaborationThreads.find((item) => item.id === threadId);
    if (!thread) {
      return;
    }
    const updatedThread = {
      ...thread,
      messages: [
        {
          id: `msg-${Math.random().toString(36).slice(2, 10)}`,
          author: "NovaCodePro",
          body,
          at: nowIso(),
        },
        ...thread.messages,
      ],
      state: "active",
    };
    setState({
      ...state,
      activeThreadId: threadId,
      collaborationThreads: state.collaborationThreads.map((item) =>
        item.id === threadId ? updatedThread : item,
      ),
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "collaboration.comment.posted",
        service: "Collaboration Service",
        subject: thread.scope,
        evidence: body,
        detail: "Collaborative note captured and synchronized with the workspace.",
      }),
    );
  }

  function focusKnowledgeNode(nodeId) {
    setState({
      ...state,
      selectedKnowledgeNodeId: nodeId,
    });
    const node = state.knowledgeGraph.find((item) => item.id === nodeId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "knowledge.graph.focused",
        service: "Knowledge Graph",
        subject: node?.label || nodeId,
        evidence: node?.links?.join(", ") || "Knowledge node focused.",
        detail: "Enterprise knowledge graph inspected from the workspace.",
      }),
    );
  }

  function runAutomationTemplate(templateId) {
    const template = AUTOMATION_TEMPLATES.find((item) => item.id === templateId);
    if (!template) {
      return;
    }
    const run = {
      id: `run-${Math.random().toString(36).slice(2, 10)}`,
      templateId: template.id,
      title: template.title,
      stages: template.stages,
      status: "queued",
      createdAt: nowIso(),
    };
    setState({
      ...state,
      automationRuns: [run, ...state.automationRuns],
      commandHistory: [template.title, ...state.commandHistory].slice(0, 30),
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "automation.template.run",
        service: "Workflow Engine",
        subject: template.title,
        evidence: template.stages.join(" → "),
        detail: "Reusable automation template started from the enterprise workspace.",
      }),
    );
  }

  function advanceWorkflow(requestId) {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    if (!currentStage) {
      return;
    }
    if (currentStage.kind === "human") {
      emit(
        appendAudit({
          actor: "NovaID",
          action: `${currentStage.id}.waiting-approval`,
          service: currentStage.service,
          subject: request.title,
          evidence: currentStage.output,
          detail: "Human approval gate is required before this request can advance.",
        }),
      );
      return;
    }

    const nextIndex = nextWorkflowIndex(request);
    const nextStage = request.workflow[nextIndex];

    const updatedRequest = {
      ...request,
      stageIndex: nextIndex,
      updatedAt: nowIso(),
      status: nextStage?.kind === "human" ? "waiting-approval" : nextIndex === WORKFLOW_SEQUENCE.length - 1 ? "operating" : "active",
      workflow: request.workflow.map((stage, index) =>
        index < nextIndex
          ? { ...stage, status: "completed" }
          : index === nextIndex
            ? { ...stage, status: nextStage?.kind === "human" ? "waiting-approval" : "in_progress" }
            : { ...stage, status: "pending" },
      ),
      artifacts: [
        ...request.artifacts,
        {
          id: `art-${Math.random().toString(36).slice(2, 10)}`,
          kind: currentStage.output,
          title: currentStage.output,
          stage: currentStage.label,
          createdAt: nowIso(),
        },
      ],
    };

    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });

    emit(
      appendAudit({
        actor: "Solution Engine",
        action: `${currentStage.id}.completed`,
        service: currentStage.service,
        subject: request.title,
        evidence: currentStage.output,
        detail: `Workflow advanced to ${nextStage ? nextStage.label : "complete"}.`,
      }),
    );
  }

  function approveGate(requestId, note = "Approved by governance.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    if (!currentStage || currentStage.kind !== "human") {
      return;
    }

    const nextIndex = nextWorkflowIndex(request);
    const nextStage = request.workflow[nextIndex];
    const updatedWorkflow = request.workflow.map((stage, index) =>
      index < request.stageIndex
        ? { ...stage, status: "completed" }
        : index === request.stageIndex
          ? { ...stage, status: "completed" }
          : index === nextIndex
            ? { ...stage, status: nextStage?.kind === "human" ? "waiting-approval" : "in_progress" }
            : { ...stage, status: "pending" },
    );

    const updatedRequest = {
      ...request,
      stageIndex: nextIndex,
      updatedAt: nowIso(),
      status: nextIndex === WORKFLOW_SEQUENCE.length - 1 ? "operating" : "active",
      approvals: [
        ...request.approvals,
        {
          id: `approval-${Math.random().toString(36).slice(2, 10)}`,
          gate: currentStage.label,
          by: "NovaTech Governance",
          at: nowIso(),
          evidence: note,
        },
      ],
      workflow: updatedWorkflow,
      artifacts: [
        ...request.artifacts,
        {
          id: `art-${Math.random().toString(36).slice(2, 10)}`,
          kind: "approval",
          title: `${currentStage.label} approved`,
          stage: currentStage.label,
          createdAt: nowIso(),
        },
      ],
    };

    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });

    emit(
      appendAudit({
        actor: "NovaTech Governance",
        action: `${currentStage.id}.approved`,
        service: currentStage.service,
        subject: request.title,
        evidence: note,
        detail: `Human gate approved and workflow advanced to ${nextStage ? nextStage.label : "complete"}.`,
      }),
    );
  }

  function pauseWorkflow(requestId, note = "Paused by operator.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const updatedRequest = {
      ...request,
      status: "paused",
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex ? { ...stage, status: "paused" } : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "paused",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workflow.paused",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function resumeWorkflow(requestId, note = "Resumed by operator.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const activeStatus = currentStage?.kind === "human" ? "waiting-approval" : "active";
    const updatedRequest = {
      ...request,
      status: activeStatus,
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex
          ? { ...stage, status: currentStage?.kind === "human" ? "waiting-approval" : "in_progress" }
          : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "resumed",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workflow.resumed",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function retryWorkflow(requestId, note = "Retry requested by operator.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const updatedRequest = {
      ...request,
      status: currentStage?.kind === "human" ? "waiting-approval" : "active",
      retries: (request.retries || 0) + 1,
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex
          ? { ...stage, status: currentStage?.kind === "human" ? "waiting-approval" : "in_progress" }
          : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "retried",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workflow.retried",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function rejectWorkflow(requestId, note = "Rejected by governance.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const updatedRequest = {
      ...request,
      status: "rejected",
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex ? { ...stage, status: "rejected" } : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "rejected",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaTech Governance",
        action: "workflow.rejected",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function attachArtifact(requestId, artifact) {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const nextRequest = {
      ...request,
      artifacts: [artifact, ...request.artifacts],
      updatedAt: nowIso(),
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? nextRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: "artifact.archived",
        service: "Artifact Repository",
        subject: artifact.title,
        evidence: artifact.kind,
        detail: "Artifact stored and versioned in the workspace repository.",
      }),
    );
  }

  function runCommand(command) {
    setState({
      ...state,
      commandHistory: [command, ...state.commandHistory].slice(0, 30),
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "command.executed",
        service: "Universal Command Palette",
        subject: command,
        evidence: "Command captured in workspace history.",
        detail: "Natural-language command executed against the platform shell.",
      }),
    );
  }

  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    createSolution,
    selectRequest,
    switchTenant,
    selectProject,
    switchRole,
    setEnvironment,
    installAgent,
    installIntegration,
    createProject,
    postComment,
    focusKnowledgeNode,
    runAutomationTemplate,
    advanceWorkflow,
    approveGate,
    pauseWorkflow,
    resumeWorkflow,
    retryWorkflow,
    rejectWorkflow,
    attachArtifact,
    runCommand,
  };
}

export const createPlatformRuntime = createRuntime;
export const platformRuntime = createRuntime();

export {
  AGENT_MARKETPLACE,
  AUTOMATION_TEMPLATES,
  COLLABORATION_THREADS,
  DEVELOPER_SURFACES,
  INTEGRATIONS,
  KNOWLEDGE_GRAPH,
  PLATFORM_CENTERS,
  PROJECTS,
  SERVICE_CATALOG,
  SOLUTION_TEMPLATES,
  TENANTS,
  WORKFLOW_SEQUENCE,
  WORKFLOW_STAGES,
};
