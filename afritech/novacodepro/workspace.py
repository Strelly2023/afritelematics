from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from afritech.afriprogramming.rbac import canonical_role_name, role_definition
from afritech.novacodepro.platform import NovaCodeProPlatform


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _organization_label(organization_id: str) -> str:
    normalized = organization_id.strip().lower()
    if "novatech" in normalized:
        return "NovaTech"
    if not organization_id:
        return "Unknown organization"
    return organization_id.replace("-", " ").replace("_", " ").title()


def _display_name(user_id: str) -> str:
    value = user_id.strip()
    if not value:
        return "NovaCodePro User"
    lowered = value.lower()
    for prefix in ("usr_", "user_", "account_", "person_"):
        if lowered.startswith(prefix):
            value = value[len(prefix) :]
            break
    value = value.replace(".", " ").replace("-", " ").replace("_", " ")
    value = " ".join(part for part in value.split() if part)
    return value.title() if value else "NovaCodePro User"


def _workspace_slug(role: str) -> str:
    mapping = {
        "ADMIN": "admin",
        "DEVELOPER": "developer",
        "PRODUCT_MANAGER": "product",
        "OPERATOR": "operations",
        "VERIFIER": "security",
        "CLIENT": "partner",
        "PARTNER": "partner",
        "CUSTOMER": "customer",
        "OBSERVER": "support",
    }
    return mapping.get(canonical_role_name(role), "workspace")


def _workspace_label(role: str) -> str:
    mapping = {
        "ADMIN": "Platform Administrator",
        "DEVELOPER": "Developer",
        "PRODUCT_MANAGER": "Product Manager",
        "OPERATOR": "DevOps Engineer",
        "VERIFIER": "Security Engineer",
        "CLIENT": "Partner",
        "PARTNER": "Partner",
        "CUSTOMER": "Customer",
        "OBSERVER": "Customer Support",
    }
    canonical = canonical_role_name(role)
    return mapping.get(canonical, role_definition(canonical).get("label", canonical.replace("_", " ").title()))


def _workspace_title(role: str) -> str:
    mapping = {
        "ADMIN": "Platform Administration Workspace",
        "DEVELOPER": "Developer Workspace",
        "PRODUCT_MANAGER": "Product Management Workspace",
        "OPERATOR": "Operations Workspace",
        "VERIFIER": "Security Workspace",
        "CLIENT": "Partner Workspace",
        "PARTNER": "Partner Workspace",
        "CUSTOMER": "Customer Workspace",
        "OBSERVER": "Support Workspace",
    }
    return mapping.get(canonical_role_name(role), "Enterprise Workspace")


def _workspace_description(role: str) -> str:
    mapping = {
        "ADMIN": "Govern platform services, tenants, identity, evidence, approvals, and operational readiness.",
        "DEVELOPER": "Turn approved requirements into secure, tested, documented, traceable, and release-ready software.",
        "PRODUCT_MANAGER": "Define the right product, prioritize the right work, align delivery teams, and ensure each release creates measurable value.",
        "OPERATOR": "Watch delivery health, deployments, reliability signals, and incident response.",
        "VERIFIER": "Review security posture, approvals, evidence, and compliance gates.",
        "CLIENT": "Coordinate partner integrations, shared resources, and certified interfaces.",
        "PARTNER": "Use governed integrations, sandbox access, and support pathways.",
        "CUSTOMER": "Track requests, deliverables, approvals, and service updates.",
        "OBSERVER": "Monitor work, incidents, and approvals without edit authority.",
    }
    return mapping.get(canonical_role_name(role), "Federated enterprise workspace")


def _base_cards(service: NovaCodeProPlatform) -> dict[str, Any]:
    summary = service.admin_summary()
    return {
        "platform_health": summary.get("platform_health", "healthy"),
        "service_health": summary.get("service_health", {}),
        "pending_approvals": summary.get("pending_approvals", []),
        "ready_release_queue": summary.get("ready_release_queue", []),
        "workflow_statuses": summary.get("workflow_statuses", {}),
        "deployment_statuses": summary.get("deployment_statuses", {}),
        "status": summary,
    }


def _developer_health(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "repositories_healthy": "18/20",
        "open_pull_requests": int(summary.get("pull_request_count", 12) or 12),
        "failing_pipelines": int(summary.get("failing_pipeline_count", 2) or 2),
        "test_pass_rate": "98.7%",
        "coverage": "94.2%",
        "critical_vulnerabilities": int(summary.get("critical_vulnerability_count", 0) or 0),
        "release_blockers": int(summary.get("release_blocker_count", 3) or 3),
    }


def _product_health(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_products": int(summary.get("product_count", 8) or 8),
        "roadmap_confidence": "87%",
        "features_on_schedule": int(summary.get("features_on_schedule", 42) or 42),
        "features_at_risk": int(summary.get("features_at_risk", 6) or 6),
        "blocked_initiatives": int(summary.get("blocked_initiatives", 3) or 3),
        "open_customer_escalations": int(summary.get("open_customer_escalations", 4) or 4),
        "upcoming_releases": int(summary.get("upcoming_releases", 5) or 5),
        "new_feedback_items": int(summary.get("new_feedback_items", 38) or 38),
        "critical_usability_issues": int(summary.get("critical_usability_issues", 2) or 2),
        "top_requested_feature": str(summary.get("top_requested_feature", "Faster agent onboarding")),
        "support_trend": str(summary.get("support_trend", "Payment verification delays")),
        "adoption_trend": str(summary.get("adoption_trend", "Increasing")),
    }


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    icon: str
    route: str
    required_permissions: tuple[str, ...]
    supported_roles: tuple[str, ...]
    supported_environments: tuple[str, ...]
    version: str
    ownership_team: str
    help_url: str
    audit_category: str
    group: str
    overview: tuple[str, ...]
    primary_actions: tuple[str, ...]


TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        id="solution-studio",
        name="Solution Studio",
        description="Turn a business request into a governed solution plan.",
        icon="◎",
        route="/novacodepro/tools/solution-studio",
        required_permissions=("solution.write", "workflow.write"),
        supported_roles=("ADMIN", "DEVELOPER"),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Solution Engineering",
        help_url="/docs/novacodepro/tools/solution-studio",
        audit_category="solution",
        group="BUILD",
        overview=("Intake", "Requirements", "Architecture", "Design", "Validation"),
        primary_actions=("Create Solution", "Open Requirements", "Generate Architecture"),
    ),
    ToolDefinition(
        id="application-factory",
        name="Application Factory",
        description="Assemble application modules and release artifacts.",
        icon="▣",
        route="/novacodepro/tools/application-factory",
        required_permissions=("solution.write", "release.write"),
        supported_roles=("ADMIN", "DEVELOPER"),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Application Factory",
        help_url="/docs/novacodepro/tools/application-factory",
        audit_category="application",
        group="BUILD",
        overview=("Modules", "Source", "Builds", "Packaging", "Artifacts"),
        primary_actions=("Generate App", "Review Modules", "Package Release"),
    ),
    ToolDefinition(
        id="projects",
        name="Project Portfolio",
        description="Track projects, stakeholders, scope, and delivery status.",
        icon="▦",
        route="/novacodepro/tools/projects",
        required_permissions=("project.read", "project.write"),
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR", "OBSERVER"),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Portfolio Office",
        help_url="/docs/novacodepro/tools/projects",
        audit_category="project",
        group="HOME",
        overview=("Projects", "Status", "Stakeholders", "Milestones", "Evidence"),
        primary_actions=("Create Project", "Open Project", "Review Scope"),
    ),
    ToolDefinition(
        id="engineering",
        name="Engineering Center",
        description="Coordinate implementation, reviews, and code evidence.",
        icon="</>",
        route="/novacodepro/tools/engineering",
        required_permissions=("solution.write", "project.write"),
        supported_roles=("ADMIN", "DEVELOPER"),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Engineering",
        help_url="/docs/novacodepro/tools/engineering",
        audit_category="engineering",
        group="BUILD",
        overview=("Source", "Changes", "Reviews", "Tasks", "Builds"),
        primary_actions=("Open Workspace", "Review Diff", "Run Build"),
    ),
    ToolDefinition(
        id="build-test-center",
        name="Build and Test Center",
        description="Run builds, tests, and quality checks on governed work.",
        icon="✓",
        route="/novacodepro/tools/build-test-center",
        required_permissions=("workflow.write", "release.write"),
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR"),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Engineering",
        help_url="/docs/novacodepro/tools/build-test-center",
        audit_category="quality",
        group="BUILD",
        overview=("Builds", "Tests", "Coverage", "Security", "Reports"),
        primary_actions=("Run Tests", "View Coverage", "Inspect Report"),
    ),
    ToolDefinition(
        id="release-center",
        name="Release Center",
        description="Prepare, approve, sign, and publish releases.",
        icon="⟶",
        route="/novacodepro/tools/release-center",
        required_permissions=("release.read", "release.write"),
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Release Engineering",
        help_url="/docs/novacodepro/tools/release-center",
        audit_category="release",
        group="DELIVER",
        overview=("Readiness", "Artifacts", "Signing", "Approval", "Verification"),
        primary_actions=("Request Approval", "Publish Release", "Rollback"),
    ),
    ToolDefinition(
        id="deployment-center",
        name="Deployment Center",
        description="Promote releases through governed environments.",
        icon="⇢",
        route="/novacodepro/tools/deployment-center",
        required_permissions=("deployment.read", "deployment.write"),
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Delivery",
        help_url="/docs/novacodepro/tools/deployment-center",
        audit_category="deployment",
        group="DELIVER",
        overview=("Environments", "Rollouts", "Health", "Rollback", "History"),
        primary_actions=("Start Deployment", "Verify Health", "Rollback"),
    ),
    ToolDefinition(
        id="environment-manager",
        name="Environment Manager",
        description="Manage environment access, routing, and readiness.",
        icon="⟐",
        route="/novacodepro/tools/environment-manager",
        required_permissions=("deployment.write", "policy.write"),
        supported_roles=("ADMIN", "OPERATOR"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Operations",
        help_url="/docs/novacodepro/tools/environment-manager",
        audit_category="environment",
        group="DELIVER",
        overview=("Regions", "Clusters", "Keys", "Policy", "Routing"),
        primary_actions=("Change Environment", "Check Readiness", "Review Access"),
    ),
    ToolDefinition(
        id="operations-center",
        name="Operations Center",
        description="Monitor services, incidents, and operational health.",
        icon="◔",
        route="/novacodepro/tools/operations-center",
        required_permissions=("read:metrics", "read:delivery"),
        supported_roles=("ADMIN", "OPERATOR", "OBSERVER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/operations-center",
        audit_category="operations",
        group="OPERATE",
        overview=("Health", "Metrics", "Alerts", "Incidents", "Uptime"),
        primary_actions=("Open Incident", "Inspect Metrics", "View Alerts"),
    ),
    ToolDefinition(
        id="reliability-center",
        name="Reliability Center",
        description="Track SLOs, error budgets, capacity, and chaos readiness.",
        icon="◐",
        route="/novacodepro/tools/reliability-center",
        required_permissions=("read:metrics", "monitoring:read"),
        supported_roles=("ADMIN", "OPERATOR"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="SRE",
        help_url="/docs/novacodepro/tools/reliability-center",
        audit_category="reliability",
        group="OPERATE",
        overview=("SLIs", "SLOs", "Budgets", "Capacity", "Runbooks"),
        primary_actions=("View SLOs", "Open Runbook", "Assess Capacity"),
    ),
    ToolDefinition(
        id="incident-command",
        name="Incident Command",
        description="Coordinate incident response and recovery actions.",
        icon="!",
        route="/novacodepro/tools/incident-command",
        required_permissions=("read:metrics", "incident.resolve"),
        supported_roles=("ADMIN", "OPERATOR", "VERIFIER", "OBSERVER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Management",
        help_url="/docs/novacodepro/tools/incident-command",
        audit_category="incident",
        group="OPERATE",
        overview=("Incidents", "Timeline", "Owners", "Recovery", "Evidence"),
        primary_actions=("Open Bridge", "Assign Owner", "Create Evidence"),
    ),
    ToolDefinition(
        id="customer-center",
        name="Customer Center",
        description="Surface customer requests, entitlements, and service status.",
        icon="☺",
        route="/novacodepro/tools/customer-center",
        required_permissions=("read:metrics", "read:verification"),
        supported_roles=("ADMIN", "OBSERVER", "CUSTOMER"),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Customer Operations",
        help_url="/docs/novacodepro/tools/customer-center",
        audit_category="customer",
        group="BUSINESS",
        overview=("Requests", "Entitlements", "Status", "Reports", "Communications"),
        primary_actions=("Open Case", "Review Status", "Send Update"),
    ),
    ToolDefinition(
        id="partner-center",
        name="Partner Center",
        description="Manage partner integrations, certificates, and shared access.",
        icon="◎",
        route="/novacodepro/tools/partner-center",
        required_permissions=("read:integration", "read:trust"),
        supported_roles=("ADMIN", "PARTNER", "CLIENT"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Partner Platform",
        help_url="/docs/novacodepro/tools/partner-center",
        audit_category="partner",
        group="BUSINESS",
        overview=("Integrations", "Sandbox", "Certificates", "Usage", "Support"),
        primary_actions=("Open Sandbox", "Review Integration", "Request Support"),
    ),
    ToolDefinition(
        id="employee-center",
        name="Employee Center",
        description="Support employees with tools, access, and internal services.",
        icon="◫",
        route="/novacodepro/tools/employee-center",
        required_permissions=("read:metrics", "read:trust"),
        supported_roles=("ADMIN", "OPERATOR"),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="People Operations",
        help_url="/docs/novacodepro/tools/employee-center",
        audit_category="employee",
        group="BUSINESS",
        overview=("Accounts", "Access", "Requests", "Policies", "Support"),
        primary_actions=("Invite Employee", "Review Access", "Open Request"),
    ),
    ToolDefinition(
        id="governance-center",
        name="Governance Center",
        description="Review policies, approvals, and governance evidence.",
        icon="⚑",
        route="/novacodepro/tools/governance-center",
        required_permissions=("policy.read", "audit.view"),
        supported_roles=("ADMIN", "VERIFIER", "OBSERVER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Governance",
        help_url="/docs/novacodepro/tools/governance-center",
        audit_category="governance",
        group="GOVERN",
        overview=("Policies", "Approvals", "Exceptions", "Audit", "Controls"),
        primary_actions=("Review Policy", "Open Approval", "Inspect Audit"),
    ),
    ToolDefinition(
        id="risk-center",
        name="Risk Center",
        description="Track enterprise risk, treatment, and acceptance.",
        icon="◈",
        route="/novacodepro/tools/risk-center",
        required_permissions=("risk.read", "risk.write"),
        supported_roles=("ADMIN", "VERIFIER", "OBSERVER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk Office",
        help_url="/docs/novacodepro/tools/risk-center",
        audit_category="risk",
        group="GOVERN",
        overview=("Risks", "Treatments", "Acceptance", "Owners", "Trends"),
        primary_actions=("Add Risk", "Treat Risk", "Accept Risk"),
    ),
    ToolDefinition(
        id="evidence-vault",
        name="Evidence Vault",
        description="Review immutable evidence bundles and signatures.",
        icon="⧉",
        route="/novacodepro/tools/evidence-vault",
        required_permissions=("evidence.read",),
        supported_roles=("ADMIN", "VERIFIER", "OBSERVER"),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Evidence",
        help_url="/docs/novacodepro/tools/evidence-vault",
        audit_category="evidence",
        group="GOVERN",
        overview=("Bundles", "Hashes", "Signatures", "Verification", "Retention"),
        primary_actions=("Open Evidence", "Verify Bundle", "Export Receipt"),
    ),
    ToolDefinition(
        id="approval-center",
        name="Approval Center",
        description="Resolve approvals, sign-offs, and delegation.",
        icon="✓",
        route="/novacodepro/tools/approval-center",
        required_permissions=("approval.read", "approval.write"),
        supported_roles=("ADMIN", "VERIFIER", "OPERATOR"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Approvals",
        help_url="/docs/novacodepro/tools/approval-center",
        audit_category="approval",
        group="GOVERN",
        overview=("Queue", "Delegation", "Quorum", "Conditions", "History"),
        primary_actions=("Review Approval", "Delegate", "Resolve"),
    ),
    ToolDefinition(
        id="security-center",
        name="Security Center",
        description="Review threats, vulnerabilities, policies, and exceptions.",
        icon="⛨",
        route="/novacodepro/tools/security-center",
        required_permissions=("compliance.view", "policy.read"),
        supported_roles=("ADMIN", "VERIFIER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/security-center",
        audit_category="security",
        group="OPERATE",
        overview=("Threats", "Findings", "Controls", "Exceptions", "Supply Chain"),
        primary_actions=("Open Finding", "Review Exception", "Inspect Policy"),
    ),
    ToolDefinition(
        id="knowledge-graph",
        name="Knowledge Graph",
        description="Trace requests, code, releases, incidents, and evidence.",
        icon="⟐",
        route="/novacodepro/tools/knowledge-graph",
        required_permissions=("graph.read", "knowledge.query"),
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR", "VERIFIER", "OBSERVER"),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Knowledge Fabric",
        help_url="/docs/novacodepro/tools/knowledge-graph",
        audit_category="knowledge",
        group="GOVERN",
        overview=("Trace", "Impact", "Ownership", "Lineage", "Search"),
        primary_actions=("Trace Node", "Find Impact", "Open Graph"),
    ),
    ToolDefinition(
        id="digital-twin",
        name="Digital Twin",
        description="Simulate outages, deployment effects, and business impact.",
        icon="◍",
        route="/novacodepro/tools/digital-twin",
        required_permissions=("twin.read", "twin.simulate"),
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR", "OBSERVER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Simulation",
        help_url="/docs/novacodepro/tools/digital-twin",
        audit_category="simulation",
        group="LEADERSHIP",
        overview=("Topology", "Scenarios", "Forecasts", "Confidence", "Evidence"),
        primary_actions=("Run Simulation", "Compare Scenarios", "Refresh Twin"),
    ),
    ToolDefinition(
        id="executive-council",
        name="Executive Council",
        description="Read executive briefings and advisory recommendations.",
        icon="⫶",
        route="/novacodepro/tools/executive-council",
        required_permissions=("read:metrics", "read:trust"),
        supported_roles=("ADMIN", "OBSERVER"),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Executive Office",
        help_url="/docs/novacodepro/tools/executive-council",
        audit_category="executive",
        group="LEADERSHIP",
        overview=("Briefings", "Forecasts", "Risks", "Options", "Decisions"),
        primary_actions=("Open Briefing", "Review Recommendation", "Prepare Pack"),
    ),
    ToolDefinition(
        id="board-portal",
        name="Board Portal",
        description="Review board packs, resolutions, and signed evidence.",
        icon="▤",
        route="/novacodepro/tools/board-portal",
        required_permissions=("audit.view", "policy.read"),
        supported_roles=("ADMIN",),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Board Secretariat",
        help_url="/docs/novacodepro/tools/board-portal",
        audit_category="board",
        group="LEADERSHIP",
        overview=("Board Packs", "Resolutions", "Votes", "Evidence", "Actions"),
        primary_actions=("Open Board Pack", "Review Resolution", "View Evidence"),
    ),
    ToolDefinition(
        id="platform-administration",
        name="Platform Administration",
        description="Manage platform services, tenants, identity, and environments.",
        icon="⚙",
        route="/novacodepro/tools/platform-administration",
        required_permissions=("rbac.manage", "policy.manage"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Operations",
        help_url="/docs/novacodepro/tools/platform-administration",
        audit_category="administration",
        group="ADMINISTRATION",
        overview=("Identity", "Tenants", "Services", "Environments", "Audit"),
        primary_actions=("Manage Tenant", "Open Service Registry", "Review Access"),
    ),
    ToolDefinition(
        id="developer-workspace",
        name="Developer Workspace",
        description="Track assigned work, sprint context, reviews, and release blockers.",
        icon="⌁",
        route="/novacodepro/tools/developer-workspace",
        required_permissions=("workspace.read", "project.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Developer Experience",
        help_url="/docs/novacodepro/tools/developer-workspace",
        audit_category="workspace",
        group="HOME",
        overview=("My Work", "Projects", "Reviews", "Builds", "Releases"),
        primary_actions=("Resume Work", "Open Sprint", "Review Blockers"),
    ),
    ToolDefinition(
        id="project-center",
        name="Project Center",
        description="Manage milestones, epics, stories, dependencies, and delivery status.",
        icon="▦",
        route="/novacodepro/tools/project-center",
        required_permissions=("project.read", "project.create", "project.update"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Product Engineering",
        help_url="/docs/novacodepro/tools/project-center",
        audit_category="project",
        group="HOME",
        overview=("Projects", "Milestones", "Epics", "Stories", "Blockers"),
        primary_actions=("Create Project", "Update Milestone", "Review Blockers"),
    ),
    ToolDefinition(
        id="code-workspace",
        name="Code Workspace",
        description="Browse, edit, refactor, debug, and test governed source code.",
        icon="</>",
        route="/novacodepro/tools/code-workspace",
        required_permissions=("code.read", "code.write"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Engineering",
        help_url="/docs/novacodepro/tools/code-workspace",
        audit_category="code",
        group="BUILD",
        overview=("Files", "Symbols", "Branches", "Changes", "Terminal"),
        primary_actions=("Open File", "Create Branch", "Run Debug"),
    ),
    ToolDefinition(
        id="repository-explorer",
        name="Repository Explorer",
        description="Inspect files, branches, commits, ownership, and repository health.",
        icon="▤",
        route="/novacodepro/tools/repository-explorer",
        required_permissions=("repository.read",),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Source Control",
        help_url="/docs/novacodepro/tools/repository-explorer",
        audit_category="repository",
        group="BUILD",
        overview=("Files", "Branches", "Commits", "Ownership", "Health"),
        primary_actions=("Open Repository", "Compare Branches", "Inspect Ownership"),
    ),
    ToolDefinition(
        id="branch-change-center",
        name="Branch and Change Center",
        description="Create branches, inspect diffs, resolve conflicts, and prepare change sets.",
        icon="⇄",
        route="/novacodepro/tools/branch-change-center",
        required_permissions=("repository.branch_create", "repository.commit"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Engineering",
        help_url="/docs/novacodepro/tools/branch-change-center",
        audit_category="change",
        group="BUILD",
        overview=("Branches", "Diffs", "Conflicts", "Commit Standards", "Change Sets"),
        primary_actions=("Create Branch", "Review Diff", "Open Change Set"),
    ),
    ToolDefinition(
        id="review-center",
        name="Pull Request and Review Center",
        description="Create pull requests, inspect checks, and manage review feedback.",
        icon="❮❯",
        route="/novacodepro/tools/review-center",
        required_permissions=("repository.pull_request_create", "code.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Engineering",
        help_url="/docs/novacodepro/tools/review-center",
        audit_category="review",
        group="DELIVER",
        overview=("Pull Requests", "Reviews", "Checks", "Comments", "Approvals"),
        primary_actions=("Create Pull Request", "Request Review", "Inspect Checks"),
    ),
    ToolDefinition(
        id="build-center",
        name="Build Center",
        description="Build web, backend, mobile, and infrastructure artifacts.",
        icon="⚒",
        route="/novacodepro/tools/build-center",
        required_permissions=("build.execute", "build.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Build Engineering",
        help_url="/docs/novacodepro/tools/build-center",
        audit_category="build",
        group="BUILD",
        overview=("Queues", "Profiles", "Logs", "Artifacts", "Reproducibility"),
        primary_actions=("Start Build", "Inspect Logs", "Download Artifact"),
    ),
    ToolDefinition(
        id="test-center",
        name="Test Center",
        description="Run and inspect unit, integration, contract, UI, and accessibility tests.",
        icon="✓",
        route="/novacodepro/tools/test-center",
        required_permissions=("test.execute", "test.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Engineering",
        help_url="/docs/novacodepro/tools/test-center",
        audit_category="test",
        group="BUILD",
        overview=("Unit", "Integration", "Contract", "UI", "Coverage"),
        primary_actions=("Run Tests", "View Coverage", "Inspect Failure"),
    ),
    ToolDefinition(
        id="api-studio",
        name="API Studio",
        description="Design API contracts, schemas, mocks, and compatibility checks.",
        icon="{}",
        route="/novacodepro/tools/api-studio",
        required_permissions=("api.design", "api.test"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="API Platform",
        help_url="/docs/novacodepro/tools/api-studio",
        audit_category="api",
        group="DESIGN",
        overview=("OpenAPI", "Schemas", "Mocking", "Versions", "Compatibility"),
        primary_actions=("Design API", "Test Request", "Generate SDK"),
    ),
    ToolDefinition(
        id="data-studio",
        name="Data Studio",
        description="Design schemas, migrations, lineage, and tenant-safe queries.",
        icon="◧",
        route="/novacodepro/tools/data-studio",
        required_permissions=("code.read", "code.write"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Data Engineering",
        help_url="/docs/novacodepro/tools/data-studio",
        audit_category="data",
        group="DESIGN",
        overview=("Schemas", "Migrations", "Indexes", "Lineage", "Retention"),
        primary_actions=("Create Migration", "Review Lineage", "Validate Isolation"),
    ),
    ToolDefinition(
        id="mobile-app-studio",
        name="Mobile App Studio",
        description="Manage mobile projects, permissions, builds, and release candidates.",
        icon="◉",
        route="/novacodepro/tools/mobile-app-studio",
        required_permissions=("code.write", "build.execute"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Mobile Engineering",
        help_url="/docs/novacodepro/tools/mobile-app-studio",
        audit_category="mobile",
        group="DESIGN",
        overview=("Platforms", "Identifiers", "Devices", "Builds", "Release Candidates"),
        primary_actions=("Open Emulator", "Build Package", "Prepare Release"),
    ),
    ToolDefinition(
        id="ui-ux-studio",
        name="UI/UX Studio",
        description="Review wireframes, component states, accessibility, and responsive layouts.",
        icon="◌",
        route="/novacodepro/tools/ui-ux-studio",
        required_permissions=("workspace.read", "code.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Design Systems",
        help_url="/docs/novacodepro/tools/ui-ux-studio",
        audit_category="design",
        group="DESIGN",
        overview=("Wireframes", "Tokens", "Components", "Accessibility", "Responsiveness"),
        primary_actions=("Review Design", "Inspect Tokens", "Validate Responsive"),
    ),
    ToolDefinition(
        id="novaai-engineering-assistant",
        name="NovaAI Engineering Assistant",
        description="Generate implementation plans, code suggestions, tests, and documentation.",
        icon="AI",
        route="/novacodepro/tools/novaai-engineering-assistant",
        required_permissions=("code.read", "documentation.write"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="AI Engineering",
        help_url="/docs/novacodepro/tools/novaai-engineering-assistant",
        audit_category="ai",
        group="ASSURE",
        overview=("Plans", "Code", "Tests", "Docs", "Logs"),
        primary_actions=("Ask NovaAI", "Refactor Code", "Generate Tests"),
    ),
    ToolDefinition(
        id="dependency-center",
        name="Dependency Center",
        description="Inspect dependencies, licenses, conflicts, and vulnerability exposure.",
        icon="∿",
        route="/novacodepro/tools/dependency-center",
        required_permissions=("artifact.read", "security.finding_read_assigned"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Supply Chain Security",
        help_url="/docs/novacodepro/tools/dependency-center",
        audit_category="dependency",
        group="ASSURE",
        overview=("Packages", "Licenses", "Vulnerabilities", "Conflicts", "SBOM"),
        primary_actions=("Review Package", "Check Vulnerability", "Generate SBOM"),
    ),
    ToolDefinition(
        id="secure-development-center",
        name="Secure Development Center",
        description="Review static analysis, secret scanning, and security remediation tasks.",
        icon="⛨",
        route="/novacodepro/tools/secure-development-center",
        required_permissions=("security.finding_read_assigned", "security.remediation_submit"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Application Security",
        help_url="/docs/novacodepro/tools/secure-development-center",
        audit_category="security",
        group="ASSURE",
        overview=("Findings", "Secrets", "Containers", "Threats", "Evidence"),
        primary_actions=("Review Finding", "Submit Remediation", "Request Security Review"),
    ),
    ToolDefinition(
        id="developer-environments",
        name="Developer Environments",
        description="Manage isolated dev workspaces, preview systems, and approved services.",
        icon="⟁",
        route="/novacodepro/tools/developer-environments",
        required_permissions=("environment.development_manage", "environment.preview_create"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Platform Enablement",
        help_url="/docs/novacodepro/tools/developer-environments",
        audit_category="environment",
        group="ASSURE",
        overview=("Workspaces", "Variables", "Services", "Datasets", "Health"),
        primary_actions=("Start Environment", "Reset Data", "Open Preview"),
    ),
    ToolDefinition(
        id="pipeline-center",
        name="Pipeline Center",
        description="Inspect CI/CD workflows, gates, failures, and pipeline settings.",
        icon="⤴",
        route="/novacodepro/tools/pipeline-center",
        required_permissions=("pipeline.read", "pipeline.execute_eligible_jobs"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Delivery Engineering",
        help_url="/docs/novacodepro/tools/pipeline-center",
        audit_category="pipeline",
        group="DELIVER",
        overview=("Stages", "Runs", "Logs", "Artifacts", "Eligibility"),
        primary_actions=("Open Pipeline", "Retry Job", "Inspect Gate"),
    ),
    ToolDefinition(
        id="artifact-center",
        name="Artifact Center",
        description="Inspect packages, checksums, signatures, and build provenance.",
        icon="⧉",
        route="/novacodepro/tools/artifact-center",
        required_permissions=("artifact.read", "artifact.submit_for_release"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Release Engineering",
        help_url="/docs/novacodepro/tools/artifact-center",
        audit_category="artifact",
        group="DELIVER",
        overview=("Packages", "Checksums", "Signatures", "SBOM", "Provenance"),
        primary_actions=("Inspect Artifact", "Verify Signature", "Submit for Release"),
    ),
    ToolDefinition(
        id="documentation-center",
        name="Documentation Center",
        description="Create and publish technical documentation, guides, and release notes.",
        icon="☰",
        route="/novacodepro/tools/documentation-center",
        required_permissions=("documentation.write", "documentation.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Developer Experience",
        help_url="/docs/novacodepro/tools/documentation-center",
        audit_category="documentation",
        group="KNOWLEDGE",
        overview=("Docs", "APIs", "Guides", "Runbooks", "Release Notes"),
        primary_actions=("Write Doc", "Publish Docs", "Review Coverage"),
    ),
    ToolDefinition(
        id="developer-diagnostics",
        name="Developer Diagnostics",
        description="Inspect traces, logs, metrics, flags, and dependency state for owned work.",
        icon="⌘",
        route="/novacodepro/tools/developer-diagnostics",
        required_permissions=("observability.read_authorized", "workspace.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Developer Experience",
        help_url="/docs/novacodepro/tools/developer-diagnostics",
        audit_category="diagnostics",
        group="ASSURE",
        overview=("Traces", "Logs", "Metrics", "Flags", "Dependencies"),
        primary_actions=("Inspect Trace", "Open Log Stream", "Compare Deployments"),
    ),
    ToolDefinition(
        id="release-request-center",
        name="Release Request Center",
        description="Prepare release candidates, attach evidence, and request approval.",
        icon="⟶",
        route="/novacodepro/tools/release-request-center",
        required_permissions=("release.request", "artifact.submit_for_release"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Release Operations",
        help_url="/docs/novacodepro/tools/release-request-center",
        audit_category="release-request",
        group="DELIVER",
        overview=("Candidates", "Evidence", "Notes", "Approvals", "Status"),
        primary_actions=("Create Release Request", "Attach Evidence", "Review Blockers"),
    ),
    ToolDefinition(
        id="engineering-knowledge-graph",
        name="Engineering Knowledge Graph",
        description="Trace ownership, APIs, services, data flows, and change impact.",
        icon="⟐",
        route="/novacodepro/tools/engineering-knowledge-graph",
        required_permissions=("observability.read_authorized", "repository.read"),
        supported_roles=("DEVELOPER",),
        supported_environments=("development", "staging", "pilot"),
        version="v1",
        ownership_team="Knowledge Fabric",
        help_url="/docs/novacodepro/tools/engineering-knowledge-graph",
        audit_category="knowledge",
        group="KNOWLEDGE",
        overview=("Ownership", "Lineage", "Impact", "Dependencies", "Search"),
        primary_actions=("Trace Change", "Inspect Impact", "Open Graph"),
    ),
    ToolDefinition(
        id="product-workspace",
        name="Product Workspace",
        description="Track priorities, products, signals, decisions, and delivery context.",
        icon="⌂",
        route="/novacodepro/tools/product-workspace",
        required_permissions=("workspace.read", "product.read"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Operations",
        help_url="/docs/novacodepro/tools/product-workspace",
        audit_category="workspace",
        group="HOME",
        overview=("Priorities", "Products", "Signals", "Decisions", "Readiness"),
        primary_actions=("Review Priorities", "Open Product Portfolio", "Inspect Launch Readiness"),
    ),
    ToolDefinition(
        id="product-portfolio",
        name="Product Portfolio",
        description="Manage product portfolio health, lifecycle stage, and investment posture.",
        icon="▣",
        route="/novacodepro/tools/product-portfolio",
        required_permissions=("product.read", "portfolio.read"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Portfolio Strategy",
        help_url="/docs/novacodepro/tools/product-portfolio",
        audit_category="portfolio",
        group="HOME",
        overview=("Products", "Lifecycle", "Investment", "Overlap", "Retirement"),
        primary_actions=("Register Product", "Review Lifecycle", "Compare Portfolio"),
    ),
    ToolDefinition(
        id="product-strategy-center",
        name="Product Strategy Center",
        description="Define product vision, target segments, themes, and success measures.",
        icon="◆",
        route="/novacodepro/tools/product-strategy-center",
        required_permissions=("strategy.read", "strategy.write", "strategy.submit"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Strategy",
        help_url="/docs/novacodepro/tools/product-strategy-center",
        audit_category="strategy",
        group="STRATEGY",
        overview=("Vision", "Segments", "Value", "Themes", "Measures"),
        primary_actions=("Draft Vision", "Review Theme", "Submit Strategy"),
    ),
    ToolDefinition(
        id="roadmap-center",
        name="Roadmap Center",
        description="Build and publish product roadmaps across time, markets, and dependencies.",
        icon="↦",
        route="/novacodepro/tools/roadmap-center",
        required_permissions=("roadmap.read", "roadmap.create", "roadmap.update"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Planning",
        help_url="/docs/novacodepro/tools/roadmap-center",
        audit_category="roadmap",
        group="STRATEGY",
        overview=("Now", "Next", "Later", "Quarterly", "Annual"),
        primary_actions=("Add Initiative", "Review Dependency", "Publish Roadmap"),
    ),
    ToolDefinition(
        id="market-regional-planning",
        name="Market and Regional Planning",
        description="Compare regions, regulatory constraints, localization needs, and launch order.",
        icon="◫",
        route="/novacodepro/tools/market-regional-planning",
        required_permissions=("roadmap.read", "product.read"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Market Strategy",
        help_url="/docs/novacodepro/tools/market-regional-planning",
        audit_category="market",
        group="STRATEGY",
        overview=("Regions", "Markets", "Localization", "Constraints", "Sequencing"),
        primary_actions=("Compare Region", "Review Constraint", "Plan Launch"),
    ),
    ToolDefinition(
        id="pricing-packaging-center",
        name="Pricing and Packaging Center",
        description="Define packaging, pricing, tiers, entitlements, and approval-ready proposals.",
        icon="¤",
        route="/novacodepro/tools/pricing-packaging-center",
        required_permissions=("pricing.read", "pricing.propose"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Monetization Strategy",
        help_url="/docs/novacodepro/tools/pricing-packaging-center",
        audit_category="pricing",
        group="STRATEGY",
        overview=("Packages", "Tiers", "Entitlements", "Scenarios", "Approval"),
        primary_actions=("Propose Pricing", "Review Tier", "Publish Package"),
    ),
    ToolDefinition(
        id="discovery-studio",
        name="Discovery Studio",
        description="Run discovery interviews, capture hypotheses, and validate opportunities.",
        icon="⌖",
        route="/novacodepro/tools/discovery-studio",
        required_permissions=("insight.create", "research.read_authorized"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Discovery",
        help_url="/docs/novacodepro/tools/discovery-studio",
        audit_category="discovery",
        group="DISCOVER",
        overview=("Hypotheses", "Interviews", "Validation", "Decision", "Evidence"),
        primary_actions=("Plan Discovery", "Review Insight", "Decide Next Step"),
    ),
    ToolDefinition(
        id="customer-insights-center",
        name="Customer Insights Center",
        description="Review customer feedback, support signals, and evidence-backed themes.",
        icon="◉",
        route="/novacodepro/tools/customer-insights-center",
        required_permissions=("insight.create", "analytics.read_aggregated"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Customer Intelligence",
        help_url="/docs/novacodepro/tools/customer-insights-center",
        audit_category="insights",
        group="DISCOVER",
        overview=("Interviews", "Support", "Themes", "Segments", "Trends"),
        primary_actions=("Open Insight", "Group Theme", "Review Evidence"),
    ),
    ToolDefinition(
        id="user-journey-studio",
        name="User Journey Studio",
        description="Map journeys, pain points, trust moments, and accessibility gaps.",
        icon="⇢",
        route="/novacodepro/tools/user-journey-studio",
        required_permissions=("requirements.read", "requirements.create"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Experience Strategy",
        help_url="/docs/novacodepro/tools/user-journey-studio",
        audit_category="journey",
        group="DISCOVER",
        overview=("Actors", "Stages", "Pain Points", "Trust", "Accessibility"),
        primary_actions=("Create Journey", "Review Pain Point", "Inspect Accessibility"),
    ),
    ToolDefinition(
        id="customer-segmentation-center",
        name="Customer Segmentation Center",
        description="Define segments, personas, needs, and eligibility assumptions.",
        icon="◧",
        route="/novacodepro/tools/customer-segmentation-center",
        required_permissions=("insight.create", "product.read"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Market Insights",
        help_url="/docs/novacodepro/tools/customer-segmentation-center",
        audit_category="segmentation",
        group="DISCOVER",
        overview=("Segments", "Personas", "Needs", "Eligibility", "Performance"),
        primary_actions=("Create Segment", "Review Persona", "Compare Need"),
    ),
    ToolDefinition(
        id="requirements-center",
        name="Requirements Center",
        description="Write product requirements, stories, criteria, and release scope.",
        icon="▤",
        route="/novacodepro/tools/requirements-center",
        required_permissions=("requirements.read", "requirements.create", "requirements.update"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Operations",
        help_url="/docs/novacodepro/tools/requirements-center",
        audit_category="requirements",
        group="PLAN",
        overview=("Problems", "Stories", "Criteria", "Dependencies", "Approvals"),
        primary_actions=("Write Requirement", "Attach Evidence", "Submit for Approval"),
    ),
    ToolDefinition(
        id="backlog-prioritization-center",
        name="Backlog and Prioritization Center",
        description="Score, rank, and sequence backlog items using governed prioritization.",
        icon="≡",
        route="/novacodepro/tools/backlog-prioritization-center",
        required_permissions=("backlog.read", "backlog.prioritize"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Planning",
        help_url="/docs/novacodepro/tools/backlog-prioritization-center",
        audit_category="backlog",
        group="PLAN",
        overview=("Epics", "Scoring", "Value", "Effort", "Risk"),
        primary_actions=("Prioritize Backlog", "Re-score Item", "Review Blocker"),
    ),
    ToolDefinition(
        id="cross-functional-planning-center",
        name="Cross-Functional Planning Center",
        description="Coordinate product, design, engineering, support, security, and finance.",
        icon="⇄",
        route="/novacodepro/tools/cross-functional-planning-center",
        required_permissions=("roadmap.update", "product.update"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Program Planning",
        help_url="/docs/novacodepro/tools/cross-functional-planning-center",
        audit_category="planning",
        group="PLAN",
        overview=("Owners", "Dependencies", "Commitments", "Risks", "Reviews"),
        primary_actions=("Open Planning Review", "Add Dependency", "Track Commitment"),
    ),
    ToolDefinition(
        id="product-risk-center",
        name="Product Risk Center",
        description="Track customer, operational, compliance, and delivery risks for products.",
        icon="⚠",
        route="/novacodepro/tools/product-risk-center",
        required_permissions=("risk.read", "risk.create", "risk.escalate"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Risk",
        help_url="/docs/novacodepro/tools/product-risk-center",
        audit_category="risk",
        group="PLAN",
        overview=("Risks", "Mitigations", "Owners", "Launch Blockers", "Acceptance"),
        primary_actions=("Create Risk", "Review Mitigation", "Escalate Risk"),
    ),
    ToolDefinition(
        id="design-collaboration-center",
        name="Design Collaboration Center",
        description="Review wireframes, feedback, accessibility, and product intent alignment.",
        icon="◌",
        route="/novacodepro/tools/design-collaboration-center",
        required_permissions=("requirements.read", "workspace.read"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Design",
        help_url="/docs/novacodepro/tools/design-collaboration-center",
        audit_category="design",
        group="DELIVER",
        overview=("Wireframes", "Feedback", "Accessibility", "Versions", "Coverage"),
        primary_actions=("Review Design", "Add Feedback", "Approve Intent"),
    ),
    ToolDefinition(
        id="engineering-delivery-view",
        name="Engineering Delivery View",
        description="Monitor engineering progress, blockers, dependencies, and forecasts.",
        icon="</>",
        route="/novacodepro/tools/engineering-delivery-view",
        required_permissions=("project.read", "analytics.read_aggregated"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Delivery Engineering",
        help_url="/docs/novacodepro/tools/engineering-delivery-view",
        audit_category="delivery",
        group="DELIVER",
        overview=("Progress", "Blockers", "Forecasts", "Dependencies", "Checks"),
        primary_actions=("Inspect Delivery", "Review Blocker", "Request Clarification"),
    ),
    ToolDefinition(
        id="release-planning-center",
        name="Release Planning Center",
        description="Define release scope, readiness, comms, and rollback planning.",
        icon="⟶",
        route="/novacodepro/tools/release-planning-center",
        required_permissions=("release.read", "release.scope_propose", "release.readiness_recommend"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Release Management",
        help_url="/docs/novacodepro/tools/release-planning-center",
        audit_category="release-planning",
        group="DELIVER",
        overview=("Scope", "Readiness", "Comms", "Rollback", "Dependencies"),
        primary_actions=("Review Scope", "Recommend Readiness", "Open Rollout"),
    ),
    ToolDefinition(
        id="pilot-management-center",
        name="Pilot Management Center",
        description="Manage pilot participants, limits, success criteria, and expansion decisions.",
        icon="⧉",
        route="/novacodepro/tools/pilot-management-center",
        required_permissions=("pilot.read", "pilot.plan", "pilot.recommend_transition"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Go-To-Market",
        help_url="/docs/novacodepro/tools/pilot-management-center",
        audit_category="pilot",
        group="DELIVER",
        overview=("Participants", "Limits", "Criteria", "Risks", "Exit"),
        primary_actions=("Plan Pilot", "Review Feedback", "Recommend Transition"),
    ),
    ToolDefinition(
        id="customer-launch-center",
        name="Customer Launch Center",
        description="Prepare launch plans, messaging, training, and support readiness.",
        icon="✦",
        route="/novacodepro/tools/customer-launch-center",
        required_permissions=("product.read", "documentation.write"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Launch Operations",
        help_url="/docs/novacodepro/tools/customer-launch-center",
        audit_category="launch",
        group="DELIVER",
        overview=("Audience", "Messaging", "Support", "Training", "Monitoring"),
        primary_actions=("Review Launch", "Open FAQ", "Track Readiness"),
    ),
    ToolDefinition(
        id="product-analytics-center",
        name="Product Analytics Center",
        description="Review adoption, funnels, cohorts, retention, and release outcomes.",
        icon="↗",
        route="/novacodepro/tools/product-analytics-center",
        required_permissions=("analytics.read_aggregated",),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Analytics",
        help_url="/docs/novacodepro/tools/product-analytics-center",
        audit_category="analytics",
        group="MEASURE",
        overview=("Adoption", "Funnels", "Retention", "Cohorts", "Outcomes"),
        primary_actions=("Review Metric", "Inspect Cohort", "Compare Release"),
    ),
    ToolDefinition(
        id="experiment-center",
        name="Experiment Center",
        description="Define controlled experiments, rollout plans, and guardrail metrics.",
        icon="◈",
        route="/novacodepro/tools/experiment-center",
        required_permissions=("experiment.create", "experiment.submit"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Experimentation",
        help_url="/docs/novacodepro/tools/experiment-center",
        audit_category="experiment",
        group="MEASURE",
        overview=("Hypotheses", "Rollouts", "Metrics", "Guardrails", "Results"),
        primary_actions=("Create Experiment", "Review Result", "Stop Rollout"),
    ),
    ToolDefinition(
        id="product-documentation-center",
        name="Product Documentation Center",
        description="Publish product briefs, launch notes, lifecycle docs, and enablement material.",
        icon="☰",
        route="/novacodepro/tools/product-documentation-center",
        required_permissions=("documentation.write", "documentation.read"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Product Operations",
        help_url="/docs/novacodepro/tools/product-documentation-center",
        audit_category="documentation",
        group="KNOWLEDGE",
        overview=("Briefs", "Launch Notes", "Guides", "Lifecycle", "Enablement"),
        primary_actions=("Write Brief", "Publish Notes", "Review Coverage"),
    ),
    ToolDefinition(
        id="novaai-product-assistant",
        name="NovaAI Product Assistant",
        description="Summarize feedback, draft requirements, compare roadmap options, and surface risk.",
        icon="AI",
        route="/novacodepro/tools/novaai-product-assistant",
        required_permissions=("product.read", "requirements.create"),
        supported_roles=("PRODUCT_MANAGER",),
        supported_environments=("business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="AI Product",
        help_url="/docs/novacodepro/tools/novaai-product-assistant",
        audit_category="ai",
        group="KNOWLEDGE",
        overview=("Feedback", "Requirements", "Options", "Risks", "Reports"),
        primary_actions=("Ask NovaAI", "Draft Requirement", "Compare Option"),
    ),
    ToolDefinition(
        id="tenant-management",
        name="Tenant Management",
        description="Create, suspend, restore, and review tenant health and isolation.",
        icon="⌂",
        route="/novacodepro/tools/tenant-management",
        required_permissions=("tenant.read", "tenant.configure"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Operations",
        help_url="/docs/novacodepro/tools/tenant-management",
        audit_category="tenant",
        group="ADMINISTRATION",
        overview=("Organizations", "Tenants", "Isolation", "Quotas", "Lifecycle"),
        primary_actions=("Create Tenant", "Suspend Tenant", "Review Isolation"),
    ),
    ToolDefinition(
        id="identity-access-center",
        name="Identity and Access Center",
        description="Manage workforce identities, access risk, and privileged sessions.",
        icon="⎈",
        route="/novacodepro/tools/identity-access-center",
        required_permissions=("identity.read", "identity.assign_role"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Identity Operations",
        help_url="/docs/novacodepro/tools/identity-access-center",
        audit_category="identity",
        group="ADMINISTRATION",
        overview=("Users", "Roles", "Sessions", "Risk", "Federation"),
        primary_actions=("Invite User", "Revoke Session", "Review Risk"),
    ),
    ToolDefinition(
        id="application-tool-registry",
        name="Application and Tool Registry",
        description="Register independent tools, routes, permissions, and rollout rings.",
        icon="▣",
        route="/novacodepro/tools/application-tool-registry",
        required_permissions=("tool.read", "tool.register"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Engineering",
        help_url="/docs/novacodepro/tools/application-tool-registry",
        audit_category="tool-registry",
        group="ADMINISTRATION",
        overview=("Tools", "Routes", "Permissions", "Owners", "Rollouts"),
        primary_actions=("Register Tool", "Disable Tool", "Review Health"),
    ),
    ToolDefinition(
        id="infrastructure-service-center",
        name="Infrastructure and Service Center",
        description="Inspect services, dependencies, latency, versions, and capacity.",
        icon="⛭",
        route="/novacodepro/tools/infrastructure-service-center",
        required_permissions=("platform.read", "operations.read"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Infrastructure",
        help_url="/docs/novacodepro/tools/infrastructure-service-center",
        audit_category="infrastructure",
        group="ADMINISTRATION",
        overview=("Services", "Dependencies", "Capacity", "Latency", "Regions"),
        primary_actions=("Inspect Service", "Review Capacity", "Open Dependency Graph"),
    ),
    ToolDefinition(
        id="artifact-registry",
        name="Artifact Registry",
        description="Review signed artifacts, versions, checksums, and rollout provenance.",
        icon="⧉",
        route="/novacodepro/tools/artifact-registry",
        required_permissions=("artifact.read", "release.verify"),
        supported_roles=("ADMIN",),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Release Operations",
        help_url="/docs/novacodepro/tools/artifact-registry",
        audit_category="artifact",
        group="DELIVER",
        overview=("Artifacts", "Versions", "Checksums", "Signing", "Provenance"),
        primary_actions=("Inspect Artifact", "Verify Checksum", "Open Provenance"),
    ),
    ToolDefinition(
        id="policy-administration",
        name="Policy Administration",
        description="Publish approved policies and map them to tools, roles, tenants, and environments.",
        icon="⚑",
        route="/novacodepro/tools/policy-administration",
        required_permissions=("policy.read", "policy.publish"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Governance",
        help_url="/docs/novacodepro/tools/policy-administration",
        audit_category="policy",
        group="ADMINISTRATION",
        overview=("Policies", "Mappings", "Enforcement", "Exceptions", "Versions"),
        primary_actions=("Publish Policy", "Review Mapping", "Open Exception"),
    ),
    ToolDefinition(
        id="compliance-center",
        name="Compliance Center",
        description="Review control coverage, evidence, exceptions, and compliance posture.",
        icon="☑",
        route="/novacodepro/tools/compliance-center",
        required_permissions=("audit.read", "governance.read"),
        supported_roles=("ADMIN",),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/compliance-center",
        audit_category="compliance",
        group="GOVERN",
        overview=("Controls", "Evidence", "Exceptions", "Posture", "Reviews"),
        primary_actions=("Review Control", "Inspect Evidence", "Open Exception"),
    ),
    ToolDefinition(
        id="integration-center",
        name="Integration Center",
        description="Manage external APIs, webhooks, identities, quotas, and failures.",
        icon="⟲",
        route="/novacodepro/tools/integration-center",
        required_permissions=("integration.read", "integration.configure"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Integration Operations",
        help_url="/docs/novacodepro/tools/integration-center",
        audit_category="integration",
        group="BUSINESS",
        overview=("APIs", "Webhooks", "Credentials", "Rates", "Failures"),
        primary_actions=("Register Integration", "Rotate Secret", "Test Connection"),
    ),
    ToolDefinition(
        id="data-regional-administration",
        name="Data and Regional Administration",
        description="Configure residency, routing, replication, retention, and exports.",
        icon="◫",
        route="/novacodepro/tools/data-regional-administration",
        required_permissions=("platform.configure", "environment.configure"),
        supported_roles=("ADMIN",),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/data-regional-administration",
        audit_category="data-regional",
        group="ADMINISTRATION",
        overview=("Residency", "Routing", "Replication", "Retention", "Exports"),
        primary_actions=("Review Residency", "Verify Replication", "Open Export Request"),
    ),
    ToolDefinition(
        id="feature-configuration-center",
        name="Feature and Configuration Center",
        description="Manage feature flags, rollout rings, kill switches, and configuration history.",
        icon="☼",
        route="/novacodepro/tools/feature-configuration-center",
        required_permissions=("platform.configure", "tool.configure"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Enablement",
        help_url="/docs/novacodepro/tools/feature-configuration-center",
        audit_category="feature-config",
        group="ADMINISTRATION",
        overview=("Flags", "Rollouts", "Overrides", "History", "Rollback"),
        primary_actions=("Enable Flag", "Adjust Rollout", "Revert Change"),
    ),
    ToolDefinition(
        id="continuity-recovery-center",
        name="Continuity and Recovery Center",
        description="Test backups, failover readiness, and regional recovery plans.",
        icon="↺",
        route="/novacodepro/tools/continuity-recovery-center",
        required_permissions=("recovery.read", "recovery.execute"),
        supported_roles=("ADMIN",),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Reliability",
        help_url="/docs/novacodepro/tools/continuity-recovery-center",
        audit_category="recovery",
        group="OPERATE",
        overview=("Backups", "RTO", "RPO", "Failover", "Exercises"),
        primary_actions=("Verify Backup", "Test Restore", "Open Failover Plan"),
    ),
    ToolDefinition(
        id="administrative-diagnostics",
        name="Administrative Diagnostics",
        description="Inspect traces, logs, sync state, and configuration with redaction.",
        icon="⌘",
        route="/novacodepro/tools/administrative-diagnostics",
        required_permissions=("audit.read", "platform.read"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Diagnostics",
        help_url="/docs/novacodepro/tools/administrative-diagnostics",
        audit_category="diagnostics",
        group="ADMINISTRATION",
        overview=("Trace IDs", "Logs", "Dependencies", "Flags", "Sessions"),
        primary_actions=("Inspect Trace", "Open Log Stream", "Review Drift"),
    ),
)


ROLE_TOOL_GROUPS: dict[str, tuple[str, ...]] = {
    "ADMIN": ("HOME", "BUILD", "DELIVER", "OPERATE", "BUSINESS", "GOVERN", "LEADERSHIP", "ADMINISTRATION"),
    "DEVELOPER": ("HOME", "BUILD", "DESIGN", "DELIVER", "ASSURE", "KNOWLEDGE"),
    "PRODUCT_MANAGER": ("HOME", "STRATEGY", "DISCOVER", "PLAN", "DELIVER", "MEASURE", "KNOWLEDGE"),
    "OPERATOR": ("HOME", "DELIVER", "OPERATE", "GOVERN"),
    "VERIFIER": ("GOVERN", "OPERATE", "LEADERSHIP"),
    "CLIENT": ("HOME", "BUILD", "BUSINESS", "GOVERN"),
    "PARTNER": ("HOME", "BUILD", "BUSINESS", "GOVERN"),
    "CUSTOMER": ("HOME", "BUSINESS", "GOVERN"),
    "OBSERVER": ("HOME", "OPERATE", "GOVERN", "LEADERSHIP"),
}


ROLE_QUICK_ACTIONS: dict[str, tuple[str, ...]] = {
    "ADMIN": (
        "Open Platform Administration",
        "Open Tenant Management",
        "Open Identity and Access Center",
        "Open Application and Tool Registry",
        "Open Infrastructure and Service Center",
        "Review Pending Approvals",
        "Inspect Operations",
        "Generate Audit Export",
    ),
    "DEVELOPER": (
        "Open Developer Workspace",
        "Open Code Workspace",
        "Create Branch",
        "Run Tests",
        "Open Review Center",
        "Submit Release Request",
    ),
    "PRODUCT_MANAGER": (
        "Create product initiative",
        "Add roadmap item",
        "Write requirements",
        "Open customer insight",
        "Prioritize backlog",
        "Start discovery",
        "Review release readiness",
        "Request product approval",
        "Generate product brief",
    ),
    "OPERATOR": (
        "Open Operations Center",
        "Check Reliability",
        "Open Incident Command",
        "View Deployments",
    ),
    "VERIFIER": (
        "Review Security Center",
        "Open Risk Center",
        "Verify Evidence",
        "Resolve Approval",
    ),
    "CLIENT": (
        "Open Partner Center",
        "Review Integration",
        "Open Sandbox",
    ),
    "PARTNER": (
        "Open Partner Center",
        "Review Integration",
        "Open Sandbox",
    ),
    "CUSTOMER": (
        "Open Customer Center",
        "View Requests",
        "Check Service Health",
    ),
    "OBSERVER": (
        "Open Operations Center",
        "Open Evidence Vault",
        "Review Audit Trail",
    ),
}


def _visible_tools(role: str, environment: str) -> list[ToolDefinition]:
    canonical = canonical_role_name(role)
    return [
        tool
        for tool in TOOL_DEFINITIONS
        if environment in tool.supported_environments and canonical in tool.supported_roles
    ]


def _navigation_groups(role: str, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
    grouped: dict[str, list[ToolDefinition]] = {}
    for tool in tools:
        grouped.setdefault(tool.group, []).append(tool)
    canonical = canonical_role_name(role)
    if canonical == "DEVELOPER":
        order = ["HOME", "BUILD", "DESIGN", "DELIVER", "ASSURE", "KNOWLEDGE"]
        labels = {
            "HOME": "My Work",
            "BUILD": "Build",
            "DESIGN": "Design",
            "DELIVER": "Deliver",
            "ASSURE": "Assure",
            "KNOWLEDGE": "Knowledge",
        }
    elif canonical == "PRODUCT_MANAGER":
        order = ["HOME", "STRATEGY", "DISCOVER", "PLAN", "DELIVER", "MEASURE", "KNOWLEDGE"]
        labels = {
            "HOME": "My Work",
            "STRATEGY": "Strategy",
            "DISCOVER": "Discover",
            "PLAN": "Plan",
            "DELIVER": "Deliver",
            "MEASURE": "Measure",
            "KNOWLEDGE": "Knowledge",
        }
    else:
        order = ["HOME", "BUILD", "DESIGN", "DELIVER", "ASSURE", "KNOWLEDGE", "OPERATE", "BUSINESS", "GOVERN", "LEADERSHIP", "ADMINISTRATION"]
        labels = {
            "HOME": "Home",
            "BUILD": "Build",
            "DESIGN": "Design",
            "DELIVER": "Deliver",
            "ASSURE": "Assure",
            "KNOWLEDGE": "Knowledge",
            "OPERATE": "Operate",
            "BUSINESS": "Business",
            "GOVERN": "Govern",
            "LEADERSHIP": "Leadership",
            "ADMINISTRATION": "Administration",
        }
    groups: list[dict[str, Any]] = []
    for group in order:
        entries = grouped.get(group, [])
        if not entries:
            continue
        groups.append(
            {
                "group": group,
                "label": labels[group],
                "tools": [
                    {
                        "id": tool.id,
                        "name": tool.name,
                        "route": tool.route,
                        "icon": tool.icon,
                        "description": tool.description,
                    }
                    for tool in entries
                ],
            }
        )
    return groups


def _workspace_cards(role: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    canonical = canonical_role_name(role)
    pending_approvals = summary.get("pending_approvals", [])
    ready_release_queue = summary.get("ready_release_queue", [])
    if canonical == "ADMIN":
        return [
            {
                "title": "Platform health",
                "value": f"{summary.get('platform_health', 'healthy').title()}",
                "meta": f"{summary.get('service_health', {}).get('healthy', 0)} healthy services",
            },
            {
                "title": "Approvals requiring attention",
                "value": len(pending_approvals),
                "meta": "Production, security, policy, and customer requests",
            },
            {
                "title": "Administrator attention",
                "value": sum(
                    int(summary.get(key, 0) or 0)
                    for key in (
                        "pending_approvals_count",
                        "expiring_certificates_count",
                        "failed_backups_count",
                        "degraded_services_count",
                        "high_risk_sessions_count",
                        "policy_violations_count",
                        "unhealthy_integrations_count",
                        "configuration_drift_count",
                    )
                ) or len(ready_release_queue),
                "meta": "Privileged approvals, certificates, backups, and drift",
            },
            {
                "title": "Enterprise signals",
                "value": "Strong",
                "meta": "Security, governance, release confidence, evidence",
            },
            {
                "title": "Recent incidents",
                "value": summary.get("incident_count", 0),
                "meta": "Operational events and recovery items",
            },
            {
                "title": "Authorized tools",
                "value": len(_visible_tools(role, "production")),
                "meta": "Launchers available for your role and environment",
            },
        ]
    if canonical == "DEVELOPER":
        health = _developer_health(summary)
        return [
            {"title": "My work", "value": summary.get("workflow_statuses", {}).get("active", 0) + len(pending_approvals), "meta": "Assigned issues, active tasks, and pending reviews"},
            {"title": "Active projects", "value": summary.get("project_count", 0), "meta": "Solutions and repositories under active delivery"},
            {"title": "Engineering health", "value": health["repositories_healthy"], "meta": f"{health['open_pull_requests']} open PRs · {health['failing_pipelines']} failing pipelines"},
            {"title": "Test pass rate", "value": health["test_pass_rate"], "meta": f"Coverage {health['coverage']} · blockers {health['release_blockers']}"},
            {"title": "Security posture", "value": health["critical_vulnerabilities"], "meta": "Critical vulnerabilities in assigned scope"},
            {"title": "Tool access", "value": len(_visible_tools(role, "development")), "meta": "Authorized developer tools"},
        ]
    if canonical == "PRODUCT_MANAGER":
        health = _product_health(summary)
        return [
            {"title": "Product portfolio", "value": health["active_products"], "meta": "Assigned products and lifecycle stage"},
            {"title": "My priorities", "value": 6, "meta": "Evidence-backed roadmap, requirement, and launch work"},
            {"title": "Product health", "value": health["roadmap_confidence"], "meta": f"{health['features_on_schedule']} on schedule · {health['features_at_risk']} at risk"},
            {"title": "Customer signals", "value": health["new_feedback_items"], "meta": f"{health['critical_usability_issues']} critical usability issues · {health['adoption_trend']} adoption"},
            {"title": "Upcoming releases", "value": health["upcoming_releases"], "meta": f"{health['open_customer_escalations']} customer escalations · support trend {health['support_trend']}"},
            {"title": "Tool access", "value": len(_visible_tools(role, "business-planning")), "meta": "Authorized product tools"},
        ]
    if canonical == "OPERATOR":
        return [
            {"title": "Deployments", "value": summary.get("deployment_count", 0), "meta": "Change and rollout visibility"},
            {"title": "Incidents", "value": summary.get("incident_count", 0), "meta": "Open and recent incidents"},
            {"title": "SLOs", "value": summary.get("slo_count", 0), "meta": "Service objectives and budgets"},
            {"title": "Services", "value": summary.get("service_count", 0), "meta": "Registered platform services"},
            {"title": "Reliability", "value": summary.get("status", {}).get("platform_health", "healthy"), "meta": "Operational posture"},
            {"title": "Quick actions", "value": len(ROLE_QUICK_ACTIONS.get(canonical, ())), "meta": "Curated operator actions"},
        ]
    if canonical == "VERIFIER":
        return [
            {"title": "Security posture", "value": "Strong", "meta": "Threat, policy, and control review"},
            {"title": "Evidence bundles", "value": summary.get("evidence_bundle_count", 0), "meta": "Immutable records and attestations"},
            {"title": "Approvals", "value": len(pending_approvals), "meta": "Pending review gates"},
            {"title": "Risks", "value": summary.get("risk_count", 0), "meta": "Security and compliance exposures"},
            {"title": "Policies", "value": summary.get("policy_count", 0), "meta": "Active governance policies"},
            {"title": "Audit events", "value": summary.get("audit_event_count", 0), "meta": "Recorded governance activity"},
        ]
    if canonical in {"CLIENT", "PARTNER"}:
        return [
            {"title": "Shared projects", "value": summary.get("project_count", 0), "meta": "Owned or shared delivery work"},
            {"title": "Integration packages", "value": summary.get("integration_count", 0), "meta": "Certificates and APIs"},
            {"title": "Approvals", "value": len(pending_approvals), "meta": "Actionable items awaiting review"},
            {"title": "Evidence", "value": summary.get("evidence_bundle_count", 0), "meta": "Verification receipts and reports"},
            {"title": "Support", "value": summary.get("incident_count", 0), "meta": "Open or recent incidents"},
            {"title": "Tool access", "value": len(_visible_tools(role, "production")), "meta": "Authorized partner tools"},
        ]
    if canonical == "CUSTOMER":
        return [
            {"title": "Requests", "value": summary.get("project_count", 0), "meta": "Requests and service work"},
            {"title": "Approvals", "value": len(pending_approvals), "meta": "Customer actions needing sign-off"},
            {"title": "Deliverables", "value": summary.get("release_count", 0), "meta": "Published outputs"},
            {"title": "Evidence", "value": summary.get("evidence_bundle_count", 0), "meta": "Receipts and reports"},
            {"title": "Service health", "value": summary.get("incident_count", 0), "meta": "Customer-facing support signals"},
            {"title": "Tool access", "value": len(_visible_tools(role, "production")), "meta": "Authorized customer tools"},
        ]
    return [
        {"title": "Workspace", "value": summary.get("service_count", 0), "meta": "Workspace summaries and status"},
        {"title": "Approvals", "value": len(pending_approvals), "meta": "Items awaiting review"},
        {"title": "Work", "value": len(ready_release_queue), "meta": "Active or ready work"},
        {"title": "Evidence", "value": summary.get("evidence_bundle_count", 0), "meta": "Auditable records"},
        {"title": "Incidents", "value": summary.get("incident_count", 0), "meta": "Operational status"},
        {"title": "Tools", "value": len(_visible_tools(role, "development")), "meta": "Visible authorized launchers"},
    ]


def build_workspace_manifest(
    service: NovaCodeProPlatform,
    *,
    user_id: str,
    role: str,
    organization_id: str,
    environment: str | None = None,
) -> dict[str, Any]:
    canonical = canonical_role_name(role)
    summary = service.admin_summary()
    if environment is None:
        if canonical == "ADMIN":
            environment = "production"
        elif canonical == "DEVELOPER":
            environment = "development"
        elif canonical == "PRODUCT_MANAGER":
            environment = "business-planning"
        else:
            environment = "staging"
    environment = environment.lower()
    visible_tools = _visible_tools(canonical, environment)
    navigation_groups = _navigation_groups(canonical, visible_tools)
    profile_label = _workspace_label(canonical)
    workspace_slug = _workspace_slug(canonical)
    workspace_id = f"enterprise-{workspace_slug}"
    tool_manifest = [
        {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "icon": tool.icon,
            "route": tool.route,
            "window_route": f"/novacodepro/tools/{tool.id}",
            "permissions": list(tool.required_permissions),
            "roles": list(tool.supported_roles),
            "environments": list(tool.supported_environments),
            "health": "healthy",
            "version": tool.version,
            "ownership_team": tool.ownership_team,
            "help_url": tool.help_url,
            "audit_category": tool.audit_category,
            "group": tool.group,
            "overview": list(tool.overview),
            "primary_actions": list(tool.primary_actions),
        }
        for tool in visible_tools
    ]
    quick_actions = ROLE_QUICK_ACTIONS.get(canonical, ())
    commands = [
        {
            "id": f"open-{tool.id}",
            "label": f"Open {tool.name}",
            "description": tool.description,
            "route": tool.route,
            "requires_confirmation": tool.group in {"DELIVER", "GOVERN", "LEADERSHIP", "ADMINISTRATION"},
        }
        for tool in visible_tools
    ]
    command_labels = {item["label"] for item in commands}
    commands.extend(
        {
            "id": f"quick-{index}",
            "label": action,
            "description": "Context-aware workspace action",
            "route": None,
            "requires_confirmation": False,
        }
        for index, action in enumerate(quick_actions, start=1)
        if action not in command_labels
    )
    return {
        "user": {
            "id": user_id,
            "display_name": _display_name(user_id),
            "organization": _organization_label(organization_id),
            "organization_id": organization_id,
            "primary_role": canonical,
            "role_label": profile_label,
        },
        "workspace": {
            "id": workspace_id,
            "slug": workspace_slug,
            "home_route": f"/novacodepro/workspace/{workspace_slug}",
            "title": _workspace_title(canonical),
            "description": _workspace_description(canonical),
            "tenant": organization_id,
            "organization": _organization_label(organization_id),
            "environments": ["production", "staging", "pilot"]
            if canonical == "ADMIN"
            else (["business-planning", "staging", "pilot"] if canonical == "PRODUCT_MANAGER" else ["development", "staging", "pilot"]),
            "selected_environment": environment,
            "authority_level": "platform-admin"
            if canonical == "ADMIN"
            else ("developer" if canonical == "DEVELOPER" else ("product-manager" if canonical == "PRODUCT_MANAGER" else "role-scoped")),
            "navigation": navigation_groups,
            "tools": tool_manifest,
            "dashboard_cards": _workspace_cards(canonical, summary),
            "pending_tasks": [
                {"id": "task-1", "title": "Review active approvals", "status": "pending"},
                {"id": "task-2", "title": "Inspect current operational state", "status": "active"},
            ],
            "pending_approvals": summary.get("pending_approvals", [])[:4],
            "current_sprint": "Sprint 24" if canonical == "DEVELOPER" else None,
            "portfolio_name": "Mobility and Payments" if canonical == "PRODUCT_MANAGER" else None,
            "product_stage": "Discovery" if canonical == "PRODUCT_MANAGER" else None,
            "active_products": service.projects()[:5] if canonical == "PRODUCT_MANAGER" else (service.projects()[:5] if canonical == "DEVELOPER" else service.projects()[:4]),
            "product_health": _product_health(summary) if canonical == "PRODUCT_MANAGER" else {},
            "customer_signals": [
                {"label": "New feedback items", "value": _product_health(summary)["new_feedback_items"]},
                {"label": "Critical usability issues", "value": _product_health(summary)["critical_usability_issues"]},
                {"label": "Top requested feature", "value": _product_health(summary)["top_requested_feature"]},
                {"label": "Support trend", "value": _product_health(summary)["support_trend"]},
                {"label": "Adoption trend", "value": _product_health(summary)["adoption_trend"]},
            ]
            if canonical == "PRODUCT_MANAGER"
            else [],
            "my_priorities": [
                {"label": "Approve NovaRide pilot requirements", "status": "pending"},
                {"label": "Review NovaPay onboarding journey", "status": "active"},
                {"label": "Resolve identity-verification dependency", "status": "blocked"},
                {"label": "Confirm Q3 roadmap", "status": "review"},
                {"label": "Review public-pilot feedback", "status": "pending"},
                {"label": "Prepare executive product update", "status": "pending"},
            ]
            if canonical == "PRODUCT_MANAGER"
            else [],
            "active_projects": service.projects()[:5] if canonical in {"DEVELOPER", "PRODUCT_MANAGER"} else service.projects()[:4],
            "recent_repositories": [
                {
                    "id": f"repo-{index + 1}",
                    "name": f"{project['name'].replace(' ', '-').lower()}-repo",
                    "project": project["name"],
                    "branch": "develop" if canonical in {"DEVELOPER", "PRODUCT_MANAGER"} else "main",
                }
                for index, project in enumerate(service.projects()[:4])
            ]
            if canonical in {"DEVELOPER", "PRODUCT_MANAGER"}
            else [],
            "developer_health": _developer_health(summary) if canonical == "DEVELOPER" else {},
            "product_portfolio": [
                {"label": "NovaRide", "status": "On track"},
                {"label": "NovaPay Agent App", "status": "At risk"},
                {"label": "NovaID Federation", "status": "On track"},
                {"label": "NovaCodePro Workspace", "status": "In discovery"},
                {"label": "Customer Portal", "status": "In pilot"},
            ]
            if canonical == "PRODUCT_MANAGER"
            else [],
            "product_decisions": [
                {"label": "Approve NovaRide pilot requirements", "value": "Pending"},
                {"label": "Review NovaPay onboarding journey", "value": "In progress"},
                {"label": "Resolve identity-verification dependency", "value": "Blocked"},
                {"label": "Confirm Q3 roadmap", "value": "Review"},
            ]
            if canonical == "PRODUCT_MANAGER"
            else [],
            "developer_work_items": [
                {"label": "Assigned issues", "value": summary.get("workflow_statuses", {}).get("active", 0)},
                {"label": "Active tasks", "value": summary.get("workflow_statuses", {}).get("waiting-approval", 0) + summary.get("workflow_statuses", {}).get("paused", 0)},
                {"label": "Pull requests", "value": 12},
                {"label": "Code reviews", "value": 8},
                {"label": "Build failures", "value": _developer_health(summary)["failing_pipelines"]},
                {"label": "Test failures", "value": 1},
                {"label": "Release requests", "value": summary.get("ready_release_queue_count", len(summary.get("ready_release_queue", [])))},
                {"label": "Security findings", "value": _developer_health(summary)["critical_vulnerabilities"]},
                {"label": "Documentation tasks", "value": 4},
            ]
            if canonical == "DEVELOPER"
            else [],
            "administrator_attention": [
                {"label": "Pending privileged approvals", "value": summary.get("pending_approvals_count", len(summary.get("pending_approvals", [])))},
                {"label": "Expiring certificates", "value": summary.get("expiring_certificates_count", 0)},
                {"label": "Failed backup jobs", "value": summary.get("failed_backups_count", 0)},
                {"label": "Degraded platform services", "value": summary.get("degraded_services_count", 0)},
                {"label": "High-risk identity sessions", "value": summary.get("high_risk_sessions_count", 0)},
                {"label": "Policy violations", "value": summary.get("policy_violations_count", 0)},
                {"label": "Unhealthy integrations", "value": summary.get("unhealthy_integrations_count", 0)},
                {"label": "Configuration drift", "value": summary.get("configuration_drift_count", 0)},
            ],
            "feature_flags": {
                "role_workspace_v2": True,
                "federated_tools": True,
                "command_palette_v2": True,
                "workspace_composition_api": True,
                "executive_workspace": canonical == "ADMIN",
                "board_workspace": canonical == "ADMIN",
                "developer_workspace": canonical == "DEVELOPER",
                "product_workspace": canonical == "PRODUCT_MANAGER",
            },
            "command_palette": commands,
            "activity_timeline": (service.audit(limit=12) or service.events(limit=12))[:12],
            "enterprise_signals": {
                "platform_health": summary.get("platform_health", "healthy"),
                "service_health": summary.get("service_health", {}),
                "evidence_completeness": "97%" if canonical == "PRODUCT_MANAGER" else "98%",
                "operational_risk": "Low" if summary.get("platform_health") == "healthy" else "Attention",
            },
            "recent_projects": service.projects()[:4],
            "recent_incidents": service.operations_incidents()[:3],
            "recent_work": service.workflows()[:4],
            "support": {
                "help_url": "/docs/novacodepro/workspace",
                "command_help": "Command-K or Ctrl-K",
            },
            "audit": {
                "last_updated": _now(),
                "session_status": "active",
            },
        }
    }


def _json_payload(manifest: dict[str, Any]) -> str:
    return html.escape(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


def render_workspace_html(manifest: dict[str, Any]) -> str:
    payload = _json_payload(manifest)
    user = manifest["user"]
    workspace = manifest["workspace"]
    navigation = workspace["navigation"]
    cards = workspace["dashboard_cards"]
    tools = workspace["tools"]
    actions = workspace["command_palette"]
    approvals = workspace["pending_approvals"]
    admin_attention = workspace.get("administrator_attention", [])
    incidents = workspace["recent_incidents"]
    projects = workspace["recent_projects"]
    work = workspace["recent_work"]
    signal = workspace["enterprise_signals"]
    env = workspace["selected_environment"].title()
    tool_cards = "\n".join(
        f"""
          <a class=\"tool-card\" href=\"{html.escape(tool['route'])}\">
            <div class=\"tool-icon\">{html.escape(tool['icon'])}</div>
            <div>
              <div class=\"tool-name\">{html.escape(tool['name'])}</div>
              <div class=\"tool-description\">{html.escape(tool['description'])}</div>
              <div class=\"tool-meta\">{html.escape(tool['ownership_team'])} · {html.escape(tool['version'])}</div>
            </div>
          </a>
        """
        for tool in tools
    ) or "<div class=\"empty-state\">No authorized tools for this workspace.</div>"
    nav_groups = []
    for group in navigation:
        items = "".join(
            f"<a href=\"{html.escape(item['route'])}\"><span>{html.escape(item['icon'])}</span>{html.escape(item['name'])}</a>"
            for item in group["tools"]
        )
        nav_groups.append(f"<section><h3>{html.escape(group['label'])}</h3><div class=\"nav-group\">{items}</div></section>")
    nav_html = "\n".join(nav_groups)
    cards_html = "\n".join(
        f"""
          <article class=\"metric-card\">
            <div class=\"metric-title\">{html.escape(card['title'])}</div>
            <div class=\"metric-value\">{html.escape(str(card['value']))}</div>
            <div class=\"metric-meta\">{html.escape(str(card['meta']))}</div>
          </article>
        """
        for card in cards
    )
    approvals_html = "".join(
        f"<li><strong>{html.escape(item.get('gate_type', item.get('title', 'Approval')))}</strong><span>{html.escape(item.get('status', 'PENDING'))}</span></li>"
        for item in approvals
    ) or "<li>No approvals waiting.</li>"
    incidents_html = "".join(
        f"<li><strong>{html.escape(item.get('title', item.get('id', 'Incident')))}</strong><span>{html.escape(item.get('status', 'open'))}</span></li>"
        for item in incidents
    ) or "<li>No incidents reported.</li>"
    projects_html = "".join(
        f"<li><strong>{html.escape(item.get('name', item.get('id', 'Project')))}</strong><span>{html.escape(item.get('status', 'unknown'))}</span></li>"
        for item in projects
    ) or "<li>No projects available.</li>"
    work_html = "".join(
        f"<li><strong>{html.escape(item.get('title', item.get('id', 'Workflow')))}</strong><span>{html.escape(item.get('status', 'unknown'))}</span></li>"
        for item in work
    ) or "<li>No active work.</li>"
    command_html = "".join(
        f"""
          <button class=\"command-item\" data-command-route=\"{html.escape(str(item.get('route') or ''))}\">
            <strong>{html.escape(item['label'])}</strong>
            <span>{html.escape(item['description'])}</span>
          </button>
        """
        for item in actions
    )
    canonical = user["primary_role"]
    if canonical == "DEVELOPER":
        developer_work_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item['value']))}</span></li>"
            for item in workspace.get("developer_work_items", [])
        ) or "<li>No assigned work.</li>"
        developer_projects_html = "".join(
            f"<li><strong>{html.escape(item.get('name', item.get('id', 'Project')))}</strong><span>{html.escape(item.get('branch', 'develop'))}</span></li>"
            for item in workspace.get("active_projects", [])
        ) or "<li>No active projects.</li>"
        developer_repositories_html = "".join(
            f"<li><strong>{html.escape(item.get('name', item.get('id', 'Repository')))}</strong><span>{html.escape(item.get('project', ''))}</span></li>"
            for item in workspace.get("recent_repositories", [])
        ) or "<li>No recent repositories.</li>"
        developer_health = workspace.get("developer_health", {})
        developer_health_html = "\n".join(
            (
                f"<li><strong>Repositories healthy</strong><span>{html.escape(str(developer_health.get('repositories_healthy', '18/20')))}</span></li>",
                f"<li><strong>Open pull requests</strong><span>{html.escape(str(developer_health.get('open_pull_requests', 12)))}</span></li>",
                f"<li><strong>Failing pipelines</strong><span>{html.escape(str(developer_health.get('failing_pipelines', 2)))}</span></li>",
                f"<li><strong>Test pass rate</strong><span>{html.escape(str(developer_health.get('test_pass_rate', '98.7%')))}</span></li>",
                f"<li><strong>Coverage</strong><span>{html.escape(str(developer_health.get('coverage', '94.2%')))}</span></li>",
                f"<li><strong>Critical vulnerabilities</strong><span>{html.escape(str(developer_health.get('critical_vulnerabilities', 0)))}</span></li>",
                f"<li><strong>Release blockers</strong><span>{html.escape(str(developer_health.get('release_blockers', 3)))}</span></li>",
            )
        )
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>My work</h2></header>
              <ul>{developer_work_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Active projects</h2></header>
              <ul>{developer_projects_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Engineering health</h2></header>
              <ul>{developer_health_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent repositories</h2></header>
              <ul>{developer_repositories_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent incidents</h2></header>
              <ul>{incidents_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Enterprise signals</h2></header>
              <ul>
                <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
                <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
                <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
              </ul>
            </section>
          </div>
        """
    elif canonical == "PRODUCT_MANAGER":
        priorities_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("my_priorities", [])
        ) or "<li>No priorities assigned.</li>"
        portfolio_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("product_portfolio", [])
        ) or "<li>No products assigned.</li>"
        product_signals_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item['value']))}</span></li>"
            for item in workspace.get("customer_signals", [])
        ) or "<li>No customer signals.</li>"
        product_decisions_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['value'])}</span></li>"
            for item in workspace.get("product_decisions", [])
        ) or "<li>No recent decisions.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Product portfolio</h2></header>
              <ul>{portfolio_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>My priorities</h2></header>
              <ul>{priorities_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Customer signals</h2></header>
              <ul>{product_signals_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Product decisions</h2></header>
              <ul>{product_decisions_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Enterprise signals</h2></header>
              <ul>
                <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
                <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
                <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
              </ul>
            </section>
          </div>
        """
    else:
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Approvals</h2></header>
              <ul>{approvals_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Administrator attention</h2></header>
              <ul>
                {"".join(f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item['value']))}</span></li>" for item in admin_attention)}
              </ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent incidents</h2></header>
              <ul>{incidents_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent projects</h2></header>
              <ul>{projects_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Active work</h2></header>
              <ul>{work_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Enterprise signals</h2></header>
              <ul>
                <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
                <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
                <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
              </ul>
            </section>
          </div>
        """
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>NovaCodePro Workspace - {html.escape(workspace['title'])}</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: #081018;
        --panel: #0f1a25;
        --panel-2: #13212f;
        --line: #223040;
        --line-2: #314558;
        --text: #eff6ff;
        --muted: #99a8b8;
        --accent: #66d9ff;
        --accent-2: #4ad1a7;
        --warning: #ffb76b;
        --danger: #ff7a7a;
        --radius: 12px;
        --shadow: 0 20px 50px rgba(0,0,0,0.32);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #0a1320 0%, #081018 100%);
        color: var(--text);
      }}
      a {{ color: inherit; text-decoration: none; }}
      button, input {{ font: inherit; }}
      .shell {{
        min-height: 100vh;
        display: grid;
        grid-template-rows: auto 1fr auto;
      }}
      .topbar, .bottombar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding: 14px 20px;
        border-bottom: 1px solid var(--line);
        background: rgba(6, 12, 20, 0.92);
        backdrop-filter: blur(14px);
      }}
      .bottombar {{
        border-top: 1px solid var(--line);
        border-bottom: 0;
        font-size: 12px;
        color: var(--muted);
      }}
      .brand {{ display:flex; align-items:center; gap:14px; }}
      .brand-badge {{
        width: 38px; height: 38px; border-radius: 10px;
        display:grid; place-items:center;
        background: linear-gradient(135deg, #1f3246, #0f2537);
        border: 1px solid var(--line-2);
        font-weight: 700;
      }}
      .brand-text strong {{ display:block; font-size: 15px; letter-spacing: 0; }}
      .brand-text span, .crumbs, .context, .meta, .metric-meta, .tool-meta, .tool-description, .card-note {{
        color: var(--muted);
      }}
      .top-actions {{ display:flex; align-items:center; gap: 10px; flex-wrap: wrap; }}
      .searchbox {{
        min-width: 240px;
        border: 1px solid var(--line);
        background: var(--panel);
        color: var(--text);
        border-radius: 10px;
        padding: 10px 12px;
      }}
      .env-pill, .role-pill, .status-pill {{
        display:inline-flex; align-items:center; gap:8px;
        border: 1px solid var(--line);
        background: var(--panel);
        border-radius: 999px;
        padding: 8px 12px;
        font-size: 12px;
      }}
      .status-dot {{ width: 8px; height: 8px; border-radius: 999px; background: var(--accent-2); }}
      .workspace {{
        display:grid;
        grid-template-columns: 280px minmax(0, 1fr) 320px;
        gap: 18px;
        padding: 18px;
      }}
      .sidebar, .context-panel {{
        background: rgba(13, 21, 31, 0.92);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        overflow: hidden;
      }}
      .sidebar {{
        padding: 14px;
      }}
      .sidebar h3, .context-panel h3, .main h2, .section-title {{
        margin: 0 0 10px 0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #cfe5f7;
      }}
      .nav-group {{
        display:grid;
        gap: 6px;
        margin-bottom: 16px;
      }}
      .nav-group a {{
        display:flex; align-items:center; gap: 10px;
        padding: 10px 12px;
        border-radius: 10px;
        background: transparent;
        border: 1px solid transparent;
      }}
      .nav-group a:hover, .nav-group a:focus-visible, .tool-card:hover, .tool-card:focus-visible {{
        border-color: var(--line-2);
        background: rgba(255,255,255,0.03);
        outline: none;
      }}
      .main {{
        min-width: 0;
        display:grid;
        gap: 18px;
      }}
      .hero {{
        background: linear-gradient(180deg, rgba(20, 36, 52, 0.92), rgba(14, 24, 35, 0.92));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 22px;
        box-shadow: var(--shadow);
      }}
      .hero h1 {{ margin: 0; font-size: 34px; line-height: 1.1; }}
      .hero p {{ margin: 10px 0 0 0; max-width: 70ch; color: var(--muted); }}
      .subline {{
        display:flex; gap: 10px; flex-wrap: wrap;
        margin-top: 16px;
      }}
      .pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.03);
        font-size: 12px;
      }}
      .grid {{
        display:grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }}
      .metric-card, .panel, .tool-card {{
        background: rgba(13, 21, 31, 0.92);
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: var(--shadow);
      }}
      .metric-card {{
        padding: 14px;
        min-height: 120px;
      }}
      .metric-title {{ font-size: 13px; color: var(--muted); }}
      .metric-value {{ font-size: 28px; margin: 10px 0 6px; font-weight: 700; }}
      .metric-meta {{ font-size: 12px; }}
      .panel {{
        padding: 16px;
      }}
      .panel header {{
        display:flex; justify-content:space-between; align-items:center; gap: 12px;
        margin-bottom: 12px;
      }}
      .panel h2 {{ margin: 0; font-size: 16px; }}
      .panel ul {{
        list-style: none;
        padding: 0;
        margin: 0;
        display:grid;
        gap: 10px;
      }}
      .panel li {{
        display:flex; align-items:center; justify-content:space-between; gap: 12px;
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.04);
      }}
      .tool-grid {{
        display:grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }}
      .tool-card {{
        display:flex; align-items:flex-start; gap: 14px;
        padding: 16px;
        min-height: 110px;
      }}
      .tool-icon {{
        width: 40px; height: 40px; border-radius: 12px;
        display:grid; place-items:center;
        background: linear-gradient(180deg, rgba(102,217,255,0.14), rgba(74,209,167,0.08));
        border: 1px solid rgba(102,217,255,0.25);
        flex: 0 0 auto;
      }}
      .tool-name {{ font-weight: 700; margin-bottom: 4px; }}
      .tool-description {{ font-size: 13px; margin-bottom: 8px; }}
      .right-stack {{
        display:grid;
        gap: 14px;
      }}
      .command-bar {{
        margin-top: 16px;
        display:flex; gap: 10px; flex-wrap: wrap;
      }}
      .command-bar button, .command-item, .action-button {{
        border: 1px solid var(--line);
        border-radius: 12px;
        background: var(--panel);
        color: var(--text);
        padding: 10px 12px;
        cursor: pointer;
      }}
      .command-item {{
        width: 100%;
        text-align: left;
        display:grid;
        gap: 4px;
      }}
      .drawer {{
        border-top: 1px solid var(--line);
        padding-top: 12px;
      }}
      .empty-state {{
        padding: 18px;
        border: 1px dashed var(--line-2);
        border-radius: 14px;
        color: var(--muted);
      }}
      .modal {{
        position: fixed; inset: 0;
        display: none;
        align-items: center; justify-content: center;
        background: rgba(0,0,0,0.55);
        padding: 20px;
      }}
      .modal[data-open=\"true\"] {{ display:flex; }}
      .modal-card {{
        width: min(720px, 100%);
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px;
        box-shadow: var(--shadow);
      }}
      .command-search {{
        width: 100%;
        margin: 10px 0 14px;
        padding: 12px 14px;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: #08121a;
        color: var(--text);
      }}
      .tool-window {{
        display:grid;
        grid-template-columns: 220px minmax(0, 1fr) 280px;
        gap: 18px;
        align-items:start;
      }}
      .window-nav, .window-main, .window-side {{
        background: rgba(13, 21, 31, 0.92);
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: var(--shadow);
        padding: 16px;
      }}
      .window-nav ul, .window-side ul {{ list-style:none; padding:0; margin:0; display:grid; gap:8px; }}
      .window-nav a {{
        display:block;
        padding: 10px 12px;
        border: 1px solid transparent;
        border-radius: 10px;
        background: rgba(255,255,255,0.03);
      }}
      .window-header {{
        display:flex; justify-content:space-between; gap: 14px; align-items:flex-start; flex-wrap:wrap;
        margin-bottom: 18px;
      }}
      .window-header h2 {{ margin: 0; font-size: 28px; }}
      .window-panels {{
        display:grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }}
      .status-chip {{
        display:inline-flex; align-items:center; gap:8px;
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.03);
      }}
      @media (max-width: 1180px) {{
        .workspace, .tool-window {{
          grid-template-columns: 1fr;
        }}
        .tool-grid, .grid, .window-panels {{
          grid-template-columns: 1fr;
        }}
        .sidebar {{ order: 2; }}
        .context-panel {{ order: 3; }}
      }}
      @media (max-width: 720px) {{
        .topbar, .bottombar {{ padding: 12px 14px; }}
        .workspace {{ padding: 12px; }}
        .hero h1 {{ font-size: 28px; }}
        .searchbox {{ min-width: 0; width: 100%; }}
      }}
    </style>
  </head>
  <body>
    <div class=\"shell\">
      <header class=\"topbar\">
        <div class=\"brand\">
          <div class=\"brand-badge\">NC</div>
          <div class=\"brand-text\">
            <strong>NovaCodePro</strong>
            <span>{html.escape(user['organization'])} / {html.escape(workspace['title'])}</span>
          </div>
        </div>
        <div class=\"top-actions\">
          <input class=\"searchbox\" type=\"search\" placeholder=\"Search projects, tools, evidence, approvals\" aria-label=\"Search workspace\" />
          <span class=\"env-pill\"><span class=\"status-dot\"></span>{html.escape(env)} · Enterprise Workspace</span>
          <button class=\"action-button\" id=\"open-command\">Command K</button>
          <span class=\"role-pill\">{html.escape(user['role_label'])}</span>
          <span class=\"role-pill\">{html.escape(user['display_name'])}</span>
        </div>
      </header>
      <div class=\"workspace\">
        <aside class=\"sidebar\" aria-label=\"Role navigation\">
          <h3>Navigation</h3>
          {nav_html}
        </aside>
        <main class=\"main\">
          <section class=\"hero\">
            <div class=\"crumbs\">Workspace / {html.escape(workspace['slug'])} / {html.escape(workspace['selected_environment'])}</div>
            <h1>Good evening, {html.escape(user['display_name'])}</h1>
            <p>{html.escape(workspace['description'])}</p>
            <div class=\"subline\">
              <span class=\"pill\">Organization: {html.escape(user['organization'])}</span>
              <span class=\"pill\">Role: {html.escape(user['role_label'])}</span>
              <span class=\"pill\">Authority: {html.escape(workspace['authority_level'])}</span>
              <span class=\"pill\">Home route: {html.escape(workspace['home_route'])}</span>
            </div>
            <div class=\"command-bar\">
              <button class=\"action-button\">Open workspace</button>
              <button class=\"action-button\">Request approval</button>
              <button class=\"action-button\">Launch tool</button>
              <button class=\"action-button\">View audit</button>
            </div>
          </section>
          <section class=\"grid\" aria-label=\"Workspace summary\">
            {cards_html}
          </section>
          <section class=\"panel\">
            <header>
              <div>
                <h2>Authorized tool launcher</h2>
                <div class=\"card-note\">Only tools authorized for your role and environment are shown.</div>
              </div>
              <span class=\"status-pill\"><span class=\"status-dot\"></span>{len(tools)} tools available</span>
            </header>
            <div class=\"tool-grid\">
              {tool_cards}
            </div>
          </section>
        </main>
        <aside class=\"context-panel\">
          {right_stack_html}
        </aside>
      </div>
      <footer class=\"bottombar\">
        <div>System status: active</div>
        <div>Current context: {html.escape(user['organization'])} / {html.escape(workspace['title'])}</div>
        <div>Evidence status: available</div>
        <div>Support: {html.escape(manifest['workspace']['support']['command_help'])}</div>
        <div>Version: workspace-v2</div>
      </footer>
    </div>
    <div class=\"modal\" id=\"command-modal\" aria-hidden=\"true\">
      <div class=\"modal-card\" role=\"dialog\" aria-modal=\"true\" aria-label=\"Command palette\">
        <strong>Command palette</strong>
        <input class=\"command-search\" id=\"command-search\" type=\"search\" placeholder=\"Type a command or tool name\" />
        <div id=\"command-list\">
          {command_html}
        </div>
      </div>
    </div>
    <script>
      const modal = document.getElementById("command-modal");
      const commandButton = document.getElementById("open-command");
      const commandSearch = document.getElementById("command-search");
      const commandItems = Array.from(document.querySelectorAll(".command-item"));
      function openCommandPalette() {{
        modal.dataset.open = "true";
        modal.setAttribute("aria-hidden", "false");
        commandSearch.value = "";
        filterCommands("");
        setTimeout(() => commandSearch.focus(), 0);
      }}
      function closeCommandPalette() {{
        modal.dataset.open = "false";
        modal.setAttribute("aria-hidden", "true");
      }}
      function filterCommands(query) {{
        const needle = query.trim().toLowerCase();
        commandItems.forEach((item) => {{
          const text = item.innerText.toLowerCase();
          item.style.display = text.includes(needle) ? "" : "none";
        }});
      }}
      commandButton.addEventListener("click", openCommandPalette);
      modal.addEventListener("click", (event) => {{
        if (event.target === modal) {{
          closeCommandPalette();
        }}
      }});
      document.addEventListener("keydown", (event) => {{
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {{
          event.preventDefault();
          openCommandPalette();
        }}
        if (event.key === "Escape") {{
          closeCommandPalette();
        }}
      }});
      commandSearch.addEventListener("input", (event) => filterCommands(event.target.value));
      commandItems.forEach((item) => {{
        item.addEventListener("click", () => {{
          const route = item.dataset.commandRoute;
          if (route) {{
            window.location.href = route;
          }}
        }});
      }});
    </script>
    <script type=\"application/json\" id=\"workspace-data\">{payload}</script>
  </body>
</html>"""


def render_tool_html(manifest: dict[str, Any]) -> str:
    payload = _json_payload(manifest)
    tool = manifest["tool"]
    workspace = manifest["workspace"]
    sidebar_items = "".join(
        f"<li><a href=\"{html.escape(item['route'])}\">{html.escape(item['name'])}</a></li>"
        for item in workspace["tools"]
    )
    overview = "".join(
        f"<li><strong>{html.escape(item)}</strong><span>Available</span></li>"
        for item in tool["overview"]
    )
    actions = "".join(
        f"<button class=\"action-button\">{html.escape(item)}</button>" for item in tool["primary_actions"]
    )
    timeline = "".join(
        f"<li><strong>{html.escape(entry.get('action', entry.get('title', 'Event')))}</strong><span>{html.escape(str(entry.get('status', entry.get('at', 'recorded'))))}</span></li>"
        for entry in workspace["activity_timeline"][:6]
    )
    evidence = "".join(
        f"<li><strong>{html.escape(entry.get('id', 'evidence'))}</strong><span>{html.escape(str(entry.get('action', 'recorded')))}</span></li>"
        for entry in workspace["pending_approvals"][:4]
    )
    approvals = "".join(
        f"<li><strong>{html.escape(entry.get('gate_type', entry.get('title', 'Approval')))}</strong><span>{html.escape(entry.get('status', 'PENDING'))}</span></li>"
        for entry in workspace["pending_approvals"][:4]
    ) or "<li>No approvals required.</li>"
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{html.escape(tool['name'])} - NovaCodePro</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: #081018;
        --panel: #0f1a25;
        --line: #223040;
        --text: #eff6ff;
        --muted: #99a8b8;
        --accent: #66d9ff;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: linear-gradient(180deg, #0a1320 0%, #081018 100%); color: var(--text); }}
      a {{ color: inherit; text-decoration: none; }}
      .shell {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr auto; }}
      .topbar, .footer {{ display:flex; justify-content:space-between; align-items:center; gap: 12px; padding: 14px 20px; background: rgba(6, 12, 20, 0.92); border-bottom: 1px solid var(--line); }}
      .footer {{ border-top: 1px solid var(--line); border-bottom: 0; color: var(--muted); font-size: 12px; }}
      .workspace {{ display:grid; grid-template-columns: 220px minmax(0, 1fr) 280px; gap: 16px; padding: 16px; }}
      .nav, .main, .side {{ background: rgba(13, 21, 31, 0.92); border: 1px solid var(--line); border-radius: 16px; padding: 16px; }}
      .nav ul, .side ul, .main ul {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
      .nav a {{ display:block; padding: 10px 12px; border-radius: 10px; background: rgba(255,255,255,0.03); }}
      .header {{ display:flex; justify-content:space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }}
      .header h1 {{ margin: 0; font-size: 32px; }}
      .sub {{ color: var(--muted); margin-top: 8px; }}
      .grid {{ display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
      .panel {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 14px; }}
      .panel h2 {{ margin: 0 0 8px 0; font-size: 16px; }}
      .panel li {{ display:flex; justify-content:space-between; gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
      .panel li:last-child {{ border-bottom: 0; }}
      .action-button {{ border: 1px solid var(--line); background: #101b28; color: var(--text); padding: 10px 12px; border-radius: 12px; cursor: pointer; }}
      .tool-actions {{ display:flex; flex-wrap: wrap; gap: 10px; }}
      .status-pill {{ display:inline-flex; align-items:center; gap:8px; border:1px solid var(--line); border-radius:999px; padding:8px 12px; color: var(--muted); }}
      .status-dot {{ width: 8px; height: 8px; border-radius:999px; background: #4ad1a7; }}
      @media (max-width: 1180px) {{ .workspace {{ grid-template-columns: 1fr; }} .grid {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <div class=\"shell\">
      <header class=\"topbar\">
        <div><strong>NovaCodePro</strong> · {html.escape(tool['name'])}</div>
        <div class=\"status-pill\"><span class=\"status-dot\"></span>{html.escape(workspace['selected_environment'])} · {html.escape(workspace['organization'])}</div>
      </header>
      <div class=\"workspace\">
        <aside class=\"nav\">
          <strong>Workspace</strong>
          <ul>{sidebar_items}</ul>
        </aside>
        <main class=\"main\">
          <div class=\"header\">
            <div>
              <div class=\"sub\">{html.escape(workspace['title'])} / {html.escape(tool['ownership_team'])}</div>
              <h1>{html.escape(tool['name'])}</h1>
              <div class=\"sub\">{html.escape(tool['description'])}</div>
            </div>
            <div class=\"tool-actions\">
              {actions}
            </div>
          </div>
          <div class=\"grid\">
            <section class=\"panel\">
              <h2>Overview</h2>
              <ul>{overview}</ul>
            </section>
            <section class=\"panel\">
              <h2>Activity timeline</h2>
              <ul>{timeline}</ul>
            </section>
            <section class=\"panel\">
              <h2>Approvals</h2>
              <ul>{approvals}</ul>
            </section>
            <section class=\"panel\">
              <h2>Evidence drawer</h2>
              <ul>{evidence}</ul>
            </section>
          </div>
        </main>
        <aside class=\"side\">
          <section class=\"panel\">
            <h2>Tool metadata</h2>
            <ul>
              <li><strong>Route</strong><span>{html.escape(tool['route'])}</span></li>
              <li><strong>Permissions</strong><span>{html.escape(', '.join(tool['permissions']))}</span></li>
              <li><strong>Roles</strong><span>{html.escape(', '.join(tool['roles']))}</span></li>
              <li><strong>Version</strong><span>{html.escape(tool['version'])}</span></li>
              <li><strong>Audit</strong><span>{html.escape(tool['audit_category'])}</span></li>
            </ul>
          </section>
          <section class=\"panel\">
            <h2>Primary actions</h2>
            <ul>
              {"".join(f"<li>{html.escape(action)}</li>" for action in tool['primary_actions'])}
            </ul>
          </section>
        </aside>
      </div>
      <footer class=\"footer\">
        <div>Breadcrumb: {html.escape(workspace['title'])} / {html.escape(tool['name'])}</div>
        <div>Evidence drawer available</div>
        <div>Audit metadata: workspace-shell-v2</div>
      </footer>
    </div>
    <script type=\"application/json\" id=\"workspace-data\">{payload}</script>
  </body>
</html>"""


def build_tool_manifest(
    service: NovaCodeProPlatform,
    *,
    user_id: str,
    role: str,
    organization_id: str,
    tool_id: str,
    environment: str | None = None,
) -> dict[str, Any]:
    workspace_manifest = build_workspace_manifest(
        service,
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        environment=environment,
    )
    workspace = workspace_manifest["workspace"]
    tool = next((item for item in workspace["tools"] if item["id"] == tool_id), None)
    if tool is None:
        raise KeyError("tool_not_found")
    tool_details = next(item for item in TOOL_DEFINITIONS if item.id == tool_id)
    return {
        "user": workspace_manifest["user"],
        "workspace": workspace,
        "tool": {
            **tool,
            "overview": list(tool_details.overview),
            "primary_actions": list(tool_details.primary_actions),
        },
    }
