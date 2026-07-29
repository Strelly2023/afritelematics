from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    BiometricPurpose,
    CaptureChannel,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    LivenessAssessmentEvent,
    LivenessAssessmentService,
    LivenessDecision,
    LivenessEvidence,
    LivenessMode,
    LivenessPolicy,
    PresentationAttackType,
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
        name="Liveness Tenant",
        security_policy=TenantSecurityPolicy(
            device_binding_required=require_integrity,
        ),
    )


def device(
    *,
    integrity_verified: bool = True,
) -> CaptureDevice:
    return CaptureDevice(
        device_reference="liveness-device",
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
    score: float = 0.92,
) -> CaptureQuality:
    return CaptureQuality(
        overall_score=score,
        face_detected=True,
        single_subject_detected=True,
    )


def evidence(
    score: float,
    *,
    attack_score: float = 0.05,
    attacks: frozenset[
        PresentationAttackType
    ] = frozenset(
        {
            PresentationAttackType.NONE,
        }
    ),
) -> LivenessEvidence:
    return LivenessEvidence(
        provider_reference="liveness-provider-reference",
        algorithm_version="pad-model-1.0",
        mode=LivenessMode.HYBRID,
        liveness_score=score,
        presentation_attack_score=attack_score,
        depth_score=0.91,
        motion_score=0.90,
        texture_score=0.92,
        detected_attack_types=attacks,
    )


def assess(
    *,
    tenant_id: str,
    identity_id: str,
    current_evidence: LivenessEvidence,
    attempt_number: int = 1,
    current_tenant: Tenant | None = None,
    current_device: CaptureDevice | None = None,
    current_environment: CaptureEnvironment | None = None,
    current_quality: CaptureQuality | None = None,
    policy: LivenessPolicy | None = None,
):
    return LivenessAssessmentService().assess(
        context=context(tenant_id),
        tenant=current_tenant or tenant(tenant_id),
        identity_id=identity_id,
        purpose=BiometricPurpose.LOGIN,
        attempt_number=attempt_number,
        capture_device=current_device or device(),
        capture_environment=(
            current_environment or environment()
        ),
        capture_quality=current_quality or quality(),
        evidence=current_evidence,
        policy=policy,
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    (
        (0.91, LivenessDecision.PASS),
        (0.75, LivenessDecision.MANUAL_REVIEW),
        (0.55, LivenessDecision.RECAPTURE),
        (0.30, LivenessDecision.FAIL),
    ),
)
def test_liveness_score_decisions(
    score: float,
    expected: LivenessDecision,
) -> None:
    tenant_id = uid()

    result = assess(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(score),
    )

    assert result.assessment.decision is expected
    assert result.event.decision is expected


@pytest.mark.parametrize(
    "attack",
    (
        PresentationAttackType.PRINTED_PHOTO,
        PresentationAttackType.SCREEN_REPLAY,
        PresentationAttackType.VIDEO_REPLAY,
        PresentationAttackType.MASK,
    ),
)
def test_detected_attack_fails_assessment(
    attack: PresentationAttackType,
) -> None:
    tenant_id = uid()

    result = assess(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            0.95,
            attacks=frozenset({attack}),
        ),
    )

    assert (
        result.assessment.decision
        is LivenessDecision.FAIL
    )
    assert result.assessment.reason_codes == (
        "PRESENTATION_ATTACK_DETECTED",
    )


@pytest.mark.parametrize(
    "attack",
    (
        PresentationAttackType.DEEPFAKE,
        PresentationAttackType.CAMERA_INJECTION,
        PresentationAttackType.VIRTUAL_CAMERA,
        PresentationAttackType.SYNTHETIC_MEDIA,
    ),
)
def test_severe_attack_locks_session(
    attack: PresentationAttackType,
) -> None:
    tenant_id = uid()

    result = assess(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            0.99,
            attacks=frozenset({attack}),
        ),
    )

    assert (
        result.assessment.decision
        is LivenessDecision.LOCK_SESSION
    )


def test_attempt_limit_locks_session() -> None:
    tenant_id = uid()

    result = assess(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(0.95),
        attempt_number=4,
        policy=LivenessPolicy(
            maximum_attempts=3,
        ),
    )

    assert (
        result.assessment.decision
        is LivenessDecision.LOCK_SESSION
    )


