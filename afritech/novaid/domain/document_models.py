from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any, Mapping

from .biometric_models import (
    BiometricPurpose,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
)
from .models import identifier, utcnow


class IdentityDocumentType(StrEnum):
    PASSPORT = "PASSPORT"
    NATIONAL_ID = "NATIONAL_ID"
    DRIVER_LICENCE = "DRIVER_LICENCE"
    RESIDENCE_PERMIT = "RESIDENCE_PERMIT"
    REFUGEE_TRAVEL_DOCUMENT = "REFUGEE_TRAVEL_DOCUMENT"
    VISA = "VISA"
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE"
    HEALTH_CARD = "HEALTH_CARD"
    OTHER_GOVERNMENT_ID = "OTHER_GOVERNMENT_ID"


class DocumentSide(StrEnum):
    FRONT = "FRONT"
    BACK = "BACK"
    BIO_DATA_PAGE = "BIO_DATA_PAGE"
    VISA_PAGE = "VISA_PAGE"
    SINGLE_PAGE = "SINGLE_PAGE"
    MULTI_PAGE = "MULTI_PAGE"


class DocumentCaptureChannel(StrEnum):
    MOBILE_CAMERA = "MOBILE_CAMERA"
    WEB_CAMERA = "WEB_CAMERA"
    FILE_UPLOAD = "FILE_UPLOAD"
    KIOSK = "KIOSK"
    ASSISTED_DESK = "ASSISTED_DESK"
    NFC = "NFC"
    API = "API"


class DocumentVerificationStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class DocumentVerificationDecision(StrEnum):
    PASS = "PASS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAIL = "FAIL"
    RECAPTURE = "RECAPTURE"


class DocumentAuthenticityDecision(StrEnum):
    AUTHENTIC = "AUTHENTIC"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    SUSPECTED_FRAUD = "SUSPECTED_FRAUD"
    UNREADABLE = "UNREADABLE"


class OCRFieldType(StrEnum):
    DOCUMENT_NUMBER = "DOCUMENT_NUMBER"
    GIVEN_NAMES = "GIVEN_NAMES"
    FAMILY_NAME = "FAMILY_NAME"
    FULL_NAME = "FULL_NAME"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    DATE_OF_ISSUE = "DATE_OF_ISSUE"
    DATE_OF_EXPIRY = "DATE_OF_EXPIRY"
    NATIONALITY = "NATIONALITY"
    SEX = "SEX"
    ADDRESS = "ADDRESS"
    ISSUING_AUTHORITY = "ISSUING_AUTHORITY"
    PERSONAL_NUMBER = "PERSONAL_NUMBER"
    PLACE_OF_BIRTH = "PLACE_OF_BIRTH"
    DOCUMENT_TYPE = "DOCUMENT_TYPE"


class MachineReadableZoneType(StrEnum):
    TD1 = "TD1"
    TD2 = "TD2"
    TD3 = "TD3"
    MRVA = "MRVA"
    MRVB = "MRVB"
    UNKNOWN = "UNKNOWN"


class BarcodeType(StrEnum):
    PDF417 = "PDF417"
    QR_CODE = "QR_CODE"
    DATA_MATRIX = "DATA_MATRIX"
    AZTEC = "AZTEC"
    CODE_128 = "CODE_128"
    UNKNOWN = "UNKNOWN"


DOCUMENT_STATUS_TRANSITIONS: dict[
    DocumentVerificationStatus,
    frozenset[DocumentVerificationStatus],
] = {
    DocumentVerificationStatus.PENDING: frozenset(
        {
            DocumentVerificationStatus.IN_PROGRESS,
            DocumentVerificationStatus.CANCELLED,
            DocumentVerificationStatus.EXPIRED,
        }
    ),
    DocumentVerificationStatus.IN_PROGRESS: frozenset(
        {
            DocumentVerificationStatus.MANUAL_REVIEW,
            DocumentVerificationStatus.VERIFIED,
            DocumentVerificationStatus.REJECTED,
            DocumentVerificationStatus.CANCELLED,
            DocumentVerificationStatus.EXPIRED,
        }
    ),
    DocumentVerificationStatus.MANUAL_REVIEW: frozenset(
        {
            DocumentVerificationStatus.VERIFIED,
            DocumentVerificationStatus.REJECTED,
            DocumentVerificationStatus.CANCELLED,
            DocumentVerificationStatus.EXPIRED,
        }
    ),
    DocumentVerificationStatus.VERIFIED: frozenset(
        {
            DocumentVerificationStatus.EXPIRED,
        }
    ),
    DocumentVerificationStatus.REJECTED: frozenset(),
    DocumentVerificationStatus.EXPIRED: frozenset(),
    DocumentVerificationStatus.CANCELLED: frozenset(),
}


