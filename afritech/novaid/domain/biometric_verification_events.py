from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .biometric_models import BiometricPurpose
from .biometric_verification_models import (
    FaceVerificationDecision,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class FaceVerificationEvent:
    event_id: str
    event_type: str
    verification_id: str
    tenant_id: str
    identity_id: str
    enrollment_id: str
    consent_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    purpose: BiometricPurpose
    decision: FaceVerificationDecision
    similarity_score: float
    threshold: float
    provider_reference: str
    algorithm_version: str
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "FACE_VERIFICATION_EVENT_ID_REQUIRED": self.event_id,
            "FACE_VERIFICATION_EVENT_TYPE_REQUIRED": self.event_type,
            "FACE_VERIFICATION_ID_REQUIRED": self.verification_id,
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "BIOMETRIC_ENROLLMENT_ID_REQUIRED": self.enrollment_id,
            "BIOMETRIC_CONSENT_ID_REQUIRED": self.consent_id,
            "ACTOR_IDENTITY_REQUIRED": self.actor_identity_id,
            "CORRELATION_ID_REQUIRED": self.correlation_id,
            "REQUEST_ID_REQUIRED": self.request_id,
            "BIOMETRIC_PROVIDER_REFERENCE_REQUIRED": (
                self.provider_reference
            ),
            "BIOMETRIC_ALGORITHM_VERSION_REQUIRED": (
                self.algorithm_version
            ),
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if not 0.0 <= float(self.similarity_score) <= 1.0:
            raise ValueError("INVALID_FACE_SIMILARITY_SCORE")

        if not 0.0 <= float(self.threshold) <= 1.0:
            raise ValueError("INVALID_FACE_MATCH_THRESHOLD")

        object.__setattr__(
            self,
            "event_type",
            self.event_type.strip().upper(),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "decision",
            FaceVerificationDecision(self.decision),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


def face_verification_event(
    *,
    verification_id: str,
    tenant_id: str,
    identity_id: str,
    enrollment_id: str,
    consent_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    purpose: BiometricPurpose,
    decision: FaceVerificationDecision,
    similarity_score: float,
    threshold: float,
    provider_reference: str,
    algorithm_version: str,
    metadata: dict[str, Any] | None = None,
) -> FaceVerificationEvent:
    return FaceVerificationEvent(
        event_id=identifier(),
        event_type=f"FACE_VERIFICATION_{decision.value}",
        verification_id=verification_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        enrollment_id=enrollment_id,
        consent_id=consent_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        purpose=purpose,
        decision=decision,
        similarity_score=similarity_score,
        threshold=threshold,
        provider_reference=provider_reference,
        algorithm_version=algorithm_version,
        metadata=dict(metadata or {}),
    )
