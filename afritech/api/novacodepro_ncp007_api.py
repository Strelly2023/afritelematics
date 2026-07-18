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
from afritech.novacodepro.ncp007 import DevelopmentError, DevelopmentExecutionContext, NovaCodeProNCP007Service
from afritech.novacodepro.platform import NovaCodeProPlatform


ACCESS_ROLES = (
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "DEVELOPER",
    "SENIOR_DEVELOPER",
    "TECH_LEAD",
    "PROJECT_OWNER",
    "PRODUCT_MANAGER",
    "BUSINESS_ANALYST",
    "ARCHITECT",
    "DESIGNER",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "RELEASE_MANAGER",
    "APPROVER",
    "AUDITOR",
    "READ_ONLY_REVIEWER",
    "AI_AGENT",
    "SERVICE_ACCOUNT",
)

EDITOR_ROLES = (
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "DEVELOPER",
    "SENIOR_DEVELOPER",
    "TECH_LEAD",
    "PROJECT_OWNER",
    "PRODUCT_MANAGER",
    "BUSINESS_ANALYST",
    "ARCHITECT",
    "DESIGNER",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "RELEASE_MANAGER",
    "APPROVER",
    "AI_AGENT",
    "SERVICE_ACCOUNT",
)

APPROVER_ROLES = (
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "TECH_LEAD",
    "RELEASE_MANAGER",
    "SECURITY_ENGINEER",
    "APPROVER",
)


def _ctx(claims: JWTClaims, *, workspace_id: str | None = None, project_id: str | None = None, session_id: str | None = None, request_id: str | None = None) -> DevelopmentExecutionContext:
    permissions = tuple(str(permission) for permission in (claims.permissions or ()))
    return DevelopmentExecutionContext(
        actor_id=str(claims.sub),
        tenant_id=str(claims.tenant_id or claims.organization_id or "novatech"),
        organization_id=str(claims.organization_id or claims.tenant_id or "novatech"),
        workspace_id=workspace_id or claims.workspace_id,
        project_id=project_id or getattr(claims, "project_id", None),
        role=str(claims.role),
        permissions=permissions,
        session_id=session_id or claims.sid or None,
        correlation_id=f"dev-{claims.sid or claims.sub}",
        causation_id=claims.sid or None,
        request_id=request_id or getattr(claims, "request_id", None),
        environment="development",
    )


def _service(platform: NovaCodeProPlatform) -> NovaCodeProNCP007Service:
    return NovaCodeProNCP007Service(platform.repository)


def _handle(error: DevelopmentError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "correlationId": error.details.get("correlation_id", ""),
        },
    ) from error


def _payload(resource_id: str | None, payload: dict[str, Any], *, id_key: str = "id") -> dict[str, Any]:
    data = dict(payload)
    if resource_id and id_key not in data:
        data[id_key] = resource_id
    return data


def _set_session_cookies(response: Response, result: dict[str, Any]) -> None:
    response.set_cookie(key=ACCESS_COOKIE_NAME, value=result["access_token"], httponly=True, secure=_cookie_secure(), samesite="lax", path="/")
    response.set_cookie(key=REFRESH_COOKIE_NAME, value=result["refresh_token"], httponly=True, secure=_cookie_secure(), samesite="lax", path="/")
    response.set_cookie(key=SESSION_COOKIE_NAME, value=result["session"]["session_id"], httponly=True, secure=_cookie_secure(), samesite="lax", path="/")
    response.set_cookie(key=CSRF_COOKIE_NAME, value=result["csrf_token"], httponly=False, secure=_cookie_secure(), samesite="lax", path="/")


