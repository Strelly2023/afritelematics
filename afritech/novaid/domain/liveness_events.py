from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .biometric_models import BiometricPurpose
from .liveness_models import (
    LivenessDecision,
    LivenessMode,
    PresentationAttackType,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class LivenessAssessmentEvent:
    event_id: str
    event_type: str
    assessment_id: str
    tenant_id: str
    identity_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    purpose: BiometricPurpose
    decision: LivenessDecision
    mode: LivenessMode
    attempt_number: int
    liveness_score: float
    presentation_attack_score: float
    detected_attack_types: frozenset[
        PresentationAttackType
    ]
    reason_codes: tuple[str, ...]
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "LIVENESS_EVENT_ID_REQUIRED": self.event_id,
            "LIVENESS_EVENT_TYPE_REQUIRED": self.event_type,
            "LIVENESS_ASSESSMENT_ID_REQUIRED": (
                self.assessment_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "ACTOR_IDENTITY_REQUIRED": (
                self.actor_identity_id
            ),
            "CORRELATION_ID_REQUIRED": self.correlation_id,
            "REQUEST_ID_REQUIRED": self.request_id,
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if self.attempt_number < 1:
            raise ValueError(
                "INVALID_LIVENESS_ATTEMPT_NUMBER"
            )

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
            LivenessDecision(self.decision),
        )
        object.__setattr__(
            self,
            "mode",
            LivenessMode(self.mode),
        )
        object.__setattr__(
            self,
            "detected_attack_types",
            frozenset(
                PresentationAttackType(value)
                for value in self.detected_attack_types
            ),
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


def liveness_assessment_event(
    *,
    assessment_id: str,
    tenant_id: str,
    identity_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    purpose: BiometricPurpose,
    decision: LivenessDecision,
    mode: LivenessMode,
    attempt_number: int,
    liveness_score: float,
    presentation_attack_score: float,
    detected_attack_types: frozenset[
        PresentationAttackType
    ],
    reason_codes: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> LivenessAssessmentEvent:
    return LivenessAssessmentEvent(
        event_id=identifier(),
        event_type=f"LIVENESS_ASSESSMENT_{decision.value}",
        assessment_id=assessment_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        purpose=purpose,
        decision=decision,
        mode=mode,
        attempt_number=attempt_number,
        liveness_score=liveness_score,
        presentation_attack_score=(
            presentation_attack_score
        ),
        detected_attack_types=detected_attack_types,
        reason_codes=reason_codes,
        metadata=dict(metadata or {}),
    )
