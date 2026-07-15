from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .enterprise_os import default_agent_registry, select_agent_team
from .platform import NovaCodeProPlatform
from .workflow_fabric import WorkflowFabricService


SOLUTION_LIFECYCLE = (
    "IDEA",
    "DISCOVERY",
    "REQUIREMENTS_DRAFT",
    "REQUIREMENTS_REVIEW",
    "REQUIREMENTS_APPROVED",
    "SOLUTION_DESIGN",
    "ARCHITECTURE_REVIEW",
    "DESIGN_APPROVED",
    "PLANNED",
    "IMPLEMENTING",
    "TESTING",
    "SECURITY_REVIEW",
    "COMPLIANCE_REVIEW",
    "CUSTOMER_REVIEW",
    "RELEASE_APPROVED",
    "DEPLOYING",
    "DEPLOYED",
    "ACCEPTANCE_TESTING",
    "ACCEPTED",
    "OPERATING",
    "ENHANCEMENT",
    "RETIRED",
)

SOLUTION_LIFECYCLE_TRANSITIONS: dict[str, set[str]] = {
    "IDEA": {"DISCOVERY", "RETIRED"},
    "DISCOVERY": {"REQUIREMENTS_DRAFT", "RETIRED"},
    "REQUIREMENTS_DRAFT": {"REQUIREMENTS_REVIEW", "DISCOVERY"},
    "REQUIREMENTS_REVIEW": {"REQUIREMENTS_APPROVED", "REQUIREMENTS_DRAFT"},
    "REQUIREMENTS_APPROVED": {"SOLUTION_DESIGN", "ENHANCEMENT"},
    "SOLUTION_DESIGN": {"ARCHITECTURE_REVIEW", "REQUIREMENTS_APPROVED"},
    "ARCHITECTURE_REVIEW": {"DESIGN_APPROVED", "SOLUTION_DESIGN"},
    "DESIGN_APPROVED": {"PLANNED", "ARCHITECTURE_REVIEW"},
    "PLANNED": {"IMPLEMENTING", "RETIRED"},
    "IMPLEMENTING": {"TESTING", "PLANNED"},
    "TESTING": {"SECURITY_REVIEW", "IMPLEMENTING"},
    "SECURITY_REVIEW": {"COMPLIANCE_REVIEW", "TESTING"},
    "COMPLIANCE_REVIEW": {"CUSTOMER_REVIEW", "SECURITY_REVIEW"},
    "CUSTOMER_REVIEW": {"RELEASE_APPROVED", "REQUIREMENTS_DRAFT"},
    "RELEASE_APPROVED": {"DEPLOYING", "CUSTOMER_REVIEW"},
    "DEPLOYING": {"DEPLOYED", "RELEASE_APPROVED"},
    "DEPLOYED": {"ACCEPTANCE_TESTING", "DEPLOYING"},
    "ACCEPTANCE_TESTING": {"ACCEPTED", "DEPLOYED"},
    "ACCEPTED": {"OPERATING", "ENHANCEMENT"},
    "OPERATING": {"ENHANCEMENT", "RETIRED"},
    "ENHANCEMENT": {"REQUIREMENTS_DRAFT", "OPERATING"},
    "RETIRED": set(),
}