FORBIDDEN_DOCUMENT_METADATA_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "document_image",
        "raw_document",
        "raw_selfie",
        "selfie",
        "raw_video",
        "video",
        "frames",
        "embedding",
        "embeddings",
        "feature_vector",
        "feature_vectors",
        "nfc_dump",
        "raw_nfc",
        "barcode_payload",
        "mrz_raw",
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
    if isinstance(value, bool) or not isinstance(
        value,
        int | float,
    ):
        raise ValueError(error_code)

    normalized = float(value)

    if not 0.0 <= normalized <= 1.0:
        raise ValueError(error_code)

    return normalized


def _country_code(
    value: str,
    error_code: str = "INVALID_COUNTRY_CODE",
) -> str:
    normalized = _required_text(
        value,
        error_code,
    ).upper()

    if len(normalized) != 2 or not normalized.isalpha():
        raise ValueError(error_code)

    return normalized


def _date_value(
    value: date | str | None,
    error_code: str,
) -> date | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(error_code) from exc

    raise ValueError(error_code)


def _assert_safe_metadata(
    metadata: Mapping[str, Any],
) -> None:
    forbidden = {
        str(key).strip().lower()
        for key in metadata
    } & FORBIDDEN_DOCUMENT_METADATA_FIELDS

    if forbidden:
        raise ValueError(
            "RAW_DOCUMENT_MATERIAL_FORBIDDEN"
        )


