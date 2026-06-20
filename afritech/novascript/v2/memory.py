from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class MemoryRecord:
    memory_id: str
    organization_id: str
    project_id: str
    intent: str
    prompt: str
    summary: dict[str, Any]
    receipts: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WorkspaceMemoryStore:
    def __init__(self, max_items_per_project: int = 25) -> None:
        self._max_items = max_items_per_project
        self._records: dict[tuple[str, str], deque[MemoryRecord]] = defaultdict(
            lambda: deque(maxlen=max_items_per_project)
        )

    def append(
        self,
        *,
        organization_id: str,
        project_id: str,
        intent: str,
        prompt: str,
        summary: dict[str, Any],
        receipts: list[dict[str, Any]] | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            memory_id=f"mem-{uuid4().hex[:12]}",
            organization_id=organization_id,
            project_id=project_id,
            intent=intent,
            prompt=prompt,
            summary=summary,
            receipts=receipts or [],
        )
        self._records[(organization_id, project_id)].append(record)
        return record

    def recent(self, *, organization_id: str, project_id: str) -> list[dict[str, Any]]:
        return [record.__dict__ for record in self._records[(organization_id, project_id)]]

    def snapshot(self, *, organization_id: str, project_id: str) -> dict[str, Any]:
        recent = self.recent(organization_id=organization_id, project_id=project_id)
        return {
            "organization_id": organization_id,
            "project_id": project_id,
            "memory_count": len(recent),
            "recent": recent[-5:],
        }


_DEFAULT_WORKSPACE_MEMORY = WorkspaceMemoryStore()


def get_workspace_memory_store() -> WorkspaceMemoryStore:
    return _DEFAULT_WORKSPACE_MEMORY
