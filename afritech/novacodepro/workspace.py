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


ROLE_WORKSPACE_PROFILES: dict[str, dict[str, Any]] = {
    "DATA_ENGINEER": {
        "slug": "data-engineering",
        "label": "Data Engineer",
        "title": "Data Engineering Workspace",
        "description": "Build and operate governed data pipelines, streaming systems, lakehouses, warehouses, and data services.",
        "environment": "data",
        "authority": "data-engineer",
        "environments": ["data", "development", "staging", "pilot", "production"],
    },
    "DATABASE_ENGINEER": {
        "slug": "database-engineer",
        "label": "Database Engineer",
        "title": "Database Engineering Workspace",
        "description": "Provision, secure, tune, and recover the database systems that support NovaTech products and data platforms.",
        "environment": "database",
        "authority": "database-engineer",
        "environments": ["database", "development", "staging", "pilot", "production"],
    },
    "AI_ML_ENGINEER": {
        "slug": "ai-ml-engineer",
        "label": "AI/ML Engineer",
        "title": "AI Engineering Workspace",
        "description": "Build, evaluate, deploy, and govern machine-learning models, agents, and inference services.",
        "environment": "ai",
        "authority": "ai-ml-engineer",
        "environments": ["ai", "development", "staging", "pilot", "production"],
    },
    "DATA_SCIENTIST": {
        "slug": "data-scientist",
        "label": "Data Scientist",
        "title": "Data Science Workspace",
        "description": "Use trusted data, statistics, experimentation, and modeling to drive evidence-based decisions.",
        "environment": "science",
        "authority": "data-scientist",
        "environments": ["science", "development", "staging", "pilot", "production"],
    },
    "PRIVACY_COMPLIANCE": {
        "slug": "privacy-compliance",
        "label": "Privacy & Compliance",
        "title": "Privacy & Compliance Workspace",
        "description": "Govern privacy, compliance, consent, retention, AI risk, and regulatory reporting across NovaTech.",
        "environment": "compliance",
        "authority": "privacy-compliance",
        "environments": ["compliance", "staging", "pilot", "production"],
    },
    "RISK_MANAGEMENT": {
        "slug": "risk",
        "label": "Risk Management",
        "title": "Enterprise Risk Workspace",
        "description": "Identify, assess, prioritize, treat, and report risks that affect NovaTech strategy and resilience.",
        "environment": "risk",
        "authority": "risk-manager",
        "environments": ["risk", "staging", "pilot", "production"],
    },
    "EXTERNAL_REGULATOR": {
        "slug": "regulator",
        "label": "Regulator",
        "title": "Regulatory Oversight Workspace",
        "description": "Provide regulators with restricted, evidence-based oversight into NovaTech regulated activities.",
        "environment": "regulator",
        "authority": "regulator",
        "environments": ["regulator", "staging", "pilot", "production"],
    },
    "LEGAL": {
        "slug": "legal",
        "label": "Legal",
        "title": "Legal Operations Workspace",
        "description": "Protect NovaTech's rights, assets, reputation, and strategic interests through trusted legal governance.",
        "environment": "legal",
        "authority": "legal-counsel",
        "environments": ["legal", "staging", "pilot", "production"],
    },
}


def _workspace_profile(role: str) -> dict[str, Any] | None:
    return ROLE_WORKSPACE_PROFILES.get(canonical_role_name(role))


def _workspace_environments(role: str) -> list[str] | None:
    profile = _workspace_profile(role)
    if profile and "environments" in profile:
        return list(profile["environments"])
    return None


def _workspace_authority(role: str) -> str | None:
    profile = _workspace_profile(role)
    if profile:
        return str(profile["authority"])
    return None


def _workspace_slug(role: str) -> str:
    profile = _workspace_profile(role)
    if profile:
        return str(profile["slug"])
    mapping = {
        "ADMIN": "admin",
        "DEVELOPER": "developer",
        "PRODUCT_MANAGER": "product",
        "BUSINESS_ANALYST": "business-analyst",
        "UI_UX_DESIGNER": "design",
        "PROJECT_MANAGER": "project-manager",
        "ARCHITECT": "architect",
        "QA_ENGINEER": "qa-engineer",
        "DEVOPS_ENGINEER": "devops-engineer",
        "CUSTOMER_SUPPORT": "customer-support",
        "OPERATIONS_TEAM": "operations",
        "BRAND_TEAM": "brand",
        "COMPLIANCE_TEAM": "compliance",
        "AUDIT_TEAM": "audit",
        "SECURITY_ENGINEER": "security",
        "INCIDENT_RESPONSE_TEAM": "incident-response",
        "DATA_ARCHITECT": "data-architect",
        "OPERATOR": "operations",
        "VERIFIER": "security",
        "CLIENT": "partner",
        "PARTNER": "partner",
        "CUSTOMER": "customer",
        "OBSERVER": "support",
    }
    return mapping.get(canonical_role_name(role), "workspace")


