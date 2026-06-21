from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


@dataclass
class MemoryRecord:
    memory_id: str
    sequence: int
    organization_id: str
    project_id: str
    intent: str
    prompt: str
    summary: dict[str, Any]
    receipts: list[dict[str, Any]] = field(default_factory=list)


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
        key = (organization_id, project_id)
        sequence = len(self._records[key]) + 1
        memory_id = "mem-" + sha256(
            f"{organization_id}:{project_id}:{sequence}:{intent}:{prompt}".encode("utf-8")
        ).hexdigest()[:12]
        record = MemoryRecord(
            memory_id=memory_id,
            sequence=sequence,
            organization_id=organization_id,
            project_id=project_id,
            intent=intent,
            prompt=prompt,
            summary=summary,
            receipts=receipts or [],
        )
        self._records[key].append(record)
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
            "evolution": _memory_evolution(recent),
            "long_term_organizational_memory": self.organization_summary(organization_id=organization_id),
        }

    def organization_summary(self, *, organization_id: str) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for (org_id, _project_id), project_records in self._records.items():
            if org_id == organization_id:
                records.extend(record.__dict__ for record in project_records)
        evolution = _memory_evolution(sorted(records, key=lambda item: (item["project_id"], item["sequence"])))
        return {
            "mode": "long_term_organizational_memory",
            "organization_id": organization_id,
            "project_count": len({record["project_id"] for record in records}),
            "memory_count": len(records),
            "evolution": evolution,
            "institutional_memory": _institutional_memory(records),
        }


def _memory_evolution(records: list[dict[str, Any]]) -> dict[str, Any]:
    intent_counts: dict[str, int] = {}
    trust_scores: list[int] = []
    for record in records:
        intent = str(record.get("intent", "unknown"))
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        summary = record.get("summary", {})
        if isinstance(summary, dict) and "trust_score" in summary:
            trust_scores.append(int(summary.get("trust_score", 0)))
    latest = trust_scores[-1] if trust_scores else None
    previous = trust_scores[-2] if len(trust_scores) > 1 else latest
    trend = "stable"
    if latest is not None and previous is not None:
        if latest > previous:
            trend = "improving"
        elif latest < previous:
            trend = "declining"
    return {
        "mode": "persistent_evolving_memory",
        "intent_counts": dict(sorted(intent_counts.items())),
        "trust_scores": trust_scores[-10:],
        "latest_trust_score": latest,
        "trend": trend,
    }


def _institutional_memory(records: list[dict[str, Any]]) -> dict[str, Any]:
    trust_scores = [
        int(record.get("summary", {}).get("trust_score", 0))
        for record in records
        if isinstance(record.get("summary"), dict) and "trust_score" in record.get("summary", {})
    ]
    risk_scores = [
        int(record.get("summary", {}).get("risk_score", 0))
        for record in records
        if isinstance(record.get("summary"), dict) and "risk_score" in record.get("summary", {})
    ]
    architecture_versions = [
        int(record.get("summary", {}).get("architecture_version", 0))
        for record in records
        if isinstance(record.get("summary"), dict) and "architecture_version" in record.get("summary", {})
    ]
    return {
        "mode": "institutional_memory",
        "engineering_memory": {"record_count": len(records)},
        "architecture_memory": {"latest_version": max(architecture_versions) if architecture_versions else None},
        "decision_memory": {"decision_count": len(records)},
        "trust_memory": {
            "latest_trust_score": trust_scores[-1] if trust_scores else None,
            "average_trust_score": round(sum(trust_scores) / len(trust_scores), 2) if trust_scores else None,
        },
        "risk_memory": {
            "latest_risk_score": risk_scores[-1] if risk_scores else None,
            "average_risk_score": round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else None,
        },
    }


_DEFAULT_WORKSPACE_MEMORY = WorkspaceMemoryStore()


def get_workspace_memory_store() -> WorkspaceMemoryStore:
    return _DEFAULT_WORKSPACE_MEMORY
