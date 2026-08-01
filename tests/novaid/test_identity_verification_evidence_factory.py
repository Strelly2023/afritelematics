from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from afritech.novaid.domain.biometric_models import (
    BiometricPurpose,
)
from afritech.novaid.domain.document_authenticity_models import (
    DocumentAuthenticityAssessmentRecord,
    DocumentAuthenticityDecision,
)
from afritech.novaid.domain.document_models import (
    DocumentExtractedData,
    IdentityDocumentType,
)
from afritech.novaid.domain.document_ocr_models import (
    OCRExtractionDecision,
    OCRExtractionRecord,
    OCRExtractionSource,
)
from afritech.novaid.domain.document_selfie_match_models import (
    DocumentSelfieMatchDecision,
    DocumentSelfieMatchRecord,
)
from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationDecision,
    IdentityVerificationEvidence,
    IdentityVerificationRecord,
)
from afritech.novaid.domain.models import AssuranceLevel
from afritech.novaid.persistence.identity_verification_evidence_factory import (
    IdentityVerificationEvidenceFactoryError,
    build_identity_verification_evidence_references,
)
from afritech.novaid.persistence.identity_verification_evidence_repository import (
    IdentityVerificationEvidenceType,
)


def uid() -> str:
    return str(uuid4())


def timestamp(minute: int = 0) -> datetime:
    return datetime(
        2026,
        8,
        1,
        10,
        minute,
        0,
        tzinfo=timezone.utc,
    )


def evidence_and_verification() -> tuple[
    IdentityVerificationEvidence,
    IdentityVerificationRecord,
]:
    tenant_id = uid()
    identity_id = uid()
    document_id = uid()
    workflow_id = uid()
    extraction_id = uid()
    assessment_id = uid()
    match_id = uid()
    liveness_id = uid()

    ocr = OCRExtractionRecord(
        extraction_id=extraction_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_type=IdentityDocumentType.PASSPORT,
        decision=OCRExtractionDecision.ACCEPT,
        source=next(iter(OCRExtractionSource)),
        overall_confidence_score=0.97,
        extracted_data=DocumentExtractedData(),
        provider_reference="provider://ocr/reference",
        algorithm_version="ocr-v1",
        document_version=1,
        extracted_at=timestamp(1),
    )

    authenticity = DocumentAuthenticityAssessmentRecord(
        assessment_id=assessment_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_type=IdentityDocumentType.PASSPORT,
        decision=DocumentAuthenticityDecision.AUTHENTIC,
        overall_score=0.96,
        tampering_score=0.01,
        provider_reference="provider://authenticity/reference",
        algorithm_version="auth-v1",
        document_version=1,
        assessed_at=timestamp(2),
    )

    selfie = DocumentSelfieMatchRecord(
        match_id=match_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_evidence_id=assessment_id,
        verification_id=uid(),
        liveness_assessment_id=liveness_id,
        document_type=IdentityDocumentType.PASSPORT,
        purpose=BiometricPurpose.EKYC,
        decision=DocumentSelfieMatchDecision.MATCH,
        similarity_score=0.95,
        liveness_score=0.98,
        document_score=0.96,
        portrait_reference="secure://portrait/reference",
        provider_reference="provider://selfie/reference",
        algorithm_version="selfie-v1",
        document_version=1,
        matched_at=timestamp(3),
    )

    evidence = IdentityVerificationEvidence(
        ocr_extraction=ocr,
        authenticity_assessment=authenticity,
        selfie_match=selfie,
        workflow_id=workflow_id,
        evidence_version=2,
        collected_at=timestamp(4),
        metadata={
            "channel": "MOBILE_APP",
        },
    )

    verification = IdentityVerificationRecord(
        verification_id=uid(),
        workflow_id=workflow_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_type=IdentityDocumentType.PASSPORT,
        purpose=BiometricPurpose.EKYC,
        decision=IdentityVerificationDecision.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL2,
        combined_score=0.965,
        ocr_score=0.97,
        authenticity_score=0.96,
        selfie_match_score=0.95,
        liveness_score=0.98,
        ocr_extraction_id=extraction_id,
        authenticity_assessment_id=assessment_id,
        selfie_match_id=match_id,
        policy_version="policy-v1",
        document_version=1,
        verified_at=timestamp(5),
    )

    return evidence, verification


def test_factory_builds_four_references() -> None:
    evidence, verification = evidence_and_verification()

    references = (
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
        )
    )

    assert len(references) == 4
    assert {
        item.evidence_type
        for item in references
    } == set(IdentityVerificationEvidenceType)


