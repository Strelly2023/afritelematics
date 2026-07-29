from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .document_models import IdentityDocumentType
from .document_ocr_models import (
    OCRExtractionDecision,
    OCRExtractionSource,
)
from .models import identifier, utcnow


@dataclass(frozen=True)
class OCRExtractionEvent:
    event_id: str
    event_type: str
    extraction_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    document_type: IdentityDocumentType
    decision: OCRExtractionDecision
    source: OCRExtractionSource
    overall_confidence_score: float
    document_version: int
    reason_codes: tuple[str, ...]
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "OCR_EVENT_ID_REQUIRED": self.event_id,
            "OCR_EVENT_TYPE_REQUIRED": self.event_type,
            "OCR_EXTRACTION_ID_REQUIRED": self.extraction_id,
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "ACTOR_IDENTITY_REQUIRED": (
                self.actor_identity_id
            ),
            "CORRELATION_ID_REQUIRED": self.correlation_id,
            "REQUEST_ID_REQUIRED": self.request_id,
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
            isinstance(self.overall_confidence_score, bool)
            or not isinstance(
                self.overall_confidence_score,
                int | float,
            )
            or not 0.0
            <= float(self.overall_confidence_score)
            <= 1.0
        ):
            raise ValueError(
                "INVALID_OCR_CONFIDENCE_SCORE"
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
            "decision",
            OCRExtractionDecision(
                self.decision
            ),
        )
        object.__setattr__(
            self,
            "source",
            OCRExtractionSource(self.source),
        )
        object.__setattr__(
            self,
            "overall_confidence_score",
            float(self.overall_confidence_score),
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


def ocr_extraction_event(
    *,
    extraction_id: str,
    tenant_id: str,
    identity_id: str,
    document_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    document_type: IdentityDocumentType,
    decision: OCRExtractionDecision,
    source: OCRExtractionSource,
    overall_confidence_score: float,
    document_version: int,
    reason_codes: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> OCRExtractionEvent:
    return OCRExtractionEvent(
        event_id=identifier(),
        event_type=f"OCR_EXTRACTION_{decision.value}",
        extraction_id=extraction_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        document_type=document_type,
        decision=decision,
        source=source,
        overall_confidence_score=(
            overall_confidence_score
        ),
        document_version=document_version,
        reason_codes=reason_codes,
        metadata=dict(metadata or {}),
    )
