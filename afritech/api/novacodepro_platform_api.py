"""Distributed NovaCodePro enterprise platform API surfaces."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from afritech.afriprogramming.rbac import canonical_role_name, role_definition
from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles, _cookie_secure
from afritech.api.auth.novacodepro_session_store import get_default_novacodepro_session_store
from afritech.novacodepro import NovaCodeProPlatform, get_novacodepro_platform
from afritech.novacodepro.completion_standard import (
    build_completion_evidence,
    completion_dashboard,
    completion_standard_model,
    evaluate_completion_state,
)
from afritech.novacodepro.edos import (
    authority_model,
    backend_service_architecture,
    capability_state_registry,
    edos_capability_model,
    edos_maturity_report,
    edos_summary,
    enterprise_readiness_matrix,
    frontend_experience_registry,
    infrastructure_certification_records,
    mobile_release_certificate,
    continuous_compliance_model,
    operational_evidence_manifest,
    prr_governance_workflow,
)
from afritech.novacodepro.operating_fabric import EnterpriseExecutionContext, normalize_role
from afritech.novacodepro.production_readiness import (
    evaluate_ga_governance,
    evaluate_operational_readiness,
    operational_readiness_program,
    production_completion_program,
)
from afritech.novacodepro.ux_operating_system import (
    ai_design_studio_model,
    component_registry_model,
    digital_ux_twin_model,
    enterprise_design_knowledge_graph_model,
    ux_operating_system_summary,
    ux_studio_registry,
    ux_validation_model,
    uxos_operational_completion_matrix,
    uxos_service_architecture,
)
from afritech.novacodepro.workspace import build_workspace_manifest


def _service() -> NovaCodeProPlatform:
    db_path = Path(os.environ.get("NOVACODEPRO_DB_PATH", "var/novacodepro-platform.sqlite3"))
    return get_novacodepro_platform(db_path)


def _bootstrap_error(code: str, message: str, status_code: int, **extra: Any) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message, **extra})


def _normalize_roles(role: str, assigned_roles: list[str] | None = None) -> list[str]:
    canonical = canonical_role_name(role)
    normalized = [canonical]
    if assigned_roles:
        for item in assigned_roles:
            value = canonical_role_name(item)
            if value not in normalized:
                normalized.append(value)
    for alias in role_definition(canonical).get("aliases", ()):
        alias_value = canonical_role_name(alias)
        if alias_value not in normalized:
            normalized.append(alias_value)
    return normalized


def _bootstrap_role_label(role: str) -> str:
    canonical = canonical_role_name(role)
    if canonical == "ADMIN":
        return "PLATFORM_ADMIN"
    if canonical == "SUPER_ADMIN":
        return "PLATFORM_OWNER"
    return canonical


def _set_session_cookies(response: Response, result: dict[str, Any]) -> None:
    from afritech.api.auth.novacodepro_session_store import (
        ACCESS_COOKIE_NAME,
        CSRF_COOKIE_NAME,
        REFRESH_COOKIE_NAME,
        SESSION_COOKIE_NAME,
    )

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=result["access_token"],
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=result["refresh_token"],
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result["session_id"],
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=result["csrf_token"],
        httponly=False,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    from afritech.api.auth.novacodepro_session_store import (
        ACCESS_COOKIE_NAME,
        CSRF_COOKIE_NAME,
        REFRESH_COOKIE_NAME,
        SESSION_COOKIE_NAME,
    )

    for cookie_name in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, SESSION_COOKIE_NAME, CSRF_COOKIE_NAME):
        response.delete_cookie(cookie_name, path="/")


def _build_session_bootstrap(service: NovaCodeProPlatform, request: Request) -> dict[str, Any]:
    session_store = get_default_novacodepro_session_store()
    try:
        current = session_store.current_session(request)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": str(exc.detail)}
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc
    if not isinstance(current, dict):
        _bootstrap_error("SESSION_REQUIRED", "Session is required.", 401)

    user_id = str(current.get("user_id") or "")
    session_role = str(current.get("active_role") or "ADMIN")
    canonical_role = canonical_role_name(session_role)
    org_id = str(current.get("organization") or current.get("tenant_id") or "")
    if not org_id:
        _bootstrap_error("TENANT_REQUIRED", "Tenant context is required.", 409)

    workspace_manifest = build_workspace_manifest(
        service,
        user_id=user_id or current.get("display_name") or "novacodepro-user",
        role=canonical_role,
        organization_id=org_id,
        environment=os.environ.get("NOVACODEPRO_ENVIRONMENT")
        or os.environ.get("AFRITECH_ENV")
        or "development",
    )
    workspace_data = workspace_manifest["workspace"]
    workspace = {
        "id": "novatech-platform" if canonical_role == "ADMIN" else workspace_data["id"],
        "name": "NovaTech Platform" if canonical_role == "ADMIN" else workspace_data["title"],
        "status": "ACTIVE",
        "home_route": "/novacodepro/dashboard" if canonical_role == "ADMIN" else workspace_data["home_route"],
        "selected_environment": workspace_data["selected_environment"],
        "authority_level": workspace_data["authority_level"],
    }
    compatibility_roles = _normalize_roles(session_role, list(current.get("assigned_roles") or []))
    canonical_display_role = _bootstrap_role_label(canonical_role)
    permissions = list(role_definition(canonical_role).get("permissions", ()))
    for required_permission in (
        "dashboard.read",
        "platform.read",
        "platform.manage",
        "workspace.read",
        "workspace.manage",
        "users.read",
        "roles.read",
        "tenants.read",
        "architecture.read",
        "nera.read",
        "eros.read",
        "digital_twin.read",
        "governance.read",
        "audit.read",
        "observability.read",
    ):
        if required_permission not in permissions:
            permissions.append(required_permission)
    role_label = role_definition(canonical_role).get("label", canonical_display_role.replace("_", " ").title())
    return {
        "authenticated": True,
        "bootstrap_state": "READY",
        "user": {
            "id": user_id,
            "username": user_id,
            "email": current.get("email"),
            "display_name": current.get("display_name"),
            "status": "ACTIVE",
            "email_verified": True,
            "active_role": canonical_display_role,
            "role_label": role_label,
        },
        "organization": {
            "id": org_id,
            "name": current.get("organization") or "NovaTech",
            "status": "ACTIVE",
        },
        "tenant": {
            "id": org_id,
            "name": current.get("organization") or "NovaTech",
            "status": "ACTIVE",
        },
        "workspace": workspace,
        "roles": compatibility_roles if canonical_display_role in compatibility_roles else [canonical_display_role, *compatibility_roles],
        "canonical_role": canonical_display_role,
        "permissions": permissions,
        "features": {
            "dashboard": True,
            "nera": True,
            "eros": True,
            "digital_twin": True,
            "governance": True,
            "observability": True,
        },
        "default_route": workspace["home_route"],
        "context": {
            "workspace_manifest": workspace_manifest,
            "session_id": current.get("session_id"),
            "session_status": current.get("status"),
            "idle_expires_at": current.get("idle_expires_at"),
            "absolute_expires_at": current.get("absolute_expires_at"),
        },
        "modules": {
            "nera": service.nera_manifest(),
            "eros": service.eros_manifest(),
            "architecture_framework": service.architecture_framework(),
        },
    }


class WorkflowCreateRequest(BaseModel):
    title: str
    request: str
    tenant_id: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    domain: str = "general"
    region: str = "Australia"
    compliance: str = "enterprise"
    surfaces: list[str] = Field(default_factory=list)


class WorkflowTransitionRequest(BaseModel):
    action: str
    note: str = ""


class ArtifactCreateRequest(BaseModel):
    workflow_id: str
    kind: str
    title: str
    uri: str = ""
    version: str = "v1"
    checksum: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class UXArtifactCreateRequest(BaseModel):
    artifact: str
    artifact_type: str = "design_artifact"
    studio: str = "UX Governance Center"
    owner: str = "NovaCodePro UX"
    reviewers: list[str] = Field(default_factory=list)
    approval_state: str = "DRAFT"
    version: str = "v1"
    traceability: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UXArtifactTransitionRequest(BaseModel):
    target_state: str
    note: str = ""


class UXEvidenceAttachRequest(BaseModel):
    evidence_refs: list[str] = Field(default_factory=list)


class UXOSServiceRecordRequest(BaseModel):
    subject: str
    provider: str = ""
    environment: str = "development"
    version: str = "v1"
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompletionEvaluationRequest(BaseModel):
    repository_complete: bool = False
    operational_verified: bool = False
    governance_approved: bool = False
    production_ready_gates: dict[str, bool] = Field(default_factory=dict)
    executive_authorized: bool = False


class CompletionEvidenceRequest(BaseModel):
    capability: str
    environment: str = "development"
    executor: str = "NovaCodePro"
    status: str = "EVIDENCE_PENDING"
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)
    trace_ids: list[str] = Field(default_factory=list)


class OperationalReadinessEvaluationRequest(BaseModel):
    evidence: dict[str, str] = Field(default_factory=dict)
    approvals: dict[str, str] = Field(default_factory=dict)
    payment_evidence: dict[str, str] = Field(default_factory=dict)


class ProjectCreateRequest(BaseModel):
    name: str
    tenant_id: str | None = None
    status: str = "Discovery"
    owner: str = "NovaCodePro"
    solution: str = "Generated solution"
    region: str = "Australia"
    budget: str = "$0"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThreadCreateRequest(BaseModel):
    tenant_id: str | None = None
    project_id: str | None = None
    scope: str
    participants: list[str] = Field(default_factory=list)


class CommentCreateRequest(BaseModel):
    body: str
    author: str = "NovaCodePro"


class KnowledgeLinkRequest(BaseModel):
    source_id: str
    target_id: str


class IntegrationConnectRequest(BaseModel):
    integration_id: str


class ReleaseCreateRequest(BaseModel):
    workflow_id: str
    title: str = "NovaCodePro release"
    channel: str = "pilot"
    target: str = "staging"
    notes: str = ""


class ReleaseTransitionRequest(BaseModel):
    action: str
    note: str = ""


class CommandRequest(BaseModel):
    command: str
    context: dict[str, Any] = Field(default_factory=dict)


class EnterpriseOperatingRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    request: str
    workspace_id: str | None = None
    project_id: str | None = None
    capability_hint: str | None = None
    products: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    desired_outcomes: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    requested_region: str | None = None
    requested_environment: str = "development"
    rollback_expectation: str | None = None


class SolutionCreateRequest(BaseModel):
    title: str
    request: str
    tenant_id: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    domain: str = "general"
    region: str = "Australia"
    compliance: str = "enterprise"
    surfaces: list[str] = Field(default_factory=list)
    version: str = "2027.1.0"


class AgentExecutionCreateRequest(BaseModel):
    agent_id: str
    version: str = "2027.1.0"
    category: str = "general"
    tenant_id: str | None = None
    project_id: str | None = None
    workflow_id: str | None = None
    stage_id: str = "intake"
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    allowed_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    timeout_seconds: int = 900
    maximum_cost: float = 0.0
    approval_policy: str = "standard"
    evidence: list[str] = Field(default_factory=list)


class ApprovalCreateRequest(BaseModel):
    gate_type: str
    workflow_id: str | None = None
    release_id: str | None = None
    requested_by: str = "NovaID"
    conditions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ApprovalDecisionRequest(BaseModel):
    note: str = ""


class DeploymentCreateRequest(BaseModel):
    workflow_id: str
    release_id: str
    environment: str = "staging"
    region: str = "Australia"
    version: str = "2027.1.0"
    metrics: dict[str, Any] = Field(default_factory=dict)


class DeploymentTransitionRequest(BaseModel):
    action: str
    note: str = ""


class KnowledgeQueryRequest(BaseModel):
    query: str


class GraphNodeRequest(BaseModel):
    id: str | None = None
    label: str
    type: str = "Service"
    tenant_id: str | None = None
    owner: str = "NovaCodePro"
    evidence: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class GraphEdgeRequest(BaseModel):
    source_id: str
    target_id: str


class GraphQueryRequest(BaseModel):
    query: str


class FederationAgreementRequest(BaseModel):
    provider_org: str | None = None
    consumer_org: str | None = None
    trust_level: str = "VERIFIED"
    allowed_capabilities: list[str] = Field(default_factory=list)
    denied_capabilities: list[str] = Field(default_factory=list)
    allowed_regions: list[str] = Field(default_factory=list)
    data_classes: list[str] = Field(default_factory=list)
    purpose: str = ""
    expires_at: str = ""
    signature: str = ""


class FederationAuthorizeRequest(BaseModel):
    capability: str
    region: str = "AU"


class FederationShareRequest(BaseModel):
    resource_id: str
    consumer_org: str
    tenant_id: str | None = None


class RegionEligibilityRequest(BaseModel):
    capacity_ok: bool = True
    keys_available: bool = True
    replication_healthy: bool = True


class RegionFailoverRequest(BaseModel):
    target_region: str
    reasons: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


class TwinSimulationRequest(BaseModel):
    scenario: str
    affected_users: int | None = None
    estimated_revenue_impact: int | None = None
    predicted_recovery_minutes: int | None = None
    policy_violations: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float | None = None


class TwinCompareRequest(BaseModel):
    compare_to: str


class DigitalTwinCreateRequest(BaseModel):
    id: str | None = None
    name: str
    type: str = "SERVICE"
    owner: str = "NovaCodePro"
    tenant_id: str | None = None
    jurisdiction: str = "AU"
    classification: str = "INTERNAL"
    region: str = "Australia"
    status: str = "healthy"
    summary: str = ""
    sources: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    topology: dict[str, Any] = Field(default_factory=dict)
    children: list[str] = Field(default_factory=list)
    observed_state: str = "HEALTHY"
    desired_state: str = "AVAILABLE"
    predicted_state: str = "STABLE"
    simulated_state: str = "NOT_RUN"
    approved_state: str = "APPROVED"
    recovered_state: str = "HEALTHY"
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    lineage: list[str] = Field(default_factory=list)


class DigitalTwinObservationRequest(BaseModel):
    observed_state: str
    observed_detail: str = ""
    observed_evidence: list[str] = Field(default_factory=list)
    desired_state: str | None = None
    desired_detail: str = ""
    desired_evidence: list[str] = Field(default_factory=list)
    predicted_state: str | None = None
    predicted_detail: str = ""
    predicted_evidence: list[str] = Field(default_factory=list)
    status: str = "healthy"
    metrics: dict[str, Any] = Field(default_factory=dict)
    actor: str = "digital-twin-engine"


class DigitalTwinRelationshipRequest(BaseModel):
    id: str | None = None
    source: str | None = None
    target: str
    type: str = "DEPENDS_ON"
    criticality: str = "MEDIUM"
    weight: float = 1.0
    rto: str = "15m"
    rpo: str = "5m"
    recovery_difficulty: float = 1.0
    confidence: float = 0.9
    evidence: list[str] = Field(default_factory=list)


class DigitalTwinRecoveryPlanRequest(BaseModel):
    scenario: str
    workflow_id: str | None = None
    expected_rto: str | None = None
    expected_rpo: str | None = None
    steps: list[str] = Field(default_factory=list)
    approvals_required: list[str] = Field(default_factory=list)
    blast_radius: int = 1
    evidence_id: str | None = None


class DigitalTwinRecoveryRequest(BaseModel):
    scenario: str
    workflow_id: str | None = None
    root_failure: str | None = None
    predicted_recovery_minutes: int | None = None
    risk_after: int | None = None
    summary: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    recovery_plan: dict[str, Any] = Field(default_factory=dict)
    actor: str = "recovery-orchestrator"
    blast_radius: int = 1
    approved_detail: str = ""
    recovered_detail: str = ""


class ExecutiveCouncilSessionRequest(BaseModel):
    subject: str
    question: str


class ExecutiveCouncilSynthesisRequest(BaseModel):
    subject: str
    consensus: str = "CONDITIONAL_APPROVAL_RECOMMENDED"
    supporting_agents: list[str] = Field(default_factory=list)
    dissenting_agents: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    escalation: str = "BOARD_REVIEW_REQUIRED"


class ExecutiveAgentAnalyzeRequest(BaseModel):
    position: str = "DEFER"
    confidence: float = 0.88
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class BoardMeetingRequest(BaseModel):
    title: str
    agenda: list[str] = Field(default_factory=list)


class BoardResolutionRequest(BaseModel):
    title: str
    meeting_id: str
    quorum: dict[str, Any] = Field(default_factory=lambda: {"required": 3, "present": 0, "met": False})
    votes: dict[str, Any] = Field(default_factory=lambda: {"for": 0, "against": 0, "abstain": 0})
    conditions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    signature: str = ""


class BoardVoteRequest(BaseModel):
    vote: str


class SliRequest(BaseModel):
    service: str
    metric: str
    target: float = 99.95
    measurement: float = 99.97
    window: str = "30d"
    status: str = "WITHIN_TARGET"


class SloRequest(BaseModel):
    service: str
    metric: str
    target: float = 99.95
    measurement: float = 99.97
    window: str = "30d"
    status: str = "WITHIN_TARGET"


class ChaosExperimentRequest(BaseModel):
    scenario: str
    scope: str = "regional"
    owner: str = "SRE"
    approval_id: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class EventTopicRequest(BaseModel):
    name: str
    owner: str = "NovaCodePro"
    retention: str = "30d"
    classification: str = "INTERNAL"
    region: str = "Australia"
    replay_policy: str = "isolated"


class EventSchemaRequest(BaseModel):
    topic: str
    version: str = "1.0"
    schema: dict[str, Any] = Field(default_factory=dict)
    compatibility: str = "BACKWARD"


class EventReplayRequest(BaseModel):
    topic: str
    tenant_id: str | None = None
    region: str = "Australia"


class MarketplaceInstallRequest(BaseModel):
    package_id: str
    tenant_id: str | None = None
    region: str = "Australia"
    version: str = "2027.1.0"


class SolutionPackageRequest(BaseModel):
    title: str
    request: str
    tenant_id: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    domain: str = "general"
    region: str = "Australia"
    compliance: str = "enterprise"
    surfaces: list[str] = Field(default_factory=list)
    version: str = "1"
    approval_type: str = "solution_review"
    risk_level: str = "medium"
    approver: str = "NovaTech Governance"
    comments: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    execution_enabled: bool = False


class RetryQueueRequest(BaseModel):
    event_id: str
    consumer_name: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0
    next_retry_at: str
    last_error: str = ""


class DeadLetterRequest(BaseModel):
    failure_reason: str


def build_novacodepro_platform_router(platform: NovaCodeProPlatform | None = None) -> APIRouter:
    service = platform or _service()
    router = APIRouter(prefix="/v1/novacodepro", tags=["novacodepro"])
    observer = require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER", "DEVELOPER")
    editor = require_roles("OPERATOR", "ADMIN", "DEVELOPER")
    ux_editor = require_roles("OPERATOR", "ADMIN", "DEVELOPER", "UI_UX_DESIGNER")

    def _tenant_context(claims: JWTClaims) -> str:
        return str(claims.organization_id or "novatech")

    def _execution_context(claims: JWTClaims, workspace_id: str | None, requested_region: str | None) -> EnterpriseExecutionContext:
        tenant_id = _tenant_context(claims)
        workspace = workspace_id or "workspace-platform"
        if not tenant_id:
            raise HTTPException(status_code=403, detail="missing_tenant_membership")
        if workspace not in {"workspace-platform", "workspace-enterprise", "workspace-operations"}:
            raise HTTPException(status_code=403, detail="unknown_workspace")
        canonical_role = normalize_role(claims.role)
        permissions = {"novacodepro.request.create", "workflow.read", "approval.read"}
        if canonical_role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "DEVELOPER", "OPERATOR"}:
            permissions.update({"workflow.write", "evidence.write", "policy.evaluate"})
        authority_grants = ("authority-level-2",)
        if canonical_role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "OPERATOR"}:
            authority_grants = ("authority-level-3",)
        return EnterpriseExecutionContext(
            subject_id=claims.sub,
            actor_type="USER",
            tenant_id=tenant_id,
            organization_id=tenant_id,
            workspace_id=workspace,
            canonical_roles=(canonical_role,),
            permissions=frozenset(permissions),
            authority_grants=authority_grants,
            session_id=claims.sid or f"jwt-{claims.sub}",
            authentication_strength="JWT",
            device_trust=80,
            session_risk=10,
            jurisdiction="AU",
            region=requested_region or "Australia",
            correlation_id=f"corr-{claims.sub}-{workspace}",
        )

    @router.get("/status")
    def status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.status()

    @router.get("/admin/summary")
    def admin_summary(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.admin_summary()

    @router.get("/solutions")
    def solutions(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.solutions()

    @router.get("/solutions/{solution_id}")
    def solution(solution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_solution(solution_id)
        if record is None:
            raise HTTPException(status_code=404, detail="solution_not_found")
        return record

    @router.post("/solutions")
    def create_solution(payload: SolutionCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_solution(data)

    @router.post("/solutions/packages")
    def create_solution_package(payload: SolutionPackageRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        data.setdefault("requested_by", claims.sub)
        return service.orchestrate_solution_package(data)

    @router.get("/agents/executions")
    def agent_executions(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.agent_executions()

    @router.get("/agents")
    def agents(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.agents()

    @router.get("/agents/registry")
    def agent_registry(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.agent_registry_catalog()

    @router.post("/agents/register")
    def register_agent(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        return service.register_agent(data)

    @router.get("/agents/executions/{execution_id}")
    def agent_execution(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_agent_execution(execution_id)
        if record is None:
            raise HTTPException(status_code=404, detail="agent_execution_not_found")
        return record

    @router.post("/agents/executions")
    def create_agent_execution(payload: AgentExecutionCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_agent_execution(data)

    @router.post("/agents/executions/{execution_id}/cancel")
    def cancel_agent_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        record = service.get_agent_execution(execution_id)
        if record is None:
            raise HTTPException(status_code=404, detail="agent_execution_not_found")
        record["status"] = "cancelled"
        service.repository.upsert("agent_execution", record)
        return record

    @router.post("/agents/executions/{execution_id}/retry")
    def retry_agent_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.retry_agent_execution(execution_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="agent_execution_not_found") from exc

    @router.get("/approvals")
    def approvals(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.approvals()

    @router.post("/approvals")
    def create_approval(payload: ApprovalCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["requested_by"] = claims.sub
        return service.create_approval(data)

    @router.post("/approvals/{approval_id}/approve")
    def approve_approval(
        approval_id: str,
        payload: ApprovalDecisionRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            return service.decide_approval(approval_id, "approve", actor=claims.sub, note=payload.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="approval_not_found") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @router.post("/approvals/{approval_id}/reject")
    def reject_approval(
        approval_id: str,
        payload: ApprovalDecisionRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            return service.decide_approval(approval_id, "reject", actor=claims.sub, note=payload.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="approval_not_found") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @router.get("/deployments")
    def deployments(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.deployments()

    @router.get("/deployments/{deployment_id}")
    def deployment(deployment_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_deployment(deployment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="deployment_not_found")
        return record

    @router.post("/deployments")
    def create_deployment(payload: DeploymentCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_deployment(data)

    @router.post("/deployments/{deployment_id}/transition")
    def transition_deployment(
        deployment_id: str,
        payload: DeploymentTransitionRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            return service.transition_deployment(deployment_id, payload.action, payload.note, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/eros")
    def eros(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.eros_manifest()

    @router.get("/digital-twins")
    def digital_twins(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.digital_twin_registry()

    @router.post("/digital-twins")
    def create_digital_twin(payload: DigitalTwinCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_digital_twin(data)

    @router.get("/digital-twins/{twin_id}")
    def digital_twin(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_or_create_digital_twin(twin_id)
        return record

    @router.get("/digital-twins/{twin_id}/summary")
    def digital_twin_summary(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_summary(twin_id)

    @router.get("/digital-twins/{twin_id}/topology")
    def digital_twin_topology(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_topology(twin_id)

    @router.get("/digital-twins/{twin_id}/health")
    def digital_twin_health(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_health(twin_id)

    @router.get("/digital-twins/{twin_id}/relationships")
    def digital_twin_relationships(twin_id: str, claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.twin_relationships(twin_id)

    @router.get("/digital-twins/{twin_id}/scores")
    def digital_twin_scores(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.twin_scores(twin_id)

    @router.get("/digital-twins/{twin_id}/snapshots")
    def digital_twin_snapshots(twin_id: str, claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.twin_snapshots(twin_id)

    @router.get("/digital-twins/{twin_id}/evidence")
    def digital_twin_evidence(twin_id: str, claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.twin_evidence(twin_id)

    @router.post("/digital-twins/{twin_id}/observe")
    def observe_digital_twin(
        twin_id: str,
        payload: DigitalTwinObservationRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.observe_twin(twin_id, payload.model_dump())

    @router.post("/digital-twins/{twin_id}/simulate")
    def simulate_digital_twin(
        twin_id: str,
        payload: TwinSimulationRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.simulate_twin(twin_id, payload.model_dump())

    @router.post("/digital-twins/{twin_id}/compare")
    def compare_digital_twins(
        twin_id: str,
        payload: TwinCompareRequest,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return service.compare_twins(twin_id, payload.model_dump())

    @router.post("/digital-twins/{twin_id}/replay")
    def replay_digital_twin(
        twin_id: str,
        payload: dict[str, Any] | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return service.replay_twin(twin_id, payload or {})

    @router.post("/digital-twins/{twin_id}/refresh")
    def refresh_digital_twin(twin_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.refresh_twin(twin_id)

    @router.post("/digital-twins/{twin_id}/relationships")
    def create_digital_twin_relationship(
        twin_id: str,
        payload: DigitalTwinRelationshipRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.create_twin_relationship(twin_id, payload.model_dump())

    @router.post("/digital-twins/{twin_id}/snapshots")
    def create_digital_twin_snapshot(
        twin_id: str,
        payload: dict[str, Any] | None = None,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.create_twin_snapshot(twin_id, payload or {})

    @router.post("/digital-twins/{twin_id}/recovery-plans")
    def create_digital_twin_recovery_plan(
        twin_id: str,
        payload: DigitalTwinRecoveryPlanRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.create_twin_recovery_plan(twin_id, payload.model_dump())

    @router.post("/digital-twins/{twin_id}/recover")
    def recover_digital_twin(
        twin_id: str,
        payload: DigitalTwinRecoveryRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.recover_twin(twin_id, payload.model_dump())

    @router.get("/twins/{twin_id}")
    def twin(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.get_or_create_digital_twin(twin_id)

    @router.get("/twins/{twin_id}/topology")
    def twin_topology(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_topology(twin_id)

    @router.get("/twins/{twin_id}/health")
    def twin_health(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_health(twin_id)

    @router.get("/twins/{twin_id}/history")
    def twin_history(twin_id: str, claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.twin_history(twin_id)

    @router.post("/twins/{twin_id}/simulate")
    def simulate_twin(twin_id: str, payload: TwinSimulationRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.simulate_twin(twin_id, payload.model_dump())

    @router.post("/twins/{twin_id}/compare")
    def compare_twins(twin_id: str, payload: TwinCompareRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.compare_twins(twin_id, payload.model_dump())

    @router.post("/twins/{twin_id}/replay")
    def replay_twin(twin_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.replay_twin(twin_id, payload or {})

    @router.post("/twins/{twin_id}/refresh")
    def refresh_twin(twin_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.refresh_twin(twin_id)

    @router.get("/tenants")
    def tenants(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.tenants()

    @router.get("/projects")
    def projects(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.projects()

    @router.post("/projects")
    def create_project(payload: ProjectCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_project(data)

    @router.get("/workflows")
    def workflows(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.workflows()

    @router.get("/workflows/{workflow_id}")
    def workflow(workflow_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_workflow(workflow_id)
        if record is None:
            raise HTTPException(status_code=404, detail="workflow_not_found")
        return record

    @router.post("/workflows")
    def create_workflow(payload: WorkflowCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_workflow(data)

    @router.post("/workflows/{workflow_id}/transition")
    def transition_workflow(
        workflow_id: str,
        payload: WorkflowTransitionRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            return service.transition_workflow(workflow_id, payload.action, payload.note, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/artifacts")
    def artifacts(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.artifacts()

    @router.post("/artifacts")
    def create_artifact(payload: ArtifactCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_artifact(data)

    @router.get("/knowledge-graph")
    def knowledge_graph(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"nodes": service.knowledge_graph()}

    @router.post("/knowledge-graph/replay")
    def replay_knowledge_graph(claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return {"nodes": service.replay_knowledge_graph()}

    @router.post("/knowledge-graph/link")
    def link_knowledge(payload: KnowledgeLinkRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.link_nodes(payload.source_id, payload.target_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="knowledge_node_not_found") from exc

    @router.get("/collaboration/threads")
    def collaboration_threads(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.collaboration_threads()

    @router.post("/collaboration/threads")
    def create_thread(payload: ThreadCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_thread(data)

    @router.post("/collaboration/threads/{thread_id}/messages")
    def post_comment(
        thread_id: str,
        payload: CommentCreateRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            return service.post_comment(thread_id, payload.body, author=payload.author or claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="thread_not_found") from exc

    @router.get("/integrations")
    def integrations(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.integrations()

    @router.post("/integrations/connect")
    def connect_integration(payload: IntegrationConnectRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.connect_integration(payload.integration_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="integration_not_found") from exc

    @router.get("/marketplace")
    def marketplace(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.marketplace()

    @router.post("/marketplace/install")
    def install_marketplace_package(
        payload: MarketplaceInstallRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        return service.install_marketplace_package(
            {
                "package_id": payload.package_id,
                "tenant_id": _tenant_context(claims),
                "region": payload.region,
                "version": payload.version,
            }
        )

    @router.post("/marketplace/uninstall")
    def uninstall_marketplace_package(
        payload: MarketplaceInstallRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            package = service.uninstall_marketplace_package(payload.package_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="marketplace_package_not_found") from exc
        return {"id": package["id"], "status": "uninstalled"}

    @router.get("/marketplace/packages")
    def marketplace_packages(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.marketplace_packages()

    @router.get("/marketplace/installations")
    def marketplace_installations(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.marketplace_installations()

    @router.post("/marketplace/packages")
    def create_marketplace_package(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        package = dict(payload)
        package["id"] = str(package.get("package_id") or package.get("id") or "package")
        package.setdefault("tenant_id", _tenant_context(claims))
        package.setdefault("installed", False)
        package.setdefault("version", "2027.1.0")
        package.setdefault("category", "solution")
        package.setdefault("signature", "sigstore-reference")
        package.setdefault("checksum", "sha256-demo")
        return service.repository.upsert("marketplace_item", package)

    @router.post("/marketplace/packages/{package_id}/verify")
    def verify_marketplace_package(package_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        package = service.repository.get("marketplace_item", package_id)
        if package is None:
            raise HTTPException(status_code=404, detail="marketplace_package_not_found")
        verified = not str(package.get("signature") or "").startswith("invalid")
        return {"package_id": package_id, "verified": verified, "package": package}

    @router.post("/marketplace/installations")
    def create_marketplace_installation(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.install_marketplace_package(
                {
                    "package_id": str(payload["package_id"]),
                    "tenant_id": _tenant_context(claims),
                    "region": str(payload.get("region") or "Australia"),
                    "version": str(payload.get("version") or "2027.1.0"),
                    "signature": str(payload.get("signature") or "sigstore-reference"),
                    "permissions": list(payload.get("permissions") or []),
                    "checksum": str(payload.get("checksum") or "sha256-demo"),
                    "publisher": str(payload.get("publisher") or "NovaTech"),
                }
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="marketplace_package_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/marketplace/installations/{installation_id}/upgrade")
    def upgrade_marketplace_installation(installation_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        package = service.repository.get("marketplace_item", installation_id)
        if package is None:
            raise HTTPException(status_code=404, detail="marketplace_package_not_found")
        package["version"] = str(payload.get("version") or package.get("version") or "2027.1.0")
        package["updated_at"] = service.audit(limit=1)[0]["at"] if service.audit(limit=1) else package.get("updated_at")
        service.repository.upsert("marketplace_item", package)
        return package

    @router.post("/marketplace/installations/{installation_id}/remove")
    def remove_marketplace_installation(installation_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            package = service.uninstall_marketplace_package(installation_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="marketplace_package_not_found") from exc
        return package

    @router.get("/releases")
    def releases(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.releases()

    @router.post("/releases")
    def create_release(payload: ReleaseCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_release(data)

    @router.post("/releases/{release_id}/transition")
    def transition_release(
        release_id: str,
        payload: ReleaseTransitionRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        try:
            return service.transition_release(release_id, payload.action, payload.note, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="release_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/solutions/{solution_id}/submit")
    def submit_solution(solution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        solution = service.get_solution(solution_id)
        if solution is None:
            raise HTTPException(status_code=404, detail="solution_not_found")
        solution["status"] = "submitted"
        solution["updated_at"] = service.audit(limit=1)[0]["at"] if service.audit(limit=1) else solution.get("updated_at")
        service.repository.upsert("solution", solution)
        return solution

    @router.post("/solutions/{solution_id}/cancel")
    def cancel_solution(solution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        solution = service.get_solution(solution_id)
        if solution is None:
            raise HTTPException(status_code=404, detail="solution_not_found")
        solution["status"] = "cancelled"
        solution["updated_at"] = service.audit(limit=1)[0]["at"] if service.audit(limit=1) else solution.get("updated_at")
        service.repository.upsert("solution", solution)
        return solution

    @router.post("/workflows/{workflow_id}/pause")
    def pause_workflow(workflow_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.transition_workflow(workflow_id, "pause", actor=claims.sub)

    @router.post("/workflows/{workflow_id}/resume")
    def resume_workflow(workflow_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.transition_workflow(workflow_id, "resume", actor=claims.sub)

    @router.post("/workflows/{workflow_id}/retry")
    def retry_workflow(workflow_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.transition_workflow(workflow_id, "retry", actor=claims.sub)

    @router.post("/workflows/{workflow_id}/reject")
    def reject_workflow(workflow_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        note = str((payload or {}).get("note") or "")
        return service.transition_workflow(workflow_id, "reject", note, actor=claims.sub)

    @router.post("/workflows/{workflow_id}/rollback")
    def rollback_workflow(workflow_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        note = str((payload or {}).get("note") or "")
        return service.transition_workflow(workflow_id, "rollback", note, actor=claims.sub)

    @router.post("/workflows/{workflow_id}/replay")
    def replay_workflow(workflow_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_workflow(workflow_id)
        if record is None:
            raise HTTPException(status_code=404, detail="workflow_not_found")
        return record

    @router.post("/risks/evaluate")
    def evaluate_risk(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        return service.evaluate_risk(data)

    @router.get("/risks")
    def risks(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.risks()

    @router.get("/risks/{risk_id}")
    def risk(risk_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_risk(risk_id)
        if record is None:
            raise HTTPException(status_code=404, detail="risk_not_found")
        return record

    @router.post("/risks/{risk_id}/treat")
    def treat_risk(risk_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.treat_risk(risk_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="risk_not_found") from exc

    @router.post("/risks/{risk_id}/accept")
    def accept_risk(risk_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.accept_risk(risk_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="risk_not_found") from exc

    @router.post("/risks/{risk_id}/close")
    def close_risk(risk_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.close_risk(risk_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="risk_not_found") from exc

    @router.get("/evidence/bundles")
    def evidence_bundles(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.evidence_bundles()

    @router.post("/evidence/bundles")
    def create_evidence_bundle(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        data.setdefault("actor", {"type": "user", "id": claims.sub})
        return service.create_evidence_bundle(data)

    @router.get("/evidence/bundles/{evidence_id}")
    def evidence_bundle(evidence_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_evidence_bundle(evidence_id)
        if record is None:
            raise HTTPException(status_code=404, detail="evidence_not_found")
        return record

    @router.post("/evidence/bundles/{evidence_id}/verify")
    def verify_evidence_bundle(evidence_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return service.verify_evidence_bundle(evidence_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="evidence_not_found") from exc

    @router.get("/evidence/search")
    def search_evidence(q: str, claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.search_evidence_bundles(q)

    @router.post("/policies")
    def create_policy(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        return service.create_policy(data)

    @router.get("/policies")
    def policies(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.policies()

    @router.post("/policies/evaluate")
    def evaluate_policy(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        return service.evaluate_policy(data)

    @router.post("/policies/{policy_id}/activate")
    def activate_policy(policy_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            active = True if payload is None else bool(payload.get("active", True))
            return service.activate_policy(policy_id, active=active)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="policy_not_found") from exc

    @router.get("/knowledge/nodes")
    def knowledge_nodes(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.knowledge_nodes()

    @router.post("/knowledge/nodes")
    def create_knowledge_node(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        return service.create_knowledge_node(data)

    @router.post("/knowledge/relationships")
    def create_knowledge_relationship(payload: KnowledgeLinkRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.create_knowledge_relationship(payload.source_id, payload.target_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="knowledge_node_not_found") from exc

    @router.get("/knowledge/trace/{node_id}")
    def knowledge_trace(node_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return service.knowledge_trace(node_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="knowledge_node_not_found") from exc

    @router.get("/knowledge/impact/{node_id}")
    def knowledge_impact(node_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return service.knowledge_impact(node_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="knowledge_node_not_found") from exc

    @router.post("/graph/nodes")
    def graph_nodes(payload: GraphNodeRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.create_knowledge_node(data)

    @router.post("/graph/edges")
    def graph_edges(payload: GraphEdgeRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.create_knowledge_relationship(payload.source_id, payload.target_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="knowledge_node_not_found") from exc

    @router.post("/graph/query")
    def graph_query(payload: GraphQueryRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.graph_query(payload.query)

    @router.post("/graph/federation/query")
    def graph_federation_query(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.graph_federation_query(payload)

    @router.post("/graph/analytics/blast-radius")
    def graph_blast_radius(payload: GraphQueryRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.graph_blast_radius(payload.query)

    @router.post("/graph/analytics/root-cause")
    def graph_root_cause(payload: GraphQueryRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.graph_root_cause(payload.query)

    @router.post("/graph/analytics/critical-path")
    def graph_critical_path(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.graph_critical_path(str(payload.get("start_id") or ""), str(payload.get("end_id") or ""))

    @router.get("/graph/trace/{node_id}")
    def graph_trace(node_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.knowledge_trace(node_id)

    @router.get("/graph/impact/{node_id}")
    def graph_impact(node_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.knowledge_impact(node_id)

    @router.post("/graph/snapshots")
    def graph_snapshot(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = dict(payload)
        data["tenant_id"] = _tenant_context(claims)
        return service.graph_snapshot(data)

    @router.post("/graph/reconcile")
    def graph_reconcile(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.graph_reconcile()

    @router.get("/event-bus")
    def event_bus_snapshot(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.event_bus_snapshot()

    @router.get("/nera")
    def nera_manifest(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.nera_manifest()

    @router.get("/capabilities")
    def capability_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.capability_model()

    @router.get("/operating-model")
    def operating_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.operating_model()

    @router.get("/data-model")
    def data_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.data_model()

    @router.get("/knowledge-model")
    def knowledge_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.knowledge_model()

    @router.get("/technology-model")
    def technology_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.technology_model()

    @router.get("/governance-model")
    def governance_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.governance_model()

    @router.get("/ai-model")
    def ai_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.ai_model()

    @router.get("/digital-twin-model")
    def digital_twin_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_model()

    @router.get("/resilience-model")
    def resilience_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.resilience_model()

    @router.post("/session/login")
    def session_login(payload: dict[str, Any], response: Response, request: Request) -> dict[str, Any]:
        session_store = get_default_novacodepro_session_store()
        identifier = str(payload.get("identifier") or payload.get("email") or payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        role = payload.get("role")
        if not identifier or not password:
            raise HTTPException(status_code=400, detail="email_and_password_required")
        result = session_store.login(
            identifier=identifier,
            password=password,
            role=str(role) if role else None,
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host if request.client else "",
        )
        _set_session_cookies(response, result)
        return {
            "status": "authenticated",
            "user": {
                "user_id": result["session"]["user_id"],
                "email": result["session"]["email"],
                "display_name": result["session"]["display_name"],
                "organization": result["session"]["organization"],
                "assigned_roles": result["session"]["assigned_roles"],
                "active_role": result["session"]["active_role"],
            },
            "session": result["session"],
            "tokens": {
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
            },
        }

    @router.get("/session")
    def session(request: Request) -> dict[str, Any]:
        return _build_session_bootstrap(service, request)

    @router.get("/session/bootstrap")
    def session_bootstrap(request: Request) -> dict[str, Any]:
        return _build_session_bootstrap(service, request)

    @router.post("/session/refresh")
    def session_refresh(request: Request, response: Response) -> dict[str, Any]:
        session_store = get_default_novacodepro_session_store()
        result = session_store.refresh_session(request)
        _set_session_cookies(response, result)
        return result

    @router.post("/session/logout")
    def session_logout(request: Request, response: Response) -> dict[str, Any]:
        session_store = get_default_novacodepro_session_store()
        result = session_store.logout(request)
        _clear_session_cookies(response)
        response.headers["Cache-Control"] = "no-store"
        return result

    @router.get("/neaf")
    def neaf_manifest(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.neaf_manifest()

    @router.get("/architecture-framework")
    def architecture_framework(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.architecture_framework()

    @router.post("/retry-queue")
    def enqueue_retry(payload: RetryQueueRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.repository.enqueue_retry(**payload.model_dump())

    @router.get("/retry-queue")
    def retry_queue(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.repository.list_retry_queue()

    @router.post("/retry-queue/{retry_id}/dead-letter")
    def dead_letter(retry_id: str, payload: DeadLetterRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.repository.move_retry_to_dead_letter(retry_id, failure_reason=payload.failure_reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="retry_not_found") from exc

    @router.get("/dead-letter-queue")
    def dead_letter_queue(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.repository.list_dead_letter_queue()

    @router.post("/releases/{release_id}/build")
    def build_release(release_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.build_release(release_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="release_not_found") from exc

    @router.post("/releases/{release_id}/sign")
    def sign_release(release_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.sign_release(release_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="release_not_found") from exc

    @router.post("/releases/{release_id}/publish")
    def publish_release(release_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.publish_release(release_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="release_not_found") from exc

    @router.post("/releases/{release_id}/promote")
    def promote_release(release_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.promote_release(release_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="release_not_found") from exc

    @router.post("/releases/{release_id}/revoke")
    def revoke_release(release_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.revoke_release(release_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="release_not_found") from exc

    @router.post("/deployments/{deployment_id}/start")
    def start_deployment(deployment_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.start_deployment(deployment_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc
        except ValueError as exc:
            message = str(exc)
            try:
                detail = json.loads(message)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail=message) from exc
            raise HTTPException(status_code=409, detail=detail) from exc

    @router.post("/deployments/{deployment_id}/pause")
    def pause_deployment(deployment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.pause_deployment(deployment_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc

    @router.post("/deployments/{deployment_id}/resume")
    def resume_deployment(deployment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.resume_deployment(deployment_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc

    @router.post("/deployments/{deployment_id}/verify")
    def verify_deployment(deployment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.verify_deployment(deployment_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc

    @router.post("/deployments/{deployment_id}/rollback")
    def rollback_deployment(deployment_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.rollback_deployment(deployment_id, note=str((payload or {}).get("note") or ""), actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc

    @router.post("/deployments/{deployment_id}/complete")
    def complete_deployment(deployment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.complete_deployment(deployment_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment_not_found") from exc

    @router.get("/operations/health")
    def operations_health(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.operations_health()

    @router.get("/operations/metrics")
    def operations_metrics(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.operations_metrics()

    @router.get("/operations/incidents")
    def operations_incidents(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.operations_incidents()

    @router.post("/operations/incidents")
    def create_incident(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_incident(payload)

    @router.post("/operations/maintenance-windows")
    def create_maintenance_window(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_incident(
            {
                "title": str(payload.get("title") or "Maintenance Window"),
                "severity": str(payload.get("severity") or "low"),
                "status": "scheduled",
                "service": str(payload.get("service") or "NovaCodePro Platform"),
                "region": str(payload.get("region") or "Australia"),
                "details": dict(payload.get("details") or {}),
            }
        )

    @router.post("/operations/backups/{backup_id}/restore")
    def restore_backup(backup_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.restore_backup(backup_id, payload or {})

    @router.post("/sre/slis")
    def create_sli(payload: SliRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.sli_record(payload.model_dump())

    @router.post("/sre/slos")
    def create_slo(payload: SloRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.slo_record(payload.model_dump())

    @router.get("/sre/error-budgets")
    def error_budgets(service_name: str = "novacodepro-gateway", window: str = "30d", claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.error_budget(service_name, window)

    @router.get("/sre/capacity")
    def capacity(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.capacity()

    @router.post("/sre/chaos/experiments")
    def create_chaos_experiment(payload: ChaosExperimentRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.chaos_experiment(payload.model_dump())

    @router.get("/executive/briefings")
    def executive_briefings(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.briefings()

    @router.post("/executive/briefings")
    def create_executive_briefing(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_briefing(payload)

    @router.get("/executive/command-center")
    def executive_command_center(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.command_center()

    @router.get("/operating-fabric")
    def operating_fabric_manifest(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.operating_fabric_manifest()

    @router.get("/operating-fabric/maturity")
    def operating_fabric_maturity(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.sovereign_maturity_report()

    @router.get("/operating-fabric/production-readiness")
    def operating_fabric_production_readiness(profile: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.production_readiness(profile)

    @router.get("/edos")
    def enterprise_delivery_operating_system(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return edos_summary()

    @router.get("/edos/capabilities")
    def enterprise_delivery_capabilities(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return edos_capability_model()

    @router.get("/edos/capability-states")
    def enterprise_delivery_capability_states(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return capability_state_registry()

    @router.get("/edos/frontends")
    def enterprise_delivery_frontends(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return frontend_experience_registry()

    @router.get("/edos/backends")
    def enterprise_delivery_backends(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return backend_service_architecture()

    @router.get("/edos/authority-model")
    def enterprise_delivery_authority_model(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return authority_model()

    @router.get("/edos/runtime-certification")
    def enterprise_delivery_runtime_certification(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"components": infrastructure_certification_records()}

    @router.get("/edos/mobile-release-certificate")
    def enterprise_delivery_mobile_release_certificate(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return mobile_release_certificate()

    @router.get("/edos/operational-evidence")
    def enterprise_delivery_operational_evidence(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return operational_evidence_manifest()

    @router.get("/edos/prr")
    def enterprise_delivery_prr(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return prr_governance_workflow()

    @router.get("/edos/maturity")
    def enterprise_delivery_maturity(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return edos_maturity_report()

    @router.get("/edos/readiness-matrix")
    def enterprise_delivery_readiness_matrix(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return enterprise_readiness_matrix()

    @router.get("/edos/continuous-compliance")
    def enterprise_delivery_continuous_compliance(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return continuous_compliance_model()

    @router.get("/edos/production-completion")
    def enterprise_delivery_production_completion(
        environment: str = "production",
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return production_completion_program(environment)

    @router.post("/edos/production-completion/ga-gate")
    def enterprise_delivery_ga_gate(
        payload: dict[str, Any] | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        body = payload or {}
        return evaluate_ga_governance(
            evidence=dict(body.get("evidence") or {}),
            approvals=dict(body.get("approvals") or {}),
        )

    @router.get("/edos/operational-readiness")
    def enterprise_delivery_operational_readiness(
        environment: str = "production",
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return operational_readiness_program(environment)

    @router.post("/edos/operational-readiness/evaluate")
    def evaluate_enterprise_operational_readiness(
        payload: OperationalReadinessEvaluationRequest,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return evaluate_operational_readiness(
            evidence=payload.evidence,
            approvals=payload.approvals,
            payment_evidence=payload.payment_evidence,
        )

    @router.get("/edos/ux-operating-system")
    def enterprise_delivery_ux_operating_system(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return ux_operating_system_summary()

    @router.get("/edos/ux-operating-system/studios")
    def enterprise_delivery_ux_studios(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return ux_studio_registry()

    @router.get("/edos/ux-operating-system/components")
    def enterprise_delivery_ux_components(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return component_registry_model()

    @router.get("/edos/ux-operating-system/ai-design")
    def enterprise_delivery_ai_design_studio(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return ai_design_studio_model()

    @router.get("/edos/ux-operating-system/validation")
    def enterprise_delivery_ux_validation(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return ux_validation_model()

    @router.get("/edos/ux-operating-system/services")
    def enterprise_delivery_uxos_services(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return uxos_service_architecture()

    @router.get("/edos/ux-operating-system/knowledge-graph")
    def enterprise_delivery_uxos_knowledge_graph(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return enterprise_design_knowledge_graph_model()

    @router.get("/edos/ux-operating-system/digital-twin")
    def enterprise_delivery_uxos_digital_twin(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return digital_ux_twin_model()

    @router.get("/edos/ux-operating-system/operational-completion")
    def enterprise_delivery_uxos_operational_completion(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return uxos_operational_completion_matrix()

    @router.get("/completion-standard")
    def enterprise_completion_standard(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return completion_standard_model()

    @router.get("/completion-standard/dashboard")
    def enterprise_completion_dashboard(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return completion_dashboard()

    @router.post("/completion-standard/evaluate")
    def evaluate_enterprise_completion(
        payload: CompletionEvaluationRequest,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return evaluate_completion_state(
            repository_complete=payload.repository_complete,
            operational_verified=payload.operational_verified,
            governance_approved=payload.governance_approved,
            production_ready_gates=payload.production_ready_gates,
            executive_authorized=payload.executive_authorized,
        )

    @router.post("/completion-standard/evidence")
    def create_completion_evidence(
        payload: CompletionEvidenceRequest,
        claims: JWTClaims = Depends(ux_editor),
    ) -> dict[str, Any]:
        body = payload.model_dump()
        body["executor"] = body.get("executor") or claims.sub
        return build_completion_evidence(body)

    @router.get("/ux/artifacts")
    def list_ux_artifacts(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.ux_artifacts()

    @router.post("/ux/artifacts")
    def create_ux_artifact(payload: UXArtifactCreateRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["actor"] = claims.sub
        return service.create_ux_artifact(data)

    @router.post("/ux/artifacts/{artifact_id}/transition")
    def transition_ux_artifact(
        artifact_id: str,
        payload: UXArtifactTransitionRequest,
        claims: JWTClaims = Depends(ux_editor),
    ) -> dict[str, Any]:
        try:
            return service.transition_ux_artifact(artifact_id, payload.target_state, actor=claims.sub, note=payload.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="ux_artifact_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/ux/artifacts/{artifact_id}/evidence")
    def attach_ux_artifact_evidence(
        artifact_id: str,
        payload: UXEvidenceAttachRequest,
        claims: JWTClaims = Depends(ux_editor),
    ) -> dict[str, Any]:
        try:
            return service.attach_ux_evidence(artifact_id, payload.evidence_refs, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="ux_artifact_not_found") from exc

    @router.post("/ux/releases/readiness")
    def assess_ux_release_readiness(claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.ux_release_readiness()

    @router.get("/uxos/operational-status")
    def uxos_operational_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.uxos_operational_status()

    @router.post("/uxos/design-sync")
    def create_ux_design_sync(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.create_ux_design_sync(payload.model_dump(), actor=claims.sub)

    @router.post("/uxos/visual-regression")
    def create_ux_visual_regression(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.create_ux_visual_regression(payload.model_dump(), actor=claims.sub)

    @router.post("/uxos/accessibility-scans")
    def create_ux_accessibility_scan(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.create_ux_accessibility_scan(payload.model_dump(), actor=claims.sub)

    @router.post("/uxos/analytics-events")
    def record_ux_analytics_event(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.record_ux_analytics_event(payload.model_dump(), actor=claims.sub)

    @router.post("/uxos/experiments")
    def create_ux_experiment(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.create_ux_experiment(payload.model_dump(), actor=claims.sub)

    @router.post("/uxos/knowledge-edges")
    def create_ux_knowledge_edge(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.create_ux_knowledge_edge(payload.model_dump(), actor=claims.sub)

    @router.post("/uxos/digital-twin-simulations")
    def create_ux_digital_twin_simulation(payload: UXOSServiceRecordRequest, claims: JWTClaims = Depends(ux_editor)) -> dict[str, Any]:
        return service.create_ux_digital_twin_simulation(payload.model_dump(), actor=claims.sub)

    @router.get("/enterprise-objects")
    def enterprise_objects(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.enterprise_objects()

    @router.get("/enterprise-capabilities")
    def enterprise_capabilities(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.enterprise_capabilities()

    @router.post("/enterprise-requests", status_code=202)
    def submit_enterprise_request(
        payload: EnterpriseOperatingRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="idempotency_key_required")
        data = payload.model_dump()
        extra = getattr(payload, "model_extra", None) or {}
        for key in ("tenant_id", "organization_id", "requested_by", "actor", "roles", "authority_level"):
            if key in extra:
                data[key] = extra[key]
        context = _execution_context(claims, payload.workspace_id, payload.requested_region)
        try:
            result = service.submit_enterprise_request(data, context=context, idempotency_key=idempotency_key)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        response.headers["Location"] = result["status_url"]
        return {
            "request_id": result["request_id"],
            "workflow_id": result["workflow_id"],
            "status": result["status"],
            "correlation_id": result["correlation_id"],
            "status_url": result["status_url"],
            "policy_outcome": result["policy_decision"]["outcome"],
            "approval_id": result["approval"]["id"],
        }

    @router.get("/enterprise-requests/{request_id}")
    def enterprise_request(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.repository.get("enterprise_object", request_id)
        if record is None or record.get("tenant_id") != _tenant_context(claims):
            raise HTTPException(status_code=404, detail="enterprise_request_not_found")
        return record

    @router.get("/command-center")
    def enterprise_command_center(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.enterprise_command_center()

    @router.get("/enterprise-relationships")
    def enterprise_relationships(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        tenant_id = _tenant_context(claims)
        return [item for item in service.enterprise_relationships() if item.get("tenant_id") == tenant_id]

    @router.get("/identity/roles/{role}/normalize")
    def normalize_authority_role(role: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.normalize_authority_role(role)

    @router.post("/executive/command-center/refresh")
    def refresh_executive_command_center(claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.command_center_refresh()

    @router.post("/executive/council/sessions")
    def create_executive_council_session(payload: ExecutiveCouncilSessionRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.executive_council_session(payload.model_dump())

    @router.get("/executive/council/sessions/{session_id}")
    def get_executive_council_session(session_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        session = service.repository.get("executive_council_session", session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="council_session_not_found")
        return session

    @router.post("/executive/agents/{role}/analyze")
    def analyze_executive_agent(role: str, payload: ExecutiveAgentAnalyzeRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.executive_agent_analyze(role, payload.model_dump())

    @router.post("/executive/council/synthesize")
    def synthesize_executive_council(payload: ExecutiveCouncilSynthesisRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.executive_council_synthesize(payload.model_dump())

    @router.post("/commands")
    def command(payload: CommandRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.run_command(payload.command, payload.context)

    @router.post("/knowledge/query")
    def query_knowledge(payload: KnowledgeQueryRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.knowledge_query(payload.query)

    @router.get("/events")
    def events(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.events()

    @router.get("/audit")
    def audit(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.audit()

    @router.post("/board/meetings")
    def board_meetings(payload: BoardMeetingRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.board_meeting(payload.model_dump())

    @router.post("/board/resolutions")
    def board_resolutions(payload: BoardResolutionRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.board_resolution(payload.model_dump())

    @router.post("/board/resolutions/{resolution_id}/vote")
    def board_vote(resolution_id: str, payload: BoardVoteRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.board_vote(resolution_id, payload.model_dump())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="board_resolution_not_found") from exc

    @router.post("/board/resolutions/{resolution_id}/close")
    def board_close(resolution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.board_close_resolution(resolution_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="board_resolution_not_found") from exc

    @router.get("/board/resolutions/{resolution_id}/evidence")
    def board_evidence(resolution_id: str, claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        try:
            return service.board_resolution_evidence(resolution_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="board_resolution_not_found") from exc

    @router.post("/events/topics")
    def create_event_topic(payload: EventTopicRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_event_topic(payload.model_dump())

    @router.get("/events/topics")
    def event_topics(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.event_topics()

    @router.post("/events/schemas")
    def create_event_schema(payload: EventSchemaRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_event_schema(payload.model_dump())

    @router.post("/events/replays")
    def create_event_replay(payload: EventReplayRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_event_replay(payload.model_dump())

    @router.get("/events/replays/{replay_id}")
    def get_event_replay(replay_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        replay = service.repository.get("event_replay", replay_id)
        if replay is None:
            raise HTTPException(status_code=404, detail="event_replay_not_found")
        return replay

    @router.post("/events/dead-letter/{event_id}/retry")
    def retry_dead_letter(event_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        matches = [event for event in service.repository.list_outbox(limit=1000, status=None) if event.get("event_id") == event_id]
        if not matches:
            raise HTTPException(status_code=404, detail="dead_letter_not_found")
        service.repository.fail_outbox_event(event_id, "")
        return {"event_id": event_id, "status": "retry_requested"}

    @router.post("/federation/agreements")
    def create_federation_agreement(payload: FederationAgreementRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["provider_org"] = _tenant_context(claims)
        return service.create_federation_agreement(data)

    @router.get("/federation/agreements")
    def federation_agreements(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.federation_agreements()

    @router.post("/federation/agreements/{agreement_id}/approve")
    def approve_federation_agreement(agreement_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.approve_federation_agreement(agreement_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="federation_agreement_not_found") from exc

    @router.post("/federation/agreements/{agreement_id}/revoke")
    def revoke_federation_agreement(agreement_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.revoke_federation_agreement(agreement_id, reason=str((payload or {}).get("reason") or ""))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="federation_agreement_not_found") from exc

    @router.post("/federation/authorize")
    def federation_authorize(payload: FederationAuthorizeRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.federation_authorize(payload.model_dump())

    @router.get("/federation/hierarchy")
    def federation_hierarchy(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.federation_hierarchy()

    @router.post("/federation/resources/share")
    def federation_share_resource(payload: FederationShareRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        data = payload.model_dump()
        data["tenant_id"] = _tenant_context(claims)
        return service.federation_share_resource(data)

    @router.post("/federation/resources/unshare")
    def federation_unshare_resource(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.federation_unshare_resource(str(payload.get("share_id") or payload.get("id") or ""))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="federation_share_not_found") from exc

    @router.get("/federation/audit")
    def federation_audit(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.federation_audit()

    @router.get("/regions")
    def regions(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.federation_hierarchy()

    @router.get("/regions/{region_id}/health")
    def region_health(region_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.region_health(region_id)

    @router.get("/regions/{region_id}/governance")
    def region_governance(region_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.region_governance(region_id)

    @router.post("/regions/{region_id}/eligibility/evaluate")
    def region_eligibility(region_id: str, payload: RegionEligibilityRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.evaluate_region_eligibility(region_id, payload.model_dump())

    @router.post("/regions/{region_id}/failover/plan")
    def region_failover_plan(region_id: str, payload: RegionFailoverRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.plan_region_failover(region_id, payload.model_dump())

    @router.post("/regions/{region_id}/failover/approve")
    def region_failover_approve(region_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.approve_region_failover(region_id, payload or {"approver": claims.sub})

    @router.post("/regions/{region_id}/failover/execute")
    def region_failover_execute(region_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.execute_region_failover(region_id, payload or {})

    @router.post("/regions/{region_id}/reconcile")
    def region_reconcile(region_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.reconcile_region(region_id)

    return router


__all__ = [
    "ArtifactCreateRequest",
    "AgentExecutionCreateRequest",
    "ApprovalCreateRequest",
    "ApprovalDecisionRequest",
    "CommandRequest",
    "CommentCreateRequest",
    "DeploymentCreateRequest",
    "DeploymentTransitionRequest",
    "IntegrationConnectRequest",
    "KnowledgeLinkRequest",
    "KnowledgeQueryRequest",
    "NovaCodeProPlatform",
    "NovaCodeProRepository",
    "MarketplaceInstallRequest",
    "ProjectCreateRequest",
    "ReleaseCreateRequest",
    "ReleaseTransitionRequest",
    "SolutionCreateRequest",
    "ThreadCreateRequest",
    "WorkflowCreateRequest",
    "WorkflowTransitionRequest",
    "build_novacodepro_platform_router",
    "get_novacodepro_platform",
]
