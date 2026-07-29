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
    FaceEnrollmentEvent,
    FaceEnrollmentService,
    RequestContext,
    Tenant,
    TenantSecurityPolicy,
)


def uid() -> str:
    return str(uuid4())


def context(
    tenant_id: str,
) -> RequestContext:
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
        name="NovaTech Biometric Tenant",
        security_policy=TenantSecurityPolicy(
            device_binding_required=require_integrity,
        ),
    )


def consent(
    tenant_id: str,
    identity_id: str,
    *,
    purpose: BiometricPurpose = (
        BiometricPurpose.ENROLLMENT
    ),
    expires_at: datetime | None = None,
) -> BiometricConsent:
    return BiometricConsent(
        consent_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        purpose=purpose,
        policy_version="2026-07-28.1",
        granted_at=datetime.now(UTC) - timedelta(minutes=1),
        expires_at=expires_at,
    )


def device(
    *,
    integrity_verified: bool = True,
) -> CaptureDevice:
    return CaptureDevice(
        device_reference="device-reference-001",
        channel=CaptureChannel.MOBILE_APP,
        platform="ios",
        integrity_verified=integrity_verified,
        hardware_backed_key_available=True,
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
    decision: CaptureDecision = CaptureDecision.ACCEPT,
) -> CaptureQuality:
    return CaptureQuality(
        overall_score=0.94,
        face_detected=True,
        single_subject_detected=True,
        minimum_required_score=0.70,
        decision=decision,
    )


def existing_enrollment(
    tenant_id: str,
    identity_id: str,
    *,
    status: BiometricEnrollmentStatus,
) -> BiometricEnrollment:
    now = datetime.now(UTC)

    return BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        consent_id=uid(),
        template_reference="vault://existing-template",
        provider_reference="existing-provider-reference",
        algorithm_version="face-model-1.0",
        status=status,
        enrolled_at=(
            now
            if status is BiometricEnrollmentStatus.ACTIVE
            else None
        ),
        revoked_at=(
            now
            if status is BiometricEnrollmentStatus.REVOKED
            else None
        ),
        created_at=now - timedelta(days=1),
    )


def test_face_enrollment_activates_with_governed_references() -> None:
    tenant_id = uid()
    identity_id = uid()
    request_context = context(tenant_id)

    result = FaceEnrollmentService().enroll(
        context=request_context,
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        consent=consent(
            tenant_id,
            identity_id,
        ),
        template_reference="vault://biometrics/template-001",
        provider_reference="provider-enrollment-001",
        algorithm_version="face-model-1.0",
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        metadata={
            "environment": "controlled-pilot",
        },
    )

    enrollment = result.enrollment

    assert enrollment.status is BiometricEnrollmentStatus.ACTIVE
    assert enrollment.biometric_type is BiometricType.FACE
    assert enrollment.purpose is BiometricPurpose.ENROLLMENT
    assert enrollment.enrolled_at is not None
    assert enrollment.version == 2
    assert enrollment.template_reference.startswith("vault://")
    assert not hasattr(enrollment, "raw_image")
    assert not hasattr(enrollment, "embedding")
    assert not hasattr(enrollment, "video")


def test_face_enrollment_emits_traceable_event() -> None:
    tenant_id = uid()
    identity_id = uid()
    request_context = context(tenant_id)

    result = FaceEnrollmentService().enroll(
        context=request_context,
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        consent=consent(
            tenant_id,
            identity_id,
        ),
        template_reference="vault://template/reference",
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
    )

    event = result.event

    assert isinstance(event, FaceEnrollmentEvent)
    assert event.event_type == "FACE_ENROLLMENT_ACTIVATED"
    assert event.tenant_id == tenant_id
    assert event.identity_id == identity_id
    assert event.enrollment_id == result.enrollment.enrollment_id
    assert event.actor_identity_id == (
        request_context.actor_identity_id
    )
    assert event.correlation_id == (
        request_context.correlation_id
    )
    assert event.request_id == (
        request_context.request_id
    )
    assert event.quality_score == 0.94


def test_cross_tenant_enrollment_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        FaceEnrollmentService().enroll(
            context=context(uid()),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
        )


def test_consent_tenant_mismatch_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="BIOMETRIC_CONSENT_TENANT_MISMATCH",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                uid(),
                identity_id,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
        )


