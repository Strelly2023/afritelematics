from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date
from uuid import uuid4

import pytest

from afritech.novaid.domain.biometric_models import BiometricPurpose
from afritech.novaid.domain.document_authenticity_models import (
    DocumentAuthenticityAssessmentRecord,
)
from afritech.novaid.domain.document_models import (
    DocumentAuthenticityDecision,
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
    FORBIDDEN_IDENTITY_VERIFICATION_FIELDS,
    IdentityVerificationDecision,
    IdentityVerificationEvidence,
    IdentityVerificationPolicy,
    IdentityVerificationRecord,
)
from afritech.novaid.domain.models import AssuranceLevel


def uid() -> str:
    return str(uuid4())


def upstream_evidence() -> tuple[
    OCRExtractionRecord,
    DocumentAuthenticityAssessmentRecord,
    DocumentSelfieMatchRecord,
]:
    tenant_id = uid()
    identity_id = uid()
    document_id = uid()
    document_type = IdentityDocumentType.PASSPORT

    ocr = OCRExtractionRecord(
        extraction_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_type=document_type,
        decision=OCRExtractionDecision.ACCEPT,
        source=OCRExtractionSource.COMBINED,
        overall_confidence_score=0.97,
        extracted_data=DocumentExtractedData(
            document_number="N1234567",
            full_name="Djuma Kikombe",
            date_of_birth="1990-01-01",
            date_of_expiry="2030-01-01",
            issuing_country_code="AU",
        ),
        provider_reference="ocr-provider",
        algorithm_version="ocr-model-1.0",
        document_version=2,
    )
    authenticity = DocumentAuthenticityAssessmentRecord(
        assessment_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_type=document_type,
        decision=DocumentAuthenticityDecision.AUTHENTIC,
        overall_score=0.96,
        tampering_score=0.02,
        provider_reference="authenticity-provider",
        algorithm_version="document-model-1.0",
        document_version=3,
        security_feature_score=0.95,
        portrait_integrity_score=0.96,
        mrz_consistent=True,
    )
    selfie_match = DocumentSelfieMatchRecord(
        match_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_id=document_id,
        document_evidence_id=uid(),
        verification_id=uid(),
        liveness_assessment_id=uid(),
        document_type=document_type,
        purpose=BiometricPurpose.EKYC,
        decision=DocumentSelfieMatchDecision.MATCH,
        similarity_score=0.95,
        liveness_score=0.98,
        document_score=0.96,
        portrait_reference="vault://documents/portrait-reference",
        provider_reference="document-selfie-provider",
        algorithm_version="document-selfie-model-1.0",
        document_version=4,
    )

    return ocr, authenticity, selfie_match


def evidence(**overrides: object) -> IdentityVerificationEvidence:
    ocr, authenticity, selfie_match = upstream_evidence()
    values: dict[str, object] = {
        "ocr_extraction": ocr,
        "authenticity_assessment": authenticity,
        "selfie_match": selfie_match,
        "workflow_id": uid(),
        "metadata": {"channel": "MOBILE_APP"},
    }
    values.update(overrides)
    return IdentityVerificationEvidence(**values)


def record(
    bound_evidence: IdentityVerificationEvidence,
    **overrides: object,
) -> IdentityVerificationRecord:
    ocr = bound_evidence.ocr_extraction
    authenticity = bound_evidence.authenticity_assessment
    selfie_match = bound_evidence.selfie_match
    values: dict[str, object] = {
        "verification_id": uid(),
        "workflow_id": bound_evidence.workflow_id,
        "tenant_id": ocr.tenant_id,
        "identity_id": ocr.identity_id,
        "document_id": ocr.document_id,
        "document_type": ocr.document_type,
        "purpose": selfie_match.purpose,
        "decision": IdentityVerificationDecision.VERIFIED,
        "assurance_level": AssuranceLevel.NID_AL2,
        "combined_score": 0.965,
        "ocr_score": ocr.overall_confidence_score,
        "authenticity_score": authenticity.overall_score,
        "selfie_match_score": selfie_match.similarity_score,
        "liveness_score": selfie_match.liveness_score,
        "ocr_extraction_id": ocr.extraction_id,
        "authenticity_assessment_id": authenticity.assessment_id,
        "selfie_match_id": selfie_match.match_id,
        "policy_version": "identity-verification-policy-v1",
        "document_version": 5,
        "reason_codes": ("ALL_CONTROLS_SATISFIED",),
    }
    values.update(overrides)
    return IdentityVerificationRecord(**values)


def test_identity_verification_decisions_are_canonical() -> None:
    assert {decision.value for decision in IdentityVerificationDecision} == {
        "VERIFIED",
        "MANUAL_REVIEW",
        "REJECTED",
        "RECAPTURE_REQUIRED",
        "LOCKED",
    }