CHAT_STATUS = (
    "REQUESTED",
    "ANALYZING",
    "CLARIFICATION_REQUIRED",
    "PLANNING",
    "GENERATING",
    "DRAFT",
    "IN_REVIEW",
    "CHANGES_REQUESTED",
    "APPROVAL_PENDING",
    "APPROVED",
    "EXECUTION_READY",
    "EXECUTING",
    "VERIFIED",
    "SAVED",
    "REJECTED",
    "SUPERSEDED",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str, payload: dict[str, Any] | None = None) -> str:
    body = json.dumps(payload or {}, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{prefix}:{body}:{_now()}".encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:12]}"


def _canonical_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _provenance(
    *,
    request: str,
    requirement_ids: list[str] | None = None,
    plan_task_id: str = "",
    generator: str = "NovaCodePro",
    version: str = "1",
    review_status: str = "DRAFT",
    approval_status: str = "PENDING",
) -> dict[str, Any]:
    return {
        "request": request,
        "requirement_ids": list(requirement_ids or []),
        "plan_task_id": plan_task_id,
        "generator": generator,
        "version": version,
        "review_status": review_status,
        "approval_status": approval_status,
    }


def _base_record(
    *,
    kind: str,
    tenant_id: str,
    organization_id: str,
    project_id: str = "",
    customer_id: str = "",
    owner: str = "NovaCodePro",
    created_by: str = "NovaCodePro",
    environment: str = "development",
    classification: str = "INTERNAL",
    retention_policy: str = "seven_years",
    version: str = "1",
    status: str = "IDEA",
    correlation_id: str = "",
    evidence_refs: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    created_at = _now()
    record = {
        "id": _new_id(kind),
        "tenant_id": tenant_id,
        "organization_id": organization_id,
        "customer_id": customer_id,
        "project_id": project_id,
        "environment": environment,
        "status": status,
        "version": version,
        "owner": owner,
        "created_by": created_by,
        "created_at": created_at,
        "updated_at": created_at,
        "correlation_id": correlation_id or project_id or tenant_id,
        "classification": classification,
        "retention_policy": retention_policy,
        "evidence_refs": list(evidence_refs or []),
        "history": [],
    }
    if extra:
        record.update(extra)
    return record


@dataclass(frozen=True)
class SolutionEngineeringContext:
    tenant_id: str
    organization_id: str
    project_id: str
    customer_id: str = ""
    environment: str = "development"
    actor_id: str = "NovaCodePro"
    role: str = "OPERATOR"


class SolutionEngineeringError(RuntimeError):
    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code


class SolutionEngineeringService:
    def __init__(self, platform: NovaCodeProPlatform, workflow_fabric: WorkflowFabricService | None = None) -> None:
        self.platform = platform
        self.workflow_fabric = workflow_fabric or WorkflowFabricService(platform)

    # -- core records -------------------------------------------------
    def create_customer(self, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        record = _base_record(
            kind="customer_organization",
            tenant_id=str(payload["tenant_id"]),
            organization_id=str(payload.get("organization_id") or payload["tenant_id"]),
            customer_id=str(payload.get("customer_id") or payload.get("id") or ""),
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=str(payload.get("environment") or "development"),
            classification=str(payload.get("classification") or "INTERNAL"),
            retention_policy=str(payload.get("retention_policy") or "seven_years"),
            status="ACTIVE",
            correlation_id=str(payload.get("correlation_id") or payload.get("id") or ""),
            extra={
                "name": str(payload.get("name") or payload.get("id") or "Customer"),
                "segment": str(payload.get("segment") or "enterprise"),
                "country": str(payload.get("country") or ""),
            },
        )
        self.platform.repository.upsert("customer_organization", record)
        self._publish("CustomerCreated", record)
        return record

    def create_workspace(self, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        record = _base_record(
            kind="customer_workspace",
            tenant_id=str(payload["tenant_id"]),
            organization_id=str(payload.get("organization_id") or payload["tenant_id"]),
            customer_id=str(payload.get("customer_id") or ""),
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=str(payload.get("environment") or "development"),
            status="ACTIVE",
            correlation_id=str(payload.get("correlation_id") or payload.get("project_id") or ""),
            extra={
                "name": str(payload.get("name") or "Customer Workspace"),
                "project_id": str(payload.get("project_id") or ""),
                "windows": list(payload.get("windows") or []),
                "contexts": list(payload.get("contexts") or ["identity", "knowledge", "workflow", "evidence"]),
                "navigation": list(payload.get("navigation") or []),
            },
        )
        self.platform.repository.upsert("customer_workspace", record)
        self._publish("WorkspaceCreated", record)
        return record

    def create_project(self, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        customer_id = str(payload.get("customer_id") or payload["tenant_id"])
        workflow = self.workflow_fabric.create_workflow(
            {
                "title": str(payload.get("name") or payload.get("title") or "Customer solution"),
                "request": str(payload.get("idea") or payload.get("request") or "Customer solution request"),
                "tenant_id": str(payload["tenant_id"]),
                "project_id": str(payload.get("project_id") or ""),
                "domain": str(payload.get("domain") or "solution-engineering"),
                "region": str(payload.get("region") or "Australia"),
                "template_id": str(payload.get("template_id") or "solution-engineering"),
                "surfaces": list(payload.get("surfaces") or ["dashboard", "discovery", "requirements", "architecture", "engineering"]),
            },
            actor=actor,
        )
        record = _base_record(
            kind="customer_project",
            tenant_id=str(payload["tenant_id"]),
            organization_id=str(payload.get("organization_id") or payload["tenant_id"]),
            customer_id=customer_id,
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=str(payload.get("environment") or "development"),
            classification=str(payload.get("classification") or "INTERNAL"),
            retention_policy=str(payload.get("retention_policy") or "seven_years"),
            status="IDEA",
            correlation_id=workflow["id"],
            extra={
                "name": str(payload.get("name") or payload.get("title") or "Customer project"),
                "summary": str(payload.get("summary") or payload.get("idea") or payload.get("request") or ""),
                "workflow_id": workflow["id"],
                "customer_id": customer_id,
                "stage": "IDEA",
                "deliverables": [],
                "approvals": [],
                "artifacts": [],
                "agents": [],
                "timeline": [{"action": "project.created", "at": _now(), "actor": actor, "status": "IDEA"}],
            },
        )
        self.platform.repository.upsert("customer_project", record)
        self._publish("ProjectCreated", record, workflow_id=workflow["id"])
        self.platform.create_knowledge_node(
            {
                "id": f"knowledge-{record['id']}",
                "label": record["name"],
                "type": "solution-project",
                "tenant_id": record["tenant_id"],
                "owner": actor,
                "evidence": [record["id"]],
            }
        )
        return record

    # -- discovery ----------------------------------------------------
    def submit_idea(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="business_idea",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="IDEA",
            correlation_id=project["workflow_id"],
            extra={
                "title": str(payload.get("title") or project["name"]),
                "problem": str(payload.get("problem") or payload.get("idea") or project["summary"]),
                "target_users": list(payload.get("target_users") or []),
                "market": str(payload.get("market") or ""),
                "industry": str(payload.get("industry") or ""),
                "budget_range": str(payload.get("budget_range") or ""),
                "timeline": str(payload.get("timeline") or ""),
            },
        )
        self.platform.repository.upsert("business_idea", record)
        self._transition_project(project, "DISCOVERY", actor=actor, evidence_ref=record["id"], note="idea submitted")
        self._publish("DiscoveryCompleted", record, workflow_id=project["workflow_id"])
        return record

    def run_discovery(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="discovery_session",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="DISCOVERY",
            correlation_id=project["workflow_id"],
            extra={
                "template": str(payload.get("template") or "enterprise"),
                "discovery_summary": str(payload.get("discovery_summary") or ""),
                "objectives": list(payload.get("objectives") or []),
                "stakeholders": list(payload.get("stakeholders") or []),
                "assumptions": list(payload.get("assumptions") or []),
                "constraints": list(payload.get("constraints") or []),
                "dependencies": list(payload.get("dependencies") or []),
                "risks": list(payload.get("risks") or []),
                "opportunities": list(payload.get("opportunities") or []),
                "success_criteria": list(payload.get("success_criteria") or []),
                "initial_scope": list(payload.get("initial_scope") or []),
                "out_of_scope": list(payload.get("out_of_scope") or []),
                "recommended_solution_types": list(payload.get("recommended_solution_types") or []),
                "follow_up_questions": list(payload.get("follow_up_questions") or []),
            },
        )
        self.platform.repository.upsert("discovery_session", record)
        self._transition_project(project, "REQUIREMENTS_DRAFT", actor=actor, evidence_ref=record["id"], note="discovery complete")
        return record

    # -- requirements -------------------------------------------------
    def create_requirement(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="requirement",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="DRAFT",
            correlation_id=project["workflow_id"],
            extra={
                "summary": str(payload.get("summary") or payload.get("title") or ""),
                "kind": str(payload.get("kind") or "functional"),
                "priority": str(payload.get("priority") or "medium"),
                "acceptance_criteria": list(payload.get("acceptance_criteria") or []),
                "dependencies": list(payload.get("dependencies") or []),
                "trace_links": list(payload.get("trace_links") or []),
                "test_links": list(payload.get("test_links") or []),
                "version": str(payload.get("version") or "1"),
            },
        )
        self.platform.repository.upsert("requirement", record)
        self._refresh_requirement_set(project, actor=actor)
        self._transition_project(project, "REQUIREMENTS_REVIEW", actor=actor, evidence_ref=record["id"], note="requirement created")
        return record

    def approve_requirements(self, project_id: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        self._transition_project(project, "REQUIREMENTS_APPROVED", actor=actor, note="requirements approved")
        req_set = self._refresh_requirement_set(project, status="APPROVED", actor=actor)
        return req_set

    def list_requirements(self, project_id: str) -> list[dict[str, Any]]:
        return [record for record in self.platform.repository.list("requirement") if record.get("project_id") == project_id]

    # -- blueprint / architecture / design ----------------------------
    def generate_blueprint(self, project_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        requirements = self.list_requirements(project_id)
        if not requirements:
            raise SolutionEngineeringError("requirements_required", "requirements_required")
        record = _base_record(
            kind="solution_blueprint",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str((payload or {}).get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="DRAFT",
            correlation_id=project["workflow_id"],
            extra={
                "executive_summary": str((payload or {}).get("executive_summary") or project.get("summary") or ""),
                "scope": list((payload or {}).get("scope") or []),
                "personas": list((payload or {}).get("personas") or []),
                "user_journeys": list((payload or {}).get("user_journeys") or []),
                "product_surfaces": list((payload or {}).get("product_surfaces") or []),
                "feature_catalogue": list((payload or {}).get("feature_catalogue") or []),
                "business_processes": list((payload or {}).get("business_processes") or []),
                "architecture": dict((payload or {}).get("architecture") or {}),
                "application_components": list((payload or {}).get("application_components") or []),
                "data_model": dict((payload or {}).get("data_model") or {}),
                "apis": list((payload or {}).get("apis") or []),
                "integrations": list((payload or {}).get("integrations") or []),
                "security": dict((payload or {}).get("security") or {}),
                "privacy": dict((payload or {}).get("privacy") or {}),
                "compliance": dict((payload or {}).get("compliance") or {}),
                "risk": dict((payload or {}).get("risk") or {}),
                "accessibility": dict((payload or {}).get("accessibility") or {}),
                "testing": dict((payload or {}).get("testing") or {}),
                "deployment": dict((payload or {}).get("deployment") or {}),
                "observability": dict((payload or {}).get("observability") or {}),
                "support": dict((payload or {}).get("support") or {}),
                "delivery_roadmap": list((payload or {}).get("delivery_roadmap") or []),
                "cost_assumptions": list((payload or {}).get("cost_assumptions") or []),
                "unresolved_decisions": list((payload or {}).get("unresolved_decisions") or []),
                "requirements_count": len(requirements),
                "provenance": _provenance(
                    request=project["summary"],
                    requirement_ids=[item["id"] for item in requirements],
                    generator="NovaCodePro Solution Engine",
                    version=str((payload or {}).get("version") or "1"),
                    review_status="REVIEWED",
                    approval_status="PENDING",
                ),
            },
        )
        record["sections"] = [
            {"section": "executive_summary", "status": "DRAFT"},
            {"section": "scope", "status": "DRAFT"},
            {"section": "personas", "status": "DRAFT"},
            {"section": "architecture", "status": "DRAFT"},
            {"section": "delivery_roadmap", "status": "DRAFT"},
        ]
        self.platform.repository.upsert("solution_blueprint", record)
        self._transition_project(project, "SOLUTION_DESIGN", actor=actor, evidence_ref=record["id"], note="blueprint generated")
        self._publish("SolutionBlueprintGenerated", record, workflow_id=project["workflow_id"])
        return record

    def review_blueprint_section(self, project_id: str, section: str, *, status: str, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        blueprint = self.get_latest("solution_blueprint", project_id)
        if blueprint is None:
            raise SolutionEngineeringError("blueprint_not_found", "blueprint_not_found")
        allowed = {"DRAFT", "REVIEWED", "APPROVED", "CHANGES_REQUESTED"}
        if status not in allowed:
            raise SolutionEngineeringError("invalid_section_status", "invalid_section_status")
        sections = list(blueprint.get("sections") or [])
        updated = False
        for entry in sections:
            if entry.get("section") == section:
                entry["status"] = status
                entry["reviewed_by"] = actor
                entry["reviewed_at"] = _now()
                updated = True
        if not updated:
            sections.append({"section": section, "status": status, "reviewed_by": actor, "reviewed_at": _now()})
        blueprint["sections"] = sections
        blueprint["updated_at"] = _now()
        self.platform.repository.upsert("solution_blueprint", blueprint)
        if status == "APPROVED":
            self._transition_project(project, "ARCHITECTURE_REVIEW", actor=actor, evidence_ref=blueprint["id"], note=f"blueprint section approved:{section}")
        elif status == "CHANGES_REQUESTED":
            self._transition_project(project, "SOLUTION_DESIGN", actor=actor, evidence_ref=blueprint["id"], note=f"changes requested:{section}")
        return blueprint

    def create_architecture_decision(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="architecture_decision",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="PROPOSED",
            correlation_id=project["workflow_id"],
            extra={
                "title": str(payload.get("title") or "Architecture decision"),
                "decision": str(payload.get("decision") or ""),
                "requirements": list(payload.get("requirements") or []),
                "risks": list(payload.get("risks") or []),
                "policies": list(payload.get("policies") or []),
                "affected_services": list(payload.get("affected_services") or []),
                "implementation_work": list(payload.get("implementation_work") or []),
                "tests": list(payload.get("tests") or []),
                "evidence": list(payload.get("evidence") or []),
                "provenance": _provenance(
                    request=project["summary"],
                    requirement_ids=[item["id"] for item in self.list_requirements(project_id)],
                    generator="NovaCodePro Architecture Studio",
                    version="1",
                    review_status="PROPOSED",
                    approval_status="PENDING",
                ),
            },
        )
        self.platform.repository.upsert("architecture_decision", record)
        return record

    def approve_architecture(self, project_id: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        architecture = self.get_latest("architecture_decision", project_id)
        if architecture is None:
            raise SolutionEngineeringError("architecture_missing", "architecture_missing")
        architecture["status"] = "APPROVED"
        architecture["approved_by"] = actor
        architecture["approved_at"] = _now()
        architecture["updated_at"] = _now()
        self.platform.repository.upsert("architecture_decision", architecture)
        self._transition_project(project, "DESIGN_APPROVED", actor=actor, evidence_ref=architecture["id"], note="architecture approved")
        self._publish("ArchitectureApproved", architecture, workflow_id=project["workflow_id"])
        return architecture

    def create_design_artifact(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="design_artifact",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="DRAFT",
            correlation_id=project["workflow_id"],
            extra={
                "artifact_type": str(payload.get("artifact_type") or "wireframe"),
                "surface": str(payload.get("surface") or "web"),
                "requirements": list(payload.get("requirements") or []),
                "section_statuses": list(payload.get("section_statuses") or []),
                "accessibility_annotations": list(payload.get("accessibility_annotations") or []),
                "localization_annotations": list(payload.get("localization_annotations") or []),
                "prototype_links": list(payload.get("prototype_links") or []),
                "provenance": _provenance(
                    request=project["summary"],
                    requirement_ids=[item["id"] for item in self.list_requirements(project_id)],
                    generator="NovaCodePro UX/UI Studio",
                    version="1",
                ),
            },
        )
        self.platform.repository.upsert("design_artifact", record)
        return record

    # -- planning / release / deployment ------------------------------
    def create_implementation_plan(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="implementation_plan",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="PLANNED",
            correlation_id=project["workflow_id"],
            extra={
                "objectives": list(payload.get("objectives") or []),
                "assumptions": list(payload.get("assumptions") or []),
                "tasks": list(payload.get("tasks") or []),
                "dependencies": list(payload.get("dependencies") or []),
                "responsible_agents": list(payload.get("responsible_agents") or []),
                "required_tools": list(payload.get("required_tools") or []),
                "required_approvals": list(payload.get("required_approvals") or []),
                "expected_outputs": list(payload.get("expected_outputs") or []),
                "validation_rules": list(payload.get("validation_rules") or []),
                "risk_level": str(payload.get("risk_level") or "medium"),
                "provenance": _provenance(
                    request=project["summary"],
                    requirement_ids=[item["id"] for item in self.list_requirements(project_id)],
                    plan_task_id=project["workflow_id"],
                    generator="NovaCodePro Planning Engine",
                    version="1",
                ),
            },
        )
        self.platform.repository.upsert("implementation_plan", record)
        self._transition_project(project, "PLANNED", actor=actor, evidence_ref=record["id"], note="implementation plan created")
        return record

    def start_implementation(self, project_id: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        self._transition_project(project, "IMPLEMENTING", actor=actor, note="implementation started")
        self._publish("ImplementationStarted", project, workflow_id=project["workflow_id"])
        return project

    def record_test_results(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="test_execution",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=actor,
            created_by=actor,
            environment=project["environment"],
            status=str(payload.get("status") or "PASS"),
            correlation_id=project["workflow_id"],
            extra={
                "suite": str(payload.get("suite") or "regression"),
                "scope": list(payload.get("scope") or []),
                "results": list(payload.get("results") or []),
                "coverage": dict(payload.get("coverage") or {}),
                "evidence_refs": list(payload.get("evidence_refs") or []),
            },
        )
        self.platform.repository.upsert("test_execution", record)
        self._transition_project(project, "TESTING", actor=actor, evidence_ref=record["id"], note="tests executed")
        self._publish("TestCompleted", record, workflow_id=project["workflow_id"])
        return record

    def security_review(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="security_review",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=actor,
            created_by=actor,
            environment=project["environment"],
            status=str(payload.get("status") or "APPROVED"),
            correlation_id=project["workflow_id"],
            extra={"findings": list(payload.get("findings") or []), "controls": list(payload.get("controls") or []), "evidence_refs": list(payload.get("evidence_refs") or [])},
        )
        self.platform.repository.upsert("security_review", record)
        self._transition_project(project, "SECURITY_REVIEW", actor=actor, evidence_ref=record["id"], note="security review completed")
        self._publish("SecurityReviewCompleted", record, workflow_id=project["workflow_id"])
        return record

    def compliance_review(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="compliance_review",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=actor,
            created_by=actor,
            environment=project["environment"],
            status=str(payload.get("status") or "APPROVED"),
            correlation_id=project["workflow_id"],
            extra={"obligations": list(payload.get("obligations") or []), "controls": list(payload.get("controls") or []), "evidence_refs": list(payload.get("evidence_refs") or [])},
        )
        self.platform.repository.upsert("compliance_review", record)
        self._transition_project(project, "COMPLIANCE_REVIEW", actor=actor, evidence_ref=record["id"], note="compliance review completed")
        self._publish("ComplianceReviewCompleted", record, workflow_id=project["workflow_id"])
        return record

    def customer_review(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="customer_review",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=actor,
            created_by=actor,
            environment=project["environment"],
            status=str(payload.get("status") or "APPROVED"),
            correlation_id=project["workflow_id"],
            extra={"comments": list(payload.get("comments") or []), "version": str(payload.get("version") or project["version"]), "evidence_refs": list(payload.get("evidence_refs") or [])},
        )
        self.platform.repository.upsert("customer_review", record)
        self._transition_project(project, "CUSTOMER_REVIEW", actor=actor, evidence_ref=record["id"], note="customer review complete")
        self._publish("CustomerReviewCompleted", record, workflow_id=project["workflow_id"])
        return record

    def accept_release_review(self, project_id: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        self._transition_project(project, "ACCEPTANCE_TESTING", actor=actor, note="acceptance testing started")
        return project

    def mark_accepted(self, project_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        self._transition_project(project, "ACCEPTED", actor=actor, evidence_ref=str((payload or {}).get("evidence_ref") or ""), note="customer accepted")
        return project

    def retire(self, project_id: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        self._transition_project(project, "RETIRED", actor=actor, note="retired")
        return project

    def create_release(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="release",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=str(payload.get("environment") or project["environment"]),
            status="DRAFT",
            correlation_id=project["workflow_id"],
            extra={
                "name": str(payload.get("name") or f"Release {project['name']}"),
                "version": str(payload.get("version") or "1"),
                "status": str(payload.get("status") or "PLANNED"),
                "scope": list(payload.get("scope") or []),
                "quality_gates": list(payload.get("quality_gates") or []),
                "security_gates": list(payload.get("security_gates") or []),
                "compliance_gates": list(payload.get("compliance_gates") or []),
                "rollback_plan": str(payload.get("rollback_plan") or ""),
                "notes": str(payload.get("notes") or ""),
                "provenance": _provenance(
                    request=project["summary"],
                    requirement_ids=[item["id"] for item in self.list_requirements(project_id)],
                    generator="NovaCodePro Release Studio",
                    version=str(payload.get("version") or "1"),
                    review_status="PENDING",
                    approval_status="PENDING",
                ),
            },
        )
        self.platform.repository.upsert("solution_release", record)
        return record

    def approve_release(self, release_id: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        release = self.platform.repository.get("solution_release", release_id)
        if release is None:
            raise SolutionEngineeringError("release_not_found", "release_not_found")
        release["status"] = "APPROVED"
        release["approved_by"] = actor
        release["approved_at"] = _now()
        release["updated_at"] = _now()
        self.platform.repository.upsert("solution_release", release)
        project = self._project(release["project_id"])
        self._transition_project(project, "RELEASE_APPROVED", actor=actor, evidence_ref=release_id, note="release approved")
        self._publish("ReleaseApproved", release, workflow_id=project["workflow_id"])
        return release

    def deploy_release(self, release_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        release = self.platform.repository.get("solution_release", release_id)
        if release is None:
            raise SolutionEngineeringError("release_not_found", "release_not_found")
        if str(release.get("status") or "").upper() != "APPROVED":
            raise SolutionEngineeringError("release_not_approved", "release_not_approved")
        project = self._project(release["project_id"])
        self._transition_project(project, "DEPLOYING", actor=actor, note="deployment started")
        release["status"] = "DEPLOYED"
        release["deployed_by"] = actor
        release["deployed_at"] = _now()
        release["image_digest"] = str((payload or {}).get("image_digest") or "")
        release["migration_version"] = str((payload or {}).get("migration_version") or "")
        release["verification"] = dict((payload or {}).get("verification") or {})
        release["evidence_hash"] = _canonical_hash({"release_id": release_id, "payload": payload or {}})
        self.platform.repository.upsert("solution_release", release)
        deployment = _base_record(
            kind="deployment",
            tenant_id=release["tenant_id"],
            organization_id=release["organization_id"],
            customer_id=release["customer_id"],
            project_id=release["project_id"],
            owner=actor,
            created_by=actor,
            environment=str((payload or {}).get("environment") or release["environment"]),
            status="DEPLOYED",
            correlation_id=release["correlation_id"],
            extra={
                "release_id": release_id,
                "plan": dict((payload or {}).get("plan") or {}),
                "change_summary": str((payload or {}).get("change_summary") or ""),
                "artifact_refs": list((payload or {}).get("artifact_refs") or []),
                "approvers": list((payload or {}).get("approvers") or []),
                "result": str((payload or {}).get("result") or "success"),
                "verification": dict((payload or {}).get("verification") or {}),
                "evidence_hash": release["evidence_hash"],
                "provenance": _provenance(
                    request=project["summary"],
                    requirement_ids=[item["id"] for item in self.list_requirements(project["id"])],
                    generator="NovaCodePro Deployment Studio",
                    version=release["version"],
                    review_status="APPROVED",
                    approval_status="APPROVED",
                ),
            },
        )
        self.platform.repository.upsert("solution_deployment", deployment)
        self._transition_project(project, "DEPLOYED", actor=actor, evidence_ref=deployment["id"], note="deployment completed")
        self._publish("DeploymentCompleted", deployment, workflow_id=project["workflow_id"])
        return deployment

    def accept_release(self, release_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        release = self.platform.repository.get("solution_release", release_id)
        if release is None:
            raise SolutionEngineeringError("release_not_found", "release_not_found")
        if str(release.get("status") or "").upper() != "DEPLOYED":
            raise SolutionEngineeringError("release_not_deployed", "release_not_deployed")
        project = self._project(release["project_id"])
        self._transition_project(project, "ACCEPTANCE_TESTING", actor=actor, note="acceptance testing started")
        acceptance = _base_record(
            kind="acceptance_record",
            tenant_id=release["tenant_id"],
            organization_id=release["organization_id"],
            customer_id=release["customer_id"],
            project_id=release["project_id"],
            owner=actor,
            created_by=actor,
            environment=release["environment"],
            status="ACCEPTED",
            correlation_id=release["correlation_id"],
            extra={
                "release_id": release_id,
                "decision": str((payload or {}).get("decision") or "ACCEPTED"),
                "evidence_hash": str((payload or {}).get("evidence_hash") or release.get("evidence_hash") or ""),
                "version": release["version"],
                "comments": list((payload or {}).get("comments") or []),
            },
        )
        self.platform.repository.upsert("acceptance_record", acceptance)
        self._transition_project(project, "ACCEPTED", actor=actor, evidence_ref=acceptance["id"], note="acceptance recorded")
        self._publish("AcceptanceGranted", acceptance, workflow_id=project["workflow_id"])
        return acceptance

    # -- support / evolution / knowledge ------------------------------
    def open_support_case(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="support_case",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="OPEN",
            correlation_id=project["workflow_id"],
            extra={
                "title": str(payload.get("title") or "Support case"),
                "description": str(payload.get("description") or ""),
                "release_id": str(payload.get("release_id") or ""),
                "severity": str(payload.get("severity") or "medium"),
            },
        )
        self.platform.repository.upsert("support_case", record)
        self._publish("SupportCaseOpened", record, workflow_id=project["workflow_id"])
        return record

    def create_enhancement_request(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="enhancement_request",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="PROPOSED",
            correlation_id=project["workflow_id"],
            extra={
                "title": str(payload.get("title") or "Enhancement request"),
                "impact": str(payload.get("impact") or ""),
                "priority": str(payload.get("priority") or "medium"),
                "source": str(payload.get("source") or "customer"),
            },
        )
        self.platform.repository.upsert("enhancement_request", record)
        self._transition_project(project, "ENHANCEMENT", actor=actor, evidence_ref=record["id"], note="enhancement requested")
        self._publish("EnhancementApproved", record, workflow_id=project["workflow_id"])
        return record

    def publish_knowledge(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="knowledge_record",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="APPROVED",
            correlation_id=project["workflow_id"],
            extra={
                "category": str(payload.get("category") or "delivery"),
                "title": str(payload.get("title") or project["name"]),
                "summary": str(payload.get("summary") or ""),
                "source_record_ids": list(payload.get("source_record_ids") or []),
                "evidence_hash": str(payload.get("evidence_hash") or ""),
            },
        )
        self.platform.repository.upsert("knowledge_record", record)
        self._publish("KnowledgePublished", record, workflow_id=project["workflow_id"])
        return record

    def create_evidence(self, project_id: str, payload: dict[str, Any], *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        record = _base_record(
            kind="evidence_record",
            tenant_id=project["tenant_id"],
            organization_id=project["organization_id"],
            customer_id=project["customer_id"],
            project_id=project["id"],
            owner=str(payload.get("owner") or actor),
            created_by=actor,
            environment=project["environment"],
            status="APPROVED",
            correlation_id=project["workflow_id"],
            extra={
                "category": str(payload.get("category") or "solution-engineering"),
                "artifact_refs": list(payload.get("artifact_refs") or []),
                "evidence_hash": str(payload.get("evidence_hash") or _canonical_hash(payload)),
                "notes": str(payload.get("notes") or ""),
            },
        )
        self.platform.repository.upsert("evidence_record", record)
        self._transition_project(project, "OPERATING", actor=actor, evidence_ref=record["id"], note="evidence generated")
        self._publish("EvidenceGenerated", record, workflow_id=project["workflow_id"])
        return record

    # -- read models --------------------------------------------------
    def get_latest(self, kind: str, project_id: str) -> dict[str, Any] | None:
        records = [record for record in self.platform.repository.list(kind) if record.get("project_id") == project_id]
        return records[0] if records else None

    def project(self, project_id: str) -> dict[str, Any]:
        project = self._project(project_id)
        project["requirements"] = self.list_requirements(project_id)
        project["blueprint"] = self.get_latest("solution_blueprint", project_id)
        project["architecture"] = self.get_latest("architecture_decision", project_id)
        project["release"] = self._latest_by_project("solution_release", project_id)
        project["acceptance"] = self._latest_by_project("acceptance_record", project_id)
        project["support_cases"] = self._records_for_project("support_case", project_id)
        project["enhancements"] = self._records_for_project("enhancement_request", project_id)
        project["knowledge"] = self._records_for_project("knowledge_record", project_id)
        project["evidence"] = self._records_for_project("evidence_record", project_id)
        return project

    def replay(self, project_id: str) -> dict[str, Any]:
        project = self._project(project_id)
        events = self.platform.repository.list_events_for_aggregate(project["workflow_id"], limit=500)
        return {"project": self.project(project_id), "timeline": list(project.get("timeline") or []), "events": events}

    def customer_dashboard(self, project_id: str) -> dict[str, Any]:
        project = self.project(project_id)
        return {
            "project_id": project["id"],
            "customer_id": project["customer_id"],
            "current_stage": project["stage"],
            "pending_reviews": len([item for item in project.get("approvals") or [] if str(item.get("status") or "").upper() != "APPROVED"]),
            "milestones": len(project.get("deliverables") or []),
            "risks": [],
            "release_status": (project.get("release") or {}).get("status"),
            "support_cases": len(project.get("support_cases") or []),
            "latest_deliverables": [item.get("title") for item in project.get("deliverables") or []],
            "evidence_refs": list(project.get("evidence_refs") or []),
        }

    def plan_agent_tasks(self, project_id: str, request: str, *, actor: str = "NovaCodePro") -> dict[str, Any]:
        project = self._project(project_id)
        team_ids = select_agent_team(request, "high")
        registry = {item["id"]: item for item in default_agent_registry()}
        tasks = []
        for idx, agent_id in enumerate(team_ids, start=1):
            agent = registry.get(agent_id)
            if not agent:
                continue
            task = {
                "id": _new_id("agent-task", {"project": project_id, "agent": agent_id, "index": idx}),
                "project_id": project_id,
                "tenant_id": project["tenant_id"],
                "agent_id": agent_id,
                "agent_name": agent["name"],
                "status": "PLANNED",
                "task_order": idx,
                "requested_by": actor,
                "input": {"request": request},
                "output": {},
                "tool_allowlist": list(agent.get("tools") or []),
                "evidence_refs": [],
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.platform.repository.upsert("agent_task", task)
            tasks.append(task)
        project["agents"] = tasks
        project["updated_at"] = _now()
        self.platform.repository.upsert("customer_project", project)
        return {"project_id": project_id, "tasks": tasks}

    # -- internals ----------------------------------------------------
    def _project(self, project_id: str) -> dict[str, Any]:
        project = self.platform.repository.get("customer_project", project_id)
        if project is None:
            raise SolutionEngineeringError("project_not_found", "project_not_found")
        return project

    def _latest_by_project(self, kind: str, project_id: str) -> dict[str, Any] | None:
        records = [record for record in self.platform.repository.list(kind) if record.get("project_id") == project_id]
        return records[0] if records else None

    def _records_for_project(self, kind: str, project_id: str) -> list[dict[str, Any]]:
        return [record for record in self.platform.repository.list(kind) if record.get("project_id") == project_id]

    def _refresh_requirement_set(self, project: dict[str, Any], *, status: str | None = None, actor: str = "NovaCodePro") -> dict[str, Any]:
        requirements = self.list_requirements(project["id"])
        record = {
            "id": f"reqset-{project['id']}",
            "tenant_id": project["tenant_id"],
            "organization_id": project["organization_id"],
            "customer_id": project["customer_id"],
            "project_id": project["id"],
            "environment": project["environment"],
            "status": status or "DRAFT",
            "version": str(len(requirements)),
            "owner": actor,
            "created_by": actor,
            "created_at": _now(),
            "updated_at": _now(),
            "correlation_id": project["workflow_id"],
            "classification": "INTERNAL",
            "retention_policy": "seven_years",
            "evidence_refs": [item["id"] for item in requirements],
            "requirements": requirements,
            "traceability_matrix": [
                {"requirement_id": item["id"], "test_links": item.get("test_links") or [], "trace_links": item.get("trace_links") or []}
                for item in requirements
            ],
        }
        self.platform.repository.upsert("requirement_set", record)
        return record

    def _transition_project(self, project: dict[str, Any], state: str, *, actor: str, evidence_ref: str = "", note: str = "") -> dict[str, Any]:
        current = str(project.get("stage") or "IDEA")
        if state not in SOLUTION_LIFECYCLE_TRANSITIONS.get(current, set()) and state != current:
            raise SolutionEngineeringError("invalid_transition", f"invalid_transition:{current}_to_{state}")
        project["stage"] = state
        project["status"] = state
        project["updated_at"] = _now()
        project.setdefault("history", [])
        project["history"] = [
            {"state": state, "actor": actor, "at": _now(), "evidence_ref": evidence_ref, "note": note},
            *list(project["history"]),
        ]
        if evidence_ref:
            project["evidence_refs"] = [evidence_ref, *list(project.get("evidence_refs") or [])]
        self.platform.repository.upsert("customer_project", project)
        if state in {"DISCOVERY", "REQUIREMENTS_DRAFT", "REQUIREMENTS_REVIEW", "REQUIREMENTS_APPROVED"}:
            try:
                self.workflow_fabric.validate(project["workflow_id"], actor=actor)
            except Exception:
                pass
        return project

    def _publish(self, event_type: str, record: dict[str, Any], *, workflow_id: str | None = None) -> None:
        self.platform.repository.append_event(
            {
                "event_id": _new_id("event", {"event_type": event_type, "record_id": record["id"]}),
                "occurred_at": _now(),
                "event_type": event_type,
                "tenant_id": record["tenant_id"],
                "organization_id": record["organization_id"],
                "project_id": record.get("project_id"),
                "workflow_id": workflow_id or record.get("workflow_id") or record.get("correlation_id"),
                "actor": {"type": "service", "id": record.get("created_by") or "NovaCodePro"},
                "correlation_id": workflow_id or record.get("correlation_id") or record["id"],
                "causation_id": record["id"],
                "metadata": {"category": "solution-engineering"},
                "data": record,
            }
        )
        self.platform.repository.append_audit(
            kind="solution-engineering",
            actor=str(record.get("created_by") or "NovaCodePro"),
            service="NovaCodePro Solution Engineering",
            subject=str(record.get("id") or ""),
            action=event_type,
            evidence=str(record.get("id") or ""),
            detail=f"{event_type} recorded for solution engineering.",
        )


__all__ = [
    "CHAT_STATUS",
    "SOLUTION_LIFECYCLE",
    "SOLUTION_LIFECYCLE_TRANSITIONS",
    "SolutionEngineeringContext",
    "SolutionEngineeringError",
    "SolutionEngineeringService",
]
