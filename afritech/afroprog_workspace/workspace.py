"""Workspace views for the runtime-safe AfriPro package."""

from __future__ import annotations

from afritech.afroprog_workspace.models import afroprog_seed_projects
from afritech.afroprog_workspace.service import AfriProAIService, seed_session


def build_workspace_payload(
    *,
    prompt: str = "Create Django model for poultry farm",
    mode: str = "code",
    project_id: str = "project-poultry-suite",
) -> dict[str, object]:
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    project = projects[project_id]
    session = seed_session(project)
    response = AfriProAIService().generate_code(prompt, mode=mode, project=project, session=session)
    return {
        "dashboard_title": "AfriPro Dashboard",
        "workspace_mode": "codex_style",
        "project_explorer": [{"path": item.path, "language": item.language} for item in project.files],
        "chat_panel": {"prompt": prompt, "mode": mode, "response": response.canonical_dict()},
        "editor_panel": response.files[0].canonical_dict(),
        "session": session.canonical_dict(),
        "project": project.canonical_dict(),
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
        "governance_linked": True,
    }


def render_afroprog_dashboard_view() -> dict[str, object]:
    return {
        "view": "afroprog_dashboard",
        "payload": build_workspace_payload(),
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
        "validates_truth": False,
        "executes_runtime": False,
    }


def render_chat_view(
    *,
    prompt: str,
    mode: str = "code",
    project_id: str = "project-poultry-suite",
) -> dict[str, object]:
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    project = projects[project_id]
    session = seed_session(project)
    response = AfriProAIService().generate_code(prompt, mode=mode, project=project, session=session)
    return {
        "view": "afroprog_chat",
        "project": project.canonical_dict(),
        "session": session.canonical_dict(),
        "response": response.canonical_dict(),
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
    }


def render_projects_view() -> dict[str, object]:
    return {
        "view": "afroprog_projects",
        "projects": [project.canonical_dict() for project in afroprog_seed_projects()],
        "read_only": True,
        "creates_authority": False,
    }


__all__ = [
    "build_workspace_payload",
    "render_afroprog_dashboard_view",
    "render_chat_view",
    "render_projects_view",
]
