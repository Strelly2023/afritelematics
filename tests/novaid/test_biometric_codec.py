from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    AuthenticationStrength,
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
    FaceAuthenticationDecision,
    FaceAuthenticationRecord,
    FaceVerificationDecision,
    FaceVerificationRecord,
    LivenessAssessmentRecord,
    LivenessDecision,
    LivenessMode,
    PresentationAttackType,
)
from afritech.novaid.persistence.biometric_codec import (
    biometric_consent_from_row,
    biometric_enrollment_from_row,
    decode_attack_types,
    decode_capture_device,
    decode_capture_environment,
    decode_capture_quality,
    decode_metadata,
    encode_attack_types,
    encode_capture_device,
    encode_capture_environment,
    encode_capture_quality,
    encode_metadata,
    face_authentication_from_row,
    face_verification_from_row,
    liveness_assessment_from_row,
)


def uid() -> str:
    return str(uuid4())


def device() -> CaptureDevice:
    return CaptureDevice(
        device_reference="device-reference",
        channel=CaptureChannel.MOBILE_APP,
        platform="ios",
        operating_system="iOS",
        application_version="2026.1.0",
        camera_facing="FRONT",
        integrity_verified=True,
        hardware_backed_key_available=True,
    )


def environment() -> CaptureEnvironment:
    return CaptureEnvironment(
        lighting=CaptureLighting.NORMAL,
        network_reference="network-reference",
        country_code="AU",
        location_accuracy_metres=5.0,
        vpn_detected=False,
        emulator_detected=False,
        rooted_or_jailbroken=False,
    )


def quality() -> CaptureQuality:
    return CaptureQuality(
        overall_score=0.93,
        face_detected=True,
        single_subject_detected=True,
        sharpness_score=0.92,
        illumination_score=0.91,
        pose_score=0.90,
        occlusion_score=0.97,
        minimum_required_score=0.70,
        decision=CaptureDecision.ACCEPT,
        reason_codes=("QUALITY_ACCEPTED",),
    )


def test_capture_device_round_trip() -> None:
    original = device()

    restored = decode_capture_device(
        encode_capture_device(original)
    )

    assert restored == original


def test_capture_environment_round_trip() -> None:
    original = environment()

    restored = decode_capture_environment(
        encode_capture_environment(original)
    )

    assert restored == original


def test_capture_quality_round_trip() -> None:
    original = quality()

    restored = decode_capture_quality(
        encode_capture_quality(original)
    )

    assert restored == original


def test_consent_from_sqlite_style_row() -> None:
    now = datetime.now(UTC)

    original = BiometricConsent(
        consent_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        purpose=BiometricPurpose.LOGIN,
        policy_version="2026-07-28.1",
        granted_at=now,
        status=BiometricConsentStatus.ACTIVE,
        expires_at=now + timedelta(days=30),
        capture_notice_version="2026-07",
        lawful_basis_reference="explicit-consent",
        metadata={"channel": "mobile"},
    )

    row = {
        "consent_id": original.consent_id,
        "tenant_id": original.tenant_id,
        "identity_id": original.identity_id,
        "purpose": original.purpose.value,
        "policy_version": original.policy_version,
        "granted_at": original.granted_at.isoformat(),
        "status": original.status.value,
        "expires_at": original.expires_at.isoformat(),
        "revoked_at": None,
        "capture_notice_version": (
            original.capture_notice_version
        ),
        "lawful_basis_reference": (
            original.lawful_basis_reference
        ),
        "metadata": encode_metadata(
            original.metadata
        ),
    }

    restored = biometric_consent_from_row(row)

    assert restored == original


def test_enrollment_round_trip_from_mapping_row() -> None:
    now = datetime.now(UTC)

    original = BiometricEnrollment(
        enrollment_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        biometric_type=BiometricType.FACE,
        purpose=BiometricPurpose.ENROLLMENT,
        consent_id=uid(),
        template_reference=(
            "vault://biometrics/template-reference"
        ),
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        status=BiometricEnrollmentStatus.ACTIVE,
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        enrolled_at=now,
        expires_at=now + timedelta(days=365),
        created_at=now,
        updated_at=now,
        version=2,
        metadata={"environment": "pilot"},
    )

    row = {
        "enrollment_id": original.enrollment_id,
        "tenant_id": original.tenant_id,
        "identity_id": original.identity_id,
        "biometric_type": original.biometric_type.value,
        "purpose": original.purpose.value,
        "consent_id": original.consent_id,
        "template_reference": (
            original.template_reference
        ),
        "provider_reference": (
            original.provider_reference
        ),
        "algorithm_version": (
            original.algorithm_version
        ),
        "status": original.status.value,
        "capture_device": encode_capture_device(
            original.capture_device
        ),
        "capture_environment": (
            encode_capture_environment(
                original.capture_environment
            )
        ),
        "capture_quality": encode_capture_quality(
            original.capture_quality
        ),
        "enrolled_at": original.enrolled_at.isoformat(),
        "expires_at": original.expires_at.isoformat(),
        "revoked_at": None,
        "created_at": original.created_at.isoformat(),
        "updated_at": original.updated_at.isoformat(),
        "version": original.version,
        "metadata": encode_metadata(original.metadata),
    }

    restored = biometric_enrollment_from_row(row)

    assert restored == original


