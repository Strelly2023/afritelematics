from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any
import uuid

from .hashing import domain_hash, utc_now, without_integrity_fields


EVENT_TYPES = (
    "OperationalVerificationProgramCreated",
    "OperationalVerificationStarted",
    "OperationalVerificationCompleted",
    "VerificationCheckStarted",
    "VerificationCheckCompleted",
    "VerificationFailed",
    "EvidenceCollected",
    "EvidenceValidated",
    "EvidenceRejected",
    "AccessibilityScanCompleted",
    "VisualRegressionCompleted",
    "ObservabilityVerificationCompleted",
    "TelemetryIngestionCompleted",
    "DigitalUXTwinSimulationCompleted",
    "PRRPackageGenerated",
    "PRRRecommendationIssued",
    "ApprovalRequested",
    "ApprovalGranted",
    "ApprovalRejected",
    "ExecutiveApprovalGranted",
    "ExecutiveApprovalRejected",
    "GAGateEvaluated",
    "PaymentActivationGateEvaluated",
)


@dataclass(slots=True)
class OperationalVerificationEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: str
    tenant_id: str
    organization_id: str
    region: str
    actor_id: str
    actor_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    aggregate_version: int = 1
    occurred_at: str = field(default_factory=utc_now)
    correlation_id: str = ""
    causation_id: str = ""
    schema_version: str = "1.0"
    integrity_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["integrity_hash"] = self.integrity_hash or domain_hash("novacodepro.event", without_integrity_fields(body))
        return body
