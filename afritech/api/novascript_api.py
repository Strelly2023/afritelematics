"""FastAPI router for the NovaScript assistant product."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.afriprogramming.roles import Role
from afritech.novascript import (
    NovaScriptArchitectureRequest,
    NovaScriptDebugRequest,
    NovaScriptDocsRequest,
    NovaScriptExplainRequest,
    NovaScriptGenerateRequest,
    NovaScriptTestRequest,
    get_novascript_service,
)


def build_novascript_router() -> APIRouter:
    service = get_novascript_service()
    router = APIRouter(prefix="/v1/novascript", tags=["novascript"])

    @router.get("/status")
    def status(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.status(organization_id=claims.organization_id)

    @router.get("/catalog")
    def catalog(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.catalog(organization_id=claims.organization_id)

    @router.get("/context/{project_id}")
    def context(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.project_context(project_id, organization_id=claims.organization_id)

    @router.post("/generate")
    def generate(
        body: NovaScriptGenerateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.generate(
            prompt=body.prompt,
            project_id=body.project_id,
            language=body.language,
            mode=body.mode,
            organization_id=claims.organization_id,
        )

    @router.post("/explain")
    def explain(
        body: NovaScriptExplainRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.explain(
            code=body.code,
            context=body.context,
            organization_id=claims.organization_id,
        )

    @router.post("/debug")
    def debug(
        body: NovaScriptDebugRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.debug(
            code=body.code,
            error=body.error,
            context=body.context,
            organization_id=claims.organization_id,
        )

    @router.post("/architecture")
    def architecture(
        body: NovaScriptArchitectureRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.architecture(
            description=body.description,
            stack=body.stack,
            organization_id=claims.organization_id,
        )

    @router.post("/tests")
    def tests(
        body: NovaScriptTestRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.tests(
            target=body.target,
            framework=body.framework,
            organization_id=claims.organization_id,
        )

    @router.post("/docs")
    def docs(
        body: NovaScriptDocsRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.docs(
            topic=body.topic,
            audience=body.audience,
            format=body.format,
            metadata=body.metadata,
            organization_id=claims.organization_id,
        )

    @router.get("/repo/{project_id}/intelligence")
    def repository_intelligence(
        project_id: str,
        focus: str = "",
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.repository_intelligence(
            project_id=project_id,
            focus=focus,
            organization_id=claims.organization_id,
        )

    return router
