from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles, _cookie_secure
from afritech.api.auth.novacodepro_session_store import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    get_default_novacodepro_session_store,
)
from afritech.novacodepro import NovaCodeProPlatform
from afritech.novacodepro.ncp003 import NCP003ExecutionContext, NovaCodeProNCP003Service


ADMIN_ROLES = {
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
}


def build_novacodepro_ncp003_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(tags=["novacodepro-ncp003"])
    ncp003 = NovaCodeProNCP003Service(service.repository)
    observer = require_roles(
        "OPERATOR",
        "ADMIN",
        "VERIFIER",
        "OBSERVER",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "CUSTOMER_SUPPORT",
        "OPERATIONS_TEAM",
        "BRAND_TEAM",
        "COMPLIANCE_TEAM",
        "AUDIT_TEAM",
        "SECURITY_ENGINEER",
        "INCIDENT_RESPONSE_TEAM",
        "DATA_ARCHITECT",
        "DATA_ENGINEER",
        "DATABASE_ENGINEER",
        "AI_ML_ENGINEER",
        "DATA_SCIENTIST",
        "PRIVACY_COMPLIANCE",
        "RISK_MANAGEMENT",
        "EXTERNAL_REGULATOR",
        "LEGAL",
        "CLIENT",
        "PARTNER",
        "CUSTOMER",
    )
    editor = require_roles(
        "OPERATOR",
        "ADMIN",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "CUSTOMER_SUPPORT",
        "OPERATIONS_TEAM",
        "BRAND_TEAM",
        "COMPLIANCE_TEAM",
        "AUDIT_TEAM",
        "SECURITY_ENGINEER",
        "INCIDENT_RESPONSE_TEAM",
        "DATA_ARCHITECT",
        "DATA_ENGINEER",
        "DATABASE_ENGINEER",
        "AI_ML_ENGINEER",
        "DATA_SCIENTIST",
        "PRIVACY_COMPLIANCE",
        "RISK_MANAGEMENT",
        "LEGAL",
    )

    def _ctx(claims: JWTClaims, workspace_id: str | None = None, *, correlation_id: str | None = None) -> NCP003ExecutionContext:
        permissions = tuple(sorted(set(str(permission) for permission in claims.permissions)))
        resolved_workspace_id = workspace_id or claims.workspace_id
        tenant_id = str(getattr(claims, "tenant_id", None) or claims.organization_id).lower()
        return NCP003ExecutionContext(
            actor_id=claims.sub,
            tenant_id=tenant_id,
            organization_id=claims.organization_id,
            workspace_id=resolved_workspace_id,
            role=claims.role,
            permissions=permissions,
            session_id=claims.sid or None,
            correlation_id=correlation_id or f"ncp003-{claims.sid or claims.sub}-{resolved_workspace_id or 'global'}",
            causation_id=claims.sid or None,
        )

    def _project(project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        project = ncp003.repository.get("project", project_id)
        if project is None:
            raise HTTPException(status_code=404, detail={"code": "project_not_found", "message": "Project was not found."})
        if str(project.get("tenant_id")) != ctx.tenant_id:
            raise HTTPException(status_code=403, detail={"code": "project_forbidden", "message": "You do not have access to this project."})
        return project

    def _request(request_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        request = ncp003.repository.get("request", request_id)
        if request is None:
            raise HTTPException(status_code=404, detail={"code": "request_not_found", "message": "Request was not found."})
        if str(request.get("tenant_id")) != ctx.tenant_id:
            raise HTTPException(status_code=403, detail={"code": "request_forbidden", "message": "You do not have access to this request."})
        return request

    def _map_domain_error(error: Exception) -> HTTPException:
        if isinstance(error, PermissionError):
            code = str(error)
            return HTTPException(status_code=403, detail={"code": code, "message": "Access denied."})
        if isinstance(error, ValueError):
            code = str(error)
            status = 409 if code in {"project_archived", "request_archived"} else 400
            return HTTPException(status_code=status, detail={"code": code, "message": code.replace("_", " ").capitalize()})
        if isinstance(error, KeyError):
            code = str(error).strip("'")
            status = 404
            return HTTPException(status_code=status, detail={"code": code, "message": code.replace("_", " ").capitalize()})
        return HTTPException(status_code=500, detail={"code": "service_unavailable", "message": "Service unavailable."})

    @router.get("/workspaces")
    def list_workspaces(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"workspaces": ncp003.list_workspaces(ctx)}

    @router.post("/workspaces")
    def create_workspace(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.create_workspace(payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/workspaces/{workspace_id}")
    def get_workspace(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            return ncp003._workspace_or_404(workspace_id, ctx)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "workspace_not_found", "message": "Workspace was not found."}) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail={"code": "workspace_forbidden", "message": "You do not have access to this workspace."}) from exc

    @router.patch("/workspaces/{workspace_id}")
    def update_workspace(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            return ncp003.update_workspace(workspace_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/workspaces/{workspace_id}/select")
    def select_workspace(
        workspace_id: str,
        request: Request,
        response: Response,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        session_store = get_default_novacodepro_session_store()
        try:
            session_result = session_store.select_workspace(request, workspace_id)
            response.set_cookie(
                key=ACCESS_COOKIE_NAME,
                value=session_result["access_token"],
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            response.set_cookie(
                key=REFRESH_COOKIE_NAME,
                value=session_result["refresh_token"],
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_result["session"]["session_id"],
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=session_result["csrf_token"],
                httponly=False,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
            selection = ncp003.select_workspace(workspace_id, ctx)
            return {
                "workspace": selection["workspace"],
                "membership": selection["membership"],
                "session": session_result["session"],
                "claims": session_result["claims"],
            }
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/workspaces/{workspace_id}/members")
    def workspace_members(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            return {"members": ncp003.workspace_members(workspace_id, ctx)}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/workspaces/{workspace_id}/members")
    def add_workspace_member(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            return ncp003.add_workspace_member(workspace_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/workspaces/{workspace_id}/members/{member_id}")
    def remove_workspace_member(workspace_id: str, member_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            ncp003.remove_workspace_member(workspace_id, member_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/workspaces/{workspace_id}/activity")
    def workspace_activity(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"activity": ncp003.workspace_activity(workspace_id, ctx)}

    @router.get("/workspaces/{workspace_id}/tasks")
    def workspace_tasks(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"tasks": ncp003.workspace_tasks(workspace_id, ctx)}

    @router.get("/workspaces/{workspace_id}/approvals")
    def workspace_approvals(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"approvals": ncp003.workspace_approvals(workspace_id, ctx)}

    @router.get("/workspaces/{workspace_id}/favorites")
    def workspace_favorites(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"favorites": ncp003.workspace_favorites(workspace_id, ctx)}

    @router.post("/workspaces/{workspace_id}/favorites")
    def add_workspace_favorite(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            return ncp003.add_workspace_favorite(workspace_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/workspaces/{workspace_id}/favorites/{favorite_id}")
    def remove_workspace_favorite(workspace_id: str, favorite_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            ncp003.remove_workspace_favorite(workspace_id, favorite_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/workspaces/{workspace_id}/notifications")
    def workspace_notifications(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"notifications": ncp003.workspace_notifications(workspace_id, ctx)}

    @router.patch("/workspaces/{workspace_id}/settings")
    def workspace_settings(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        try:
            return ncp003.update_workspace_settings(workspace_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects")
    def projects(workspace_id: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"projects": ncp003.list_projects(ctx, workspace_id=workspace_id)}

    @router.post("/projects")
    def create_project(
        payload: dict[str, Any],
        claims: JWTClaims = Depends(editor),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        ctx = _ctx(claims, payload.get("workspace_id"))
        try:
            return ncp003.create_project(payload, ctx, idempotency_key=idempotency_key)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}")
    def project(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return _project(project_id, ctx)

    @router.patch("/projects/{project_id}")
    def update_project(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.update_project(project_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/projects/{project_id}/archive")
    def archive_project(project_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.archive_project(project_id, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/projects/{project_id}/restore")
    def restore_project(project_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.restore_project(project_id, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/activity")
    def project_activity(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"activity": ncp003.project_activity(project_id, ctx)}

    @router.get("/projects/{project_id}/members")
    def project_members(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"members": ncp003.project_members(project_id, ctx)}

    @router.post("/projects/{project_id}/members")
    def add_project_member(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.add_project_member(project_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/projects/{project_id}/members/{member_id}")
    def remove_project_member(project_id: str, member_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            ncp003.remove_project_member(project_id, member_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/milestones")
    def milestones(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"milestones": ncp003.milestone_list(project_id, ctx)}

    @router.post("/projects/{project_id}/milestones")
    def create_milestone(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.create_milestone(project_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/milestones/{milestone_id}")
    def milestone(project_id: str, milestone_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return ncp003._project_record_or_404("project_milestone", milestone_id, project_id, ctx)

    @router.patch("/projects/{project_id}/milestones/{milestone_id}")
    def update_milestone(project_id: str, milestone_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.update_milestone(project_id, milestone_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/projects/{project_id}/milestones/{milestone_id}")
    def delete_milestone(project_id: str, milestone_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            ncp003.delete_milestone(project_id, milestone_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/work-items")
    def work_items(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"work_items": ncp003.list_work_items(project_id, ctx)}

    @router.post("/projects/{project_id}/work-items")
    def create_work_item(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.create_work_item(project_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/work-items/{work_item_id}")
    def work_item(project_id: str, work_item_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return ncp003._project_record_or_404("project_work_item", work_item_id, project_id, ctx)

    @router.patch("/projects/{project_id}/work-items/{work_item_id}")
    def update_work_item(project_id: str, work_item_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.update_work_item(project_id, work_item_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/projects/{project_id}/work-items/{work_item_id}/assign")
    def assign_work_item(project_id: str, work_item_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.assign_work_item(project_id, work_item_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/projects/{project_id}/work-items/{work_item_id}/transition")
    def transition_work_item(project_id: str, work_item_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.transition_work_item(project_id, work_item_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/projects/{project_id}/work-items/{work_item_id}")
    def delete_work_item(project_id: str, work_item_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            ncp003.delete_work_item(project_id, work_item_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/risks")
    def risks(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"risks": ncp003.list_risks(project_id, ctx)}

    @router.post("/projects/{project_id}/risks")
    def create_risk(project_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.create_risk(project_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.patch("/projects/{project_id}/risks/{risk_id}")
    def update_risk(project_id: str, risk_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.update_risk(project_id, risk_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/projects/{project_id}/roadmap")
    def roadmap(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return ncp003.roadmap(project_id, ctx)

    @router.get("/requests")
    def requests(workspace_id: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims, workspace_id)
        return {"requests": ncp003.list_requests(ctx, workspace_id=workspace_id)}

    @router.post("/requests")
    def create_request(
        payload: dict[str, Any],
        claims: JWTClaims = Depends(editor),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        ctx = _ctx(claims, payload.get("workspace_id"))
        try:
            return ncp003.create_request(payload, ctx, idempotency_key=idempotency_key)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/requests/{request_id}")
    def request_detail(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return _request(request_id, ctx)

    @router.patch("/requests/{request_id}")
    def update_request(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.update_request(request_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/requests/{request_id}/submit")
    def submit_request(request_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.submit_request(request_id, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/requests/{request_id}/transition")
    def transition_request(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.transition_request(request_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/requests/{request_id}/archive")
    def archive_request(request_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.archive_request(request_id, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/requests/{request_id}/history")
    def request_history(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"history": ncp003.request_history(request_id, ctx)}

    @router.get("/requests/{request_id}/assignments")
    def request_assignments(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"assignments": ncp003.request_assignments(request_id, ctx)}

    @router.post("/requests/{request_id}/assignments")
    def add_request_assignment(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.add_request_assignment(request_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/requests/{request_id}/assignments/{assignment_id}")
    def remove_request_assignment(request_id: str, assignment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            ncp003.remove_request_assignment(request_id, assignment_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/requests/{request_id}/comments")
    def request_comments(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"comments": ncp003.request_comments(request_id, ctx)}

    @router.post("/requests/{request_id}/comments")
    def add_request_comment(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.add_request_comment(request_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.patch("/requests/{request_id}/comments/{comment_id}")
    def update_request_comment(request_id: str, comment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.update_request_comment(request_id, comment_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.delete("/requests/{request_id}/comments/{comment_id}")
    def delete_request_comment(request_id: str, comment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            ncp003.delete_request_comment(request_id, comment_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/requests/{request_id}/attachments")
    def request_attachments(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"attachments": ncp003.request_attachments(request_id, ctx)}

    @router.post("/requests/{request_id}/attachments")
    def add_request_attachment(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.add_request_attachment(request_id, payload, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/requests/{request_id}/attachments/{attachment_id}")
    def request_attachment(request_id: str, attachment_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        attachment = ncp003.get_request_attachment(request_id, attachment_id, ctx)
        if attachment is None:
            raise HTTPException(status_code=404, detail={"code": "attachment_not_found", "message": "Attachment was not found."})
        return attachment

    @router.delete("/requests/{request_id}/attachments/{attachment_id}")
    def delete_request_attachment(request_id: str, attachment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            ncp003.delete_request_attachment(request_id, attachment_id, ctx)
            return {"status": "deleted"}
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.get("/notifications")
    def notifications(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"notifications": ncp003.notifications(ctx)}

    @router.patch("/notifications/{notification_id}/read")
    def read_notification(notification_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        try:
            return ncp003.read_notification(notification_id, ctx)
        except Exception as exc:
            raise _map_domain_error(exc) from exc

    @router.post("/notifications/read-all")
    def read_all_notifications(claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        ctx = _ctx(claims)
        return {"notifications": ncp003.read_all_notifications(ctx)}

    return router
