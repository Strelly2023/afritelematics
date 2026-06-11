"""File explorer helpers for the AfriPro workspace."""

from __future__ import annotations

from ..projects.models import ProjectWorkspace


def build_project_explorer(project: ProjectWorkspace) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "path": item.path,
            "language": item.language,
        }
        for item in project.files
    )


__all__ = ["build_project_explorer"]
