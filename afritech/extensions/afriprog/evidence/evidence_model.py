from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class EvidenceModelError(Exception):
    """Raised when evidence model construction fails."""


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    phase: str
    source: str
    status: str
    subject: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise EvidenceModelError("evidence_id must not be empty")

        if not self.phase.strip():
            raise EvidenceModelError("phase must not be empty")

        if not self.source.strip():
            raise EvidenceModelError("source must not be empty")

        if not self.status.strip():
            raise EvidenceModelError("status must not be empty")

        if not self.subject.strip():
            raise EvidenceModelError("subject must not be empty")

    @property
    def evidence_hash(self) -> str:
        material = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "phase": self.phase,
            "source": self.source,
            "status": self.status,
            "subject": self.subject,
            "payload": self.payload,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            **self.canonical_payload(),
            "evidence_hash": self.evidence_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_dict()
