from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    BiometricConsent,
    BiometricConsentStatus,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureChannel,
    CaptureDecision,
    CaptureDevice,
    CaptureEnvironment,
    CaptureLighting,
    CaptureQuality,
)


def uid() -> str:
    return str(uuid4())


def consent(
    *,
    purpose: BiometricPurpose = BiometricPurpose.ENROLLMENT,
) -> BiometricConsent:
    return BiometricConsent(
        consent_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        purpose=purpose,
        policy_version="2026-07-28.1",
        granted_at=datetime.now(UTC),
        capture_notice_version="2026-07",
        lawful_basis_reference="explicit-consent",
    )


def quality() -> CaptureQuality:
    return CaptureQuality(
        overall_score=0.91,
        face_detected=True,
        single_subject_detected=True,
        sharpness_score=0.90,
        illumination_score=0.88,
        pose_score=0.92,
        occlusion_score=0.97,
    )


def enrollment(
    *,
    status: BiometricEnrollmentStatus = (
        BiometricEnrollmentStatus.PENDING
    ),
    enrolled_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> BiometricEnrollment:
    return BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        consent_id=uid(),
        template_reference="vault://biometrics/template-001",
        provider_reference="provider-enrollment-001",
        algorithm_version="face-model-1.0",
        status=status,
        capture_device=CaptureDevice(
            device_reference="device-reference-001",
            channel=CaptureChannel.MOBILE_APP,
            platform="ios",
            operating_system="iOS",
            application_version="2026.1.0",
            camera_facing=" front ",
            integrity_verified=True,
            hardware_backed_key_available=True,
        ),
        capture_environment=CaptureEnvironment(
            lighting=CaptureLighting.NORMAL,
            network_reference="network-reference-001",
            country_code=" au ",
            location_accuracy_metres=8.5,
        ),
        capture_quality=quality(),
        enrolled_at=enrolled_at,
        revoked_at=revoked_at,
    )


def test_biometric_consent_is_purpose_bound() -> None:
    current = consent()

    assert current.is_active(
        purpose=BiometricPurpose.ENROLLMENT,
    ) is True
    assert current.is_active(
        purpose=BiometricPurpose.LOGIN,
    ) is False


def test_expired_consent_is_not_active() -> None:
    now = datetime.now(UTC)

    current = BiometricConsent(
        consent_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        purpose=BiometricPurpose.ENROLLMENT,
        policy_version="2026-07-28.1",
        granted_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
    )

    assert current.is_active(at=now) is False


def test_consent_revocation_is_immutable() -> None:
    current = consent()
    revoked = current.revoke()

    assert current.status is BiometricConsentStatus.ACTIVE
    assert revoked.status is BiometricConsentStatus.REVOKED
    assert revoked.revoked_at is not None


def test_revoked_consent_requires_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="BIOMETRIC_CONSENT_REVOKED_AT_REQUIRED",
    ):
        BiometricConsent(
            consent_id=uid(),
            tenant_id=uid(),
            identity_id=uid(),
            purpose=BiometricPurpose.ENROLLMENT,
            policy_version="2026-07-28.1",
            granted_at=datetime.now(UTC),
            status=BiometricConsentStatus.REVOKED,
        )


def test_capture_device_normalizes_values() -> None:
    device = CaptureDevice(
        device_reference="  device-reference  ",
        channel="MOBILE_APP",
        platform="  ios  ",
        camera_facing=" front ",
    )

    assert device.device_reference == "device-reference"
    assert device.channel is CaptureChannel.MOBILE_APP
    assert device.platform == "ios"
    assert device.camera_facing == "FRONT"


def test_capture_environment_normalizes_country_code() -> None:
    environment = CaptureEnvironment(
        country_code=" au ",
        lighting="NORMAL",
    )

    assert environment.country_code == "AU"
    assert environment.lighting is CaptureLighting.NORMAL


@pytest.mark.parametrize(
    "country_code",
    (
        "",
        "A",
        "AUS",
        "12",
        "A1",
    ),
)
def test_capture_environment_rejects_invalid_country(
    country_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_COUNTRY_CODE",
    ):
        CaptureEnvironment(
            country_code=country_code,
        )


