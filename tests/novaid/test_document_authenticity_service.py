from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    BarcodeEvidence,
    BarcodeType,
    CaptureChannel,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    DocumentAuthenticityAssessmentEvent,
    DocumentAuthenticityDecision,
    DocumentAuthenticityPolicy,
    DocumentAuthenticityProviderEvidence,
    DocumentAuthenticityService,
    DocumentCaptureChannel,
    DocumentCaptureReference,
    DocumentFraudIndicator,
    DocumentSecurityFeature,
    DocumentSecurityFeatureEvidence,
    DocumentSide,
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
    MachineReadableZoneEvidence,
    MachineReadableZoneType,
    RequestContext,
    Tenant,
    TenantSecurityPolicy,
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


def tenant(
    tenant_id: str,
    *,
    require_integrity: bool = False,
) -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name="Document Authenticity Tenant",
        security_policy=TenantSecurityPolicy(
            device_binding_required=require_integrity,
        ),
    )


def capture(
    *,
    integrity_verified: bool = True,
    emulator_detected: bool = False,
    rooted_or_jailbroken: bool = False,
    quality_score: float = 0.94,
) -> DocumentCaptureReference:
    return DocumentCaptureReference(
        capture_id=uid(),
        side=DocumentSide.BIO_DATA_PAGE,
        channel=DocumentCaptureChannel.MOBILE_CAMERA,
        encrypted_object_reference=(
            "vault://document/capture-reference"
        ),
        media_type="image/jpeg",
        checksum_sha256="a" * 64,
        capture_device=CaptureDevice(
            device_reference="document-device",
            channel=CaptureChannel.MOBILE_APP,
            integrity_verified=integrity_verified,
        ),
        capture_environment=CaptureEnvironment(
            country_code="AU",
            emulator_detected=emulator_detected,
            rooted_or_jailbroken=rooted_or_jailbroken,
        ),
        capture_quality=CaptureQuality(
            overall_score=quality_score,
            face_detected=True,
            single_subject_detected=True,
        ),
    )


def document(
    tenant_id: str,
    identity_id: str,
    *,
    current_capture: DocumentCaptureReference | None = None,
    with_barcode: bool = False,
) -> IdentityDocument:
    return IdentityDocument(
        document_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        status=DocumentVerificationStatus.IN_PROGRESS,
        captures=(current_capture or capture(),),
        mrz_evidence=MachineReadableZoneEvidence(
            mrz_type=MachineReadableZoneType.TD3,
            document_code="P",
            issuing_country_code="AUS",
            document_number="N1234567",
            nationality_code="AUS",
            date_of_birth="1990-01-01",
            expiry_date="2030-01-01",
            checksums_valid=True,
            confidence_score=0.98,
            provider_reference="mrz-provider",
            algorithm_version="mrz-model-1.0",
        ),
        barcode_evidence=(
            BarcodeEvidence(
                barcode_type=BarcodeType.PDF417,
                checksum_valid=True,
                confidence_score=0.95,
                provider_reference="barcode-provider",
                algorithm_version="barcode-model-1.0",
            )
            if with_barcode
            else None
        ),
        expires_at=date(2030, 1, 1),
    )


def evidence(
    *,
    score: float = 0.95,
    tampering_score: float = 0.03,
    security_feature_score: float | None = 0.94,
    portrait_integrity_score: float | None = 0.95,
    mrz_consistent: bool | None = True,
    barcode_consistent: bool | None = True,
    supported: bool = True,
    fraud_indicators: frozenset[
        DocumentFraudIndicator
    ] = frozenset({DocumentFraudIndicator.NONE}),
    metadata: dict[str, object] | None = None,
) -> DocumentAuthenticityProviderEvidence:
    return DocumentAuthenticityProviderEvidence(
        provider_reference="authenticity-provider",
        provider_decision_reference="decision-reference",
        algorithm_version="document-model-1.0",
        document_type=IdentityDocumentType.PASSPORT,
        overall_score=score,
        tampering_score=tampering_score,
        security_feature_score=security_feature_score,
        hologram_score=0.92,
        portrait_integrity_score=portrait_integrity_score,
        image_integrity_score=0.95,
        layout_consistency_score=0.96,
        mrz_consistent=mrz_consistent,
        barcode_consistent=barcode_consistent,
        document_template_supported=supported,
        detected_features=(
            DocumentSecurityFeatureEvidence(
                feature=DocumentSecurityFeature.HOLOGRAM,
                present=True,
                confidence_score=0.92,
            ),
            DocumentSecurityFeatureEvidence(
                feature=DocumentSecurityFeature.MRZ,
                present=True,
                confidence_score=0.98,
            ),
        ),
        fraud_indicators=fraud_indicators,
        metadata=dict(metadata or {}),
    )


