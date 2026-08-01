from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationEvidence,
    IdentityVerificationRecord,
)
from afritech.novaid.persistence.identity_verification_evidence_repository import (
    IdentityVerificationEvidenceReference,
    IdentityVerificationEvidenceType,
)


class IdentityVerificationEvidenceFactoryError(
    ValueError
):
    """Raised when governed evidence cannot be referenced safely."""


def build_identity_verification_evidence_references(
    *,
    verification: IdentityVerificationRecord,
    evidence: IdentityVerificationEvidence,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[
    IdentityVerificationEvidenceReference,
    ...,
]:
    if not isinstance(
        verification,
        IdentityVerificationRecord,
    ):
        raise IdentityVerificationEvidenceFactoryError(
            "IDENTITY_VERIFICATION_RECORD_REQUIRED"
        )

    if not isinstance(
        evidence,
        IdentityVerificationEvidence,
    ):
        raise IdentityVerificationEvidenceFactoryError(
            "IDENTITY_VERIFICATION_EVIDENCE_REQUIRED"
        )

    _assert_common_bindings(
        verification=verification,
        evidence=evidence,
    )

    shared_metadata = _build_shared_metadata(
        evidence=evidence,
        metadata=metadata,
    )

    references = (
        IdentityVerificationEvidenceReference(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
            evidence_type=(
                IdentityVerificationEvidenceType.OCR_EXTRACTION
            ),
            evidence_id=(
                evidence.ocr_extraction.extraction_id
            ),
            evidence_version=evidence.evidence_version,
            collected_at=evidence.collected_at,
            metadata={
                **shared_metadata,
                "source_record_type": "OCRExtractionRecord",
                "algorithm_version": (
                    evidence.ocr_extraction.algorithm_version
                ),
                "provider_reference": (
                    evidence.ocr_extraction.provider_reference
                ),
                "recorded_at": (
                    evidence.ocr_extraction.extracted_at.isoformat()
                ),
            },
        ),
        IdentityVerificationEvidenceReference(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
            evidence_type=(
                IdentityVerificationEvidenceType
                .DOCUMENT_AUTHENTICITY
            ),
            evidence_id=(
                evidence.authenticity_assessment.assessment_id
            ),
            evidence_version=evidence.evidence_version,
            collected_at=evidence.collected_at,
            metadata={
                **shared_metadata,
                "source_record_type": (
                    "DocumentAuthenticityAssessmentRecord"
                ),
                "algorithm_version": (
                    evidence.authenticity_assessment
                    .algorithm_version
                ),
                "provider_reference": (
                    evidence.authenticity_assessment
                    .provider_reference
                ),
                "recorded_at": (
                    evidence.authenticity_assessment
                    .assessed_at
                    .isoformat()
                ),
            },
        ),
        IdentityVerificationEvidenceReference(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
            evidence_type=(
                IdentityVerificationEvidenceType
                .DOCUMENT_SELFIE_MATCH
            ),
            evidence_id=evidence.selfie_match.match_id,
            evidence_version=evidence.evidence_version,
            collected_at=evidence.collected_at,
            metadata={
                **shared_metadata,
                "source_record_type": (
                    "DocumentSelfieMatchRecord"
                ),
                "algorithm_version": (
                    evidence.selfie_match.algorithm_version
                ),
                "provider_reference": (
                    evidence.selfie_match.provider_reference
                ),
                "recorded_at": (
                    evidence.selfie_match.matched_at.isoformat()
                ),
            },
        ),
        IdentityVerificationEvidenceReference(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
            evidence_type=(
                IdentityVerificationEvidenceType
                .LIVENESS_ASSESSMENT
            ),
            evidence_id=(
                evidence.selfie_match.liveness_assessment_id
            ),
            evidence_version=evidence.evidence_version,
            collected_at=evidence.collected_at,
            metadata={
                **shared_metadata,
                "source_record_type": (
                    "DocumentSelfieMatchRecord"
                ),
                "source_field": "liveness_assessment_id",
                "algorithm_version": (
                    evidence.selfie_match.algorithm_version
                ),
                "recorded_at": (
                    evidence.selfie_match.matched_at.isoformat()
                ),
            },
        ),
    )

    _assert_unique_references(references)

    return tuple(
        sorted(
            references,
            key=lambda item: (
                item.evidence_type.value,
                item.evidence_id,
            ),
        )
    )


def _assert_common_bindings(
    *,
    verification: IdentityVerificationRecord,
    evidence: IdentityVerificationEvidence,
) -> None:
    ocr = evidence.ocr_extraction
    authenticity = evidence.authenticity_assessment
    selfie = evidence.selfie_match

    _assert_equal(
        evidence.workflow_id,
        verification.workflow_id,
        "IDENTITY_VERIFICATION_EVIDENCE_WORKFLOW_MISMATCH",
    )

    for actual, error_code in (
        (
            ocr.tenant_id,
            "OCR_EVIDENCE_TENANT_MISMATCH",
        ),
        (
            authenticity.tenant_id,
            "AUTHENTICITY_EVIDENCE_TENANT_MISMATCH",
        ),
        (
            selfie.tenant_id,
            "SELFIE_MATCH_EVIDENCE_TENANT_MISMATCH",
        ),
    ):
        _assert_equal(
            actual,
            verification.tenant_id,
            error_code,
        )

    for actual, error_code in (
        (
            ocr.identity_id,
            "OCR_EVIDENCE_IDENTITY_MISMATCH",
        ),
        (
            authenticity.identity_id,
            "AUTHENTICITY_EVIDENCE_IDENTITY_MISMATCH",
        ),
        (
            selfie.identity_id,
            "SELFIE_MATCH_EVIDENCE_IDENTITY_MISMATCH",
        ),
    ):
        _assert_equal(
            actual,
            verification.identity_id,
            error_code,
        )

    for actual, error_code in (
        (
            ocr.document_id,
            "OCR_EVIDENCE_DOCUMENT_MISMATCH",
        ),
        (
            authenticity.document_id,
            "AUTHENTICITY_EVIDENCE_DOCUMENT_MISMATCH",
        ),
        (
            selfie.document_id,
            "SELFIE_MATCH_EVIDENCE_DOCUMENT_MISMATCH",
        ),
    ):
        _assert_equal(
            actual,
            verification.document_id,
            error_code,
        )

    for actual, error_code in (
        (
            ocr.document_type,
            "OCR_EVIDENCE_DOCUMENT_TYPE_MISMATCH",
        ),
        (
            authenticity.document_type,
            "AUTHENTICITY_EVIDENCE_DOCUMENT_TYPE_MISMATCH",
        ),
        (
            selfie.document_type,
            "SELFIE_MATCH_EVIDENCE_DOCUMENT_TYPE_MISMATCH",
        ),
    ):
        _assert_equal(
            actual,
            verification.document_type,
            error_code,
        )

    for actual, error_code in (
        (
            ocr.document_version,
            "OCR_EVIDENCE_DOCUMENT_VERSION_MISMATCH",
        ),
        (
            authenticity.document_version,
            "AUTHENTICITY_EVIDENCE_DOCUMENT_VERSION_MISMATCH",
        ),
        (
            selfie.document_version,
            "SELFIE_MATCH_EVIDENCE_DOCUMENT_VERSION_MISMATCH",
        ),
    ):
        _assert_equal(
            actual,
            verification.document_version,
            error_code,
        )

    _assert_equal(
        ocr.extraction_id,
        verification.ocr_extraction_id,
        "OCR_EVIDENCE_IDENTIFIER_MISMATCH",
    )
    _assert_equal(
        authenticity.assessment_id,
        verification.authenticity_assessment_id,
        "AUTHENTICITY_EVIDENCE_IDENTIFIER_MISMATCH",
    )
    _assert_equal(
        selfie.match_id,
        verification.selfie_match_id,
        "SELFIE_MATCH_EVIDENCE_IDENTIFIER_MISMATCH",
    )

    _required_text(
        selfie.liveness_assessment_id,
        "LIVENESS_ASSESSMENT_ID_REQUIRED",
    )


def _build_shared_metadata(
    *,
    evidence: IdentityVerificationEvidence,
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if metadata is not None and not isinstance(
        metadata,
        Mapping,
    ):
        raise IdentityVerificationEvidenceFactoryError(
            "EVIDENCE_REFERENCE_METADATA_MAPPING_REQUIRED"
        )

    return {
        "workflow_id": evidence.workflow_id,
        "evidence_version": evidence.evidence_version,
        **dict(evidence.metadata),
        **dict(metadata or {}),
    }


def _assert_unique_references(
    references: tuple[
        IdentityVerificationEvidenceReference,
        ...,
    ],
) -> None:
    types = [
        item.evidence_type
        for item in references
    ]
    identifiers = [
        (
            item.evidence_type,
            item.evidence_id,
        )
        for item in references
    ]

    if len(types) != len(set(types)):
        raise IdentityVerificationEvidenceFactoryError(
            "DUPLICATE_IDENTITY_VERIFICATION_EVIDENCE_TYPE"
        )

    if len(identifiers) != len(set(identifiers)):
        raise IdentityVerificationEvidenceFactoryError(
            "DUPLICATE_IDENTITY_VERIFICATION_EVIDENCE_REFERENCE"
        )


def _assert_equal(
    actual: object,
    expected: object,
    error_code: str,
) -> None:
    if actual != expected:
        raise IdentityVerificationEvidenceFactoryError(
            error_code
        )


def _required_text(
    value: object,
    error_code: str,
) -> str:
    if not isinstance(value, str):
        raise IdentityVerificationEvidenceFactoryError(
            error_code
        )

    normalized = value.strip()

    if not normalized:
        raise IdentityVerificationEvidenceFactoryError(
            error_code
        )

    return normalized


__all__ = [
    "IdentityVerificationEvidenceFactoryError",
    "build_identity_verification_evidence_references",
]
