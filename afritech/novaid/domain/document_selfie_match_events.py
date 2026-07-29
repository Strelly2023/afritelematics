from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .biometric_models import BiometricPurpose
from .document_models import IdentityDocumentType
from .document_selfie_match_models import (
    DocumentSelfieMatchDecision,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class DocumentSelfieMatchEvent:
    event_id: str
    event_type: str
    match_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    verification_id: str
    liveness_assessment_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    document_type: IdentityDocumentType
    purpose: BiometricPurpose
    decision: DocumentSelfieMatchDecision
    similarity_score: float
    document_version: int
    reason_codes: tuple[str, ...]
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "DOCUMENT_SELFIE_EVENT_ID_REQUIRED": self.event_id,
            "DOCUMENT_SELFIE_EVENT_TYPE_REQUIRED": self.event_type,
            "DOCUMENT_SELFIE_MATCH_ID_REQUIRED": self.match_id,
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "FACE_VERIFICATION_ID_REQUIRED": self.verification_id,
            "LIVENESS_ASSESSMENT_ID_REQUIRED": (
                self.liveness_assessment_id
            ),
            "ACTOR_IDENTITY_REQUIRED": self.actor_identity_id,
            "CORRELATION_ID_REQUIRED": self.correlation_id,
            "REQUEST_ID_REQUIRED": self.request_id,
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if self.document_version < 1:
            raise ValueError("INVALID_DOCUMENT_VERSION")

        if (
            isinstance(self.similarity_score, bool)
            or not isinstance(
                self.similarity_score,
                int | float,
            )
            or not 0.0 <= float(self.similarity_score) <= 1.0
        ):
            raise ValueError(
                "INVALID_DOCUMENT_SELFIE_SIMILARITY_SCORE"
            )

        object.__setattr__(
            self,
            "event_type",
            self.event_type.strip().upper(),
        )
        object.__setattr__(
            self,
            "document_type",
            IdentityDocumentType(self.document_type),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "decision",
            DocumentSelfieMatchDecision(self.decision),
        )
        object.__setattr__(
            self,
            "similarity_score",
            float(self.similarity_score),
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


def document_selfie_match_event(
    *,
    match_id: str,
    tenant_id: str,
    identity_id: str,
    document_id: str,
    verification_id: str,
    liveness_assessment_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    document_type: IdentityDocumentType,
    purpose: BiometricPurpose,
    decision: DocumentSelfieMatchDecision,
    similarity_score: float,
    document_version: int,
    reason_codes: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> DocumentSelfieMatchEvent:
    return DocumentSelfieMatchEvent(
        event_id=identifier(),
        event_type=f"DOCUMENT_SELFIE_MATCH_{decision.value}",
        match_id=match_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        verification_id=verification_id,
        liveness_assessment_id=liveness_assessment_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        document_type=document_type,
        purpose=purpose,
        decision=decision,
        similarity_score=similarity_score,
        document_version=document_version,
        reason_codes=reason_codes,
        metadata=dict(metadata or {}),
    )
