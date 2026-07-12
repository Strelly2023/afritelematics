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


def build_novacodepro_platform_router(platform: NovaCodeProPlatform | None = None) -> APIRouter:
    service = platform or _service()
    router = APIRouter(prefix="/v1/novacodepro", tags=["novacodepro"])
    observer = require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER", "DEVELOPER")
    editor = require_roles("OPERATOR", "ADMIN", "DEVELOPER")

    @router.get("/status")
    def status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return service.status()

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

    @router.get("/audit")
    def audit(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return service.audit()

    return router


__all__ = [
    "ArtifactCreateRequest",
    "CommandRequest",
    "CommentCreateRequest",
    "IntegrationConnectRequest",
    "KnowledgeLinkRequest",
    "NovaCodeProPlatform",
    "NovaCodeProRepository",
    "ProjectCreateRequest",
    "ReleaseCreateRequest",
    "ReleaseTransitionRequest",
    "ThreadCreateRequest",
    "WorkflowCreateRequest",
    "WorkflowTransitionRequest",
    "build_novacodepro_platform_router",
    "get_novacodepro_platform",
]