def _workspace_label(role: str) -> str:
    profile = _workspace_profile(role)
    if profile:
        return str(profile["label"])
    mapping = {
        "ADMIN": "Platform Administrator",
        "DEVELOPER": "Developer",
        "PRODUCT_MANAGER": "Product Manager",
        "BUSINESS_ANALYST": "Business Analyst",
        "UI_UX_DESIGNER": "UI/UX Designer",
        "PROJECT_MANAGER": "Project Manager",
        "ARCHITECT": "Architect",
        "QA_ENGINEER": "QA Engineer",
        "DEVOPS_ENGINEER": "DevOps Engineer",
        "CUSTOMER_SUPPORT": "Customer Support",
        "OPERATIONS_TEAM": "Operations Team",
        "BRAND_TEAM": "Brand Team",
        "COMPLIANCE_TEAM": "Compliance Team",
        "AUDIT_TEAM": "Audit Team",
        "SECURITY_ENGINEER": "Security Engineer",
        "INCIDENT_RESPONSE_TEAM": "Incident Response Team",
        "DATA_ARCHITECT": "Data Architect",
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
    profile = _workspace_profile(role)
    if profile:
        return str(profile["title"])
    mapping = {
        "ADMIN": "Platform Administration Workspace",
        "DEVELOPER": "Developer Workspace",
        "PRODUCT_MANAGER": "Product Management Workspace",
        "BUSINESS_ANALYST": "Business Analysis Workspace",
        "UI_UX_DESIGNER": "Design Studio",
        "PROJECT_MANAGER": "Project Delivery Workspace",
        "ARCHITECT": "Architecture Workspace",
        "QA_ENGINEER": "Quality Engineering Workspace",
        "DEVOPS_ENGINEER": "DevOps Workspace",
        "CUSTOMER_SUPPORT": "Customer Support Workspace",
        "OPERATIONS_TEAM": "Operations Workspace",
        "BRAND_TEAM": "Brand Management Workspace",
        "COMPLIANCE_TEAM": "Compliance Workspace",
        "AUDIT_TEAM": "Audit Workspace",
        "SECURITY_ENGINEER": "Cyber Security Workspace",
        "INCIDENT_RESPONSE_TEAM": "Incident Response Workspace",
        "DATA_ARCHITECT": "Data Architecture Workspace",
        "OPERATOR": "Operations Workspace",
        "VERIFIER": "Security Workspace",
        "CLIENT": "Partner Workspace",
        "PARTNER": "Partner Workspace",
        "CUSTOMER": "Customer Workspace",
        "OBSERVER": "Support Workspace",
    }
    return mapping.get(canonical_role_name(role), "Enterprise Workspace")


def _workspace_description(role: str) -> str:
    profile = _workspace_profile(role)
    if profile:
        return str(profile["description"])
    mapping = {
        "ADMIN": "Govern platform services, tenants, identity, evidence, approvals, and operational readiness.",
        "DEVELOPER": "Turn approved requirements into secure, tested, documented, traceable, and release-ready software.",
        "PRODUCT_MANAGER": "Define the right product, prioritize the right work, align delivery teams, and ensure each release creates measurable value.",
        "BUSINESS_ANALYST": "Translate business needs into clear, testable, and traceable requirements that deliver measurable value.",
        "UI_UX_DESIGNER": "Transform business and customer requirements into accessible, consistent, user-centered experiences.",
        "PROJECT_MANAGER": "Plan, coordinate, and deliver NovaTech projects within scope, schedule, budget, quality, and governance.",
        "ARCHITECT": "Design secure, scalable, interoperable, future-ready technology architectures.",
        "QA_ENGINEER": "Verify that every solution meets functional, security, performance, accessibility, and governance requirements.",
        "DEVOPS_ENGINEER": "Automate delivery, infrastructure, observability, and operations for reliable production change.",
        "CUSTOMER_SUPPORT": "Resolve customer issues, protect customer trust, and improve service experience.",
        "OPERATIONS_TEAM": "Operate, monitor, coordinate, and continuously improve NovaTech business and technology operations.",
        "BRAND_TEAM": "Build, protect, govern, and evolve the NovaTech brand across every touchpoint.",
        "COMPLIANCE_TEAM": "Ensure NovaTech products, operations, and business processes comply with laws, regulations, contracts, and governance policies.",
        "AUDIT_TEAM": "Provide independent assurance that governance, controls, and obligations function as intended.",
        "SECURITY_ENGINEER": "Protect NovaTech platforms, identities, infrastructure, and data through proactive cybersecurity.",
        "INCIDENT_RESPONSE_TEAM": "Detect, coordinate, contain, recover, and learn from incidents across the NovaTech ecosystem.",
        "DATA_ARCHITECT": "Design and govern NovaTech's enterprise data foundations, contracts, and platform patterns.",
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


def _business_analysis_health(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_projects": int(summary.get("project_count", 8) or 8),
        "requirements_completed": int(summary.get("requirements_completed", 126) or 126),
        "pending_reviews": int(summary.get("pending_reviews", 14) or 14),
        "open_change_requests": int(summary.get("open_change_requests", 6) or 6),
        "approved_business_rules": int(summary.get("approved_business_rules", 89) or 89),
        "stakeholder_approvals": "92%",
    }


def _design_health(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "screens_designed": int(summary.get("screens_designed", 184) or 184),
        "pending_reviews": int(summary.get("pending_reviews", 12) or 12),
        "approved_components": int(summary.get("approved_components", 236) or 236),
        "accessibility_score": "96%",
        "prototype_completion": "89%",
        "design_debt": "Low",
    }


def _project_health(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "projects": int(summary.get("project_count", 12) or 12),
        "on_track": int(summary.get("projects_on_track", 8) or 8),
        "at_risk": int(summary.get("projects_at_risk", 3) or 3),
        "critical": int(summary.get("projects_critical", 1) or 1),
        "milestones_due": int(summary.get("milestones_due", 14) or 14),
        "open_risks": int(summary.get("project_risks", 21) or 21),
        "budget_utilization": "67%",
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR", "DEVOPS_ENGINEER"),
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
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR", "DEVOPS_ENGINEER"),
        supported_environments=("operations", "staging", "pilot", "production"),
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
        supported_roles=("ADMIN", "DEVELOPER", "OPERATOR", "DEVOPS_ENGINEER"),
        supported_environments=("operations", "staging", "pilot", "production"),
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
        supported_environments=("operations", "staging", "pilot", "production"),
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
        supported_environments=("operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        id="business-analysis-workspace",
        name="Business Analysis Workspace",
        description="Track initiatives, requirements, stakeholder requests, and analysis tasks.",
        icon="⌂",
        route="/novacodepro/tools/business-analysis-workspace",
        required_permissions=("requirements.read", "requirements.create"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Business Analysis",
        help_url="/docs/novacodepro/tools/business-analysis-workspace",
        audit_category="workspace",
        group="ANALYSIS",
        overview=("Initiatives", "Requirements", "Stakeholders", "Approvals", "Documents"),
        primary_actions=("Review Tasks", "Open Requirements", "Start Interview"),
    ),
    ToolDefinition(
        id="requirements-management-center",
        name="Requirements Management Center",
        description="Create and version business, functional, and non-functional requirements.",
        icon="▤",
        route="/novacodepro/tools/requirements-management-center",
        required_permissions=("requirements.read", "requirements.create", "requirements.update"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Business Analysis",
        help_url="/docs/novacodepro/tools/requirements-management-center",
        audit_category="requirements",
        group="ANALYSIS",
        overview=("BRD", "FRD", "Stories", "Criteria", "Traceability"),
        primary_actions=("Create BRD", "Submit Requirement", "Review Traceability"),
    ),
    ToolDefinition(
        id="business-process-modeling-studio",
        name="Business Process Modeling Studio",
        description="Design AS-IS and TO-BE process models, swimlanes, and BPMN flows.",
        icon="⇄",
        route="/novacodepro/tools/business-process-modeling-studio",
        required_permissions=("process.read", "process.model"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Business Process",
        help_url="/docs/novacodepro/tools/business-process-modeling-studio",
        audit_category="process",
        group="ANALYSIS",
        overview=("AS-IS", "TO-BE", "BPMN", "Swimlanes", "Optimization"),
        primary_actions=("Open Process", "Create Model", "Review Bottleneck"),
    ),
    ToolDefinition(
        id="user-story-backlog-center",
        name="User Story & Backlog Center",
        description="Create epics, stories, backlog items, and business-value priorities.",
        icon="≡",
        route="/novacodepro/tools/user-story-backlog-center",
        required_permissions=("backlog.create", "backlog.prioritize"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Delivery Planning",
        help_url="/docs/novacodepro/tools/user-story-backlog-center",
        audit_category="backlog",
        group="PLANNING",
        overview=("Epics", "Features", "Stories", "Priority", "Readiness"),
        primary_actions=("Create Story", "Prioritize Backlog", "Link Requirement"),
    ),
    ToolDefinition(
        id="business-rules-center",
        name="Business Rules Center",
        description="Define business rules, decision tables, eligibility, and approval logic.",
        icon="⚑",
        route="/novacodepro/tools/business-rules-center",
        required_permissions=("process.model", "risk.review"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Business Rules",
        help_url="/docs/novacodepro/tools/business-rules-center",
        audit_category="rules",
        group="ANALYSIS",
        overview=("Rules", "Decision Tables", "Eligibility", "Validation", "Dependencies"),
        primary_actions=("Create Rule", "Review Eligibility", "Map Compliance"),
    ),
    ToolDefinition(
        id="customer-journey-analysis",
        name="Customer Journey Analysis",
        description="Map journeys, pain points, opportunities, and service blueprints.",
        icon="⇢",
        route="/novacodepro/tools/customer-journey-analysis",
        required_permissions=("research.read", "insight.create"),
        supported_roles=("BUSINESS_ANALYST", "PRODUCT_MANAGER"),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Experience Strategy",
        help_url="/docs/novacodepro/tools/customer-journey-analysis",
        audit_category="journey",
        group="STAKEHOLDERS",
        overview=("Journeys", "Pain Points", "Opportunities", "Personas", "Blueprints"),
        primary_actions=("Map Journey", "Review Pain Point", "Open Opportunity"),
    ),
    ToolDefinition(
        id="workflow-automation-center",
        name="Workflow Automation Center",
        description="Analyze bottlenecks, automation opportunities, and ROI for process change.",
        icon="⤴",
        route="/novacodepro/tools/workflow-automation-center",
        required_permissions=("process.model", "analytics.read_aggregated"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Automation Strategy",
        help_url="/docs/novacodepro/tools/workflow-automation-center",
        audit_category="automation",
        group="PLANNING",
        overview=("Bottlenecks", "Opportunities", "ROI", "Simulation", "Optimization"),
        primary_actions=("Analyze Workflow", "Estimate ROI", "Propose Automation"),
    ),
    ToolDefinition(
        id="business-analytics-center",
        name="Business Analytics Center",
        description="Review KPIs, trends, forecasts, and business intelligence dashboards.",
        icon="↗",
        route="/novacodepro/tools/business-analytics-center",
        required_permissions=("analytics.read", "analytics.read_aggregated"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER", "PRODUCT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Business Intelligence",
        help_url="/docs/novacodepro/tools/business-analytics-center",
        audit_category="analytics",
        group="INTELLIGENCE",
        overview=("KPIs", "Trends", "Forecasts", "Conversion", "Outcomes"),
        primary_actions=("Review KPI", "Compare Trend", "Open Forecast"),
    ),
    ToolDefinition(
        id="gap-analysis-center",
        name="Gap Analysis Center",
        description="Compare current and future states across process, capability, and readiness gaps.",
        icon="⊟",
        route="/novacodepro/tools/gap-analysis-center",
        required_permissions=("requirements.read", "risk.review"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Business Transformation",
        help_url="/docs/novacodepro/tools/gap-analysis-center",
        audit_category="gap-analysis",
        group="PLANNING",
        overview=("Current State", "Future State", "Gaps", "Readiness", "Mitigation"),
        primary_actions=("Open Gap", "Review Maturity", "Propose Action"),
    ),
    ToolDefinition(
        id="business-impact-center",
        name="Business Impact Center",
        description="Assess financial, regulatory, operational, and customer impact of change.",
        icon="⚠",
        route="/novacodepro/tools/business-impact-center",
        required_permissions=("risk.review", "risk.create"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER", "PRODUCT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Business Risk",
        help_url="/docs/novacodepro/tools/business-impact-center",
        audit_category="impact",
        group="GOVERNANCE",
        overview=("Business", "Operational", "Customer", "Financial", "Regulatory"),
        primary_actions=("Assess Impact", "Review Mitigation", "Escalate Risk"),
    ),
    ToolDefinition(
        id="solution-evaluation-center",
        name="Solution Evaluation Center",
        description="Compare solution options, feasibility, costs, and benefits.",
        icon="◇",
        route="/novacodepro/tools/solution-evaluation-center",
        required_permissions=("product.read", "requirements.read"),
        supported_roles=("BUSINESS_ANALYST", "PRODUCT_MANAGER"),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Solution Strategy",
        help_url="/docs/novacodepro/tools/solution-evaluation-center",
        audit_category="solution-evaluation",
        group="PLANNING",
        overview=("Alternatives", "Feasibility", "Cost", "Benefit", "ROI"),
        primary_actions=("Compare Options", "Review Feasibility", "Open Recommendation"),
    ),
    ToolDefinition(
        id="compliance-policy-mapping",
        name="Compliance Mapping Center",
        description="Map business requirements to policies, obligations, controls, and evidence.",
        icon="☑",
        route="/novacodepro/tools/compliance-policy-mapping",
        required_permissions=("requirements.read", "governance.read"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Governance Analysis",
        help_url="/docs/novacodepro/tools/compliance-policy-mapping",
        audit_category="compliance-mapping",
        group="GOVERNANCE",
        overview=("Policies", "Obligations", "Controls", "Evidence", "Gaps"),
        primary_actions=("Map Policy", "Review Gap", "Open Evidence"),
    ),
    ToolDefinition(
        id="business-documentation-center",
        name="Business Documentation Center",
        description="Create BRDs, meeting minutes, glossaries, and business-facing documentation.",
        icon="☰",
        route="/novacodepro/tools/business-documentation-center",
        required_permissions=("documentation.write", "documentation.read"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Business Documentation",
        help_url="/docs/novacodepro/tools/business-documentation-center",
        audit_category="documentation",
        group="INTELLIGENCE",
        overview=("BRD", "FRD", "Glossary", "SOPs", "Minutes"),
        primary_actions=("Write BRD", "Publish Minutes", "Review Glossary"),
    ),
    ToolDefinition(
        id="workshop-center",
        name="Workshop Center",
        description="Plan interviews, workshops, and follow-up actions with stakeholders.",
        icon="✦",
        route="/novacodepro/tools/workshop-center",
        required_permissions=("stakeholder.manage", "documentation.write"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Program Delivery",
        help_url="/docs/novacodepro/tools/workshop-center",
        audit_category="workshop",
        group="STAKEHOLDERS",
        overview=("Workshops", "Attendance", "Actions", "Decisions", "Follow-up"),
        primary_actions=("Schedule Workshop", "Capture Notes", "Track Actions"),
    ),
    ToolDefinition(
        id="change-management-center",
        name="Change Management Center",
        description="Review scope changes, impact, approvals, and rollout planning.",
        icon="⇄",
        route="/novacodepro/tools/change-management-center",
        required_permissions=("change.request", "requirements.update"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Change Governance",
        help_url="/docs/novacodepro/tools/change-management-center",
        audit_category="change",
        group="GOVERNANCE",
        overview=("Changes", "Impact", "Approvals", "History", "Rollout"),
        primary_actions=("Submit Change", "Review Impact", "Open Approval"),
    ),
    ToolDefinition(
        id="requirements-traceability-center",
        name="Requirements Traceability Center",
        description="Trace business goals to requirements, stories, design, development, testing, and outcomes.",
        icon="⟐",
        route="/novacodepro/tools/requirements-traceability-center",
        required_permissions=("traceability.manage", "requirements.read"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER", "PRODUCT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Traceability",
        help_url="/docs/novacodepro/tools/requirements-traceability-center",
        audit_category="traceability",
        group="GOVERNANCE",
        overview=("Goals", "Requirements", "Stories", "Design", "Outcomes"),
        primary_actions=("Trace Requirement", "Inspect Coverage", "Open Outcome"),
    ),
    ToolDefinition(
        id="business-reporting-center",
        name="Business Reporting Center",
        description="Generate executive, project, KPI, risk, and compliance reports.",
        icon="▤",
        route="/novacodepro/tools/business-reporting-center",
        required_permissions=("report.generate", "analytics.read"),
        supported_roles=("BUSINESS_ANALYST", "PROJECT_MANAGER", "PRODUCT_MANAGER"),
        supported_environments=("analysis", "business-planning", "delivery", "staging", "pilot"),
        version="v1",
        ownership_team="Business Reporting",
        help_url="/docs/novacodepro/tools/business-reporting-center",
        audit_category="reporting",
        group="INTELLIGENCE",
        overview=("Executive", "Project", "KPI", "Risk", "Compliance"),
        primary_actions=("Generate Report", "Open KPI", "Export Summary"),
    ),
    ToolDefinition(
        id="novaai-business-analyst-assistant",
        name="NovaAI Business Analyst Assistant",
        description="Summarize interviews, draft BRDs, generate stories, and identify gaps.",
        icon="AI",
        route="/novacodepro/tools/novaai-business-analyst-assistant",
        required_permissions=("requirements.create", "documentation.write"),
        supported_roles=("BUSINESS_ANALYST",),
        supported_environments=("analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="AI Business Analysis",
        help_url="/docs/novacodepro/tools/novaai-business-analyst-assistant",
        audit_category="ai",
        group="INTELLIGENCE",
        overview=("Summaries", "BRD Drafts", "Stories", "Gaps", "Reports"),
        primary_actions=("Ask NovaAI", "Draft BRD", "Detect Gap"),
    ),
    ToolDefinition(
        id="design-workspace",
        name="Design Workspace",
        description="Track design projects, tasks, reviews, and accessibility progress.",
        icon="⌂",
        route="/novacodepro/tools/design-workspace",
        required_permissions=("design.read", "design.create"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Operations",
        help_url="/docs/novacodepro/tools/design-workspace",
        audit_category="workspace",
        group="DESIGN",
        overview=("Projects", "Tasks", "Reviews", "Components", "Accessibility"),
        primary_actions=("Open Project", "Review Tasks", "Inspect Accessibility"),
    ),
    ToolDefinition(
        id="wireframe-studio",
        name="Wireframe Studio",
        description="Create low-, mid-, and high-fidelity wireframes and user flow maps.",
        icon="▢",
        route="/novacodepro/tools/wireframe-studio",
        required_permissions=("wireframe.create", "design.create"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="UX Design",
        help_url="/docs/novacodepro/tools/wireframe-studio",
        audit_category="wireframe",
        group="DESIGN",
        overview=("Wireframes", "Flows", "Layouts", "Annotations", "Hierarchy"),
        primary_actions=("Create Wireframe", "Review Flow", "Open Layout"),
    ),
    ToolDefinition(
        id="visual-design-studio",
        name="Visual Design Studio",
        description="Design application screens, themes, branding, and responsive visuals.",
        icon="◼",
        route="/novacodepro/tools/visual-design-studio",
        required_permissions=("design.update", "design.create"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Visual Design",
        help_url="/docs/novacodepro/tools/visual-design-studio",
        audit_category="visual-design",
        group="DESIGN",
        overview=("Screens", "Themes", "Branding", "Responsive", "Localization"),
        primary_actions=("Design Screen", "Preview Theme", "Open Brand"),
    ),
    ToolDefinition(
        id="prototype-studio",
        name="Prototype Studio",
        description="Build clickable prototypes, transitions, and stakeholder demos.",
        icon="▷",
        route="/novacodepro/tools/prototype-studio",
        required_permissions=("prototype.create", "design.create"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Interaction Design",
        help_url="/docs/novacodepro/tools/prototype-studio",
        audit_category="prototype",
        group="DESIGN",
        overview=("Flows", "Transitions", "Variants", "Demos", "Reviews"),
        primary_actions=("Create Prototype", "Share Demo", "Review Variant"),
    ),
    ToolDefinition(
        id="user-journey-studio",
        name="User Journey Studio",
        description="Map journeys, pain points, trust moments, and accessibility gaps.",
        icon="⇢",
        route="/novacodepro/tools/user-journey-studio",
        required_permissions=("requirements.read", "requirements.create"),
        supported_roles=("PRODUCT_MANAGER", "UI_UX_DESIGNER", "BUSINESS_ANALYST"),
        supported_environments=("design", "analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Experience Strategy",
        help_url="/docs/novacodepro/tools/user-journey-studio",
        audit_category="journey",
        group="DISCOVER",
        overview=("Actors", "Stages", "Pain Points", "Trust", "Accessibility"),
        primary_actions=("Create Journey", "Review Pain Point", "Inspect Accessibility"),
    ),
    ToolDefinition(
        id="design-system-manager",
        name="NovaTech Design System",
        description="Maintain design tokens, components, breakpoints, motion, and accessibility rules.",
        icon="⚙",
        route="/novacodepro/tools/design-system-manager",
        required_permissions=("designsystem.read", "designsystem.update"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Systems",
        help_url="/docs/novacodepro/tools/design-system-manager",
        audit_category="design-system",
        group="SYSTEM",
        overview=("Tokens", "Components", "Motion", "Breakpoints", "Rules"),
        primary_actions=("Review Tokens", "Publish Component", "Open Rule"),
    ),
    ToolDefinition(
        id="component-library",
        name="Component Library",
        description="Browse, version, and publish reusable design components.",
        icon="▣",
        route="/novacodepro/tools/component-library",
        required_permissions=("component.read", "component.publish"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Systems",
        help_url="/docs/novacodepro/tools/component-library",
        audit_category="component",
        group="SYSTEM",
        overview=("Buttons", "Cards", "Tables", "Dialogs", "Forms"),
        primary_actions=("Open Component", "Preview Variant", "Publish Component"),
    ),
    ToolDefinition(
        id="responsive-design-studio",
        name="Responsive Design Studio",
        description="Preview layouts across desktop, tablet, mobile, and large displays.",
        icon="⇱",
        route="/novacodepro/tools/responsive-design-studio",
        required_permissions=("design.read", "design.update"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Product Design",
        help_url="/docs/novacodepro/tools/responsive-design-studio",
        audit_category="responsive-design",
        group="SYSTEM",
        overview=("Desktop", "Tablet", "Mobile", "Foldable", "Large Display"),
        primary_actions=("Preview Layout", "Review Breakpoint", "Open Variant"),
    ),
    ToolDefinition(
        id="accessibility-center",
        name="Accessibility Center",
        description="Review WCAG compliance, keyboard support, contrast, and motion rules.",
        icon="♿",
        route="/novacodepro/tools/accessibility-center",
        required_permissions=("accessibility.review", "design.read"),
        supported_roles=("UI_UX_DESIGNER", "PRODUCT_MANAGER", "BUSINESS_ANALYST"),
        supported_environments=("design", "analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Accessibility",
        help_url="/docs/novacodepro/tools/accessibility-center",
        audit_category="accessibility",
        group="SYSTEM",
        overview=("Contrast", "Keyboard", "Screen Reader", "Motion", "Touch Targets"),
        primary_actions=("Run Audit", "Review Issue", "Open Report"),
    ),
    ToolDefinition(
        id="ux-research-center",
        name="UX Research Center",
        description="Capture interviews, surveys, testing notes, personas, and findings.",
        icon="◔",
        route="/novacodepro/tools/ux-research-center",
        required_permissions=("research.read", "research.create"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="UX Research",
        help_url="/docs/novacodepro/tools/ux-research-center",
        audit_category="research",
        group="RESEARCH",
        overview=("Interviews", "Surveys", "Testing", "Personas", "Findings"),
        primary_actions=("Add Interview", "Open Finding", "Review Persona"),
    ),
    ToolDefinition(
        id="usability-testing-center",
        name="Usability Testing",
        description="Schedule and review usability sessions, observations, and recommendations.",
        icon="⌚",
        route="/novacodepro/tools/usability-testing-center",
        required_permissions=("research.create", "analytics.read"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="UX Research",
        help_url="/docs/novacodepro/tools/usability-testing-center",
        audit_category="usability",
        group="RESEARCH",
        overview=("Completion", "Task Time", "Errors", "Satisfaction", "Findings"),
        primary_actions=("Schedule Session", "Review Result", "Open Recommendation"),
    ),
    ToolDefinition(
        id="interaction-design-studio",
        name="Interaction Design Studio",
        description="Design micro-interactions, animations, loading states, and feedback patterns.",
        icon="◌",
        route="/novacodepro/tools/interaction-design-studio",
        required_permissions=("design.create", "design.update"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Interaction Design",
        help_url="/docs/novacodepro/tools/interaction-design-studio",
        audit_category="interaction",
        group="DESIGN",
        overview=("Motion", "Hover", "Loading", "Empty", "Error"),
        primary_actions=("Open Interaction", "Review Motion", "Preview State"),
    ),
    ToolDefinition(
        id="asset-manager",
        name="Asset Manager",
        description="Manage icons, logos, images, illustrations, fonts, and exports.",
        icon="⧉",
        route="/novacodepro/tools/asset-manager",
        required_permissions=("asset.upload", "asset.manage"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Creative Operations",
        help_url="/docs/novacodepro/tools/asset-manager",
        audit_category="asset",
        group="CREATIVE",
        overview=("Icons", "Logos", "Images", "Fonts", "Exports"),
        primary_actions=("Upload Asset", "Review Asset", "Publish Export"),
    ),
    ToolDefinition(
        id="collaboration-center",
        name="Collaboration Center",
        description="Collaborate with product, development, QA, and stakeholders on designs.",
        icon="⇄",
        route="/novacodepro/tools/collaboration-center",
        required_permissions=("design.review", "documentation.write"),
        supported_roles=("UI_UX_DESIGNER", "PRODUCT_MANAGER", "BUSINESS_ANALYST"),
        supported_environments=("design", "analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Design Collaboration",
        help_url="/docs/novacodepro/tools/collaboration-center",
        audit_category="collaboration",
        group="DELIVERY",
        overview=("Comments", "Mentions", "Versions", "Approval", "Tasks"),
        primary_actions=("Add Comment", "Request Review", "Open Version"),
    ),
    ToolDefinition(
        id="design-review-center",
        name="Design Review Center",
        description="Review design QA, brand compliance, accessibility, and handoff readiness.",
        icon="☑",
        route="/novacodepro/tools/design-review-center",
        required_permissions=("design.review", "accessibility.review"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Review",
        help_url="/docs/novacodepro/tools/design-review-center",
        audit_category="design-review",
        group="DELIVERY",
        overview=("QA", "Brand", "Accessibility", "Handoff", "History"),
        primary_actions=("Open Review", "Approve Design", "Inspect History"),
    ),
    ToolDefinition(
        id="developer-handoff-center",
        name="Developer Handoff",
        description="Generate design specs, asset exports, and implementation notes for developers.",
        icon="⟶",
        route="/novacodepro/tools/developer-handoff-center",
        required_permissions=("handoff.generate", "documentation.write"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Systems",
        help_url="/docs/novacodepro/tools/developer-handoff-center",
        audit_category="handoff",
        group="DELIVERY",
        overview=("Specs", "Assets", "Spacing", "Tokens", "Notes"),
        primary_actions=("Generate Handoff", "Export Assets", "Review Spec"),
    ),
    ToolDefinition(
        id="design-analytics",
        name="Design Analytics",
        description="Measure consistency, reuse, accessibility score, and review time.",
        icon="↗",
        route="/novacodepro/tools/design-analytics",
        required_permissions=("analytics.read", "design.read"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Analytics",
        help_url="/docs/novacodepro/tools/design-analytics",
        audit_category="analytics",
        group="RESEARCH",
        overview=("Reuse", "Consistency", "Accessibility", "Prototype", "Review Time"),
        primary_actions=("Open Metric", "Inspect Consistency", "Review Debt"),
    ),
    ToolDefinition(
        id="novaai-design-assistant",
        name="NovaAI Design Assistant",
        description="Generate wireframes, variants, UX copy, and accessibility suggestions.",
        icon="AI",
        route="/novacodepro/tools/novaai-design-assistant",
        required_permissions=("design.create", "research.create"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="AI Design",
        help_url="/docs/novacodepro/tools/novaai-design-assistant",
        audit_category="ai",
        group="CREATIVE",
        overview=("Wireframes", "Variants", "Copy", "Accessibility", "Summaries"),
        primary_actions=("Ask NovaAI", "Generate Variant", "Open Summary"),
    ),
    ToolDefinition(
        id="brand-management-center",
        name="Brand Center",
        description="Manage logos, colors, typography, branding, and regional themes.",
        icon="◆",
        route="/novacodepro/tools/brand-management-center",
        required_permissions=("designsystem.update", "asset.manage"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-management-center",
        audit_category="brand",
        group="CREATIVE",
        overview=("Brand Assets", "Colors", "Typography", "Themes", "Guidelines"),
        primary_actions=("Review Brand", "Update Theme", "Publish Asset"),
    ),
    ToolDefinition(
        id="design-documentation-center",
        name="Design Documentation",
        description="Maintain design guidelines, standards, patterns, and release notes.",
        icon="☰",
        route="/novacodepro/tools/design-documentation-center",
        required_permissions=("documentation.write", "documentation.read"),
        supported_roles=("UI_UX_DESIGNER",),
        supported_environments=("design", "staging", "pilot"),
        version="v1",
        ownership_team="Design Operations",
        help_url="/docs/novacodepro/tools/design-documentation-center",
        audit_category="documentation",
        group="DELIVERY",
        overview=("Guidelines", "Patterns", "Standards", "Notes", "Coverage"),
        primary_actions=("Write Doc", "Publish Guide", "Review Coverage"),
    ),
    ToolDefinition(
        id="project-workspace",
        name="Project Workspace",
        description="Track active projects, milestones, priorities, and project-level tasks.",
        icon="⌂",
        route="/novacodepro/tools/project-workspace",
        required_permissions=("project.read", "project.update"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Project Delivery",
        help_url="/docs/novacodepro/tools/project-workspace",
        audit_category="workspace",
        group="PROJECTS",
        overview=("Projects", "Milestones", "Tasks", "Risks", "Reports"),
        primary_actions=("Review Project", "Update Milestone", "Open RAID"),
    ),
    ToolDefinition(
        id="project-portfolio-center",
        name="Project Portfolio Center",
        description="Manage projects, portfolios, programs, and delivery lifecycle.",
        icon="▦",
        route="/novacodepro/tools/project-portfolio-center",
        required_permissions=("portfolio.read", "portfolio.manage"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Program Management",
        help_url="/docs/novacodepro/tools/project-portfolio-center",
        audit_category="portfolio",
        group="PROJECTS",
        overview=("Projects", "Programs", "Lifecycle", "Health", "Investment"),
        primary_actions=("Create Project", "Archive Project", "Compare Portfolio"),
    ),
    ToolDefinition(
        id="project-planning-center",
        name="Project Planning Center",
        description="Create charters, WBS, schedules, deliverables, and dependencies.",
        icon="↦",
        route="/novacodepro/tools/project-planning-center",
        required_permissions=("schedule.create", "schedule.update"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Planning",
        help_url="/docs/novacodepro/tools/project-planning-center",
        audit_category="planning",
        group="DELIVERY",
        overview=("Charter", "WBS", "Schedule", "Dependencies", "Timeline"),
        primary_actions=("Create Plan", "Update Schedule", "Review Critical Path"),
    ),
    ToolDefinition(
        id="resource-management-center",
        name="Resource Management Center",
        description="Assign team members, balance workloads, and forecast staffing needs.",
        icon="◫",
        route="/novacodepro/tools/resource-management-center",
        required_permissions=("resource.assign", "project.update"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Project Delivery",
        help_url="/docs/novacodepro/tools/resource-management-center",
        audit_category="resource",
        group="DELIVERY",
        overview=("Utilization", "Capacity", "Skills", "Availability", "Forecast"),
        primary_actions=("Assign Resource", "Review Utilization", "Open Forecast"),
    ),
    ToolDefinition(
        id="schedule-management-center",
        name="Schedule Management Center",
        description="Track timelines, milestones, critical path, and schedule variance.",
        icon="⏱",
        route="/novacodepro/tools/schedule-management-center",
        required_permissions=("schedule.update", "project.read"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Planning",
        help_url="/docs/novacodepro/tools/schedule-management-center",
        audit_category="schedule",
        group="DELIVERY",
        overview=("Gantt", "Milestones", "Variance", "Critical Path", "Completion"),
        primary_actions=("Update Timeline", "Review Variance", "Open Milestone"),
    ),
    ToolDefinition(
        id="budget-cost-management-center",
        name="Budget & Cost Management Center",
        description="Monitor budgets, spend, forecasts, and delegated cost approvals.",
        icon="¤",
        route="/novacodepro/tools/budget-cost-management-center",
        required_permissions=("budget.read", "budget.manage_assigned"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Finance Delivery",
        help_url="/docs/novacodepro/tools/budget-cost-management-center",
        audit_category="budget",
        group="OPERATIONS",
        overview=("Budget", "Spend", "Forecast", "Variance", "Approvals"),
        primary_actions=("Review Budget", "Open Cost Report", "Request Approval"),
    ),
    ToolDefinition(
        id="raid-management-center",
        name="RAID Management Center",
        description="Manage project risks, assumptions, issues, and dependencies.",
        icon="⚠",
        route="/novacodepro/tools/raid-management-center",
        required_permissions=("risk.create", "risk.manage"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Program Delivery",
        help_url="/docs/novacodepro/tools/raid-management-center",
        audit_category="raid",
        group="GOVERNANCE",
        overview=("Risks", "Assumptions", "Issues", "Dependencies", "Mitigation"),
        primary_actions=("Add Risk", "Review Issue", "Open Dependency"),
    ),
    ToolDefinition(
        id="milestone-center",
        name="Milestone Center",
        description="Track milestones, deliverables, evidence, and acceptance readiness.",
        icon="◆",
        route="/novacodepro/tools/milestone-center",
        required_permissions=("milestone.manage", "project.read"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Project Delivery",
        help_url="/docs/novacodepro/tools/milestone-center",
        audit_category="milestone",
        group="DELIVERY",
        overview=("Milestones", "Deliverables", "Evidence", "Acceptance", "Status"),
        primary_actions=("Update Milestone", "Review Evidence", "Open Deliverable"),
    ),
    ToolDefinition(
        id="sprint-coordination-center",
        name="Sprint Coordination Center",
        description="Coordinate sprint planning, capacity, retrospectives, and release support.",
        icon="⇄",
        route="/novacodepro/tools/sprint-coordination-center",
        required_permissions=("schedule.update", "project.update"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Agile Delivery",
        help_url="/docs/novacodepro/tools/sprint-coordination-center",
        audit_category="sprint",
        group="DELIVERY",
        overview=("Sprints", "Capacity", "Velocity", "Retro", "Release Support"),
        primary_actions=("Plan Sprint", "Review Capacity", "Open Retro"),
    ),
    ToolDefinition(
        id="change-control-center",
        name="Change Control Center",
        description="Manage change requests, impact analysis, approval workflow, and baselines.",
        icon="⇄",
        route="/novacodepro/tools/change-control-center",
        required_permissions=("change.request", "change.review"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Governance Delivery",
        help_url="/docs/novacodepro/tools/change-control-center",
        audit_category="change-control",
        group="GOVERNANCE",
        overview=("Changes", "Impact", "Approvals", "History", "Baselines"),
        primary_actions=("Submit Change", "Review Impact", "Open Baseline"),
    ),
    ToolDefinition(
        id="governance-center",
        name="Governance Center",
        description="Review project governance gates, compliance status, and audit readiness.",
        icon="☑",
        route="/novacodepro/tools/governance-center",
        required_permissions=("governance.review", "documentation.write"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Governance Delivery",
        help_url="/docs/novacodepro/tools/governance-center",
        audit_category="governance",
        group="GOVERNANCE",
        overview=("Gates", "Compliance", "Docs", "Audits", "Approvals"),
        primary_actions=("Review Gate", "Open Audit", "Confirm Readiness"),
    ),
    ToolDefinition(
        id="quality-readiness-center",
        name="Quality & Readiness Center",
        description="Monitor QA, UAT, security, operational, and deployment readiness.",
        icon="✓",
        route="/novacodepro/tools/quality-readiness-center",
        required_permissions=("project.read", "report.generate"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Assurance",
        help_url="/docs/novacodepro/tools/quality-readiness-center",
        audit_category="readiness",
        group="GOVERNANCE",
        overview=("QA", "UAT", "Security", "Operations", "Deployment"),
        primary_actions=("Review Readiness", "Open Gate", "Inspect Evidence"),
    ),
    ToolDefinition(
        id="communications-center",
        name="Communications Center",
        description="Manage status reports, team announcements, customer updates, and minutes.",
        icon="✉",
        route="/novacodepro/tools/communications-center",
        required_permissions=("documentation.write", "report.generate"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Program Communications",
        help_url="/docs/novacodepro/tools/communications-center",
        audit_category="communications",
        group="COMMUNICATION",
        overview=("Reports", "Announcements", "Updates", "Minutes", "Actions"),
        primary_actions=("Draft Update", "Publish Report", "Review Minutes"),
    ),
    ToolDefinition(
        id="vendor-partner-center",
        name="Vendor & Partner Center",
        description="Track vendors, partners, contracts, SLAs, and deliverables.",
        icon="⟲",
        route="/novacodepro/tools/vendor-partner-center",
        required_permissions=("stakeholder.manage", "report.generate"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Vendor Management",
        help_url="/docs/novacodepro/tools/vendor-partner-center",
        audit_category="vendor",
        group="OPERATIONS",
        overview=("Vendors", "Partners", "Contracts", "SLAs", "Deliverables"),
        primary_actions=("Review Vendor", "Open SLA", "Track Deliverable"),
    ),
    ToolDefinition(
        id="executive-reporting-center",
        name="Executive Reporting Center",
        description="Generate executive, portfolio, budget, risk, and KPI reports.",
        icon="▤",
        route="/novacodepro/tools/executive-reporting-center",
        required_permissions=("report.generate", "analytics.read"),
        supported_roles=("PROJECT_MANAGER", "BUSINESS_ANALYST", "PRODUCT_MANAGER"),
        supported_environments=("delivery", "analysis", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Executive Reporting",
        help_url="/docs/novacodepro/tools/executive-reporting-center",
        audit_category="reporting",
        group="COMMUNICATION",
        overview=("Executive", "Portfolio", "Budget", "Risk", "KPI"),
        primary_actions=("Generate Pack", "Open KPI", "Export Summary"),
    ),
    ToolDefinition(
        id="lessons-learned-center",
        name="Lessons Learned Center",
        description="Capture retrospectives, best practices, and reusable templates.",
        icon="✦",
        route="/novacodepro/tools/lessons-learned-center",
        required_permissions=("documentation.write", "report.generate"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Continuous Improvement",
        help_url="/docs/novacodepro/tools/lessons-learned-center",
        audit_category="lessons",
        group="OPERATIONS",
        overview=("Retrospectives", "Best Practices", "Templates", "Improvements", "Sharing"),
        primary_actions=("Capture Lesson", "Review Best Practice", "Open Template"),
    ),
    ToolDefinition(
        id="project-documentation-center",
        name="Project Documentation Center",
        description="Maintain charters, plans, RAID logs, decisions, status reports, and closures.",
        icon="☰",
        route="/novacodepro/tools/project-documentation-center",
        required_permissions=("documentation.write", "documentation.read"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Project Documentation",
        help_url="/docs/novacodepro/tools/project-documentation-center",
        audit_category="documentation",
        group="OPERATIONS",
        overview=("Charter", "Plan", "RAID", "Decisions", "Closure"),
        primary_actions=("Write Doc", "Publish Plan", "Review Closure"),
    ),
    ToolDefinition(
        id="novaai-project-assistant",
        name="NovaAI Project Assistant",
        description="Create plans, summarize meetings, forecast delays, and draft reports.",
        icon="AI",
        route="/novacodepro/tools/novaai-project-assistant",
        required_permissions=("report.generate", "project.read"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="AI Project",
        help_url="/docs/novacodepro/tools/novaai-project-assistant",
        audit_category="ai",
        group="OPERATIONS",
        overview=("Plans", "Summaries", "Risks", "Reports", "Forecasts"),
        primary_actions=("Ask NovaAI", "Draft Plan", "Open Risk"),
    ),
    ToolDefinition(
        id="project-delivery-command-center",
        name="Project Delivery Command Center",
        description="Monitor active projects, dependencies, resource utilization, and delivery confidence.",
        icon="⌘",
        route="/novacodepro/tools/project-delivery-command-center",
        required_permissions=("project.read", "analytics.read_aggregated"),
        supported_roles=("PROJECT_MANAGER",),
        supported_environments=("delivery", "business-planning", "staging", "pilot"),
        version="v1",
        ownership_team="Project Operations",
        help_url="/docs/novacodepro/tools/project-delivery-command-center",
        audit_category="command-center",
        group="PROJECTS",
        overview=("Status", "Dependencies", "Resources", "Issues", "Confidence"),
        primary_actions=("Open Project", "Inspect Issue", "Review Confidence"),
    ),
    ToolDefinition(
        id="tenant-management",
        name="Tenant Management",
        description="Create, suspend, restore, and review tenant health and isolation.",
        icon="⌂",
        route="/novacodepro/tools/tenant-management",
        required_permissions=("tenant.read", "tenant.configure"),
        supported_roles=("ADMIN",),
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
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
        supported_environments=("development", "operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Diagnostics",
        help_url="/docs/novacodepro/tools/administrative-diagnostics",
        audit_category="diagnostics",
        group="ADMINISTRATION",
        overview=("Trace IDs", "Logs", "Dependencies", "Flags", "Sessions"),
        primary_actions=("Inspect Trace", "Open Log Stream", "Review Drift"),
    ),
    ToolDefinition(
        id="architecture-workspace",
        name="Architecture Workspace",
        description="Review assigned systems, designs, risks, and architecture alignment.",
        icon="⌂",
        route="/novacodepro/tools/architecture-workspace",
        required_permissions=("architecture.read", "review.create"),
        supported_roles=("ARCHITECT",),
        supported_environments=("architecture", "staging", "pilot"),
        version="v1",
        ownership_team="Architecture",
        help_url="/docs/novacodepro/tools/architecture-workspace",
        audit_category="architecture",
        group="HOME",
        overview=("Initiatives", "Risks", "Reviews", "Diagrams", "ADRs"),
        primary_actions=("Review Design", "Open ADR", "Inspect Risk"),
    ),
    ToolDefinition(
        id="enterprise-architecture-center",
        name="Enterprise Architecture Center",
        description="Define enterprise capability maps, principles, standards, and future state.",
        icon="⌘",
        route="/novacodepro/tools/enterprise-architecture-center",
        required_permissions=("architecture.read", "standards.read"),
        supported_roles=("ARCHITECT",),
        supported_environments=("architecture", "staging", "pilot"),
        version="v1",
        ownership_team="Enterprise Architecture",
        help_url="/docs/novacodepro/tools/enterprise-architecture-center",
        audit_category="architecture",
        group="ARCHITECTURE",
        overview=("Capabilities", "Principles", "Standards", "Portfolio", "Future State"),
        primary_actions=("Open Map", "Review Standard", "Publish View"),
    ),
    ToolDefinition(
        id="solution-architecture-studio",
        name="Solution Architecture Studio",
        description="Design solution blueprints, services, integrations, and deployments.",
        icon="◆",
        route="/novacodepro/tools/solution-architecture-studio",
        required_permissions=("architecture.create", "api.design", "integration.design"),
        supported_roles=("ARCHITECT",),
        supported_environments=("architecture", "staging", "pilot"),
        version="v1",
        ownership_team="Solution Architecture",
        help_url="/docs/novacodepro/tools/solution-architecture-studio",
        audit_category="architecture",
        group="ARCHITECTURE",
        overview=("Blueprints", "Services", "Integration", "Deployment", "Runtime"),
        primary_actions=("Create Blueprint", "Review Context", "Publish Design"),
    ),
    ToolDefinition(
        id="architecture-governance-center",
        name="Architecture Governance Center",
        description="Schedule reviews, validate standards, and manage architecture exceptions.",
        icon="⚑",
        route="/novacodepro/tools/architecture-governance-center",
        required_permissions=("review.create", "standards.propose"),
        supported_roles=("ARCHITECT",),
        supported_environments=("architecture", "staging", "pilot"),
        version="v1",
        ownership_team="Architecture Governance",
        help_url="/docs/novacodepro/tools/architecture-governance-center",
        audit_category="architecture-governance",
        group="GOVERNANCE",
        overview=("Reviews", "Exceptions", "Standards", "Boards", "Compliance"),
        primary_actions=("Schedule Review", "Open Exception", "Publish Standard"),
    ),
    ToolDefinition(
        id="architecture-documentation-center",
        name="Architecture Documentation Center",
        description="Maintain reference architectures, standards, ADRs, and blueprints.",
        icon="☰",
        route="/novacodepro/tools/architecture-documentation-center",
        required_permissions=("documentation.publish", "architecture.read"),
        supported_roles=("ARCHITECT",),
        supported_environments=("architecture", "staging", "pilot"),
        version="v1",
        ownership_team="Architecture Documentation",
        help_url="/docs/novacodepro/tools/architecture-documentation-center",
        audit_category="documentation",
        group="KNOWLEDGE",
        overview=("Reference", "ADRs", "Standards", "Guides", "Roadmap"),
        primary_actions=("Publish Doc", "Open ADR", "Review Guide"),
    ),
    ToolDefinition(
        id="architecture-command-center",
        name="Architecture Command Center",
        description="Monitor architecture health, compliance, and dependency posture.",
        icon="⌘",
        route="/novacodepro/tools/architecture-command-center",
        required_permissions=("architecture.read", "analytics.read"),
        supported_roles=("ARCHITECT",),
        supported_environments=("architecture", "staging", "pilot"),
        version="v1",
        ownership_team="Architecture Operations",
        help_url="/docs/novacodepro/tools/architecture-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Landscape", "Dependencies", "Standards", "Risks", "Health"),
        primary_actions=("Inspect Topology", "Review Health", "Open Compliance"),
    ),
    ToolDefinition(
        id="quality-engineering-workspace",
        name="Quality Engineering Workspace",
        description="Track active test projects, execution status, defects, and readiness.",
        icon="⌂",
        route="/novacodepro/tools/quality-engineering-workspace",
        required_permissions=("test.read", "quality.report"),
        supported_roles=("QA_ENGINEER",),
        supported_environments=("quality", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Engineering",
        help_url="/docs/novacodepro/tools/quality-engineering-workspace",
        audit_category="quality",
        group="HOME",
        overview=("Projects", "Tests", "Defects", "Readiness", "Evidence"),
        primary_actions=("Open Test Plan", "Review Defect", "Run Suite"),
    ),
    ToolDefinition(
        id="test-management-center",
        name="Test Management Center",
        description="Create test plans, suites, cases, and execution cycles.",
        icon="☑",
        route="/novacodepro/tools/test-management-center",
        required_permissions=("test.create", "requirements.traceability.read"),
        supported_roles=("QA_ENGINEER",),
        supported_environments=("quality", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Engineering",
        help_url="/docs/novacodepro/tools/test-management-center",
        audit_category="test-management",
        group="TESTING",
        overview=("Plans", "Suites", "Cases", "Cycles", "Traceability"),
        primary_actions=("Create Plan", "Add Suite", "Open Trace"),
    ),
    ToolDefinition(
        id="automation-testing-center",
        name="Automation Testing Center",
        description="Build and run regression, API, UI, and mobile automation.",
        icon="⚙",
        route="/novacodepro/tools/automation-testing-center",
        required_permissions=("automation.manage", "test.execute"),
        supported_roles=("QA_ENGINEER",),
        supported_environments=("quality", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Automation",
        help_url="/docs/novacodepro/tools/automation-testing-center",
        audit_category="automation",
        group="TESTING",
        overview=("Regression", "API", "UI", "Mobile", "Parallel"),
        primary_actions=("Run Regression", "Open Report", "Schedule Run"),
    ),
    ToolDefinition(
        id="release-readiness-center",
        name="Release Readiness Center",
        description="Review quality gates, defect thresholds, and release recommendation evidence.",
        icon="✓",
        route="/novacodepro/tools/release-readiness-center",
        required_permissions=("release.readiness.review", "test.read"),
        supported_roles=("QA_ENGINEER",),
        supported_environments=("quality", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Release",
        help_url="/docs/novacodepro/tools/release-readiness-center",
        audit_category="release-readiness",
        group="QUALITY",
        overview=("Gates", "Defects", "Docs", "Evidence", "Recommendation"),
        primary_actions=("Review Gates", "Inspect Defects", "Recommend Release"),
    ),
    ToolDefinition(
        id="test-evidence-center",
        name="Test Evidence Center",
        description="Store screenshots, logs, videos, and signed test reports.",
        icon="✦",
        route="/novacodepro/tools/test-evidence-center",
        required_permissions=("evidence.upload", "test.read"),
        supported_roles=("QA_ENGINEER",),
        supported_environments=("quality", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Evidence",
        help_url="/docs/novacodepro/tools/test-evidence-center",
        audit_category="evidence",
        group="QUALITY",
        overview=("Screenshots", "Logs", "Videos", "Reports", "Signatures"),
        primary_actions=("Upload Evidence", "Verify Report", "Open Bundle"),
    ),
    ToolDefinition(
        id="quality-command-center",
        name="Quality Command Center",
        description="Monitor cross-product quality, defect trends, automation, and release health.",
        icon="⌘",
        route="/novacodepro/tools/quality-command-center",
        required_permissions=("quality.report", "analytics.read"),
        supported_roles=("QA_ENGINEER",),
        supported_environments=("quality", "staging", "pilot"),
        version="v1",
        ownership_team="Quality Operations",
        help_url="/docs/novacodepro/tools/quality-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Quality", "Defects", "Automation", "Readiness", "Alerts"),
        primary_actions=("Open Trend", "Review Quality", "Inspect Alert"),
    ),
    ToolDefinition(
        id="devops-workspace",
        name="DevOps Workspace",
        description="Monitor deployments, pipelines, incidents, and platform operations.",
        icon="⌂",
        route="/novacodepro/tools/devops-workspace",
        required_permissions=("deployment.read", "observability.read"),
        supported_roles=("DEVOPS_ENGINEER",),
        supported_environments=("development", "operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="DevOps",
        help_url="/docs/novacodepro/tools/devops-workspace",
        audit_category="devops",
        group="HOME",
        overview=("Deployments", "Pipelines", "Health", "Incidents", "Readiness"),
        primary_actions=("Open Deployment", "Run Pipeline", "Inspect Logs"),
    ),
    ToolDefinition(
        id="cicd-pipeline-center",
        name="CI/CD Pipeline Center",
        description="Create, execute, and analyze governed pipelines.",
        icon="⇄",
        route="/novacodepro/tools/cicd-pipeline-center",
        required_permissions=("pipeline.read", "pipeline.execute"),
        supported_roles=("DEVOPS_ENGINEER",),
        supported_environments=("development", "operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Delivery Engineering",
        help_url="/docs/novacodepro/tools/cicd-pipeline-center",
        audit_category="pipeline",
        group="DELIVERY",
        overview=("Workflows", "Approvals", "Artifacts", "Analytics", "Gates"),
        primary_actions=("Run Pipeline", "Open Workflow", "Review Gate"),
    ),
    ToolDefinition(
        id="deployment-center",
        name="Deployment Center",
        description="Execute approved releases across environments with rollback support.",
        icon="⟲",
        route="/novacodepro/tools/deployment-center",
        required_permissions=("deployment.deploy_authorized", "deployment.read"),
        supported_roles=("DEVOPS_ENGINEER",),
        supported_environments=("staging", "pilot", "production"),
        version="v1",
        ownership_team="Release Operations",
        help_url="/docs/novacodepro/tools/deployment-center",
        audit_category="deployment",
        group="DELIVERY",
        overview=("Rollout", "Rollback", "Readiness", "Evidence", "Topology"),
        primary_actions=("Deploy Release", "Pause Rollout", "Rollback"),
    ),
    ToolDefinition(
        id="observability-center",
        name="Observability Center",
        description="Monitor metrics, logs, traces, alerts, latency, and capacity.",
        icon="◌",
        route="/novacodepro/tools/observability-center",
        required_permissions=("observability.read", "analytics.read"),
        supported_roles=("DEVOPS_ENGINEER",),
        supported_environments=("development", "operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Observability",
        help_url="/docs/novacodepro/tools/observability-center",
        audit_category="observability",
        group="OPERATIONS",
        overview=("Metrics", "Logs", "Traces", "Alerts", "Latency"),
        primary_actions=("Open Dashboard", "Inspect Trace", "Review Alert"),
    ),
    ToolDefinition(
        id="environment-management-center",
        name="Environment Management Center",
        description="Provision and manage development, QA, pilot, staging, production, and DR environments.",
        icon="⌂",
        route="/novacodepro/tools/environment-management-center",
        required_permissions=("environment.manage", "environment.validate"),
        supported_roles=("DEVOPS_ENGINEER",),
        supported_environments=("development", "operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Platform Operations",
        help_url="/docs/novacodepro/tools/environment-management-center",
        audit_category="environment",
        group="RELIABILITY",
        overview=("Environments", "Health", "Drift", "Resources", "Cleanup"),
        primary_actions=("Open Environment", "Validate Config", "Compare"),
    ),
    ToolDefinition(
        id="devops-command-center",
        name="DevOps Command Center",
        description="View deployment maps, infrastructure health, release flow, and live topology.",
        icon="⌘",
        route="/novacodepro/tools/devops-command-center",
        required_permissions=("deployment.read", "analytics.read"),
        supported_roles=("DEVOPS_ENGINEER",),
        supported_environments=("development", "operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="DevOps Operations",
        help_url="/docs/novacodepro/tools/devops-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Status", "Map", "Health", "Alerts", "KPIs"),
        primary_actions=("Open Map", "Inspect Health", "Review KPI"),
    ),
    ToolDefinition(
        id="customer-support-workspace",
        name="Customer Support Workspace",
        description="Manage tickets, queues, SLAs, and customer interactions.",
        icon="⌂",
        route="/novacodepro/tools/customer-support-workspace",
        required_permissions=("ticket.read", "ticket.update"),
        supported_roles=("CUSTOMER_SUPPORT",),
        supported_environments=("support", "staging", "pilot"),
        version="v1",
        ownership_team="Customer Support",
        help_url="/docs/novacodepro/tools/customer-support-workspace",
        audit_category="support",
        group="HOME",
        overview=("Queue", "SLA", "Incidents", "Customers", "Actions"),
        primary_actions=("Open Ticket", "Search Customer", "Escalate"),
    ),
    ToolDefinition(
        id="customer-360-center",
        name="Customer 360 Center",
        description="View authorized customer profile, accounts, interactions, and support history.",
        icon="◉",
        route="/novacodepro/tools/customer-360-center",
        required_permissions=("customer.read_authorized", "identity.verify"),
        supported_roles=("CUSTOMER_SUPPORT",),
        supported_environments=("support", "staging", "pilot"),
        version="v1",
        ownership_team="Customer Intelligence",
        help_url="/docs/novacodepro/tools/customer-360-center",
        audit_category="customer",
        group="CARE",
        overview=("Identity", "Accounts", "History", "Devices", "Preferences"),
        primary_actions=("Open Profile", "Verify Identity", "Inspect History"),
    ),
    ToolDefinition(
        id="ticket-management-center",
        name="Ticket Management Center",
        description="Create, assign, triage, and close customer tickets.",
        icon="✎",
        route="/novacodepro/tools/ticket-management-center",
        required_permissions=("ticket.create", "ticket.update", "ticket.assign"),
        supported_roles=("CUSTOMER_SUPPORT",),
        supported_environments=("support", "staging", "pilot"),
        version="v1",
        ownership_team="Support Operations",
        help_url="/docs/novacodepro/tools/ticket-management-center",
        audit_category="ticket",
        group="SUPPORT",
        overview=("New", "Assigned", "Investigating", "Waiting", "Closed"),
        primary_actions=("Create Ticket", "Assign Ticket", "Close Ticket"),
    ),
    ToolDefinition(
        id="incident-communication-center",
        name="Incident Communication Center",
        description="Link tickets to incidents and send governed customer updates.",
        icon="⚠",
        route="/novacodepro/tools/incident-communication-center",
        required_permissions=("escalation.create", "analytics.read"),
        supported_roles=("CUSTOMER_SUPPORT",),
        supported_environments=("support", "staging", "pilot"),
        version="v1",
        ownership_team="Incident Communications",
        help_url="/docs/novacodepro/tools/incident-communication-center",
        audit_category="incident",
        group="OPERATIONS",
        overview=("Incidents", "Customers", "Updates", "Templates", "Impact"),
        primary_actions=("Open Incident", "Send Update", "Link Ticket"),
    ),
    ToolDefinition(
        id="support-analytics-center",
        name="Support Analytics Center",
        description="Analyze satisfaction, backlog, resolution trends, and regional support load.",
        icon="⌘",
        route="/novacodepro/tools/support-analytics-center",
        required_permissions=("analytics.read",),
        supported_roles=("CUSTOMER_SUPPORT",),
        supported_environments=("support", "staging", "pilot"),
        version="v1",
        ownership_team="Support Analytics",
        help_url="/docs/novacodepro/tools/support-analytics-center",
        audit_category="analytics",
        group="MANAGEMENT",
        overview=("CSAT", "Backlog", "SLA", "Trends", "Performance"),
        primary_actions=("Open Trend", "Review KPI", "Export Report"),
    ),
    ToolDefinition(
        id="customer-support-command-center",
        name="Customer Support Command Center",
        description="Monitor global support queue, regional status, and live support metrics.",
        icon="⌘",
        route="/novacodepro/tools/customer-support-command-center",
        required_permissions=("ticket.read", "analytics.read"),
        supported_roles=("CUSTOMER_SUPPORT",),
        supported_environments=("support", "staging", "pilot"),
        version="v1",
        ownership_team="Support Command",
        help_url="/docs/novacodepro/tools/customer-support-command-center",
        audit_category="command-center",
        group="MANAGEMENT",
        overview=("Queue", "SLA", "Incidents", "Health", "Workload"),
        primary_actions=("Inspect Queue", "Review SLA", "Open Incident"),
    ),
    ToolDefinition(
        id="operations-workspace",
        name="Operations Workspace",
        description="Track daily operations, shift status, regional workload, and executive summaries.",
        icon="⌂",
        route="/novacodepro/tools/operations-workspace",
        required_permissions=("operations.read", "operations.dashboard.read"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/operations-workspace",
        audit_category="operations",
        group="HOME",
        overview=("Operations", "Shifts", "KPIs", "Calendar", "Approvals"),
        primary_actions=("View Operations", "Open Incident", "Review Alerts"),
    ),
    ToolDefinition(
        id="operations-command-center",
        name="Operations Command Center",
        description="Monitor global operations, service health, regional activity, and business flow.",
        icon="⌘",
        route="/novacodepro/tools/operations-command-center",
        required_permissions=("operations.read", "analytics.read"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/operations-command-center",
        audit_category="command-center",
        group="OPERATIONS",
        overview=("Global View", "Regions", "Services", "Alerts", "Business Activity"),
        primary_actions=("Inspect Operations", "Review Alerts", "Open Dashboard"),
    ),
    ToolDefinition(
        id="service-operations-center",
        name="Service Operations Center",
        description="Monitor services, databases, messaging, and scheduled tasks.",
        icon="◔",
        route="/novacodepro/tools/service-operations-center",
        required_permissions=("service.monitor", "operations.read"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/service-operations-center",
        audit_category="operations",
        group="OPERATIONS",
        overview=("APIs", "Applications", "Databases", "Messaging", "Jobs"),
        primary_actions=("Monitor Service", "Open History", "Enter Maintenance"),
    ),
    ToolDefinition(
        id="incident-operations-center",
        name="Incident Operations Center",
        description="Coordinate incident response, war rooms, severity, and recovery monitoring.",
        icon="!",
        route="/novacodepro/tools/incident-operations-center",
        required_permissions=("incident.create", "incident.coordinate"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/incident-operations-center",
        audit_category="incident",
        group="COORDINATION",
        overview=("Incidents", "Severity", "War Room", "Timeline", "Recovery"),
        primary_actions=("Declare Incident", "Open War Room", "Notify Teams"),
    ),
    ToolDefinition(
        id="operational-monitoring-center",
        name="Operational Monitoring Center",
        description="Track platform health, queues, transactions, and business KPIs.",
        icon="◌",
        route="/novacodepro/tools/operational-monitoring-center",
        required_permissions=("operations.read", "analytics.read"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/operational-monitoring-center",
        audit_category="monitoring",
        group="OPERATIONS",
        overview=("Health", "KPIs", "Queues", "Transactions", "Integrations"),
        primary_actions=("Inspect Health", "Open KPI", "Review Alert"),
    ),
    ToolDefinition(
        id="business-operations-center",
        name="Business Operations Center",
        description="Manage ride, payment, identity, merchant, customer, partner, and employee operations.",
        icon="◫",
        route="/novacodepro/tools/business-operations-center",
        required_permissions=("operations.read", "operations.manage"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/business-operations-center",
        audit_category="operations",
        group="BUSINESS",
        overview=("Ride", "Payments", "Identity", "Merchants", "Customers"),
        primary_actions=("Open Business View", "Inspect Flow", "Review Escalation"),
    ),
    ToolDefinition(
        id="regional-operations-center",
        name="Regional Operations Center",
        description="Manage region-specific availability, compliance, incidents, and maintenance.",
        icon="◈",
        route="/novacodepro/tools/regional-operations-center",
        required_permissions=("operations.read", "resource.coordinate"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/regional-operations-center",
        audit_category="operations",
        group="COORDINATION",
        overview=("Regions", "KPIs", "Compliance", "Incidents", "Maintenance"),
        primary_actions=("Open Region", "Review Compliance", "Inspect Incident"),
    ),
    ToolDefinition(
        id="maintenance-change-center",
        name="Maintenance & Change Center",
        description="Schedule maintenance, govern change windows, and verify recovery readiness.",
        icon="⚑",
        route="/novacodepro/tools/maintenance-change-center",
        required_permissions=("maintenance.schedule", "operations.manage"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/maintenance-change-center",
        audit_category="change",
        group="COORDINATION",
        overview=("Maintenance", "Windows", "Outages", "Verification", "History"),
        primary_actions=("Schedule Maintenance", "Approve Window", "Review History"),
    ),
    ToolDefinition(
        id="operational-scheduling-center",
        name="Operational Scheduling Center",
        description="Plan jobs, shifts, maintenance windows, and recurring operational activities.",
        icon="🗓",
        route="/novacodepro/tools/operational-scheduling-center",
        required_permissions=("operations.manage", "resource.coordinate"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/operational-scheduling-center",
        audit_category="scheduling",
        group="COORDINATION",
        overview=("Jobs", "Shifts", "Tasks", "Calendar", "Windows"),
        primary_actions=("Schedule Job", "Adjust Shift", "Open Calendar"),
    ),
    ToolDefinition(
        id="resource-coordination-center",
        name="Resource Coordination Center",
        description="Coordinate teams, vehicles, vendors, and operational equipment.",
        icon="◎",
        route="/novacodepro/tools/resource-coordination-center",
        required_permissions=("resource.coordinate", "operations.manage"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/resource-coordination-center",
        audit_category="coordination",
        group="COORDINATION",
        overview=("Teams", "Vehicles", "Equipment", "Vendors", "Capacity"),
        primary_actions=("Assign Resource", "Review Capacity", "Open Request"),
    ),
    ToolDefinition(
        id="business-continuity-center",
        name="Business Continuity Center",
        description="Manage continuity plans, recovery readiness, and disaster recovery coordination.",
        icon="⟲",
        route="/novacodepro/tools/business-continuity-center",
        required_permissions=("continuity.manage", "operations.read"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/business-continuity-center",
        audit_category="continuity",
        group="GOVERNANCE",
        overview=("Continuity", "Recovery", "Failover", "Exercises", "Evidence"),
        primary_actions=("Open Plan", "Run Exercise", "Review Evidence"),
    ),
    ToolDefinition(
        id="operational-communications-center",
        name="Operational Communications Center",
        description="Coordinate internal announcements, customer notifications, and maintenance notices.",
        icon="✉",
        route="/novacodepro/tools/operational-communications-center",
        required_permissions=("communications.publish", "operations.manage"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/operational-communications-center",
        audit_category="communications",
        group="INTELLIGENCE",
        overview=("Announcements", "Incidents", "Maintenance", "Customers", "Partners"),
        primary_actions=("Draft Notice", "Publish Update", "Review Audience"),
    ),
    ToolDefinition(
        id="executive-operations-dashboard",
        name="Executive Operations Dashboard",
        description="Present enterprise operations KPIs, customer impact, and operational risk.",
        icon="⫶",
        route="/novacodepro/tools/executive-operations-dashboard",
        required_permissions=("operations.read", "report.generate"),
        supported_roles=("OPERATIONS_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Operations",
        help_url="/docs/novacodepro/tools/executive-operations-dashboard",
        audit_category="executive",
        group="INTELLIGENCE",
        overview=("KPIs", "Availability", "Impact", "Risk", "Alerts"),
        primary_actions=("Open KPI", "Review Risk", "Export Report"),
    ),
    ToolDefinition(
        id="brand-workspace",
        name="Brand Workspace",
        description="Track campaign status, brand health, asset approvals, and launches.",
        icon="⌂",
        route="/novacodepro/tools/brand-workspace",
        required_permissions=("brand.read", "brand.review"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-workspace",
        audit_category="brand",
        group="HOME",
        overview=("Brand", "Campaigns", "Assets", "Reviews", "Guidelines"),
        primary_actions=("Review Brand", "Open Campaign", "Approve Asset"),
    ),
    ToolDefinition(
        id="brand-identity-center",
        name="Brand Identity Center",
        description="Manage corporate identity, product branding, hierarchy, and positioning.",
        icon="◉",
        route="/novacodepro/tools/brand-identity-center",
        required_permissions=("brand.update", "brand.read"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-identity-center",
        audit_category="brand",
        group="BRAND",
        overview=("Corporate", "Products", "Hierarchy", "Positioning", "Naming"),
        primary_actions=("Update Identity", "Review Naming", "Open Hierarchy"),
    ),
    ToolDefinition(
        id="brand-guidelines-center",
        name="Brand Guidelines Center",
        description="Maintain logo usage, typography, color, tone, localization, and accessibility guidance.",
        icon="⚑",
        route="/novacodepro/tools/brand-guidelines-center",
        required_permissions=("brand.update", "documentation.write"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-guidelines-center",
        audit_category="brand",
        group="BRAND",
        overview=("Logo", "Typography", "Color", "Tone", "Localization"),
        primary_actions=("Publish Guideline", "Review Usage", "Open Standard"),
    ),
    ToolDefinition(
        id="digital-asset-management",
        name="Digital Asset Management",
        description="Search, approve, version, and distribute approved brand assets.",
        icon="▣",
        route="/novacodepro/tools/digital-asset-management",
        required_permissions=("asset.upload", "asset.publish"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/digital-asset-management",
        audit_category="asset",
        group="MARKETING",
        overview=("Logos", "Templates", "Photos", "Videos", "License"),
        primary_actions=("Upload Asset", "Review Rights", "Publish Kit"),
    ),
    ToolDefinition(
        id="campaign-management-center",
        name="Campaign Management Center",
        description="Plan and govern brand, product, regional, and social campaigns.",
        icon="✎",
        route="/novacodepro/tools/campaign-management-center",
        required_permissions=("campaign.create", "campaign.manage"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/campaign-management-center",
        audit_category="campaign",
        group="MARKETING",
        overview=("Campaigns", "Launches", "Budget", "Performance", "Approvals"),
        primary_actions=("Create Campaign", "Review Launch", "Inspect Performance"),
    ),
    ToolDefinition(
        id="brand-compliance-center",
        name="Brand Compliance Center",
        description="Scan websites, mobile apps, and materials for brand and accessibility compliance.",
        icon="✓",
        route="/novacodepro/tools/brand-compliance-center",
        required_permissions=("brand.review", "analytics.read"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-compliance-center",
        audit_category="compliance",
        group="GOVERNANCE",
        overview=("Website", "Mobile", "Materials", "Issues", "Score"),
        primary_actions=("Run Scan", "Review Issue", "Open Report"),
    ),
    ToolDefinition(
        id="digital-experience-center",
        name="Website & Digital Experience Center",
        description="Review brand consistency across websites, portals, apps, and landing pages.",
        icon="◌",
        route="/novacodepro/tools/digital-experience-center",
        required_permissions=("brand.review", "design.read"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/digital-experience-center",
        audit_category="experience",
        group="EXPERIENCE",
        overview=("Websites", "Portals", "Apps", "Navigation", "Accessibility"),
        primary_actions=("Review Site", "Open Portal", "Inspect Accessibility"),
    ),
    ToolDefinition(
        id="brand-analytics-center",
        name="Brand Analytics Center",
        description="Analyze awareness, engagement, consistency, sentiment, and reach.",
        icon="⌘",
        route="/novacodepro/tools/brand-analytics-center",
        required_permissions=("analytics.read", "brand.read"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-analytics-center",
        audit_category="analytics",
        group="INTELLIGENCE",
        overview=("Awareness", "Engagement", "Sentiment", "Traffic", "Score"),
        primary_actions=("Open Trend", "Inspect Sentiment", "Export Report"),
    ),
    ToolDefinition(
        id="brand-command-center",
        name="Brand Command Center",
        description="Monitor brand compliance, campaign flow, approvals, and public sentiment.",
        icon="⫶",
        route="/novacodepro/tools/brand-command-center",
        required_permissions=("brand.read", "analytics.read"),
        supported_roles=("BRAND_TEAM", "ADMIN"),
        supported_environments=("marketing", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Brand",
        help_url="/docs/novacodepro/tools/brand-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Brand Health", "Campaigns", "Assets", "Sentiment", "Approvals"),
        primary_actions=("Open Dashboard", "Review Brand", "Inspect Alert"),
    ),
    ToolDefinition(
        id="compliance-workspace",
        name="Compliance Workspace",
        description="Track obligations, reviews, findings, and regulatory tasks.",
        icon="⌂",
        route="/novacodepro/tools/compliance-workspace",
        required_permissions=("compliance.read", "compliance.review"),
        supported_roles=("COMPLIANCE_TEAM", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/compliance-workspace",
        audit_category="compliance",
        group="HOME",
        overview=("Compliance", "Audits", "Findings", "Reviews", "Tasks"),
        primary_actions=("Open Review", "Inspect Finding", "Run Report"),
    ),
    ToolDefinition(
        id="regulatory-compliance-center",
        name="Regulatory Compliance Center",
        description="Manage legal and regulatory obligations across products and regions.",
        icon="⚑",
        route="/novacodepro/tools/regulatory-compliance-center",
        required_permissions=("compliance.review", "regulatory.reporting"),
        supported_roles=("COMPLIANCE_TEAM", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/regulatory-compliance-center",
        audit_category="regulatory",
        group="COMPLIANCE",
        overview=("Obligations", "Regions", "Reviews", "Reports", "Alerts"),
        primary_actions=("Open Obligation", "Review Region", "Generate Report"),
    ),
    ToolDefinition(
        id="policy-management-center",
        name="Policy Management Center",
        description="Draft, review, publish, and track policy versions and acknowledgements.",
        icon="✎",
        route="/novacodepro/tools/policy-management-center",
        required_permissions=("policy.create", "policy.publish"),
        supported_roles=("COMPLIANCE_TEAM", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/policy-management-center",
        audit_category="policy",
        group="GOVERNANCE",
        overview=("Drafts", "Versions", "Acknowledgements", "Exceptions", "History"),
        primary_actions=("Draft Policy", "Publish Policy", "Review Acknowledgement"),
    ),
    ToolDefinition(
        id="audit-management-center",
        name="Audit Management Center",
        description="Plan and manage audits, findings, corrective actions, and reports.",
        icon="◈",
        route="/novacodepro/tools/audit-management-center",
        required_permissions=("audit.create", "audit.manage"),
        supported_roles=("COMPLIANCE_TEAM", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/audit-management-center",
        audit_category="audit",
        group="ASSURANCE",
        overview=("Audits", "Findings", "Actions", "Reports", "Schedules"),
        primary_actions=("Start Audit", "Review Evidence", "Open Report"),
    ),
    ToolDefinition(
        id="evidence-records-center",
        name="Evidence & Records Center",
        description="Maintain evidence packages, immutable records, and acknowledgements.",
        icon="⧉",
        route="/novacodepro/tools/evidence-records-center",
        required_permissions=("evidence.read", "report.generate"),
        supported_roles=("COMPLIANCE_TEAM", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/evidence-records-center",
        audit_category="evidence",
        group="ASSURANCE",
        overview=("Evidence", "Records", "Approvals", "Retention", "Holds"),
        primary_actions=("Open Evidence", "Verify Record", "Export Report"),
    ),
    ToolDefinition(
        id="compliance-command-center",
        name="Compliance Command Center",
        description="Track compliance score, obligations, investigations, and board reporting.",
        icon="⫶",
        route="/novacodepro/tools/compliance-command-center",
        required_permissions=("compliance.read", "analytics.read"),
        supported_roles=("COMPLIANCE_TEAM", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Compliance",
        help_url="/docs/novacodepro/tools/compliance-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Score", "Audits", "Findings", "Investigations", "Board"),
        primary_actions=("Open Dashboard", "Review Finding", "Export Brief"),
    ),
    ToolDefinition(
        id="audit-workspace",
        name="Audit Workspace",
        description="Review assigned audits, evidence, findings, and corrective actions.",
        icon="⌂",
        route="/novacodepro/tools/audit-workspace",
        required_permissions=("audit.read", "evidence.read"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/audit-workspace",
        audit_category="audit",
        group="HOME",
        overview=("Audits", "Findings", "Actions", "Evidence", "Packs"),
        primary_actions=("Start Audit", "Review Evidence", "Open Finding"),
    ),
    ToolDefinition(
        id="audit-planning-center",
        name="Audit Planning Center",
        description="Create annual plans, scopes, objectives, and audit programs.",
        icon="🗓",
        route="/novacodepro/tools/audit-planning-center",
        required_permissions=("audit.plan.manage", "audit.create"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/audit-planning-center",
        audit_category="audit",
        group="AUDIT",
        overview=("Plan", "Scope", "Objectives", "Calendar", "Approval"),
        primary_actions=("Create Plan", "Set Scope", "Schedule Review"),
    ),
    ToolDefinition(
        id="audit-execution-center",
        name="Audit Execution Center",
        description="Perform fieldwork for operational, financial, technology, and security audits.",
        icon="◔",
        route="/novacodepro/tools/audit-execution-center",
        required_permissions=("audit.execute", "audit.read"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/audit-execution-center",
        audit_category="audit",
        group="AUDIT",
        overview=("Fieldwork", "Testing", "Observations", "Evidence", "Workpapers"),
        primary_actions=("Open Workpaper", "Review Test", "Add Finding"),
    ),
    ToolDefinition(
        id="evidence-verification-center",
        name="Evidence Verification Center",
        description="Verify integrity, signatures, timestamps, and chain of custody.",
        icon="⧉",
        route="/novacodepro/tools/evidence-verification-center",
        required_permissions=("evidence.verify", "evidence.read"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/evidence-verification-center",
        audit_category="evidence",
        group="ASSURANCE",
        overview=("Integrity", "Signatures", "Timestamps", "Chain", "Status"),
        primary_actions=("Verify Bundle", "Inspect Signature", "Open Receipt"),
    ),
    ToolDefinition(
        id="audit-findings-center",
        name="Audit Findings Center",
        description="Manage audit observations, risk ratings, responses, and escalations.",
        icon="⚠",
        route="/novacodepro/tools/audit-findings-center",
        required_permissions=("finding.create", "finding.update"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/audit-findings-center",
        audit_category="audit",
        group="AUDIT",
        overview=("Critical", "High", "Medium", "Low", "Responses"),
        primary_actions=("Create Finding", "Review Response", "Escalate"),
    ),
    ToolDefinition(
        id="corrective-action-center",
        name="Corrective Action Center",
        description="Track owners, due dates, verification, and closure of corrective actions.",
        icon="✓",
        route="/novacodepro/tools/corrective-action-center",
        required_permissions=("correctiveaction.review", "audit.read"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/corrective-action-center",
        audit_category="audit",
        group="ASSURANCE",
        overview=("Actions", "Owners", "Due Dates", "Verification", "Closure"),
        primary_actions=("Open Action", "Verify Closure", "Escalate Delay"),
    ),
    ToolDefinition(
        id="audit-analytics-center",
        name="Audit Analytics Center",
        description="Analyze coverage, findings, repeat issues, and regional assurance trends.",
        icon="⌘",
        route="/novacodepro/tools/audit-analytics-center",
        required_permissions=("analytics.read", "audit.read"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/audit-analytics-center",
        audit_category="analytics",
        group="INTELLIGENCE",
        overview=("Coverage", "Findings", "Actions", "Trends", "Heatmap"),
        primary_actions=("Open Trend", "Review KPI", "Export Report"),
    ),
    ToolDefinition(
        id="audit-committee-center",
        name="Audit Committee Center",
        description="Prepare committee packs, opinions, responses, and recommendations.",
        icon="⫶",
        route="/novacodepro/tools/audit-committee-center",
        required_permissions=("committee.report", "report.generate"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/audit-committee-center",
        audit_category="committee",
        group="INTELLIGENCE",
        overview=("Packs", "Responses", "Opinions", "Actions", "Board"),
        primary_actions=("Prepare Pack", "Review Opinion", "Export Summary"),
    ),
    ToolDefinition(
        id="enterprise-audit-command-center",
        name="Enterprise Audit Command Center",
        description="View enterprise assurance coverage, findings, and corrective action status.",
        icon="⌘",
        route="/novacodepro/tools/enterprise-audit-command-center",
        required_permissions=("audit.read", "analytics.read"),
        supported_roles=("AUDIT_TEAM", "ADMIN"),
        supported_environments=("audit", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Audit",
        help_url="/docs/novacodepro/tools/enterprise-audit-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Coverage", "Findings", "Controls", "Actions", "Board"),
        primary_actions=("Open Dashboard", "Inspect Control", "Export Brief"),
    ),
    ToolDefinition(
        id="security-workspace",
        name="Security Workspace",
        description="Track security posture, investigations, vulnerabilities, and control status.",
        icon="⌂",
        route="/novacodepro/tools/security-workspace",
        required_permissions=("security.read", "security.monitor"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/security-workspace",
        audit_category="security",
        group="HOME",
        overview=("Security", "Alerts", "Vulnerabilities", "Incidents", "Controls"),
        primary_actions=("Investigate Alert", "Review Vulnerability", "Open SIEM"),
    ),
    ToolDefinition(
        id="security-operations-center",
        name="Security Operations Center",
        description="Monitor threats, anomalies, alerts, and incident response flow.",
        icon="◔",
        route="/novacodepro/tools/security-operations-center",
        required_permissions=("security.monitor", "incident.manage"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/security-operations-center",
        audit_category="security",
        group="SECURITY",
        overview=("Threats", "Alerts", "Intrusions", "Identity", "Cases"),
        primary_actions=("Triage Alert", "Open Case", "Hunt Threat"),
    ),
    ToolDefinition(
        id="iam-center",
        name="Identity & Access Management Center",
        description="Manage identities, MFA, passkeys, SSO, federation, and sessions.",
        icon="◉",
        route="/novacodepro/tools/iam-center",
        required_permissions=("identity.manage", "security.read"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/iam-center",
        audit_category="identity",
        group="SECURITY",
        overview=("Users", "MFA", "Passkeys", "Federation", "Sessions"),
        primary_actions=("Review Identity", "Inspect Session", "Open Federation"),
    ),
    ToolDefinition(
        id="zero-trust-center",
        name="Zero Trust Center",
        description="Implement conditional access, device trust, and least-privilege policies.",
        icon="⚑",
        route="/novacodepro/tools/zero-trust-center",
        required_permissions=("security.policy.review", "security.read"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/zero-trust-center",
        audit_category="security",
        group="PROTECTION",
        overview=("Trust", "Policies", "Access", "Devices", "Risk"),
        primary_actions=("Review Policy", "Open Access", "Inspect Trust"),
    ),
    ToolDefinition(
        id="vulnerability-management-center",
        name="Vulnerability Management Center",
        description="Track CVEs, remediation, patch status, and risk prioritization.",
        icon="⚠",
        route="/novacodepro/tools/vulnerability-management-center",
        required_permissions=("vulnerability.manage", "security.read"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/vulnerability-management-center",
        audit_category="vulnerability",
        group="PROTECTION",
        overview=("CVE", "Exposure", "Remediation", "Patch", "SLA"),
        primary_actions=("Open Vulnerability", "Review SLA", "Assign Remediation"),
    ),
    ToolDefinition(
        id="application-security-center",
        name="Application Security Center",
        description="Review SAST, DAST, SCA, secrets, and API security findings.",
        icon="</>",
        route="/novacodepro/tools/application-security-center",
        required_permissions=("security.scan", "security.read"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/application-security-center",
        audit_category="application-security",
        group="PROTECTION",
        overview=("Source", "APIs", "Mobile", "Dependencies", "Findings"),
        primary_actions=("Run Scan", "Inspect Finding", "Open Remediation"),
    ),
    ToolDefinition(
        id="incident-response-center",
        name="Security Incident Response Center",
        description="Coordinate containment, eradication, recovery, and evidence preservation.",
        icon="!",
        route="/novacodepro/tools/incident-response-center",
        required_permissions=("incident.manage", "security.read"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/incident-response-center",
        audit_category="incident",
        group="DETECTION",
        overview=("Incidents", "Containment", "Forensics", "Recovery", "Evidence"),
        primary_actions=("Open Incident", "Contain Threat", "Preserve Evidence"),
    ),
    ToolDefinition(
        id="siem-log-analytics-center",
        name="SIEM & Log Analytics Center",
        description="Correlate security logs, alerts, and detections across the platform.",
        icon="◌",
        route="/novacodepro/tools/siem-log-analytics-center",
        required_permissions=("siem.read", "security.monitor"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/siem-log-analytics-center",
        audit_category="siem",
        group="DETECTION",
        overview=("Logs", "Alerts", "Rules", "Cases", "Dashboards"),
        primary_actions=("Open SIEM", "Review Detection", "Export Log"),
    ),
    ToolDefinition(
        id="security-command-center",
        name="Enterprise Security Command Center",
        description="Present enterprise security posture, identity risk, and board reporting.",
        icon="⫶",
        route="/novacodepro/tools/security-command-center",
        required_permissions=("security.read", "security.report"),
        supported_roles=("SECURITY_ENGINEER", "ADMIN"),
        supported_environments=("security", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Security",
        help_url="/docs/novacodepro/tools/security-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Posture", "Alerts", "Vulnerabilities", "Identity", "Board"),
        primary_actions=("Open Dashboard", "Review Posture", "Export Report"),
    ),
    ToolDefinition(
        id="incident-response-workspace",
        name="Incident Response Workspace",
        description="Track incident queues, responders, recovery progress, and shift status.",
        icon="⌂",
        route="/novacodepro/tools/incident-response-workspace",
        required_permissions=("incident.read", "incident.manage"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/incident-response-workspace",
        audit_category="incident",
        group="HOME",
        overview=("Incidents", "Responders", "Shifts", "Recovery", "Communications"),
        primary_actions=("Declare Incident", "Open Bridge", "Review Timeline"),
    ),
    ToolDefinition(
        id="incident-command-center",
        name="Incident Command Center",
        description="Assign commanders, manage timelines, and coordinate live response.",
        icon="⌘",
        route="/novacodepro/tools/incident-command-center",
        required_permissions=("incident.create", "incident.manage"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/incident-command-center",
        audit_category="incident",
        group="RESPONSE",
        overview=("Command", "Timeline", "Owners", "Recovery", "Updates"),
        primary_actions=("Declare Incident", "Assign Commander", "Open War Room"),
    ),
    ToolDefinition(
        id="incident-detection-center",
        name="Incident Detection Center",
        description="Monitor alerts, anomalies, customer reports, and AI-assisted detection.",
        icon="◔",
        route="/novacodepro/tools/incident-detection-center",
        required_permissions=("incident.read", "analytics.read"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/incident-detection-center",
        audit_category="incident",
        group="RESPONSE",
        overview=("Alerts", "Anomalies", "Reports", "Security", "Health"),
        primary_actions=("Review Alert", "Open Detection", "Inspect Trend"),
    ),
    ToolDefinition(
        id="war-room-collaboration-center",
        name="War Room Collaboration Center",
        description="Coordinate live collaboration, decisions, tasks, and evidence sharing.",
        icon="✎",
        route="/novacodepro/tools/war-room-collaboration-center",
        required_permissions=("warroom.manage", "incident.manage"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/war-room-collaboration-center",
        audit_category="war-room",
        group="RESPONSE",
        overview=("Chat", "Tasks", "Decisions", "Evidence", "Whiteboard"),
        primary_actions=("Open War Room", "Assign Task", "Capture Decision"),
    ),
    ToolDefinition(
        id="service-recovery-center",
        name="Service Recovery Center",
        description="Coordinate rollback, failover, backup restoration, and health validation.",
        icon="⟲",
        route="/novacodepro/tools/service-recovery-center",
        required_permissions=("recovery.coordinate", "incident.manage"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/service-recovery-center",
        audit_category="recovery",
        group="RECOVERY",
        overview=("Recovery", "Rollback", "Failover", "Validation", "Impact"),
        primary_actions=("Start Recovery", "Validate Health", "Open Failover"),
    ),
    ToolDefinition(
        id="customer-impact-center",
        name="Customer Impact Center",
        description="Assess customer impact, affected regions, and communication requirements.",
        icon="◉",
        route="/novacodepro/tools/customer-impact-center",
        required_permissions=("incident.read", "communications.publish"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/customer-impact-center",
        audit_category="impact",
        group="RECOVERY",
        overview=("Customers", "Regions", "Severity", "Notifications", "Support"),
        primary_actions=("Review Impact", "Draft Update", "Open Support View"),
    ),
    ToolDefinition(
        id="evidence-preservation-center",
        name="Evidence Preservation Center",
        description="Collect logs, snapshots, traces, and immutable incident evidence.",
        icon="⧉",
        route="/novacodepro/tools/evidence-preservation-center",
        required_permissions=("evidence.collect", "incident.manage"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/evidence-preservation-center",
        audit_category="evidence",
        group="INVESTIGATION",
        overview=("Logs", "Traces", "Snapshots", "Forensics", "Chain"),
        primary_actions=("Collect Evidence", "Preserve Log", "Open Receipt"),
    ),
    ToolDefinition(
        id="root-cause-analysis-center",
        name="Root Cause Analysis Center",
        description="Perform five whys, dependency analysis, and lessons learned review.",
        icon="⚠",
        route="/novacodepro/tools/root-cause-analysis-center",
        required_permissions=("incident.read", "analytics.read"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/root-cause-analysis-center",
        audit_category="analysis",
        group="INVESTIGATION",
        overview=("Cause", "Factors", "Dependencies", "Actions", "Lessons"),
        primary_actions=("Open Analysis", "Review Cause", "Export Findings"),
    ),
    ToolDefinition(
        id="incident-analytics-center",
        name="Incident Analytics Center",
        description="Analyze detection, response, recovery, and customer impact trends.",
        icon="⌘",
        route="/novacodepro/tools/incident-analytics-center",
        required_permissions=("analytics.read", "incident.read"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/incident-analytics-center",
        audit_category="analytics",
        group="INVESTIGATION",
        overview=("Detection", "Response", "Recovery", "Impact", "Trends"),
        primary_actions=("Open Trend", "Review KPI", "Export Report"),
    ),
    ToolDefinition(
        id="enterprise-incident-command-center",
        name="Enterprise Incident Command Center",
        description="Provide executive visibility for live incidents, recovery, and customer impact.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-incident-command-center",
        required_permissions=("incident.read", "report.generate"),
        supported_roles=("INCIDENT_RESPONSE_TEAM", "ADMIN"),
        supported_environments=("operations", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Incident Response",
        help_url="/docs/novacodepro/tools/enterprise-incident-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Map", "Health", "Impact", "Recovery", "KPI"),
        primary_actions=("Open Dashboard", "Review Recovery", "Export Brief"),
    ),
    ToolDefinition(
        id="data-architecture-workspace",
        name="Data Architecture Workspace",
        description="Review domains, models, contracts, lineage, and governance tasks.",
        icon="⌂",
        route="/novacodepro/tools/data-architecture-workspace",
        required_permissions=("dataarchitecture.read", "architecture.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-architecture-workspace",
        audit_category="data-architecture",
        group="HOME",
        overview=("Domains", "Models", "Contracts", "Lineage", "Tasks"),
        primary_actions=("Create Domain", "Review Model", "Trace Lineage"),
    ),
    ToolDefinition(
        id="enterprise-data-architecture-center",
        name="Enterprise Data Architecture Center",
        description="Map the enterprise data landscape and target-state architecture.",
        icon="◈",
        route="/novacodepro/tools/enterprise-data-architecture-center",
        required_permissions=("dataarchitecture.read", "dataarchitecture.create"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/enterprise-data-architecture-center",
        audit_category="data-architecture",
        group="ARCHITECTURE",
        overview=("Landscape", "Domains", "Sources", "Targets", "Roadmap"),
        primary_actions=("Open Map", "Review Standard", "Publish Roadmap"),
    ),
    ToolDefinition(
        id="data-domain-center",
        name="Data Domain Center",
        description="Define data domains, ownership, boundaries, and maturity.",
        icon="◉",
        route="/novacodepro/tools/data-domain-center",
        required_permissions=("datadomain.create", "datadomain.update"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-domain-center",
        audit_category="data-domain",
        group="ARCHITECTURE",
        overview=("Domains", "Owners", "Boundaries", "Events", "Maturity"),
        primary_actions=("Create Domain", "Assign Owner", "Review Boundary"),
    ),
    ToolDefinition(
        id="data-modeling-studio",
        name="Data Modeling Studio",
        description="Create conceptual and logical data models for governed data products.",
        icon="▦",
        route="/novacodepro/tools/data-modeling-studio",
        required_permissions=("datamodel.create", "architecture.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-modeling-studio",
        audit_category="data-model",
        group="ARCHITECTURE",
        overview=("Entities", "Relationships", "Identifiers", "Constraints", "Versions"),
        primary_actions=("Create Model", "Compare Version", "Review Constraint"),
    ),
    ToolDefinition(
        id="data-contract-center",
        name="Data Contract Center",
        description="Publish producer-consumer contracts with compatibility and quality expectations.",
        icon="⚑",
        route="/novacodepro/tools/data-contract-center",
        required_permissions=("datacontract.create", "datacontract.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-contract-center",
        audit_category="data-contract",
        group="CONTRACTS",
        overview=("Schemas", "Quality", "Freshness", "Ownership", "Compatibility"),
        primary_actions=("Create Contract", "Review Change", "Publish Version"),
    ),
    ToolDefinition(
        id="schema-registry",
        name="Schema Registry",
        description="Validate and version API, event, and storage schemas.",
        icon="⌘",
        route="/novacodepro/tools/schema-registry",
        required_permissions=("schema.read", "schema.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/schema-registry",
        audit_category="schema",
        group="CONTRACTS",
        overview=("Schemas", "Versions", "Compatibility", "Consumers", "Migration"),
        primary_actions=("Review Schema", "Compare Version", "Approve Change"),
    ),
    ToolDefinition(
        id="data-lineage-center",
        name="Data Lineage Center",
        description="Trace data flow from source systems to analytics and AI consumers.",
        icon="⟐",
        route="/novacodepro/tools/data-lineage-center",
        required_permissions=("lineage.read", "lineage.manage"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-lineage-center",
        audit_category="lineage",
        group="GOVERNANCE",
        overview=("Sources", "Transforms", "Consumers", "Impact", "Coverage"),
        primary_actions=("Trace Lineage", "Inspect Impact", "Export Evidence"),
    ),
    ToolDefinition(
        id="data-governance-center",
        name="Data Governance Center",
        description="Manage ownership, stewardship, policies, and certification workflows.",
        icon="⚑",
        route="/novacodepro/tools/data-governance-center",
        required_permissions=("catalog.update", "architecture.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-governance-center",
        audit_category="governance",
        group="GOVERNANCE",
        overview=("Ownership", "Policies", "Stewards", "Certifications", "Exceptions"),
        primary_actions=("Review Policy", "Assign Steward", "Open Exception"),
    ),
    ToolDefinition(
        id="data-quality-center",
        name="Data Quality Center",
        description="Define and monitor quality rules, thresholds, and incidents.",
        icon="✓",
        route="/novacodepro/tools/data-quality-center",
        required_permissions=("dataquality.define", "dataquality.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-quality-center",
        audit_category="quality",
        group="GOVERNANCE",
        overview=("Accuracy", "Completeness", "Freshness", "Validity", "Incidents"),
        primary_actions=("Define Rule", "Review Incident", "Open Trend"),
    ),
    ToolDefinition(
        id="data-residency-center",
        name="Data Residency and Sovereignty Center",
        description="Review jurisdiction rules, regional routing, and residency compliance.",
        icon="◌",
        route="/novacodepro/tools/data-residency-center",
        required_permissions=("residency.review", "classification.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/data-residency-center",
        audit_category="residency",
        group="PROTECTION",
        overview=("Residency", "Jurisdictions", "Routes", "Transfers", "Exceptions"),
        primary_actions=("Review Residency", "Inspect Transfer", "Open Exception"),
    ),
    ToolDefinition(
        id="ai-data-architecture-center",
        name="AI and Machine Learning Data Architecture",
        description="Govern feature stores, training datasets, vector stores, and provenance.",
        icon="⟡",
        route="/novacodepro/tools/ai-data-architecture-center",
        required_permissions=("dataarchitecture.read", "architecture.review"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/ai-data-architecture-center",
        audit_category="ai-data",
        group="PLATFORMS",
        overview=("Features", "Training", "Provenance", "Quality", "Retention"),
        primary_actions=("Review Dataset", "Inspect Provenance", "Open Control"),
    ),
    ToolDefinition(
        id="enterprise-data-command-center",
        name="Enterprise Data Command Center",
        description="Present enterprise data health, quality, lineage, and governance status.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-data-command-center",
        required_permissions=("dataarchitecture.read", "analytics.read"),
        supported_roles=("DATA_ARCHITECT", "ADMIN"),
        supported_environments=("data", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Architecture",
        help_url="/docs/novacodepro/tools/enterprise-data-command-center",
        audit_category="command-center",
        group="ASSURANCE",
        overview=("Health", "Lineage", "Quality", "Residency", "Adoption"),
        primary_actions=("Open Dashboard", "Review Quality", "Export Brief"),
    ),
    ToolDefinition(
        id="data-engineering-workspace",
        name="Data Engineering Workspace",
        description="Track pipelines, incidents, quality alerts, deployments, and data products.",
        icon="⌂",
        route="/novacodepro/tools/data-engineering-workspace",
        required_permissions=("pipeline.read", "dataset.read_authorized"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/data-engineering-workspace",
        audit_category="data-engineering",
        group="HOME",
        overview=("Pipelines", "Streaming", "Quality", "Lineage", "Work"),
        primary_actions=("Create Pipeline", "Run Pipeline", "Open Incident"),
    ),
    ToolDefinition(
        id="data-pipeline-center",
        name="Data Pipeline Center",
        description="Create and manage governed ETL, ELT, batch, and CDC pipelines.",
        icon="⇄",
        route="/novacodepro/tools/data-pipeline-center",
        required_permissions=("pipeline.create", "pipeline.update"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/data-pipeline-center",
        audit_category="pipeline",
        group="BUILD",
        overview=("ETL", "ELT", "Batch", "CDC", "Backfills"),
        primary_actions=("Create Pipeline", "Run Pipeline", "Review History"),
    ),
    ToolDefinition(
        id="streaming-data-center",
        name="Streaming Data Center",
        description="Manage Kafka, Pulsar, replay, consumer lag, and event delivery.",
        icon="◔",
        route="/novacodepro/tools/streaming-data-center",
        required_permissions=("stream.read", "stream.configure"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/streaming-data-center",
        audit_category="streaming",
        group="REAL_TIME",
        overview=("Streams", "Topics", "Lag", "Replay", "DLQ"),
        primary_actions=("Open Stream", "Inspect Lag", "Replay Event"),
    ),
    ToolDefinition(
        id="data-observability-center",
        name="Data Observability Center",
        description="Monitor freshness, schema drift, anomalies, and data incidents.",
        icon="◌",
        route="/novacodepro/tools/data-observability-center",
        required_permissions=("quality.monitor", "platform.monitor"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/data-observability-center",
        audit_category="observability",
        group="TRUST",
        overview=("Freshness", "Drift", "Alerts", "Latency", "Incidents"),
        primary_actions=("Open Alert", "Review Drift", "Inspect Trend"),
    ),
    ToolDefinition(
        id="data-quality-center-engineering",
        name="Data Quality Center",
        description="Create validation rules and monitor dataset quality incidents.",
        icon="✓",
        route="/novacodepro/tools/data-quality-center",
        required_permissions=("quality.rule_create", "quality.incident_manage"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/data-quality-center",
        audit_category="quality",
        group="TRUST",
        overview=("Rules", "Thresholds", "Certified", "Incidents", "Evidence"),
        primary_actions=("Create Rule", "Open Incident", "Certify Dataset"),
    ),
    ToolDefinition(
        id="data-deployment-center",
        name="Data Deployment Center",
        description="Deploy pipelines and transformations with approvals, verification, and rollback.",
        icon="⟲",
        route="/novacodepro/tools/data-deployment-center",
        required_permissions=("pipeline.deploy_authorized", "transformation.execute"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/data-deployment-center",
        audit_category="deployment",
        group="DELIVER",
        overview=("Deployments", "Validation", "Rollback", "Evidence", "Readiness"),
        primary_actions=("Deploy", "Validate", "Rollback"),
    ),
    ToolDefinition(
        id="enterprise-data-operations-command-center",
        name="Enterprise Data Operations Command Center",
        description="Present data pipeline health, freshness, quality, capacity, and incidents.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-data-operations-command-center",
        required_permissions=("platform.monitor", "report.generate"),
        supported_roles=("DATA_ENGINEER", "ADMIN"),
        supported_environments=("data", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Platform",
        help_url="/docs/novacodepro/tools/enterprise-data-operations-command-center",
        audit_category="command-center",
        group="OPERATE",
        overview=("Pipelines", "Freshness", "Quality", "Capacity", "Incidents"),
        primary_actions=("Open Dashboard", "Review KPI", "Export Report"),
    ),
    ToolDefinition(
        id="database-engineering-workspace",
        name="Database Engineering Workspace",
        description="Review database health, migrations, capacity, backups, and incidents.",
        icon="⌂",
        route="/novacodepro/tools/database-engineering-workspace",
        required_permissions=("database.read", "database.monitor"),
        supported_roles=("DATABASE_ENGINEER", "ADMIN"),
        supported_environments=("database", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Database Platform",
        help_url="/docs/novacodepro/tools/database-engineering-workspace",
        audit_category="database",
        group="FLEET",
        overview=("Fleet", "Performance", "Protection", "Change", "Runbooks"),
        primary_actions=("Review Health", "Open Migration", "Run Recovery"),
    ),
    ToolDefinition(
        id="database-fleet-center",
        name="Database Fleet Center",
        description="Inventory database systems across products, tenants, regions, and environments.",
        icon="▦",
        route="/novacodepro/tools/database-fleet-center",
        required_permissions=("database.read",),
        supported_roles=("DATABASE_ENGINEER", "ADMIN"),
        supported_environments=("database", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Database Platform",
        help_url="/docs/novacodepro/tools/database-fleet-center",
        audit_category="database",
        group="FLEET",
        overview=("Instances", "Versions", "Owners", "Criticality", "Lifecycle"),
        primary_actions=("Open Fleet", "Inspect Version", "Review Owner"),
    ),
    ToolDefinition(
        id="database-migration-center",
        name="Database Migration Center",
        description="Create governed migration packages with rollback and reconciliation.",
        icon="⇄",
        route="/novacodepro/tools/database-migration-center",
        required_permissions=("migration.create", "migration.execute_authorized"),
        supported_roles=("DATABASE_ENGINEER", "ADMIN"),
        supported_environments=("database", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Database Platform",
        help_url="/docs/novacodepro/tools/database-migration-center",
        audit_category="migration",
        group="ENGINEERING",
        overview=("Draft", "Test", "Approve", "Schedule", "Verify"),
        primary_actions=("Create Migration", "Test Rollback", "Open Evidence"),
    ),
    ToolDefinition(
        id="database-reliability-center",
        name="Database Reliability Center",
        description="Track availability objectives, failover health, and resilience work.",
        icon="◐",
        route="/novacodepro/tools/database-reliability-center",
        required_permissions=("database.monitor", "restore.test"),
        supported_roles=("DATABASE_ENGINEER", "ADMIN"),
        supported_environments=("database", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Database Platform",
        help_url="/docs/novacodepro/tools/database-reliability-center",
        audit_category="reliability",
        group="RELIABILITY",
        overview=("Availability", "Replica Health", "Recovery", "Incidents", "Budgets"),
        primary_actions=("Review SLO", "Open Incident", "Test Recovery"),
    ),
    ToolDefinition(
        id="database-security-center",
        name="Database Security Center",
        description="Enforce database authentication, encryption, logging, and privileged access.",
        icon="⛨",
        route="/novacodepro/tools/database-security-center",
        required_permissions=("database.security.configure", "database.access.review"),
        supported_roles=("DATABASE_ENGINEER", "ADMIN"),
        supported_environments=("database", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Database Security",
        help_url="/docs/novacodepro/tools/database-security-center",
        audit_category="security",
        group="PROTECTION",
        overview=("Encryption", "Access", "Logging", "Keys", "Hardening"),
        primary_actions=("Review Access", "Rotate Keys", "Open Audit"),
    ),
    ToolDefinition(
        id="enterprise-database-command-center",
        name="Enterprise Database Command Center",
        description="Provide enterprise database health, performance, and resilience visibility.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-database-command-center",
        required_permissions=("database.read", "report.generate"),
        supported_roles=("DATABASE_ENGINEER", "ADMIN"),
        supported_environments=("database", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Database Platform",
        help_url="/docs/novacodepro/tools/enterprise-database-command-center",
        audit_category="command-center",
        group="ASSURANCE",
        overview=("Health", "Replication", "Backup", "Performance", "Incidents"),
        primary_actions=("Open Dashboard", "Review Health", "Export Report"),
    ),
    ToolDefinition(
        id="ai-engineering-workspace",
        name="AI Engineering Workspace",
        description="Track models, agents, experiments, evaluations, and production health.",
        icon="⌂",
        route="/novacodepro/tools/ai-engineering-workspace",
        required_permissions=("ai.workspace.read", "experiment.create"),
        supported_roles=("AI_ML_ENGINEER", "ADMIN"),
        supported_environments=("ai", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="AI Platform",
        help_url="/docs/novacodepro/tools/ai-engineering-workspace",
        audit_category="ai",
        group="HOME",
        overview=("Models", "Experiments", "Agents", "Safety", "Reviews"),
        primary_actions=("Create Experiment", "Run Evaluation", "Open Incident"),
    ),
    ToolDefinition(
        id="model-development-studio",
        name="Model Development Studio",
        description="Create model projects, training code, notebooks, and candidate artifacts.",
        icon="◈",
        route="/novacodepro/tools/model-development-studio",
        required_permissions=("model.create", "training.execute"),
        supported_roles=("AI_ML_ENGINEER", "ADMIN"),
        supported_environments=("ai", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="AI Platform",
        help_url="/docs/novacodepro/tools/model-development-studio",
        audit_category="model",
        group="DEVELOP",
        overview=("Projects", "Training", "Code", "Artifacts", "Assumptions"),
        primary_actions=("Create Model", "Run Training", "Open Notebook"),
    ),
    ToolDefinition(
        id="experiment-tracking-center",
        name="Experiment Tracking Center",
        description="Compare runs, metrics, datasets, and reproducibility evidence.",
        icon="⌘",
        route="/novacodepro/tools/experiment-tracking-center",
        required_permissions=("experiment.create", "experiment.execute"),
        supported_roles=("AI_ML_ENGINEER", "ADMIN"),
        supported_environments=("ai", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="AI Platform",
        help_url="/docs/novacodepro/tools/experiment-tracking-center",
        audit_category="experiment",
        group="DEVELOP",
        overview=("Runs", "Metrics", "Parameters", "Artifacts", "Baselines"),
        primary_actions=("Open Run", "Compare Models", "Promote Candidate"),
    ),
    ToolDefinition(
        id="feature-store-center",
        name="Feature Store Center",
        description="Register reusable features, freshness expectations, and consumers.",
        icon="◌",
        route="/novacodepro/tools/feature-store-center",
        required_permissions=("feature.create", "feature.publish_authorized"),
        supported_roles=("AI_ML_ENGINEER", "ADMIN"),
        supported_environments=("ai", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="AI Platform",
        help_url="/docs/novacodepro/tools/feature-store-center",
        audit_category="feature",
        group="DATA",
        overview=("Features", "Groups", "Freshness", "Consumers", "Lineage"),
        primary_actions=("Create Feature", "Review Freshness", "Open Consumer"),
    ),
    ToolDefinition(
        id="training-pipeline-center",
        name="Training Pipeline Center",
        description="Build repeatable training workflows with captured evidence and reproducibility.",
        icon="⇄",
        route="/novacodepro/tools/training-pipeline-center",
        required_permissions=("training.execute", "training.schedule"),
        supported_roles=("AI_ML_ENGINEER", "ADMIN"),
        supported_environments=("ai", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="AI Platform",
        help_url="/docs/novacodepro/tools/training-pipeline-center",
        audit_category="training",
        group="DEVELOP",
        overview=("Runs", "Schedules", "Compute", "Checkpoints", "Evidence"),
        primary_actions=("Run Training", "Schedule Retrain", "Open Evidence"),
    ),
    ToolDefinition(
        id="ai-dataset-center",
        name="AI Dataset Center",
        description="Manage training and evaluation datasets with privacy and provenance controls.",
        icon="▦",
        route="/novacodepro/tools/ai-dataset-center",
        required_permissions=("dataset.read_authorized", "dataset.version"),
        supported_roles=("AI_ML_ENGINEER", "ADMIN"),
        supported_environments=("ai", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="AI Governance",
        help_url="/docs/novacodepro/tools/ai-dataset-center",
        audit_category="dataset",
        group="DATA",
        overview=("Datasets", "Labels", "Provenance", "Privacy", "Versions"),
        primary_actions=("Review Dataset", "Open Version", "Inspect Provenance"),
    ),
    ToolDefinition(
        id="data-science-workspace",
        name="Data Science Workspace",
        description="Track analyses, experiments, models, blockers, and decision support work.",
        icon="⌂",
        route="/novacodepro/tools/data-science-workspace",
        required_permissions=("analysis.create", "dataset.read_authorized"),
        supported_roles=("DATA_SCIENTIST", "ADMIN"),
        supported_environments=("science", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Science",
        help_url="/docs/novacodepro/tools/data-science-workspace",
        audit_category="data-science",
        group="HOME",
        overview=("Analyses", "Experiments", "Models", "Insights", "Reviews"),
        primary_actions=("Create Analysis", "Design Experiment", "Open Notebook"),
    ),
    ToolDefinition(
        id="problem-framing-center",
        name="Analytical Problem Framing Center",
        description="Translate business questions into analytical questions, hypotheses, and data needs.",
        icon="◎",
        route="/novacodepro/tools/problem-framing-center",
        required_permissions=("analysis.create",),
        supported_roles=("DATA_SCIENTIST", "ADMIN"),
        supported_environments=("science", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Science",
        help_url="/docs/novacodepro/tools/problem-framing-center",
        audit_category="analysis",
        group="DISCOVER",
        overview=("Question", "Hypotheses", "Owners", "Metrics", "Risks"),
        primary_actions=("Frame Problem", "Open Dataset", "Draft Plan"),
    ),
    ToolDefinition(
        id="exploratory-analysis-studio",
        name="Exploratory Data Analysis Studio",
        description="Profile datasets, distributions, anomalies, and segment behavior.",
        icon="◌",
        route="/novacodepro/tools/exploratory-analysis-studio",
        required_permissions=("dataset.read_authorized", "notebook.execute"),
        supported_roles=("DATA_SCIENTIST", "ADMIN"),
        supported_environments=("science", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Science",
        help_url="/docs/novacodepro/tools/exploratory-analysis-studio",
        audit_category="analysis",
        group="DISCOVER",
        overview=("Profile", "Outliers", "Trends", "Segments", "Reports"),
        primary_actions=("Profile Data", "Open Notebook", "Export Report"),
    ),
    ToolDefinition(
        id="experiment-design-center",
        name="Experiment Design Center",
        description="Design governed experiments with power, sample size, and guardrails.",
        icon="⇄",
        route="/novacodepro/tools/experiment-design-center",
        required_permissions=("experiment.design", "experiment.analyze"),
        supported_roles=("DATA_SCIENTIST", "ADMIN"),
        supported_environments=("science", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Science",
        help_url="/docs/novacodepro/tools/experiment-design-center",
        audit_category="experiment",
        group="EXPERIMENT",
        overview=("Hypotheses", "Power", "Guardrails", "Variants", "Approval"),
        primary_actions=("Design Experiment", "Estimate Power", "Submit Review"),
    ),
    ToolDefinition(
        id="forecasting-center",
        name="Forecasting Center",
        description="Create demand, revenue, and operational forecasts with intervals and scenarios.",
        icon="⟐",
        route="/novacodepro/tools/forecasting-center",
        required_permissions=("forecast.create",),
        supported_roles=("DATA_SCIENTIST", "ADMIN"),
        supported_environments=("science", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Science",
        help_url="/docs/novacodepro/tools/forecasting-center",
        audit_category="forecasting",
        group="ANALYZE",
        overview=("Demand", "Revenue", "Interval", "Backtest", "Scenarios"),
        primary_actions=("Create Forecast", "Backtest Model", "Open Scenario"),
    ),
    ToolDefinition(
        id="data-science-validation-center",
        name="Data Science Validation Center",
        description="Validate models, assumptions, fairness, explainability, and reproducibility.",
        icon="✓",
        route="/novacodepro/tools/data-science-validation-center",
        required_permissions=("model.evaluate", "reproducibility.manage"),
        supported_roles=("DATA_SCIENTIST", "ADMIN"),
        supported_environments=("science", "development", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Data Science",
        help_url="/docs/novacodepro/tools/data-science-validation-center",
        audit_category="validation",
        group="VALIDATE",
        overview=("Validation", "Fairness", "Explainability", "Reproducibility", "Reviews"),
        primary_actions=("Run Validation", "Review Bias", "Export Evidence"),
    ),
    ToolDefinition(
        id="privacy-compliance-workspace",
        name="Privacy & Compliance Workspace",
        description="Track privacy reviews, compliance findings, policy status, and regulatory work.",
        icon="⌂",
        route="/novacodepro/tools/privacy-compliance-workspace",
        required_permissions=("privacy.read", "compliance.read"),
        supported_roles=("PRIVACY_COMPLIANCE", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Privacy & Compliance",
        help_url="/docs/novacodepro/tools/privacy-compliance-workspace",
        audit_category="privacy-compliance",
        group="PRIVACY",
        overview=("Reviews", "Investigations", "Policies", "Incidents", "Tasks"),
        primary_actions=("Review PIA", "Open Compliance Case", "Generate Report"),
    ),
    ToolDefinition(
        id="privacy-governance-center",
        name="Privacy Governance Center",
        description="Manage privacy principles, controls, ownership, and data lifecycle governance.",
        icon="⚑",
        route="/novacodepro/tools/privacy-governance-center",
        required_permissions=("privacy.review", "policy.manage"),
        supported_roles=("PRIVACY_COMPLIANCE", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Privacy & Compliance",
        help_url="/docs/novacodepro/tools/privacy-governance-center",
        audit_category="privacy",
        group="PRIVACY",
        overview=("Principles", "Controls", "Lifecycle", "Ownership", "Exceptions"),
        primary_actions=("Review Policy", "Open Control", "Publish Update"),
    ),
    ToolDefinition(
        id="privacy-impact-assessment-center",
        name="Privacy Impact Assessment Center",
        description="Perform PIA, DPIA, high-risk processing, and AI privacy reviews.",
        icon="◉",
        route="/novacodepro/tools/privacy-impact-assessment-center",
        required_permissions=("pia.create", "dpia.create"),
        supported_roles=("PRIVACY_COMPLIANCE", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Privacy & Compliance",
        help_url="/docs/novacodepro/tools/privacy-impact-assessment-center",
        audit_category="privacy",
        group="COMPLIANCE",
        overview=("PIA", "DPIA", "AI Risk", "Transfers", "Mitigations"),
        primary_actions=("Create Assessment", "Review Risk", "Request Approval"),
    ),
    ToolDefinition(
        id="compliance-monitoring-center",
        name="Compliance Monitoring Center",
        description="Continuously monitor compliance posture, findings, and obligations.",
        icon="◔",
        route="/novacodepro/tools/compliance-monitoring-center",
        required_permissions=("compliance.manage", "analytics.read"),
        supported_roles=("PRIVACY_COMPLIANCE", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Privacy & Compliance",
        help_url="/docs/novacodepro/tools/compliance-monitoring-center",
        audit_category="monitoring",
        group="COMPLIANCE",
        overview=("Score", "Obligations", "Findings", "Alerts", "Trends"),
        primary_actions=("Open Monitor", "Review Finding", "Export Report"),
    ),
    ToolDefinition(
        id="enterprise-privacy-compliance-command-center",
        name="Enterprise Privacy & Compliance Command Center",
        description="Present privacy maturity, compliance posture, incidents, and board reporting.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-privacy-compliance-command-center",
        required_permissions=("compliance.read", "report.generate"),
        supported_roles=("PRIVACY_COMPLIANCE", "ADMIN"),
        supported_environments=("compliance", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Privacy & Compliance",
        help_url="/docs/novacodepro/tools/enterprise-privacy-compliance-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Posture", "Privacy", "Compliance", "Incidents", "Board"),
        primary_actions=("Open Dashboard", "Review Posture", "Export Report"),
    ),
    ToolDefinition(
        id="enterprise-risk-workspace",
        name="Enterprise Risk Workspace",
        description="Review active risks, appetite breaches, exposures, and treatment work.",
        icon="⌂",
        route="/novacodepro/tools/enterprise-risk-workspace",
        required_permissions=("risk.read", "risk.update"),
        supported_roles=("RISK_MANAGEMENT", "ADMIN"),
        supported_environments=("risk", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk",
        help_url="/docs/novacodepro/tools/enterprise-risk-workspace",
        audit_category="risk",
        group="ENTERPRISE_RISK",
        overview=("Risks", "Appetite", "Treatments", "Indicators", "Reviews"),
        primary_actions=("Register Risk", "Run Assessment", "Open Register"),
    ),
    ToolDefinition(
        id="enterprise-risk-register",
        name="Enterprise Risk Register",
        description="Maintain the authoritative inventory of enterprise risks.",
        icon="▦",
        route="/novacodepro/tools/enterprise-risk-register",
        required_permissions=("riskregister.manage", "risk.read"),
        supported_roles=("RISK_MANAGEMENT", "ADMIN"),
        supported_environments=("risk", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk",
        help_url="/docs/novacodepro/tools/enterprise-risk-register",
        audit_category="risk",
        group="ENTERPRISE_RISK",
        overview=("Owners", "Impacts", "Ratings", "Controls", "History"),
        primary_actions=("Add Risk", "Review Owner", "Open Treatment"),
    ),
    ToolDefinition(
        id="risk-assessment-center",
        name="Risk Assessment Center",
        description="Conduct qualitative and quantitative assessments and record assumptions.",
        icon="◉",
        route="/novacodepro/tools/risk-assessment-center",
        required_permissions=("riskassessment.create", "riskassessment.review"),
        supported_roles=("RISK_MANAGEMENT", "ADMIN"),
        supported_environments=("risk", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk",
        help_url="/docs/novacodepro/tools/risk-assessment-center",
        audit_category="assessment",
        group="CONTROLS",
        overview=("Likelihood", "Impact", "Residual", "Controls", "Evidence"),
        primary_actions=("Create Assessment", "Review Controls", "Export Evidence"),
    ),
    ToolDefinition(
        id="risk-treatment-center",
        name="Risk Treatment Center",
        description="Plan, track, and verify risk treatments and mitigations.",
        icon="⇄",
        route="/novacodepro/tools/risk-treatment-center",
        required_permissions=("risktreatment.create", "risktreatment.monitor"),
        supported_roles=("RISK_MANAGEMENT", "ADMIN"),
        supported_environments=("risk", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk",
        help_url="/docs/novacodepro/tools/risk-treatment-center",
        audit_category="treatment",
        group="CONTROLS",
        overview=("Treatments", "Owners", "Due Dates", "Status", "Verification"),
        primary_actions=("Create Treatment", "Review Progress", "Close Action"),
    ),
    ToolDefinition(
        id="risk-heat-map-center",
        name="Risk Heat Map Center",
        description="Display risks by likelihood, impact, and appetite status.",
        icon="⫶",
        route="/novacodepro/tools/risk-heat-map-center",
        required_permissions=("risk.read", "analytics.read"),
        supported_roles=("RISK_MANAGEMENT", "ADMIN"),
        supported_environments=("risk", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk",
        help_url="/docs/novacodepro/tools/risk-heat-map-center",
        audit_category="analysis",
        group="ANALYSIS",
        overview=("Likelihood", "Impact", "Breach", "Exposure", "Trend"),
        primary_actions=("Open Heat Map", "Filter Risk", "Export View"),
    ),
    ToolDefinition(
        id="enterprise-risk-command-center",
        name="Enterprise Risk Command Center",
        description="Present enterprise risk posture, appetite breaches, and board alerts.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-risk-command-center",
        required_permissions=("risk.read", "riskreport.generate"),
        supported_roles=("RISK_MANAGEMENT", "ADMIN"),
        supported_environments=("risk", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Risk",
        help_url="/docs/novacodepro/tools/enterprise-risk-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Posture", "Breaches", "KRIs", "Loss Events", "Board"),
        primary_actions=("Open Dashboard", "Review Exposure", "Export Report"),
    ),
    ToolDefinition(
        id="regulatory-oversight-workspace",
        name="Regulatory Oversight Workspace",
        description="Review licences, submissions, incidents, and supervisory obligations.",
        icon="⌂",
        route="/novacodepro/tools/regulatory-oversight-workspace",
        required_permissions=("regulator.workspace.read", "submission.read"),
        supported_roles=("EXTERNAL_REGULATOR",),
        supported_environments=("regulator", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Regulatory Affairs",
        help_url="/docs/novacodepro/tools/regulatory-oversight-workspace",
        audit_category="regulatory",
        group="OVERSIGHT",
        overview=("Licences", "Submissions", "Matters", "Incidents", "Deadlines"),
        primary_actions=("Review Submission", "Open Licence", "Inspect Incident"),
    ),
    ToolDefinition(
        id="regulatory-submission-center",
        name="Regulatory Submission Center",
        description="Receive, validate, and track regulated submissions and reporting packages.",
        icon="▦",
        route="/novacodepro/tools/regulatory-submission-center",
        required_permissions=("submission.read", "submission.review"),
        supported_roles=("EXTERNAL_REGULATOR",),
        supported_environments=("regulator", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Regulatory Affairs",
        help_url="/docs/novacodepro/tools/regulatory-submission-center",
        audit_category="submission",
        group="SUPERVISION",
        overview=("Draft", "Submitted", "Review", "Clarification", "Accepted"),
        primary_actions=("Review Return", "Request Clarification", "Accept Submission"),
    ),
    ToolDefinition(
        id="regulatory-reporting-center",
        name="Regulatory Reporting Center",
        description="Review structured regulatory reports, signatures, and evidence packages.",
        icon="⫶",
        route="/novacodepro/tools/regulatory-reporting-center",
        required_permissions=("report.read_authorized", "evidence.read_authorized"),
        supported_roles=("EXTERNAL_REGULATOR",),
        supported_environments=("regulator", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Regulatory Affairs",
        help_url="/docs/novacodepro/tools/regulatory-reporting-center",
        audit_category="reporting",
        group="SUPERVISION",
        overview=("Reports", "Trends", "Attestations", "Lineage", "Signatures"),
        primary_actions=("Open Report", "Inspect Signature", "Export Evidence"),
    ),
    ToolDefinition(
        id="evidence-review-center",
        name="Evidence Review Center",
        description="Verify hashes, signatures, timestamps, and chain of custody.",
        icon="⧉",
        route="/novacodepro/tools/evidence-review-center",
        required_permissions=("evidence.verify", "evidence.read_authorized"),
        supported_roles=("EXTERNAL_REGULATOR",),
        supported_environments=("regulator", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Regulatory Affairs",
        help_url="/docs/novacodepro/tools/evidence-review-center",
        audit_category="evidence",
        group="ASSURANCE",
        overview=("Integrity", "Timestamps", "Hash", "Chain", "Status"),
        primary_actions=("Verify Evidence", "Open Receipt", "Flag Missing"),
    ),
    ToolDefinition(
        id="supervisory-inquiry-center",
        name="Supervisory Inquiry Center",
        description="Create formal information requests and track responses.",
        icon="✎",
        route="/novacodepro/tools/supervisory-inquiry-center",
        required_permissions=("inquiry.create", "inquiry.manage"),
        supported_roles=("EXTERNAL_REGULATOR",),
        supported_environments=("regulator", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Regulatory Affairs",
        help_url="/docs/novacodepro/tools/supervisory-inquiry-center",
        audit_category="inquiry",
        group="SUPERVISION",
        overview=("Scope", "Deadlines", "Requests", "Responses", "Status"),
        primary_actions=("Create Inquiry", "Request Evidence", "Close Inquiry"),
    ),
    ToolDefinition(
        id="regulatory-command-center",
        name="Regulatory Command Center",
        description="Present jurisdiction-specific oversight, deadlines, incidents, and findings.",
        icon="⫶",
        route="/novacodepro/tools/regulatory-command-center",
        required_permissions=("analytics.read_authorized", "regulator.workspace.read"),
        supported_roles=("EXTERNAL_REGULATOR",),
        supported_environments=("regulator", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Regulatory Affairs",
        help_url="/docs/novacodepro/tools/regulatory-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Licences", "Reports", "Inquiries", "Incidents", "Findings"),
        primary_actions=("Open Dashboard", "Review Matter", "Export Report"),
    ),
    ToolDefinition(
        id="legal-operations-workspace",
        name="Legal Operations Workspace",
        description="Track legal matters, contract work, regulatory requests, and priorities.",
        icon="⌂",
        route="/novacodepro/tools/legal-operations-workspace",
        required_permissions=("legal.read", "legal.review"),
        supported_roles=("LEGAL", "ADMIN"),
        supported_environments=("legal", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Legal",
        help_url="/docs/novacodepro/tools/legal-operations-workspace",
        audit_category="legal",
        group="OPERATIONS",
        overview=("Matters", "Contracts", "Reviews", "Calendar", "Approvals"),
        primary_actions=("Review Contract", "Create Opinion", "Open Matter"),
    ),
    ToolDefinition(
        id="legal-matter-management-center",
        name="Legal Matter Management Center",
        description="Manage legal cases, investigations, advice requests, and litigation.",
        icon="◉",
        route="/novacodepro/tools/legal-matter-management-center",
        required_permissions=("legalopinion.create", "litigation.manage"),
        supported_roles=("LEGAL", "ADMIN"),
        supported_environments=("legal", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Legal",
        help_url="/docs/novacodepro/tools/legal-matter-management-center",
        audit_category="matter",
        group="OPERATIONS",
        overview=("Cases", "Requests", "Advice", "Litigation", "Responses"),
        primary_actions=("Open Matter", "Create Opinion", "Assign Counsel"),
    ),
    ToolDefinition(
        id="contract-lifecycle-management-center",
        name="Contract Lifecycle Management Center",
        description="Manage draft contracts, negotiations, approvals, renewals, and terminations.",
        icon="⇄",
        route="/novacodepro/tools/contract-lifecycle-management-center",
        required_permissions=("contract.create", "contract.review"),
        supported_roles=("LEGAL", "ADMIN"),
        supported_environments=("legal", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Legal",
        help_url="/docs/novacodepro/tools/contract-lifecycle-management-center",
        audit_category="contract",
        group="CONTRACTS",
        overview=("Drafts", "Negotiations", "Approvals", "Renewals", "Expiry"),
        primary_actions=("Create Contract", "Review Terms", "Open Approval"),
    ),
    ToolDefinition(
        id="legal-risk-assessment-center",
        name="Legal Risk Assessment Center",
        description="Assess contract, litigation, regulatory, and cross-border legal risk.",
        icon="⚠",
        route="/novacodepro/tools/legal-risk-assessment-center",
        required_permissions=("legalrisk.review", "legal.read"),
        supported_roles=("LEGAL", "ADMIN"),
        supported_environments=("legal", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Legal",
        help_url="/docs/novacodepro/tools/legal-risk-assessment-center",
        audit_category="risk",
        group="DISPUTES",
        overview=("Contract", "Litigation", "Regulatory", "IP", "Cross-Border"),
        primary_actions=("Review Risk", "Open Assessment", "Export Memo"),
    ),
    ToolDefinition(
        id="legal-document-management-center",
        name="Legal Document Management Center",
        description="Manage contracts, opinions, notices, board papers, and legal archives.",
        icon="⧉",
        route="/novacodepro/tools/legal-document-management-center",
        required_permissions=("document.manage", "legal.read"),
        supported_roles=("LEGAL", "ADMIN"),
        supported_environments=("legal", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Legal",
        help_url="/docs/novacodepro/tools/legal-document-management-center",
        audit_category="document",
        group="INTELLIGENCE",
        overview=("Documents", "Archives", "Notices", "Board", "Evidence"),
        primary_actions=("Open Archive", "Review Document", "Export Bundle"),
    ),
    ToolDefinition(
        id="enterprise-legal-command-center",
        name="Enterprise Legal Command Center",
        description="Provide enterprise legal oversight across matters, contracts, disputes, and governance.",
        icon="⫶",
        route="/novacodepro/tools/enterprise-legal-command-center",
        required_permissions=("legal.read", "report.generate"),
        supported_roles=("LEGAL", "ADMIN"),
        supported_environments=("legal", "staging", "pilot", "production"),
        version="v1",
        ownership_team="Legal",
        help_url="/docs/novacodepro/tools/enterprise-legal-command-center",
        audit_category="command-center",
        group="INTELLIGENCE",
        overview=("Matters", "Contracts", "Risks", "Litigation", "Reports"),
        primary_actions=("Open Dashboard", "Review Matter", "Export Brief"),
    ),
)


ROLE_TOOL_GROUPS: dict[str, tuple[str, ...]] = {
    "ADMIN": ("HOME", "BUILD", "DELIVER", "OPERATE", "BUSINESS", "GOVERN", "LEADERSHIP", "ADMINISTRATION"),
    "DEVELOPER": ("HOME", "BUILD", "DESIGN", "DELIVER", "ASSURE", "KNOWLEDGE"),
    "PRODUCT_MANAGER": ("HOME", "STRATEGY", "DISCOVER", "PLAN", "DELIVER", "MEASURE", "KNOWLEDGE"),
    "BUSINESS_ANALYST": ("HOME", "ANALYSIS", "STAKEHOLDERS", "PLANNING", "GOVERNANCE", "INTELLIGENCE"),
    "UI_UX_DESIGNER": ("HOME", "DESIGN", "SYSTEM", "RESEARCH", "DELIVERY", "CREATIVE"),
    "PROJECT_MANAGER": ("HOME", "PROJECTS", "DELIVERY", "GOVERNANCE", "COMMUNICATION", "OPERATIONS"),
    "ARCHITECT": ("HOME", "ARCHITECTURE", "GOVERNANCE", "KNOWLEDGE", "INTELLIGENCE"),
    "QA_ENGINEER": ("HOME", "TESTING", "QUALITY", "INTELLIGENCE"),
    "DEVOPS_ENGINEER": ("HOME", "DELIVERY", "OPERATIONS", "RELIABILITY", "INTELLIGENCE"),
    "CUSTOMER_SUPPORT": ("HOME", "SUPPORT", "CARE", "OPERATIONS", "MANAGEMENT"),
    "OPERATIONS_TEAM": ("HOME", "OPERATIONS", "BUSINESS", "COORDINATION", "GOVERNANCE", "INTELLIGENCE"),
    "BRAND_TEAM": ("HOME", "BRAND", "MARKETING", "EXPERIENCE", "GOVERNANCE", "INTELLIGENCE"),
    "COMPLIANCE_TEAM": ("HOME", "COMPLIANCE", "ASSURANCE", "REGULATORY", "GOVERNANCE", "INTELLIGENCE"),
    "AUDIT_TEAM": ("HOME", "AUDIT", "ASSURANCE", "GOVERNANCE", "INTELLIGENCE"),
    "SECURITY_ENGINEER": ("HOME", "SECURITY", "PROTECTION", "DETECTION", "GOVERNANCE", "INTELLIGENCE"),
    "INCIDENT_RESPONSE_TEAM": ("HOME", "RESPONSE", "RECOVERY", "INVESTIGATION", "CONTINUITY", "INTELLIGENCE"),
    "DATA_ARCHITECT": ("HOME", "ARCHITECTURE", "CONTRACTS", "GOVERNANCE", "PROTECTION", "PLATFORMS", "ASSURANCE"),
    "DATA_ENGINEER": ("HOME", "BUILD", "REAL_TIME", "PLATFORMS", "TRUST", "DELIVER", "OPERATE"),
    "DATABASE_ENGINEER": ("FLEET", "ENGINEERING", "RELIABILITY", "PROTECTION", "OPERATIONS", "ASSURANCE"),
    "AI_ML_ENGINEER": ("HOME", "DEVELOP", "DATA", "GENAI", "EVALUATE", "DELIVER", "OPERATE", "GOVERN"),
    "DATA_SCIENTIST": ("HOME", "DISCOVER", "ANALYZE", "EXPERIMENT", "MODEL", "VALIDATE", "DELIVER", "INTELLIGENCE"),
    "PRIVACY_COMPLIANCE": ("HOME", "PRIVACY", "COMPLIANCE", "DATA_GOVERNANCE", "OPERATIONS", "INTELLIGENCE"),
    "RISK_MANAGEMENT": ("HOME", "ENTERPRISE_RISK", "CONTROLS", "ANALYSIS", "RISK_DOMAINS", "GOVERNANCE", "INTELLIGENCE"),
    "EXTERNAL_REGULATOR": ("HOME", "OVERSIGHT", "SUPERVISION", "ASSURANCE", "REGULATORY_DOMAINS", "INCIDENTS", "ENFORCEMENT", "INTELLIGENCE"),
    "LEGAL": ("HOME", "OPERATIONS", "CONTRACTS", "GOVERNANCE", "LEGAL_DOMAINS", "DISPUTES", "INTELLIGENCE"),
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
    "BUSINESS_ANALYST": (
        "Create Business Requirement",
        "Open Process Model",
        "Start Stakeholder Interview",
        "Analyze Workflow",
        "Review KPIs",
        "Create User Story",
        "Generate Business Report",
        "Submit Requirement",
    ),
    "UI_UX_DESIGNER": (
        "Create Wireframe",
        "Open Design Studio",
        "Prototype Flow",
        "Review Components",
        "Publish Design",
        "Inspect Accessibility",
        "Export Assets",
        "Generate Design Specs",
    ),
    "PROJECT_MANAGER": (
        "Create Project",
        "Assign Resources",
        "Update Schedule",
        "Review Risks",
        "Open RAID Register",
        "Generate Status Report",
        "Approve Baseline",
        "Schedule Meeting",
    ),
    "ARCHITECT": (
        "Create Architecture",
        "Open System Model",
        "Review ADR",
        "Design API",
        "Review Integration",
        "Validate Standards",
        "Publish Architecture",
        "Start Design Review",
    ),
    "QA_ENGINEER": (
        "Run Test Suite",
        "Execute Regression",
        "Open Failed Tests",
        "Report Defect",
        "Review Release",
        "Generate Test Report",
        "Verify Bug Fix",
        "Create Test Plan",
    ),
    "DEVOPS_ENGINEER": (
        "Run Pipeline",
        "Deploy Release",
        "Rollback Deployment",
        "Review Infrastructure",
        "Scale Services",
        "Open Logs",
        "Rotate Secrets",
        "View Kubernetes Cluster",
    ),
    "CUSTOMER_SUPPORT": (
        "Create Ticket",
        "Search Customer",
        "Verify Identity",
        "Escalate Issue",
        "Refund Request",
        "Knowledge Base",
        "Live Chat",
        "View Customer Timeline",
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
    "OPERATIONS_TEAM": (
        "View Operations",
        "Open Incident",
        "Monitor Services",
        "Review Alerts",
        "Approve Maintenance",
        "Run Operational Report",
    ),
    "BRAND_TEAM": (
        "Create Campaign",
        "Upload Assets",
        "Review Brand Compliance",
        "Open Asset Library",
        "Publish Guidelines",
        "Review Website",
        "Generate Brand Report",
    ),
    "COMPLIANCE_TEAM": (
        "Open Audit",
        "Review Policies",
        "Investigate Alert",
        "Approve Exception",
        "Generate Report",
        "Review Evidence",
        "Launch Compliance Review",
    ),
    "AUDIT_TEAM": (
        "Start Audit",
        "Create Audit Plan",
        "Review Evidence",
        "Verify Controls",
        "Issue Findings",
        "Generate Audit Report",
        "Review Corrective Actions",
    ),
    "SECURITY_ENGINEER": (
        "Investigate Alert",
        "Review Vulnerabilities",
        "Run Security Scan",
        "Open SIEM",
        "Review IAM",
        "Manage Certificates",
        "Open Incident",
        "Generate Report",
    ),
    "INCIDENT_RESPONSE_TEAM": (
        "Declare Incident",
        "Open War Room",
        "Assign Commander",
        "Notify Teams",
        "Contain Incident",
        "Recover Services",
        "Generate Timeline",
        "Close Incident",
    ),
    "DATA_ARCHITECT": (
        "Create Data Domain",
        "Design Canonical Model",
        "Register Data Product",
        "Review Schema Change",
        "Trace Data Lineage",
        "Run Privacy Impact Review",
        "Compare Storage Options",
        "Publish Data Standard",
    ),
    "DATA_ENGINEER": (
        "Run Pipeline",
        "Create Pipeline",
        "Inspect Lineage",
        "Review Data Quality",
        "Replay Event Stream",
        "Open Lakehouse",
        "Deploy Transformation",
        "Open Data Incident",
    ),
    "DATABASE_ENGINEER": (
        "Open Database Health",
        "Review Slow Queries",
        "Create Migration Plan",
        "Verify Backup",
        "Inspect Replication",
        "Open Incident",
        "Review Capacity",
        "Run Recovery Test",
    ),
    "AI_ML_ENGINEER": (
        "Create Experiment",
        "Open Model Workspace",
        "Build Training Pipeline",
        "Run Evaluation",
        "Compare Model Versions",
        "Review Drift",
        "Create Model Card",
        "Open AI Incident",
    ),
    "DATA_SCIENTIST": (
        "Create Analysis",
        "Open Notebook",
        "Design Experiment",
        "Create Forecast",
        "Run Statistical Test",
        "Request Productionization",
        "Publish Insight",
        "Explore Dataset",
    ),
    "PRIVACY_COMPLIANCE": (
        "Review Privacy Impact Assessment",
        "Approve Data Processing",
        "Review AI Risk",
        "Manage Consent",
        "Generate Regulatory Report",
        "Open Compliance Case",
        "Review Retention Policy",
    ),
    "RISK_MANAGEMENT": (
        "Register Risk",
        "Run Risk Assessment",
        "Review Treatment Plan",
        "Escalate Material Risk",
        "Create Risk Scenario",
        "Review KRI",
        "Prepare Executive Report",
    ),
    "EXTERNAL_REGULATOR": (
        "Review Regulatory Submission",
        "Request Additional Evidence",
        "Open Licence Record",
        "Inspect Material Incident",
        "Schedule Inspection",
        "Generate Oversight Report",
    ),
    "LEGAL": (
        "Review Contract",
        "Create Legal Opinion",
        "Open Litigation Matter",
        "Review AI Policy",
        "Register Trademark",
        "Review Privacy Notice",
        "Generate Board Brief",
    ),
}


ROLE_NAVIGATION_LAYOUTS: dict[str, tuple[tuple[str, str], ...]] = {
    "DATA_ENGINEER": (
        ("HOME", "Build"),
        ("REAL_TIME", "Real Time"),
        ("PLATFORMS", "Platforms"),
        ("TRUST", "Trust"),
        ("DELIVER", "Deliver"),
        ("OPERATE", "Operate"),
    ),
    "DATABASE_ENGINEER": (
        ("FLEET", "Fleet"),
        ("ENGINEERING", "Engineering"),
        ("RELIABILITY", "Reliability"),
        ("PROTECTION", "Protection"),
        ("OPERATIONS", "Operations"),
        ("ASSURANCE", "Assurance"),
    ),
    "AI_ML_ENGINEER": (
        ("HOME", "Develop"),
        ("DATA", "Data"),
        ("GENAI", "Generative AI"),
        ("EVALUATE", "Evaluate"),
        ("DELIVER", "Deliver"),
        ("OPERATE", "Operate"),
        ("GOVERN", "Govern"),
    ),
    "DATA_SCIENTIST": (
        ("HOME", "Discover"),
        ("ANALYZE", "Analyze"),
        ("EXPERIMENT", "Experiment"),
        ("MODEL", "Model"),
        ("VALIDATE", "Validate"),
        ("DELIVER", "Deliver"),
        ("INTELLIGENCE", "Intelligence"),
    ),
    "PRIVACY_COMPLIANCE": (
        ("PRIVACY", "Privacy"),
        ("COMPLIANCE", "Compliance"),
        ("DATA_GOVERNANCE", "Data Governance"),
        ("OPERATIONS", "Operations"),
        ("INTELLIGENCE", "Intelligence"),
    ),
    "RISK_MANAGEMENT": (
        ("ENTERPRISE_RISK", "Enterprise Risk"),
        ("CONTROLS", "Controls"),
        ("ANALYSIS", "Analysis"),
        ("RISK_DOMAINS", "Risk Domains"),
        ("GOVERNANCE", "Governance"),
        ("INTELLIGENCE", "Intelligence"),
    ),
    "EXTERNAL_REGULATOR": (
        ("OVERSIGHT", "Oversight"),
        ("SUPERVISION", "Supervision"),
        ("ASSURANCE", "Assurance"),
        ("REGULATORY_DOMAINS", "Regulatory Domains"),
        ("INCIDENTS", "Incidents"),
        ("ENFORCEMENT", "Enforcement"),
        ("INTELLIGENCE", "Intelligence"),
    ),
    "LEGAL": (
        ("OPERATIONS", "Operations"),
        ("CONTRACTS", "Contracts"),
        ("GOVERNANCE", "Governance"),
        ("LEGAL_DOMAINS", "Legal Domains"),
        ("DISPUTES", "Disputes & Risk"),
        ("INTELLIGENCE", "Intelligence"),
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
    if canonical in ROLE_NAVIGATION_LAYOUTS:
        order = [group for group, _label in ROLE_NAVIGATION_LAYOUTS[canonical]]
        labels = {group: label for group, label in ROLE_NAVIGATION_LAYOUTS[canonical]}
    elif canonical == "DEVELOPER":
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
    elif canonical == "BUSINESS_ANALYST":
        order = ["HOME", "ANALYSIS", "STAKEHOLDERS", "PLANNING", "GOVERNANCE", "INTELLIGENCE"]
        labels = {
            "HOME": "Analysis",
            "ANALYSIS": "Analysis",
            "STAKEHOLDERS": "Stakeholders",
            "PLANNING": "Planning",
            "GOVERNANCE": "Governance",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "UI_UX_DESIGNER":
        order = ["HOME", "DESIGN", "SYSTEM", "RESEARCH", "DELIVERY", "CREATIVE"]
        labels = {
            "HOME": "Design",
            "DESIGN": "Design",
            "SYSTEM": "System",
            "RESEARCH": "Research",
            "DELIVERY": "Delivery",
            "CREATIVE": "Creative",
        }
    elif canonical == "PROJECT_MANAGER":
        order = ["HOME", "PROJECTS", "DELIVERY", "GOVERNANCE", "COMMUNICATION", "OPERATIONS"]
        labels = {
            "HOME": "Projects",
            "PROJECTS": "Projects",
            "DELIVERY": "Delivery",
            "GOVERNANCE": "Governance",
            "COMMUNICATION": "Communication",
            "OPERATIONS": "Operations",
        }
    elif canonical == "ARCHITECT":
        order = ["HOME", "ARCHITECTURE", "GOVERNANCE", "KNOWLEDGE", "INTELLIGENCE"]
        labels = {
            "HOME": "Overview",
            "ARCHITECTURE": "Architecture",
            "GOVERNANCE": "Governance",
            "KNOWLEDGE": "Knowledge",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "QA_ENGINEER":
        order = ["HOME", "TESTING", "QUALITY", "INTELLIGENCE"]
        labels = {
            "HOME": "Quality Engineering",
            "TESTING": "Testing",
            "QUALITY": "Quality",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "DEVOPS_ENGINEER":
        order = ["HOME", "DELIVERY", "OPERATIONS", "RELIABILITY", "INTELLIGENCE"]
        labels = {
            "HOME": "DevOps",
            "DELIVERY": "Delivery",
            "OPERATIONS": "Operations",
            "RELIABILITY": "Reliability",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "CUSTOMER_SUPPORT":
        order = ["HOME", "SUPPORT", "CARE", "OPERATIONS", "MANAGEMENT"]
        labels = {
            "HOME": "Overview",
            "SUPPORT": "Support",
            "CARE": "Customer Care",
            "OPERATIONS": "Operations",
            "MANAGEMENT": "Management",
        }
    elif canonical == "OPERATIONS_TEAM":
        order = ["HOME", "OPERATIONS", "BUSINESS", "COORDINATION", "GOVERNANCE", "INTELLIGENCE"]
        labels = {
            "HOME": "Overview",
            "OPERATIONS": "Operations",
            "BUSINESS": "Business",
            "COORDINATION": "Coordination",
            "GOVERNANCE": "Governance",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "BRAND_TEAM":
        order = ["HOME", "BRAND", "MARKETING", "EXPERIENCE", "GOVERNANCE", "INTELLIGENCE"]
        labels = {
            "HOME": "Brand",
            "BRAND": "Brand",
            "MARKETING": "Marketing",
            "EXPERIENCE": "Experience",
            "GOVERNANCE": "Governance",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "COMPLIANCE_TEAM":
        order = ["HOME", "COMPLIANCE", "ASSURANCE", "REGULATORY", "GOVERNANCE", "INTELLIGENCE"]
        labels = {
            "HOME": "Compliance",
            "COMPLIANCE": "Compliance",
            "ASSURANCE": "Assurance",
            "REGULATORY": "Regulatory",
            "GOVERNANCE": "Governance",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "AUDIT_TEAM":
        order = ["HOME", "AUDIT", "ASSURANCE", "GOVERNANCE", "INTELLIGENCE"]
        labels = {
            "HOME": "Audit",
            "AUDIT": "Audit",
            "ASSURANCE": "Assurance",
            "GOVERNANCE": "Governance",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "SECURITY_ENGINEER":
        order = ["HOME", "SECURITY", "PROTECTION", "DETECTION", "GOVERNANCE", "INTELLIGENCE"]
        labels = {
            "HOME": "Security",
            "SECURITY": "Security",
            "PROTECTION": "Protection",
            "DETECTION": "Detection",
            "GOVERNANCE": "Governance",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "INCIDENT_RESPONSE_TEAM":
        order = ["HOME", "RESPONSE", "RECOVERY", "INVESTIGATION", "CONTINUITY", "INTELLIGENCE"]
        labels = {
            "HOME": "Response",
            "RESPONSE": "Response",
            "RECOVERY": "Recovery",
            "INVESTIGATION": "Investigation",
            "CONTINUITY": "Continuity",
            "INTELLIGENCE": "Intelligence",
        }
    elif canonical == "DATA_ARCHITECT":
        order = ["HOME", "ARCHITECTURE", "CONTRACTS", "GOVERNANCE", "PROTECTION", "PLATFORMS", "ASSURANCE"]
        labels = {
            "HOME": "Architecture",
            "ARCHITECTURE": "Architecture",
            "CONTRACTS": "Contracts",
            "GOVERNANCE": "Governance",
            "PROTECTION": "Protection",
            "PLATFORMS": "Platforms",
            "ASSURANCE": "Assurance",
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
    if canonical == "BUSINESS_ANALYST":
        health = _business_analysis_health(summary)
        return [
            {"title": "Assigned projects", "value": health["active_projects"], "meta": "Initiatives and analysis work"},
            {"title": "Requirements completed", "value": health["requirements_completed"], "meta": "BRDs, stories, and acceptance criteria"},
            {"title": "Pending reviews", "value": health["pending_reviews"], "meta": "Stakeholder and requirement reviews"},
            {"title": "Open change requests", "value": health["open_change_requests"], "meta": "Scope and process changes"},
            {"title": "Approved business rules", "value": health["approved_business_rules"], "meta": "Governed rule set"},
            {"title": "Stakeholder approvals", "value": health["stakeholder_approvals"], "meta": "Approval completion across programs"},
        ]
    if canonical == "UI_UX_DESIGNER":
        health = _design_health(summary)
        return [
            {"title": "My design projects", "value": summary.get("project_count", 5) or 5, "meta": "Active design work"},
            {"title": "Active tasks", "value": summary.get("workflow_statuses", {}).get("active", 0) + len(pending_approvals), "meta": "Wireframes, prototypes, reviews"},
            {"title": "Design health", "value": health["accessibility_score"], "meta": f"{health['screens_designed']} screens · {health['approved_components']} approved components"},
            {"title": "Prototype completion", "value": health["prototype_completion"], "meta": f"Pending reviews {health['pending_reviews']}"},
            {"title": "Design debt", "value": health["design_debt"], "meta": "Consistency and accessibility quality"},
            {"title": "Tool access", "value": len(_visible_tools(role, "design")), "meta": "Authorized design tools"},
        ]
    if canonical == "PROJECT_MANAGER":
        health = _project_health(summary)
        return [
            {"title": "Active projects", "value": health["projects"], "meta": f"{health['on_track']} on track · {health['at_risk']} at risk"},
            {"title": "My tasks", "value": len(pending_approvals) + health["critical"], "meta": "Scheduling, governance, and reporting work"},
            {"title": "Portfolio health", "value": health["budget_utilization"], "meta": f"{health['milestones_due']} milestones due · {health['open_risks']} open risks"},
            {"title": "Resource pressure", "value": health["open_risks"], "meta": "Dependencies, staffing, and commitments"},
            {"title": "Quality readiness", "value": "High" if health["critical"] <= 1 else "Attention", "meta": "UAT, security, and deployment readiness"},
            {"title": "Tool access", "value": len(_visible_tools(role, "delivery")), "meta": "Authorized project tools"},
        ]
    if canonical == "ARCHITECT":
        return [
            {"title": "Architecture decisions", "value": 324, "meta": "ADRs and standards decisions tracked"},
            {"title": "Open reviews", "value": 18, "meta": "Solution, API, and platform reviews"},
            {"title": "Standards compliance", "value": "97%", "meta": "Reference architecture alignment"},
            {"title": "Technical debt", "value": "Low", "meta": "Modernization and refactoring pressure"},
            {"title": "Critical risks", "value": 2, "meta": "Design risks requiring escalation"},
            {"title": "Reference architectures", "value": 46, "meta": "Reusable patterns and blueprints"},
        ]
    if canonical == "QA_ENGINEER":
        return [
            {"title": "Test cases executed", "value": 8420, "meta": "Regression, API, mobile, and UI coverage"},
            {"title": "Pass rate", "value": "98.9%", "meta": "Recent execution quality"},
            {"title": "Failed tests", "value": 24, "meta": "Open test failures"},
            {"title": "Open defects", "value": 18, "meta": "Verified and triaged defects"},
            {"title": "Automation coverage", "value": "91%", "meta": "Automated validation coverage"},
            {"title": "Release readiness", "value": "96%", "meta": "Quality gate confidence"},
        ]
    if canonical == "DEVOPS_ENGINEER":
        return [
            {"title": "Active deployments", "value": 5, "meta": "Healthy, rolling, and pending releases"},
            {"title": "Infrastructure health", "value": "Strong", "meta": "Service and cluster state"},
            {"title": "CI/CD status", "value": 12, "meta": "Running pipelines"},
            {"title": "Deployment success", "value": "99.4%", "meta": "Successful delivery rate"},
            {"title": "Production availability", "value": "99.98%", "meta": "Platform uptime"},
            {"title": "Quick actions", "value": len(ROLE_QUICK_ACTIONS.get(canonical, ())), "meta": "Authorized operational actions"},
        ]
    if canonical == "CUSTOMER_SUPPORT":
        return [
            {"title": "Open tickets", "value": 28, "meta": "Active support queue"},
            {"title": "High priority", "value": 4, "meta": "Escalated customer requests"},
            {"title": "Resolved today", "value": 19, "meta": "Completed support work"},
            {"title": "CSAT", "value": "96%", "meta": "Customer satisfaction"},
            {"title": "Average response", "value": "8 min", "meta": "First response performance"},
            {"title": "SLA breaches", "value": 0, "meta": "Current SLA posture"},
        ]
    if canonical == "OPERATIONS_TEAM":
        return [
            {"title": "Platform status", "value": "Healthy", "meta": f"{summary.get('service_count', 184)} services online"},
            {"title": "Critical incidents", "value": 0, "meta": "No critical incidents"},
            {"title": "Operational alerts", "value": 4, "meta": "Open alerts requiring attention"},
            {"title": "Today's operations", "value": 2846, "meta": "Completed operational jobs"},
            {"title": "Business operations", "value": 138241, "meta": "Processed payments and transactions"},
            {"title": "Tool access", "value": len(_visible_tools(role, "operations")), "meta": "Authorized operations tools"},
        ]
    if canonical == "BRAND_TEAM":
        return [
            {"title": "Brand health", "value": "97%", "meta": "Brand compliance score"},
            {"title": "Approved assets", "value": 3482, "meta": "Published and approved assets"},
            {"title": "Brand violations", "value": 12, "meta": "Open issues requiring review"},
            {"title": "Active campaigns", "value": 18, "meta": "Brand and launch campaigns"},
            {"title": "Products reviewed", "value": 26, "meta": "Products and experiences checked"},
            {"title": "Tool access", "value": len(_visible_tools(role, "marketing")), "meta": "Authorized brand tools"},
        ]
    if canonical == "COMPLIANCE_TEAM":
        return [
            {"title": "Compliance score", "value": "98%", "meta": "Overall compliance posture"},
            {"title": "Open findings", "value": 6, "meta": "Findings requiring follow-up"},
            {"title": "Policy exceptions", "value": 3, "meta": "Approved temporary exceptions"},
            {"title": "Upcoming audits", "value": 4, "meta": "Scheduled assurance activities"},
            {"title": "Regulatory reviews", "value": 2, "meta": "Active regulatory reviews"},
            {"title": "Tool access", "value": len(_visible_tools(role, "compliance")), "meta": "Authorized compliance tools"},
        ]
    if canonical == "AUDIT_TEAM":
        return [
            {"title": "Active audits", "value": 12, "meta": "Open audit engagements"},
            {"title": "Completed audits", "value": 146, "meta": "Closed assurance work"},
            {"title": "Open findings", "value": 23, "meta": "Current observations"},
            {"title": "Critical findings", "value": 1, "meta": "High-priority issues"},
            {"title": "Evidence reviews", "value": 521, "meta": "Verified evidence items"},
            {"title": "Tool access", "value": len(_visible_tools(role, "audit")), "meta": "Authorized audit tools"},
        ]
    if canonical == "SECURITY_ENGINEER":
        return [
            {"title": "Security score", "value": "99%", "meta": "Overall security posture"},
            {"title": "Critical alerts", "value": 0, "meta": "Immediate alerts"},
            {"title": "High alerts", "value": 2, "meta": "High priority items"},
            {"title": "Vulnerabilities", "value": 17, "meta": "Tracked vulnerabilities"},
            {"title": "Active incidents", "value": 1, "meta": "Open security incidents"},
            {"title": "Tool access", "value": len(_visible_tools(role, "security")), "meta": "Authorized security tools"},
        ]
    if canonical == "INCIDENT_RESPONSE_TEAM":
        return [
            {"title": "Critical incidents", "value": 0, "meta": "No critical incidents"},
            {"title": "Major incidents", "value": 1, "meta": "Major incidents in progress"},
            {"title": "War rooms active", "value": 1, "meta": "Live coordination rooms"},
            {"title": "Mean response", "value": "6m", "meta": "Response time"},
            {"title": "Mean recovery", "value": "24m", "meta": "Recovery time"},
            {"title": "Tool access", "value": len(_visible_tools(role, "operations")), "meta": "Authorized incident tools"},
        ]
    if canonical == "DATA_ARCHITECT":
        return [
            {"title": "Registered data products", "value": 184, "meta": "Catalogued data products"},
            {"title": "Authoritative domains", "value": 26, "meta": "Owned data domains"},
            {"title": "Data quality score", "value": "97%", "meta": "Quality posture"},
            {"title": "Lineage gaps", "value": 8, "meta": "Unresolved lineage gaps"},
            {"title": "Open reviews", "value": 11, "meta": "Architecture reviews in progress"},
            {"title": "Tool access", "value": len(_visible_tools(role, "data")), "meta": "Authorized data tools"},
        ]
    if canonical == "DATA_ENGINEER":
        return [
            {"title": "Running pipelines", "value": 842, "meta": "Healthy, successful, and failed jobs"},
            {"title": "Pipeline availability", "value": "99.97%", "meta": "Operational pipeline uptime"},
            {"title": "Streaming clusters", "value": "Healthy", "meta": "Kafka, Pulsar, and event mesh"},
            {"title": "Certified datasets", "value": 274, "meta": "Published data products"},
            {"title": "Quality incidents", "value": 2, "meta": "Freshness and schema issues"},
            {"title": "Tool access", "value": len(_visible_tools(role, "data")), "meta": "Authorized data engineering tools"},
        ]
    if canonical == "DATABASE_ENGINEER":
        return [
            {"title": "Database instances", "value": 86, "meta": "Managed production and non-production databases"},
            {"title": "Production availability", "value": "99.99%", "meta": "Critical database uptime"},
            {"title": "Backup success", "value": "99.8%", "meta": "Verified backup completion"},
            {"title": "Slow-query alerts", "value": 7, "meta": "Performance tuning queue"},
            {"title": "Critical databases", "value": 18, "meta": "High-priority systems"},
            {"title": "Tool access", "value": len(_visible_tools(role, "database")), "meta": "Authorized database engineering tools"},
        ]
    if canonical == "AI_ML_ENGINEER":
        return [
            {"title": "Registered models", "value": 86, "meta": "Model inventory"},
            {"title": "Production models", "value": 24, "meta": "Approved live services"},
            {"title": "Inference availability", "value": "99.96%", "meta": "Model-serving uptime"},
            {"title": "Evaluation gate pass", "value": "97.4%", "meta": "Candidate model readiness"},
            {"title": "Open safety findings", "value": 4, "meta": "Responsible AI and safety items"},
            {"title": "Tool access", "value": len(_visible_tools(role, "ai")), "meta": "Authorized AI engineering tools"},
        ]
    if canonical == "DATA_SCIENTIST":
        return [
            {"title": "Active studies", "value": 18, "meta": "Open analytical work"},
            {"title": "Running experiments", "value": 7, "meta": "A/B and simulation work"},
            {"title": "Reproducible studies", "value": "98%", "meta": "Evidence-ready analysis"},
            {"title": "Forecast accuracy", "value": "94.2%", "meta": "Published forecasting performance"},
            {"title": "Quality blockers", "value": 3, "meta": "Data issues affecting studies"},
            {"title": "Tool access", "value": len(_visible_tools(role, "science")), "meta": "Authorized data science tools"},
        ]
    if canonical == "PRIVACY_COMPLIANCE":
        return [
            {"title": "Compliance score", "value": "99%", "meta": "Privacy and compliance posture"},
            {"title": "Consent records", "value": "18.4M", "meta": "Managed consent volume"},
            {"title": "Privacy requests", "value": 234, "meta": "Open and completed requests"},
            {"title": "Cross-border transfers", "value": 14, "meta": "Active transfer reviews"},
            {"title": "Open findings", "value": 3, "meta": "Privacy and regulatory issues"},
            {"title": "Tool access", "value": len(_visible_tools(role, "compliance")), "meta": "Authorized privacy and compliance tools"},
        ]
    if canonical == "RISK_MANAGEMENT":
        return [
            {"title": "Active risks", "value": 146, "meta": "Enterprise risk register"},
            {"title": "Risks above appetite", "value": 9, "meta": "Breach and escalation set"},
            {"title": "Overdue treatments", "value": 7, "meta": "Open remediation items"},
            {"title": "Critical risks", "value": 2, "meta": "High-consequence exposures"},
            {"title": "KRI breaches", "value": 3, "meta": "Warning and critical indicators"},
            {"title": "Tool access", "value": len(_visible_tools(role, "risk")), "meta": "Authorized risk tools"},
        ]
    if canonical == "EXTERNAL_REGULATOR":
        return [
            {"title": "Active licences", "value": 8, "meta": "Supervised products and entities"},
            {"title": "Open matters", "value": 3, "meta": "Supervisory work in progress"},
            {"title": "Overdue submissions", "value": 0, "meta": "Reporting timeliness"},
            {"title": "Material incidents", "value": 1, "meta": "Current incident attention"},
            {"title": "Remediation items", "value": 5, "meta": "Open findings and actions"},
            {"title": "Tool access", "value": len(_visible_tools(role, "regulator")), "meta": "Authorized regulatory tools"},
        ]
    if canonical == "LEGAL":
        return [
            {"title": "Active contracts", "value": 1284, "meta": "Contract portfolio"},
            {"title": "Open matters", "value": 39, "meta": "Legal matters and disputes"},
            {"title": "Pending approvals", "value": 21, "meta": "Business requests awaiting review"},
            {"title": "Court matters", "value": 1, "meta": "Active litigation"},
            {"title": "IP assets", "value": 684, "meta": "Trademark, copyright, and trade secret assets"},
            {"title": "Tool access", "value": len(_visible_tools(role, "legal")), "meta": "Authorized legal tools"},
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
    profile = _workspace_profile(canonical)
    if environment is None:
        if profile:
            environment = str(profile["environment"])
        elif canonical == "ADMIN":
            environment = "production"
        elif canonical == "DEVELOPER":
            environment = "development"
        elif canonical == "PRODUCT_MANAGER":
            environment = "business-planning"
        elif canonical == "BUSINESS_ANALYST":
            environment = "analysis"
        elif canonical == "UI_UX_DESIGNER":
            environment = "design"
        elif canonical == "PROJECT_MANAGER":
            environment = "delivery"
        elif canonical == "ARCHITECT":
            environment = "architecture"
        elif canonical == "QA_ENGINEER":
            environment = "quality"
        elif canonical == "DEVOPS_ENGINEER":
            environment = "operations"
        elif canonical == "CUSTOMER_SUPPORT":
            environment = "support"
        elif canonical == "OPERATIONS_TEAM":
            environment = "operations"
        elif canonical == "BRAND_TEAM":
            environment = "marketing"
        elif canonical == "COMPLIANCE_TEAM":
            environment = "compliance"
        elif canonical == "AUDIT_TEAM":
            environment = "audit"
        elif canonical == "SECURITY_ENGINEER":
            environment = "security"
        elif canonical == "INCIDENT_RESPONSE_TEAM":
            environment = "operations"
        elif canonical == "DATA_ARCHITECT":
            environment = "data"
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
            "environments": _workspace_environments(canonical)
            if _workspace_environments(canonical)
            else (
                ["production", "staging", "pilot"]
                if canonical == "ADMIN"
                else (
                    ["business-planning", "staging", "pilot"]
                    if canonical in {"PRODUCT_MANAGER", "BUSINESS_ANALYST"}
                    else (
                        ["design", "staging", "pilot"]
                        if canonical == "UI_UX_DESIGNER"
                        else (
                            ["delivery", "business-planning", "staging", "pilot"]
                            if canonical == "PROJECT_MANAGER"
                            else (
                                ["architecture", "staging", "pilot"]
                                if canonical == "ARCHITECT"
                                else (
                                    ["quality", "staging", "pilot"]
                                    if canonical == "QA_ENGINEER"
                                    else (
                                        ["operations", "staging", "pilot", "production"]
                                        if canonical == "DEVOPS_ENGINEER"
                                        else (
                                            ["support", "staging", "pilot"]
                                            if canonical == "CUSTOMER_SUPPORT"
                                            else ["development", "staging", "pilot"]
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            ),
            "selected_environment": environment,
            "authority_level": _workspace_authority(canonical)
            if _workspace_authority(canonical)
            else (
                "platform-admin"
                if canonical == "ADMIN"
                else (
                    "developer"
                    if canonical == "DEVELOPER"
                    else (
                        "product-manager"
                        if canonical == "PRODUCT_MANAGER"
                        else (
                            "business-analyst"
                            if canonical == "BUSINESS_ANALYST"
                            else (
                                "designer"
                                if canonical == "UI_UX_DESIGNER"
                                else (
                                    "project-manager"
                                    if canonical == "PROJECT_MANAGER"
                                    else (
                                        "architect"
                                        if canonical == "ARCHITECT"
                                        else (
                                            "qa-engineer"
                                            if canonical == "QA_ENGINEER"
                                            else (
                                                "devops-engineer"
                                                if canonical == "DEVOPS_ENGINEER"
                                                else ("customer-support" if canonical == "CUSTOMER_SUPPORT" else "role-scoped")
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            ),
            "navigation": navigation_groups,
            "tools": tool_manifest,
            "dashboard_cards": _workspace_cards(canonical, summary),
            "pending_tasks": [
                {"id": "task-1", "title": "Review active approvals", "status": "pending"},
                {"id": "task-2", "title": "Inspect current operational state", "status": "active"},
            ],
            "pending_approvals": summary.get("pending_approvals", [])[:4],
            "current_sprint": "Sprint 24" if canonical == "DEVELOPER" else None,
            "portfolio_name": "Mobility and Payments"
            if canonical == "PRODUCT_MANAGER"
            else (
                "Mobility & Financial Services"
                if canonical == "BUSINESS_ANALYST"
                else (
                    "Projects Portfolio"
                    if canonical == "PROJECT_MANAGER"
                    else (
                        "Mobility & Financial Operations"
                        if canonical == "OPERATIONS_TEAM"
                        else (
                            "Brand Portfolio"
                            if canonical == "BRAND_TEAM"
                            else (
                                "Compliance Obligations"
                                if canonical == "COMPLIANCE_TEAM"
                                else (
                                    "Enterprise Assurance"
                                    if canonical == "AUDIT_TEAM"
                                    else (
                                        "Cybersecurity"
                                        if canonical == "SECURITY_ENGINEER"
                                        else (
                                            "Global Incident Response"
                                            if canonical == "INCIDENT_RESPONSE_TEAM"
                                            else (
                                                "Enterprise Data Architecture"
                                                if canonical == "DATA_ARCHITECT"
                                                else (
                                                    "Enterprise Data Engineering"
                                                    if canonical == "DATA_ENGINEER"
                                                    else (
                                                        "Database Engineering"
                                                        if canonical == "DATABASE_ENGINEER"
                                                        else (
                                                            "AI/ML Engineering"
                                                            if canonical == "AI_ML_ENGINEER"
                                                            else (
                                                                "Data Science"
                                                                if canonical == "DATA_SCIENTIST"
                                                                else (
                                                                    "Privacy & Compliance"
                                                                    if canonical == "PRIVACY_COMPLIANCE"
                                                                    else (
                                                                        "Enterprise Risk"
                                                                        if canonical == "RISK_MANAGEMENT"
                                                                        else (
                                                                            "Regulatory Oversight"
                                                                            if canonical == "EXTERNAL_REGULATOR"
                                                                            else ("Legal Operations" if canonical == "LEGAL" else None)
                                                                        )
                                                                    )
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            ),
            "product_stage": "Discovery" if canonical == "PRODUCT_MANAGER" else None,
            "analysis_focus": "Requirements and process analysis" if canonical == "BUSINESS_ANALYST" else None,
            "design_focus": "Design Studio" if canonical == "UI_UX_DESIGNER" else None,
            "project_focus": "Project Delivery" if canonical == "PROJECT_MANAGER" else None,
            "architecture_focus": "Enterprise Architecture" if canonical == "ARCHITECT" else None,
            "quality_focus": "Quality Engineering" if canonical == "QA_ENGINEER" else None,
            "devops_focus": "Delivery and operations" if canonical == "DEVOPS_ENGINEER" else None,
            "support_focus": "Customer Support" if canonical == "CUSTOMER_SUPPORT" else None,
            "active_products": service.projects()[:5] if canonical in {"PRODUCT_MANAGER", "DEVELOPER", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "CUSTOMER_SUPPORT"} else service.projects()[:4],
            "product_health": _product_health(summary) if canonical == "PRODUCT_MANAGER" else {},
            "analysis_health": _business_analysis_health(summary) if canonical == "BUSINESS_ANALYST" else {},
            "design_health": _design_health(summary) if canonical == "UI_UX_DESIGNER" else {},
            "project_health": _project_health(summary) if canonical == "PROJECT_MANAGER" else {},
            "architecture_health": {
                "architecture_decisions": 324,
                "open_reviews": 18,
                "standards_compliance": "97%",
                "technical_debt": "Low",
                "critical_risks": 2,
                "reference_architectures": 46,
            }
            if canonical == "ARCHITECT"
            else {},
            "quality_health": {
                "test_cases_executed": 8420,
                "pass_rate": "98.9%",
                "failed_tests": 24,
                "open_defects": 18,
                "automation_coverage": "91%",
                "release_readiness": "96%",
            }
            if canonical == "QA_ENGINEER"
            else {},
            "devops_health": {
                "active_deployments": 5,
                "infrastructure_health": "Strong",
                "ci_cd_status": 12,
                "deployment_success": "99.4%",
                "production_availability": "99.98%",
            }
            if canonical == "DEVOPS_ENGINEER"
            else {},
            "support_health": {
                "open_tickets": 28,
                "high_priority": 4,
                "resolved_today": 19,
                "csat": "96%",
                "average_response": "8 min",
                "sla_breaches": 0,
            }
            if canonical == "CUSTOMER_SUPPORT"
            else {},
            "operations_health": {
                "platform_status": "Healthy",
                "critical_incidents": 0,
                "major_incidents": 1,
                "operational_alerts": 4,
                "services_online": 184,
                "regional_availability": "100%",
                "completed_jobs": 2846,
                "pending_operations": 42,
                "support_escalations": 18,
                "deployment_windows": 3,
                "maintenance_activities": 2,
            }
            if canonical == "OPERATIONS_TEAM"
            else {},
            "brand_health": {
                "brand_compliance": "97%",
                "approved_assets": 3482,
                "brand_violations": 12,
                "campaigns_active": 18,
                "products_reviewed": 26,
            }
            if canonical == "BRAND_TEAM"
            else {},
            "compliance_health": {
                "compliance_score": "98%",
                "open_findings": 6,
                "critical_findings": 0,
                "policy_exceptions": 3,
                "upcoming_audits": 4,
                "regulatory_reviews": 2,
            }
            if canonical == "COMPLIANCE_TEAM"
            else {},
            "audit_health": {
                "active_audits": 12,
                "completed_audits": 146,
                "open_findings": 23,
                "critical_findings": 1,
                "corrective_actions": 38,
                "evidence_reviews": 521,
            }
            if canonical == "AUDIT_TEAM"
            else {},
            "security_health": {
                "security_score": "99%",
                "critical_alerts": 0,
                "high_alerts": 2,
                "vulnerabilities": 17,
                "active_incidents": 1,
            }
            if canonical == "SECURITY_ENGINEER"
            else {},
            "incident_health": {
                "critical_incidents": 0,
                "major_incidents": 1,
                "medium_incidents": 4,
                "resolved_today": 23,
                "teams_engaged": 8,
                "war_rooms_active": 1,
                "mttd": "2m",
                "mttr": "6m",
                "mttr_recovery": "24m",
                "sla": "99.6%",
            }
            if canonical == "INCIDENT_RESPONSE_TEAM"
            else {},
            "data_health": {
                "registered_data_products": 184,
                "authoritative_domains": 26,
                "critical_datasets": 42,
                "data_quality_score": "97%",
                "classified_assets": "99%",
                "lineage_gaps": 8,
                "open_reviews": 11,
            }
            if canonical == "DATA_ARCHITECT"
            else {},
            "customer_signals": [
                {"label": "New feedback items", "value": _product_health(summary)["new_feedback_items"]},
                {"label": "Critical usability issues", "value": _product_health(summary)["critical_usability_issues"]},
                {"label": "Top requested feature", "value": _product_health(summary)["top_requested_feature"]},
                {"label": "Support trend", "value": _product_health(summary)["support_trend"]},
                {"label": "Adoption trend", "value": _product_health(summary)["adoption_trend"]},
            ]
            if canonical == "PRODUCT_MANAGER"
            else [],
            "operations_items": [
                {"label": "Platform Status", "status": "Healthy"},
                {"label": "Major Incidents", "status": "1 monitoring"},
                {"label": "Operational Alerts", "status": "4 open"},
                {"label": "Pending Operations", "status": "42 queued"},
                {"label": "Business Jobs", "status": "2,846 completed"},
            ]
            if canonical == "OPERATIONS_TEAM"
            else [],
            "brand_campaigns": [
                {"label": "NovaRide Public Pilot", "status": "Active"},
                {"label": "NovaPay Africa Launch", "status": "Review"},
                {"label": "NovaID Business Identity", "status": "Approved"},
                {"label": "NovaCodePro Enterprise", "status": "Active"},
            ]
            if canonical == "BRAND_TEAM"
            else [],
            "compliance_tasks": [
                {"label": "Review AML alerts", "status": "pending"},
                {"label": "Approve policy updates", "status": "active"},
                {"label": "Validate KYC controls", "status": "pending"},
                {"label": "Audit NovaPay operations", "status": "pending"},
                {"label": "Review partner compliance", "status": "active"},
                {"label": "Generate compliance report", "status": "pending"},
            ]
            if canonical == "COMPLIANCE_TEAM"
            else [],
            "audit_activities": [
                {"label": "Infrastructure Audit", "status": "active"},
                {"label": "NovaPay Financial Audit", "status": "active"},
                {"label": "Security Control Review", "status": "review"},
                {"label": "Evidence Verification", "status": "active"},
                {"label": "Audit Committee Report", "status": "pending"},
            ]
            if canonical == "AUDIT_TEAM"
            else [],
            "security_alerts": [
                {"label": "Investigate Alert", "status": "open"},
                {"label": "Review Vulnerabilities", "status": "open"},
                {"label": "Run Security Scan", "status": "queued"},
                {"label": "Open SIEM", "status": "ready"},
            ]
            if canonical == "SECURITY_ENGINEER"
            else [],
            "incident_items": [
                {"label": "Critical Incidents", "status": "0"},
                {"label": "Major Incidents", "status": "1 monitoring"},
                {"label": "War Rooms", "status": "1 active"},
                {"label": "Recovery", "status": "Normal"},
                {"label": "Communications", "status": "Active"},
            ]
            if canonical == "INCIDENT_RESPONSE_TEAM"
            else [],
            "data_initiatives": [
                {"label": "Canonical Transfer Model", "status": "in progress"},
                {"label": "Trip-Event Architecture", "status": "review"},
                {"label": "Identity Graph", "status": "planned"},
                {"label": "Lakehouse Modernization", "status": "in progress"},
                {"label": "Customer 360 Data Product", "status": "review"},
            ]
            if canonical == "DATA_ARCHITECT"
            else [],
            "data_engineering_items": [
                {"label": "Run NovaPay settlement pipeline", "status": "healthy"},
                {"label": "Validate NovaRide trip event feed", "status": "monitoring"},
                {"label": "Refresh AI feature store", "status": "scheduled"},
                {"label": "Review schema drift alerts", "status": "pending"},
                {"label": "Publish certified dataset", "status": "ready"},
            ]
            if canonical == "DATA_ENGINEER"
            else [],
            "database_items": [
                {"label": "Review slow queries", "status": "open"},
                {"label": "Create migration plan", "status": "review"},
                {"label": "Verify backup", "status": "pending"},
                {"label": "Inspect replication", "status": "monitoring"},
                {"label": "Open incident", "status": "ready"},
            ]
            if canonical == "DATABASE_ENGINEER"
            else [],
            "ai_ml_items": [
                {"label": "Create experiment", "status": "active"},
                {"label": "Run evaluation", "status": "queued"},
                {"label": "Compare model versions", "status": "review"},
                {"label": "Review drift", "status": "monitoring"},
                {"label": "Open AI incident", "status": "ready"},
            ]
            if canonical == "AI_ML_ENGINEER"
            else [],
            "data_science_items": [
                {"label": "Create analysis", "status": "active"},
                {"label": "Design experiment", "status": "pending"},
                {"label": "Create forecast", "status": "ready"},
                {"label": "Request productionization", "status": "review"},
                {"label": "Open notebook", "status": "active"},
            ]
            if canonical == "DATA_SCIENTIST"
            else [],
            "privacy_compliance_items": [
                {"label": "Review Privacy Impact Assessment", "status": "pending"},
                {"label": "Approve Data Processing", "status": "active"},
                {"label": "Review AI Risk", "status": "monitoring"},
                {"label": "Manage Consent", "status": "active"},
                {"label": "Generate Regulatory Report", "status": "ready"},
            ]
            if canonical == "PRIVACY_COMPLIANCE"
            else [],
            "risk_items": [
                {"label": "Register risk", "status": "pending"},
                {"label": "Run risk assessment", "status": "active"},
                {"label": "Review treatment plan", "status": "monitoring"},
                {"label": "Escalate material risk", "status": "ready"},
                {"label": "Prepare executive report", "status": "review"},
            ]
            if canonical == "RISK_MANAGEMENT"
            else [],
            "regulator_items": [
                {"label": "Review regulatory submission", "status": "pending"},
                {"label": "Request additional evidence", "status": "active"},
                {"label": "Inspect material incident", "status": "monitoring"},
                {"label": "Schedule inspection", "status": "ready"},
                {"label": "Generate oversight report", "status": "review"},
            ]
            if canonical == "EXTERNAL_REGULATOR"
            else [],
            "legal_items": [
                {"label": "Review contract", "status": "pending"},
                {"label": "Create legal opinion", "status": "active"},
                {"label": "Open litigation matter", "status": "monitoring"},
                {"label": "Review AI policy", "status": "review"},
                {"label": "Generate board brief", "status": "ready"},
            ]
            if canonical == "LEGAL"
            else [],
            "analysis_tasks": [
                {"label": "Gather stakeholder requirements", "status": "pending"},
                {"label": "Review business process models", "status": "active"},
                {"label": "Validate acceptance criteria", "status": "pending"},
                {"label": "Prepare BRD for NovaPay", "status": "pending"},
                {"label": "Support sprint planning", "status": "active"},
            ]
            if canonical == "BUSINESS_ANALYST"
            else [],
            "design_projects": [
                {"label": "NovaRide Mobile App", "status": "in progress"},
                {"label": "NovaPay Wallet", "status": "review"},
                {"label": "NovaCodePro Dashboard", "status": "in progress"},
                {"label": "NovaID Identity Portal", "status": "planned"},
                {"label": "Merchant Portal", "status": "review"},
            ]
            if canonical == "UI_UX_DESIGNER"
            else [],
            "design_tasks": [
                {"label": "Create rider booking flow", "status": "active"},
                {"label": "Improve NovaPay onboarding", "status": "active"},
                {"label": "Review accessibility issues", "status": "pending"},
                {"label": "Design driver earnings screen", "status": "pending"},
                {"label": "Update design system", "status": "active"},
                {"label": "Prototype customer dashboard", "status": "pending"},
            ]
            if canonical == "UI_UX_DESIGNER"
            else [],
            "project_portfolio": [
                {"label": "NovaRide Public Pilot", "status": "On Track"},
                {"label": "NovaPay Agent Platform", "status": "At Risk"},
                {"label": "NovaID Federation", "status": "On Track"},
                {"label": "NovaCodePro Workspace", "status": "Planning"},
                {"label": "Merchant Portal", "status": "Testing"},
            ]
            if canonical == "PROJECT_MANAGER"
            else [],
            "project_tasks": [
                {"label": "Approve sprint plan", "status": "pending"},
                {"label": "Review project risks", "status": "active"},
                {"label": "Prepare steering committee report", "status": "pending"},
                {"label": "Resolve resource conflict", "status": "blocked"},
                {"label": "Review milestone completion", "status": "active"},
                {"label": "Plan next release", "status": "pending"},
            ]
            if canonical == "PROJECT_MANAGER"
            else [],
            "architecture_initiatives": [
                {"label": "NovaRide Dispatch v3", "status": "review"},
                {"label": "NovaPay Cross-Border Platform", "status": "in progress"},
                {"label": "NovaID Federation", "status": "planned"},
                {"label": "NovaCodePro Workspace", "status": "in progress"},
                {"label": "Enterprise Event Platform", "status": "review"},
            ]
            if canonical == "ARCHITECT"
            else [],
            "quality_projects": [
                {"label": "NovaRide Public Pilot", "status": "In progress"},
                {"label": "NovaPay Wallet", "status": "In progress"},
                {"label": "NovaID Federation", "status": "Review"},
                {"label": "NovaCodePro Workspace", "status": "Testing"},
                {"label": "Merchant Portal", "status": "Verification"},
            ]
            if canonical == "QA_ENGINEER"
            else [],
            "devops_deployments": [
                {"label": "NovaRide Production", "status": "Healthy"},
                {"label": "NovaPay Staging", "status": "Deploying"},
                {"label": "NovaID Public Pilot", "status": "Healthy"},
                {"label": "NovaCodePro QA", "status": "Ready"},
                {"label": "Merchant Portal", "status": "Rolling Update"},
            ]
            if canonical == "DEVOPS_ENGINEER"
            else [],
            "support_queue": [
                {"label": "NovaRide Payment Delay", "status": "Monitoring"},
                {"label": "NovaPay Transfer Verification", "status": "Resolved"},
                {"label": "NovaID Login Issue", "status": "Investigating"},
            ]
            if canonical == "CUSTOMER_SUPPORT"
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
            "active_projects": service.projects()[:5] if canonical in {"DEVELOPER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "UI_UX_DESIGNER", "PROJECT_MANAGER", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "CUSTOMER_SUPPORT"} else service.projects()[:4],
            "recent_repositories": [
                {
                    "id": f"repo-{index + 1}",
                    "name": f"{project['name'].replace(' ', '-').lower()}-repo",
                    "project": project["name"],
                    "branch": "develop" if canonical in {"DEVELOPER", "PRODUCT_MANAGER"} else "main",
                }
                for index, project in enumerate(service.projects()[:4])
            ]
            if canonical in {"DEVELOPER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "UI_UX_DESIGNER", "PROJECT_MANAGER", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "CUSTOMER_SUPPORT"}
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
                "business_analyst_workspace": canonical == "BUSINESS_ANALYST",
                "design_workspace": canonical == "UI_UX_DESIGNER",
                "project_workspace": canonical == "PROJECT_MANAGER",
                "architecture_workspace": canonical == "ARCHITECT",
                "quality_workspace": canonical == "QA_ENGINEER",
                "devops_workspace": canonical == "DEVOPS_ENGINEER",
                "customer_support_workspace": canonical == "CUSTOMER_SUPPORT",
                "operations_workspace": canonical == "OPERATIONS_TEAM",
                "brand_workspace": canonical == "BRAND_TEAM",
                "compliance_workspace": canonical == "COMPLIANCE_TEAM",
                "audit_workspace": canonical == "AUDIT_TEAM",
                "security_workspace": canonical == "SECURITY_ENGINEER",
                "incident_response_workspace": canonical == "INCIDENT_RESPONSE_TEAM",
                "data_architect_workspace": canonical == "DATA_ARCHITECT",
                "data_engineer_workspace": canonical == "DATA_ENGINEER",
                "database_engineer_workspace": canonical == "DATABASE_ENGINEER",
                "ai_ml_engineer_workspace": canonical == "AI_ML_ENGINEER",
                "data_scientist_workspace": canonical == "DATA_SCIENTIST",
                "privacy_compliance_workspace": canonical == "PRIVACY_COMPLIANCE",
                "risk_management_workspace": canonical == "RISK_MANAGEMENT",
                "regulatory_oversight_workspace": canonical == "EXTERNAL_REGULATOR",
                "legal_workspace": canonical == "LEGAL",
            },
            "command_palette": commands,
            "activity_timeline": (service.audit(limit=12) or service.events(limit=12))[:12],
            "enterprise_signals": {
                "platform_health": summary.get("platform_health", "healthy"),
                "service_health": summary.get("service_health", {}),
                "evidence_completeness": "97%"
                if canonical == "PRODUCT_MANAGER"
                else (
                    "96%"
                    if canonical in {"BUSINESS_ANALYST", "UI_UX_DESIGNER", "PROJECT_MANAGER", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "CUSTOMER_SUPPORT"}
                    else "98%"
                ),
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
    elif canonical == "BUSINESS_ANALYST":
        analysis_projects_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("assigned_projects", [])
        ) or "<li>No assigned projects.</li>"
        analysis_tasks_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("analysis_tasks", [])
        ) or "<li>No analysis tasks.</li>"
        analysis_work_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("analysis_work_items", [])
        ) or "<li>No active analysis work.</li>"
        analysis_documents_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("recent_documents", [])
        ) or "<li>No recent documents.</li>"
        analysis_health = workspace.get("analysis_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Assigned projects</h2></header>
              <ul>{analysis_projects_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>My tasks</h2></header>
              <ul>{analysis_tasks_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Analysis health</h2></header>
              <ul>
                <li><strong>Requirements completed</strong><span>{html.escape(str(analysis_health.get('requirements_completed', 126)))}</span></li>
                <li><strong>Pending reviews</strong><span>{html.escape(str(analysis_health.get('pending_reviews', 14)))}</span></li>
                <li><strong>Open change requests</strong><span>{html.escape(str(analysis_health.get('open_change_requests', 6)))}</span></li>
                <li><strong>Approved business rules</strong><span>{html.escape(str(analysis_health.get('approved_business_rules', 89)))}</span></li>
                <li><strong>Stakeholder approvals</strong><span>{html.escape(str(analysis_health.get('stakeholder_approvals', '92%')))}</span></li>
              </ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent documents</h2></header>
              <ul>{analysis_documents_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Active work</h2></header>
              <ul>{analysis_work_items_html}</ul>
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
    elif canonical == "UI_UX_DESIGNER":
        design_projects_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("design_projects", [])
        ) or "<li>No design projects.</li>"
        design_tasks_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("design_tasks", [])
        ) or "<li>No design tasks.</li>"
        design_components_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("design_components", [])
        ) or "<li>No component activity.</li>"
        design_prototypes_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("recent_prototypes", [])
        ) or "<li>No recent prototypes.</li>"
        design_health = workspace.get("design_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>My design projects</h2></header>
              <ul>{design_projects_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Active tasks</h2></header>
              <ul>{design_tasks_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Design health</h2></header>
              <ul>
                <li><strong>Screens designed</strong><span>{html.escape(str(design_health.get('screens_designed', 184)))}</span></li>
                <li><strong>Pending reviews</strong><span>{html.escape(str(design_health.get('pending_reviews', 12)))}</span></li>
                <li><strong>Approved components</strong><span>{html.escape(str(design_health.get('approved_components', 236)))}</span></li>
                <li><strong>Accessibility score</strong><span>{html.escape(str(design_health.get('accessibility_score', '96%')))}</span></li>
                <li><strong>Prototype completion</strong><span>{html.escape(str(design_health.get('prototype_completion', '89%')))}</span></li>
              </ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent prototypes</h2></header>
              <ul>{design_prototypes_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Component activity</h2></header>
              <ul>{design_components_html}</ul>
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
    elif canonical == "PROJECT_MANAGER":
        portfolio_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("project_portfolio", [])
        ) or "<li>No active projects.</li>"
        project_tasks_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("project_tasks", [])
        ) or "<li>No project tasks.</li>"
        milestones_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("milestones", [])
        ) or "<li>No milestone activity.</li>"
        dependencies_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(str(item.get('value', item.get('status', ''))))}</span></li>"
            for item in workspace.get("project_dependencies", [])
        ) or "<li>No dependency updates.</li>"
        project_health = workspace.get("project_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Project portfolio</h2></header>
              <ul>{portfolio_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>My tasks</h2></header>
              <ul>{project_tasks_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Portfolio health</h2></header>
              <ul>
                <li><strong>Projects</strong><span>{html.escape(str(project_health.get('projects', 12)))}</span></li>
                <li><strong>On track</strong><span>{html.escape(str(project_health.get('on_track', 8)))}</span></li>
                <li><strong>At risk</strong><span>{html.escape(str(project_health.get('at_risk', 3)))}</span></li>
                <li><strong>Critical</strong><span>{html.escape(str(project_health.get('critical', 1)))}</span></li>
                <li><strong>Budget utilization</strong><span>{html.escape(str(project_health.get('budget_utilization', '67%')))}</span></li>
              </ul>
            </section>
            <section class=\"panel\">
              <header><h2>Milestones</h2></header>
              <ul>{milestones_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Dependencies</h2></header>
              <ul>{dependencies_html}</ul>
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
    elif canonical == "ARCHITECT":
        initiatives_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("architecture_initiatives", [])
        ) or "<li>No architecture initiatives.</li>"
        architecture_health = workspace.get("architecture_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Active architecture initiatives</h2></header>
              <ul>{initiatives_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Architecture health</h2></header>
              <ul>
                <li><strong>Architecture decisions</strong><span>{html.escape(str(architecture_health.get('architecture_decisions', 324)))}</span></li>
                <li><strong>Open reviews</strong><span>{html.escape(str(architecture_health.get('open_reviews', 18)))}</span></li>
                <li><strong>Standards compliance</strong><span>{html.escape(str(architecture_health.get('standards_compliance', '97%')))}</span></li>
                <li><strong>Technical debt</strong><span>{html.escape(str(architecture_health.get('technical_debt', 'Low')))}</span></li>
                <li><strong>Critical risks</strong><span>{html.escape(str(architecture_health.get('critical_risks', 2)))}</span></li>
                <li><strong>Reference architectures</strong><span>{html.escape(str(architecture_health.get('reference_architectures', 46)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent work</h2></header>
              <ul>{work_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Recent projects</h2></header>
              <ul>{projects_html}</ul>
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
    elif canonical == "QA_ENGINEER":
        qa_projects_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("quality_projects", [])
        ) or "<li>No active test projects.</li>"
        quality_health = workspace.get("quality_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Active test projects</h2></header>
              <ul>{qa_projects_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>My tasks</h2></header>
              <ul>{work_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Quality health</h2></header>
              <ul>
                <li><strong>Test cases executed</strong><span>{html.escape(str(quality_health.get('test_cases_executed', 8420)))}</span></li>
                <li><strong>Pass rate</strong><span>{html.escape(str(quality_health.get('pass_rate', '98.9%')))}</span></li>
                <li><strong>Failed tests</strong><span>{html.escape(str(quality_health.get('failed_tests', 24)))}</span></li>
                <li><strong>Open defects</strong><span>{html.escape(str(quality_health.get('open_defects', 18)))}</span></li>
                <li><strong>Automation coverage</strong><span>{html.escape(str(quality_health.get('automation_coverage', '91%')))}</span></li>
                <li><strong>Release readiness</strong><span>{html.escape(str(quality_health.get('release_readiness', '96%')))}</span></li>
              </ul>
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
    elif canonical == "DEVOPS_ENGINEER":
        deployments_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("devops_deployments", [])
        ) or "<li>No active deployments.</li>"
        devops_health = workspace.get("devops_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>Active deployments</h2></header>
              <ul>{deployments_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Infrastructure health</h2></header>
              <ul>
                <li><strong>Services running</strong><span>{html.escape(str(devops_health.get('active_deployments', 5)))}</span></li>
                <li><strong>Infrastructure health</strong><span>{html.escape(str(devops_health.get('infrastructure_health', 'Strong')))}</span></li>
                <li><strong>CI/CD status</strong><span>{html.escape(str(devops_health.get('ci_cd_status', 12)))}</span></li>
                <li><strong>Deployment success</strong><span>{html.escape(str(devops_health.get('deployment_success', '99.4%')))}</span></li>
                <li><strong>Production availability</strong><span>{html.escape(str(devops_health.get('production_availability', '99.98%')))}</span></li>
              </ul>
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
    elif canonical == "CUSTOMER_SUPPORT":
        queue_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("support_queue", [])
        ) or "<li>No queued tickets.</li>"
        support_health = workspace.get("support_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\">
              <header><h2>My queue</h2></header>
              <ul>{queue_html}</ul>
            </section>
            <section class=\"panel\">
              <header><h2>Customer health</h2></header>
              <ul>
                <li><strong>Open tickets</strong><span>{html.escape(str(support_health.get('open_tickets', 28)))}</span></li>
                <li><strong>High priority</strong><span>{html.escape(str(support_health.get('high_priority', 4)))}</span></li>
                <li><strong>Resolved today</strong><span>{html.escape(str(support_health.get('resolved_today', 19)))}</span></li>
                <li><strong>CSAT</strong><span>{html.escape(str(support_health.get('csat', '96%')))}</span></li>
                <li><strong>Average response</strong><span>{html.escape(str(support_health.get('average_response', '8 min')))}</span></li>
                <li><strong>SLA breaches</strong><span>{html.escape(str(support_health.get('sla_breaches', 0)))}</span></li>
              </ul>
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
    elif canonical == "OPERATIONS_TEAM":
        operations_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("operations_items", [])
        ) or "<li>No operations items.</li>"
        operations_health = workspace.get("operations_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Today's operations</h2></header><ul>{operations_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Operational status</h2></header>
              <ul>
                <li><strong>Platform status</strong><span>{html.escape(str(operations_health.get('platform_status', 'Healthy')))}</span></li>
                <li><strong>Critical incidents</strong><span>{html.escape(str(operations_health.get('critical_incidents', 0)))}</span></li>
                <li><strong>Major incidents</strong><span>{html.escape(str(operations_health.get('major_incidents', 1)))}</span></li>
                <li><strong>Operational alerts</strong><span>{html.escape(str(operations_health.get('operational_alerts', 4)))}</span></li>
                <li><strong>Services online</strong><span>{html.escape(str(operations_health.get('services_online', 184)))}</span></li>
                <li><strong>Regional availability</strong><span>{html.escape(str(operations_health.get('regional_availability', '100%')))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Business operations</h2></header>
              <ul>
                <li><strong>Completed jobs</strong><span>{html.escape(str(operations_health.get('completed_jobs', 2846)))}</span></li>
                <li><strong>Pending operations</strong><span>{html.escape(str(operations_health.get('pending_operations', 42)))}</span></li>
                <li><strong>Support escalations</strong><span>{html.escape(str(operations_health.get('support_escalations', 18)))}</span></li>
                <li><strong>Deployment windows</strong><span>{html.escape(str(operations_health.get('deployment_windows', 3)))}</span></li>
                <li><strong>Maintenance activities</strong><span>{html.escape(str(operations_health.get('maintenance_activities', 2)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "BRAND_TEAM":
        brand_campaigns_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("brand_campaigns", [])
        ) or "<li>No active campaigns.</li>"
        brand_health = workspace.get("brand_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Active campaigns</h2></header><ul>{brand_campaigns_html}</ul></section>
            <section class=\"panel\"><header><h2>Brand health</h2></header>
              <ul>
                <li><strong>Brand compliance</strong><span>{html.escape(str(brand_health.get('brand_compliance', '97%')))}</span></li>
                <li><strong>Approved assets</strong><span>{html.escape(str(brand_health.get('approved_assets', 3482)))}</span></li>
                <li><strong>Brand violations</strong><span>{html.escape(str(brand_health.get('brand_violations', 12)))}</span></li>
                <li><strong>Campaigns active</strong><span>{html.escape(str(brand_health.get('campaigns_active', 18)))}</span></li>
                <li><strong>Products reviewed</strong><span>{html.escape(str(brand_health.get('products_reviewed', 26)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent projects</h2></header><ul>{projects_html}</ul></section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "COMPLIANCE_TEAM":
        compliance_tasks_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("compliance_tasks", [])
        ) or "<li>No compliance tasks.</li>"
        compliance_health = workspace.get("compliance_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Today's tasks</h2></header><ul>{compliance_tasks_html}</ul></section>
            <section class=\"panel\"><header><h2>Compliance health</h2></header>
              <ul>
                <li><strong>Compliance score</strong><span>{html.escape(str(compliance_health.get('compliance_score', '98%')))}</span></li>
                <li><strong>Open findings</strong><span>{html.escape(str(compliance_health.get('open_findings', 6)))}</span></li>
                <li><strong>Critical findings</strong><span>{html.escape(str(compliance_health.get('critical_findings', 0)))}</span></li>
                <li><strong>Policy exceptions</strong><span>{html.escape(str(compliance_health.get('policy_exceptions', 3)))}</span></li>
                <li><strong>Upcoming audits</strong><span>{html.escape(str(compliance_health.get('upcoming_audits', 4)))}</span></li>
                <li><strong>Regulatory reviews</strong><span>{html.escape(str(compliance_health.get('regulatory_reviews', 2)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "AUDIT_TEAM":
        audit_activities_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("audit_activities", [])
        ) or "<li>No audit activities.</li>"
        audit_health = workspace.get("audit_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Today's activities</h2></header><ul>{audit_activities_html}</ul></section>
            <section class=\"panel\"><header><h2>Audit health</h2></header>
              <ul>
                <li><strong>Active audits</strong><span>{html.escape(str(audit_health.get('active_audits', 12)))}</span></li>
                <li><strong>Completed audits</strong><span>{html.escape(str(audit_health.get('completed_audits', 146)))}</span></li>
                <li><strong>Open findings</strong><span>{html.escape(str(audit_health.get('open_findings', 23)))}</span></li>
                <li><strong>Critical findings</strong><span>{html.escape(str(audit_health.get('critical_findings', 1)))}</span></li>
                <li><strong>Corrective actions</strong><span>{html.escape(str(audit_health.get('corrective_actions', 38)))}</span></li>
                <li><strong>Evidence reviews</strong><span>{html.escape(str(audit_health.get('evidence_reviews', 521)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent projects</h2></header><ul>{projects_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "SECURITY_ENGINEER":
        security_alerts_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("security_alerts", [])
        ) or "<li>No security alerts.</li>"
        security_health = workspace.get("security_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Security operations</h2></header><ul>{security_alerts_html}</ul></section>
            <section class=\"panel\"><header><h2>Security health</h2></header>
              <ul>
                <li><strong>Security score</strong><span>{html.escape(str(security_health.get('security_score', '99%')))}</span></li>
                <li><strong>Critical alerts</strong><span>{html.escape(str(security_health.get('critical_alerts', 0)))}</span></li>
                <li><strong>High alerts</strong><span>{html.escape(str(security_health.get('high_alerts', 2)))}</span></li>
                <li><strong>Vulnerabilities</strong><span>{html.escape(str(security_health.get('vulnerabilities', 17)))}</span></li>
                <li><strong>Active incidents</strong><span>{html.escape(str(security_health.get('active_incidents', 1)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "INCIDENT_RESPONSE_TEAM":
        incident_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("incident_items", [])
        ) or "<li>No incident items.</li>"
        incident_health = workspace.get("incident_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Live operations</h2></header><ul>{incident_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Response metrics</h2></header>
              <ul>
                <li><strong>Mean detection</strong><span>{html.escape(str(incident_health.get('mttd', '2m')))}</span></li>
                <li><strong>Mean response</strong><span>{html.escape(str(incident_health.get('mttr', '6m')))}</span></li>
                <li><strong>Mean recovery</strong><span>{html.escape(str(incident_health.get('mttr_recovery', '24m')))}</span></li>
                <li><strong>SLA compliance</strong><span>{html.escape(str(incident_health.get('sla', '99.6%')))}</span></li>
                <li><strong>Teams engaged</strong><span>{html.escape(str(incident_health.get('teams_engaged', 8)))}</span></li>
                <li><strong>War rooms active</strong><span>{html.escape(str(incident_health.get('war_rooms_active', 1)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "DATA_ARCHITECT":
        data_initiatives_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("data_initiatives", [])
        ) or "<li>No data initiatives.</li>"
        data_health = workspace.get("data_health", {})
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Active initiatives</h2></header><ul>{data_initiatives_html}</ul></section>
            <section class=\"panel\"><header><h2>Data estate health</h2></header>
              <ul>
                <li><strong>Registered data products</strong><span>{html.escape(str(data_health.get('registered_data_products', 184)))}</span></li>
                <li><strong>Authoritative domains</strong><span>{html.escape(str(data_health.get('authoritative_domains', 26)))}</span></li>
                <li><strong>Critical datasets</strong><span>{html.escape(str(data_health.get('critical_datasets', 42)))}</span></li>
                <li><strong>Data quality score</strong><span>{html.escape(str(data_health.get('data_quality_score', '97%')))}</span></li>
                <li><strong>Classified assets</strong><span>{html.escape(str(data_health.get('classified_assets', '99%')))}</span></li>
                <li><strong>Lineage gaps</strong><span>{html.escape(str(data_health.get('lineage_gaps', 8)))}</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Open reviews</h2></header><ul>{projects_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "DATA_ENGINEER":
        pipeline_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("data_engineering_items", [])
        ) or "<li>No pipeline items.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Pipeline work</h2></header><ul>{pipeline_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Platform health</h2></header>
              <ul>
                <li><strong>Streaming clusters</strong><span>Healthy</span></li>
                <li><strong>Lakehouse</strong><span>Healthy</span></li>
                <li><strong>Warehouse</strong><span>Healthy</span></li>
                <li><strong>Data APIs</strong><span>Healthy</span></li>
                <li><strong>Storage</strong><span>Healthy</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Data quality</h2></header>
              <ul>
                <li><strong>Certified datasets</strong><span>274</span></li>
                <li><strong>Freshness SLA</strong><span>99.6%</span></li>
                <li><strong>Quality incidents</strong><span>2</span></li>
                <li><strong>Schema violations</strong><span>1</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "DATABASE_ENGINEER":
        database_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("database_items", [])
        ) or "<li>No database work.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Database fleet</h2></header><ul>{database_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Database health</h2></header>
              <ul>
                <li><strong>Instances</strong><span>86</span></li>
                <li><strong>Healthy instances</strong><span>84</span></li>
                <li><strong>Degraded instances</strong><span>2</span></li>
                <li><strong>Backup success</strong><span>99.8%</span></li>
                <li><strong>Privileged access reviews</strong><span>100%</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Performance</h2></header>
              <ul>
                <li><strong>Slow-query alerts</strong><span>7</span></li>
                <li><strong>Replication lag alerts</strong><span>1</span></li>
                <li><strong>Connection saturation</strong><span>2</span></li>
                <li><strong>Deadlock events</strong><span>4</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "AI_ML_ENGINEER":
        ai_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("ai_ml_items", [])
        ) or "<li>No AI work.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Model work</h2></header><ul>{ai_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Model estate</h2></header>
              <ul>
                <li><strong>Registered models</strong><span>86</span></li>
                <li><strong>Production models</strong><span>24</span></li>
                <li><strong>Models under evaluation</strong><span>17</span></li>
                <li><strong>Evaluation gate pass rate</strong><span>97.4%</span></li>
                <li><strong>Open safety findings</strong><span>4</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Production health</h2></header>
              <ul>
                <li><strong>Inference availability</strong><span>99.96%</span></li>
                <li><strong>Average latency</strong><span>82 ms</span></li>
                <li><strong>Degraded services</strong><span>2</span></li>
                <li><strong>High-risk exceptions</strong><span>1</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "DATA_SCIENTIST":
        study_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("data_science_items", [])
        ) or "<li>No active studies.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Active studies</h2></header><ul>{study_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Analytical health</h2></header>
              <ul>
                <li><strong>Validated model candidates</strong><span>14</span></li>
                <li><strong>Experiments reaching power</strong><span>6</span></li>
                <li><strong>Reproducible studies</strong><span>98%</span></li>
                <li><strong>Forecast accuracy</strong><span>94.2%</span></li>
                <li><strong>Open data blockers</strong><span>3</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Model and experiment health</h2></header>
              <ul>
                <li><strong>Running experiments</strong><span>7</span></li>
                <li><strong>Inconclusive experiments</strong><span>2</span></li>
                <li><strong>Drift investigations</strong><span>3</span></li>
                <li><strong>Approved datasets</strong><span>100%</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "PRIVACY_COMPLIANCE":
        privacy_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("privacy_compliance_items", [])
        ) or "<li>No compliance work.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Today's tasks</h2></header><ul>{privacy_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Compliance health</h2></header>
              <ul>
                <li><strong>Compliance score</strong><span>99%</span></li>
                <li><strong>Critical violations</strong><span>0</span></li>
                <li><strong>Open findings</strong><span>3</span></li>
                <li><strong>Privacy incidents</strong><span>1</span></li>
                <li><strong>Policies current</strong><span>100%</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Privacy operations</h2></header>
              <ul>
                <li><strong>Consent records</strong><span>18.4M</span></li>
                <li><strong>DSAR requests</strong><span>21</span></li>
                <li><strong>Cross-border transfers</strong><span>14</span></li>
                <li><strong>Retention reviews</strong><span>36</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "RISK_MANAGEMENT":
        risk_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("risk_items", [])
        ) or "<li>No risk items.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Risk attention</h2></header><ul>{risk_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise risk posture</h2></header>
              <ul>
                <li><strong>Total active risks</strong><span>146</span></li>
                <li><strong>Critical risks</strong><span>2</span></li>
                <li><strong>High risks</strong><span>17</span></li>
                <li><strong>Risks above appetite</strong><span>9</span></li>
                <li><strong>Overdue treatments</strong><span>7</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Risk domains</h2></header>
              <ul>
                <li><strong>Technology</strong><span>Moderate</span></li>
                <li><strong>Cybersecurity</strong><span>Moderate</span></li>
                <li><strong>Privacy</strong><span>Moderate</span></li>
                <li><strong>Third-party</strong><span>Moderate</span></li>
                <li><strong>Business continuity</strong><span>Moderate</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "EXTERNAL_REGULATOR":
        regulator_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("regulator_items", [])
        ) or "<li>No active supervision items.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Current attention</h2></header><ul>{regulator_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Submission status</h2></header>
              <ul>
                <li><strong>Due this month</strong><span>6</span></li>
                <li><strong>Submitted</strong><span>4</span></li>
                <li><strong>Under review</strong><span>2</span></li>
                <li><strong>Returned for clarification</strong><span>1</span></li>
                <li><strong>Approved</strong><span>9</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Oversight status</h2></header>
              <ul>
                <li><strong>Active licences</strong><span>8</span></li>
                <li><strong>Licence conditions</strong><span>14</span></li>
                <li><strong>Open regulatory matters</strong><span>3</span></li>
                <li><strong>Material incidents</strong><span>1</span></li>
                <li><strong>Outstanding remediation</strong><span>5</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
          </div>
        """
    elif canonical == "LEGAL":
        legal_items_html = "".join(
            f"<li><strong>{html.escape(item['label'])}</strong><span>{html.escape(item['status'])}</span></li>"
            for item in workspace.get("legal_items", [])
        ) or "<li>No legal matters.</li>"
        right_stack_html = f"""
          <div class=\"right-stack\">
            <section class=\"panel\"><header><h2>Legal matters</h2></header><ul>{legal_items_html}</ul></section>
            <section class=\"panel\"><header><h2>Legal portfolio</h2></header>
              <ul>
                <li><strong>Active contracts</strong><span>1,284</span></li>
                <li><strong>Legal reviews</strong><span>142</span></li>
                <li><strong>Open matters</strong><span>39</span></li>
                <li><strong>Pending approvals</strong><span>21</span></li>
                <li><strong>Court matters</strong><span>1</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Intellectual property</h2></header>
              <ul>
                <li><strong>Patents</strong><span>11</span></li>
                <li><strong>Trademarks</strong><span>27</span></li>
                <li><strong>Copyright assets</strong><span>684</span></li>
                <li><strong>Trade secrets</strong><span>49</span></li>
              </ul>
            </section>
            <section class=\"panel\"><header><h2>Recent incidents</h2></header><ul>{incidents_html}</ul></section>
            <section class=\"panel\"><header><h2>Enterprise signals</h2></header><ul>
              <li><strong>Platform health</strong><span>{html.escape(str(signal['platform_health']))}</span></li>
              <li><strong>Evidence completeness</strong><span>{html.escape(str(signal['evidence_completeness']))}</span></li>
              <li><strong>Operational risk</strong><span>{html.escape(str(signal['operational_risk']))}</span></li>
            </ul></section>
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
