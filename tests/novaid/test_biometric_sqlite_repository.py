from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    AuthenticationStrength,
    BiometricConsent,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureChannel,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    FaceAuthenticationDecision,
    FaceAuthenticationRecord,
    FaceVerificationDecision,
    FaceVerificationRecord,
    Identity,
    LivenessAssessmentRecord,
    LivenessDecision,
    LivenessMode,
    PresentationAttackType,
    RequestContext,
)
from afritech.novaid.persistence.sqlite import (
    NovaIDUnitOfWork,
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


def capture_device() -> CaptureDevice:
    return CaptureDevice(
        device_reference="device-reference",
        channel=CaptureChannel.MOBILE_APP,
        integrity_verified=True,
        hardware_backed_key_available=True,
    )


def capture_environment() -> CaptureEnvironment:
    return CaptureEnvironment(
        country_code="AU",
    )


def capture_quality() -> CaptureQuality:
    return CaptureQuality(
        overall_score=0.94,
        face_detected=True,
        single_subject_detected=True,
    )


def bootstrap(
    store: NovaIDUnitOfWork,
) -> tuple[str, str]:
    tenant_id = uid()
    identity_id = uid()
    now = datetime.now(UTC)

    store.create_tenant(
        tenant_id,
        "Biometric Repository Tenant",
        now,
    )
    store.add_identity(
        Identity(
            identity_id=identity_id,
            tenant_id=tenant_id,
            normalized_email=(
                f"{identity_id}@biometric.example"
            ),
        )
    )

    return tenant_id, identity_id


def consent(
    tenant_id: str,
    identity_id: str,
) -> BiometricConsent:
    now = datetime.now(UTC)

    return BiometricConsent(
        consent_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        purpose=BiometricPurpose.LOGIN,
        policy_version="2026-07-28.1",
        granted_at=now,
        expires_at=now + timedelta(days=30),
        capture_notice_version="2026-07",
        lawful_basis_reference="explicit-consent",
        metadata={"source": "sqlite-repository-test"},
    )


def enrollment(
    tenant_id: str,
    identity_id: str,
    consent_id: str,
) -> BiometricEnrollment:
    now = datetime.now(UTC)

    return BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        consent_id=consent_id,
        template_reference="vault://template/reference",
        provider_reference="provider-enrollment-reference",
        algorithm_version="face-model-1.0",
        status=BiometricEnrollmentStatus.ACTIVE,
        capture_device=capture_device(),
        capture_environment=capture_environment(),
        capture_quality=capture_quality(),
        enrolled_at=now,
        created_at=now,
        updated_at=now,
        version=2,
        metadata={"source": "sqlite-repository-test"},
    )


def verification(
    tenant_id: str,
    identity_id: str,
    enrollment_id: str,
    consent_id: str,
) -> FaceVerificationRecord:
    return FaceVerificationRecord(
        verification_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        enrollment_id=enrollment_id,
        consent_id=consent_id,
        purpose=BiometricPurpose.LOGIN,
        decision=FaceVerificationDecision.MATCH,
        similarity_score=0.94,
        match_threshold=0.85,
        manual_review_threshold=0.65,
        provider_reference="provider-verification-reference",
        algorithm_version="face-model-1.0",
        capture_device=capture_device(),
        capture_environment=capture_environment(),
        capture_quality=capture_quality(),
        reason_codes=("PROVIDER_EVALUATED",),
        metadata={"source": "sqlite-repository-test"},
    )


def authentication(
    tenant_id: str,
    identity_id: str,
    verification_id: str,
    enrollment_id: str,
) -> FaceAuthenticationRecord:
    return FaceAuthenticationRecord(
        authentication_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        verification_id=verification_id,
        enrollment_id=enrollment_id,
        purpose=BiometricPurpose.LOGIN,
        decision=FaceAuthenticationDecision.ALLOW,
        verification_decision=FaceVerificationDecision.MATCH,
        risk_score=0.10,
        authentication_strength=AuthenticationStrength.PASSKEY,
        current_assurance_level=AssuranceLevel.NID_AL2,
        required_assurance_level=AssuranceLevel.NID_AL1,
        reason_codes=(
            "FACE_AUTHENTICATION_CONTROLS_SATISFIED",
        ),
        metadata={"source": "sqlite-repository-test"},
    )


def liveness(
    tenant_id: str,
    identity_id: str,
) -> LivenessAssessmentRecord:
    return LivenessAssessmentRecord(
        assessment_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        purpose=BiometricPurpose.LOGIN,
        decision=LivenessDecision.PASS,
        attempt_number=1,
        mode=LivenessMode.HYBRID,
        liveness_score=0.95,
        presentation_attack_score=0.04,
        provider_reference="provider-liveness-reference",
        algorithm_version="pad-model-1.0",
        capture_device=capture_device(),
        capture_environment=capture_environment(),
        capture_quality=capture_quality(),
        detected_attack_types=frozenset(
            {PresentationAttackType.NONE}
        ),
        reason_codes=("LIVENESS_CONTROLS_SATISFIED",),
        metadata={"source": "sqlite-repository-test"},
    )


def test_biometric_consent_round_trip() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        original = consent(tenant_id, identity_id)

        store.add_biometric_consent(original)

        restored = store.get_biometric_consent(
            context(tenant_id),
            original.consent_id,
        )

    assert restored == original


