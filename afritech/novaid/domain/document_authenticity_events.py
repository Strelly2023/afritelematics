from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .document_models import (
    DocumentAuthenticityDecision,
    IdentityDocumentType,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class DocumentAuthenticityAssessmentEvent:
    event_id: str
    event_type: str
    assessment_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    document_type: IdentityDocumentType
    decision: DocumentAuthenticityDecision
    overall_score: float
    tampering_score: float
    document_version: int
    reason_codes: tuple[str, ...]
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "DOCUMENT_AUTHENTICITY_EVENT_ID_REQUIRED":
                self.event_id,
            "DOCUMENT_AUTHENTICITY_EVENT_TYPE_REQUIRED":
                self.event_type,
            "DOCUMENT_AUTHENTICITY_ASSESSMENT_ID_REQUIRED":
                self.assessment_id,
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "ACTOR_IDENTITY_REQUIRED":
                self.actor_identity_id,
            "CORRELATION_ID_REQUIRED":
                self.correlation_id,
            "REQUEST_ID_REQUIRED":
                self.request_id,
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

        for value, error_code in (
            (
                self.overall_score,
                "INVALID_DOCUMENT_AUTHENTICITY_SCORE",
            ),
            (
                self.tampering_score,
                "INVALID_DOCUMENT_TAMPERING_SCORE",
            ),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not 0.0 <= float(value) <= 1.0
            ):
                raise ValueError(error_code)

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
            "decision",
            DocumentAuthenticityDecision(self.decision),
        )
        object.__setattr__(
            self,
            "overall_score",
            float(self.overall_score),
        )
        object.__setattr__(
            self,
            "tampering_score",
            float(self.tampering_score),
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


def document_authenticity_assessment_event(
    *,
    assessment_id: str,
    tenant_id: str,
    identity_id: str,
    document_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    document_type: IdentityDocumentType,
    decision: DocumentAuthenticityDecision,
    overall_score: float,
    tampering_score: float,
    document_version: int,
    reason_codes: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> DocumentAuthenticityAssessmentEvent:
    return DocumentAuthenticityAssessmentEvent(
        event_id=identifier(),
        event_type=(
            f"DOCUMENT_AUTHENTICITY_{decision.value}"
        ),
        assessment_id=assessment_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        document_type=document_type,
        decision=decision,
        overall_score=overall_score,
        tampering_score=tampering_score,
        document_version=document_version,
        reason_codes=reason_codes,
        metadata=dict(metadata or {}),
    )