def test_capture_quality_accepts_valid_capture() -> None:
    current = quality()

    assert current.acceptable() is True
    assert current.decision is CaptureDecision.ACCEPT


@pytest.mark.parametrize(
    "score",
    (
        -0.1,
        1.1,
    ),
)
def test_capture_quality_rejects_invalid_scores(
    score: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_CAPTURE_QUALITY_SCORE",
    ):
        CaptureQuality(
            overall_score=score,
            face_detected=True,
            single_subject_detected=True,
        )


def test_accept_decision_must_match_capture_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="CAPTURE_ACCEPT_DECISION_INCONSISTENT",
    ):
        CaptureQuality(
            overall_score=0.40,
            face_detected=True,
            single_subject_detected=True,
            minimum_required_score=0.70,
            decision=CaptureDecision.ACCEPT,
        )


def test_enrollment_stores_references_not_raw_media() -> None:
    current = enrollment()

    assert current.template_reference.startswith("vault://")
    assert current.provider_reference == "provider-enrollment-001"
    assert not hasattr(current, "raw_image")
    assert not hasattr(current, "embedding")
    assert not hasattr(current, "video")


def test_pending_enrollment_can_activate() -> None:
    current = enrollment()

    active = current.transition(
        BiometricEnrollmentStatus.ACTIVE,
    )

    assert current.status is BiometricEnrollmentStatus.PENDING
    assert active.status is BiometricEnrollmentStatus.ACTIVE
    assert active.enrolled_at is not None
    assert active.version == current.version + 1


def test_active_enrollment_can_suspend_and_reactivate() -> None:
    now = datetime.now(UTC)

    active = enrollment(
        status=BiometricEnrollmentStatus.ACTIVE,
        enrolled_at=now,
    )

    suspended = active.transition(
        BiometricEnrollmentStatus.SUSPENDED,
    )
    reactivated = suspended.transition(
        BiometricEnrollmentStatus.ACTIVE,
    )

    assert suspended.status is BiometricEnrollmentStatus.SUSPENDED
    assert reactivated.status is BiometricEnrollmentStatus.ACTIVE
    assert reactivated.enrolled_at == active.enrolled_at
    assert reactivated.version == active.version + 2


def test_revoked_enrollment_is_terminal() -> None:
    active = enrollment(
        status=BiometricEnrollmentStatus.ACTIVE,
        enrolled_at=datetime.now(UTC),
    )

    revoked = active.transition(
        BiometricEnrollmentStatus.REVOKED,
    )

    assert revoked.revoked_at is not None

    with pytest.raises(
        ValueError,
        match="INVALID_BIOMETRIC_ENROLLMENT_TRANSITION",
    ):
        revoked.transition(
            BiometricEnrollmentStatus.ACTIVE,
        )


def test_active_enrollment_requires_enrolled_at() -> None:
    with pytest.raises(
        ValueError,
        match="BIOMETRIC_ENROLLED_AT_REQUIRED",
    ):
        enrollment(
            status=BiometricEnrollmentStatus.ACTIVE,
        )


def test_effective_enrollment_honors_expiry() -> None:
    now = datetime.now(UTC)

    active = BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.LOGIN,
        consent_id=uid(),
        template_reference="vault://template/current",
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        status=BiometricEnrollmentStatus.ACTIVE,
        enrolled_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=1),
        created_at=now - timedelta(days=1),
    )

    assert active.is_effective(at=now) is True
    assert active.is_effective(
        at=now + timedelta(days=2),
    ) is False


def test_biometric_objects_are_immutable() -> None:
    current = enrollment()

    with pytest.raises(FrozenInstanceError):
        current.status = (  # type: ignore[misc]
            BiometricEnrollmentStatus.ACTIVE
        )


def test_metadata_is_defensively_copied() -> None:
    metadata = {
        "purpose": "controlled-pilot",
    }

    current = BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        consent_id=uid(),
        template_reference="vault://template/reference",
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        metadata=metadata,
    )

    metadata["purpose"] = "changed"

    assert current.metadata == {
        "purpose": "controlled-pilot",
    }


def test_capture_environment_allows_omitted_country() -> None:
    environment = CaptureEnvironment(
        country_code=None,
    )

    assert environment.country_code is None