def test_elevated_attack_score_requires_review() -> None:
    tenant_id = uid()

    result = assess(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            0.95,
            attack_score=0.50,
        ),
    )

    assert (
        result.assessment.decision
        is LivenessDecision.MANUAL_REVIEW
    )


def test_cross_tenant_assessment_fails_closed() -> None:
    tenant_id = uid()

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        LivenessAssessmentService().assess(
            context=context(uid()),
            tenant=tenant(tenant_id),
            identity_id=uid(),
            purpose=BiometricPurpose.LOGIN,
            attempt_number=1,
            capture_device=device(),
            capture_environment=environment(),
            capture_quality=quality(),
            evidence=evidence(0.95),
        )


def test_device_integrity_policy_is_enforced() -> None:
    tenant_id = uid()

    with pytest.raises(
        PermissionError,
        match="CAPTURE_DEVICE_INTEGRITY_REQUIRED",
    ):
        assess(
            tenant_id=tenant_id,
            identity_id=uid(),
            current_evidence=evidence(0.95),
            current_tenant=tenant(
                tenant_id,
                require_integrity=True,
            ),
            current_device=device(
                integrity_verified=False,
            ),
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
def test_compromised_environment_is_rejected(
    capture_environment: CaptureEnvironment,
    error: str,
) -> None:
    tenant_id = uid()

    with pytest.raises(
        PermissionError,
        match=error,
    ):
        assess(
            tenant_id=tenant_id,
            identity_id=uid(),
            current_evidence=evidence(0.95),
            current_environment=capture_environment,
        )


def test_capture_quality_policy_is_enforced() -> None:
    tenant_id = uid()

    with pytest.raises(
        ValueError,
        match="LIVENESS_CAPTURE_QUALITY_BELOW_POLICY",
    ):
        assess(
            tenant_id=tenant_id,
            identity_id=uid(),
            current_evidence=evidence(0.95),
            current_quality=quality(0.75),
            policy=LivenessPolicy(
                minimum_capture_quality_score=0.80,
            ),
        )


def test_inconsistent_attack_types_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="INCONSISTENT_PRESENTATION_ATTACK_TYPES",
    ):
        evidence(
            0.95,
            attacks=frozenset(
                {
                    PresentationAttackType.NONE,
                    PresentationAttackType.PRINTED_PHOTO,
                }
            ),
        )


@pytest.mark.parametrize(
    ("recapture", "review", "passed"),
    (
        (0.70, 0.65, 0.85),
        (0.45, 0.85, 0.85),
        (0.45, 0.90, 0.85),
    ),
)
def test_invalid_threshold_order_is_rejected(
    recapture: float,
    review: float,
    passed: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_LIVENESS_THRESHOLD_ORDER",
    ):
        LivenessPolicy(
            recapture_threshold=recapture,
            manual_review_threshold=review,
            pass_threshold=passed,
        )


def test_event_is_traceable() -> None:
    tenant_id = uid()
    request_context = context(tenant_id)

    result = LivenessAssessmentService().assess(
        context=request_context,
        tenant=tenant(tenant_id),
        identity_id=uid(),
        purpose=BiometricPurpose.LOGIN,
        attempt_number=1,
        capture_device=device(),
        capture_environment=environment(),
        capture_quality=quality(),
        evidence=evidence(0.95),
    )

    event = result.event

    assert isinstance(event, LivenessAssessmentEvent)
    assert event.actor_identity_id == (
        request_context.actor_identity_id
    )
    assert event.correlation_id == (
        request_context.correlation_id
    )
    assert event.request_id == (
        request_context.request_id
    )
    assert event.event_type == "LIVENESS_ASSESSMENT_PASS"


def test_result_record_and_event_are_immutable() -> None:
    tenant_id = uid()

    result = assess(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(0.95),
    )

    with pytest.raises(FrozenInstanceError):
        result.assessment = result.assessment  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]


def test_liveness_domain_contains_no_raw_media() -> None:
    current = evidence(0.95)

    assert not hasattr(current, "raw_video")
    assert not hasattr(current, "raw_image")
    assert not hasattr(current, "frames")
    assert not hasattr(current, "embedding")