def test_biometric_enrollment_round_trip() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        current_consent = consent(
            tenant_id,
            identity_id,
        )
        store.add_biometric_consent(current_consent)

        original = enrollment(
            tenant_id,
            identity_id,
            current_consent.consent_id,
        )
        store.add_biometric_enrollment(original)

        restored = store.get_biometric_enrollment(
            context(tenant_id),
            original.enrollment_id,
        )

    assert restored == original


def test_biometric_enrollment_update_is_versioned() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        current_consent = consent(
            tenant_id,
            identity_id,
        )
        store.add_biometric_consent(current_consent)

        original = enrollment(
            tenant_id,
            identity_id,
            current_consent.consent_id,
        )
        store.add_biometric_enrollment(original)

        suspended = original.transition(
            BiometricEnrollmentStatus.SUSPENDED,
        )

        store.update_biometric_enrollment(
            context(tenant_id),
            suspended,
            expected_version=original.version,
        )

        restored = store.get_biometric_enrollment(
            context(tenant_id),
            original.enrollment_id,
        )

    assert restored.status is BiometricEnrollmentStatus.SUSPENDED
    assert restored.version == original.version + 1


def test_stale_enrollment_update_is_rejected() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        current_consent = consent(
            tenant_id,
            identity_id,
        )
        store.add_biometric_consent(current_consent)

        original = enrollment(
            tenant_id,
            identity_id,
            current_consent.consent_id,
        )
        store.add_biometric_enrollment(original)

        suspended = original.transition(
            BiometricEnrollmentStatus.SUSPENDED,
        )

        with pytest.raises(
            RuntimeError,
            match="CONCURRENCY_CONFLICT",
        ):
            store.update_biometric_enrollment(
                context(tenant_id),
                suspended,
                expected_version=original.version + 10,
            )


def test_face_verification_round_trip() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        current_consent = consent(tenant_id, identity_id)
        store.add_biometric_consent(current_consent)

        current_enrollment = enrollment(
            tenant_id,
            identity_id,
            current_consent.consent_id,
        )
        store.add_biometric_enrollment(current_enrollment)

        original = verification(
            tenant_id,
            identity_id,
            current_enrollment.enrollment_id,
            current_consent.consent_id,
        )
        store.add_face_verification(original)

        restored = store.get_face_verification(
            context(tenant_id),
            original.verification_id,
        )

    assert restored == original


def test_face_authentication_round_trip() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        current_consent = consent(tenant_id, identity_id)
        store.add_biometric_consent(current_consent)

        current_enrollment = enrollment(
            tenant_id,
            identity_id,
            current_consent.consent_id,
        )
        store.add_biometric_enrollment(current_enrollment)

        current_verification = verification(
            tenant_id,
            identity_id,
            current_enrollment.enrollment_id,
            current_consent.consent_id,
        )
        store.add_face_verification(current_verification)

        original = authentication(
            tenant_id,
            identity_id,
            current_verification.verification_id,
            current_enrollment.enrollment_id,
        )
        store.add_face_authentication(original)

        restored = store.get_face_authentication(
            context(tenant_id),
            original.authentication_id,
        )

    assert restored == original


def test_liveness_assessment_round_trip() -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        original = liveness(tenant_id, identity_id)

        store.add_liveness_assessment(original)

        restored = store.get_liveness_assessment(
            context(tenant_id),
            original.assessment_id,
        )

    assert restored == original


@pytest.mark.parametrize(
    (
        "getter",
        "identifier_name",
    ),
    (
        ("get_biometric_consent", "consent_id"),
        ("get_biometric_enrollment", "enrollment_id"),
        ("get_face_verification", "verification_id"),
        ("get_face_authentication", "authentication_id"),
        ("get_liveness_assessment", "assessment_id"),
    ),
)
def test_biometric_reads_fail_closed_for_other_tenant(
    getter: str,
    identifier_name: str,
) -> None:
    store = NovaIDUnitOfWork()

    with store:
        tenant_id, identity_id = bootstrap(store)
        other_tenant_id, _ = bootstrap(store)

        current_consent = consent(tenant_id, identity_id)
        store.add_biometric_consent(current_consent)

        current_enrollment = enrollment(
            tenant_id,
            identity_id,
            current_consent.consent_id,
        )
        store.add_biometric_enrollment(current_enrollment)

        current_verification = verification(
            tenant_id,
            identity_id,
            current_enrollment.enrollment_id,
            current_consent.consent_id,
        )
        store.add_face_verification(current_verification)

        current_authentication = authentication(
            tenant_id,
            identity_id,
            current_verification.verification_id,
            current_enrollment.enrollment_id,
        )
        store.add_face_authentication(
            current_authentication
        )

        current_liveness = liveness(
            tenant_id,
            identity_id,
        )
        store.add_liveness_assessment(current_liveness)

        records = {
            "consent_id": current_consent.consent_id,
            "enrollment_id": (
                current_enrollment.enrollment_id
            ),
            "verification_id": (
                current_verification.verification_id
            ),
            "authentication_id": (
                current_authentication.authentication_id
            ),
            "assessment_id": (
                current_liveness.assessment_id
            ),
        }

        with pytest.raises(
            LookupError,
            match="TENANT_ACCESS_DENIED",
        ):
            getattr(store, getter)(
                context(other_tenant_id),
                records[identifier_name],
            )
