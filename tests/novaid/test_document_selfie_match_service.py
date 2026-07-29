from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    BiometricPurpose,
    CaptureChannel,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    DocumentSelfieMatchDecision,
    DocumentSelfieMatchEvidence,
    DocumentSelfieMatchEvent,
    DocumentSelfieMatchPolicy,
    DocumentSelfieMatchService,
    DocumentVerificationDecision,
    DocumentVerificationEvidence,
    DocumentVerificationStatus,
    FaceVerificationDecision,
    FaceVerificationRecord,
    IdentityDocument,
    IdentityDocumentType,
    LivenessAssessmentRecord,
    LivenessDecision,
    LivenessMode,
    PresentationAttackType,
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
        name="Document Selfie Match Tenant",
    )


def capture_device() -> CaptureDevice:
    return CaptureDevice(
        device_reference="selfie-device",
        channel=CaptureChannel.MOBILE_APP,
        integrity_verified=True,
    )


def capture_environment() -> CaptureEnvironment:
    return CaptureEnvironment(country_code="AU")


def capture_quality() -> CaptureQuality:
    return CaptureQuality(
        overall_score=0.94,
        face_detected=True,
        single_subject_detected=True,
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
    )


def document_evidence(
    current: IdentityDocument,
    *,
    decision: DocumentVerificationDecision = (
        DocumentVerificationDecision.PASS
    ),
    score: float = 0.95,
    portrait_reference: str | None = (
        "vault://documents/portrait-reference"
    ),
) -> DocumentVerificationEvidence:
    return DocumentVerificationEvidence(
        evidence_id=uid(),
        tenant_id=current.tenant_id,
        identity_id=current.identity_id,
        document_id=current.document_id,
        decision=decision,
        document_type=current.document_type,
        issuing_country_code="AU",
        provider_reference="document-provider",
        algorithm_version="document-model-1.0",
        overall_score=score,
        portrait_reference=portrait_reference,
    )


def face_verification(
    current: IdentityDocument,
    *,
    decision: FaceVerificationDecision = (
        FaceVerificationDecision.MATCH
    ),
    score: float = 0.94,
    purpose: BiometricPurpose = BiometricPurpose.EKYC,
) -> FaceVerificationRecord:
    return FaceVerificationRecord(
        verification_id=uid(),
        tenant_id=current.tenant_id,
        identity_id=current.identity_id,
        enrollment_id=uid(),
        consent_id=uid(),
        purpose=purpose,
        decision=decision,
        similarity_score=score,
        match_threshold=0.85,
        manual_review_threshold=0.65,
        provider_reference="face-provider",
        algorithm_version="face-model-1.0",
        capture_device=capture_device(),
        capture_environment=capture_environment(),
        capture_quality=capture_quality(),
    )


def liveness(
    current: IdentityDocument,
    *,
    decision: LivenessDecision = LivenessDecision.PASS,
    score: float = 0.95,
) -> LivenessAssessmentRecord:
    return LivenessAssessmentRecord(
        assessment_id=uid(),
        tenant_id=current.tenant_id,
        identity_id=current.identity_id,
        purpose=BiometricPurpose.EKYC,
        decision=decision,
        attempt_number=1,
        mode=LivenessMode.HYBRID,
        liveness_score=score,
        presentation_attack_score=0.03,
        provider_reference="liveness-provider",
        algorithm_version="pad-model-1.0",
        capture_device=capture_device(),
        capture_environment=capture_environment(),
        capture_quality=capture_quality(),
        detected_attack_types=frozenset(
            {PresentationAttackType.NONE}
        ),
    )


def evidence(
    current: IdentityDocument,
    *,
    document_decision: DocumentVerificationDecision = (
        DocumentVerificationDecision.PASS
    ),
    face_decision: FaceVerificationDecision = (
        FaceVerificationDecision.MATCH
    ),
    liveness_decision: LivenessDecision = (
        LivenessDecision.PASS
    ),
    similarity_score: float = 0.94,
    liveness_score: float = 0.95,
    document_score: float = 0.95,
) -> DocumentSelfieMatchEvidence:
    return DocumentSelfieMatchEvidence(
        document_evidence=document_evidence(
            current,
            decision=document_decision,
            score=document_score,
        ),
        face_verification=face_verification(
            current,
            decision=face_decision,
            score=similarity_score,
        ),
        liveness_assessment=liveness(
            current,
            decision=liveness_decision,
            score=liveness_score,
        ),
        provider_reference="document-selfie-provider",
        algorithm_version="document-selfie-model-1.0",
    )


