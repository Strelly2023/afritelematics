from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from afritech.novacodepro.platform import NovaCodeProPlatform, _new_id, _now
from afritech.novacodepro.solution_engineering import SolutionEngineeringService
from afritech.novacodepro.workflow_fabric import WorkflowFabricService


def _canonical_hash(payload: Any) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _kind(name: str) -> str:
    return f"product_{name}"


def _ensure_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _ensure_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _ensure_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _ensure_status(value: Any, allowed: tuple[str, ...], fallback: str) -> str:
    status = _ensure_text(value, fallback)
    if status not in allowed:
        raise ProductFactoryError("invalid_status", f"invalid_status:{status}")
    return status


REQUEST_STATES = (
    "Draft",
    "Submitted",
    "Under Review",
    "Clarification Required",
    "Approved",
    "Rejected",
    "Deferred",
    "Converted to Product",
    "Converted to Project",
    "Archived",
)

BLUEPRINT_STATES = ("Draft", "Under Review", "Approved", "Amended", "Archived")

PHASE_STATES = (
    "Not Started",
    "Ready",
    "In Progress",
    "Generated",
    "Under Review",
    "Changes Required",
    "Approved",
    "Blocked",
    "Completed",
    "Waived",
    "Archived",
)

PHASE_TRANSITIONS: dict[str, set[str]] = {
    "Not Started": {"Ready", "Archived"},
    "Ready": {"In Progress", "Blocked", "Archived"},
    "In Progress": {"Generated", "Blocked", "Archived"},
    "Generated": {"Under Review", "Changes Required", "Approved", "Blocked"},
    "Under Review": {"Changes Required", "Approved", "Blocked"},
    "Changes Required": {"In Progress", "Blocked"},
    "Approved": {"Completed", "Waived"},
    "Blocked": {"Ready", "Archived"},
    "Completed": {"Archived"},
    "Waived": {"Archived"},
    "Archived": set(),
}

PRODUCT_ARCHETYPES: tuple[dict[str, Any], ...] = (
    {
        "id": "consumer-mobile-app",
        "name": "Consumer Mobile App",
        "status": "PUBLISHED",
        "roles": ["Consumer", "Support", "Administrator"],
        "capabilities": ["registration", "profile", "search", "notifications", "offline", "payments"],
        "modules": ["Identity", "Home", "Search", "Messages", "Account", "Support"],
        "workflows": ["onboarding", "task_completion", "issue_resolution"],
        "ui_surfaces": ["mobile"],
        "database_entities": ["users", "sessions", "preferences", "notifications"],
        "api_categories": ["auth", "profile", "support"],
        "event_categories": ["user.lifecycle", "notification.delivery"],
        "integration_categories": ["identity", "sms", "push"],
        "security_baseline": ["mfa", "session_management", "device_binding"],
        "compliance": ["privacy", "accessibility"],
        "test_categories": ["unit", "api", "browser", "mobile"],
        "operational_controls": ["feature_flags", "monitoring"],
        "release_gates": ["ux_review", "security_review", "mobile_build"],
    },
    {
        "id": "subscription-saas",
        "name": "Subscription SaaS",
        "status": "PUBLISHED",
        "roles": ["Tenant Admin", "Billing Admin", "Support", "Auditor"],
        "capabilities": ["multi-tenancy", "billing", "roles", "reporting", "audit", "integrations"],
        "modules": ["Workspace", "Administration", "Billing", "Reports"],
        "workflows": ["tenant_setup", "subscription_management", "billing_reconciliation"],
        "ui_surfaces": ["web"],
        "database_entities": ["tenants", "subscriptions", "invoices", "audit_events"],
        "api_categories": ["tenant", "billing", "reporting"],
        "event_categories": ["tenant.lifecycle", "billing.lifecycle"],
        "integration_categories": ["payments", "email", "analytics"],
        "security_baseline": ["rbac", "tenant_isolation", "audit"],
        "compliance": ["privacy", "financial_controls"],
        "test_categories": ["unit", "api", "browser", "contract"],
        "operational_controls": ["slo", "alerts", "runbooks"],
        "release_gates": ["qa", "security", "finance_review"],
    },
    {
        "id": "platform-enterprise",
        "name": "Multi-tenant Enterprise Platform",
        "status": "PUBLISHED",
        "roles": ["Platform Admin", "Product Manager", "Architect", "QA Engineer", "SRE"],
        "capabilities": ["request_intake", "blueprints", "traceability", "governance", "evidence", "releases"],
        "modules": ["Product Factory", "Requirements", "Architecture", "Design", "Development", "Operations"],
        "workflows": ["concept_to_production", "release_governance", "continuous_improvement"],
        "ui_surfaces": ["web", "desktop"],
        "database_entities": ["product_requests", "blueprints", "traceability_links", "release_candidates"],
        "api_categories": ["product_factory", "governance", "operations"],
        "event_categories": ["product.lifecycle", "gate.decision", "evidence.publication"],
        "integration_categories": ["repo", "ci", "deployment", "observability"],
        "security_baseline": ["tenant_isolation", "rbac", "approval_gates", "audit"],
        "compliance": ["privacy", "security", "operational_readiness"],
        "test_categories": ["unit", "api", "browser", "e2e", "security"],
        "operational_controls": ["release_gates", "slo", "incident_management"],
        "release_gates": ["prr", "pilot", "ga"],
    },
)