def test_consent_identity_mismatch_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="BIOMETRIC_CONSENT_IDENTITY_MISMATCH",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                uid(),
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
        )


def test_consent_must_be_enrollment_purpose() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        ValueError,
        match="BIOMETRIC_CONSENT_PURPOSE_MISMATCH",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
                purpose=BiometricPurpose.LOGIN,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
        )


def test_expired_consent_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="ACTIVE_BIOMETRIC_CONSENT_REQUIRED",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
                expires_at=(
                    datetime.now(UTC)
                    - timedelta(seconds=1)
                ),
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
        )


def test_unacceptable_capture_quality_is_rejected() -> None:
    tenant_id = uid()
    identity_id = uid()

    rejected_quality = CaptureQuality(
        overall_score=0.55,
        face_detected=True,
        single_subject_detected=True,
        minimum_required_score=0.70,
        decision=CaptureDecision.RECAPTURE,
    )

    with pytest.raises(
        ValueError,
        match="ACCEPTABLE_FACE_CAPTURE_REQUIRED",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=rejected_quality,
        )


def test_device_integrity_policy_is_enforced() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="CAPTURE_DEVICE_INTEGRITY_REQUIRED",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(
                tenant_id,
                require_integrity=True,
            ),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(
                integrity_verified=False,
            ),
            capture_environment=environment(),
            capture_quality=quality(),
        )


@pytest.mark.parametrize(
    (
        "capture_environment",
        "error",
    ),
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

    with pytest.raises(
        PermissionError,
        match=error,
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=capture_environment,
            capture_quality=quality(),
        )


@pytest.mark.parametrize(
    "status",
    (
        BiometricEnrollmentStatus.PENDING,
        BiometricEnrollmentStatus.ACTIVE,
        BiometricEnrollmentStatus.SUSPENDED,
    ),
)
def test_duplicate_non_terminal_enrollment_is_rejected(
    status: BiometricEnrollmentStatus,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        ValueError,
        match="DUPLICATE_ACTIVE_FACE_ENROLLMENT",
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
            ),
            template_reference="vault://template/reference",
            provider_reference="provider-reference",
            algorithm_version="face-model-1.0",
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            existing_enrollments=(
                existing_enrollment(
                    tenant_id,
                    identity_id,
                    status=status,
                ),
            ),
        )


def test_revoked_enrollment_does_not_block_reenrollment() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = FaceEnrollmentService().enroll(
        context=context(tenant_id),
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        consent=consent(
            tenant_id,
            identity_id,
        ),
        template_reference="vault://template/new",
        provider_reference="provider-reference-new",
        algorithm_version="face-model-1.1",
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        existing_enrollments=(
            existing_enrollment(
                tenant_id,
                identity_id,
                status=BiometricEnrollmentStatus.REVOKED,
            ),
        ),
    )

    assert (
        result.enrollment.status
        is BiometricEnrollmentStatus.ACTIVE
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
        "error",
    ),
    (
        (
            "template_reference",
            "   ",
            "BIOMETRIC_TEMPLATE_REFERENCE_REQUIRED",
        ),
        (
            "provider_reference",
            "",
            "BIOMETRIC_PROVIDER_REFERENCE_REQUIRED",
        ),
        (
            "algorithm_version",
            "   ",
            "BIOMETRIC_ALGORITHM_VERSION_REQUIRED",
        ),
    ),
)
def test_secure_references_are_required(
    field_name: str,
    field_value: str,
    error: str,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    arguments = {
        "template_reference": "vault://template/reference",
        "provider_reference": "provider-reference",
        "algorithm_version": "face-model-1.0",
    }
    arguments[field_name] = field_value

    with pytest.raises(
        ValueError,
        match=error,
    ):
        FaceEnrollmentService().enroll(
            context=context(tenant_id),
            tenant=tenant(tenant_id),
            identity_id=identity_id,
            consent=consent(
                tenant_id,
                identity_id,
            ),
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            **arguments,
        )


def test_face_enrollment_result_and_event_are_immutable() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = FaceEnrollmentService().enroll(
        context=context(tenant_id),
        tenant=tenant(tenant_id),
        identity_id=identity_id,
        consent=consent(
            tenant_id,
            identity_id,
        ),
        template_reference="vault://template/reference",
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
    )

    with pytest.raises(FrozenInstanceError):
        result.enrollment = result.enrollment  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]