def match(
    current: IdentityDocument,
    current_evidence: DocumentSelfieMatchEvidence,
    *,
    current_context: RequestContext | None = None,
    current_tenant: Tenant | None = None,
    policy: DocumentSelfieMatchPolicy | None = None,
):
    return DocumentSelfieMatchService().match(
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


def test_valid_document_selfie_match_is_accepted() -> None:
    current = document(uid(), uid())

    result = match(current, evidence(current))

    assert (
        result.match.decision
        is DocumentSelfieMatchDecision.MATCH
    )
    assert result.match.reason_codes == (
        "DOCUMENT_SELFIE_CONTROLS_SATISFIED",
    )


@pytest.mark.parametrize(
    ("face_decision", "expected"),
    (
        (
            FaceVerificationDecision.NO_MATCH,
            DocumentSelfieMatchDecision.NO_MATCH,
        ),
        (
            FaceVerificationDecision.MANUAL_REVIEW,
            DocumentSelfieMatchDecision.MANUAL_REVIEW,
        ),
    ),
)
def test_face_decisions_are_enforced(
    face_decision: FaceVerificationDecision,
    expected: DocumentSelfieMatchDecision,
) -> None:
    current = document(uid(), uid())

    result = match(
        current,
        evidence(
            current,
            face_decision=face_decision,
        ),
    )

    assert result.match.decision is expected


@pytest.mark.parametrize(
    ("decision", "expected"),
    (
        (
            LivenessDecision.RECAPTURE,
            DocumentSelfieMatchDecision.RECAPTURE,
        ),
        (
            LivenessDecision.MANUAL_REVIEW,
            DocumentSelfieMatchDecision.MANUAL_REVIEW,
        ),
        (
            LivenessDecision.FAIL,
            DocumentSelfieMatchDecision.LOCK_SESSION,
        ),
        (
            LivenessDecision.LOCK_SESSION,
            DocumentSelfieMatchDecision.LOCK_SESSION,
        ),
    ),
)
def test_liveness_decisions_are_enforced(
    decision: LivenessDecision,
    expected: DocumentSelfieMatchDecision,
) -> None:
    current = document(uid(), uid())

    result = match(
        current,
        evidence(
            current,
            liveness_decision=decision,
        ),
    )

    assert result.match.decision is expected


@pytest.mark.parametrize(
    ("decision", "expected"),
    (
        (
            DocumentVerificationDecision.MANUAL_REVIEW,
            DocumentSelfieMatchDecision.MANUAL_REVIEW,
        ),
        (
            DocumentVerificationDecision.RECAPTURE,
            DocumentSelfieMatchDecision.RECAPTURE,
        ),
        (
            DocumentVerificationDecision.FAIL,
            DocumentSelfieMatchDecision.NO_MATCH,
        ),
    ),
)
def test_document_decisions_are_enforced(
    decision: DocumentVerificationDecision,
    expected: DocumentSelfieMatchDecision,
) -> None:
    current = document(uid(), uid())

    result = match(
        current,
        evidence(
            current,
            document_decision=decision,
        ),
    )

    assert result.match.decision is expected


def test_cross_tenant_request_fails_closed() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        match(
            current,
            evidence(current),
            current_context=context(uid()),
        )


def test_evidence_tenant_mismatch_fails_closed() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_verification = replace(
        current_evidence.face_verification,
        tenant_id=uid(),
    )
    current_evidence = replace(
        current_evidence,
        face_verification=mismatched_verification,
    )

    with pytest.raises(
        PermissionError,
        match="DOCUMENT_SELFIE_TENANT_MISMATCH",
    ):
        match(current, current_evidence)


def test_identity_mismatch_fails_closed() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_liveness = replace(
        current_evidence.liveness_assessment,
        identity_id=uid(),
    )
    current_evidence = replace(
        current_evidence,
        liveness_assessment=mismatched_liveness,
    )

    with pytest.raises(
        PermissionError,
        match="DOCUMENT_SELFIE_IDENTITY_MISMATCH",
    ):
        match(current, current_evidence)


def test_document_binding_mismatch_is_rejected() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    mismatched_document_evidence = replace(
        current_evidence.document_evidence,
        document_id=uid(),
    )
    current_evidence = replace(
        current_evidence,
        document_evidence=mismatched_document_evidence,
    )

    with pytest.raises(
        ValueError,
        match="DOCUMENT_EVIDENCE_BINDING_MISMATCH",
    ):
        match(current, current_evidence)


def test_stale_version_is_rejected() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        DocumentSelfieMatchService().match(
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
        match="DOCUMENT_NOT_AVAILABLE_FOR_SELFIE_MATCH",
    ):
        match(current, evidence(current))


def test_missing_portrait_reference_is_rejected() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        ValueError,
        match="DOCUMENT_PORTRAIT_REFERENCE_REQUIRED",
    ):
        DocumentSelfieMatchEvidence(
            document_evidence=document_evidence(
                current,
                portrait_reference=None,
            ),
            face_verification=face_verification(current),
            liveness_assessment=liveness(current),
            provider_reference="provider",
            algorithm_version="model-1.0",
        )