@dataclass(frozen=True)
class DocumentCaptureReference:
    capture_id: str
    side: DocumentSide
    channel: DocumentCaptureChannel
    encrypted_object_reference: str
    media_type: str
    checksum_sha256: str
    captured_at: datetime = field(default_factory=utcnow)
    capture_device: CaptureDevice | None = None
    capture_environment: CaptureEnvironment | None = None
    capture_quality: CaptureQuality | None = None
    page_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capture_id",
            _required_text(
                self.capture_id,
                "DOCUMENT_CAPTURE_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "side",
            DocumentSide(self.side),
        )
        object.__setattr__(
            self,
            "channel",
            DocumentCaptureChannel(self.channel),
        )
        object.__setattr__(
            self,
            "encrypted_object_reference",
            _required_text(
                self.encrypted_object_reference,
                "DOCUMENT_OBJECT_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "media_type",
            _required_text(
                self.media_type,
                "DOCUMENT_MEDIA_TYPE_REQUIRED",
            ).lower(),
        )

        checksum = _required_text(
            self.checksum_sha256,
            "DOCUMENT_CHECKSUM_REQUIRED",
        ).lower()

        if (
            len(checksum) != 64
            or any(
                character not in "0123456789abcdef"
                for character in checksum
            )
        ):
            raise ValueError(
                "INVALID_DOCUMENT_CHECKSUM"
            )

        object.__setattr__(
            self,
            "checksum_sha256",
            checksum,
        )

        if self.page_number is not None:
            if (
                isinstance(self.page_number, bool)
                or not isinstance(self.page_number, int)
                or self.page_number < 1
            ):
                raise ValueError(
                    "INVALID_DOCUMENT_PAGE_NUMBER"
                )

        metadata = dict(self.metadata)
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class OCRField:
    field_type: OCRFieldType
    value: str
    confidence_score: float
    source_reference: str | None = None
    normalized_value: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "field_type",
            OCRFieldType(self.field_type),
        )
        object.__setattr__(
            self,
            "value",
            _required_text(
                self.value,
                "OCR_FIELD_VALUE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _probability(
                self.confidence_score,
                "INVALID_OCR_CONFIDENCE_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "source_reference",
            _optional_text(
                self.source_reference
            ),
        )
        object.__setattr__(
            self,
            "normalized_value",
            _optional_text(
                self.normalized_value
            ),
        )


@dataclass(frozen=True)
class MachineReadableZoneEvidence:
    mrz_type: MachineReadableZoneType
    document_code: str
    issuing_country_code: str
    document_number: str
    nationality_code: str | None
    date_of_birth: date | str | None
    expiry_date: date | str | None
    checksums_valid: bool
    confidence_score: float
    provider_reference: str
    algorithm_version: str
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "mrz_type",
            MachineReadableZoneType(self.mrz_type),
        )
        object.__setattr__(
            self,
            "document_code",
            _required_text(
                self.document_code,
                "MRZ_DOCUMENT_CODE_REQUIRED",
            ).upper(),
        )
        object.__setattr__(
            self,
            "issuing_country_code",
            _required_text(
                self.issuing_country_code,
                "MRZ_ISSUING_COUNTRY_REQUIRED",
            ).upper(),
        )
        object.__setattr__(
            self,
            "document_number",
            _required_text(
                self.document_number,
                "MRZ_DOCUMENT_NUMBER_REQUIRED",
            ).upper(),
        )

        nationality = _optional_text(
            self.nationality_code
        )

        object.__setattr__(
            self,
            "nationality_code",
            nationality.upper()
            if nationality is not None
            else None,
        )
        object.__setattr__(
            self,
            "date_of_birth",
            _date_value(
                self.date_of_birth,
                "INVALID_MRZ_DATE_OF_BIRTH",
            ),
        )
        object.__setattr__(
            self,
            "expiry_date",
            _date_value(
                self.expiry_date,
                "INVALID_MRZ_EXPIRY_DATE",
            ),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _probability(
                self.confidence_score,
                "INVALID_MRZ_CONFIDENCE_SCORE",
            ),
        )
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
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class BarcodeEvidence:
    barcode_type: BarcodeType
    checksum_valid: bool | None
    confidence_score: float
    provider_reference: str
    algorithm_version: str
    extracted_fields: tuple[OCRField, ...] = ()
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "barcode_type",
            BarcodeType(self.barcode_type),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _probability(
                self.confidence_score,
                "INVALID_BARCODE_CONFIDENCE_SCORE",
            ),
        )
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
            "extracted_fields",
            tuple(self.extracted_fields),
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
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class DocumentExtractedData:
    document_number: str | None = None
    given_names: tuple[str, ...] = ()
    family_name: str | None = None
    full_name: str | None = None
    date_of_birth: date | str | None = None
    date_of_issue: date | str | None = None
    date_of_expiry: date | str | None = None
    nationality_code: str | None = None
    issuing_country_code: str | None = None
    issuing_authority: str | None = None
    sex: str | None = None
    address: str | None = None
    place_of_birth: str | None = None
    fields: tuple[OCRField, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "document_number",
            _optional_text(self.document_number),
        )

        normalized_names = tuple(
            name.strip()
            for name in self.given_names
            if isinstance(name, str)
            and name.strip()
        )

        object.__setattr__(
            self,
            "given_names",
            normalized_names,
        )
        object.__setattr__(
            self,
            "family_name",
            _optional_text(self.family_name),
        )
        object.__setattr__(
            self,
            "full_name",
            _optional_text(self.full_name),
        )
        object.__setattr__(
            self,
            "date_of_birth",
            _date_value(
                self.date_of_birth,
                "INVALID_DOCUMENT_DATE_OF_BIRTH",
            ),
        )
        object.__setattr__(
            self,
            "date_of_issue",
            _date_value(
                self.date_of_issue,
                "INVALID_DOCUMENT_DATE_OF_ISSUE",
            ),
        )
        object.__setattr__(
            self,
            "date_of_expiry",
            _date_value(
                self.date_of_expiry,
                "INVALID_DOCUMENT_DATE_OF_EXPIRY",
            ),
        )

        nationality = _optional_text(
            self.nationality_code
        )
        issuing_country = _optional_text(
            self.issuing_country_code
        )

        object.__setattr__(
            self,
            "nationality_code",
            nationality.upper()
            if nationality is not None
            else None,
        )
        object.__setattr__(
            self,
            "issuing_country_code",
            (
                _country_code(issuing_country)
                if issuing_country is not None
                else None
            ),
        )
        object.__setattr__(
            self,
            "issuing_authority",
            _optional_text(
                self.issuing_authority
            ),
        )
        object.__setattr__(
            self,
            "sex",
            (
                _optional_text(self.sex).upper()
                if _optional_text(self.sex)
                else None
            ),
        )
        object.__setattr__(
            self,
            "address",
            _optional_text(self.address),
        )
        object.__setattr__(
            self,
            "place_of_birth",
            _optional_text(
                self.place_of_birth
            ),
        )
        object.__setattr__(
            self,
            "fields",
            tuple(self.fields),
        )

        if (
            self.date_of_issue is not None
            and self.date_of_expiry is not None
            and self.date_of_expiry
            <= self.date_of_issue
        ):
            raise ValueError(
                "INVALID_DOCUMENT_VALIDITY_PERIOD"
            )