def test_face_verification_round_trip() -> None:
    now = datetime.now(UTC)

    original = FaceVerificationRecord(
        verification_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        enrollment_id=uid(),
        consent_id=uid(),
        purpose=BiometricPurpose.LOGIN,
        decision=FaceVerificationDecision.MATCH,
        similarity_score=0.94,
        match_threshold=0.85,
        manual_review_threshold=0.65,
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        verified_at=now,
        version=1,
        reason_codes=("PROVIDER_EVALUATED",),
        metadata={"source": "codec-test"},
    )

    row = {
        "verification_id": original.verification_id,
        "tenant_id": original.tenant_id,
        "identity_id": original.identity_id,
        "enrollment_id": original.enrollment_id,
        "consent_id": original.consent_id,
        "purpose": original.purpose.value,
        "decision": original.decision.value,
        "similarity_score": original.similarity_score,
        "match_threshold": original.match_threshold,
        "manual_review_threshold": (
            original.manual_review_threshold
        ),
        "provider_reference": (
            original.provider_reference
        ),
        "algorithm_version": (
            original.algorithm_version
        ),
        "capture_device": encode_capture_device(
            original.capture_device
        ),
        "capture_environment": (
            encode_capture_environment(
                original.capture_environment
            )
        ),
        "capture_quality": encode_capture_quality(
            original.capture_quality
        ),
        "verified_at": original.verified_at.isoformat(),
        "version": original.version,
        "reason_codes": json.dumps(
            list(original.reason_codes)
        ),
        "metadata": encode_metadata(original.metadata),
    }

    restored = face_verification_from_row(row)

    assert restored == original


def test_face_authentication_round_trip() -> None:
    now = datetime.now(UTC)

    original = FaceAuthenticationRecord(
        authentication_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        verification_id=uid(),
        enrollment_id=uid(),
        purpose=BiometricPurpose.LOGIN,
        decision=FaceAuthenticationDecision.ALLOW,
        verification_decision=(
            FaceVerificationDecision.MATCH
        ),
        risk_score=0.12,
        authentication_strength=(
            AuthenticationStrength.PASSKEY
        ),
        current_assurance_level=(
            AssuranceLevel.NID_AL2
        ),
        required_assurance_level=(
            AssuranceLevel.NID_AL1
        ),
        authenticated_at=now,
        reason_codes=(
            "FACE_AUTHENTICATION_CONTROLS_SATISFIED",
        ),
        metadata={"source": "codec-test"},
    )

    row = {
        "authentication_id": (
            original.authentication_id
        ),
        "tenant_id": original.tenant_id,
        "identity_id": original.identity_id,
        "verification_id": (
            original.verification_id
        ),
        "enrollment_id": original.enrollment_id,
        "purpose": original.purpose.value,
        "decision": original.decision.value,
        "verification_decision": (
            original.verification_decision.value
        ),
        "risk_score": original.risk_score,
        "authentication_strength": (
            original.authentication_strength.value
        ),
        "current_assurance_level": (
            original.current_assurance_level.value
        ),
        "required_assurance_level": (
            original.required_assurance_level.value
        ),
        "authenticated_at": (
            original.authenticated_at.isoformat()
        ),
        "reason_codes": json.dumps(
            list(original.reason_codes)
        ),
        "metadata": encode_metadata(original.metadata),
    }

    restored = face_authentication_from_row(row)

    assert restored == original


def test_liveness_assessment_round_trip() -> None:
    now = datetime.now(UTC)

    original = LivenessAssessmentRecord(
        assessment_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        purpose=BiometricPurpose.LOGIN,
        decision=LivenessDecision.PASS,
        attempt_number=1,
        mode=LivenessMode.HYBRID,
        liveness_score=0.95,
        presentation_attack_score=0.04,
        provider_reference="provider-reference",
        algorithm_version="pad-model-1.0",
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        assessed_at=now,
        detected_attack_types=frozenset(
            {
                PresentationAttackType.NONE,
            }
        ),
        reason_codes=(
            "LIVENESS_CONTROLS_SATISFIED",
        ),
        metadata={"source": "codec-test"},
    )

    row = {
        "assessment_id": original.assessment_id,
        "tenant_id": original.tenant_id,
        "identity_id": original.identity_id,
        "purpose": original.purpose.value,
        "decision": original.decision.value,
        "attempt_number": original.attempt_number,
        "mode": original.mode.value,
        "liveness_score": original.liveness_score,
        "presentation_attack_score": (
            original.presentation_attack_score
        ),
        "provider_reference": (
            original.provider_reference
        ),
        "algorithm_version": (
            original.algorithm_version
        ),
        "capture_device": encode_capture_device(
            original.capture_device
        ),
        "capture_environment": (
            encode_capture_environment(
                original.capture_environment
            )
        ),
        "capture_quality": encode_capture_quality(
            original.capture_quality
        ),
        "assessed_at": original.assessed_at.isoformat(),
        "detected_attack_types": encode_attack_types(
            original.detected_attack_types
        ),
        "reason_codes": json.dumps(
            list(original.reason_codes)
        ),
        "metadata": encode_metadata(original.metadata),
    }

    restored = liveness_assessment_from_row(row)

    assert restored == original


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64-data"},
        {"raw_video": "blob-reference"},
        {"embedding": [0.1, 0.2]},
        {"feature_vector": [1, 2, 3]},
        {"provider_secret": "secret"},
        {"private_key": "secret"},
    ),
)
def test_raw_biometric_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="RAW_BIOMETRIC_MATERIAL_FORBIDDEN",
    ):
        encode_metadata(metadata)


def test_raw_material_is_rejected_during_decode() -> None:
    with pytest.raises(
        ValueError,
        match="RAW_BIOMETRIC_MATERIAL_FORBIDDEN",
    ):
        decode_metadata(
            json.dumps(
                {
                    "embedding": [0.1, 0.2],
                }
            )
        )


def test_attack_types_round_trip() -> None:
    original = frozenset(
        {
            PresentationAttackType.DEEPFAKE,
            PresentationAttackType.CAMERA_INJECTION,
        }
    )

    assert decode_attack_types(
        encode_attack_types(original)
    ) == original
