"""Evidence records for integration verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(frozen=True, slots=True)
class IntegrationEvidence:
    evidence_id: str
    product_code: str
    provider_id: str
    operation: str
    status: str
    checksum: str
    payload: dict[str, Any] = field(default_factory=dict)
    recorded_at: float = field(default_factory=time)


@dataclass(slots=True)
class IntegrationEvidenceStore:
    records: list[IntegrationEvidence] = field(default_factory=list)

    def record(self, evidence: IntegrationEvidence) -> IntegrationEvidence:
        self.records.append(evidence)
        return evidence

