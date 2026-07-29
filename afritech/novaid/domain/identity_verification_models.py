from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from .biometric_models import BiometricPurpose
from .document_authenticity_models import (
    DocumentAuthenticityAssessmentRecord,
)
from .document_models import (
    DocumentAuthenticityDecision,
    IdentityDocumentType,
)
from .document_ocr_models import (
    OCRExtractionDecision,
    OCRExtractionRecord,
)
from .document_selfie_match_models import (
    DocumentSelfieMatchDecision,
    DocumentSelfieMatchRecord,
)
from .models import AssuranceLevel, utcnow


class IdentityVerificationDecision(StrEnum):
    VERIFIED = "VERIFIED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"
    RECAPTURE_REQUIRED = "RECAPTURE_REQUIRED"
    LOCKED = "LOCKED"


class IdentityVerificationStage(StrEnum):
    OCR = "OCR"
    DOCUMENT_AUTHENTICITY = "DOCUMENT_AUTHENTICITY"
    DOCUMENT_SELFIE_MATCH = "DOCUMENT_SELFIE_MATCH"
    FINAL_DECISION = "FINAL_DECISION"


FORBIDDEN_IDENTITY_VERIFICATION_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "image_bytes",
        "document_image",
        "portrait_image",
        "raw_portrait",
        "raw_selfie",
        "selfie",
        "selfie_image",
        "raw_video",
        "video",
        "frames",
        "embedding",
        "embeddings",
        "feature_vector",
        "feature_vectors",
        "face_template",
        "biometric_template",
        "raw_mrz",
        "mrz_raw",
        "barcode_payload",
        "nfc_dump",
        "provider_payload",
        "full_provider_response",
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
    } & FORBIDDEN_IDENTITY_VERIFICATION_FIELDS

    if forbidden:
        raise ValueError(
            "RAW_IDENTITY_VERIFICATION_MATERIAL_FORBIDDEN"
        )


@dataclass(frozen=True)
class IdentityVerificationPolicy:
    minimum_ocr_score: float = 0.85
    minimum_authenticity_score: float = 0.85
    minimum_selfie_match_score: float = 0.85
    minimum_liveness_score: float = 0.85
    minimum_combined_score: float = 0.85
    manual_review_combined_score: float = 0.65
    require_ocr_accept: bool = True
    require_authentic_document: bool = True
    require_document_selfie_match: bool = True
    require_ekyc_purpose: bool = True
    reject_suspected_fraud: bool = True
    lock_on_session_lock: bool = True
    verified_assurance_level: AssuranceLevel = (
        AssuranceLevel.NID_AL2
    )
    manual_review_assurance_level: AssuranceLevel = (
        AssuranceLevel.NID_AL1
    )
    policy_version: str = "2026-07-29.1"

    def __post_init__(self) -> None:
        values = {
            "minimum_ocr_score": (
                self.minimum_ocr_score,
                "INVALID_IDENTITY_VERIFICATION_OCR_THRESHOLD",
            ),
            "minimum_authenticity_score": (
                self.minimum_authenticity_score,
                "INVALID_IDENTITY_VERIFICATION_AUTHENTICITY_THRESHOLD",
            ),
            "minimum_selfie_match_score": (
                self.minimum_selfie_match_score,
                "INVALID_IDENTITY_VERIFICATION_MATCH_THRESHOLD",
            ),
            "minimum_liveness_score": (
                self.minimum_liveness_score,
                "INVALID_IDENTITY_VERIFICATION_LIVENESS_THRESHOLD",
            ),
            "minimum_combined_score": (
                self.minimum_combined_score,
                "INVALID_IDENTITY_VERIFICATION_COMBINED_THRESHOLD",
            ),
            "manual_review_combined_score": (
                self.manual_review_combined_score,
                "INVALID_IDENTITY_VERIFICATION_REVIEW_THRESHOLD",
            ),
        }

        for field_name, (
            value,
            error_code,
        ) in values.items():
            object.__setattr__(
                self,
                field_name,
                _probability(value, error_code),
            )

        if (
            self.manual_review_combined_score
            >= self.minimum_combined_score
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_THRESHOLD_ORDER"
            )

        object.__setattr__(
            self,
            "verified_assurance_level",
            AssuranceLevel(
                self.verified_assurance_level
            ),
        )
        object.__setattr__(
            self,
            "manual_review_assurance_level",
            AssuranceLevel(
                self.manual_review_assurance_level
            ),
        )
        object.__setattr__(
            self,
            "policy_version",
            _required_text(
                self.policy_version,
                "IDENTITY_VERIFICATION_POLICY_VERSION_REQUIRED",
            ),
        )


    # ------------------------------------------------------------------
    # Backward-compatible policy vocabulary
    #
    # These aliases preserve the canonical Step 4E implementation fields
    # while supporting the earlier model-contract terminology.
    # ------------------------------------------------------------------
    @property
    def require_ocr_acceptance(self) -> bool:
        return self.require_ocr_accept

    @property
    def require_document_authenticity(self) -> bool:
        return self.require_authentic_document

    @property
    def require_face_match(self) -> bool:
        return self.require_document_selfie_match

    @property
    def require_liveness(self) -> bool:
        return self.require_document_selfie_match


