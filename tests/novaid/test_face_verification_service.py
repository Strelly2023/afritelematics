from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    BiometricConsent,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureChannel,
    CaptureDecision,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    FaceMatchEvidence,
    FaceVerificationDecision,
    FaceVerificationEvent,
    FaceVerificationPolicy,
    FaceVerificationService,
    RequestContext,
    Tenant,
    TenantSecurityPolicy,
)


def uid() -> str:
    return str(uuid4())


def request_context(tenant_id: str) -> RequestContext:
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
    device_binding_required: bool = False,
) -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name="Face Verification Tenant",
        security_policy=TenantSecurityPolicy(
            device_binding_required=(
                device_binding_required
            ),
        ),
    )


def enrollment(
    tenant_id: str,
    identity_id: str,
    *,
    status: BiometricEnrollmentStatus = (
        BiometricEnrollmentStatus.ACTIVE
    ),
    expires_at: datetime | None = None,
) -> BiometricEnrollment:
    now = datetime.now(UTC)

    return BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        consent_id=uid(),
        template_reference="vault://face/template-001",
        provider_reference="enrollment-provider-reference",
        algorithm_version="face-model-1.0",
        status=status,
        enrolled_at=(
            now - timedelta(days=1)
            if status
            in {
                BiometricEnrollmentStatus.ACTIVE,
                BiometricEnrollmentStatus.SUSPENDED,
                BiometricEnrollmentStatus.REVOKED,
            }
            else None
        ),
        revoked_at=(
            now - timedelta(minutes=1)
            if status is BiometricEnrollmentStatus.REVOKED
            else None
        ),
        expires_at=expires_at,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(minutes=1),
    )


def consent(
    tenant_id: str,
    identity_id: str,
    *,
    purpose: BiometricPurpose = BiometricPurpose.LOGIN,
    expires_at: datetime | None = None,
) -> BiometricConsent:
    return BiometricConsent(
        consent_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        purpose=purpose,
        policy_version="2026-07-28.1",
        granted_at=datetime.now(UTC) - timedelta(minutes=5),
        expires_at=expires_at,
    )


def device(
    *,
    integrity_verified: bool = True,
) -> CaptureDevice:
    return CaptureDevice(
        device_reference="verification-device-001",
        channel=CaptureChannel.MOBILE_APP,
        integrity_verified=integrity_verified,
    )


def environment(
    *,
    emulator_detected: bool = False,
    rooted_or_jailbroken: bool = False,
) -> CaptureEnvironment:
    return CaptureEnvironment(
        country_code="AU",
        emulator_detected=emulator_detected,
        rooted_or_jailbroken=rooted_or_jailbroken,
    )


def quality(
    *,
    score: float = 0.92,
    decision: CaptureDecision = CaptureDecision.ACCEPT,
) -> CaptureQuality:
    return CaptureQuality(
        overall_score=score,
        face_detected=True,
        single_subject_detected=True,
        minimum_required_score=0.70,
        decision=decision,
    )


def evidence(score: float) -> FaceMatchEvidence:
    return FaceMatchEvidence(
        provider_reference="verification-provider-reference",
        provider_decision_reference="decision-001",
        algorithm_version="face-model-1.0",
        similarity_score=score,
        confidence_score=0.97,
        reason_codes=("provider_evaluated",),
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    (
        (0.91, FaceVerificationDecision.MATCH),
        (0.75, FaceVerificationDecision.MANUAL_REVIEW),
        (0.40, FaceVerificationDecision.NO_MATCH),
    ),
)
def test_verification_decision_thresholds(
    score: float,
    expected: FaceVerificationDecision,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    result = FaceVerificationService().verify(
        context=request_context(tenant_id),
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        enrollment=enrollment(tenant_id, identity_id),
        consent=consent(tenant_id, identity_id),
        purpose=BiometricPurpose.LOGIN,
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        match_evidence=evidence(score),
    )

    assert result.verification.decision is expected
    assert result.event.decision is expected
    assert result.event.event_type == (
        f"FACE_VERIFICATION_{expected.value}"
    )


def test_verification_is_traceable_and_contains_no_raw_media() -> None:
    tenant_id = uid()
    identity_id = uid()
    context = request_context(tenant_id)

    result = FaceVerificationService().verify(
        context=context,
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        enrollment=enrollment(tenant_id, identity_id),
        consent=consent(tenant_id, identity_id),
        purpose=BiometricPurpose.LOGIN,
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        match_evidence=evidence(0.91),
    )

    record = result.verification
    event = result.event

    assert event.actor_identity_id == context.actor_identity_id
    assert event.correlation_id == context.correlation_id
    assert event.request_id == context.request_id
    assert record.provider_reference == (
        "verification-provider-reference"
    )
    assert not hasattr(record, "raw_image")
    assert not hasattr(record, "embedding")
    assert not hasattr(record, "video")


def test_cross_tenant_verification_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        FaceVerificationService().verify(
            context=request_context(uid()),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, identity_id),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


def test_enrollment_tenant_mismatch_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="BIOMETRIC_ENROLLMENT_TENANT_MISMATCH",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(uid(), identity_id),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


def test_enrollment_identity_mismatch_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="BIOMETRIC_ENROLLMENT_IDENTITY_MISMATCH",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, uid()),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