@dataclass(frozen=True)
class DocumentAuthenticityEvidence:
    decision: DocumentAuthenticityDecision
    overall_score: float
    tampering_score: float
    security_feature_score: float | None = None
    hologram_score: float | None = None
    portrait_integrity_score: float | None = None
    mrz_consistent: bool | None = None
    barcode_consistent: bool | None = None
    provider_reference: str = ""
    algorithm_version: str = ""
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "decision",
            DocumentAuthenticityDecision(
                self.decision
            ),
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
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


@dataclass(frozen=True)
class IdentityDocument:
    document_id: str
    tenant_id: str
    identity_id: str
    document_type: IdentityDocumentType
    issuing_country_code: str
    status: DocumentVerificationStatus = (
        DocumentVerificationStatus.PENDING
    )
    purpose: BiometricPurpose = BiometricPurpose.EKYC
    document_number_reference: str | None = None
    captures: tuple[DocumentCaptureReference, ...] = ()
    extracted_data: DocumentExtractedData | None = None
    mrz_evidence: MachineReadableZoneEvidence | None = None
    barcode_evidence: BarcodeEvidence | None = None
    authenticity_evidence: (
        DocumentAuthenticityEvidence | None
    ) = None
    provider_reference: str | None = None
    algorithm_version: str | None = None
    issued_at: date | str | None = None
    expires_at: date | str | None = None
    verified_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "document_id",
            _required_text(
                self.document_id,
                "DOCUMENT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "TENANT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "identity_id",
            _required_text(
                self.identity_id,
                "IDENTITY_ID_REQUIRED",
            ),
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
            "issuing_country_code",
            _country_code(
                self.issuing_country_code
            ),
        )
        object.__setattr__(
            self,
            "status",
            DocumentVerificationStatus(
                self.status
            ),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "document_number_reference",
            _optional_text(
                self.document_number_reference
            ),
        )
        object.__setattr__(
            self,
            "captures",
            tuple(self.captures),
        )
        object.__setattr__(
            self,
            "provider_reference",
            _optional_text(
                self.provider_reference
            ),
        )
        object.__setattr__(
            self,
            "algorithm_version",
            _optional_text(
                self.algorithm_version
            ),
        )
        object.__setattr__(
            self,
            "issued_at",
            _date_value(
                self.issued_at,
                "INVALID_DOCUMENT_ISSUE_DATE",
            ),
        )
        object.__setattr__(
            self,
            "expires_at",
            _date_value(
                self.expires_at,
                "INVALID_DOCUMENT_EXPIRY_DATE",
            ),
        )

        if self.version < 1:
            raise ValueError(
                "INVALID_AGGREGATE_VERSION"
            )

        if (
            self.issued_at is not None
            and self.expires_at is not None
            and self.expires_at <= self.issued_at
        ):
            raise ValueError(
                "INVALID_DOCUMENT_VALIDITY_PERIOD"
            )

        capture_ids = [
            capture.capture_id
            for capture in self.captures
        ]

        if len(capture_ids) != len(set(capture_ids)):
            raise ValueError(
                "DUPLICATE_DOCUMENT_CAPTURE"
            )

        if (
            self.status
            is DocumentVerificationStatus.VERIFIED
            and self.verified_at is None
        ):
            raise ValueError(
                "DOCUMENT_VERIFIED_AT_REQUIRED"
            )

        metadata = dict(self.metadata)
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    def is_expired(
        self,
        *,
        at: date | datetime | None = None,
    ) -> bool:
        if self.expires_at is None:
            return False

        if at is None:
            moment = datetime.now(UTC).date()
        elif isinstance(at, datetime):
            moment = at.date()
        else:
            moment = at

        return moment >= self.expires_at

    def transition(
        self,
        target: DocumentVerificationStatus | str,
        *,
        at: datetime | None = None,
    ) -> IdentityDocument:
        normalized_target = (
            DocumentVerificationStatus(target)
        )

        if (
            normalized_target
            not in DOCUMENT_STATUS_TRANSITIONS[
                self.status
            ]
        ):
            raise ValueError(
                "INVALID_DOCUMENT_STATUS_TRANSITION"
            )

        moment = at or utcnow()
        changes: dict[str, Any] = {
            "status": normalized_target,
            "updated_at": moment,
            "version": self.version + 1,
        }

        if (
            normalized_target
            is DocumentVerificationStatus.VERIFIED
        ):
            changes["verified_at"] = moment

        return replace(
            self,
            **changes,
        )


