"""Runtime-safe AfriPro AI service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.afriprogramming.integration import build_afriprog_to_afriprogramming_view
from afritech.afroprog_workspace.models import (
    ChatMessage,
    ChatSession,
    ProjectWorkspace,
)
from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal
from afritech.extensions.afriprog.design_generator.design_orchestrator import DesignOrchestrator


@dataclass(frozen=True)
class GeneratedWorkspaceFile:
    path: str
    language: str
    content: str

    def canonical_dict(self) -> dict[str, str]:
        return {"path": self.path, "language": self.language, "content": self.content}


@dataclass(frozen=True)
class ChatWorkspaceResponse:
    prompt: str
    mode: str
    explanation: str
    files: tuple[GeneratedWorkspaceFile, ...]
    governance_view: dict[str, Any]
    execution_preview: dict[str, object]
    evidence: dict[str, object]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "prompt": self.prompt,
            "mode": self.mode,
            "explanation": self.explanation,
            "files": [item.canonical_dict() for item in self.files],
            "governance_view": self.governance_view,
            "execution_preview": self.execution_preview,
            "evidence": self.evidence,
        }


def _files(specs: tuple[tuple[str, str, str], ...]) -> tuple[GeneratedWorkspaceFile, ...]:
    return tuple(GeneratedWorkspaceFile(path=a, language=b, content=c) for a, b, c in specs)


def _poultry_bundle() -> tuple[GeneratedWorkspaceFile, ...]:
    return _files(
        (
            ("poultry/apps/farm/models.py", "python", "from django.db import models\n\n\nclass PoultryHouse(models.Model):\n    name = models.CharField(max_length=64, unique=True)\n    capacity = models.PositiveIntegerField()\n\n\nclass Flock(models.Model):\n    code = models.CharField(max_length=32, unique=True)\n    bird_count = models.PositiveIntegerField()\n"),
            ("poultry/apps/farm/serializers.py", "python", "from rest_framework import serializers\n"),
            ("poultry/apps/farm/views.py", "python", "permission_classes = [HasFarmOperationsAccess]\n"),
            ("poultry/apps/farm/urls.py", "python", "urlpatterns = router.urls\n"),
        )
    )


def _employee_bundle() -> tuple[GeneratedWorkspaceFile, ...]:
    return _files(
        (
            ("employee_api/models.py", "python", "from django.db import models\n\n\nclass EmployeeProfile(models.Model):\n    department = models.CharField(max_length=64)\n"),
            ("employee_api/views.py", "python", "from rest_framework.viewsets import ModelViewSet\n"),
        )
    )


class AfriProAIService:
    def generate_code(
        self,
        prompt: str,
        *,
        mode: str,
        project: ProjectWorkspace,
        session: ChatSession,
    ) -> ChatWorkspaceResponse:
        lowered = prompt.lower()
        design = DesignOrchestrator().generate("Build a Poultry Management System")
        files = _poultry_bundle() if any(word in lowered for word in ("poultry", "farm", "vaccin")) else _employee_bundle()
        explanation = (
            "Generated a Django backend starter for the poultry system." if files[0].path.startswith("poultry/")
            else "Generated a Django employee RBAC starter."
        )
        proposal = generate_context_aware_proposal(
            intent=prompt,
            affected_files=tuple(item.path for item in files),
        )
        return ChatWorkspaceResponse(
            prompt=prompt,
            mode=mode,
            explanation=explanation,
            files=files,
            governance_view=build_afriprog_to_afriprogramming_view(proposal),
            execution_preview={
                "mode": "preview_only",
                "sandboxed": True,
                "mutation_allowed": False,
                "next_step": "send_to_governance",
            },
            evidence={
                "design_domain": design.domain.domain,
                "design_evidence_id": design.evidence.evidence_id,
                "design_review_admitted": design.review.admitted,
                "session_id": session.session_id,
                "project_id": project.project_id,
            },
        )


def seed_session(project: ProjectWorkspace) -> ChatSession:
    return ChatSession(
        session_id=f"session-{project.project_id}",
        project_id=project.project_id,
        open_file=project.files[0].path,
        messages=(
            ChatMessage(
                role="system",
                content="AfriPro is proposal-only and routes through AfriProgramming governance.",
                mode="analysis",
            ),
        ),
    )


__all__ = [
    "AfriProAIService",
    "ChatWorkspaceResponse",
    "GeneratedWorkspaceFile",
    "seed_session",
]
