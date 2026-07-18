from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.api.auth.novacodepro_session_store import get_default_novacodepro_session_store
from afritech.novacodepro.ncp006a import ArchitectureError, ArchitectureExecutionContext, NovaCodeProNCP006AService
from afritech.novacodepro.platform import NovaCodeProPlatform


ACCESS_ROLES = (
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "DEVELOPER",
    "PRODUCT_MANAGER",
    "BUSINESS_ANALYST",
    "PROJECT_MANAGER",
    "ARCHITECT",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "COMPLIANCE_OFFICER",
    "EXECUTIVE",
    "AUDITOR",
)


def _ctx(claims: JWTClaims, *, workspace_id: str | None = None, project_id: str | None = None, request_id: str | None = None, causation_id: str | None = None) -> ArchitectureExecutionContext:
    return ArchitectureExecutionContext(
        actor_id=str(claims.sub),
        tenant_id=str(claims.tenant_id or claims.organization_id or "novatech"),
        organization_id=str(claims.organization_id or claims.tenant_id or "novatech"),
        workspace_id=workspace_id or claims.workspace_id,
        project_id=project_id,
        request_id=request_id,
        role=str(claims.role),
        permissions=tuple(str(permission) for permission in (claims.permissions or ())),
        session_id=str(claims.sid or ""),
        correlation_id=f"corr-{claims.sid or claims.sub}",
        causation_id=causation_id,
        environment="development",
    )


def _model_ctx(ncp006a: NovaCodeProNCP006AService, claims: JWTClaims, model_id: str | None) -> ArchitectureExecutionContext:
    if not model_id:
        return _ctx(claims)
    model = ncp006a.repository.get("architecture_model", model_id)
    if model is None:
        raise ArchitectureError("architecture_model_not_found", "Architecture model not found.", 404)
    if str(model.get("tenant_id") or "") != str(claims.tenant_id or claims.organization_id or "novatech"):
        raise ArchitectureError("cross_tenant_architecture_forbidden", "Cross-tenant access is forbidden.", 403)
    return _ctx(
        claims,
        workspace_id=str(model.get("workspace_id") or claims.workspace_id or ""),
        project_id=str(model.get("project_id") or getattr(claims, "project_id", None) or ""),
        request_id=str(model.get("request_id") or getattr(claims, "request_id", None) or ""),
    )


def _handle(error: ArchitectureError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message, "details": error.details},
    ) from error


class WorkspacePayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str | None = None
    workspace_id: str | None = None
    name: str
    slug: str | None = None
    description: str | None = None
    domain: str | None = None
    status: str | None = None
    owner_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str | None = None
    model_id: str | None = None
    workspace_id: str
    project_id: str | None = None
    request_id: str | None = None
    name: str
    slug: str | None = None
    description: str | None = None
    domain: str | None = None
    status: str | None = None
    owner_id: str | None = None
    component_ids: list[str] = Field(default_factory=list)
    interface_ids: list[str] = Field(default_factory=list)
    data_ids: list[str] = Field(default_factory=list)
    security_ids: list[str] = Field(default_factory=list)
    deployment_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)
    technology_standard: str | None = None
    threat_model: list[str] = Field(default_factory=list)
    slo: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChildPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str | None = None
    model_id: str
    name: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    validation_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str | None = None
    approval_id: str | None = None
    model_id: str | None = None
    requested_from: str | None = None
    required_role: str | None = None
    risk_class: str | None = None
    conditions: list[str] = Field(default_factory=list)
    reason: str | None = None
    decision: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_novacodepro_ncp006a_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(prefix="/architecture", tags=["novacodepro-architecture"])
    ncp006a = NovaCodeProNCP006AService(service.repository)
    observer = require_roles(*ACCESS_ROLES)
    editor = require_roles("ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN", "DEVELOPER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "PROJECT_MANAGER", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "SECURITY_ENGINEER", "COMPLIANCE_OFFICER", "EXECUTIVE")

    @router.get("/workspaces")
    def list_workspaces(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"workspaces": ncp006a.list_workspaces(_ctx(claims))}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/workspaces")
    def create_workspace(payload: WorkspacePayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.create_workspace(payload.model_dump(), _ctx(claims))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}")
    def get_workspace(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp006a.get_workspace(workspace_id, _ctx(claims, workspace_id=workspace_id))
        except ArchitectureError as error:
            _handle(error)

    @router.patch("/workspaces/{workspace_id}")
    def update_workspace(workspace_id: str, payload: WorkspacePayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.update_workspace(workspace_id, payload.model_dump(), _ctx(claims, workspace_id=workspace_id))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/workspaces/{workspace_id}/select")
    def select_workspace(workspace_id: str, request: Request, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            session_store = get_default_novacodepro_session_store()
            session = session_store.select_workspace(request, workspace_id)
            return {"session": session["session"], "claims": session["claims"], "workspace": ncp006a.get_workspace(workspace_id, _ctx(claims, workspace_id=workspace_id))}
        except ArchitectureError as error:
            _handle(error)

    @router.get("/models")
    def list_models(workspace_id: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"models": ncp006a.list_models(_ctx(claims, workspace_id=workspace_id), workspace_id=workspace_id)}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/models")
    def create_model(payload: ModelPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.create_model(payload.model_dump(), _ctx(claims, workspace_id=payload.workspace_id, project_id=payload.project_id, request_id=payload.request_id))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/models/{model_id}")
    def get_model(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp006a.get_model(model_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.patch("/models/{model_id}")
    def update_model(model_id: str, payload: ModelPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.update_model(model_id, payload.model_dump(), _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/models/{model_id}/archive")
    def archive_model(model_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.archive_model(model_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/models/{model_id}/versions")
    def list_versions(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"versions": ncp006a.list_versions(model_id, _model_ctx(ncp006a, claims, model_id))}
        except ArchitectureError as error:
            _handle(error)

    @router.get("/models/{model_id}/versions/{version_id}")
    def get_version(model_id: str, version_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp006a.get_version(model_id, version_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/models/from-ai-execution/{execution_id}")
    def draft_from_ai_execution(execution_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.draft_from_ai_execution({"execution_id": execution_id, **payload}, _ctx(claims, workspace_id=payload.get("workspace_id"), project_id=payload.get("project_id"), request_id=payload.get("request_id")))
        except ArchitectureError as error:
            _handle(error)

    def _child_list(route_prefix: str, kind: str, getter):
        @router.get(route_prefix)
        def _list(model_id: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
            try:
                return {kind: getter(_model_ctx(ncp006a, claims, model_id), model_id=model_id)}
            except ArchitectureError as error:
                _handle(error)

    def _child_create(route_prefix: str, kind: str, creator, permission: str = "architecture.create"):
        @router.post(route_prefix)
        def _create(payload: ChildPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return creator(payload.model_dump(), _model_ctx(ncp006a, claims, payload.model_id))
            except ArchitectureError as error:
                _handle(error)

    def _child_update(route_prefix: str, kind: str, updater):
        @router.get(route_prefix + "/{item_id}")
        def _get(item_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
            try:
                records = updater.__self__._list_kind(kind, _model_ctx(ncp006a, claims, None), model_id=None)  # type: ignore[attr-defined]
                for record in records:
                    if record["id"] == item_id:
                        return record
                raise ArchitectureError(f"{kind}_not_found", f"{kind.replace('_', ' ').title()} not found.", 404)
            except ArchitectureError as error:
                _handle(error)

        @router.patch(route_prefix + "/{item_id}")
        def _patch(item_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                model_id = str(payload.get("model_id") or payload.get("id") or "")
                return updater(item_id, payload, _model_ctx(ncp006a, claims, model_id))
            except ArchitectureError as error:
                _handle(error)

    _child_list("/components", "components", ncp006a.list_components)
    _child_create("/components", "architecture_component", ncp006a.create_component)
    _child_update("/components", "architecture_component", ncp006a.update_component)

    _child_list("/interfaces", "interfaces", ncp006a.list_interfaces)
    _child_create("/interfaces", "architecture_interface", ncp006a.create_interface)
    _child_update("/interfaces", "architecture_interface", ncp006a.update_interface)

    _child_list("/data", "data", ncp006a.list_data)
    _child_create("/data", "architecture_data", ncp006a.create_data)
    _child_update("/data", "architecture_data", ncp006a.update_data)

    _child_list("/security", "security", ncp006a.list_security)
    _child_create("/security", "architecture_security", ncp006a.create_security)
    _child_update("/security", "architecture_security", ncp006a.update_security)

    _child_list("/deployments", "deployments", ncp006a.list_deployments)
    _child_create("/deployments", "architecture_deployment", ncp006a.create_deployment)
    _child_update("/deployments", "architecture_deployment", ncp006a.update_deployment)

    @router.get("/relationships")
    def list_relationships(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"relationships": ncp006a.list_relationships(_model_ctx(ncp006a, claims, model_id), model_id=model_id)}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/relationships")
    def create_relationship(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.add_relationship(payload, _model_ctx(ncp006a, claims, str(payload.get("model_id") or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/traceability/links")
    def list_traceability_links(model_id: str | None = None, resource_type: str | None = None, resource_id: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {
                "links": ncp006a.list_traceability_links(
                    _model_ctx(ncp006a, claims, model_id),
                    resource_type=resource_type,
                    resource_id=resource_id,
                )
            }
        except ArchitectureError as error:
            _handle(error)

    @router.post("/traceability/links")
    def create_traceability_link(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.create_traceability_link(payload, _model_ctx(ncp006a, claims, str(payload.get("model_id") or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/traceability/coverage")
    def traceability_coverage(model_id: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp006a.calculate_traceability_coverage(_model_ctx(ncp006a, claims, model_id), model_id=model_id)
        except ArchitectureError as error:
            _handle(error)

    @router.get("/reviews")
    def list_reviews(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"reviews": ncp006a.list_reviews(model_id, _model_ctx(ncp006a, claims, model_id))}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/reviews")
    def create_review(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.create_review(str(payload.get("model_id") or ""), payload, _model_ctx(ncp006a, claims, str(payload.get("model_id") or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/reviews/{review_id}/complete")
    def complete_review(review_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.complete_review(str(payload.get("model_id") or ""), review_id, payload, _model_ctx(ncp006a, claims, str(payload.get("model_id") or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/approvals")
    def list_approvals(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"approvals": ncp006a.list_approvals(model_id, _model_ctx(ncp006a, claims, model_id))}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/approvals")
    def request_approval(payload: ApprovalPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.request_approval(str(payload.model_id or ""), payload.model_dump(), _model_ctx(ncp006a, claims, str(payload.model_id or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/approve")
    def approve(approval_id: str, payload: ApprovalPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.decide_approval(str(payload.model_id or ""), approval_id, {**payload.model_dump(), "decision": "APPROVED"}, _model_ctx(ncp006a, claims, str(payload.model_id or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/reject")
    def reject(approval_id: str, payload: ApprovalPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.decide_approval(str(payload.model_id or ""), approval_id, {**payload.model_dump(), "decision": "REJECTED"}, _model_ctx(ncp006a, claims, str(payload.model_id or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/request-changes")
    def request_changes(approval_id: str, payload: ApprovalPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.decide_approval(str(payload.model_id or ""), approval_id, {**payload.model_dump(), "decision": "CHANGES_REQUESTED"}, _model_ctx(ncp006a, claims, str(payload.model_id or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/baselines")
    def list_baselines(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"baselines": ncp006a.list_baselines(model_id, _model_ctx(ncp006a, claims, model_id))}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/baselines")
    def create_baseline(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.create_baseline(str(payload.get("model_id") or ""), payload, _model_ctx(ncp006a, claims, str(payload.get("model_id") or "")))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/baselines/{baseline_id}/approve")
    def approve_baseline(model_id: str, baseline_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.approve_baseline(model_id, baseline_id, payload, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/baselines/{baseline_id}/activate")
    def activate_baseline(model_id: str, baseline_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.activate_baseline(model_id, baseline_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.post("/baselines/{baseline_id}/supersede")
    def supersede_baseline(model_id: str, baseline_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.supersede_baseline(model_id, baseline_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/validation")
    def list_validation_results(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"validation_results": ncp006a.list_validation_results(_model_ctx(ncp006a, claims, model_id), model_id=model_id)}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/validation")
    def validate(model_id: str, payload: ValidationPayload, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.validate_model(model_id, payload.model_dump(), _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/fitness")
    def list_fitness_functions(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"fitness": ncp006a.list_fitness_functions(_model_ctx(ncp006a, claims, model_id), model_id=model_id)}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/fitness")
    def evaluate_fitness(model_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.evaluate_fitness(model_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/diagrams")
    def list_diagrams(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"diagrams": ncp006a.list_diagrams(_model_ctx(ncp006a, claims, model_id), model_id=model_id)}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/diagrams")
    def create_diagram(model_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.create_diagram(model_id, payload, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    @router.get("/impact")
    def list_impact(model_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"impact": ncp006a.list_impact(_model_ctx(ncp006a, claims, model_id), model_id=model_id)}
        except ArchitectureError as error:
            _handle(error)

    @router.post("/impact")
    def calculate_impact(model_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp006a.calculate_impact(model_id, _model_ctx(ncp006a, claims, model_id))
        except ArchitectureError as error:
            _handle(error)

    return router


__all__ = ["build_novacodepro_ncp006a_router"]
