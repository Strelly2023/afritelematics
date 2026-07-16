"""Immutable runtime evidence generation for NovaTech product activation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
import hashlib
import json
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RuntimeEvidenceRecord:
    evidence_id: str
    product_code: str
    version: str
    environment: str
    region: str
    operation: str
    actor_id: str
    approval_id: str
    correlation_id: str
    inputs_hash: str
    result_hash: str
    module_checksum: str
    configuration_checksum: str
    infrastructure_checksum: str
    checks: tuple[dict[str, Any], ...]
    recorded_at: str
    signature: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "product_code": self.product_code,
            "version": self.version,
            "environment": self.environment,
            "region": self.region,
            "operation": self.operation,
            "actor_id": self.actor_id,
            "approval_id": self.approval_id,
            "correlation_id": self.correlation_id,
            "inputs_hash": self.inputs_hash,
            "result_hash": self.result_hash,
            "module_checksum": self.module_checksum,
            "configuration_checksum": self.configuration_checksum,
            "infrastructure_checksum": self.infrastructure_checksum,
            "checks": list(self.checks),
            "recorded_at": self.recorded_at,
            "signature": self.signature,
        }


class RuntimeEvidenceService:
    def __init__(self) -> None:
        self._records: dict[str, RuntimeEvidenceRecord] = {}

    def record(
        self,
        *,
        product_code: str,
        version: str,
        environment: str,
        region: str,
        operation: str,
        actor_id: str,
        approval_id: str,
        correlation_id: str,
        inputs: Mapping[str, Any],
        result: Mapping[str, Any],
        module_checksum: str,
        configuration_checksum: str,
        infrastructure_checksum: str,
        checks: tuple[dict[str, Any], ...] = (),
    ) -> RuntimeEvidenceRecord:
        record = RuntimeEvidenceRecord(
            evidence_id=f"evidence-{uuid.uuid4().hex[:16]}",
            product_code=product_code,
            version=version,
            environment=environment,
            region=region,
            operation=operation,
            actor_id=actor_id,
            approval_id=approval_id,
            correlation_id=correlation_id,
            inputs_hash=_sha(inputs),
            result_hash=_sha(result),
            module_checksum=module_checksum,
            configuration_checksum=configuration_checksum,
            infrastructure_checksum=infrastructure_checksum,
            checks=checks,
            recorded_at=_now(),
            signature=_sha({"product_code": product_code, "version": version, "operation": operation, "inputs": inputs, "result": result}),
        )
        self._records[record.evidence_id] = record
        return record

    def get(self, evidence_id: str) -> RuntimeEvidenceRecord:
        return self._records[evidence_id]

    def snapshot(self) -> dict[str, Any]:
        return {"evidence": [record.canonical_dict() for record in self._records.values()]}


__all__ = ["RuntimeEvidenceRecord", "RuntimeEvidenceService"]
