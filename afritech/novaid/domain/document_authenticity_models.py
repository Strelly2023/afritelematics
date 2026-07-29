from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from .document_models import (
    DocumentAuthenticityDecision,
    IdentityDocumentType,
)
from .models import utcnow


class DocumentSecurityFeature(StrEnum):
    HOLOGRAM = "HOLOGRAM"
    UV_PATTERN = "UV_PATTERN"
    MICROPRINT = "MICROPRINT"
    GUILLOCHE = "GUILLOCHE"
    OPTICALLY_VARIABLE_INK = "OPTICALLY_VARIABLE_INK"
    LASER_ENGRAVING = "LASER_ENGRAVING"
    TACTILE_FEATURE = "TACTILE_FEATURE"
    KINEGRAM = "KINEGRAM"
    SECURITY_THREAD = "SECURITY_THREAD"
    WATERMARK = "WATERMARK"
    PORTRAIT_BINDING = "PORTRAIT_BINDING"
    MRZ = "MRZ"
    BARCODE = "BARCODE"
    NFC_CHIP = "NFC_CHIP"
    UNKNOWN = "UNKNOWN"


class DocumentFraudIndicator(StrEnum):
    NONE = "NONE"
    IMAGE_MANIPULATION = "IMAGE_MANIPULATION"
    TEXT_REPLACEMENT = "TEXT_REPLACEMENT"
    PORTRAIT_REPLACEMENT = "PORTRAIT_REPLACEMENT"
    FONT_INCONSISTENCY = "FONT_INCONSISTENCY"
    LAYOUT_INCONSISTENCY = "LAYOUT_INCONSISTENCY"
    MRZ_MISMATCH = "MRZ_MISMATCH"
    BARCODE_MISMATCH = "BARCODE_MISMATCH"
    EXPIRED_TEMPLATE = "EXPIRED_TEMPLATE"
    COPY_OR_SCREEN_CAPTURE = "COPY_OR_SCREEN_CAPTURE"
    SYNTHETIC_DOCUMENT = "SYNTHETIC_DOCUMENT"
    PROVIDER_HIGH_RISK = "PROVIDER_HIGH_RISK"
    UNKNOWN = "UNKNOWN"


SEVERE_DOCUMENT_FRAUD_INDICATORS = frozenset(
    {
        DocumentFraudIndicator.IMAGE_MANIPULATION,
        DocumentFraudIndicator.TEXT_REPLACEMENT,
        DocumentFraudIndicator.PORTRAIT_REPLACEMENT,
        DocumentFraudIndicator.MRZ_MISMATCH,
        DocumentFraudIndicator.BARCODE_MISMATCH,
        DocumentFraudIndicator.SYNTHETIC_DOCUMENT,
        DocumentFraudIndicator.PROVIDER_HIGH_RISK,
    }
)


FORBIDDEN_DOCUMENT_AUTHENTICITY_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "image_bytes",
        "document_image",
        "portrait_image",
        "raw_portrait",
        "raw_video",
        "video",
        "frames",
        "raw_mrz",
        "mrz_raw",
        "barcode_payload",
        "raw_barcode",
        "nfc_dump",
        "raw_nfc",
        "embedding",
        "embeddings",
        "feature_vector",
        "feature_vectors",
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


def _optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError("INVALID_OPTIONAL_TEXT")

    normalized = value.strip()
    return normalized or None


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
    } & FORBIDDEN_DOCUMENT_AUTHENTICITY_FIELDS

    if forbidden:
        raise ValueError(
            "RAW_DOCUMENT_AUTHENTICITY_MATERIAL_FORBIDDEN"
        )


