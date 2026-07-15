from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro.platform import get_novacodepro_platform
from afritech.novacodepro.workflow_fabric import WorkflowFabricService


def _service() -> WorkflowFabricService:
    db_path = Path(os.environ.get("NOVACODEPRO_DB_PATH", "var/novacodepro-platform.sqlite3"))
    platform = get_novacodepro_platform(db_path)
    return WorkflowFabricService(platform)


class WorkflowCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    request: str
    tenant_id: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    domain: str | None = None
    region: str | None = None
    compliance: str | None = None
    surfaces: list[str] = Field(default_factory=list)
    category: str | None = None
    owner: str | None = None
    risk_level: str | None = None
    workflow_version: str | None = None
    environment: str | None = None
    required_approvals: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    evidence_profile: str | None = None
    retention_policy: str | None = None
    audit_profile: str | None = None
    rollback_strategy: str | None = None
    compensation_strategy: str | None = None
    human_tasks: list[str] = Field(default_factory=list)
    ai_tasks: list[str] = Field(default_factory=list)
    forms: list[str] = Field(default_factory=list)
    notifications: list[str] = Field(default_factory=list)
    documentation: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None


class WorkflowActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = None
    approval_reference: str | None = None
    reason: str | None = None
    environment: str | None = None
    version: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class PromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str


def build_novacodepro_workflow_fabric_router(service: WorkflowFabricService | None = None) -> APIRouter:
    fabric = service or _service()
    router = APIRouter(tags=["novacodepro-workflow-fabric"])

    readers = require_roles("OBSERVER", "OPERATOR", "ADMIN", "DEVELOPER")
    editors = require_roles("OPERATOR", "ADMIN", "DEVELOPER")
    operations = require_roles("OPERATOR", "ADMIN")

    @router.get("/v1/workflow-fabric")
    def workflow_fabric_summary(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return fabric.summary()

    @router.get("/v1/workflow-fabric/connectors")
    def workflow_fabric_connectors(claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        return fabric.connectors()

    @router.get("/v1/workflow-fabric/marketplace")
    def workflow_fabric_marketplace(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return fabric.marketplace()

    @router.get("/v1/workflows")
    def workflows(claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        return fabric.workflows()

    @router.get("/v1/workflows/{workflow_id}")
    def workflow(workflow_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return fabric.workflow_view(workflow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.post("/v1/workflows")
    def create_workflow(payload: WorkflowCreateRequest, claims: JWTClaims = Depends(editors)) -> dict[str, Any]:
        data = payload.model_dump(exclude_none=True)
        data.setdefault("tenant_id", claims.organization_id or claims.tenant_id or "novatech")
        return fabric.create_workflow(data, actor=claims.sub)

    @router.post("/v1/workflows/generate")
    def generate_workflow(payload: PromptRequest, claims: JWTClaims = Depends(editors)) -> dict[str, Any]:
        return fabric.generate_from_prompt(payload.prompt, actor=claims.sub)

    @router.post("/v1/workflows/{workflow_id}/validate")
    def validate_workflow(workflow_id: str, claims: JWTClaims = Depends(editors)) -> dict[str, Any]:
        try:
            return fabric.validate(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/compile")
    def compile_workflow(workflow_id: str, claims: JWTClaims = Depends(editors)) -> dict[str, Any]:
        try:
            return fabric.compile(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/review")
    def review_workflow(workflow_id: str, payload: WorkflowActionRequest | None = None, claims: JWTClaims = Depends(editors)) -> dict[str, Any]:
        try:
            return fabric.review(workflow_id, (payload or {}).model_dump(exclude_none=True) if payload else None, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.post("/v1/workflows/{workflow_id}/approve")
    def approve_workflow(workflow_id: str, payload: WorkflowActionRequest | None = None, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.approve(workflow_id, (payload or {}).model_dump(exclude_none=True) if payload else None, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.post("/v1/workflows/{workflow_id}/deploy")
    def deploy_workflow(workflow_id: str, payload: WorkflowActionRequest | None = None, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.deploy(workflow_id, (payload or {}).model_dump(exclude_none=True) if payload else None, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/execute")
    def execute_workflow(workflow_id: str, payload: WorkflowActionRequest | None = None, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.execute(workflow_id, (payload or {}).model_dump(exclude_none=True) if payload else None, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/pause")
    def pause_workflow(workflow_id: str, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.pause(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/resume")
    def resume_workflow(workflow_id: str, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.resume(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/complete")
    def complete_workflow(workflow_id: str, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.complete(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/verify")
    def verify_workflow(workflow_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return fabric.verify(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/workflows/{workflow_id}/evidence")
    def emit_workflow_evidence(workflow_id: str, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.emit_evidence(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.post("/v1/workflows/{workflow_id}/archive")
    def archive_workflow(workflow_id: str, claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        try:
            return fabric.archive(workflow_id, actor=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/v1/workflows/{workflow_id}/views")
    def workflow_views(workflow_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return fabric.views(workflow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.get("/v1/workflows/{workflow_id}/timeline")
    def workflow_timeline(workflow_id: str, claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        try:
            return fabric.timeline(workflow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.get("/v1/workflows/{workflow_id}/replay")
    def workflow_replay(workflow_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return fabric.replay(workflow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.get("/v1/workflows/{workflow_id}/evidence")
    def workflow_evidence(workflow_id: str, claims: JWTClaims = Depends(readers)) -> list[dict[str, Any]]:
        try:
            return fabric.evidence(workflow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    @router.get("/v1/workflows/{workflow_id}/analytics")
    def workflow_analytics(workflow_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return fabric.analytics(workflow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="workflow_not_found") from exc

    return router


__all__ = ["build_novacodepro_workflow_fabric_router"]
