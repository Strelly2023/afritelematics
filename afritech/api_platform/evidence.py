"""Evidence recording for the API platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json
import uuid


def _sha(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    product_code: str
    endpoint_id: str
    request_id: str
    correlation_id: str
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)


class EvidenceStore:
    def __init__(self) -> None:
        self.records: dict[str, EvidenceRecord] = {}

    def record(self, *, product_code: str, endpoint_id: str, request_id: str, correlation_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> EvidenceRecord:
        record = EvidenceRecord(
            evidence_id=f"evidence-{uuid.uuid4().hex[:16]}",
            product_code=product_code,
            endpoint_id=endpoint_id,
            request_id=request_id,
            correlation_id=correlation_id,
            checksum=_sha(payload),
            metadata=metadata or {},
        )
        self.records[record.evidence_id] = record
        return record