PHASES: tuple[dict[str, Any], ...] = (
    {
        "id": "planning-analysis",
        "name": "Planning & Analysis",
        "entry_criteria": ["request submitted", "stakeholders identified"],
        "exit_criteria": ["blueprint approved", "scope agreed"],
        "deliverables": ["Product Blueprint", "Business Requirements Document", "Stakeholder Register"],
    },
    {
        "id": "uiux-design",
        "name": "UI/UX Design",
        "entry_criteria": ["requirements approved"],
        "exit_criteria": ["screen inventory approved", "accessibility reviewed"],
        "deliverables": ["Wireframes", "Design System", "UX Specs"],
    },
    {
        "id": "architecture-database",
        "name": "Architecture & Database Design",
        "entry_criteria": ["design direction confirmed"],
        "exit_criteria": ["architecture approved", "database design approved"],
        "deliverables": ["C4 diagrams", "ERD", "ADRs"],
    },
    {
        "id": "backend-development",
        "name": "Backend Development",
        "entry_criteria": ["architecture approved"],
        "exit_criteria": ["backend tests passing"],
        "deliverables": ["Services", "APIs", "Migrations"],
    },
    {
        "id": "frontend-development",
        "name": "Frontend Development",
        "entry_criteria": ["design approved"],
        "exit_criteria": ["browser tests passing"],
        "deliverables": ["Web App", "Component Library"],
    },
    {
        "id": "mobile-development",
        "name": "Mobile Applications",
        "entry_criteria": ["mobile scope approved"],
        "exit_criteria": ["mobile build verified"],
        "deliverables": ["Mobile App", "Store readiness"],
    },
    {
        "id": "integrations",
        "name": "Integrations",
        "entry_criteria": ["provider registry approved"],
        "exit_criteria": ["contract tests passing"],
        "deliverables": ["Adapters", "Contracts"],
    },
    {
        "id": "quality",
        "name": "Testing & Quality Assurance",
        "entry_criteria": ["development complete"],
        "exit_criteria": ["mandatory quality gates passing"],
        "deliverables": ["Test plan", "Evidence", "Defect register"],
    },
    {
        "id": "deployment-readiness",
        "name": "Deployment & Production Readiness",
        "entry_criteria": ["quality complete"],
        "exit_criteria": ["prr passed", "pilot ready"],
        "deliverables": ["Release manifest", "Runbooks", "Rollback plan"],
    },
    {
        "id": "operations-improvement",
        "name": "Operations, Monitoring & Continuous Improvement",
        "entry_criteria": ["pilot approved"],
        "exit_criteria": ["operational review complete"],
        "deliverables": ["Dashboards", "Incidents", "Improvement backlog"],
    },
)

