"""Runtime-safe AfriPro workspace package."""

from afritech.afroprog_workspace.service import AfriProAIService, seed_session
from afritech.afroprog_workspace.workspace import (
    build_workspace_payload,
    render_afroprog_dashboard_view,
    render_chat_view,
    render_projects_view,
)

__all__ = [
    "AfriProAIService",
    "build_workspace_payload",
    "render_afroprog_dashboard_view",
    "render_chat_view",
    "render_projects_view",
    "seed_session",
]
