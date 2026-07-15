from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro.platform import get_novacodepro_platform
from afritech.novacodepro.solution_engineering import SolutionEngineeringError, SolutionEngineeringService
from afritech.novacodepro.workflow_fabric import WorkflowFabricService


SOLUTION_WINDOWS = (
    "Customer Dashboard",
    "Discovery Workspace",
    "Requirements Studio",
    "Business Analysis Studio",
    "UX/UI Studio",
    "Architecture Studio",
    "Engineering Studio",
    "Data Studio",
    "AI Studio",
    "Workflow Studio",
    "Quality Studio",
    "Security Studio",
    "Compliance and Risk Studio",
    "Delivery and Release Studio",
    "Operations Layer",
    "Governed Chat Workspace",
    "Approvals",
    "Knowledge and Evidence",
    "Customer Acceptance Portal",
    "Support and Evolution Workspace",
)


def _service() -> SolutionEngineeringService:
    db_path = Path(os.environ.get("NOVACODEPRO_DB_PATH", "var/novacodepro-platform.sqlite3"))
    platform = get_novacodepro_platform(db_path)
    return SolutionEngineeringService(platform, WorkflowFabricService(platform))


def _solution_team() -> tuple[str, ...]:
    return (
        "CUSTOMER",
        "CLIENT",
        "PARTNER",
        "ADMIN",
        "OPERATOR",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "ARCHITECT",
        "PROJECT_MANAGER",
        "QA_ENGINEER",
        "SECURITY_ENGINEER",
        "DEVOPS_ENGINEER",
        "DATA_ARCHITECT",
        "AI_ML_ENGINEER",
        "PRIVACY_COMPLIANCE",
        "COMPLIANCE_TEAM",
        "RISK_MANAGEMENT",
        "AUDIT_TEAM",
        "CUSTOMER_SUPPORT",
        "OBSERVER",
    )


class CustomerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    organization_id: str | None = None
    customer_id: str | None = None
    name: str
    segment: str | None = None
    country: str | None = None
    environment: str | None = None
    classification: str | None = None
    retention_policy: str | None = None
    owner: str | None = None
    correlation_id: str | None = None


class WorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    organization_id: str | None = None
    customer_id: str | None = None
    project_id: str
    name: str
    environment: str | None = None
    windows: list[str] = Field(default_factory=list)
    contexts: list[str] = Field(default_factory=list)
    navigation: list[str] = Field(default_factory=list)
    owner: str | None = None


class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    organization_id: str | None = None
    customer_id: str | None = None
    project_id: str | None = None
    name: str
    idea: str
    request: str | None = None
    domain: str | None = None
    region: str | None = None
    environment: str | None = None
    owner: str | None = None
    surfaces: list[str] = Field(default_factory=list)


class IdeaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    problem: str
    target_users: list[str] = Field(default_factory=list)
    market: str | None = None
    industry: str | None = None
    budget_range: str | None = None
    timeline: str | None = None


class RequirementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    kind: str | None = None
    priority: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    trace_links: list[str] = Field(default_factory=list)
    test_links: list[str] = Field(default_factory=list)
    owner: str | None = None
    version: str | None = None


class ReviewSectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section: str
    status: str


class BlueprintRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str | None = None
    scope: list[str] = Field(default_factory=list)
    personas: list[dict[str, Any]] = Field(default_factory=list)
    user_journeys: list[dict[str, Any]] = Field(default_factory=list)
    product_surfaces: list[str] = Field(default_factory=list)
    feature_catalogue: list[str] = Field(default_factory=list)
    business_processes: list[dict[str, Any]] = Field(default_factory=list)
    architecture: dict[str, Any] = Field(default_factory=dict)
    application_components: list[str] = Field(default_factory=list)
    data_model: dict[str, Any] = Field(default_factory=dict)
    apis: list[dict[str, Any]] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    security: dict[str, Any] = Field(default_factory=dict)
    privacy: dict[str, Any] = Field(default_factory=dict)
    compliance: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    accessibility: dict[str, Any] = Field(default_factory=dict)
    testing: dict[str, Any] = Field(default_factory=dict)
    deployment: dict[str, Any] = Field(default_factory=dict)
    observability: dict[str, Any] = Field(default_factory=dict)
    support: dict[str, Any] = Field(default_factory=dict)
    delivery_roadmap: list[str] = Field(default_factory=list)
    cost_assumptions: list[str] = Field(default_factory=list)
    unresolved_decisions: list[str] = Field(default_factory=list)


class ArchitectureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    decision: str
    requirements: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    implementation_work: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class DesignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str | None = None
    surface: str | None = None
    requirements: list[str] = Field(default_factory=list)
    section_statuses: list[dict[str, Any]] = Field(default_factory=list)
    accessibility_annotations: list[str] = Field(default_factory=list)
    localization_annotations: list[str] = Field(default_factory=list)
    prototype_links: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objectives: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    responsible_agents: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    validation_rules: list[str] = Field(default_factory=list)
    risk_level: str | None = None


class ReleaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    version: str | None = None
    environment: str | None = None
    scope: list[str] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)
    security_gates: list[str] = Field(default_factory=list)
    compliance_gates: list[str] = Field(default_factory=list)
    rollback_plan: str | None = None
    notes: str | None = None


class DeploymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    image_digest: str | None = None
    migration_version: str | None = None
    environment: str | None = None
    approvers: list[str] = Field(default_factory=list)
    result: str | None = None
    verification: dict[str, Any] = Field(default_factory=dict)


class AcceptanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str | None = None
    evidence_hash: str | None = None
    comments: list[str] = Field(default_factory=list)


def build_solution_engineering_router(service: SolutionEngineeringService | None = None) -> APIRouter:
    engine = service or _service()
    router = APIRouter(prefix="/v1/solution-engineering", tags=["solution-engineering"])

    readers = require_roles(*_solution_team())
    writers = require_roles("ADMIN", "OPERATOR", "DEVELOPER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "UI_UX_DESIGNER", "ARCHITECT", "PROJECT_MANAGER", "QA_ENGINEER", "SECURITY_ENGINEER", "DEVOPS_ENGINEER", "CUSTOMER_SUPPORT")
    customer_writer = require_roles("CUSTOMER", "CLIENT", "PARTNER", "ADMIN", "OPERATOR")
    approvers = require_roles("ADMIN", "OPERATOR", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "ARCHITECT", "PROJECT_MANAGER", "SECURITY_ENGINEER", "PRIVACY_COMPLIANCE", "COMPLIANCE_TEAM", "RISK_MANAGEMENT", "AUDIT_TEAM", "CUSTOMER_APPROVER")

    def _html_page(title: str, body: str) -> str:
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #09111a; color: #edf4ff; }}
    .shell {{ min-height: 100vh; padding: 24px; }}
    .grid {{ display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .panel {{ background: #101b28; border: 1px solid #223040; border-radius: 14px; padding: 16px; }}
    .panel h2 {{ margin: 0 0 10px; font-size: 18px; }}
    .panel ul {{ margin: 0; padding-left: 18px; }}
    .hero {{ margin-bottom: 20px; display:flex; justify-content:space-between; gap:16px; align-items:flex-end; flex-wrap: wrap; }}
    .windows {{ display:flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }}
    .window {{ border: 1px solid #2d4054; border-radius: 999px; padding: 8px 12px; background: #0f1a25; }}
    .muted {{ color: #9badc3; }}
    @media (max-width: 980px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body><div class="shell">{body}</div></body></html>"""

    @router.get("", response_model=None)
    def overview(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        projects = [project for project in engine.platform.repository.list("customer_project") if str(project.get("tenant_id") or "") == (claims.tenant_id or claims.organization_id)]
        return {
            "service": "NovaCodePro Solution Engineering",
            "windows": list(SOLUTION_WINDOWS),
            "lifecycle": list(projects[0].get("history") or []) if projects else [],
            "projects": projects,
            "customers": [record for record in engine.platform.repository.list("customer_organization") if str(record.get("tenant_id") or "") == (claims.tenant_id or claims.organization_id)],
            "workspace_count": len([record for record in engine.platform.repository.list("customer_workspace") if str(record.get("tenant_id") or "") == (claims.tenant_id or claims.organization_id)]),
        }

    @router.get("/studio", response_class=HTMLResponse)
    def studio(claims: JWTClaims = Depends(readers)) -> str:
        summary = engine.platform.admin_summary()
        windows = "".join(f'<span class="window">{window}</span>' for window in SOLUTION_WINDOWS)
        body = f"""
        <div class="hero">
          <div>
            <div class="muted">NovaCodePro Enterprise Solution Engineering Operating System</div>
            <h1>Customer Solution Studio</h1>
            <p class="muted">Governed discovery, requirements, architecture, delivery, and support.</p>
          </div>
          <div class="muted">Projects: {summary.get('project_count', 0)} · Workflows: {len(engine.platform.workflows())}</div>
        </div>
        <div class="windows">{windows}</div>
        <div class="grid" style="margin-top: 18px;">
          <section class="panel"><h2>Customer Dashboard</h2><p class="muted">Status, approvals, risks, releases, and support.</p></section>
          <section class="panel"><h2>Governed Chat Workspace</h2><p class="muted">Request-to-solution intake with approvals and evidence.</p></section>
          <section class="panel"><h2>Operations Layer</h2><p class="muted">Health, logs, metrics, incidents, and customer impact.</p></section>
          <section class="panel"><h2>Knowledge and Evidence</h2><p class="muted">Approved deliverables, audit trails, and reusable knowledge.</p></section>
        </div>
        """
        return _html_page("NovaCodePro Solution Studio", body)

    @router.get("/customers")
    def customers(claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        tenant = claims.tenant_id or claims.organization_id
        return [record for record in engine.platform.repository.list("customer_organization") if str(record.get("tenant_id") or "") == tenant]

    @router.post("/customers")
    def create_customer(payload: CustomerRequest, claims: JWTClaims = Depends(customer_writer)) -> dict[str, Any]:
        data = payload.model_dump()
        data["organization_id"] = data.get("organization_id") or claims.organization_id
        data["tenant_id"] = claims.tenant_id or data["tenant_id"]
        return engine.create_customer(data, actor=claims.sub)

    @router.get("/workspaces")
    def workspaces(claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        tenant = claims.tenant_id or claims.organization_id
        return [record for record in engine.platform.repository.list("customer_workspace") if str(record.get("tenant_id") or "") == tenant]

    @router.post("/workspaces")
    def create_workspace(payload: WorkspaceRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        data = payload.model_dump()
        data["organization_id"] = data.get("organization_id") or claims.organization_id
        data["tenant_id"] = claims.tenant_id or data["tenant_id"]
        return engine.create_workspace(data, actor=claims.sub)

    @router.get("/projects")
    def projects(claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        tenant = claims.tenant_id or claims.organization_id
        return [record for record in engine.platform.repository.list("customer_project") if str(record.get("tenant_id") or "") == tenant]

    @router.post("/projects")
    def create_project(payload: ProjectRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        data = payload.model_dump()
        data["organization_id"] = data.get("organization_id") or claims.organization_id
        data["tenant_id"] = claims.tenant_id or data["tenant_id"]
        return engine.create_project(data, actor=claims.sub)

    @router.get("/projects/{project_id}")
    def project(project_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return project
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.get("/projects/{project_id}/timeline")
    def project_timeline(project_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.replay(project_id)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/idea")
    def submit_idea(project_id: str, payload: IdeaRequest, claims: JWTClaims = Depends(customer_writer)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.submit_idea(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/discovery")
    def discovery(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.run_discovery(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/requirements")
    def create_requirement(project_id: str, payload: RequirementRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_requirement(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/requirements/approve")
    def approve_requirements(project_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.approve_requirements(project_id, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/blueprint")
    def create_blueprint(project_id: str, payload: BlueprintRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.generate_blueprint(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/blueprint/sections")
    def review_blueprint_section(project_id: str, payload: ReviewSectionRequest, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.review_blueprint_section(project_id, payload.section, status=payload.status, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/architecture")
    def create_architecture(project_id: str, payload: ArchitectureRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_architecture_decision(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/architecture/approve")
    def approve_architecture(project_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.approve_architecture(project_id, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/designs")
    def create_design(project_id: str, payload: DesignRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_design_artifact(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/plans")
    def create_plan(project_id: str, payload: PlanRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_implementation_plan(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/implement")
    def implement(project_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.start_implementation(project_id, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/tests")
    def test_project(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.record_test_results(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/security-review")
    def security_review(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.security_review(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/compliance-review")
    def compliance_review(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.compliance_review(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/customer-review")
    def customer_review(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(customer_writer)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.customer_review(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/release")
    def create_release(project_id: str, payload: ReleaseRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_release(project_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/releases/{release_id}/approve")
    def approve_release(release_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return engine.approve_release(release_id, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/releases/{release_id}/deploy")
    def deploy_release(release_id: str, payload: DeploymentRequest, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return engine.deploy_release(release_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.post("/releases/{release_id}/accept")
    def accept_release(release_id: str, payload: AcceptanceRequest, claims: JWTClaims = Depends(customer_writer)) -> dict[str, Any]:
        try:
            return engine.accept_release(release_id, payload.model_dump(), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code}) from exc

    @router.get("/projects/{project_id}/support")
    def support_cases(project_id: str, claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        tenant = claims.tenant_id or claims.organization_id
        return [record for record in engine.platform.repository.list("support_case") if str(record.get("tenant_id") or "") == tenant and str(record.get("project_id") or "") == project_id]

    @router.post("/projects/{project_id}/support")
    def open_support_case(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(customer_writer)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.open_support_case(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/enhancements")
    def create_enhancement(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(customer_writer)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_enhancement_request(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/knowledge")
    def publish_knowledge(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.publish_knowledge(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.post("/projects/{project_id}/evidence")
    def create_evidence(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.create_evidence(project_id, payload, actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.get("/projects/{project_id}/digital-twin")
    def digital_twin(project_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        project = engine.project(project_id)
        if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=404, detail={"code": "project_not_found"})
        return project

    @router.get("/projects/{project_id}/agents")
    def agents(project_id: str, claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        tenant = claims.tenant_id or claims.organization_id
        return [record for record in engine.platform.repository.list("agent_task") if str(record.get("tenant_id") or "") == tenant and str(record.get("project_id") or "") == project_id]

    @router.post("/projects/{project_id}/agents")
    def plan_agents(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            project = engine.project(project_id)
            if str(project.get("tenant_id") or "") != (claims.tenant_id or claims.organization_id):
                raise SolutionEngineeringError("project_not_found", "project_not_found")
            return engine.plan_agent_tasks(project_id, str(payload.get("request") or ""), actor=claims.sub)
        except SolutionEngineeringError as exc:
            raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    @router.get("/windows")
    def windows(claims: JWTClaims = Depends(readers)) -> list[str]:
        return list(SOLUTION_WINDOWS)

    return router


__all__ = ["build_solution_engineering_router"]
