from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from .enums import EvidenceStatus
from .errors import EvidencePolicyError
from .hashing import utc_now
from .models import EvidenceEnvelope


def create_evidence_envelope(
    evidence_type: str,
    producer: str,
    environment: str,
    subject: str,
    release_id: str,
    execution_id: str,
    *,
    producer_version: str = "1.0",
    source_uri: str = "",
    artifact_refs: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
    findings: list[dict[str, Any]] | None = None,
    trace_ids: list[str] | None = None,
    screenshot_refs: list[str] | None = None,
    log_refs: list[str] | None = None,
    correlation_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> EvidenceEnvelope:
    now = utc_now()
    return EvidenceEnvelope(
        evidence_id=f"ev_{uuid.uuid4().hex}",
        evidence_type=evidence_type,
        producer=producer,
        producer_version=producer_version,
        environment=environment,
        subject=subject,
        release_id=release_id,
        execution_id=execution_id,
        collected_at=now,
        valid_from=now,
        valid_until="9999-12-31T00:00:00Z" if environment != "production" else now,
        status=EvidenceStatus.COLLECTED,
        source_uri=source_uri,
        artifact_refs=artifact_refs or [],
        metrics=metrics or {},
        findings=findings or [],
        trace_ids=trace_ids or [],
        screenshot_refs=screenshot_refs or [],
        log_refs=log_refs or [],
        correlation_id=correlation_id,
        metadata=metadata or {"signature_assurance": "DEVELOPMENT_ONLY"},
    )


def validate_evidence(envelope: EvidenceEnvelope, *, production: bool = False) -> EvidenceEnvelope:
    if envelope.status in {EvidenceStatus.EXPIRED, EvidenceStatus.SUPERSEDED, EvidenceStatus.REJECTED}:
        raise EvidencePolicyError(f"evidence_not_valid:{envelope.status.value}")
    if production and envelope.metadata.get("signature_assurance") == "DEVELOPMENT_ONLY":
        raise EvidencePolicyError("development_signature_cannot_approve_production")
    valid_until = datetime.fromisoformat(envelope.valid_until.replace("Z", "+00:00"))
    if valid_until < datetime.now(UTC):
        envelope.status = EvidenceStatus.EXPIRED
        raise EvidencePolicyError("evidence_expired")
    envelope.status = EvidenceStatus.VALIDATED
    return envelope
