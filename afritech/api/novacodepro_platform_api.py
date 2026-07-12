"""Distributed NovaCodePro enterprise platform API surfaces."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro import NovaCodeProPlatform, get_novacodepro_platform


def _service() -> NovaCodeProPlatform:
    db_path = Path(os.environ.get("NOVACODEPRO_DB_PATH", "var/novacodepro-platform.sqlite3"))
    return get_novacodepro_platform(db_path)


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


class MarketplaceInstallRequest(BaseModel):
    package_id: str
    tenant_id: str | None = None
    region: str = "Australia"
    version: str = "2027.1.0"


def build_novacodepro_platform_router(platform: NovaCodeProPlatform | None = None) -> APIRouter:
    service = platform or _service()
    router = APIRouter(prefix="/v1/novacodepro", tags=["novacodepro"])
    observer = require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER", "DEVELOPER")
    editor = require_roles("OPERATOR", "ADMIN", "DEVELOPER")

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
        return service.create_solution(payload.model_dump())

    @router.get("/agents/executions")
    def agent_executions(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.agent_executions()

    @router.get("/agents/executions/{execution_id}")
    def agent_execution(execution_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_agent_execution(execution_id)
        if record is None:
            raise HTTPException(status_code=404, detail="agent_execution_not_found")
        return record

    @router.post("/agents/executions")
    def create_agent_execution(payload: AgentExecutionCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_agent_execution(payload.model_dump())

    @router.post("/agents/executions/{execution_id}/cancel")
    def cancel_agent_execution(execution_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        record = service.get_agent_execution(execution_id)
        if record is None:
            raise HTTPException(status_code=404, detail="agent_execution_not_found")
        record["status"] = "cancelled"
        service.repository.upsert("agent_execution", record)
        return record

    @router.get("/approvals")
    def approvals(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.approvals()

    @router.post("/approvals")
    def create_approval(payload: ApprovalCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_approval(payload.model_dump())

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
        return service.create_deployment(payload.model_dump())

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

    @router.get("/digital-twins/{twin_id}")
    def digital_twin(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        record = service.get_or_create_digital_twin(twin_id)
        return record

    @router.get("/digital-twins/{twin_id}/topology")
    def digital_twin_topology(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_topology(twin_id)

    @router.get("/digital-twins/{twin_id}/health")
    def digital_twin_health(twin_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.digital_twin_health(twin_id)

    @router.get("/tenants")
    def tenants(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.tenants()

    @router.get("/projects")
    def projects(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.projects()

    @router.post("/projects")
    def create_project(payload: ProjectCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_project(payload.model_dump())

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
        return service.create_workflow(payload.model_dump())

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
        return service.create_artifact(payload.model_dump())

    @router.get("/knowledge-graph")
    def knowledge_graph(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"nodes": service.knowledge_graph()}

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
        return service.create_thread(payload.model_dump())

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
        package = {
            "id": payload.package_id,
            "tenant_id": payload.tenant_id or service.tenants()[0]["id"],
            "region": payload.region,
            "version": payload.version,
            "installed_at": service.audit(limit=1)[0]["at"] if service.audit(limit=1) else None,
            "status": "installed",
        }
        service.repository.upsert("marketplace_item", {
            "id": payload.package_id,
            "name": payload.package_id.replace("-", " ").title(),
            "category": "solution",
            "version": payload.version,
            "installed": True,
            "tenant_id": package["tenant_id"],
            "region": payload.region,
            "created_at": package["installed_at"] or "",
            "updated_at": package["installed_at"] or "",
        })
        return package

    @router.post("/marketplace/uninstall")
    def uninstall_marketplace_package(
        payload: MarketplaceInstallRequest,
        claims: JWTClaims = Depends(editor),
    ) -> dict[str, Any]:
        item = service.repository.get("marketplace_item", payload.package_id)
        if item is None:
            raise HTTPException(status_code=404, detail="marketplace_package_not_found")
        item["installed"] = False
        item["updated_at"] = service.audit(limit=1)[0]["at"] if service.audit(limit=1) else item.get("updated_at")
        service.repository.upsert("marketplace_item", item)
        return {"id": payload.package_id, "status": "uninstalled"}

    @router.get("/releases")
    def releases(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.releases()

    @router.post("/releases")
    def create_release(payload: ReleaseCreateRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.create_release(payload.model_dump())

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

    @router.post("/commands")
    def command(payload: CommandRequest, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        return service.run_command(payload.command, payload.context)

    @router.post("/knowledge/query")
    def query_knowledge(payload: KnowledgeQueryRequest, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        query = payload.query.lower()
        matches = [
            node
            for node in service.knowledge_graph()
            if query in node.get("label", "").lower() or query in node.get("id", "").lower()
        ]
        return {"query": payload.query, "matches": matches, "match_count": len(matches)}

    @router.get("/events")
    def events(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.events()

    @router.get("/audit")
    def audit(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.audit()

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