def assess(
    current: IdentityDocument,
    current_evidence: DocumentAuthenticityProviderEvidence,
    *,
    current_context: RequestContext | None = None,
    current_tenant: Tenant | None = None,
    policy: DocumentAuthenticityPolicy | None = None,
):
    return DocumentAuthenticityService().assess(
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


def test_high_quality_document_is_authentic() -> None:
    current = document(uid(), uid())

    result = assess(current, evidence())

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.AUTHENTIC
    )
    assert result.document.authenticity_evidence is not None
    assert result.document.version == current.version + 1


def test_medium_score_requires_manual_review() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(score=0.75),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.MANUAL_REVIEW
    )
    assert (
        result.document.status
        is DocumentVerificationStatus.MANUAL_REVIEW
    )


def test_low_score_is_unreadable() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(score=0.40),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.UNREADABLE
    )


@pytest.mark.parametrize(
    "indicator",
    (
        DocumentFraudIndicator.IMAGE_MANIPULATION,
        DocumentFraudIndicator.TEXT_REPLACEMENT,
        DocumentFraudIndicator.PORTRAIT_REPLACEMENT,
        DocumentFraudIndicator.MRZ_MISMATCH,
        DocumentFraudIndicator.BARCODE_MISMATCH,
        DocumentFraudIndicator.SYNTHETIC_DOCUMENT,
    ),
)
def test_severe_fraud_is_rejected(
    indicator: DocumentFraudIndicator,
) -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(
            fraud_indicators=frozenset({indicator}),
        ),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.SUSPECTED_FRAUD
    )


def test_severe_tampering_is_rejected() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(tampering_score=0.90),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.SUSPECTED_FRAUD
    )


def test_mrz_inconsistency_is_rejected() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(mrz_consistent=False),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.SUSPECTED_FRAUD
    )


def test_barcode_inconsistency_is_rejected_when_present() -> None:
    current = document(
        uid(),
        uid(),
        with_barcode=True,
    )

    result = assess(
        current,
        evidence(barcode_consistent=False),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.SUSPECTED_FRAUD
    )


def test_unsupported_template_is_unreadable() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(supported=False),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.UNREADABLE
    )


def test_weak_security_features_require_review() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(security_feature_score=0.40),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.MANUAL_REVIEW
    )


def test_weak_portrait_integrity_requires_review() -> None:
    current = document(uid(), uid())

    result = assess(
        current,
        evidence(portrait_integrity_score=0.40),
    )

    assert (
        result.assessment.decision
        is DocumentAuthenticityDecision.MANUAL_REVIEW
    )


def test_cross_tenant_request_fails_closed() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        assess(
            current,
            evidence(),
            current_context=context(uid()),
        )


def test_document_tenant_mismatch_fails_closed() -> None:
    tenant_id = uid()
    current = document(uid(), uid())

    with pytest.raises(
        PermissionError,
        match="DOCUMENT_TENANT_MISMATCH",
    ):
        assess(
            current,
            evidence(),
            current_context=context(tenant_id),
            current_tenant=tenant(tenant_id),
        )


def test_stale_version_is_rejected() -> None:
    current = document(uid(), uid())

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        DocumentAuthenticityService().assess(
            context=context(current.tenant_id),
            tenant=tenant(current.tenant_id),
            document=current,
            evidence=evidence(),
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
        match="DOCUMENT_NOT_AVAILABLE_FOR_AUTHENTICITY",
    ):
        assess(current, evidence())


def test_document_type_mismatch_is_rejected() -> None:
    current = document(uid(), uid())
    current_evidence = replace(
        evidence(),
        document_type=IdentityDocumentType.DRIVER_LICENCE,
    )

    with pytest.raises(
        ValueError,
        match="AUTHENTICITY_DOCUMENT_TYPE_MISMATCH",
    ):
        assess(current, current_evidence)


