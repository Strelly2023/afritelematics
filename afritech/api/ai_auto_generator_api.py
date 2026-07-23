from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro import NovaCodeProPlatform
from afritech.novacodepro.ai_auto_generator import AIAutoGeneratorContext, AIAutoGeneratorError, NovaCodeProAIAutoGeneratorService


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


def build_ai_auto_generator_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ai-auto-generator", tags=["ai-auto-generator"])
    generator = NovaCodeProAIAutoGeneratorService(service.repository)
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
        "AUDIT_TEAM",
        "RISK_MANAGEMENT",
        "PRIVACY_COMPLIANCE",
        "DATA_ARCHITECT",
        "DATA_ENGINEER",
        "DATABASE_ENGINEER",
        "AI_ML_ENGINEER",
        "DATA_SCIENTIST",
        "LEGAL",
    )
    approver = require_roles(
        "OPERATOR",
        "ADMIN",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "SECURITY_ENGINEER",
        "COMPLIANCE_TEAM",
        "COMPLIANCE_OFFICER",
        "AUDIT_TEAM",
        "RISK_MANAGEMENT",
        "PRIVACY_COMPLIANCE",
        "EXTERNAL_REGULATOR",
    )

    def _ctx(
        claims: JWTClaims,
        *,
        execution_id: str | None = None,
        project_id: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AIAutoGeneratorContext:
        workspace_id = claims.workspace_id or ""
        permissions = tuple(sorted({str(permission) for permission in claims.permissions}))
        if not workspace_id:
            raise HTTPException(status_code=409, detail={"code": "workspace_required", "message": "Workspace context is required."})
        return AIAutoGeneratorContext(
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
            correlation_id=correlation_id or f"ai-auto-generator-{claims.sid or claims.sub}-{execution_id or request_id or workspace_id}",
            causation_id=claims.sid or None,
        )

    def _map_error(error: Exception) -> HTTPException:
        if isinstance(error, AIAutoGeneratorError):
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
            return HTTPException(status_code=403, detail={"code": "forbidden", "message": str(error)})
        if isinstance(error, KeyError):
            code = str(error).strip("'")
            return HTTPException(status_code=404, detail={"code": code, "message": code.replace("_", " ").capitalize()})
        return HTTPException(status_code=500, detail={"code": "service_unavailable", "message": "Service unavailable."})

    @router.get("/executions")
    def list_executions(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"executions": generator.list_executions(_ctx(claims))}

    @router.post("/executions")
    def create_execution(
        payload: dict[str, Any],
        claims: JWTClaims = Depends(editor),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            data = dict(payload)
            if idempotency_key:
                data["idempotency_key"] = idempotency_key
            execution = generator.create_execution(
                data,
                _ctx(
                    claims,
                    project_id=str(payload.get("project_id") or ""),
                    request_id=str(payload.get("request_id") or ""),
                    correlation_id=str(payload.get("correlation_id") or "") or None,
                ),
            )
            return execution
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/executions/{execution_id}")
    def get_execution(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return generator.get_execution(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/approvals")
    def approve_execution(execution_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return generator.approve_stage(execution_id, payload, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/retry")
    def retry_execution(execution_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return generator.retry(execution_id, payload, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/pause")
    def pause_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return generator.pause(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/resume")
    def resume_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return generator.resume(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/cancel")
    def cancel_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return generator.cancel(execution_id, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/executions/{execution_id}/artifacts/{artifact_id}/regenerate")
    def regenerate_artifact(execution_id: str, artifact_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return generator.regenerate_artifact(execution_id, artifact_id, payload, _ctx(claims, execution_id=execution_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/projects/{project_id}/traceability")
    def project_traceability(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return generator.traceability(project_id, _ctx(claims, project_id=project_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/projects/{project_id}/evidence")
    def project_evidence(project_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return generator.evidence(project_id, _ctx(claims, project_id=project_id))
        except Exception as exc:
            raise _map_error(exc) from exc

    return router


__all__ = ["build_ai_auto_generator_router"]
