from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro import NovaCodeProPlatform
from afritech.novacodepro.ncp004 import NCP004Error, NCP004ExecutionContext, NovaCodeProNCP004Service


ACCESS_ROLES = (
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


def build_novacodepro_ncp004_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(prefix="/ai", tags=["novacodepro-ai"])
    ncp004 = NovaCodeProNCP004Service(service.repository)
    observer = require_roles(*ACCESS_ROLES)
    editor = require_roles(
        "OPERATOR",
        "ADMIN",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "SECURITY_ENGINEER",
        "COMPLIANCE_TEAM",
        "OPERATIONS_TEAM",
    )
    approver = require_roles(
        "OPERATOR",
        "ADMIN",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "SECURITY_ENGINEER",
        "COMPLIANCE_TEAM",
        "OPERATIONS_TEAM",
        "AUDITOR",
        "COMPLIANCE_OFFICER",
        "EXTERNAL_REGULATOR",
    )

    def _ctx(claims: JWTClaims, *, execution_id: str | None = None, project_id: str | None = None, request_id: str | None = None, correlation_id: str | None = None) -> NCP004ExecutionContext:
        workspace_id = claims.workspace_id or ""
        permissions = tuple(sorted({str(permission) for permission in claims.permissions}))
        if not workspace_id:
            raise HTTPException(status_code=409, detail={"code": "workspace_required", "message": "Workspace context is required."})
        return NCP004ExecutionContext(
            execution_id=execution_id or request_id or workspace_id,
            actor_id=claims.sub,
            tenant_id=str(claims.tenant_id or claims.organization_id).lower(),
            organization_id=claims.organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            request_id=request_id,
            role=claims.role,
            permissions=permissions,
            environment="development",
            session_id=claims.sid or None,
            correlation_id=correlation_id or f"ncp004-{claims.sid or claims.sub}-{execution_id or request_id or workspace_id}",
            causation_id=claims.sid or None,
            approval_references=(),
        )

    def _map_error(error: Exception) -> HTTPException:
        if isinstance(error, NCP004Error):
            return HTTPException(
                status_code=error.status_code,
                detail={
                    "code": error.code,
                    "message": error.message,
                    "retryable": error.retryable,
                    "details": error.details,
                    "correlationId": error.details.get("correlation_id", ""),
                },
            )
        if isinstance(error, PermissionError):
            return HTTPException(status_code=403, detail={"code": "ai_execution_forbidden", "message": str(error)})
        if isinstance(error, KeyError):
            return HTTPException(status_code=404, detail={"code": str(error).strip("'"), "message": str(error).strip("'").replace("_", " ")})
        return HTTPException(status_code=500, detail={"code": "service_unavailable", "message": "Service unavailable."})

    @router.get("/executions")
    def list_executions(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"executions": ncp004.list_executions(_ctx(claims))}

    @router.post("/executions")
    def create_execution(payload: dict[str, Any], claims: JWTClaims = Depends(editor), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
        ctx = _ctx(claims, project_id=payload.get("project_id"), request_id=payload.get("request_id"))
        try:
            if idempotency_key:
                payload = {**payload, "idempotency_key": idempotency_key}
            execution = ncp004.create_execution(payload, ctx)
            return execution
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}")
    def get_execution(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.get_execution(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/analyse")
    def analyse_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.analyse_execution(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}/clarifications")
    def list_clarifications(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"clarifications": ncp004.list_clarifications(execution_id, _ctx(claims, execution_id=execution_id))}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/clarifications/{clarification_id}/answer")
    def answer_clarification(execution_id: str, clarification_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.answer_clarification(execution_id, clarification_id, payload, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/clarifications/complete")
    def complete_clarifications(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.complete_clarifications(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/generate-requirements")
    def generate_requirements(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.generate_requirements(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/generate-plan")
    def generate_plan(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.generate_plan(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}/plan")
    def get_plan(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            execution = ncp004.get_execution(execution_id, _ctx(claims, execution_id=execution_id))
            return {"plan": execution.get("plan") or {}}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/plan/regenerate")
    def regenerate_plan(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            execution = ncp004.get_execution(execution_id, _ctx(claims, execution_id=execution_id))
            execution["plan"] = {}
            execution["requirements"] = execution.get("requirements") or []
            ncp004.repository.upsert("ai_execution", execution)
            return ncp004.generate_plan(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/plan/validate")
    def validate_plan(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.validate_plan(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/request-approval")
    def request_approval(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.request_approval(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/approvals")
    def approvals(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"approvals": ncp004.list_approvals(_ctx(claims))}

    @router.get("/approvals/{approval_id}")
    def approval(approval_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.get_approval(approval_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/approvals/{approval_id}/approve")
    def approve(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp004.approve(approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/approvals/{approval_id}/reject")
    def reject(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp004.reject(approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/approvals/{approval_id}/request-changes")
    def request_changes(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp004.request_changes(approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/execute")
    def execute(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.execute(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/verify")
    def verify(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.verify(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/cancel")
    def cancel(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.cancel(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/pause")
    def pause(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.pause(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/resume")
    def resume(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.resume(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/rollback")
    def rollback(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.rollback(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}/timeline")
    def timeline(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"timeline": ncp004.timeline(execution_id, _ctx(claims, execution_id=execution_id))}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}/evidence")
    def evidence(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"evidence": ncp004.evidence(execution_id, _ctx(claims, execution_id=execution_id))}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}/replay")
    def replay(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.replay(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/agents")
    def agents(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"agents": ncp004.list_agents(_ctx(claims))}

    @router.post("/agents")
    def create_agent(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.create_agent(payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/agents/{agent_id}")
    def get_agent(agent_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.get_agent(agent_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/agents/{agent_id}")
    def patch_agent(agent_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.patch_agent(agent_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/agents/{agent_id}/versions")
    def add_agent_version(agent_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.add_agent_version(agent_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/agents/{agent_id}/enable")
    def enable_agent(agent_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.enable_agent(agent_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/agents/{agent_id}/disable")
    def disable_agent(agent_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.disable_agent(agent_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/tools")
    def tools(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"tools": ncp004.list_tools(_ctx(claims))}

    @router.get("/tools/{tool_id}")
    def tool(tool_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.get_tool(tool_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/tools/{tool_id}/enable")
    def enable_tool(tool_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.enable_tool(tool_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/tools/{tool_id}/disable")
    def disable_tool(tool_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.disable_tool(tool_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/notifications")
    def notifications(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"notifications": ncp004.notifications(_ctx(claims))}

    @router.patch("/notifications/{notification_id}/read")
    def read_notification(notification_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.read_notification(notification_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/notifications/read-all")
    def read_all_notifications(claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.read_all_notifications(_ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requests")
    def legacy_requests(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"executions": ncp004.list_executions(_ctx(claims))}

    @router.post("/requests")
    def legacy_request_create(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.request_alias(payload, _ctx(claims))["request"]
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requests/{request_id}")
    def legacy_request_get(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.execution_alias(request_id, _ctx(claims, execution_id=request_id))["request"]
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requests/{request_id}/plan")
    def legacy_request_plan(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.execution_plan_alias(request_id, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/interpretation")
    def legacy_request_interpretation(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.update_interpretation(request_id, payload, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/review")
    def legacy_request_review(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.request_review(request_id, payload, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/submit-review")
    def legacy_submit_review(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.submit_review(request_id, payload, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/approval")
    def legacy_request_approval(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.request_approval(request_id, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/approve")
    def legacy_approve(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            approval_id = str(payload.get("approval_id") or ncp004.get_execution(request_id, _ctx(claims, execution_id=request_id)).get("approval_id"))
            return ncp004.approve(approval_id, payload, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/reject")
    def legacy_reject(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            approval_id = str(payload.get("approval_id") or ncp004.get_execution(request_id, _ctx(claims, execution_id=request_id)).get("approval_id"))
            return ncp004.reject(approval_id, payload, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/changes")
    def legacy_changes(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            approval_id = str(payload.get("approval_id") or ncp004.get_execution(request_id, _ctx(claims, execution_id=request_id)).get("approval_id"))
            return ncp004.request_changes(approval_id, payload, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/execute")
    def legacy_execute(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.execute(request_id, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/cancel")
    def legacy_cancel(request_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp004.cancel(request_id, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/retry")
    def legacy_retry(request_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            execution = ncp004.get_execution(request_id, _ctx(claims, execution_id=request_id))
            execution["retry_count"] = int(execution.get("retry_count") or 0) + 1
            execution["status"] = "RETRYING"
            ncp004.repository.upsert("ai_execution", execution)
            return execution
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requests/{request_id}/verify")
    def legacy_verify(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.verify(request_id, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requests/{request_id}/evidence")
    def legacy_evidence(request_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp004.get_evidence(request_id, _ctx(claims, execution_id=request_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge")
    def knowledge() -> dict[str, Any]:
        return {"knowledge": []}

    @router.get("/conversations")
    def conversations(
        query: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        repository: str | None = None,
        branch: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        artifact_type: str | None = None,
        pinned: bool | None = None,
        archived: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        filters = {
            "query": query,
            "tenant_id": tenant_id or str(getattr(claims, "tenant_id", None) or claims.organization_id or ""),
            "workspace_id": workspace_id or claims.workspace_id,
            "project_id": project_id,
            "repository": repository,
            "branch": branch,
            "environment": environment,
            "status": status,
            "artifact_type": artifact_type,
            "pinned": pinned,
            "archived": archived,
            "limit": limit,
            "offset": offset,
        }
        return {"conversations": service.conversations(filters)}

    @router.post("/conversations")
    def create_conversation(
        payload: dict[str, Any],
        claims: JWTClaims = Depends(editor),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        data = dict(payload)
        tenant_id = str(claims.organization_id or claims.tenant_id or "").lower()
        data.setdefault("tenant_id", tenant_id)
        data.setdefault("organization_id", claims.organization_id or tenant_id)
        data.setdefault("workspace_id", claims.workspace_id or payload.get("workspace_id"))
        data.setdefault("actor_id", claims.sub)
        if idempotency_key:
            data["idempotency_key"] = idempotency_key
        try:
            return service.create_conversation(data)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/conversations/{conversation_id}")
    def get_conversation(conversation_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return service.get_conversation(conversation_id)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/conversations/{conversation_id}")
    def update_conversation(conversation_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.update_conversation(conversation_id, payload, actor=claims.sub)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/conversations/{conversation_id}/messages")
    def post_conversation_message(conversation_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            message = dict(payload)
            message.setdefault("actor", claims.sub)
            return service.add_conversation_message(conversation_id, message, actor=claims.sub)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/conversations/{conversation_id}/context")
    def get_conversation_context(conversation_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return service.conversation_context(conversation_id)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.put("/conversations/{conversation_id}/context")
    def update_conversation_context(conversation_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            context = dict(payload.get("context") or payload)
            return service.update_conversation(
                conversation_id,
                {
                    "context": context,
                    "context_sources": list(payload.get("context_sources") or []),
                    "workspace_id": payload.get("workspace_id"),
                    "project_id": payload.get("project_id"),
                    "repository": payload.get("repository"),
                    "branch": payload.get("branch"),
                    "environment": payload.get("environment"),
                    "correlation_id": payload.get("correlation_id"),
                },
                actor=claims.sub,
            )
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/conversations/{conversation_id}/artifacts")
    def get_conversation_artifacts(conversation_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"artifacts": service.conversation_artifacts(conversation_id)}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/conversations/{conversation_id}/traceability")
    def get_conversation_traceability(conversation_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return service.conversation_traceability(conversation_id)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/conversations/{conversation_id}/archive")
    def archive_conversation(conversation_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.archive_conversation(conversation_id, actor=claims.sub)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/conversations/{conversation_id}/restore")
    def restore_conversation(conversation_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.restore_conversation(conversation_id, actor=claims.sub)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/conversations/{conversation_id}")
    def delete_conversation(conversation_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return service.delete_conversation(conversation_id, actor=claims.sub)
        except Exception as exc:
            raise _map_error(exc) from exc

    return router


__all__ = ["build_novacodepro_ncp004_router"]
