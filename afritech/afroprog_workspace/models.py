"""Runtime-safe data contracts for AfriPro."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProjectFile:
    path: str
    language: str
    content: str

    def canonical_dict(self) -> dict[str, str]:
        return {"path": self.path, "language": self.language, "content": self.content}


@dataclass(frozen=True)
class ProjectWorkspace:
    project_id: str
    name: str
    stack: str
    description: str
    files: tuple[ProjectFile, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "stack": self.stack,
            "description": self.description,
            "files": [item.canonical_dict() for item in self.files],
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    mode: str

    def canonical_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content, "mode": self.mode}


@dataclass(frozen=True)
class ChatSession:
    session_id: str
    project_id: str
    open_file: str
    messages: tuple[ChatMessage, ...] = field(default_factory=tuple)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "open_file": self.open_file,
            "messages": [message.canonical_dict() for message in self.messages],
        }


def afroprog_seed_projects() -> tuple[ProjectWorkspace, ...]:
    return (
        ProjectWorkspace(
            project_id="project-poultry-suite",
            name="Poultry Operations Suite",
            stack="Django + DRF",
            description="Code generation workspace for poultry farm management and vaccine tracking.",
            files=(
                ProjectFile(
                    path="poultry/apps/farm/models.py",
                    language="python",
                    content="from django.db import models\n",
                ),
                ProjectFile(
                    path="poultry/apps/farm/serializers.py",
                    language="python",
                    content="from rest_framework import serializers\n",
                ),
            ),
            tags=("poultry", "django", "operations"),
        ),
        ProjectWorkspace(
            project_id="project-employee-rbac",
            name="Employee RBAC API",
            stack="Django + DRF",
            description="Starter workspace for employee management and permissions.",
            files=(
                ProjectFile(
                    path="employee_api/models.py",
                    language="python",
                    content="from django.db import models\n",
                ),
            ),
            tags=("rbac", "api", "django"),
        ),
    )


__all__ = [
    "ChatMessage",
    "ChatSession",
    "ProjectFile",
    "ProjectWorkspace",
    "afroprog_seed_projects",
]