def test_factory_uses_canonical_identifiers() -> None:
    evidence, verification = evidence_and_verification()

    references = {
        item.evidence_type: item
        for item in (
            build_identity_verification_evidence_references(
                verification=verification,
                evidence=evidence,
            )
        )
    }

    assert (
        references[
            IdentityVerificationEvidenceType.OCR_EXTRACTION
        ].evidence_id
        == evidence.ocr_extraction.extraction_id
    )
    assert (
        references[
            IdentityVerificationEvidenceType
            .DOCUMENT_AUTHENTICITY
        ].evidence_id
        == evidence.authenticity_assessment.assessment_id
    )
    assert (
        references[
            IdentityVerificationEvidenceType
            .DOCUMENT_SELFIE_MATCH
        ].evidence_id
        == evidence.selfie_match.match_id
    )
    assert (
        references[
            IdentityVerificationEvidenceType
            .LIVENESS_ASSESSMENT
        ].evidence_id
        == evidence.selfie_match.liveness_assessment_id
    )


def test_factory_preserves_version_and_timestamp() -> None:
    evidence, verification = evidence_and_verification()

    references = (
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
        )
    )

    assert all(
        item.evidence_version
        == evidence.evidence_version
        for item in references
    )
    assert all(
        item.collected_at
        == evidence.collected_at
        for item in references
    )


def test_factory_output_is_deterministic() -> None:
    evidence, verification = evidence_and_verification()

    first = build_identity_verification_evidence_references(
        verification=verification,
        evidence=evidence,
    )
    second = build_identity_verification_evidence_references(
        verification=verification,
        evidence=evidence,
    )

    assert first == second
    assert tuple(
        item.evidence_type.value
        for item in first
    ) == tuple(
        sorted(
            item.value
            for item in IdentityVerificationEvidenceType
        )
    )


def test_factory_merges_safe_metadata() -> None:
    evidence, verification = evidence_and_verification()

    references = (
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
            metadata={
                "region": "AU",
            },
        )
    )

    for item in references:
        assert item.metadata["channel"] == "MOBILE_APP"
        assert item.metadata["region"] == "AU"
        assert (
            item.metadata["workflow_id"]
            == evidence.workflow_id
        )


@pytest.mark.parametrize(
    ("target", "field_name", "error_code"),
    (
        (
            "ocr",
            "tenant_id",
            "OCR_EVIDENCE_TENANT_MISMATCH",
        ),
        (
            "authenticity",
            "identity_id",
            "AUTHENTICITY_EVIDENCE_IDENTITY_MISMATCH",
        ),
        (
            "selfie",
            "document_id",
            "SELFIE_MATCH_EVIDENCE_DOCUMENT_MISMATCH",
        ),
        (
            "ocr",
            "document_version",
            "OCR_EVIDENCE_DOCUMENT_VERSION_MISMATCH",
        ),
        (
            "authenticity",
            "assessment_id",
            "AUTHENTICITY_EVIDENCE_IDENTIFIER_MISMATCH",
        ),
        (
            "selfie",
            "match_id",
            "SELFIE_MATCH_EVIDENCE_IDENTIFIER_MISMATCH",
        ),
    ),
)
def test_inconsistent_evidence_fails_closed(
    target: str,
    field_name: str,
    error_code: str,
) -> None:
    evidence, verification = evidence_and_verification()

    replacement: object = (
        2
        if field_name == "document_version"
        else uid()
    )

    if target == "ocr":
        evidence = replace(
            evidence,
            ocr_extraction=replace(
                evidence.ocr_extraction,
                **{field_name: replacement},
            ),
        )
    elif target == "authenticity":
        evidence = replace(
            evidence,
            authenticity_assessment=replace(
                evidence.authenticity_assessment,
                **{field_name: replacement},
            ),
        )
    else:
        evidence = replace(
            evidence,
            selfie_match=replace(
                evidence.selfie_match,
                **{field_name: replacement},
            ),
        )

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match=error_code,
    ):
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
        )


def test_workflow_mismatch_fails_closed() -> None:
    evidence, verification = evidence_and_verification()

    evidence = replace(
        evidence,
        workflow_id=uid(),
    )

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_"
            "WORKFLOW_MISMATCH"
        ),
    ):
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
        )


def test_blank_liveness_identifier_fails_closed() -> None:
    evidence, verification = evidence_and_verification()

    object.__setattr__(
        evidence.selfie_match,
        "liveness_assessment_id",
        " ",
    )

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match="LIVENESS_ASSESSMENT_ID_REQUIRED",
    ):
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
        )


def test_wrong_verification_type_is_rejected() -> None:
    evidence, _ = evidence_and_verification()

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match="IDENTITY_VERIFICATION_RECORD_REQUIRED",
    ):
        build_identity_verification_evidence_references(
            verification=object(),  # type: ignore[arg-type]
            evidence=evidence,
        )


def test_wrong_evidence_type_is_rejected() -> None:
    _, verification = evidence_and_verification()

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match="IDENTITY_VERIFICATION_EVIDENCE_REQUIRED",
    ):
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=object(),  # type: ignore[arg-type]
        )


def test_invalid_metadata_type_is_rejected() -> None:
    evidence, verification = evidence_and_verification()

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match="EVIDENCE_REFERENCE_METADATA_MAPPING_REQUIRED",
    ):
        build_identity_verification_evidence_references(
            verification=verification,
            evidence=evidence,
            metadata=object(),  # type: ignore[arg-type]
        )
