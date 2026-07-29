from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    BiometricPurpose,
    DocumentAuthenticityAssessmentRecord,
    DocumentAuthenticityDecision,
    DocumentSelfieMatchDecision,
    DocumentSelfieMatchRecord,
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
    IdentityVerificationDecision,
    IdentityVerificationEvidence,
    IdentityVerificationOutcomeEvent,
    IdentityVerificationPolicy,
    IdentityVerificationService,
    OCRExtractionDecision,
    OCRExtractionRecord,
    OCRExtractionSource,
    DocumentExtractedData,
    RequestContext,
    Tenant,
)


def uid() -> str:
    return str(uuid4())


def context(tenant_id: str) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_identity_id=uid(),
        actor_membership_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        authentication_strength="PASSKEY",
    )


def tenant(tenant_id: str) -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name="Identity Verification Tenant",
    )


def document(
    tenant_id: str,
    identity_id: str,
) -> IdentityDocument:
    return IdentityDocument(
        document_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        status=DocumentVerificationStatus.IN_PROGRESS,
        expires_at=date(2030, 1, 1),
        version=4,
    )


def ocr(
    current: IdentityDocument,
    *,
    decision: OCRExtractionDecision = (
        OCRExtractionDecision.ACCEPT
    ),
    score: float = 0.96,
) -> OCRExtractionRecord:
    return OCRExtractionRecord(
        extraction_id=uid(),
        tenant_id=current.tenant_id,
        identity_id=current.identity_id,
        document_id=current.document_id,
        document_type=current.document_type,
        decision=decision,
        source=OCRExtractionSource.COMBINED,
        overall_confidence_score=score,
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


def authenticity(
    current: IdentityDocument,
    *,
    decision: DocumentAuthenticityDecision = (
        DocumentAuthenticityDecision.AUTHENTIC
    ),
    score: float = 0.95,
) -> DocumentAuthenticityAssessmentRecord:
    return DocumentAuthenticityAssessmentRecord(
        assessment_id=uid(),
        tenant_id=current.tenant_id,
        identity_id=current.identity_id,
        document_id=current.document_id,
        document_type=current.document_type,
        decision=decision,
        overall_score=score,
        tampering_score=0.03,
        provider_reference="authenticity-provider",
        algorithm_version="document-model-1.0",
        document_version=3,
        security_feature_score=0.94,
        portrait_integrity_score=0.95,
        mrz_consistent=True,
    )


def selfie_match(
    current: IdentityDocument,
    *,
    decision: DocumentSelfieMatchDecision = (
        DocumentSelfieMatchDecision.MATCH
    ),
    score: float = 0.94,
    liveness_score: float = 0.95,
    purpose: BiometricPurpose = BiometricPurpose.EKYC,
) -> DocumentSelfieMatchRecord:
    return DocumentSelfieMatchRecord(
        match_id=uid(),
        tenant_id=current.tenant_id,
        identity_id=current.identity_id,
        document_id=current.document_id,
        document_evidence_id=uid(),
        verification_id=uid(),
        liveness_assessment_id=uid(),
        document_type=current.document_type,
        purpose=purpose,
        decision=decision,
        similarity_score=score,
        liveness_score=liveness_score,
        document_score=0.95,
        portrait_reference=(
            "vault://documents/portrait-reference"
        ),
        provider_reference="document-selfie-provider",
        algorithm_version="document-selfie-model-1.0",
        document_version=4,
    )


def evidence(
    current: IdentityDocument,
    *,
    ocr_decision: OCRExtractionDecision = (
        OCRExtractionDecision.ACCEPT
    ),
    authenticity_decision: (
        DocumentAuthenticityDecision
    ) = DocumentAuthenticityDecision.AUTHENTIC,
    selfie_decision: DocumentSelfieMatchDecision = (
        DocumentSelfieMatchDecision.MATCH
    ),
    ocr_score: float = 0.96,
    authenticity_score: float = 0.95,
    selfie_score: float = 0.94,
    liveness_score: float = 0.95,
) -> IdentityVerificationEvidence:
    return IdentityVerificationEvidence(
        ocr_extraction=ocr(
            current,
            decision=ocr_decision,
            score=ocr_score,
        ),
        authenticity_assessment=authenticity(
            current,
            decision=authenticity_decision,
            score=authenticity_score,
        ),
        selfie_match=selfie_match(
            current,
            decision=selfie_decision,
            score=selfie_score,
            liveness_score=liveness_score,
        ),
        workflow_id=uid(),
    )


def verify(
    current: IdentityDocument,
    current_evidence: IdentityVerificationEvidence,
    *,
    current_context: RequestContext | None = None,
    current_tenant: Tenant | None = None,
    policy: IdentityVerificationPolicy | None = None,
):
    return IdentityVerificationService().verify(
        context=(
            current_context
            or context(current.tenant_id)
        ),
        tenant=(
            current_tenant
            or tenant(current.tenant_id)
        ),
        document=current,
        evidence=current_evidence,
        expected_version=current.version,
        policy=policy,
    )


def test_complete_controls_produce_verified_decision() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(current),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.VERIFIED
    )
    assert (
        result.document.status
        is DocumentVerificationStatus.VERIFIED
    )
    assert result.document.verified_at is not None
    assert (
        result.verification.assurance_level
        is AssuranceLevel.NID_AL2
    )