@dataclass(frozen=True)
class DocumentVerificationEvidence:
    evidence_id: str
    tenant_id: str
    identity_id: str
    document_id: str
    decision: DocumentVerificationDecision
    document_type: IdentityDocumentType
    issuing_country_code: str
    provider_reference: str
    algorithm_version: str
    overall_score: float
    authenticity_score: float | None = None
    data_consistency_score: float | None = None
    portrait_reference: str | None = None
    reason_codes: tuple[str, ...] = ()
    evaluated_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, error_code in (
            (
                self.evidence_id,
                "DOCUMENT_EVIDENCE_ID_REQUIRED",
            ),
            (
                self.tenant_id,
                "TENANT_ID_REQUIRED",
            ),
            (
                self.identity_id,
                "IDENTITY_ID_REQUIRED",
            ),
            (
                self.document_id,
                "DOCUMENT_ID_REQUIRED",
            ),
            (
                self.provider_reference,
                "DOCUMENT_PROVIDER_REFERENCE_REQUIRED",
            ),
            (
                self.algorithm_version,
                "DOCUMENT_ALGORITHM_VERSION_REQUIRED",
            ),
        ):
            _required_text(value, error_code)

        object.__setattr__(
            self,
            "decision",
            DocumentVerificationDecision(
                self.decision
            ),
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
            "issuing_country_code",
            _country_code(
                self.issuing_country_code
            ),
        )
        object.__setattr__(
            self,
            "overall_score",
            _probability(
                self.overall_score,
                "INVALID_DOCUMENT_VERIFICATION_SCORE",
            ),
        )

        for field_name in (
            "authenticity_score",
            "data_consistency_score",
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
            "portrait_reference",
            _optional_text(
                self.portrait_reference
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

        metadata = dict(self.metadata)
        _assert_safe_metadata(metadata)

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )


def new_document_id() -> str:
    return identifier()


def new_document_capture_id() -> str:
    return identifier()


def new_document_evidence_id() -> str:
    return identifier()


__all__ = [
    "BarcodeEvidence",
    "BarcodeType",
    "DOCUMENT_STATUS_TRANSITIONS",
    "DocumentAuthenticityDecision",
    "DocumentAuthenticityEvidence",
    "DocumentCaptureChannel",
    "DocumentCaptureReference",
    "DocumentExtractedData",
    "DocumentSide",
    "DocumentVerificationDecision",
    "DocumentVerificationEvidence",
    "DocumentVerificationStatus",
    "FORBIDDEN_DOCUMENT_METADATA_FIELDS",
    "IdentityDocument",
    "IdentityDocumentType",
    "MachineReadableZoneEvidence",
    "MachineReadableZoneType",
    "OCRField",
    "OCRFieldType",
    "new_document_capture_id",
    "new_document_evidence_id",
    "new_document_id",
]
