from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Mapping

from .document_models import (
    BarcodeEvidence,
    DocumentExtractedData,
    IdentityDocumentType,
    MachineReadableZoneEvidence,
    OCRField,
    OCRFieldType,
)
from .models import utcnow


class OCRExtractionDecision(StrEnum):
    ACCEPT = "ACCEPT"
    PARTIAL = "PARTIAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    RECAPTURE = "RECAPTURE"
    REJECT = "REJECT"


class OCRExtractionSource(StrEnum):
    VISUAL_TEXT = "VISUAL_TEXT"
    MRZ = "MRZ"
    BARCODE = "BARCODE"
    NFC = "NFC"
    COMBINED = "COMBINED"


FORBIDDEN_OCR_PAYLOAD_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "image_bytes",
        "raw_document",
        "raw_selfie",
        "raw_video",
        "video",
        "frames",
        "raw_text",
        "full_provider_response",
        "provider_payload",
        "barcode_payload",
        "mrz_raw",
        "raw_mrz",
        "nfc_dump",
        "raw_nfc",
        "embedding",
        "feature_vector",
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


def _assert_safe_payload(
    payload: Mapping[str, Any],
) -> None:
    forbidden = {
        str(key).strip().lower()
        for key in payload
    } & FORBIDDEN_OCR_PAYLOAD_FIELDS

    if forbidden:
        raise ValueError(
            "RAW_DOCUMENT_MATERIAL_FORBIDDEN"
        )


@dataclass(frozen=True)
class OCRProviderEvidence:
    provider_reference: str
    algorithm_version: str
    source: OCRExtractionSource
    document_type: IdentityDocumentType
    overall_confidence_score: float
    fields: tuple[OCRField, ...]
    extracted_data: DocumentExtractedData
    mrz_evidence: MachineReadableZoneEvidence | None = None
    barcode_evidence: BarcodeEvidence | None = None
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
            "source",
            OCRExtractionSource(self.source),
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
            "overall_confidence_score",
            _probability(
                self.overall_confidence_score,
                "INVALID_OCR_CONFIDENCE_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "fields",
            tuple(self.fields),
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
                    reason.strip().upper()
                    for reason in self.reason_codes
                    if isinstance(reason, str)
                    and reason.strip()
                )
            ),
        )

        field_types = [
            field.field_type
            for field in self.fields
        ]

        if len(field_types) != len(set(field_types)):
            raise ValueError(
                "DUPLICATE_OCR_FIELD_TYPE"
            )

        metadata = dict(self.metadata)
        _assert_safe_payload(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class OCRExtractionPolicy:
    acceptance_threshold: float = 0.85
    manual_review_threshold: float = 0.65
    minimum_required_field_confidence: float = 0.70
    minimum_capture_quality_score: float = 0.70
    require_document_number: bool = True
    require_name: bool = True
    require_date_of_birth: bool = True
    require_expiry_for_expiring_documents: bool = True
    require_valid_mrz_checksums_for_passports: bool = True
    require_device_integrity: bool = False
    deny_emulators: bool = True
    deny_compromised_devices: bool = True

    def __post_init__(self) -> None:
        acceptance = _probability(
            self.acceptance_threshold,
            "INVALID_OCR_ACCEPTANCE_THRESHOLD",
        )
        review = _probability(
            self.manual_review_threshold,
            "INVALID_OCR_REVIEW_THRESHOLD",
        )
        field_confidence = _probability(
            self.minimum_required_field_confidence,
            "INVALID_OCR_FIELD_THRESHOLD",
        )
        capture_quality = _probability(
            self.minimum_capture_quality_score,
            "INVALID_OCR_CAPTURE_THRESHOLD",
        )

        if review >= acceptance:
            raise ValueError(
                "INVALID_OCR_THRESHOLD_ORDER"
            )

        object.__setattr__(
            self,
            "acceptance_threshold",
            acceptance,
        )
        object.__setattr__(
            self,
            "manual_review_threshold",
            review,
        )
        object.__setattr__(
            self,
            "minimum_required_field_confidence",
            field_confidence,
        )
        object.__setattr__(
            self,
            "minimum_capture_quality_score",
            capture_quality,
        )


@dataclass(frozen=True)
class OCRExtractionRecord:
    extraction_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    document_type: IdentityDocumentType
    decision: OCRExtractionDecision
    source: OCRExtractionSource
    overall_confidence_score: float
    extracted_data: DocumentExtractedData
    provider_reference: str
    algorithm_version: str
    document_version: int
    fields: tuple[OCRField, ...] = ()
    mrz_evidence: MachineReadableZoneEvidence | None = None
    barcode_evidence: BarcodeEvidence | None = None
    extracted_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "OCR_EXTRACTION_ID_REQUIRED": self.extraction_id,
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
            normalized = _required_text(
                value,
                error_code,
            )
            field_name = {
                "OCR_EXTRACTION_ID_REQUIRED": "extraction_id",
                "TENANT_ID_REQUIRED": "tenant_id",
                "IDENTITY_ID_REQUIRED": "identity_id",
                "DOCUMENT_ID_REQUIRED": "document_id",
                "DOCUMENT_PROVIDER_REFERENCE_REQUIRED": (
                    "provider_reference"
                ),
                "DOCUMENT_ALGORITHM_VERSION_REQUIRED": (
                    "algorithm_version"
                ),
            }[error_code]

            object.__setattr__(
                self,
                field_name,
                normalized,
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
            _probability(
                self.overall_confidence_score,
                "INVALID_OCR_CONFIDENCE_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "fields",
            tuple(self.fields),
        )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(
                dict.fromkeys(
                    reason.strip().upper()
                    for reason in self.reason_codes
                    if isinstance(reason, str)
                    and reason.strip()
                )
            ),
        )

        metadata = dict(self.metadata)
        _assert_safe_payload(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


def required_ocr_field_types(
    document_type: IdentityDocumentType,
) -> frozenset[OCRFieldType]:
    if document_type is IdentityDocumentType.PASSPORT:
        return frozenset(
            {
                OCRFieldType.DOCUMENT_NUMBER,
                OCRFieldType.FAMILY_NAME,
                OCRFieldType.DATE_OF_BIRTH,
                OCRFieldType.DATE_OF_EXPIRY,
            }
        )

    if document_type is IdentityDocumentType.DRIVER_LICENCE:
        return frozenset(
            {
                OCRFieldType.DOCUMENT_NUMBER,
                OCRFieldType.FULL_NAME,
                OCRFieldType.DATE_OF_BIRTH,
                OCRFieldType.DATE_OF_EXPIRY,
            }
        )

    if document_type is IdentityDocumentType.NATIONAL_ID:
        return frozenset(
            {
                OCRFieldType.DOCUMENT_NUMBER,
                OCRFieldType.FULL_NAME,
                OCRFieldType.DATE_OF_BIRTH,
            }
        )

    return frozenset(
        {
            OCRFieldType.DOCUMENT_NUMBER,
            OCRFieldType.FULL_NAME,
        }
    )


__all__ = [
    "FORBIDDEN_OCR_PAYLOAD_FIELDS",
    "OCRExtractionDecision",
    "OCRExtractionPolicy",
    "OCRExtractionRecord",
    "OCRExtractionSource",
    "OCRProviderEvidence",
    "required_ocr_field_types",
]
