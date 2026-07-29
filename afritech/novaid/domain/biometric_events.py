from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .biometric_models import (
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class FaceEnrollmentEvent:
    event_id: str
    event_type: str
    tenant_id: str
    identity_id: str
    enrollment_id: str
    consent_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    biometric_type: BiometricType
    purpose: BiometricPurpose
    enrollment_status: BiometricEnrollmentStatus
    enrollment_version: int
    quality_score: float
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required_values = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "identity_id": self.identity_id,
            "enrollment_id": self.enrollment_id,
            "consent_id": self.consent_id,
            "actor_identity_id": self.actor_identity_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
        }

        for field_name, value in required_values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"FACE_ENROLLMENT_EVENT_{field_name.upper()}_REQUIRED"
                )

            object.__setattr__(
                self,
                field_name,
                value.strip(),
            )

        if self.enrollment_version < 1:
            raise ValueError(
                "INVALID_AGGREGATE_VERSION"
            )

        if (
            isinstance(self.quality_score, bool)
            or not isinstance(self.quality_score, int | float)
            or not 0.0 <= float(self.quality_score) <= 1.0
        ):
            raise ValueError(
                "INVALID_CAPTURE_QUALITY_SCORE"
            )

        object.__setattr__(
            self,
            "event_type",
            self.event_type.strip().upper(),
        )
        object.__setattr__(
            self,
            "biometric_type",
            BiometricType(self.biometric_type),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "enrollment_status",
            BiometricEnrollmentStatus(
                self.enrollment_status
            ),
        )
        object.__setattr__(
            self,
            "quality_score",
            float(self.quality_score),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


def face_enrollment_event(
    *,
    tenant_id: str,
    identity_id: str,
    enrollment_id: str,
    consent_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    enrollment_status: BiometricEnrollmentStatus,
    enrollment_version: int,
    quality_score: float,
    metadata: dict[str, Any] | None = None,
) -> FaceEnrollmentEvent:
    return FaceEnrollmentEvent(
        event_id=identifier(),
        event_type="FACE_ENROLLMENT_ACTIVATED",
        tenant_id=tenant_id,
        identity_id=identity_id,
        enrollment_id=enrollment_id,
        consent_id=consent_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        enrollment_status=enrollment_status,
        enrollment_version=enrollment_version,
        quality_score=quality_score,
        metadata=dict(metadata or {}),
    )