@pytest.mark.parametrize(
    "ocr_decision",
    (
        OCRExtractionDecision.MANUAL_REVIEW,
    ),
)
def test_ocr_review_routes_to_manual_review(
    ocr_decision: OCRExtractionDecision,
) -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            ocr_decision=ocr_decision,
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.MANUAL_REVIEW
    )


def test_ocr_recaputure_routes_to_recaputure_required() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            ocr_decision=OCRExtractionDecision.RECAPTURE,
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.RECAPTURE_REQUIRED
    )


def test_ocr_rejection_rejects_verification() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            ocr_decision=OCRExtractionDecision.REJECT,
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.REJECTED
    )


def test_suspected_fraud_rejects_verification() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            authenticity_decision=(
                DocumentAuthenticityDecision.SUSPECTED_FRAUD
            ),
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.REJECTED
    )
    assert result.verification.reason_codes == (
        "DOCUMENT_FRAUD_DETECTED",
    )


def test_unreadable_document_requests_recapture() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            authenticity_decision=(
                DocumentAuthenticityDecision.UNREADABLE
            ),
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.RECAPTURE_REQUIRED
    )


def test_authenticity_review_routes_to_manual_review() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            authenticity_decision=(
                DocumentAuthenticityDecision.MANUAL_REVIEW
            ),
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.MANUAL_REVIEW
    )


def test_selfie_no_match_rejects_verification() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            selfie_decision=(
                DocumentSelfieMatchDecision.NO_MATCH
            ),
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.REJECTED
    )


def test_selfie_recaputure_requests_recaputure() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            selfie_decision=(
                DocumentSelfieMatchDecision.RECAPTURE
            ),
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.RECAPTURE_REQUIRED
    )


def test_session_lock_produces_locked_decision() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            selfie_decision=(
                DocumentSelfieMatchDecision.LOCK_SESSION
            ),
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.LOCKED
    )


def test_cross_tenant_request_fails_closed() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        verify(
            current,
            evidence(current),
            current_context=context(uid()),
        )


def test_evidence_tenant_mismatch_fails_closed() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_ocr = replace(
        current_evidence.ocr_extraction,
        tenant_id=uid(),
    )
    current_evidence = replace(
        current_evidence,
        ocr_extraction=mismatched_ocr,
    )

    with pytest.raises(
        PermissionError,
        match="IDENTITY_VERIFICATION_TENANT_MISMATCH",
    ):
        verify(current, current_evidence)


def test_evidence_identity_mismatch_fails_closed() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_authenticity = replace(
        current_evidence.authenticity_assessment,
        identity_id=uid(),
    )
    current_evidence = replace(
        current_evidence,
        authenticity_assessment=mismatched_authenticity,
    )

    with pytest.raises(
        PermissionError,
        match="IDENTITY_VERIFICATION_IDENTITY_MISMATCH",
    ):
        verify(current, current_evidence)


def test_document_binding_mismatch_is_rejected() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_match = replace(
        current_evidence.selfie_match,
        document_id=uid(),
    )
    current_evidence = replace(
        current_evidence,
        selfie_match=mismatched_match,
    )

    with pytest.raises(
        ValueError,
        match="IDENTITY_VERIFICATION_DOCUMENT_MISMATCH",
    ):
        verify(current, current_evidence)


