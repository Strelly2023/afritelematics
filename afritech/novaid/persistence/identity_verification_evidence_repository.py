from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable


class IdentityVerificationEvidenceType(str, Enum):
    OCR_EXTRACTION = "OCR_EXTRACTION"
    DOCUMENT_AUTHENTICITY = "DOCUMENT_AUTHENTICITY"
    DOCUMENT_SELFIE_MATCH = "DOCUMENT_SELFIE_MATCH"
    LIVENESS_ASSESSMENT = "LIVENESS_ASSESSMENT"


FORBIDDEN_EVIDENCE_REFERENCE_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "image_bytes",
        "document_bytes",
        "raw_document",
        "raw_selfie",
        "selfie_bytes",
        "raw_video",
        "video_bytes",
        "raw_frames",
        "raw_text",
        "raw_mrz",
        "barcode_payload",
        "raw_barcode",
        "provider_payload",
        "provider_response",
        "full_provider_response",
        "embedding",
        "embeddings",
        "face_embedding",
        "biometric_template",
        "template_bytes",
        "api_key",
        "private_key",
        "provider_secret",
        "access_token",
        "refresh_token",
        "password",
        "credential",
        "secret",
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


def _positive_integer(
    value: int,
    error_code: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise ValueError(error_code)

    return value


def _aware_datetime(
    value: datetime,
    error_code: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(error_code)

    if value.tzinfo is None:
        raise ValueError(error_code)

    return value


def _assert_safe_metadata(
    metadata: Mapping[str, Any],
) -> None:
    if not isinstance(metadata, Mapping):
        raise ValueError(
            "EVIDENCE_REFERENCE_METADATA_MAPPING_REQUIRED"
        )

    def walk(
        value: object,
        *,
        path: str = "$",
    ) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                normalized = str(key).strip().lower()

                if normalized in FORBIDDEN_EVIDENCE_REFERENCE_FIELDS:
                    raise ValueError(
                        "RAW_EVIDENCE_REFERENCE_MATERIAL_FORBIDDEN:"
                        f"{path}.{normalized}"
                    )

                walk(
                    nested,
                    path=f"{path}.{normalized}",
                )

            return

        if isinstance(
            value,
            (list, tuple, set, frozenset),
        ):
            for index, nested in enumerate(value):
                walk(
                    nested,
                    path=f"{path}[{index}]",
                )

    walk(metadata)


@dataclass(frozen=True, slots=True)
class IdentityVerificationEvidenceReference:
    tenant_id: str
    verification_id: str
    evidence_type: IdentityVerificationEvidenceType
    evidence_id: str
    evidence_version: int
    collected_at: datetime
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
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
            "verification_id",
            _required_text(
                self.verification_id,
                "IDENTITY_VERIFICATION_ID_REQUIRED",
            ),
        )

        if not isinstance(
            self.evidence_type,
            IdentityVerificationEvidenceType,
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_EVIDENCE_TYPE"
            )

        object.__setattr__(
            self,
            "evidence_id",
            _required_text(
                self.evidence_id,
                "IDENTITY_VERIFICATION_EVIDENCE_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "evidence_version",
            _positive_integer(
                self.evidence_version,
                "INVALID_IDENTITY_VERIFICATION_EVIDENCE_VERSION",
            ),
        )
        object.__setattr__(
            self,
            "collected_at",
            _aware_datetime(
                self.collected_at,
                "IDENTITY_VERIFICATION_EVIDENCE_TIMESTAMP_REQUIRED",
            ),
        )

        _assert_safe_metadata(self.metadata)

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@runtime_checkable
class IdentityVerificationEvidenceRepository(Protocol):
    def add_evidence_reference(
        self,
        reference: IdentityVerificationEvidenceReference,
    ) -> None:
        ...

    def get_evidence_reference(
        self,
        *,
        tenant_id: str,
        verification_id: str,
        evidence_type: IdentityVerificationEvidenceType,
    ) -> IdentityVerificationEvidenceReference | None:
        ...

    def list_verification_evidence(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> tuple[
        IdentityVerificationEvidenceReference,
        ...,
    ]:
        ...

    def evidence_reference_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
        evidence_type: IdentityVerificationEvidenceType,
    ) -> bool:
        ...


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


__all__ = [
    "FORBIDDEN_EVIDENCE_REFERENCE_FIELDS",
    "IdentityVerificationEvidenceReference",
    "IdentityVerificationEvidenceRepository",
    "IdentityVerificationEvidenceType",
    "utc_now",
]