def test_device_integrity_is_enforced() -> None:
    tenant_id = uid()
    current = document(
        tenant_id,
        uid(),
        current_capture=capture(
            integrity_verified=False,
        ),
    )

    with pytest.raises(
        PermissionError,
        match="CAPTURE_DEVICE_INTEGRITY_REQUIRED",
    ):
        assess(
            current,
            evidence(),
            current_tenant=tenant(
                tenant_id,
                require_integrity=True,
            ),
        )


@pytest.mark.parametrize(
    ("current_capture", "error"),
    (
        (
            capture(emulator_detected=True),
            "DOCUMENT_CAPTURE_EMULATOR_DENIED",
        ),
        (
            capture(rooted_or_jailbroken=True),
            "DOCUMENT_CAPTURE_COMPROMISED_DEVICE_DENIED",
        ),
    ),
)
def test_compromised_capture_is_rejected(
    current_capture: DocumentCaptureReference,
    error: str,
) -> None:
    current = document(
        uid(),
        uid(),
        current_capture=current_capture,
    )

    with pytest.raises(
        PermissionError,
        match=error,
    ):
        assess(current, evidence())


def test_capture_quality_is_enforced() -> None:
    current = document(
        uid(),
        uid(),
        current_capture=capture(
            quality_score=0.75,
        ),
    )

    with pytest.raises(
        ValueError,
        match="DOCUMENT_CAPTURE_QUALITY_BELOW_POLICY",
    ):
        assess(
            current,
            evidence(),
            policy=DocumentAuthenticityPolicy(
                minimum_capture_quality_score=0.80,
            ),
        )


def test_duplicate_security_feature_is_rejected() -> None:
    duplicate = DocumentSecurityFeatureEvidence(
        feature=DocumentSecurityFeature.HOLOGRAM,
        present=True,
        confidence_score=0.90,
    )

    with pytest.raises(
        ValueError,
        match="DUPLICATE_DOCUMENT_SECURITY_FEATURE",
    ):
        replace(
            evidence(),
            detected_features=(duplicate, duplicate),
        )


def test_inconsistent_fraud_indicators_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="INCONSISTENT_DOCUMENT_FRAUD_INDICATORS",
    ):
        evidence(
            fraud_indicators=frozenset(
                {
                    DocumentFraudIndicator.NONE,
                    DocumentFraudIndicator.IMAGE_MANIPULATION,
                }
            ),
        )


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"document_image": "base64"},
        {"raw_mrz": "raw"},
        {"barcode_payload": "raw"},
        {"nfc_dump": "raw"},
        {"embedding": [0.1, 0.2]},
        {"provider_payload": {"raw": True}},
        {"provider_secret": "secret"},
    ),
)
def test_raw_authenticity_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="RAW_DOCUMENT_AUTHENTICITY_MATERIAL_FORBIDDEN",
    ):
        evidence(metadata=metadata)


def test_event_is_traceable() -> None:
    current = document(uid(), uid())
    request_context = context(current.tenant_id)

    result = assess(
        current,
        evidence(),
        current_context=request_context,
    )

    assert isinstance(
        result.event,
        DocumentAuthenticityAssessmentEvent,
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
        == "DOCUMENT_AUTHENTICITY_AUTHENTIC"
    )


def test_result_is_immutable() -> None:
    current = document(uid(), uid())
    result = assess(current, evidence())

    with pytest.raises(FrozenInstanceError):
        result.assessment.decision = (  # type: ignore[misc]
            DocumentAuthenticityDecision.SUSPECTED_FRAUD
        )

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("review", "authentic"),
    (
        (0.85, 0.85),
        (0.90, 0.85),
    ),
)
def test_invalid_score_threshold_order_is_rejected(
    review: float,
    authentic: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_AUTHENTICITY_THRESHOLD_ORDER",
    ):
        DocumentAuthenticityPolicy(
            manual_review_threshold=review,
            authentic_threshold=authentic,
        )


def test_invalid_tampering_threshold_order_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_TAMPERING_THRESHOLD_ORDER",
    ):
        DocumentAuthenticityPolicy(
            maximum_tampering_score=0.80,
            severe_tampering_score=0.70,
        )
