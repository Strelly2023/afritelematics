from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .biometric_models import BiometricPurpose
from .face_authentication_models import (
    FaceAuthenticationDecision,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class FaceAuthenticationEvent:
    event_id: str
    event_type: str
    authentication_id: str
    tenant_id: str
    identity_id: str
    verification_id: str
    enrollment_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    purpose: BiometricPurpose
    decision: FaceAuthenticationDecision
    risk_score: float
    reason_codes: tuple[str, ...]
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "FACE_AUTHENTICATION_EVENT_ID_REQUIRED": (
                self.event_id
            ),
            "FACE_AUTHENTICATION_EVENT_TYPE_REQUIRED": (
                self.event_type
            ),
            "FACE_AUTHENTICATION_ID_REQUIRED": (
                self.authentication_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "FACE_VERIFICATION_ID_REQUIRED": (
                self.verification_id
            ),
            "BIOMETRIC_ENROLLMENT_ID_REQUIRED": (
                self.enrollment_id
            ),
            "ACTOR_IDENTITY_REQUIRED": (
                self.actor_identity_id
            ),
            "CORRELATION_ID_REQUIRED": self.correlation_id,
            "REQUEST_ID_REQUIRED": self.request_id,
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if (
            isinstance(self.risk_score, bool)
            or not isinstance(self.risk_score, int | float)
            or not 0.0 <= float(self.risk_score) <= 1.0
        ):
            raise ValueError("INVALID_RISK_SCORE")

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
            FaceAuthenticationDecision(self.decision),
        )
        object.__setattr__(
            self,
            "risk_score",
            float(self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(self.reason_codes),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


def face_authentication_event(
    *,
    authentication_id: str,
    tenant_id: str,
    identity_id: str,
    verification_id: str,
    enrollment_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    purpose: BiometricPurpose,
    decision: FaceAuthenticationDecision,
    risk_score: float,
    reason_codes: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> FaceAuthenticationEvent:
    return FaceAuthenticationEvent(
        event_id=identifier(),
        event_type=f"FACE_AUTHENTICATION_{decision.value}",
        authentication_id=authentication_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        verification_id=verification_id,
        enrollment_id=enrollment_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        purpose=purpose,
        decision=decision,
        risk_score=risk_score,
        reason_codes=reason_codes,
        metadata=dict(metadata or {}),
    )
