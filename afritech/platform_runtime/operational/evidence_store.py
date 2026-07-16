"""Persistent runtime evidence storage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..persistence.models import EvidenceRecord
from ..persistence.repository import RuntimeControlRepository
from ..runtime_evidence import RuntimeEvidenceRecord


@dataclass
class PersistentEvidenceStore:
    repository: RuntimeControlRepository
    object_root: Path

    async def write(self, record: RuntimeEvidenceRecord, payload: dict[str, Any]) -> str:
        target = self.object_root / record.environment / record.region / record.product_code / record.version / record.evidence_id
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{record.operation}.json"
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        checksum = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        await self.repository.save_evidence_record(
            EvidenceRecord(
                id=record.evidence_id,
                product_code=record.product_code,
                product_version=record.version,
                environment=record.environment,
                region=record.region,
                tenant_id=payload.get("tenant_id", ""),
                status="PERSISTED",
                checksum=checksum,
                evidence_id=record.evidence_id,
                operation=record.operation,
                object_uri=path.as_uri(),
                signature=record.signature,
                recorded_at=record.recorded_at,
                created_by=record.actor_id,
                updated_by=record.actor_id,
                correlation_id=record.correlation_id,
                metadata={"approval_id": record.approval_id},
            )
        )
        return path.as_uri()
