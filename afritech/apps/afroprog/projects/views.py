"""Project listing views for AfriPro."""

from __future__ import annotations

from .models import afroprog_seed_projects


def render_projects_view() -> dict[str, object]:
    return {
        "view": "afroprog_projects",
        "projects": [project.canonical_dict() for project in afroprog_seed_projects()],
        "read_only": True,
        "creates_authority": False,
    }


__all__ = ["render_projects_view"]
