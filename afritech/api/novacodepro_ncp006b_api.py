from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from afritech.api.auth.jwt_device_auth import JWTClaims, _cookie_secure, require_roles
from afritech.api.auth.novacodepro_session_store import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    get_default_novacodepro_session_store,
)
from afritech.novacodepro import NovaCodeProPlatform
from afritech.novacodepro.ncp006b import DesignError, DesignExecutionContext, NovaCodeProNCP006BService


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
    "UI_UX_DESIGNER",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "COMPLIANCE_OFFICER",
    "AUDITOR",
    "EXECUTIVE",
)

EDITOR_ROLES = (
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "PRODUCT_MANAGER",
    "BUSINESS_ANALYST",
    "PROJECT_MANAGER",
    "ARCHITECT",
    "UI_UX_DESIGNER",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "COMPLIANCE_OFFICER",
)

APPROVER_ROLES = (
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "PRODUCT_MANAGER",
    "BUSINESS_ANALYST",
    "PROJECT_MANAGER",
    "ARCHITECT",
    "UI_UX_DESIGNER",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "COMPLIANCE_OFFICER",
)


def _ctx(
    claims: JWTClaims,
    *,
    workspace_id: str | None = None,
    project_id: str | None = None,
    request_id: str | None = None,
    requirement_set_id: str | None = None,
    architecture_workspace_id: str | None = None,
    architecture_model_id: str | None = None,
    architecture_baseline_id: str | None = None,
    experience_workspace_id: str | None = None,
    design_project_id: str | None = None,
) -> DesignExecutionContext:
    return DesignExecutionContext(
        actor_id=str(claims.sub),
        tenant_id=str(claims.tenant_id or claims.organization_id or "novatech"),
        organization_id=str(claims.organization_id or claims.tenant_id or "novatech"),
        workspace_id=workspace_id or claims.workspace_id,
        project_id=project_id or getattr(claims, "project_id", None),
        request_id=request_id or getattr(claims, "request_id", None),
        requirement_set_id=requirement_set_id,
        architecture_workspace_id=architecture_workspace_id,
        architecture_model_id=architecture_model_id,
        architecture_baseline_id=architecture_baseline_id,
        experience_workspace_id=experience_workspace_id,
        design_project_id=design_project_id,
        role=str(claims.role),
        permissions=tuple(str(permission) for permission in (claims.permissions or ())),
        session_id=str(claims.sid or ""),
        correlation_id=f"corr-{claims.sid or claims.sub}",
        causation_id=claims.sid or None,
        environment="development",
    )


def _handle(error: DesignError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "retryable": False,
            "details": error.details,
            "correlationId": error.details.get("correlation_id", ""),
        },
    ) from error


def _payload(resource_id: str | None, payload: dict[str, Any], *, id_key: str = "id") -> dict[str, Any]:
    data = dict(payload)
    if resource_id and id_key not in data:
        data[id_key] = resource_id
    return data


def _resource_handler(service: NovaCodeProNCP006BService, resource_type: str, claims: JWTClaims, payload: dict[str, Any]) -> DesignExecutionContext:
    return _ctx(
        claims,
        workspace_id=str(payload.get("workspace_id") or payload.get("experience_workspace_id") or claims.workspace_id or ""),
        project_id=str(payload.get("project_id") or payload.get("design_project_id") or getattr(claims, "project_id", "") or ""),
        request_id=str(payload.get("request_id") or getattr(claims, "request_id", "") or ""),
        requirement_set_id=str(payload.get("requirement_set_id") or ""),
        architecture_workspace_id=str(payload.get("architecture_workspace_id") or ""),
        architecture_model_id=str(payload.get("architecture_model_id") or ""),
        architecture_baseline_id=str(payload.get("architecture_baseline_id") or ""),
        experience_workspace_id=str(payload.get("experience_workspace_id") or ""),
        design_project_id=str(payload.get("design_project_id") or payload.get("project_id") or getattr(claims, "project_id", "") or ""),
    )


