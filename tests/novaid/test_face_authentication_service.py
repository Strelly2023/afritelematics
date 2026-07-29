from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    AuthenticationStrength,
    BiometricPurpose,
    CaptureChannel,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    FaceAuthenticationContext,
    FaceAuthenticationDecision,
    FaceAuthenticationEvent,
    FaceAuthenticationPolicy,
    FaceAuthenticationService,
    FaceVerificationDecision,
    FaceVerificationRecord,
    IdentityStatus,
    RequestContext,
    Tenant,
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


def tenant(tenant_id: str) -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name="Face Authentication Tenant",
    )


def verification(
    tenant_id: str,
    identity_id: str,
    *,
    decision: FaceVerificationDecision = (
        FaceVerificationDecision.MATCH
    ),
    purpose: BiometricPurpose = BiometricPurpose.LOGIN,
) -> FaceVerificationRecord:
    return FaceVerificationRecord(
        verification_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        enrollment_id=uid(),
        consent_id=uid(),
        purpose=purpose,
        decision=decision,
        similarity_score=(
            0.92
            if decision is FaceVerificationDecision.MATCH
            else 0.70
        ),
        match_threshold=0.85,
        manual_review_threshold=0.65,
        provider_reference="provider-reference",
        algorithm_version="face-model-1.0",
        capture_device=CaptureDevice(
            device_reference="device-reference",
            channel=CaptureChannel.MOBILE_APP,
            integrity_verified=True,
        ),
        capture_environment=CaptureEnvironment(
            country_code="AU",
        ),
        capture_quality=CaptureQuality(
            overall_score=0.92,
            face_detected=True,
            single_subject_detected=True,
        ),
        verified_at=datetime.now(UTC),
    )


def authentication_context(
    tenant_id: str,
    identity_id: str,
    *,
    verification_decision: FaceVerificationDecision = (
        FaceVerificationDecision.MATCH
    ),
    identity_status: IdentityStatus = IdentityStatus.ACTIVE,
    membership_active: bool = True,
    credential_active: bool = True,
    authentication_strength: AuthenticationStrength = (
        AuthenticationStrength.PASSKEY
    ),
    current_assurance: AssuranceLevel = AssuranceLevel.NID_AL2,
    required_assurance: AssuranceLevel = AssuranceLevel.NID_AL1,
    risk_score: float = 0.10,
    session_active: bool = True,
    failed_attempts: int = 0,
) -> FaceAuthenticationContext:
    return FaceAuthenticationContext(
        verification=verification(
            tenant_id,
            identity_id,
            decision=verification_decision,
        ),
        identity_status=identity_status,
        membership_active=membership_active,
        credential_active=credential_active,
        authentication_strength=authentication_strength,
        current_assurance_level=current_assurance,
        required_assurance_level=required_assurance,
        risk_score=risk_score,
        session_active=session_active,
        previous_failed_attempts=failed_attempts,
        purpose=BiometricPurpose.LOGIN,
    )


def authenticate(
    *,
    tenant_id: str,
    identity_id: str,
    context: FaceAuthenticationContext | None = None,
    policy: FaceAuthenticationPolicy | None = None,
):
    return FaceAuthenticationService().authenticate(
        request_context=request_context(tenant_id),
        tenant=tenant(tenant_id),
        authentication_context=(
            context
            or authentication_context(
                tenant_id,
                identity_id,
            )
        ),
        policy=policy,
    )


def test_matching_face_with_satisfied_controls_is_allowed() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
    )

    assert (
        result.authentication.decision
        is FaceAuthenticationDecision.ALLOW
    )
    assert result.authentication.reason_codes == (
        "FACE_AUTHENTICATION_CONTROLS_SATISFIED",
    )


@pytest.mark.parametrize(
    ("decision", "expected"),
    (
        (
            FaceVerificationDecision.NO_MATCH,
            FaceAuthenticationDecision.DENY,
        ),
        (
            FaceVerificationDecision.MANUAL_REVIEW,
            FaceAuthenticationDecision.REQUIRE_MANUAL_REVIEW,
        ),
    ),
)
def test_face_verification_decision_is_enforced(
    decision: FaceVerificationDecision,
    expected: FaceAuthenticationDecision,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            verification_decision=decision,
        ),
    )

    assert result.authentication.decision is expected


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        (
            "identity_status",
            IdentityStatus.SUSPENDED,
            "IDENTITY_NOT_ACTIVE",
        ),
        (
            "membership_active",
            False,
            "MEMBERSHIP_NOT_ACTIVE",
        ),
        (
            "credential_active",
            False,
            "CREDENTIAL_NOT_ACTIVE",
        ),
        (
            "session_active",
            False,
            "SESSION_NOT_ACTIVE",
        ),
    ),
)
def test_inactive_security_bindings_are_denied(
    field: str,
    value: object,
    reason: str,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    arguments = {
        "identity_status": IdentityStatus.ACTIVE,
        "membership_active": True,
        "credential_active": True,
        "session_active": True,
    }
    arguments[field] = value

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            **arguments,
        ),
    )

    assert (
        result.authentication.decision
        is FaceAuthenticationDecision.DENY
    )
    assert result.authentication.reason_codes == (reason,)