@dataclass(frozen=True)
class DocumentSecurityFeatureEvidence:
    feature: DocumentSecurityFeature
    present: bool
    confidence_score: float
    provider_reference: str | None = None
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature",
            DocumentSecurityFeature(self.feature),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _probability(
                self.confidence_score,
                "INVALID_SECURITY_FEATURE_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "provider_reference",
            _optional_text(self.provider_reference),
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


@dataclass(frozen=True)
class DocumentAuthenticityProviderEvidence:
    provider_reference: str
    algorithm_version: str
    document_type: IdentityDocumentType
    overall_score: float
    tampering_score: float
    security_feature_score: float | None = None
    hologram_score: float | None = None
    portrait_integrity_score: float | None = None
    image_integrity_score: float | None = None
    layout_consistency_score: float | None = None
    mrz_consistent: bool | None = None
    barcode_consistent: bool | None = None
    document_template_supported: bool = True
    detected_features: tuple[
        DocumentSecurityFeatureEvidence,
        ...
    ] = ()
    fraud_indicators: frozenset[
        DocumentFraudIndicator
    ] = frozenset()
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
                "DOCUMENT_PROVIDER_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "algorithm_version",
            _required_text(
                self.algorithm_version,
                "DOCUMENT_ALGORITHM_VERSION_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "document_type",
            IdentityDocumentType(self.document_type),
        )
        object.__setattr__(
            self,
            "overall_score",
            _probability(
                self.overall_score,
                "INVALID_DOCUMENT_AUTHENTICITY_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "tampering_score",
            _probability(
                self.tampering_score,
                "INVALID_DOCUMENT_TAMPERING_SCORE",
            ),
        )

        for field_name in (
            "security_feature_score",
            "hologram_score",
            "portrait_integrity_score",
            "image_integrity_score",
            "layout_consistency_score",
        ):
            value = getattr(self, field_name)

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _probability(
                        value,
                        "INVALID_DOCUMENT_COMPONENT_SCORE",
                    ),
                )

        features = tuple(self.detected_features)
        feature_types = tuple(
            feature.feature for feature in features
        )

        if len(feature_types) != len(set(feature_types)):
            raise ValueError(
                "DUPLICATE_DOCUMENT_SECURITY_FEATURE"
            )

        indicators = frozenset(
            DocumentFraudIndicator(value)
            for value in self.fraud_indicators
        )

        if (
            DocumentFraudIndicator.NONE in indicators
            and len(indicators) > 1
        ):
            raise ValueError(
                "INCONSISTENT_DOCUMENT_FRAUD_INDICATORS"
            )

        object.__setattr__(
            self,
            "detected_features",
            features,
        )
        object.__setattr__(
            self,
            "fraud_indicators",
            indicators,
        )
        object.__setattr__(
            self,
            "provider_decision_reference",
            _optional_text(
                self.provider_decision_reference
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

    def severe_fraud_detected(self) -> bool:
        return bool(
            self.fraud_indicators
            & SEVERE_DOCUMENT_FRAUD_INDICATORS
        )


@dataclass(frozen=True)
class DocumentAuthenticityPolicy:
    authentic_threshold: float = 0.85
    manual_review_threshold: float = 0.65
    maximum_tampering_score: float = 0.30
    severe_tampering_score: float = 0.80
    minimum_security_feature_score: float = 0.65
    minimum_portrait_integrity_score: float = 0.65
    minimum_capture_quality_score: float = 0.70
    require_supported_template: bool = True
    require_mrz_consistency_for_passports: bool = True
    require_barcode_consistency_when_present: bool = True
    require_security_features: bool = True
    require_device_integrity: bool = False
    deny_emulators: bool = True
    deny_compromised_devices: bool = True
    fail_on_severe_fraud: bool = True

    def __post_init__(self) -> None:
        authentic = _probability(
            self.authentic_threshold,
            "INVALID_AUTHENTICITY_PASS_THRESHOLD",
        )
        review = _probability(
            self.manual_review_threshold,
            "INVALID_AUTHENTICITY_REVIEW_THRESHOLD",
        )
        maximum_tampering = _probability(
            self.maximum_tampering_score,
            "INVALID_TAMPERING_THRESHOLD",
        )
        severe_tampering = _probability(
            self.severe_tampering_score,
            "INVALID_SEVERE_TAMPERING_THRESHOLD",
        )
        security_feature = _probability(
            self.minimum_security_feature_score,
            "INVALID_SECURITY_FEATURE_THRESHOLD",
        )
        portrait_integrity = _probability(
            self.minimum_portrait_integrity_score,
            "INVALID_PORTRAIT_INTEGRITY_THRESHOLD",
        )
        capture_quality = _probability(
            self.minimum_capture_quality_score,
            "INVALID_DOCUMENT_CAPTURE_THRESHOLD",
        )

        if review >= authentic:
            raise ValueError(
                "INVALID_AUTHENTICITY_THRESHOLD_ORDER"
            )

        if severe_tampering <= maximum_tampering:
            raise ValueError(
                "INVALID_TAMPERING_THRESHOLD_ORDER"
            )

        object.__setattr__(
            self,
            "authentic_threshold",
            authentic,
        )
        object.__setattr__(
            self,
            "manual_review_threshold",
            review,
        )
        object.__setattr__(
            self,
            "maximum_tampering_score",
            maximum_tampering,
        )
        object.__setattr__(
            self,
            "severe_tampering_score",
            severe_tampering,
        )
        object.__setattr__(
            self,
            "minimum_security_feature_score",
            security_feature,
        )
        object.__setattr__(
            self,
            "minimum_portrait_integrity_score",
            portrait_integrity,
        )
        object.__setattr__(
            self,
            "minimum_capture_quality_score",
            capture_quality,
        )


@dataclass(frozen=True)
class DocumentAuthenticityAssessmentRecord:
    assessment_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    document_type: IdentityDocumentType
    decision: DocumentAuthenticityDecision
    overall_score: float
    tampering_score: float
    provider_reference: str
    algorithm_version: str
    document_version: int
    security_feature_score: float | None = None
    hologram_score: float | None = None
    portrait_integrity_score: float | None = None
    mrz_consistent: bool | None = None
    barcode_consistent: bool | None = None
    fraud_indicators: frozenset[
        DocumentFraudIndicator
    ] = frozenset()
    assessed_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "DOCUMENT_AUTHENTICITY_ASSESSMENT_ID_REQUIRED": (
                self.assessment_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "DOCUMENT_ID_REQUIRED": self.document_id,
            "DOCUMENT_PROVIDER_REFERENCE_REQUIRED": (
                self.provider_reference
            ),
            "DOCUMENT_ALGORITHM_VERSION_REQUIRED": (
                self.algorithm_version
            ),
        }

        for error_code, value in required.items():
            object.__setattr__(
                self,
                {
                    "DOCUMENT_AUTHENTICITY_ASSESSMENT_ID_REQUIRED":
                        "assessment_id",
                    "TENANT_ID_REQUIRED": "tenant_id",
                    "IDENTITY_ID_REQUIRED": "identity_id",
                    "DOCUMENT_ID_REQUIRED": "document_id",
                    "DOCUMENT_PROVIDER_REFERENCE_REQUIRED":
                        "provider_reference",
                    "DOCUMENT_ALGORITHM_VERSION_REQUIRED":
                        "algorithm_version",
                }[error_code],
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
            _probability(
                self.overall_score,
                "INVALID_DOCUMENT_AUTHENTICITY_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "tampering_score",
            _probability(
                self.tampering_score,
                "INVALID_DOCUMENT_TAMPERING_SCORE",
            ),
        )

        for field_name in (
            "security_feature_score",
            "hologram_score",
            "portrait_integrity_score",
        ):
            value = getattr(self, field_name)

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _probability(
                        value,
                        "INVALID_DOCUMENT_COMPONENT_SCORE",
                    ),
                )

        object.__setattr__(
            self,
            "fraud_indicators",
            frozenset(
                DocumentFraudIndicator(value)
                for value in self.fraud_indicators
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
    "DocumentAuthenticityAssessmentRecord",
    "DocumentAuthenticityPolicy",
    "DocumentAuthenticityProviderEvidence",
    "DocumentFraudIndicator",
    "DocumentSecurityFeature",
    "DocumentSecurityFeatureEvidence",
    "FORBIDDEN_DOCUMENT_AUTHENTICITY_FIELDS",
    "SEVERE_DOCUMENT_FRAUD_INDICATORS",
]
