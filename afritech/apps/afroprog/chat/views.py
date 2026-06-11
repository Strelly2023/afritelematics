"""Read-only Django-style chat views for AfriPro."""

from __future__ import annotations

from .ai_service import AfriProAIService, seed_session
from ..projects.models import afroprog_seed_projects


def render_chat_view(
    *,
    prompt: str,
    mode: str = "code",
    project_id: str = "project-poultry-suite",
) -> dict[str, object]:
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    project = projects[project_id]
    session = seed_session(project)
    response = AfriProAIService().generate_code(
        prompt,
        mode=mode,
        project=project,
        session=session,
    )
    return {
        "view": "afroprog_chat",
        "project": project.canonical_dict(),
        "session": session.canonical_dict(),
        "response": response.canonical_dict(),
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
    }


__all__ = ["render_chat_view"]