def build_novacodepro_ncp006b_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(prefix="/design", tags=["novacodepro-design"])
    design = NovaCodeProNCP006BService(service.repository)
    observer = require_roles(*ACCESS_ROLES)
    editor = require_roles(*EDITOR_ROLES)
    approver = require_roles(*APPROVER_ROLES)

    @router.get("/workspaces")
    def list_workspaces(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"experience_workspaces": design.list_workspaces(_ctx(claims))}
        except DesignError as error:
            _handle(error)

    @router.post("/workspaces")
    def create_workspace(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_workspace(payload, _resource_handler(design, "experience_workspace", claims, payload))
        except DesignError as error:
            _handle(error)

    @router.get("/workspaces/{experience_workspace_id}")
    def get_workspace(experience_workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.get_workspace(experience_workspace_id, _ctx(claims, workspace_id=experience_workspace_id, experience_workspace_id=experience_workspace_id))
        except DesignError as error:
            _handle(error)

    @router.patch("/workspaces/{experience_workspace_id}")
    def update_workspace(experience_workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.update_workspace(experience_workspace_id, payload, _ctx(claims, workspace_id=experience_workspace_id, experience_workspace_id=experience_workspace_id))
        except DesignError as error:
            _handle(error)

    @router.post("/workspaces/{experience_workspace_id}/archive")
    def archive_workspace(experience_workspace_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.archive_workspace(experience_workspace_id, _ctx(claims, workspace_id=experience_workspace_id, experience_workspace_id=experience_workspace_id))
        except DesignError as error:
            _handle(error)

    @router.post("/workspaces/{experience_workspace_id}/restore")
    def restore_workspace(experience_workspace_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.restore_workspace(experience_workspace_id, _ctx(claims, workspace_id=experience_workspace_id, experience_workspace_id=experience_workspace_id))
        except DesignError as error:
            _handle(error)

    @router.post("/workspaces/{experience_workspace_id}/select")
    def select_workspace(experience_workspace_id: str, request: Request, response: Response, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            session_store = get_default_novacodepro_session_store()
            session = session_store.select_workspace(request, experience_workspace_id)
            response.set_cookie(
                key=ACCESS_COOKIE_NAME,
                value=session["access_token"],
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            response.set_cookie(
                key=REFRESH_COOKIE_NAME,
                value=session["refresh_token"],
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session["session"]["session_id"],
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=session["csrf_token"],
                httponly=False,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            workspace = design.get_workspace(experience_workspace_id, _ctx(claims, workspace_id=experience_workspace_id, experience_workspace_id=experience_workspace_id))
            return {"session": session["session"], "claims": session["claims"], "workspace": workspace}
        except DesignError as error:
            _handle(error)

    @router.get("/workspaces/{experience_workspace_id}/summary")
    def workspace_summary(experience_workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.workspace_summary(experience_workspace_id, _ctx(claims, workspace_id=experience_workspace_id, experience_workspace_id=experience_workspace_id))
        except DesignError as error:
            _handle(error)

    def _collection(resource_path: str, resource_type: str, *, list_key: str | None = None):
        plural_key = list_key or f"{resource_type}s"

        @router.get(resource_path)
        def _list(claims: JWTClaims = Depends(observer), workspace_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
            try:
                return {plural_key: design.list_resources(resource_type, _ctx(claims, workspace_id=workspace_id, project_id=project_id))}
            except DesignError as error:
                _handle(error)

        @router.post(resource_path)
        def _create(payload: dict[str, Any], claims: JWTClaims = Depends(editor), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
            try:
                body = dict(payload)
                if idempotency_key:
                    body["metadata"] = {**dict(body.get("metadata") or {}), "idempotency_key": idempotency_key}
                return design.create_resource(resource_type, body, _resource_handler(design, resource_type, claims, body))
            except DesignError as error:
                _handle(error)

        @router.get(f"{resource_path}/{{resource_id}}")
        def _get(resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
            try:
                return design.get_resource(resource_type, resource_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.patch(f"{resource_path}/{{resource_id}}")
        def _patch(resource_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return design.update_resource(resource_type, resource_id, payload, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.delete(f"{resource_path}/{{resource_id}}")
        def _delete(resource_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return design.delete_resource(resource_type, resource_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.post(f"{resource_path}/{{resource_id}}/archive")
        def _archive(resource_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return design.archive_resource(resource_type, resource_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.post(f"{resource_path}/{{resource_id}}/restore")
        def _restore(resource_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return design.restore_resource(resource_type, resource_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.get(f"{resource_path}/{{resource_id}}/versions")
        def _versions(resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
            try:
                return {"versions": design.list_versions(resource_type, resource_id, _ctx(claims))}
            except DesignError as error:
                _handle(error)

        @router.get(f"{resource_path}/{{resource_id}}/versions/{{version_id}}")
        def _version(resource_id: str, version_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
            try:
                return design.get_version(resource_type, resource_id, version_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.get(f"{resource_path}/{{resource_id}}/compare")
        def _compare(resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
            try:
                return design.compare_versions(resource_type, resource_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        @router.post(f"{resource_path}/{{resource_id}}/transition")
        def _transition(resource_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return design.transition_resource(
                    resource_type,
                    resource_id,
                    str(payload.get("status") or payload.get("target_status") or ""),
                    _ctx(claims),
                    reason=str(payload.get("reason") or ""),
                    approval_reference=payload.get("approval_reference"),
                    evidence_reference=payload.get("evidence_reference"),
                )
            except DesignError as error:
                _handle(error)

        @router.post(f"{resource_path}/{{resource_id}}/validate")
        def _validate(resource_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
            try:
                return design.validate_artifact(resource_type, resource_id, _ctx(claims))
            except DesignError as error:
                _handle(error)

        return _list, _create, _get, _patch, _delete

    for route, resource_type, list_key in [
        ("/briefs", "experience_brief", "briefs"),
        ("/research", "research_study", "research_studies"),
        ("/personas", "persona", "personas"),
        ("/journeys", "journey_map", "journeys"),
        ("/service-blueprints", "service_blueprint", "service_blueprints"),
        ("/information-architecture", "information_architecture", "information_architectures"),
        ("/user-flows", "user_flow", "user_flows"),
        ("/wireframes", "wireframe", "wireframes"),
        ("/screens", "screen_design", "screen_designs"),
        ("/systems", "design_system", "design_systems"),
        ("/tokens", "design_token", "design_tokens"),
        ("/themes", "theme", "themes"),
        ("/brands", "brand", "brands"),
        ("/components", "component_definition", "components"),
        ("/interaction-patterns", "interaction_pattern", "interaction_patterns"),
        ("/responsive-specifications", "responsive_specification", "responsive_specifications"),
        ("/content", "content_specification", "content_specifications"),
        ("/localization", "localization_resource", "localization_resources"),
        ("/accessibility", "accessibility_requirement", "accessibility_requirements"),
        ("/prototypes", "prototype", "prototypes"),
        ("/comments", "design_comment", "comments"),
        ("/risks", "design_risk", "risks"),
        ("/debt", "design_debt_item", "debt"),
    ]:
        _collection(route, resource_type, list_key=list_key)

    @router.post("/research/{research_id}/findings")
    def add_research_finding(research_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_research_finding(research_id, payload, _ctx(claims, workspace_id=str(payload.get("workspace_id") or claims.workspace_id or "")))
        except DesignError as error:
            _handle(error)

    @router.post("/research/{research_id}/complete")
    def complete_research(research_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.complete_research(research_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/journeys/{journey_id}/stages")
    def add_journey_stage(journey_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.add_journey_stage(journey_id, payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.patch("/journeys/{journey_id}/stages/{stage_id}")
    def update_journey_stage(journey_id: str, stage_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.update_journey_stage(journey_id, stage_id, payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/service-blueprints/{blueprint_id}/steps")
    def add_blueprint_step(blueprint_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.add_blueprint_step(blueprint_id, payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.patch("/service-blueprints/{blueprint_id}/steps/{step_id}")
    def update_blueprint_step(blueprint_id: str, step_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            blueprint = design.get_resource("service_blueprint", blueprint_id, _ctx(claims))
            steps = list(blueprint.get("steps") or [])
            for step in steps:
                if step.get("id") == step_id:
                    step.update(payload)
            blueprint["steps"] = steps
            blueprint["version"] = int(blueprint.get("version") or 1) + 1
            blueprint["updated_at"] = payload.get("updated_at") or blueprint["updated_at"]
            design.repository.upsert("service_blueprint", blueprint)
            return blueprint
        except DesignError as error:
            _handle(error)

    @router.post("/information-architecture/{ia_id}/nodes")
    def add_navigation_node(ia_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            ia = design.get_resource("information_architecture", ia_id, _ctx(claims))
            nodes = list(ia.get("nodes") or [])
            node = {"id": payload.get("id") or f"node-{len(nodes)+1}", **payload}
            nodes.append(node)
            ia["nodes"] = nodes
            ia["version"] = int(ia.get("version") or 1) + 1
            design.repository.upsert("information_architecture", ia)
            return node
        except DesignError as error:
            _handle(error)

    @router.patch("/information-architecture/{ia_id}/nodes/{node_id}")
    def update_navigation_node(ia_id: str, node_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            ia = design.get_resource("information_architecture", ia_id, _ctx(claims))
            nodes = list(ia.get("nodes") or [])
            for node in nodes:
                if node.get("id") == node_id:
                    node.update(payload)
            ia["nodes"] = nodes
            ia["version"] = int(ia.get("version") or 1) + 1
            design.repository.upsert("information_architecture", ia)
            return ia
        except DesignError as error:
            _handle(error)

    @router.delete("/information-architecture/{ia_id}/nodes/{node_id}")
    def delete_navigation_node(ia_id: str, node_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            ia = design.get_resource("information_architecture", ia_id, _ctx(claims))
            ia["nodes"] = [node for node in list(ia.get("nodes") or []) if node.get("id") != node_id]
            ia["version"] = int(ia.get("version") or 1) + 1
            design.repository.upsert("information_architecture", ia)
            return ia
        except DesignError as error:
            _handle(error)

    @router.post("/information-architecture/{ia_id}/validate")
    def validate_information_architecture(ia_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_artifact("information_architecture", ia_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/user-flows/{flow_id}/nodes")
    def add_flow_node(flow_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.add_flow_node(flow_id, payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/user-flows/{flow_id}/edges")
    def add_flow_edge(flow_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.add_flow_edge(flow_id, payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.patch("/user-flows/{flow_id}/nodes/{node_id}")
    def update_flow_node(flow_id: str, node_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            flow = design.get_resource("user_flow", flow_id, _ctx(claims))
            nodes = list(flow.get("nodes") or [])
            for node in nodes:
                if node.get("id") == node_id:
                    node.update(payload)
            flow["nodes"] = nodes
            flow["version"] = int(flow.get("version") or 1) + 1
            design.repository.upsert("user_flow", flow)
            return flow
        except DesignError as error:
            _handle(error)

    @router.patch("/user-flows/{flow_id}/edges/{edge_id}")
    def update_flow_edge(flow_id: str, edge_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            flow = design.get_resource("user_flow", flow_id, _ctx(claims))
            edges = list(flow.get("edges") or [])
            for edge in edges:
                if edge.get("id") == edge_id:
                    edge.update(payload)
            flow["edges"] = edges
            flow["version"] = int(flow.get("version") or 1) + 1
            design.repository.upsert("user_flow", flow)
            return flow
        except DesignError as error:
            _handle(error)

    @router.delete("/user-flows/{flow_id}/nodes/{node_id}")
    def delete_flow_node(flow_id: str, node_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            flow = design.get_resource("user_flow", flow_id, _ctx(claims))
            flow["nodes"] = [node for node in list(flow.get("nodes") or []) if node.get("id") != node_id]
            flow["version"] = int(flow.get("version") or 1) + 1
            design.repository.upsert("user_flow", flow)
            return flow
        except DesignError as error:
            _handle(error)

    @router.delete("/user-flows/{flow_id}/edges/{edge_id}")
    def delete_flow_edge(flow_id: str, edge_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            flow = design.get_resource("user_flow", flow_id, _ctx(claims))
            flow["edges"] = [edge for edge in list(flow.get("edges") or []) if edge.get("id") != edge_id]
            flow["version"] = int(flow.get("version") or 1) + 1
            design.repository.upsert("user_flow", flow)
            return flow
        except DesignError as error:
            _handle(error)

    @router.post("/user-flows/{flow_id}/validate")
    def validate_user_flow(flow_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_user_flow(flow_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/tokens/validate")
    def validate_tokens(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            tokens = list(payload.get("tokens") or [payload])
            return {"status": "PASS", "findings": design._validate_tokens(tokens)}  # noqa: SLF001
        except DesignError as error:
            _handle(error)

    @router.post("/tokens/export")
    def export_tokens(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_export_record(payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/tokens/import")
    def import_tokens(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_import_record(payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/themes/{theme_id}/validate")
    def validate_theme(theme_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_artifact("theme", theme_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/themes/{theme_id}/preview")
    def preview_theme(theme_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.get_resource("theme", theme_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/themes/{theme_id}/publish")
    def publish_theme(theme_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return design.transition_resource("theme", theme_id, "APPROVED", _ctx(claims), reason="theme published")
        except DesignError as error:
            _handle(error)

    @router.post("/components/{component_id}/validate")
    def validate_component(component_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_artifact("component_definition", component_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/components/{component_id}/deprecate")
    def deprecate_component(component_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.transition_resource("component_definition", component_id, "SUPERSEDED", _ctx(claims), reason="component deprecated")
        except DesignError as error:
            _handle(error)

    @router.get("/components/{component_id}/implementation-contract")
    def get_component_contract(component_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            component = design.get_resource("component_definition", component_id, _ctx(claims))
            return {"implementation_contract": component.get("implementation_contract") or {}}
        except DesignError as error:
            _handle(error)

    @router.post("/components/{component_id}/implementation-contract")
    def set_component_contract(component_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            component = design.get_resource("component_definition", component_id, _ctx(claims))
            component["implementation_contract"] = dict(payload)
            component["version"] = int(component.get("version") or 1) + 1
            design.repository.upsert("component_definition", component)
            return {"implementation_contract": component["implementation_contract"], "component": component}
        except DesignError as error:
            _handle(error)

    @router.post("/components/{component_id}/implementation-contract/validate")
    def validate_component_contract(component_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            component = design.get_resource("component_definition", component_id, _ctx(claims))
            if not component.get("implementation_contract"):
                raise DesignError("design_component_invalid", "Implementation contract is required.", 400)
            return {"status": "PASS", "component_id": component_id}
        except DesignError as error:
            _handle(error)

    @router.post("/components/{component_id}/implementation-contract/publish")
    def publish_component_contract(component_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            component = design.get_resource("component_definition", component_id, _ctx(claims))
            component["implementation_contract"] = {**dict(component.get("implementation_contract") or {}), "published": True}
            component["version"] = int(component.get("version") or 1) + 1
            design.repository.upsert("component_definition", component)
            design._emit("ComponentContractPublished", _ctx(claims), component)  # noqa: SLF001
            return {"implementation_contract": component["implementation_contract"], "component": component}
        except DesignError as error:
            _handle(error)

    @router.get("/traceability/links")
    def list_traceability_links(claims: JWTClaims = Depends(observer), resource_type: str | None = None, resource_id: str | None = None) -> dict[str, Any]:
        try:
            return {"links": design.list_traceability_links(_ctx(claims), resource_type=resource_type, resource_id=resource_id)}
        except DesignError as error:
            _handle(error)

    @router.post("/traceability/links")
    def create_traceability_link(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_traceability_link(payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/traceability/coverage")
    def traceability_coverage(claims: JWTClaims = Depends(observer), workspace_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
        try:
            return design.coverage(_ctx(claims, workspace_id=workspace_id, project_id=project_id), workspace_id=workspace_id, project_id=project_id)
        except DesignError as error:
            _handle(error)

    @router.post("/traceability/coverage/calculate")
    def calculate_traceability_coverage(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.coverage(_ctx(claims, workspace_id=payload.get("workspace_id"), project_id=payload.get("project_id")), workspace_id=payload.get("workspace_id"), project_id=payload.get("project_id"))
        except DesignError as error:
            _handle(error)

    @router.get("/traceability/gaps")
    def traceability_gaps(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            coverage = design.coverage(_ctx(claims))
            return {"gaps": coverage.get("gaps", [])}
        except DesignError as error:
            _handle(error)

    @router.post("/traceability/snapshots")
    def create_traceability_snapshot(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.traceability_snapshot(_ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/traceability/snapshots/{snapshot_id}")
    def get_traceability_snapshot(snapshot_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            snapshot = design.repository.get("design_traceability_snapshot", snapshot_id)
            if snapshot is None:
                raise DesignError("design_artifact_not_found", "Traceability snapshot not found.", 404)
            return snapshot
        except DesignError as error:
            _handle(error)

    @router.get("/reviews")
    def list_reviews(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"reviews": design.list_collection("design_review", _ctx(claims))}

    @router.post("/reviews")
    def create_review(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_review(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/reviews/{review_id}/complete")
    def complete_review(review_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.complete_review(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), review_id, payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/approvals")
    def list_approvals(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"approvals": design.list_collection("design_approval", _ctx(claims))}

    @router.post("/approvals")
    def create_approval(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_approval(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/approve")
    def approve_approval(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return design.decide_approval(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), approval_id, "APPROVED", payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/reject")
    def reject_approval(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return design.decide_approval(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), approval_id, "REJECTED", payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/request-changes")
    def request_changes_approval(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.decide_approval(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), approval_id, "CHANGES_REQUESTED", payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/baselines")
    def create_baseline(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_baseline(str(payload.get("design_project_id") or payload.get("project_id") or ""), payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/baselines/{baseline_id}")
    def get_baseline(baseline_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            baseline = design.repository.get("design_baseline", baseline_id)
            if baseline is None:
                raise DesignError("design_artifact_not_found", "Design baseline not found.", 404)
            return baseline
        except DesignError as error:
            _handle(error)

    @router.post("/baselines/{baseline_id}/supersede")
    def supersede_baseline(baseline_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.supersede_baseline(baseline_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/baselines/{baseline_id}/verify")
    def verify_baseline(baseline_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.verify_baseline(baseline_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/impact")
    def calculate_impact(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.calculate_impact(str(payload.get("resource_type") or "design_artifact"), str(payload.get("resource_id") or ""), _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/impact/{impact_id}")
    def get_impact(impact_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            impact = design.repository.get("design_impact_analysis", impact_id)
            if impact is None:
                raise DesignError("design_artifact_not_found", "Design impact analysis not found.", 404)
            return impact
        except DesignError as error:
            _handle(error)

    @router.post("/drift/calculate")
    def calculate_drift(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return design.calculate_drift(_ctx(claims, workspace_id=payload.get("workspace_id"), project_id=payload.get("project_id")), resource_type=str(payload.get("resource_type") or ""), resource_id=str(payload.get("resource_id") or ""))
        except DesignError as error:
            _handle(error)

    @router.get("/drift")
    def list_drift(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"drift": design.list_collection("design_drift", _ctx(claims))}

    @router.get("/drift/{drift_id}")
    def get_drift(drift_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            drift = design.repository.get("design_drift", drift_id)
            if drift is None:
                raise DesignError("design_drift_source_unavailable", "Design drift not found.", 404)
            return drift
        except DesignError as error:
            _handle(error)

    @router.post("/imports")
    def create_import(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_import_record(payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/imports/{import_id}")
    def get_import(import_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            record = design.repository.get("design_import", import_id)
            if record is None:
                raise DesignError("design_import_failed", "Design import not found.", 404)
            return record
        except DesignError as error:
            _handle(error)

    @router.post("/exports")
    def create_export(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_export_record(payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/exports/{export_id}")
    def get_export(export_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            record = design.repository.get("design_export", export_id)
            if record is None:
                raise DesignError("design_export_failed", "Design export not found.", 404)
            return record
        except DesignError as error:
            _handle(error)

    @router.post("/handoffs")
    def create_handoff(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_handoff(payload, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/handoffs")
    def list_handoffs(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"handoffs": design.list_collection("design_handoff", _ctx(claims))}

    @router.get("/ai/generations")
    def list_ai_generations(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"generations": design.list_collection("design_generation_record", _ctx(claims))}

    @router.post("/ai/drafts")
    def create_ai_design_draft(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_ai_design_draft(payload, _ctx(claims, project_id=payload.get("project_id")))
        except DesignError as error:
            _handle(error)

    @router.get("/handoffs/{handoff_id}")
    def get_handoff(handoff_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            handoff = design.repository.get("design_handoff", handoff_id)
            if handoff is None:
                raise DesignError("design_handoff_invalid", "Design handoff not found.", 404)
            return handoff
        except DesignError as error:
            _handle(error)

    @router.post("/handoffs/{handoff_id}/validate")
    def validate_handoff(handoff_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_handoff(handoff_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.post("/handoffs/{handoff_id}/publish")
    def publish_handoff(handoff_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            handoff = design.repository.get("design_handoff", handoff_id)
            if handoff is None:
                raise DesignError("design_handoff_invalid", "Design handoff not found.", 404)
            handoff["status"] = "PUBLISHED"
            design.repository.upsert("design_handoff", handoff)
            return handoff
        except DesignError as error:
            _handle(error)

    @router.post("/validation/rules")
    def create_validation_rule(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            record = dict(payload)
            record.setdefault("id", payload.get("id") or f"rule-{payload.get('name', 'design')}")
            record.setdefault("tenant_id", claims.tenant_id or claims.organization_id or "novatech")
            record.setdefault("workspace_id", claims.workspace_id)
            record.setdefault("status", "ENABLED")
            design.repository.upsert("design_validation_rule", record)
            return record
        except DesignError as error:
            _handle(error)

    @router.get("/validation/rules")
    def list_validation_rules(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"rules": design.list_collection("design_validation_rule", _ctx(claims))}

    @router.get("/validation/rules/{rule_id}")
    def get_validation_rule(rule_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            rule = design.repository.get("design_validation_rule", rule_id)
            if rule is None:
                raise DesignError("design_validation_failed", "Validation rule not found.", 404)
            return rule
        except DesignError as error:
            _handle(error)

    @router.patch("/validation/rules/{rule_id}")
    def update_validation_rule(rule_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            rule = design.repository.get("design_validation_rule", rule_id)
            if rule is None:
                raise DesignError("design_validation_failed", "Validation rule not found.", 404)
            rule.update(payload)
            design.repository.upsert("design_validation_rule", rule)
            return rule
        except DesignError as error:
            _handle(error)

    @router.post("/artifacts/{artifact_id}/validate")
    def validate_artifact(artifact_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            resource_type = str(payload.get("resource_type") or payload.get("artifact_type") or "experience_brief")
            return design.validate_artifact(resource_type, artifact_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/artifacts/{artifact_id}/validation-results")
    def list_artifact_validation_results(artifact_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {
            "validation_results": [
                item
                for item in design.list_collection("design_validation_result", _ctx(claims))
                if str(item.get("resource_id") or "") == artifact_id
            ]
        }

    @router.get("/validation/results/{result_id}")
    def get_validation_result(result_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            result = design.repository.get("design_validation_result", result_id)
            if result is None:
                raise DesignError("design_validation_failed", "Validation result not found.", 404)
            return result
        except DesignError as error:
            _handle(error)

    @router.post("/fitness-functions")
    def create_fitness_function(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            record = dict(payload)
            record.setdefault("id", payload.get("id") or f"fitness-{payload.get('name', 'design')}")
            record.setdefault("tenant_id", claims.tenant_id or claims.organization_id or "novatech")
            record.setdefault("workspace_id", claims.workspace_id)
            design.repository.upsert("design_fitness_function", record)
            return record
        except DesignError as error:
            _handle(error)

    @router.get("/fitness-functions")
    def list_fitness_functions(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"fitness_functions": design.list_collection("design_fitness_function", _ctx(claims))}

    @router.get("/fitness-functions/{fitness_id}")
    def get_fitness_function(fitness_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            fitness = design.repository.get("design_fitness_function", fitness_id)
            if fitness is None:
                raise DesignError("design_fitness_failed", "Fitness function not found.", 404)
            return fitness
        except DesignError as error:
            _handle(error)

    @router.patch("/fitness-functions/{fitness_id}")
    def update_fitness_function(fitness_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            fitness = design.repository.get("design_fitness_function", fitness_id)
            if fitness is None:
                raise DesignError("design_fitness_failed", "Fitness function not found.", 404)
            fitness.update(payload)
            design.repository.upsert("design_fitness_function", fitness)
            return fitness
        except DesignError as error:
            _handle(error)

    @router.post("/fitness-functions/{fitness_id}/execute")
    def execute_fitness_function(fitness_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_fitness(fitness_id, _ctx(claims))
        except DesignError as error:
            _handle(error)

    @router.get("/fitness-functions/{fitness_id}/results")
    def fitness_function_results(fitness_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"results": [item for item in design.list_collection("design_metric_record", _ctx(claims)) if str(item.get("fitness_id") or "") == fitness_id]}
        except DesignError as error:
            _handle(error)

    @router.post("/projects/{design_project_id}/fitness/execute")
    def execute_project_fitness(design_project_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.validate_fitness(design_project_id, _ctx(claims, project_id=design_project_id, design_project_id=design_project_id))
        except DesignError as error:
            _handle(error)

    @router.get("/projects/{design_project_id}/fitness/results")
    def project_fitness_results(design_project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"results": [item for item in design.list_collection("design_metric_record", _ctx(claims, project_id=design_project_id, design_project_id=design_project_id)) if str(item.get("project_id") or "") == design_project_id]}
        except DesignError as error:
            _handle(error)

    @router.get("/projects/{design_project_id}/baselines")
    def list_project_baselines(design_project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"baselines": [item for item in design.list_collection("design_baseline", _ctx(claims, project_id=design_project_id, design_project_id=design_project_id)) if str(item.get("design_project_id") or item.get("project_id") or "") == design_project_id]}

    @router.post("/projects/{design_project_id}/baseline")
    def create_project_baseline(design_project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return design.create_baseline(design_project_id, payload, _ctx(claims, project_id=design_project_id, design_project_id=design_project_id))
        except DesignError as error:
            _handle(error)

    @router.get("/projects/{design_project_id}/baselines/{baseline_id}")
    def get_project_baseline(design_project_id: str, baseline_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            baseline = design.repository.get("design_baseline", baseline_id)
            if baseline is None or str(baseline.get("design_project_id") or baseline.get("project_id") or "") != design_project_id:
                raise DesignError("design_artifact_not_found", "Design baseline not found.", 404)
            return baseline
        except DesignError as error:
            _handle(error)

    return router


__all__ = ["build_novacodepro_ncp006b_router"]