def build_novacodepro_ncp007_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(prefix="/api/v1/development", tags=["novacodepro-development"])
    dev = _service(service)
    observer = require_roles(*ACCESS_ROLES)
    editor = require_roles(*EDITOR_ROLES)
    approver = require_roles(*APPROVER_ROLES)

    @router.get("/workspaces")
    def list_workspaces(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            ctx = _ctx(claims)
            return {"workspaces": dev.list_workspaces(ctx)}
        except DevelopmentError as error:
            _handle(error)

    @router.post("/workspaces")
    def create_workspace(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_workspace(payload, _ctx(claims, workspace_id=payload.get("workspace_id"), project_id=payload.get("project_id")))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}")
    def get_workspace(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_workspace(workspace_id, _ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.patch("/workspaces/{workspace_id}")
    def update_workspace(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.update_workspace(workspace_id, payload, _ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/workspaces/{workspace_id}/archive")
    def archive_workspace(workspace_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.archive_workspace(workspace_id, _ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/workspaces/{workspace_id}/restore")
    def restore_workspace(workspace_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.restore_workspace(workspace_id, _ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}/summary")
    def workspace_summary(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.workspace_summary(workspace_id, _ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/workspaces/{workspace_id}/select")
    def select_workspace(workspace_id: str, request: Request, response: Response, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            session_store = get_default_novacodepro_session_store()
            session = session_store.select_workspace(request, workspace_id)
            workspace = {"id": workspace_id, "status": "SELECTED"}
            try:
                workspace = dev.get_workspace(workspace_id, _ctx(claims, workspace_id=workspace_id))
            except DevelopmentError:
                workspace = {**workspace, "selection_warning": "workspace_detail_unavailable"}
            _set_session_cookies(response, session)
            return {"session": session["session"], "claims": session["claims"], "workspace": workspace}
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}/repository/tree")
    def repository_tree(workspace_id: str, path: str = ".", claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.repository_tree(_ctx(claims, workspace_id=workspace_id), path=path)
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}/repository/file")
    def repository_file(workspace_id: str, path: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.repository_file(_ctx(claims, workspace_id=workspace_id), path=path)
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}/repository/search")
    def repository_search(workspace_id: str, query: str, path: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.repository_search(_ctx(claims, workspace_id=workspace_id), query, path=path)
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}/repository/status")
    def repository_status(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.repository_status(_ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/workspaces/{workspace_id}/repository/diff")
    def repository_diff(workspace_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.repository_diff(_ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/workspaces/{workspace_id}/sessions")
    def create_session(workspace_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_session(workspace_id, payload, _ctx(claims, workspace_id=workspace_id))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/sessions/{session_id}")
    def get_session(session_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_session(session_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/sessions/{session_id}/complete")
    def complete_session(session_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.complete_session(session_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/sessions/{session_id}/cancel")
    def cancel_session(session_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.cancel_session(session_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/sessions/{session_id}/tasks")
    def list_tasks(session_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"tasks": dev.list_tasks(session_id, _ctx(claims))}
        except DevelopmentError as error:
            _handle(error)

    @router.post("/sessions/{session_id}/tasks")
    def create_task(session_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_task(session_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.patch("/tasks/{task_id}")
    def update_task(task_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.update_task(task_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/tasks/{task_id}/generate")
    def generate(task_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
        try:
            body = dict(payload)
            if idempotency_key:
                body.setdefault("metadata", {})
                body["metadata"]["idempotency_key"] = idempotency_key
            return dev.create_generation_request(task_id, body, _ctx(claims, request_id=body.get("request_id")))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/generation-requests/{request_id}")
    def get_generation_request(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_generation_request(request_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/generation-requests/{request_id}/retry")
    def retry_generation_request(request_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.retry_generation_request(request_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/generation-requests/{request_id}/cancel")
    def cancel_generation_request(request_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.cancel_generation_request(request_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}")
    def get_change_set(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_change_set(change_set_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}/files")
    def get_change_set_files(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"files": dev.list_change_set_files(change_set_id, _ctx(claims))}
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}/diff")
    def get_change_set_diff(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            change_set = dev.get_change_set(change_set_id, _ctx(claims))
            return {"change_set_id": change_set_id, "summary": change_set.get("summary"), "files": dev.list_change_set_files(change_set_id, _ctx(claims))}
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/dry-run")
    def dry_run_change_set(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.dry_run_change_set(change_set_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/apply")
    def apply_change_set(change_set_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.apply_change_set(change_set_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/revert")
    def revert_change_set(change_set_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.revert_change_set(change_set_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/reject")
    def reject_change_set(change_set_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return dev.reject_change_set(change_set_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/validations")
    def create_validation(change_set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_validation_run(change_set_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}/validations")
    def list_validations(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"validation_runs": dev.list_validation_runs(change_set_id, _ctx(claims))}
        except DevelopmentError as error:
            _handle(error)

    @router.get("/validation-runs/{validation_run_id}")
    def get_validation_run(validation_run_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_validation_run(validation_run_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/validation-runs/{validation_run_id}/cancel")
    def cancel_validation_run(validation_run_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.cancel_validation_run(validation_run_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/reviews")
    def create_review(change_set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_review(change_set_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}/reviews")
    def list_reviews(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"reviews": dev.list_reviews(change_set_id, _ctx(claims))}
        except DevelopmentError as error:
            _handle(error)

    @router.post("/reviews/{review_id}/comments")
    def add_review_comment(review_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.add_review_comment(review_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.patch("/review-comments/{comment_id}")
    def update_review_comment(comment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.update_review_comment(comment_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/reviews/{review_id}/approve")
    def approve_review(review_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return dev.decide_review(review_id, "APPROVED", _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/reviews/{review_id}/request-changes")
    def request_review_changes(review_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return dev.decide_review(review_id, "CHANGES_REQUESTED", _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/reviews/{review_id}/reject")
    def reject_review(review_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return dev.decide_review(review_id, "REJECTED", _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/approval-requests")
    def request_approval(change_set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.request_approval(change_set_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}/approvals")
    def list_approvals(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"approvals": dev.list_approvals(change_set_id, _ctx(claims))}
        except DevelopmentError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/approve")
    def approve(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return dev.decide_approval(approval_id, "APPROVED", _ctx(claims), payload)
        except DevelopmentError as error:
            _handle(error)

    @router.post("/approvals/{approval_id}/reject")
    def reject(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return dev.decide_approval(approval_id, "REJECTED", _ctx(claims), payload)
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/commit-proposals")
    def create_commit_proposal(change_set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_commit_proposal(change_set_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/commit-proposals/{proposal_id}")
    def get_commit_proposal(proposal_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_commit_proposal(proposal_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/commit-proposals/{proposal_id}/execute")
    def execute_commit_proposal(proposal_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.execute_commit_proposal(proposal_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/change-sets/{change_set_id}/pull-request-proposals")
    def create_pull_request_proposal(change_set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.create_pull_request_proposal(change_set_id, payload, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.post("/pull-request-proposals/{proposal_id}/execute")
    def execute_pull_request_proposal(proposal_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.execute_pull_request_proposal(proposal_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/sessions/{session_id}/timeline")
    def session_timeline(session_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"events": dev.timeline(_ctx(claims, session_id=session_id), session_id=session_id)}
        except DevelopmentError as error:
            _handle(error)

    @router.get("/change-sets/{change_set_id}/evidence")
    def change_set_evidence(change_set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"evidence": dev.evidence(_ctx(claims), change_set_id=change_set_id)}
        except DevelopmentError as error:
            _handle(error)

    @router.post("/sessions/{session_id}/commands")
    def execute_command(session_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return dev.execute_command(session_id, payload, _ctx(claims, session_id=session_id))
        except DevelopmentError as error:
            _handle(error)

    @router.get("/command-executions/{execution_id}")
    def get_command_execution(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return dev.get_command_run(execution_id, _ctx(claims))
        except DevelopmentError as error:
            _handle(error)

    return router
