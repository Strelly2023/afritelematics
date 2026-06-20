from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KnowledgeEntry:
    name: str
    category: str
    description: str
    recommended_files: tuple[str, ...]
    notes: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "recommended_files": list(self.recommended_files),
            "notes": list(self.notes),
        }


class ArchitectureKnowledgeBase:
    def __init__(self) -> None:
        self._entries = {
            "fastapi_service": KnowledgeEntry(
                name="FastAPI service",
                category="backend",
                description="Build explicit routers, schemas, and dependency-injected service layers.",
                recommended_files=("app/main.py", "app/api/router.py", "app/schemas.py"),
                notes=("Keep routes thin", "Push logic into services"),
            ),
            "django_service": KnowledgeEntry(
                name="Django service",
                category="backend",
                description="Model views and serializers explicitly and keep business logic out of views.",
                recommended_files=("apps/api/views.py", "apps/api/serializers.py"),
                notes=("Use DRF", "Separate admin from public API"),
            ),
            "react_frontend": KnowledgeEntry(
                name="React frontend",
                category="frontend",
                description="Prefer component boundaries, data hooks, and typed service adapters.",
                recommended_files=("src/App.tsx", "src/components/", "src/services/api.ts"),
                notes=("Keep presentation and transport separate", "Type props and responses"),
            ),
            "tests": KnowledgeEntry(
                name="Testing strategy",
                category="quality",
                description="Generate unit, API, and regression tests with clear setup and assertions.",
                recommended_files=("tests/test_generated.py",),
                notes=("Assert stable contracts", "Prefer deterministic fixtures"),
            ),
            "deployment": KnowledgeEntry(
                name="Deployment automation",
                category="delivery",
                description="Build Docker, CI, and deployment scripts as separate artifacts.",
                recommended_files=("Dockerfile", ".github/workflows/ci.yml"),
                notes=("Keep deploy scripts reproducible", "Avoid runtime side effects"),
            ),
            "governance": KnowledgeEntry(
                name="Governance integration",
                category="trust",
                description="Pair generated code with verification, policy, and governance receipts.",
                recommended_files=("gov/receipt.json",),
                notes=("Never claim runtime authority", "Record evidence before release"),
            ),
        }

    def list(self) -> list[dict[str, Any]]:
        return [entry.canonical_dict() for entry in self._entries.values()]

    def match(self, text: str) -> list[dict[str, Any]]:
        lowered = text.lower()
        matches: list[KnowledgeEntry] = []
        for entry in self._entries.values():
            if any(token in lowered for token in entry.name.lower().split()) or entry.category in lowered:
                matches.append(entry)
        if not matches:
            matches = [self._entries["fastapi_service"], self._entries["tests"], self._entries["governance"]]
        return [entry.canonical_dict() for entry in matches]


_DEFAULT_KB = ArchitectureKnowledgeBase()


def get_architecture_knowledge_base() -> ArchitectureKnowledgeBase:
    return _DEFAULT_KB