def test_weak_authentication_requires_step_up() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            authentication_strength=(
                AuthenticationStrength.PASSWORD
            ),
        ),
    )

    assert (
        result.authentication.decision
        is FaceAuthenticationDecision.REQUIRE_STEP_UP
    )


def test_insufficient_assurance_requires_step_up() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            current_assurance=AssuranceLevel.NID_AL1,
            required_assurance=AssuranceLevel.NID_AL2,
        ),
    )

    assert (
        result.authentication.decision
        is FaceAuthenticationDecision.REQUIRE_STEP_UP
    )


def test_elevated_risk_requires_step_up() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            risk_score=0.70,
        ),
    )

    assert (
        result.authentication.decision
        is FaceAuthenticationDecision.REQUIRE_STEP_UP
    )


@pytest.mark.parametrize(
    ("risk_score", "expected"),
    (
        (
            0.85,
            FaceAuthenticationDecision.LOCK_SESSION,
        ),
        (
            0.96,
            FaceAuthenticationDecision.LOCK_IDENTITY,
        ),
    ),
)
def test_high_risk_causes_lock_decision(
    risk_score: float,
    expected: FaceAuthenticationDecision,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            risk_score=risk_score,
        ),
    )

    assert result.authentication.decision is expected


@pytest.mark.parametrize(
    ("attempts", "expected"),
    (
        (
            3,
            FaceAuthenticationDecision.LOCK_SESSION,
        ),
        (
            5,
            FaceAuthenticationDecision.LOCK_IDENTITY,
        ),
    ),
)
def test_failure_thresholds_cause_lock_decision(
    attempts: int,
    expected: FaceAuthenticationDecision,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
        context=authentication_context(
            tenant_id,
            identity_id,
            failed_attempts=attempts,
        ),
    )

    assert result.authentication.decision is expected


def test_cross_tenant_request_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        FaceAuthenticationService().authenticate(
            request_context=request_context(uid()),
            tenant=tenant(tenant_id),
            authentication_context=authentication_context(
                tenant_id,
                identity_id,
            ),
        )


def test_verification_tenant_mismatch_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        PermissionError,
        match="FACE_VERIFICATION_TENANT_MISMATCH",
    ):
        FaceAuthenticationService().authenticate(
            request_context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            authentication_context=authentication_context(
                uid(),
                identity_id,
            ),
        )


def test_authentication_event_is_traceable() -> None:
    tenant_id = uid()
    identity_id = uid()
    context = request_context(tenant_id)

    result = FaceAuthenticationService().authenticate(
        request_context=context,
        tenant=tenant(tenant_id),
        authentication_context=authentication_context(
            tenant_id,
            identity_id,
        ),
    )

    event = result.event

    assert isinstance(event, FaceAuthenticationEvent)
    assert event.actor_identity_id == context.actor_identity_id
    assert event.correlation_id == context.correlation_id
    assert event.request_id == context.request_id
    assert event.event_type == "FACE_AUTHENTICATION_ALLOW"


def test_result_record_and_event_are_immutable() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = authenticate(
        tenant_id=tenant_id,
        identity_id=identity_id,
    )

    with pytest.raises(FrozenInstanceError):
        result.authentication = (  # type: ignore[misc]
            result.authentication
        )

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]


@pytest.mark.parametrize(
    "risk_score",
    (-0.1, 1.1),
)
def test_invalid_risk_score_is_rejected(
    risk_score: float,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    with pytest.raises(
        ValueError,
        match="INVALID_RISK_SCORE",
    ):
        authentication_context(
            tenant_id,
            identity_id,
            risk_score=risk_score,
        )


def test_context_contains_no_raw_biometric_media() -> None:
    tenant_id = uid()
    identity_id = uid()

    current = authentication_context(
        tenant_id,
        identity_id,
    )

    assert not hasattr(current, "raw_image")
    assert not hasattr(current, "embedding")
    assert not hasattr(current, "video")
