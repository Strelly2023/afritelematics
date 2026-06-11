"""FastAPI adapter for AfriPro dashboard and chat workspace."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.afroprog_workspace.workspace import (
    build_workspace_payload,
    render_afroprog_dashboard_view,
    render_chat_view,
    render_projects_view,
)


def build_afroprog_workspace_router() -> APIRouter:
    router = APIRouter(tags=["afroprog-workspace"])

    @router.get("/v1/afroprog/dashboard")
    def afroprog_dashboard(
        _: object = Depends(require_roles("OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, object]:
        return render_afroprog_dashboard_view()

    @router.post("/v1/afroprog/chat/prompts")
    def afroprog_chat_prompt(
        prompt: str,
        mode: str = "code",
        project_id: str = "project-poultry-suite",
        _: object = Depends(require_roles("OPERATOR", "DEVELOPER")),
    ) -> dict[str, object]:
        return render_chat_view(prompt=prompt, mode=mode, project_id=project_id)

    @router.get("/v1/afroprog/projects")
    def afroprog_projects(
        _: object = Depends(require_roles("OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, object]:
        return render_projects_view()

    @router.get("/v1/afroprog/workspace")
    def afroprog_workspace(
        prompt: str = "Create Django model for poultry farm",
        mode: str = "code",
        project_id: str = "project-poultry-suite",
        _: object = Depends(require_roles("OPERATOR", "DEVELOPER")),
    ) -> dict[str, object]:
        return build_workspace_payload(prompt=prompt, mode=mode, project_id=project_id)

    return router


__all__ = ["build_afroprog_workspace_router"]