@dataclass(frozen=True)
class IdentityVerificationEvidence:
    ocr_extraction: OCRExtractionRecord
    authenticity_assessment: (
        DocumentAuthenticityAssessmentRecord
    )
    selfie_match: DocumentSelfieMatchRecord
    workflow_id: str
    evidence_version: int = 1
    collected_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "workflow_id",
            _required_text(
                self.workflow_id,
                "IDENTITY_VERIFICATION_WORKFLOW_ID_REQUIRED",
            ),
        )

        if (
            isinstance(self.evidence_version, bool)
            or not isinstance(self.evidence_version, int)
            or self.evidence_version < 1
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_EVIDENCE_VERSION"
            )

        metadata = dict(self.metadata)
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class IdentityVerificationRecord:
    verification_id: str
    workflow_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    document_type: IdentityDocumentType
    purpose: BiometricPurpose
    decision: IdentityVerificationDecision
    assurance_level: AssuranceLevel
    combined_score: float
    ocr_score: float
    authenticity_score: float
    selfie_match_score: float
    liveness_score: float
    ocr_extraction_id: str
    authenticity_assessment_id: str
    selfie_match_id: str
    policy_version: str
    document_version: int
    verified_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "IDENTITY_VERIFICATION_ID_REQUIRED": (
                self.verification_id
            ),
            "IDENTITY_VERIFICATION_WORKFLOW_ID_REQUIRED": (
                self.workflow_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "OCR_EXTRACTION_ID_REQUIRED": (
                self.ocr_extraction_id
            ),
            "DOCUMENT_AUTHENTICITY_ASSESSMENT_ID_REQUIRED": (
                self.authenticity_assessment_id
            ),
            "DOCUMENT_SELFIE_MATCH_ID_REQUIRED": (
                self.selfie_match_id
            ),
            "IDENTITY_VERIFICATION_POLICY_VERSION_REQUIRED": (
                self.policy_version
            ),
        }

        field_names = {
            "IDENTITY_VERIFICATION_ID_REQUIRED": (
                "verification_id"
            ),
            "IDENTITY_VERIFICATION_WORKFLOW_ID_REQUIRED": (
                "workflow_id"
            ),
            "TENANT_ID_REQUIRED": "tenant_id",
            "IDENTITY_ID_REQUIRED": "identity_id",
            "DOCUMENT_ID_REQUIRED": "document_id",
            "OCR_EXTRACTION_ID_REQUIRED": (
                "ocr_extraction_id"
            ),
            "DOCUMENT_AUTHENTICITY_ASSESSMENT_ID_REQUIRED": (
                "authenticity_assessment_id"
            ),
            "DOCUMENT_SELFIE_MATCH_ID_REQUIRED": (
                "selfie_match_id"
            ),
            "IDENTITY_VERIFICATION_POLICY_VERSION_REQUIRED": (
                "policy_version"
            ),
        }

        for error_code, value in required.items():
            object.__setattr__(
                self,
                field_names[error_code],
                _required_text(value, error_code),
            )

        if (
            isinstance(self.document_version, bool)
            or not isinstance(self.document_version, int)
            or self.document_version < 1
        ):
            raise ValueError(
                "INVALID_DOCUMENT_VERSION"
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

        for field_name, error_code in (
            (
                "combined_score",
                "INVALID_IDENTITY_VERIFICATION_COMBINED_SCORE",
            ),
            (
                "ocr_score",
                "INVALID_IDENTITY_VERIFICATION_OCR_SCORE",
            ),
            (
                "authenticity_score",
                "INVALID_IDENTITY_VERIFICATION_AUTHENTICITY_SCORE",
            ),
            (
                "selfie_match_score",
                "INVALID_IDENTITY_VERIFICATION_MATCH_SCORE",
            ),
            (
                "liveness_score",
                "INVALID_IDENTITY_VERIFICATION_LIVENESS_SCORE",
            ),
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(
                    getattr(self, field_name),
                    error_code,
                ),
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


__all__ = [
    "FORBIDDEN_IDENTITY_VERIFICATION_FIELDS",
    "IdentityVerificationDecision",
    "IdentityVerificationEvidence",
    "IdentityVerificationPolicy",
    "IdentityVerificationRecord",
    "IdentityVerificationStage",
]
