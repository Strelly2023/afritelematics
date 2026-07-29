from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from .biometric_models import BiometricPurpose
from .biometric_verification_models import (
    FaceVerificationDecision,
    FaceVerificationRecord,
)
from .document_models import (
    DocumentVerificationEvidence,
    IdentityDocumentType,
)
from .liveness_models import (
    LivenessAssessmentRecord,
    LivenessDecision,
)
from .models import utcnow


class DocumentSelfieMatchDecision(StrEnum):
    MATCH = "MATCH"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NO_MATCH = "NO_MATCH"
    RECAPTURE = "RECAPTURE"
    LOCK_SESSION = "LOCK_SESSION"


FORBIDDEN_DOCUMENT_SELFIE_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "document_image",
        "portrait_image",
        "raw_portrait",
        "raw_selfie",
        "selfie",
        "selfie_image",
        "image_bytes",
        "raw_video",
        "video",
        "frames",
        "embedding",
        "embeddings",
        "feature_vector",
        "feature_vectors",
        "face_template",
        "biometric_template",
        "provider_payload",
        "provider_secret",
        "api_key",
        "private_key",
    }
)


def _required_text(
    value: str,
    error_code: str,
) -> str:
    if not isinstance(value, str):
        raise ValueError(error_code)

    normalized = value.strip()

    if not normalized:
        raise ValueError(error_code)

    return normalized


def _probability(
    value: float,
    error_code: str,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
    ):
        raise ValueError(error_code)

    normalized = float(value)

    if not 0.0 <= normalized <= 1.0:
        raise ValueError(error_code)

    return normalized


def _assert_safe_metadata(
    metadata: Mapping[str, Any],
) -> None:
    forbidden = {
        str(key).strip().lower()
        for key in metadata
    } & FORBIDDEN_DOCUMENT_SELFIE_FIELDS

    if forbidden:
        raise ValueError(
            "RAW_DOCUMENT_SELFIE_MATERIAL_FORBIDDEN"
        )


@dataclass(frozen=True)
class DocumentSelfieMatchPolicy:
    match_threshold: float = 0.85
    manual_review_threshold: float = 0.65
    minimum_liveness_score: float = 0.85
    minimum_document_score: float = 0.70
    require_document_pass: bool = True
    require_liveness_pass: bool = True
    lock_on_liveness_attack: bool = True
    require_ekyc_purpose: bool = True

    def __post_init__(self) -> None:
        match_threshold = _probability(
            self.match_threshold,
            "INVALID_DOCUMENT_SELFIE_MATCH_THRESHOLD",
        )
        review_threshold = _probability(
            self.manual_review_threshold,
            "INVALID_DOCUMENT_SELFIE_REVIEW_THRESHOLD",
        )
        liveness_threshold = _probability(
            self.minimum_liveness_score,
            "INVALID_DOCUMENT_SELFIE_LIVENESS_THRESHOLD",
        )
        document_threshold = _probability(
            self.minimum_document_score,
            "INVALID_DOCUMENT_SELFIE_DOCUMENT_THRESHOLD",
        )

        if review_threshold >= match_threshold:
            raise ValueError(
                "INVALID_DOCUMENT_SELFIE_THRESHOLD_ORDER"
            )

        object.__setattr__(
            self,
            "match_threshold",
            match_threshold,
        )
        object.__setattr__(
            self,
            "manual_review_threshold",
            review_threshold,
        )
        object.__setattr__(
            self,
            "minimum_liveness_score",
            liveness_threshold,
        )
        object.__setattr__(
            self,
            "minimum_document_score",
            document_threshold,
        )


@dataclass(frozen=True)
class DocumentSelfieMatchEvidence:
    document_evidence: DocumentVerificationEvidence
    face_verification: FaceVerificationRecord
    liveness_assessment: LivenessAssessmentRecord
    provider_reference: str
    algorithm_version: str
    provider_decision_reference: str | None = None
    evaluated_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_reference",
            _required_text(
                self.provider_reference,
                "DOCUMENT_SELFIE_PROVIDER_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "algorithm_version",
            _required_text(
                self.algorithm_version,
                "DOCUMENT_SELFIE_ALGORITHM_VERSION_REQUIRED",
            ),
        )

        if self.provider_decision_reference is not None:
            normalized = self.provider_decision_reference.strip()
            object.__setattr__(
                self,
                "provider_decision_reference",
                normalized or None,
            )

        if not self.document_evidence.portrait_reference:
            raise ValueError(
                "DOCUMENT_PORTRAIT_REFERENCE_REQUIRED"
            )

        object.__setattr__(
            self,
            "reason_codes",
            tuple(
                dict.fromkeys(
                    code.strip().upper()
                    for code in self.reason_codes
                    if isinstance(code, str)
                    and code.strip()
                )
            ),
        )

        metadata = dict(self.metadata)
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class DocumentSelfieMatchRecord:
    match_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    document_evidence_id: str
    verification_id: str
    liveness_assessment_id: str
    document_type: IdentityDocumentType
    purpose: BiometricPurpose
    decision: DocumentSelfieMatchDecision
    similarity_score: float
    liveness_score: float
    document_score: float
    portrait_reference: str
    provider_reference: str
    algorithm_version: str
    document_version: int
    matched_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "DOCUMENT_SELFIE_MATCH_ID_REQUIRED": self.match_id,
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "DOCUMENT_EVIDENCE_ID_REQUIRED": (
                self.document_evidence_id
            ),
            "FACE_VERIFICATION_ID_REQUIRED": (
                self.verification_id
            ),
            "LIVENESS_ASSESSMENT_ID_REQUIRED": (
                self.liveness_assessment_id
            ),
            "DOCUMENT_PORTRAIT_REFERENCE_REQUIRED": (
                self.portrait_reference
            ),
            "DOCUMENT_SELFIE_PROVIDER_REFERENCE_REQUIRED": (
                self.provider_reference
            ),
            "DOCUMENT_SELFIE_ALGORITHM_VERSION_REQUIRED": (
                self.algorithm_version
            ),
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if (
            isinstance(self.document_version, bool)
            or not isinstance(self.document_version, int)
            or self.document_version < 1
        ):
            raise ValueError("INVALID_DOCUMENT_VERSION")

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
            _probability(
                self.similarity_score,
                "INVALID_DOCUMENT_SELFIE_SIMILARITY_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "liveness_score",
            _probability(
                self.liveness_score,
                "INVALID_DOCUMENT_SELFIE_LIVENESS_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "document_score",
            _probability(
                self.document_score,
                "INVALID_DOCUMENT_SELFIE_DOCUMENT_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(self.reason_codes),
        )

        metadata = dict(self.metadata)
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


__all__ = [
    "DocumentSelfieMatchDecision",
    "DocumentSelfieMatchEvidence",
    "DocumentSelfieMatchPolicy",
    "DocumentSelfieMatchRecord",
    "FORBIDDEN_DOCUMENT_SELFIE_FIELDS",
]
