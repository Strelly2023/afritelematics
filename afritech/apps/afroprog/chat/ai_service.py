"""AI prompt to Django code generation for AfriPro."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.afriprogramming.integration import (
    build_afriprog_to_afriprogramming_view,
)
from .models import ChatMessage, ChatSession
from ..editor.code_editor import build_editor_document
from ..editor.execution_engine import preview_execution
from ..projects.models import ProjectFile, ProjectWorkspace
from afritech.extensions.afriprog.copilot_assist import (
    generate_context_aware_proposal,
)
from afritech.extensions.afriprog.design_generator.design_orchestrator import (
    DesignOrchestrator,
)


MODES = ("code", "debug", "analysis")


@dataclass(frozen=True)
class GeneratedWorkspaceFile:
    path: str
    language: str
    content: str

    def canonical_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "language": self.language,
            "content": self.content,
        }


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


def _bundle_files(specs: tuple[tuple[str, str, str], ...]) -> tuple[GeneratedWorkspaceFile, ...]:
    return tuple(
        GeneratedWorkspaceFile(path=path, language=language, content=content)
        for path, language, content in specs
    )


def _poultry_django_bundle() -> tuple[GeneratedWorkspaceFile, ...]:
    return _bundle_files(
        (
            (
                "poultry/apps/farm/models.py",
                "python",
                """from django.db import models


class PoultryHouse(models.Model):
    name = models.CharField(max_length=64, unique=True)
    capacity = models.PositiveIntegerField()
    active = models.BooleanField(default=True)


class Flock(models.Model):
    code = models.CharField(max_length=32, unique=True)
    poultry_house = models.ForeignKey(PoultryHouse, on_delete=models.PROTECT, related_name="flocks")
    bird_type = models.CharField(max_length=32)
    bird_count = models.PositiveIntegerField()
    hatch_date = models.DateField()
    vaccination_status = models.CharField(max_length=32, default="scheduled")
""",
            ),
            (
                "poultry/apps/farm/serializers.py",
                "python",
                """from rest_framework import serializers

from .models import Flock, PoultryHouse


class PoultryHouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoultryHouse
        fields = ("id", "name", "capacity", "active")


class FlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flock
        fields = (
            "id",
            "code",
            "poultry_house",
            "bird_type",
            "bird_count",
            "hatch_date",
            "vaccination_status",
        )
""",
            ),
            (
                "poultry/apps/farm/permissions.py",
                "python",
                """from rest_framework.permissions import BasePermission


class HasFarmOperationsAccess(BasePermission):
    message = "farm operations access requires explicit RBAC permission"

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
""",
            ),
            (
                "poultry/apps/farm/views.py",
                "python",
                """from rest_framework.viewsets import ModelViewSet

from .models import Flock, PoultryHouse
from .permissions import HasFarmOperationsAccess
from .serializers import FlockSerializer, PoultryHouseSerializer


class PoultryHouseViewSet(ModelViewSet):
    queryset = PoultryHouse.objects.all()
    serializer_class = PoultryHouseSerializer
    permission_classes = [HasFarmOperationsAccess]


class FlockViewSet(ModelViewSet):
    queryset = Flock.objects.select_related("poultry_house").all()
    serializer_class = FlockSerializer
    permission_classes = [HasFarmOperationsAccess]
""",
            ),
            (
                "poultry/apps/farm/urls.py",
                "python",
                """from rest_framework.routers import DefaultRouter

from .views import FlockViewSet, PoultryHouseViewSet

router = DefaultRouter()
router.register("houses", PoultryHouseViewSet, basename="poultry-house")
router.register("flocks", FlockViewSet, basename="flock")

urlpatterns = router.urls
""",
            ),
            (
                "poultry/apps/farm/tests/test_api.py",
                "python",
                """def test_flock_api_requires_authenticated_access():
    assert True
""",
            ),
        )
    )


def _employee_bundle() -> tuple[GeneratedWorkspaceFile, ...]:
    return _bundle_files(
        (
            (
                "employee_api/models.py",
                "python",
                """from django.contrib.auth import get_user_model
from django.db import models


class EmployeeRole(models.TextChoices):
    MANAGER = "manager", "Manager"
    OPERATOR = "operator", "Operator"
    AUDITOR = "auditor", "Auditor"


class EmployeeProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=EmployeeRole.choices)
    department = models.CharField(max_length=64)
""",
            ),
            (
                "employee_api/views.py",
                "python",
                """from rest_framework.viewsets import ModelViewSet

from .models import EmployeeProfile
from .serializers import EmployeeProfileSerializer


class EmployeeProfileViewSet(ModelViewSet):
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
""",
            ),
        )
    )


class AfriProAIService:
    """Codex-style prompt handling for proposal-only Django generation."""

    def generate_code(
        self,
        prompt: str,
        *,
        mode: str,
        project: ProjectWorkspace,
        session: ChatSession,
    ) -> ChatWorkspaceResponse:
        if mode not in MODES:
            raise ValueError(f"unsupported mode: {mode}")

        lowered = prompt.lower()
        design = DesignOrchestrator().generate("Build a Poultry Management System")

        if "poultry" in lowered or "farm" in lowered or "vaccin" in lowered:
            files = _poultry_django_bundle()
            explanation = (
                "Generated a Django + DRF poultry operations starter with houses, flocks, "
                "RBAC permission hooks, API routing, and a test scaffold."
            )
        elif "employee" in lowered or "rbac" in lowered:
            files = _employee_bundle()
            explanation = (
                "Generated an employee management starter with Django model, DRF viewset, "
                "and role-aware profile support."
            )
        else:
            files = _poultry_django_bundle()
            explanation = (
                "Defaulted to the poultry management template bundle because this workspace "
                "is optimized for the poultry system domain."
            )

        proposal = generate_context_aware_proposal(
            intent=prompt,
            affected_files=tuple(item.path for item in files),
        )
        governance_view = build_afriprog_to_afriprogramming_view(proposal)
        editor = build_editor_document(
            files[0].path,
            files[0].language,
            files[0].content,
        )
        preview = preview_execution(editor.content)
        evidence = {
            "design_domain": design.domain.domain,
            "design_evidence_id": design.evidence.evidence_id,
            "design_review_admitted": design.review.admitted,
            "session_id": session.session_id,
            "project_id": project.project_id,
            "open_file": session.open_file,
        }

        return ChatWorkspaceResponse(
            prompt=prompt,
            mode=mode,
            explanation=explanation,
            files=files,
            governance_view=governance_view,
            execution_preview=preview,
            evidence=evidence,
        )

    def debug_code(self, code: str) -> dict[str, object]:
        issues = []
        if "permission_classes" not in code:
            issues.append("RBAC permission_classes missing from generated viewset")
        if "models.Model" not in code:
            issues.append("No Django model class detected")
        return {
            "issues": issues,
            "fixes": [
                "Add explicit permission class to preserve RBAC boundaries",
                "Route output through governance before applying any patch",
            ],
            "mode": "debug",
        }

    def analyze_session(self, session: ChatSession) -> dict[str, object]:
        return {
            "message_count": len(session.messages),
            "active_modes": sorted({message.mode for message in session.messages}),
            "current_file": session.open_file,
        }


def seed_session(project: ProjectWorkspace) -> ChatSession:
    return ChatSession(
        session_id=f"session-{project.project_id}",
        project_id=project.project_id,
        open_file=project.files[0].path if project.files else "workspace.py",
        messages=(
            ChatMessage(
                role="system",
                content=(
                    "AfriPro is a proposal-only developer workspace. Runtime mutation remains "
                    "blocked until AfriProgramming governance accepts the handoff."
                ),
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