CAPABILITY_INVENTORY: tuple[dict[str, Any], ...] = (
    {
        "capability": "Workspace management",
        "existing_implementation": "Partial",
        "source_paths": ["afritech/novacodepro/workspace.py", "afritech/api/novacodepro_workspace_api.py", "novacodepro_portal/src/platform/workspaceRoutes.js"],
        "database_entities": ["workspace", "solution", "project"],
        "apis": ["/v1/novacodepro/workspace", "/v1/solution-engineering/workspaces"],
        "ui_routes": ["/novacodepro/workspace", "/novacodepro/solutions"],
        "tests": ["novacodepro_portal/tests/roleWorkspace.test.js", "novacodepro_portal/tests/workspaceRoutes.test.js"],
        "current_maturity": "usable",
        "missing_functionality": ["Product Factory-specific workspace composition"],
        "upgrade_strategy": "Extend the existing workspace shell with a unified factory landing page.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
    {
        "capability": "Product request intake",
        "existing_implementation": "Partial",
        "source_paths": ["afritech/api/solution_engineering_api.py", "afritech/novacodepro/solution_engineering.py"],
        "database_entities": ["customer_project", "business_idea", "discovery_session"],
        "apis": ["/v1/solution-engineering/projects", "/v1/solution-engineering/projects/{id}/idea"],
        "ui_routes": ["/novacodepro/solutions/projects"],
        "tests": ["novacodepro_portal/tests/ncp003Portal.test.js", "novacodepro_portal/tests/ncp003E2E.test.js"],
        "current_maturity": "usable",
        "missing_functionality": ["First-class governed request intake workflow and decision log"],
        "upgrade_strategy": "Add a request record layer with approval trail and conversion to product/project.",
        "migration_impact": "Medium",
        "compatibility_risk": "Medium",
    },
    {
        "capability": "Product blueprint",
        "existing_implementation": "Partial",
        "source_paths": ["afritech/api/solution_engineering_api.py", "afritech/novacodepro/solution_engineering.py"],
        "database_entities": ["solution_blueprint", "requirement", "architecture_decision"],
        "apis": ["/v1/solution-engineering/projects/{id}/blueprint", "/v1/solution-engineering/projects/{id}/architecture"],
        "ui_routes": ["/novacodepro/solutions/projects/{id}/architecture"],
        "tests": ["novacodepro_portal/tests/ncp003Portal.test.js"],
        "current_maturity": "usable",
        "missing_functionality": ["Immutable approved blueprint versions and amendment history"],
        "upgrade_strategy": "Version blueprints as immutable approvals with controlled amendments.",
        "migration_impact": "Medium",
        "compatibility_risk": "Medium",
    },
    {
        "capability": "Archetype engine",
        "existing_implementation": "Missing",
        "source_paths": ["afritech/novacodepro/demo/factories/_catalog.py", "afritech/novacodepro/demo/factories/projects.py"],
        "database_entities": ["product_archetype"],
        "apis": ["/v1/product-factory/archetypes"],
        "ui_routes": ["/novacodepro/product-factory/archetypes"],
        "tests": ["tests/novacodepro/test_product_factory.py"],
        "current_maturity": "planned",
        "missing_functionality": ["Clone, publish, deprecate, and versioned archetype workflows"],
        "upgrade_strategy": "Seed governed archetypes and allow cloning with overrides.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
    {
        "capability": "Lifecycle governance",
        "existing_implementation": "Partial",
        "source_paths": ["afritech/novacodepro/solution_engineering.py", "afritech/novacodepro/production_readiness.py"],
        "database_entities": ["workflow", "approval", "release"],
        "apis": ["/v1/workflows", "/v1/solution-engineering/projects/{id}/release"],
        "ui_routes": ["/novacodepro/solutions/projects/{id}/releases"],
        "tests": ["novacodepro_portal/tests/ncp003Portal.test.js", "tests/novaride_runtime/unit/test_state_machines.py"],
        "current_maturity": "usable",
        "missing_functionality": ["Unified ten-phase product lifecycle state model"],
        "upgrade_strategy": "Project phases should be normalized into one governed SDLC model.",
        "migration_impact": "Medium",
        "compatibility_risk": "Medium",
    },
    {
        "capability": "Traceability",
        "existing_implementation": "Partial",
        "source_paths": ["afritech/novacodepro/operational_verification", "afritech/novacodepro/solution_engineering.py"],
        "database_entities": ["evidence_bundle", "knowledge_node"],
        "apis": ["/v1/solution-engineering/projects/{id}/timeline", "/v1/workflows/{id}/evidence"],
        "ui_routes": ["/novacodepro/solutions/projects/{id}/evidence"],
        "tests": ["tests/release/test_traceability_validation.py"],
        "current_maturity": "usable",
        "missing_functionality": ["Cross-artifact requirement-to-code-to-test-to-evidence links"],
        "upgrade_strategy": "Materialize trace links and surface coverage gaps.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
    {
        "capability": "Operations Studio",
        "existing_implementation": "Implemented",
        "source_paths": ["afritech/api/novacodepro_ncp008_api.py", "novacodepro_portal/src/novacodepro/NCP008Portal.jsx"],
        "database_entities": ["ncp008_operations_*"],
        "apis": ["/api/v1/operations/overview", "/api/v1/operations/incidents"],
        "ui_routes": ["/novacodepro/operations"],
        "tests": ["novacodepro_portal/tests/ncp008Portal.test.js", "novacodepro_portal/tests/ncp008OperationsFlow.test.js"],
        "current_maturity": "operational",
        "missing_functionality": ["Product Factory-level linkage to release governance"],
        "upgrade_strategy": "Link operations signals into the product-factory gate model.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
    {
        "capability": "Evidence management",
        "existing_implementation": "Implemented",
        "source_paths": ["afritech/novacodepro/operational_verification", "artifacts/release-baseline/evidence"],
        "database_entities": ["evidence_bundle", "audit_events"],
        "apis": ["/v1/workflows/{id}/evidence", "/v1/solution-engineering/projects/{id}/evidence"],
        "ui_routes": ["/novacodepro/solutions/projects/{id}/evidence"],
        "tests": ["tests/release/test_evidence_manifest_validation.py"],
        "current_maturity": "operational",
        "missing_functionality": ["Unified evidence explorer across product-factory phases"],
        "upgrade_strategy": "Expose evidence bundles in the factory landing page.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
    {
        "capability": "Identity and access control",
        "existing_implementation": "Implemented",
        "source_paths": ["afritech/api/auth/jwt_device_auth.py", "afritech/afriprogramming/rbac.py"],
        "database_entities": ["session", "approval", "audit_events"],
        "apis": ["/auth/*", "/v1/novacodepro/*"],
        "ui_routes": ["/novacodepro/login"],
        "tests": ["tests/api/test_novacodepro_operations_api.py", "novacodepro_portal/tests/runtime.test.js"],
        "current_maturity": "operational",
        "missing_functionality": ["Factory-specific role-aware onboarding surfaces"],
        "upgrade_strategy": "Reuse the current session model and role permissions.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
    {
        "capability": "AI-assisted generation",
        "existing_implementation": "Implemented",
        "source_paths": ["afritech/novacodepro/solution_engineering.py", "novacodepro_portal/src/platform/aiWorkspace.jsx"],
        "database_entities": ["agent_execution", "solution_request"],
        "apis": ["/v1/workflows/generate", "/v1/solution-engineering/projects/{id}/blueprint"],
        "ui_routes": ["/novacodepro/ai", "/novacodepro/solutions"],
        "tests": ["novacodepro_portal/tests/aiWorkspace.test.js"],
        "current_maturity": "operational",
        "missing_functionality": ["Factory-curated prompt packs and governed output versions"],
        "upgrade_strategy": "Surface AI generation as a factory action, not a separate assistant.",
        "migration_impact": "Low",
        "compatibility_risk": "Low",
    },
)


def _request_status_transition(current: str, target: str) -> bool:
    transitions = {
        "Draft": {"Submitted", "Archived"},
        "Submitted": {"Under Review", "Clarification Required", "Approved", "Rejected", "Deferred", "Archived"},
        "Under Review": {"Clarification Required", "Approved", "Rejected", "Deferred"},
        "Clarification Required": {"Under Review", "Submitted", "Archived"},
        "Approved": {"Converted to Product", "Converted to Project", "Archived"},
        "Rejected": {"Archived"},
        "Deferred": {"Under Review", "Archived"},
        "Converted to Product": {"Archived"},
        "Converted to Project": {"Archived"},
        "Archived": set(),
    }
    return target in transitions.get(current, set())


@dataclass(frozen=True)
class ProductFactoryContext:
    tenant_id: str
    organization_id: str
    project_id: str = ""
    environment: str = "development"
    actor_id: str = "NovaCodePro"
    role: str = "OPERATOR"


class ProductFactoryError(RuntimeError):
    def __init__(self, code: str, message: str | None = None, status_code: int = 400) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.status_code = status_code


class ProductFactoryService:
    def __init__(self, platform: NovaCodeProPlatform) -> None:
        self.platform = platform
        self.solution_engineering = SolutionEngineeringService(platform, WorkflowFabricService(platform))
        self.enterprise = ProductFactoryEnterpriseService(platform)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.enterprise, name):
            return getattr(self.enterprise, name)
        raise AttributeError(name)

    # ------------------------------------------------------------------
    # Current-state inventory / gaps
    # ------------------------------------------------------------------
    def capability_inventory(self) -> dict[str, Any]:
        capabilities = [dict(item) for item in CAPABILITY_INVENTORY]
        gaps = [item for item in capabilities if item.get("missing_functionality")]
        maturity_counts: dict[str, int] = {}
        for item in capabilities:
            maturity_counts[item["current_maturity"]] = maturity_counts.get(item["current_maturity"], 0) + 1
        return {
            "generated_at": _now(),
            "capabilities": capabilities,
            "summary": {
                "total": len(capabilities),
                "implemented": sum(1 for item in capabilities if item["existing_implementation"] == "Implemented"),
                "partial": sum(1 for item in capabilities if item["existing_implementation"] == "Partial"),
                "missing": sum(1 for item in capabilities if item["existing_implementation"] == "Missing"),
                "gap_count": len(gaps),
                "maturity_counts": maturity_counts,
            },
        }

    def gap_matrix(self) -> dict[str, Any]:
        inventory = self.capability_inventory()
        matrix = []
        for item in inventory["capabilities"]:
            matrix.append(
                {
                    "capability": item["capability"],
                    "maturity": item["current_maturity"],
                    "missing": item["missing_functionality"],
                    "upgrade_strategy": item["upgrade_strategy"],
                    "migration_impact": item["migration_impact"],
                    "compatibility_risk": item["compatibility_risk"],
                }
            )
        return {"generated_at": inventory["generated_at"], "matrix": matrix, "summary": inventory["summary"]}

    # ------------------------------------------------------------------
    # Overview / state
    # ------------------------------------------------------------------
    def overview(self, ctx: ProductFactoryContext) -> dict[str, Any]:
        requests = self.requests(ctx)
        blueprints = self.blueprints(ctx)
        archetypes = self.archetypes()
        phases = self.phases(ctx)
        approvals = self.approvals(ctx)
        evidence = self.evidence(ctx)
        releases = self.platform.releases()
        return {
            "generated_at": _now(),
            "environment": ctx.environment,
            "summary": {
                "requests": len(requests),
                "blueprints": len(blueprints),
                "archetypes": len(archetypes),
                "phases": len(phases),
                "approvals": len(approvals),
                "evidence_items": len(evidence),
                "releases": len(releases),
                "open_gaps": len(self.gap_matrix()["matrix"]),
            },
            "requests": requests[:10],
            "blueprints": blueprints[:10],
            "archetypes": archetypes[:10],
            "phases": phases,
            "approvals": approvals[:10],
            "evidence": evidence[:10],
            "inventory": self.capability_inventory(),
            "gaps": self.gap_matrix(),
            "operations": {
                "product_factory_status": "operational",
                "governance_mode": "human_approved",
                "audit_count": len(self.platform.audit()),
                "latest_activity": self.platform.events(limit=20)[:10],
            },
        }

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------
    def requests(self, ctx: ProductFactoryContext) -> list[dict[str, Any]]:
        return [
            record
            for record in self.platform.repository.list("product_request")
            if str(record.get("tenant_id") or "") == ctx.tenant_id
        ]

    def create_request(self, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        request_id = str(payload.get("id") or _new_id("product-request"))
        status = _ensure_status(payload.get("status"), REQUEST_STATES, "Draft")
        record = {
            "id": request_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "project_id": _ensure_text(payload.get("project_id")),
            "name": _ensure_text(payload.get("product_name") or payload.get("name"), "New Product"),
            "description": _ensure_text(payload.get("product_description") or payload.get("description")),
            "core_business_problem": _ensure_text(payload.get("core_business_problem")),
            "target_users": _ensure_list(payload.get("target_users")),
            "target_market": _ensure_text(payload.get("target_market")),
            "industry": _ensure_text(payload.get("industry")),
            "product_category": _ensure_text(payload.get("product_category")),
            "business_model": _ensure_text(payload.get("business_model")),
            "revenue_model": _ensure_text(payload.get("revenue_model")),
            "geographic_scope": _ensure_text(payload.get("geographic_scope")),
            "supported_languages": _ensure_list(payload.get("supported_languages")),
            "supported_currencies": _ensure_list(payload.get("supported_currencies")),
            "regulatory_requirements": _ensure_list(payload.get("regulatory_requirements")),
            "data_classification": _ensure_text(payload.get("data_classification")),
            "data_residency": _ensure_text(payload.get("data_residency")),
            "required_integrations": _ensure_list(payload.get("required_integrations")),
            "supported_platforms": _ensure_list(payload.get("supported_platforms")),
            "supported_devices": _ensure_list(payload.get("supported_devices")),
            "expected_usage": _ensure_text(payload.get("expected_usage")),
            "transaction_volume": _ensure_text(payload.get("transaction_volume")),
            "availability_target": _ensure_text(payload.get("availability_target")),
            "performance_target": _ensure_text(payload.get("performance_target")),
            "security_classification": _ensure_text(payload.get("security_classification")),
            "accessibility_requirements": _ensure_list(payload.get("accessibility_requirements")),
            "branding_requirements": _ensure_list(payload.get("branding_requirements")),
            "delivery_priority": _ensure_text(payload.get("delivery_priority")),
            "budget_constraints": _ensure_text(payload.get("budget_constraints")),
            "timeline_constraints": _ensure_text(payload.get("timeline_constraints")),
            "known_risks": _ensure_list(payload.get("known_risks")),
            "existing_systems": _ensure_list(payload.get("existing_systems")),
            "migration_requirements": _ensure_list(payload.get("migration_requirements")),
            "operational_requirements": _ensure_list(payload.get("operational_requirements")),
            "support_requirements": _ensure_list(payload.get("support_requirements")),
            "reviewer_assignment": _ensure_text(payload.get("reviewer_assignment")),
            "attachments": _ensure_list(payload.get("attachments")),
            "clarification_threads": _ensure_list(payload.get("clarification_threads")),
            "decision_records": _ensure_list(payload.get("decision_records")),
            "approval_evidence": _ensure_list(payload.get("approval_evidence")),
            "status": status,
            "version": int(payload.get("version") or 1),
            "history": list(payload.get("history") or []),
            "audit": list(payload.get("audit") or []),
            "notifications": list(payload.get("notifications") or []),
            "idempotency_key": _ensure_text(payload.get("idempotency_key")),
            "created_at": payload.get("created_at") or _now(),
            "updated_at": _now(),
        }
        existing = self.platform.repository.get("product_request", request_id)
        if existing and existing.get("idempotency_key") and existing.get("idempotency_key") == record["idempotency_key"]:
            return existing
        self.platform.repository.upsert("product_request", record)
        self._audit(ctx, "product_request", request_id, "create", "Product request created")
        self._append_event("product_request.created", ctx, request_id, {"status": status, "name": record["name"]})
        return record

    def transition_request(self, request_id: str, target_status: str, ctx: ProductFactoryContext, *, note: str = "") -> dict[str, Any]:
        request = self._request(request_id, ctx)
        if not _request_status_transition(str(request.get("status") or "Draft"), target_status):
            raise ProductFactoryError("invalid_request_transition", "invalid_request_transition")
        request["status"] = target_status
        request["history"] = list(request.get("history") or []) + [{"status": target_status, "at": _now(), "actor": ctx.actor_id, "note": note}]
        request["updated_at"] = _now()
        self.platform.repository.upsert("product_request", request)
        self._audit(ctx, "product_request", request_id, "transition", target_status)
        self._append_event("product_request.transitioned", ctx, request_id, {"status": target_status, "note": note})
        return request

    def approve_request(self, request_id: str, ctx: ProductFactoryContext, *, approval_ref: str = "") -> dict[str, Any]:
        request = self.transition_request(request_id, "Approved", ctx, note=approval_ref or "approved")
        approval = self._approval_record(ctx, subject=request["id"], gate="Product Request Approval", decision="APPROVED", evidence=[request["id"]], approval_ref=approval_ref)
        request["approval_id"] = approval["id"]
        self.platform.repository.upsert("product_request", request)
        return request

    def reject_request(self, request_id: str, ctx: ProductFactoryContext, *, reason: str = "") -> dict[str, Any]:
        request = self.transition_request(request_id, "Rejected", ctx, note=reason or "rejected")
        request["rejection_reason"] = reason or "Rejected by reviewer"
        self.platform.repository.upsert("product_request", request)
        return request

    def archive_request(self, request_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        return self.transition_request(request_id, "Archived", ctx, note="archived")

    def convert_request_to_product(self, request_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        request = self.approve_request(request_id, ctx)
        product = {
            "id": f"product-{request['id']}",
            "tenant_id": request["tenant_id"],
            "organization_id": request["organization_id"],
            "request_id": request["id"],
            "name": request["name"],
            "description": request["description"],
            "status": "Converted to Product",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.platform.repository.upsert("product", product)
        request["status"] = "Converted to Product"
        request["product_id"] = product["id"]
        self.platform.repository.upsert("product_request", request)
        self._append_event("product_request.converted", ctx, request_id, {"product_id": product["id"]})
        return product

    def convert_request_to_project(self, request_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        request = self._request(request_id, ctx)
        project = self.solution_engineering.create_project(
            {
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "customer_id": ctx.tenant_id,
                "project_id": f"project-{request_id}",
                "name": request["name"],
                "idea": request["description"] or request["core_business_problem"] or request["name"],
                "request": request["description"],
                "domain": request["product_category"] or "product-factory",
                "region": request["geographic_scope"] or "Australia",
                "environment": ctx.environment,
                "owner": ctx.actor_id,
            },
            actor=ctx.actor_id,
        )
        request["status"] = "Converted to Project"
        request["project_id"] = project["id"]
        self.platform.repository.upsert("product_request", request)
        self._append_event("product_request.project_converted", ctx, request_id, {"project_id": project["id"]})
        return project

    def _request(self, request_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        request = self.platform.repository.get("product_request", request_id)
        if request is None or str(request.get("tenant_id") or "") != ctx.tenant_id:
            raise ProductFactoryError("request_not_found", "request_not_found", 404)
        return request

    # ------------------------------------------------------------------
    # Blueprints
    # ------------------------------------------------------------------
    def blueprints(self, ctx: ProductFactoryContext) -> list[dict[str, Any]]:
        return [
            record
            for record in self.platform.repository.list("product_blueprint")
            if str(record.get("tenant_id") or "") == ctx.tenant_id
        ]

    def create_blueprint(self, request_id: str, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        request = self._request(request_id, ctx)
        existing = self.platform.repository.list("product_blueprint")
        versions = [int(item.get("version") or 0) for item in existing if item.get("request_id") == request_id]
        version = max(versions or [0]) + 1
        blueprint = {
            "id": str(payload.get("id") or _new_id("product-blueprint")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "request_id": request_id,
            "product_name": _ensure_text(payload.get("product_name"), request["name"]),
            "vision": _ensure_text(payload.get("vision")),
            "mission": _ensure_text(payload.get("mission")),
            "core_problem": _ensure_text(payload.get("core_problem"), request.get("core_business_problem")),
            "target_users": _ensure_list(payload.get("target_users") or request.get("target_users")),
            "user_segments": _ensure_list(payload.get("user_segments")),
            "jobs_to_be_done": _ensure_list(payload.get("jobs_to_be_done")),
            "value_proposition": _ensure_text(payload.get("value_proposition")),
            "market_context": _ensure_text(payload.get("market_context"), request.get("target_market")),
            "competitive_position": _ensure_text(payload.get("competitive_position")),
            "business_objectives": _ensure_list(payload.get("business_objectives")),
            "capabilities": _ensure_list(payload.get("capabilities")),
            "boundaries": _ensure_list(payload.get("boundaries")),
            "mvp_scope": _ensure_list(payload.get("mvp_scope")),
            "future_scope": _ensure_list(payload.get("future_scope")),
            "functional_requirements": _ensure_list(payload.get("functional_requirements")),
            "non_functional_requirements": _ensure_list(payload.get("non_functional_requirements")),
            "security_requirements": _ensure_list(payload.get("security_requirements")),
            "privacy_requirements": _ensure_list(payload.get("privacy_requirements")),
            "compliance_requirements": _ensure_list(payload.get("compliance_requirements")),
            "accessibility_requirements": _ensure_list(payload.get("accessibility_requirements")),
            "operational_requirements": _ensure_list(payload.get("operational_requirements")),
            "localisation_requirements": _ensure_list(payload.get("localisation_requirements")),
            "kpis": _ensure_list(payload.get("kpis")),
            "success_metrics": _ensure_list(payload.get("success_metrics")),
            "risks": _ensure_list(payload.get("risks")),
            "assumptions": _ensure_list(payload.get("assumptions")),
            "constraints": _ensure_list(payload.get("constraints")),
            "dependencies": _ensure_list(payload.get("dependencies")),
            "recommended_architecture": _ensure_text(payload.get("recommended_architecture")),
            "technology_profile": _ensure_text(payload.get("technology_profile")),
            "delivery_strategy": _ensure_text(payload.get("delivery_strategy")),
            "roadmap": _ensure_list(payload.get("roadmap")),
            "status": _ensure_status(payload.get("status"), BLUEPRINT_STATES, "Draft"),
            "version": version,
            "amends_id": _ensure_text(payload.get("amends_id")),
            "approved_at": _ensure_text(payload.get("approved_at")),
            "approval_evidence": _ensure_list(payload.get("approval_evidence")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.platform.repository.upsert("product_blueprint", blueprint)
        self._audit(ctx, "product_blueprint", blueprint["id"], "create", "Product blueprint created")
        self._append_event("product_blueprint.created", ctx, request_id, {"blueprint_id": blueprint["id"], "version": version})
        return blueprint

    def approve_blueprint(self, blueprint_id: str, ctx: ProductFactoryContext, *, evidence: list[str] | None = None) -> dict[str, Any]:
        blueprint = self._blueprint(blueprint_id, ctx)
        blueprint["status"] = "Approved"
        blueprint["approved_at"] = _now()
        blueprint["approval_evidence"] = list(evidence or [])
        blueprint["updated_at"] = _now()
        self.platform.repository.upsert("product_blueprint", blueprint)
        self._approval_record(ctx, subject=blueprint["id"], gate="Product Blueprint Approval", decision="APPROVED", evidence=list(evidence or []))
        self._append_event("product_blueprint.approved", ctx, blueprint_id, {"status": "Approved"})
        return blueprint

    def amend_blueprint(self, blueprint_id: str, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        blueprint = self._blueprint(blueprint_id, ctx)
        if blueprint.get("status") == "Approved":
            amended = copy.deepcopy(blueprint)
            amended["id"] = _new_id("product-blueprint")
            amended["amends_id"] = blueprint["id"]
            amended["version"] = int(blueprint.get("version") or 1) + 1
            amended["status"] = "Amended"
            amended["updated_at"] = _now()
            amended.update({key: value for key, value in payload.items() if key not in {"id", "tenant_id", "organization_id", "request_id"}})
            self.platform.repository.upsert("product_blueprint", amended)
            self._append_event("product_blueprint.amended", ctx, blueprint["request_id"], {"blueprint_id": amended["id"], "previous_blueprint_id": blueprint["id"]})
            return amended
        blueprint.update({key: value for key, value in payload.items() if key not in {"id", "tenant_id", "organization_id", "request_id"}})
        blueprint["updated_at"] = _now()
        self.platform.repository.upsert("product_blueprint", blueprint)
        return blueprint

    def _blueprint(self, blueprint_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        blueprint = self.platform.repository.get("product_blueprint", blueprint_id)
        if blueprint is None or str(blueprint.get("tenant_id") or "") != ctx.tenant_id:
            raise ProductFactoryError("blueprint_not_found", "blueprint_not_found", 404)
        return blueprint

    # ------------------------------------------------------------------
    # Archetypes
    # ------------------------------------------------------------------
    def archetypes(self) -> list[dict[str, Any]]:
        records = self.platform.repository.list("product_archetype")
        if records:
            return records
        seeded = []
        for archetype in PRODUCT_ARCHETYPES:
            seeded.append(self.platform.repository.upsert("product_archetype", {**archetype, "created_at": _now(), "updated_at": _now()}))
        return seeded

    def get_archetype(self, archetype_id: str) -> dict[str, Any] | None:
        return self.platform.repository.get("product_archetype", archetype_id)

    def clone_archetype(self, archetype_id: str, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        archetype = self.get_archetype(archetype_id)
        if archetype is None:
            raise ProductFactoryError("archetype_not_found", "archetype_not_found", 404)
        clone = copy.deepcopy(archetype)
        clone["id"] = _ensure_text(payload.get("id"), _new_id("product-archetype"))
        clone["status"] = "DRAFT"
        clone["tenant_id"] = ctx.tenant_id
        clone["organization_id"] = ctx.organization_id
        clone["source_archetype_id"] = archetype["id"]
        clone["name"] = _ensure_text(payload.get("name"), archetype["name"])
        clone["overrides"] = _ensure_dict(payload.get("overrides"))
        clone["created_at"] = _now()
        clone["updated_at"] = _now()
        self.platform.repository.upsert("product_archetype", clone)
        self._append_event("product_archetype.cloned", ctx, clone["id"], {"source_archetype_id": archetype["id"]})
        return clone

    def publish_archetype(self, archetype_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        archetype = self.get_archetype(archetype_id)
        if archetype is None:
            raise ProductFactoryError("archetype_not_found", "archetype_not_found", 404)
        archetype["status"] = "PUBLISHED"
        archetype["updated_at"] = _now()
        self.platform.repository.upsert("product_archetype", archetype)
        return archetype

    def deprecate_archetype(self, archetype_id: str, ctx: ProductFactoryContext) -> dict[str, Any]:
        archetype = self.get_archetype(archetype_id)
        if archetype is None:
            raise ProductFactoryError("archetype_not_found", "archetype_not_found", 404)
        archetype["status"] = "DEPRECATED"
        archetype["updated_at"] = _now()
        self.platform.repository.upsert("product_archetype", archetype)
        return archetype

    # ------------------------------------------------------------------
    # Phases and traceability
    # ------------------------------------------------------------------
    def phases(self, ctx: ProductFactoryContext) -> list[dict[str, Any]]:
        phases = self.platform.repository.list("product_phase")
        if not phases:
            phases = [
                self.platform.repository.upsert(
                    "product_phase",
                    {
                        "id": _new_id("product-phase"),
                        "tenant_id": ctx.tenant_id,
                        "organization_id": ctx.organization_id,
                        "name": phase["name"],
                        "phase_key": phase["id"],
                        "status": "Not Started",
                        "entry_criteria": list(phase["entry_criteria"]),
                        "exit_criteria": list(phase["exit_criteria"]),
                        "deliverables": list(phase["deliverables"]),
                        "readiness_score": 0,
                        "gate_decision": "Deferred",
                        "tasks": [],
                        "owners": [],
                        "contributors": [],
                        "reviewers": [],
                        "approvers": [],
                        "dependencies": [],
                        "risks": [],
                        "issues": [],
                        "decisions": [],
                        "comments": [],
                        "attachments": [],
                        "evidence": [],
                        "history": [],
                        "linked_requirements": [],
                        "linked_tests": [],
                        "linked_releases": [],
                        "created_at": _now(),
                        "updated_at": _now(),
                    },
                )
                for phase in PHASES
            ]
        return [phase for phase in phases if str(phase.get("tenant_id") or "") == ctx.tenant_id]

    def transition_phase(self, phase_id: str, status: str, ctx: ProductFactoryContext, *, note: str = "") -> dict[str, Any]:
        phase = self.platform.repository.get("product_phase", phase_id)
        if phase is None or str(phase.get("tenant_id") or "") != ctx.tenant_id:
            raise ProductFactoryError("phase_not_found", "phase_not_found", 404)
        current = str(phase.get("status") or "Not Started")
        if status not in PHASE_TRANSITIONS.get(current, set()):
            raise ProductFactoryError("invalid_phase_transition", "invalid_phase_transition")
        phase["status"] = status
        phase["history"] = list(phase.get("history") or []) + [{"status": status, "at": _now(), "actor": ctx.actor_id, "note": note}]
        phase["updated_at"] = _now()
        phase["readiness_score"] = min(int(phase.get("readiness_score") or 0) + 10, 100)
        phase["gate_decision"] = "Approved" if status in {"Approved", "Completed"} else phase.get("gate_decision") or "Deferred"
        self.platform.repository.upsert("product_phase", phase)
        self._append_event("product_phase.transitioned", ctx, phase_id, {"status": status})
        return phase

    def traceability_matrix(self, ctx: ProductFactoryContext) -> dict[str, Any]:
        requests = self.requests(ctx)
        blueprints = self.blueprints(ctx)
        phases = self.phases(ctx)
        links = self.platform.repository.list("product_trace_link")
        evidence = self.evidence(ctx)
        matrix = []
        for request in requests:
            linked_blueprint = next((item for item in blueprints if item.get("request_id") == request["id"]), None)
            linked_phase = next((item for item in phases if request["id"] in _ensure_list(item.get("linked_requirements"))), None)
            matrix.append(
                {
                    "requirement_id": request["id"],
                    "requirement": request["name"],
                    "source_code_paths": linked_blueprint and linked_blueprint.get("capabilities") or [],
                    "test_ids": [item.get("id") for item in links if item.get("request_id") == request["id"]],
                    "evidence_ids": [item["id"] for item in evidence if item.get("request_id") == request["id"]],
                    "status": request.get("status"),
                    "linked_phase": linked_phase and linked_phase.get("name"),
                }
            )
        return {"generated_at": _now(), "matrix": matrix, "coverage": {"requirements": len(requests), "links": len(links), "evidence": len(evidence)}}

    # ------------------------------------------------------------------
    # Evidence / approvals / audit
    # ------------------------------------------------------------------
    def approvals(self, ctx: ProductFactoryContext | None = None) -> list[dict[str, Any]]:
        tenant_id = str(getattr(ctx, "tenant_id", "") or "")
        return [
            approval
            for approval in self.platform.approvals()
            if not tenant_id or str(approval.get("tenant_id") or "") == tenant_id
        ]

    def evidence(self, ctx: ProductFactoryContext) -> list[dict[str, Any]]:
        evidence = self.platform.repository.list("product_evidence")
        return [item for item in evidence if str(item.get("tenant_id") or "") == ctx.tenant_id]

    def create_evidence(self, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        evidence = {
            "id": str(payload.get("id") or _new_id("product-evidence")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "request_id": _ensure_text(payload.get("request_id")),
            "blueprint_id": _ensure_text(payload.get("blueprint_id")),
            "phase_id": _ensure_text(payload.get("phase_id")),
            "gate_id": _ensure_text(payload.get("gate_id")),
            "title": _ensure_text(payload.get("title"), "Evidence"),
            "type": _ensure_text(payload.get("type"), "artifact"),
            "subject": _ensure_text(payload.get("subject")),
            "actor": ctx.actor_id,
            "correlation_id": _ensure_text(payload.get("correlation_id"), ctx.project_id or ctx.tenant_id),
            "integrity_status": _ensure_text(payload.get("integrity_status"), "VERIFIED"),
            "source_records": _ensure_list(payload.get("source_records")),
            "timeline": _ensure_list(payload.get("timeline")),
            "verification_status": _ensure_text(payload.get("verification_status"), "PASS"),
            "manifest": _ensure_dict(payload.get("manifest")),
            "result": _ensure_text(payload.get("result"), "PASS"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.platform.repository.upsert("product_evidence", evidence)
        self._append_event("product_evidence.created", ctx, evidence["id"], {"subject": evidence["subject"], "type": evidence["type"]})
        return evidence

    def audit(self, ctx: ProductFactoryContext, limit: int = 100) -> list[dict[str, Any]]:
        prefix = f"{ctx.tenant_id}:"
        return [
            item
            for item in self.platform.audit(limit=limit)
            if not ctx.tenant_id or str(item.get("detail") or "").startswith(prefix)
        ]

    def create_gate_decision(self, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        gate = {
            "id": str(payload.get("id") or _new_id("product-gate")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "name": _ensure_text(payload.get("name"), "Gate"),
            "phase_id": _ensure_text(payload.get("phase_id")),
            "release_id": _ensure_text(payload.get("release_id")),
            "decision": _ensure_text(payload.get("decision"), "Deferred"),
            "decision_maker": _ensure_text(payload.get("decision_maker"), ctx.actor_id),
            "role": _ensure_text(payload.get("role"), ctx.role),
            "timestamp": _ensure_text(payload.get("timestamp"), _now()),
            "evidence": _ensure_list(payload.get("evidence")),
            "conditions": _ensure_list(payload.get("conditions")),
            "exceptions": _ensure_list(payload.get("exceptions")),
            "rationale": _ensure_text(payload.get("rationale")),
            "expiry": _ensure_text(payload.get("expiry")),
            "linked_commit": _ensure_text(payload.get("linked_commit")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.platform.repository.upsert("product_gate", gate)
        self._append_event("product_gate.decided", ctx, gate["id"], {"decision": gate["decision"], "phase_id": gate["phase_id"]})
        return gate

    def improvement_backlog(self, ctx: ProductFactoryContext) -> list[dict[str, Any]]:
        return [
            item
            for item in self.platform.repository.list("product_improvement")
            if str(item.get("tenant_id") or "") == ctx.tenant_id
        ]

    def create_improvement(self, payload: dict[str, Any], ctx: ProductFactoryContext) -> dict[str, Any]:
        improvement = {
            "id": str(payload.get("id") or _new_id("product-improvement")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "title": _ensure_text(payload.get("title"), "Improvement"),
            "description": _ensure_text(payload.get("description")),
            "source": _ensure_text(payload.get("source"), "analytics"),
            "priority": _ensure_text(payload.get("priority"), "medium"),
            "status": _ensure_text(payload.get("status"), "Open"),
            "linked_request_id": _ensure_text(payload.get("linked_request_id")),
            "linked_requirement_id": _ensure_text(payload.get("linked_requirement_id")),
            "linked_release_id": _ensure_text(payload.get("linked_release_id")),
            "evidence": _ensure_list(payload.get("evidence")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.platform.repository.upsert("product_improvement", improvement)
        return improvement

    def demo_product(self, ctx: ProductFactoryContext) -> dict[str, Any]:
        requests = self.requests(ctx)
        if requests:
            return requests[0]
        request = self.create_request(
            {
                "product_name": "NovaFactory Demo",
                "product_description": "Synthetic demonstration product for governed SDLC and release governance.",
                "core_business_problem": "Provide a repeatable governed product factory baseline.",
                "target_users": ["Product Manager", "Architect", "Engineer", "QA Engineer", "Operations"],
                "target_market": "Enterprise",
                "industry": "Software Platform",
                "product_category": "Digital Product Factory",
                "business_model": "Internal platform",
                "revenue_model": "Cost center",
                "geographic_scope": "Australia",
                "supported_languages": ["en-AU"],
                "supported_currencies": ["AUD"],
                "regulatory_requirements": ["privacy", "security", "audit"],
                "data_classification": "INTERNAL",
                "data_residency": "Australia",
                "required_integrations": ["NovaID", "NovaPay", "NovaRide"],
                "supported_platforms": ["Web"],
                "supported_devices": ["Desktop", "Tablet"],
                "expected_usage": "Internal enterprise usage",
                "transaction_volume": "Low",
                "availability_target": "99.9%",
                "performance_target": "sub-second common actions",
                "security_classification": "Sensitive internal",
                "accessibility_requirements": ["WCAG 2.2 AA"],
                "branding_requirements": ["NovaTech"],
                "delivery_priority": "High",
                "budget_constraints": "Controlled",
                "timeline_constraints": "Quarterly",
                "known_risks": ["Scope creep", "Approval delays"],
                "existing_systems": ["NovaCodePro"],
                "migration_requirements": ["Preserve history"],
                "operational_requirements": ["Audit trail", "Observability"],
                "support_requirements": ["Support escalation", "Evidence retention"],
                "reviewer_assignment": ctx.actor_id,
                "status": "Approved",
            },
            ctx,
        )
        self.create_blueprint(
            request["id"],
            {
                "vision": "One governed product factory.",
                "mission": "Take a product from concept to production with traceability.",
                "capabilities": ["request intake", "requirements", "design", "architecture", "development", "testing", "release"],
                "mvp_scope": ["request intake", "blueprint", "traceability", "gate review"],
                "future_scope": ["mobile generation", "external integrations", "multi-tenant ecosystems"],
                "recommended_architecture": "Existing NovaCodePro workspace plus governed service layer",
                "technology_profile": "Python backend, React frontend, SQLite/Postgres-ready repository",
                "delivery_strategy": "Iterative governed phases",
                "roadmap": ["planning", "design", "build", "verify", "deploy"],
                "status": "Approved",
            },
            ctx,
        )
        return request

    def _approval_record(self, ctx: ProductFactoryContext, *, subject: str, gate: str, decision: str, evidence: list[str], approval_ref: str = "") -> dict[str, Any]:
        approval = {
            "id": str(_new_id("product-approval")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "subject": subject,
            "gate": gate,
            "decision": decision,
            "decision_maker": ctx.actor_id,
            "role": ctx.role,
            "approval_ref": approval_ref,
            "evidence": list(evidence),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.platform.repository.upsert("approval", approval)
        return approval

    def _audit(self, ctx: ProductFactoryContext, kind: str, subject: str, action: str, detail: str) -> dict[str, Any]:
        return self.platform.repository.append_audit(
            kind=kind,
            actor=ctx.actor_id,
            service="NovaCodePro Product Factory",
            subject=subject,
            action=action,
            evidence=detail,
            detail=f"{ctx.tenant_id}:{detail}",
        )

    def _append_event(self, event_type: str, ctx: ProductFactoryContext, aggregate_id: str, data: dict[str, Any]) -> None:
        self.platform.repository.append_event(
            {
                "event_id": _new_id("pf-event"),
                "occurred_at": _now(),
                "event_type": event_type,
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "project_id": ctx.project_id or None,
                "workflow_id": ctx.project_id or None,
                "actor": {"type": "user", "id": ctx.actor_id},
                "correlation_id": aggregate_id,
                "causation_id": aggregate_id,
                "metadata": {"source": "product-factory"},
                "data": data,
            }
        )


def build_product_factory_context(
    claims: Any,
    *,
    project_id: str | None = None,
    environment: str | None = None,
) -> ProductFactoryContext:
    tenant_id = str(getattr(claims, "organization_id", "") or getattr(claims, "tenant_id", "") or "")
    return ProductFactoryContext(
        tenant_id=tenant_id,
        organization_id=tenant_id,
        project_id=str(project_id or ""),
        environment=str(environment or "development"),
        actor_id=str(getattr(claims, "sub", "") or "NovaCodePro"),
        role=str(getattr(claims, "role", "") or "OPERATOR"),
    )


__all__ = [
    "CAPABILITY_INVENTORY",
    "PHASES",
    "PHASE_STATES",
    "PHASE_TRANSITIONS",
    "PRODUCT_ARCHETYPES",
    "ProductFactoryContext",
    "ProductFactoryError",
    "ProductFactoryService",
    "REQUEST_STATES",
    "BLUEPRINT_STATES",
    "build_product_factory_context",
]

from .product_factory_enterprise import ProductFactoryEnterpriseService  # noqa: E402