def test_default_policy_is_fail_closed() -> None:
    policy = IdentityVerificationPolicy()

    assert policy.require_ocr_accept is True
    assert policy.require_authentic_document is True
    assert policy.require_document_selfie_match is True
    assert policy.require_ekyc_purpose is True
    assert policy.reject_suspected_fraud is True
    assert policy.lock_on_session_lock is True
    assert policy.manual_review_combined_score < policy.minimum_combined_score


def test_evidence_contains_all_typed_governed_results() -> None:
    item = evidence()

    assert item.ocr_extraction.decision is OCRExtractionDecision.ACCEPT
    assert (
        item.authenticity_assessment.decision
        is DocumentAuthenticityDecision.AUTHENTIC
    )
    assert (
        item.selfie_match.decision
        is DocumentSelfieMatchDecision.MATCH
    )
    assert item.selfie_match.liveness_score == pytest.approx(0.98)
    assert item.selfie_match.document_version == 4


def test_evidence_preserves_cross_record_bindings() -> None:
    item = evidence()

    assert {
        item.ocr_extraction.tenant_id,
        item.authenticity_assessment.tenant_id,
        item.selfie_match.tenant_id,
    } == {item.ocr_extraction.tenant_id}
    assert {
        item.ocr_extraction.identity_id,
        item.authenticity_assessment.identity_id,
        item.selfie_match.identity_id,
    } == {item.ocr_extraction.identity_id}
    assert {
        item.ocr_extraction.document_id,
        item.authenticity_assessment.document_id,
        item.selfie_match.document_id,
    } == {item.ocr_extraction.document_id}


def test_record_contains_traceability_and_scores() -> None:
    item_evidence = evidence()
    item = record(item_evidence)

    assert item.workflow_id == item_evidence.workflow_id
    assert item.tenant_id == item_evidence.ocr_extraction.tenant_id
    assert item.ocr_extraction_id == item_evidence.ocr_extraction.extraction_id
    assert (
        item.authenticity_assessment_id
        == item_evidence.authenticity_assessment.assessment_id
    )
    assert item.selfie_match_id == item_evidence.selfie_match.match_id
    assert item.assurance_level is AssuranceLevel.NID_AL2


@pytest.mark.parametrize(
    ("field_name", "invalid_score"),
    (
        ("combined_score", -0.01),
        ("ocr_score", 1.01),
        ("authenticity_score", True),
        ("selfie_match_score", 1.1),
        ("liveness_score", -1),
    ),
)
def test_invalid_record_scores_are_rejected(
    field_name: str,
    invalid_score: object,
) -> None:
    with pytest.raises(ValueError):
        record(evidence(), **{field_name: invalid_score})


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": b"image"},
        {"provider_payload": {"decision": "PASS"}},
        {"raw_selfie": "base64"},
        {"raw_mrz": "P<AUS..."},
        {"barcode_payload": "raw-value"},
        {"api_key": "secret"},
    ),
)
def test_raw_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="RAW_IDENTITY_VERIFICATION_MATERIAL_FORBIDDEN",
    ):
        evidence(metadata=metadata)


def test_metadata_is_defensively_copied() -> None:
    metadata = {"source": "controlled-pilot"}
    item = evidence(metadata=metadata)

    metadata["source"] = "changed"

    assert item.metadata == {"source": "controlled-pilot"}


def test_reason_codes_are_normalized_and_deduplicated() -> None:
    item = record(
        evidence(),
        reason_codes=(" review_required ", "REVIEW_REQUIRED"),
    )

    assert item.reason_codes == ("REVIEW_REQUIRED",)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("minimum_ocr_score", -0.1),
        ("minimum_authenticity_score", 1.1),
        ("minimum_liveness_score", True),
        ("manual_review_combined_score", 0.9),
    ),
)
def test_invalid_policy_values_are_rejected(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        IdentityVerificationPolicy(**{field_name: value})


def test_models_are_immutable() -> None:
    item_evidence = evidence()
    item_record = record(item_evidence)

    with pytest.raises(FrozenInstanceError):
        item_evidence.workflow_id = uid()  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        item_record.decision = (  # type: ignore[misc]
            IdentityVerificationDecision.REJECTED
        )


def test_forbidden_field_registry_covers_raw_material() -> None:
    assert {
        "raw_image",
        "raw_selfie",
        "raw_video",
        "raw_mrz",
        "barcode_payload",
        "provider_payload",
        "embedding",
        "biometric_template",
        "api_key",
        "private_key",
    }.issubset(FORBIDDEN_IDENTITY_VERIFICATION_FIELDS)


def test_models_do_not_contain_raw_media_fields() -> None:
    model_fields = {
        field_name.lower()
        for model in (
            IdentityVerificationEvidence,
            IdentityVerificationRecord,
        )
        for field_name in model.__dataclass_fields__
    }

    assert not model_fields & FORBIDDEN_IDENTITY_VERIFICATION_FIELDS


def test_replace_preserves_validation() -> None:
    item = record(evidence())

    with pytest.raises(
        ValueError,
        match="INVALID_IDENTITY_VERIFICATION_OCR_SCORE",
    ):
        replace(item, ocr_score=2.0)