def test_similarity_below_policy_routes_to_review() -> None:
    current = document(uid(), uid())

    result = match(
        current,
        evidence(
            current,
            similarity_score=0.75,
        ),
    )

    assert (
        result.match.decision
        is DocumentSelfieMatchDecision.MANUAL_REVIEW
    )


def test_low_liveness_score_requests_recapture() -> None:
    current = document(uid(), uid())

    result = match(
        current,
        evidence(
            current,
            liveness_score=0.70,
        ),
    )

    assert (
        result.match.decision
        is DocumentSelfieMatchDecision.RECAPTURE
    )


def test_event_is_traceable() -> None:
    current = document(uid(), uid())
    request_context = context(current.tenant_id)

    result = match(
        current,
        evidence(current),
        current_context=request_context,
    )

    assert isinstance(
        result.event,
        DocumentSelfieMatchEvent,
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
        == "DOCUMENT_SELFIE_MATCH_MATCH"
    )


def test_result_record_and_event_are_immutable() -> None:
    current = document(uid(), uid())
    result = match(current, evidence(current))

    with pytest.raises(FrozenInstanceError):
        result.match.decision = (  # type: ignore[misc]
            DocumentSelfieMatchDecision.NO_MATCH
        )

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_selfie": "base64"},
        {"document_image": "base64"},
        {"portrait_image": "base64"},
        {"embedding": [0.1, 0.2]},
        {"feature_vector": [1, 2]},
        {"provider_payload": {"raw": True}},
        {"provider_secret": "secret"},
    ),
)
def test_raw_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    current = document(uid(), uid())

    with pytest.raises(
        ValueError,
        match="RAW_DOCUMENT_SELFIE_MATERIAL_FORBIDDEN",
    ):
        DocumentSelfieMatchEvidence(
            document_evidence=document_evidence(current),
            face_verification=face_verification(current),
            liveness_assessment=liveness(current),
            provider_reference="provider",
            algorithm_version="model-1.0",
            metadata=metadata,
        )


def test_domain_contains_no_raw_media_fields() -> None:
    current = document(uid(), uid())
    current_evidence = evidence(current)

    for field_name in (
        "raw_selfie",
        "document_image",
        "portrait_image",
        "embedding",
        "feature_vector",
        "video",
        "frames",
    ):
        assert not hasattr(current_evidence, field_name)


@pytest.mark.parametrize(
    ("review", "matched"),
    (
        (0.85, 0.85),
        (0.90, 0.85),
    ),
)
def test_invalid_threshold_order_is_rejected(
    review: float,
    matched: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_DOCUMENT_SELFIE_THRESHOLD_ORDER",
    ):
        DocumentSelfieMatchPolicy(
            manual_review_threshold=review,
            match_threshold=matched,
        )
