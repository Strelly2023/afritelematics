from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .biometric_models import BiometricPurpose
from .document_models import IdentityDocumentType
from .identity_verification_models import (
    IdentityVerificationDecision,
)
from .models import AssuranceLevel, identifier, utcnow


@dataclass(frozen=True)
class IdentityVerificationOutcomeEvent:
    event_id: str
    event_type: str
    verification_id: str
    workflow_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    document_type: IdentityDocumentType
    purpose: BiometricPurpose
    decision: IdentityVerificationDecision
    assurance_level: AssuranceLevel
    combined_score: float
    policy_version: str
    document_version: int
    reason_codes: tuple[str, ...]
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "IDENTITY_VERIFICATION_EVENT_ID_REQUIRED": (
                self.event_id
            ),
            "IDENTITY_VERIFICATION_EVENT_TYPE_REQUIRED": (
                self.event_type
            ),
            "IDENTITY_VERIFICATION_ID_REQUIRED": (
                self.verification_id
            ),
            "IDENTITY_VERIFICATION_WORKFLOW_ID_REQUIRED": (
                self.workflow_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "ACTOR_IDENTITY_REQUIRED": (
                self.actor_identity_id
            ),
            "CORRELATION_ID_REQUIRED": (
                self.correlation_id
            ),
            "REQUEST_ID_REQUIRED": self.request_id,
            "IDENTITY_VERIFICATION_POLICY_VERSION_REQUIRED": (
                self.policy_version
            ),
        }

        for error_code, value in required.items():
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(error_code)

        if (
            isinstance(self.document_version, bool)
            or not isinstance(self.document_version, int)
            or self.document_version < 1
        ):
            raise ValueError(
                "INVALID_DOCUMENT_VERSION"
            )

        if (
            isinstance(self.combined_score, bool)
            or not isinstance(
                self.combined_score,
                int | float,
            )
            or not 0.0
            <= float(self.combined_score)
            <= 1.0
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_COMBINED_SCORE"
            )

        object.__setattr__(
            self,
            "event_type",
            self.event_type.strip().upper(),
        )
        object.__setattr__(
            self,
            "document_type",
            IdentityDocumentType(
                self.document_type
            ),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "decision",
            IdentityVerificationDecision(
                self.decision
            ),
        )
        object.__setattr__(
            self,
            "assurance_level",
            AssuranceLevel(self.assurance_level),
        )
        object.__setattr__(
            self,
            "combined_score",
            float(self.combined_score),
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


def identity_verification_outcome_event(
    *,
    verification_id: str,
    workflow_id: str,
    tenant_id: str,
    identity_id: str,
    document_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    document_type: IdentityDocumentType,
    purpose: BiometricPurpose,
    decision: IdentityVerificationDecision,
    assurance_level: AssuranceLevel,
    combined_score: float,
    policy_version: str,
    document_version: int,
    reason_codes: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> IdentityVerificationOutcomeEvent:
    return IdentityVerificationOutcomeEvent(
        event_id=identifier(),
        event_type=(
            f"IDENTITY_VERIFICATION_{decision.value}"
        ),
        verification_id=verification_id,
        workflow_id=workflow_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        document_type=document_type,
        purpose=purpose,
        decision=decision,
        assurance_level=assurance_level,
        combined_score=combined_score,
        policy_version=policy_version,
        document_version=document_version,
        reason_codes=reason_codes,
        metadata=dict(metadata or {}),
    )