def test_document_type_mismatch_is_rejected() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_ocr = replace(
        current_evidence.ocr_extraction,
        document_type=(
            IdentityDocumentType.DRIVER_LICENCE
        ),
    )
    current_evidence = replace(
        current_evidence,
        ocr_extraction=mismatched_ocr,
    )

    with pytest.raises(
        ValueError,
        match="IDENTITY_VERIFICATION_DOCUMENT_TYPE_MISMATCH",
    ):
        verify(current, current_evidence)


def test_stale_document_version_is_rejected() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        IdentityVerificationService().verify(
            context=context(current.tenant_id),
            tenant=tenant(current.tenant_id),
            document=current,
            evidence=evidence(current),
            expected_version=current.version + 1,
        )


def test_terminal_document_is_rejected() -> None:
    current = document(uid(), uid())
    current = replace(
        current,
        status=DocumentVerificationStatus.REJECTED,
    )

    with pytest.raises(
        ValueError,
        match=(
            "DOCUMENT_NOT_AVAILABLE_FOR_FINAL_VERIFICATION"
        ),
    ):
        verify(current, evidence(current))


def test_low_component_score_requires_review() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            selfie_score=0.75,
        ),
    )

    assert (
        result.verification.decision
        is IdentityVerificationDecision.MANUAL_REVIEW
    )
    assert (
        "SELFIE_MATCH_SCORE_BELOW_POLICY"
        in result.verification.reason_codes
    )


def test_combined_score_is_calculated() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(
            current,
            ocr_score=0.96,
            authenticity_score=0.92,
            selfie_score=0.90,
            liveness_score=0.94,
        ),
    )

    assert result.verification.combined_score == (
        round(
            (0.96 + 0.92 + 0.90 + 0.94) / 4,
            6,
        )
    )


def test_event_is_traceable() -> None:
    current = document(uid(), uid())
    request_context = context(current.tenant_id)

    result = verify(
        current,
        evidence(current),
        current_context=request_context,
    )

    assert isinstance(
        result.event,
        IdentityVerificationOutcomeEvent,
    )
    assert result.event.actor_identity_id == (
        request_context.actor_identity_id
    )
    assert result.event.correlation_id == (
        request_context.correlation_id
    )
    assert result.event.request_id == (
        request_context.request_id
    )
    assert (
        result.event.event_type
        == "IDENTITY_VERIFICATION_VERIFIED"
    )


def test_result_record_and_event_are_immutable() -> None:
    current = document(uid(), uid())

    result = verify(
        current,
        evidence(current),
    )

    with pytest.raises(FrozenInstanceError):
        result.verification.decision = (  # type: ignore[misc]
            IdentityVerificationDecision.REJECTED
        )

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"raw_selfie": "base64"},
        {"document_image": "base64"},
        {"embedding": [0.1, 0.2]},
        {"feature_vector": [1, 2]},
        {"raw_mrz": "raw"},
        {"barcode_payload": "raw"},
        {"provider_payload": {"raw": True}},
        {"provider_secret": "secret"},
    ),
)
def test_raw_verification_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    current = document(uid(), uid())

    with pytest.raises(
        ValueError,
        match=(
            "RAW_IDENTITY_VERIFICATION_MATERIAL_FORBIDDEN"
        ),
    ):
        IdentityVerificationEvidence(
            ocr_extraction=ocr(current),
            authenticity_assessment=authenticity(current),
            selfie_match=selfie_match(current),
            workflow_id=uid(),
            metadata=metadata,
        )


def test_metadata_is_defensively_copied() -> None:
    current = document(uid(), uid())
    metadata = {"source": "controlled-pilot"}

    current_evidence = IdentityVerificationEvidence(
        ocr_extraction=ocr(current),
        authenticity_assessment=authenticity(current),
        selfie_match=selfie_match(current),
        workflow_id=uid(),
        metadata=metadata,
    )

    metadata["source"] = "changed"

    assert current_evidence.metadata == {
        "source": "controlled-pilot",
    }


@pytest.mark.parametrize(
    ("review", "verified"),
    (
        (0.85, 0.85),
        (0.90, 0.85),
    ),
)
def test_invalid_threshold_order_is_rejected(
    review: float,
    verified: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "INVALID_IDENTITY_VERIFICATION_THRESHOLD_ORDER"
        ),
    ):
        IdentityVerificationPolicy(
            manual_review_combined_score=review,
            minimum_combined_score=verified,
        )
