from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "novacodepro_portal" / "src" / "App.jsx"
PACKAGE = ROOT / "novacodepro_portal" / "package.json"
RUNTIME = ROOT / "novacodepro_portal" / "src" / "platform" / "runtime.js"
CATALOG = ROOT / "novacodepro_portal" / "src" / "platform" / "catalog.js"
SOLUTION_PORTAL = ROOT / "novacodepro_portal" / "src" / "solutions" / "SolutionEngineeringPortal.jsx"
SOLUTION_ROUTES = ROOT / "novacodepro_portal" / "src" / "platform" / "solutionRoutes.js"
SOLUTION_API = ROOT / "novacodepro_portal" / "src" / "platform" / "solutionEngineeringApi.js"
AI_WORKSPACE = ROOT / "novacodepro_portal" / "src" / "platform" / "aiWorkspace.jsx"
AI_WORKSPACE_MODEL = ROOT / "novacodepro_portal" / "src" / "platform" / "aiWorkspaceModel.js"
AI_WORKSPACE_API = ROOT / "novacodepro_portal" / "src" / "platform" / "aiWorkspaceApi.js"


def test_novacodepro_portal_is_a_separate_vite_app() -> None:
    package_text = PACKAGE.read_text(encoding="utf-8")
    assert '"name": "novacodepro-portal"' in package_text
    assert '"build": "vite build"' in package_text
    assert '"dev": "vite --host 127.0.0.1"' in package_text


def test_novacodepro_portal_covers_the_expected_workspaces() -> None:
    text = "\n".join(
        [
            APP.read_text(encoding="utf-8"),
            CATALOG.read_text(encoding="utf-8"),
            RUNTIME.read_text(encoding="utf-8"),
            SOLUTION_PORTAL.read_text(encoding="utf-8"),
            SOLUTION_ROUTES.read_text(encoding="utf-8"),
            SOLUTION_API.read_text(encoding="utf-8"),
            AI_WORKSPACE.read_text(encoding="utf-8"),
            AI_WORKSPACE_MODEL.read_text(encoding="utf-8"),
            AI_WORKSPACE_API.read_text(encoding="utf-8"),
        ]
    )
    for token in [
        "NovaCodePro",
        "What would you like to accomplish today?",
        "AI doctrine",
        "AI proposes. Policies constrain. Humans authorize. Systems execute.",
        "Request summary",
        "Suggested solution",
        "Execution status",
        "Workflow monitor",
        "Plan only",
        "Send and execute",
        "Create workflow",
        "Attachments",
        "29-window enterprise maturity model",
        "Window 16",
        "Human Approval Center",
        "Window 26",
        "Approval Policy and Routing Engine",
        "Enterprise Command Center",
        "Shared platform services",
        "Shared interaction model",
        "Release Factory",
        "Deployment Center",
        "Digital Twin",
        "Enterprise Digital Twin",
        "Operations Center",
        "Continuous Improvement",
        "Board of Directors",
        "Chief Executive Officer",
        "Chief Operating Officer",
        "Chief Technology Officer",
        "Chief Financial Officer",
        "Chief Product Officer",
        "Chief Information Security Officer",
        "Chief Legal & Compliance Officer",
        "Platform Administrator",
        "Governance model",
        "Governance matrix",
        "Platform administration center",
        "Identity & Access",
        "Organizations & Tenants",
        "Infrastructure & Operations",
        "Engineering & Delivery",
        "Governance & Audit",
        "Monitoring & Cost",
        "Marketplace & Settings",
        "Software Engineer",
        "Operations Manager",
        "Business Administrator",
        "Partner Administrator",
        "Customer Success",
        "Executive",
        "Command palette",
        "Multi-window dock",
        "NovaID",
        "NovaCodePro Experience Platform",
        "Web Frontend",
        "Mobile App",
        "Inspector App",
        "Desktop App",
        "Developer Portal",
        "Operational Verification",
        "Configured",
        "Executed",
        "Verified",
        "Certified",
        "Approved",
        "APIs, SDKs, tutorials, sandbox, auth, webhooks, changelog, and status",
        "novacodepro.afritechnology.com",
        "Trust Center",
        "Release Center",
        "Observability Center",
        "Data Center",
        "Security Center",
        "Executive Center",
        "Policy Engine",
        "Enterprise foundation",
        "Knowledge Graph",
        "Automation engine",
        "Developer platform",
        "Distributed platform",
        "Enterprise Evidence Engine",
        "Enterprise Risk Engine",
        "Executive AI Services",
        "Workflow Service",
        "Artifact Service",
        "Release Factory",
        "Observability Service",
        "Platform health",
        "Service registry",
        "Governance queue",
        "Workflow builder",
        "Digital twin",
        "Marketplace",
        "Command Service",
        "Customer Solutions",
        "Discovery Workspace",
        "Requirements Studio",
        "Business Analysis Studio",
        "UX/UI Studio",
        "Architecture Studio",
        "Engineering Studio",
        "Quality Studio",
        "Security Studio",
        "Compliance & Risk Studio",
        "Release Studio",
        "Deployment Studio",
        "Customer Acceptance Portal",
        "Operations Layer",
        "Support and Evolution",
        "Workflow Fabric",
        "Approvals",
        "Knowledge",
        "Evidence",
        "Universal AI Workspace",
        "AIRequestComposer",
        "AIUnderstandingPanel",
        "AgentCollaborationPanel",
        "ExecutionTimeline",
        "ArtifactExplorer",
        "ApprovalWorkspace",
        "ExecutionMonitor",
        "KnowledgeCapturePanel",
        "WorkspaceContextPanel",
        "AISuggestionsPanel",
        "NotConnectedError",
        "/novacodepro/solutions",
        "/v1/solution-engineering",
        "/v1/workflow-fabric",
    ]:
        assert token in text


def test_novacodepro_portal_mentions_the_separate_dashboard_boundary() -> None:
    text = APP.read_text(encoding="utf-8")
    assert "Separate from the current NovaTech dashboard surface." in text


def test_novacodepro_portal_has_real_platform_services() -> None:
    runtime = RUNTIME.read_text(encoding="utf-8")
    catalog = CATALOG.read_text(encoding="utf-8")
    for token in [
        "createPlatformRuntime",
        "localStorage",
        "solution.request.created",
        "solution.deployment.prepared",
        "audit.event.appended",
        "WORKFLOW_STAGES",
        "SERVICE_CATALOG",
        "AGENT_MARKETPLACE",
        "SOLUTION_TEMPLATES",
        "TENANTS",
        "PROJECTS",
        "COLLABORATION_THREADS",
        "KNOWLEDGE_GRAPH",
        "AUTOMATION_TEMPLATES",
        "INTEGRATIONS",
        "DEVELOPER_SURFACES",
        "queryKnowledgeGraph",
        "traceKnowledgePath",
        "runEnterpriseInteraction",
        "approvalRoutes",
        "evidenceBundles",
        "riskRegister",
        "digitalTwinScenarios",
        "executiveInsights",
        "commandCenterSnapshots",
        "switchTenant",
        "createProject",
        "postComment",
        "focusKnowledgeNode",
        "runAutomationTemplate",
        "mode: payload.mode",
        "attachments: payload.attachments",
        "contextSources: payload.contextSources",
        "selectedAgents: payload.selectedAgents",
        "environment: payload.environment",
    ]:
        assert token in runtime + catalog
