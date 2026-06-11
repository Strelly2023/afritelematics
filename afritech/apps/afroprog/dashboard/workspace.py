"""Workspace composition for the AfriPro dashboard."""

from __future__ import annotations

from ..chat.ai_service import AfriProAIService, seed_session
from ..editor.file_manager import build_project_explorer
from ..projects.models import afroprog_seed_projects


def build_workspace_payload(
    *,
    prompt: str = "Create Django model for poultry farm",
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
        "dashboard_title": "AfriPro Dashboard",
        "workspace_mode": "codex_style",
        "project_explorer": build_project_explorer(project),
        "chat_panel": {
            "prompt": prompt,
            "mode": mode,
            "response": response.canonical_dict(),
        },
        "editor_panel": response.files[0].canonical_dict(),
        "session": session.canonical_dict(),
        "project": project.canonical_dict(),
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
        "governance_linked": True,
    }


__all__ = ["build_workspace_payload"]