@pytest.mark.parametrize(
    "status",
    (
        BiometricEnrollmentStatus.PENDING,
        BiometricEnrollmentStatus.SUSPENDED,
        BiometricEnrollmentStatus.REVOKED,
    ),
)
def test_inactive_enrollment_is_rejected(
    status: BiometricEnrollmentStatus,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    current = enrollment(
        tenant_id,
        identity_id,
        status=status,
    )

    with pytest.raises(
        PermissionError,
        match="ACTIVE_FACE_ENROLLMENT_REQUIRED",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=current,
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


def test_expired_enrollment_is_rejected() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="ACTIVE_FACE_ENROLLMENT_REQUIRED",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(
                tenant_id,
                identity_id,
                expires_at=(
                    datetime.now(UTC)
                    - timedelta(seconds=1)
                ),
            ),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


def test_consent_purpose_mismatch_is_rejected() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        ValueError,
        match="BIOMETRIC_CONSENT_PURPOSE_MISMATCH",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, identity_id),
            consent=consent(
                tenant_id,
                identity_id,
                purpose=BiometricPurpose.STEP_UP,
            ),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


def test_expired_consent_is_rejected() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="ACTIVE_BIOMETRIC_CONSENT_REQUIRED",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, identity_id),
            consent=consent(
                tenant_id,
                identity_id,
                expires_at=(
                    datetime.now(UTC)
                    - timedelta(seconds=1)
                ),
            ),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


def test_capture_quality_below_policy_is_rejected() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        ValueError,
        match="FACE_CAPTURE_QUALITY_BELOW_POLICY",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, identity_id),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(score=0.75),
            match_evidence=evidence(0.91),
            policy=FaceVerificationPolicy(
                minimum_capture_quality_score=0.80,
            ),
        )


def test_device_integrity_policy_is_enforced() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="CAPTURE_DEVICE_INTEGRITY_REQUIRED",
    ):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(
                tenant_id,
                device_binding_required=True,
            ),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, identity_id),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(
                integrity_verified=False,
            ),
            capture_environment=environment(),
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


@pytest.mark.parametrize(
    ("capture_environment", "error"),
    (
        (
            environment(emulator_detected=True),
            "BIOMETRIC_CAPTURE_EMULATOR_DENIED",
        ),
        (
            environment(rooted_or_jailbroken=True),
            "BIOMETRIC_CAPTURE_COMPROMISED_DEVICE_DENIED",
        ),
    ),
)
def test_compromised_capture_environment_is_rejected(
    capture_environment: CaptureEnvironment,
    error: str,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(PermissionError, match=error):
        FaceVerificationService().verify(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            enrollment=enrollment(tenant_id, identity_id),
            consent=consent(tenant_id, identity_id),
            purpose=BiometricPurpose.LOGIN,
            capture_device=device(),
            capture_environment=capture_environment,
            capture_quality=quality(),
            match_evidence=evidence(0.91),
        )


@pytest.mark.parametrize(
    ("match", "review", "error"),
    (
        (
            0.60,
            0.65,
            "INVALID_FACE_VERIFICATION_THRESHOLD_ORDER",
        ),
        (
            0.85,
            0.85,
            "INVALID_FACE_VERIFICATION_THRESHOLD_ORDER",
        ),
    ),
)
def test_invalid_policy_threshold_order_is_rejected(
    match: float,
    review: float,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        FaceVerificationPolicy(
            match_threshold=match,
            manual_review_threshold=review,
        )


@pytest.mark.parametrize(
    "score",
    (-0.1, 1.1),
)
def test_invalid_similarity_score_is_rejected(
    score: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_FACE_SIMILARITY_SCORE",
    ):
        evidence(score)


def test_result_record_and_event_are_immutable() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = FaceVerificationService().verify(
        context=request_context(tenant_id),
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        enrollment=enrollment(tenant_id, identity_id),
        consent=consent(tenant_id, identity_id),
        purpose=BiometricPurpose.LOGIN,
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        match_evidence=evidence(0.91),
    )

    assert isinstance(result.event, FaceVerificationEvent)

    with pytest.raises(FrozenInstanceError):
        result.verification = result.verification  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]
