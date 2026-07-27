from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    Identity,
    IdentityStatus,
    RequestContext,
    VerificationStatus,
)
from afritech.novaid.domain.verification_events import (
    IdentityVerificationEvent,
)
from afritech.novaid.domain.verification_service import (
    IdentityVerificationService,
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
        authentication_strength="PASSWORD_OTP",
    )


def identity(
    tenant_id: str,
    *,
    verification_status: VerificationStatus = (
        VerificationStatus.UNVERIFIED
    ),
    assurance_level: AssuranceLevel = AssuranceLevel.NID_AL0,
) -> Identity:
    return Identity(
        identity_id=uid(),
        tenant_id=tenant_id,
        normalized_email="verification@example.com",
        status=IdentityStatus.PENDING_VERIFICATION,
        verification_status=verification_status,
        assurance_level=assurance_level,
    )


def test_complete_verification_flow_elevates_assurance() -> None:
    tenant_id = uid()
    service = IdentityVerificationService()
    ctx = context(tenant_id)
    original = identity(tenant_id)

    pending = service.start(
        context=ctx,
        identity=original,
        expected_version=original.version,
    ).identity

    in_progress = service.begin_processing(
        context=ctx,
        identity=pending,
        expected_version=pending.version,
    ).identity

    verified_result = service.approve(
        context=ctx,
        identity=in_progress,
        expected_version=in_progress.version,
        assurance_level=AssuranceLevel.NID_AL2,
        metadata={"evidence": "document-and-biometric"},
    )

    verified = verified_result.identity

    assert verified.verification_status is VerificationStatus.VERIFIED
    assert verified.assurance_level is AssuranceLevel.NID_AL2
    assert verified.status is IdentityStatus.PENDING_VERIFICATION
    assert verified.version == original.version + 3
    assert verified_result.event.event_type == "IDENTITY_VERIFIED"
    assert verified_result.event.identity_version == verified.version


def test_manual_review_can_approve_identity() -> None:
    tenant_id = uid()
    service = IdentityVerificationService()
    ctx = context(tenant_id)

    pending = service.start(
        context=ctx,
        identity=identity(tenant_id),
        expected_version=1,
    ).identity

    in_progress = service.begin_processing(
        context=ctx,
        identity=pending,
        expected_version=pending.version,
    ).identity

    review = service.require_manual_review(
        context=ctx,
        identity=in_progress,
        expected_version=in_progress.version,
    ).identity

    verified = service.approve(
        context=ctx,
        identity=review,
        expected_version=review.version,
        assurance_level=AssuranceLevel.NID_AL3,
    ).identity

    assert verified.verification_status is VerificationStatus.VERIFIED
    assert verified.assurance_level is AssuranceLevel.NID_AL3


def test_invalid_verification_transition_fails_closed() -> None:
    tenant_id = uid()
    current = identity(tenant_id)

    with pytest.raises(
        ValueError,
        match="INVALID_VERIFICATION_TRANSITION",
    ):
        IdentityVerificationService().approve(
            context=context(tenant_id),
            identity=current,
            expected_version=current.version,
            assurance_level=AssuranceLevel.NID_AL2,
        )


def test_verified_identity_requires_nonzero_assurance() -> None:
    tenant_id = uid()
    current = identity(
        tenant_id,
        verification_status=VerificationStatus.IN_PROGRESS,
    )

    with pytest.raises(
        ValueError,
        match="VERIFIED_ASSURANCE_LEVEL_TOO_LOW",
    ):
        IdentityVerificationService().approve(
            context=context(tenant_id),
            identity=current,
            expected_version=current.version,
            assurance_level=AssuranceLevel.NID_AL0,
        )


def test_assurance_downgrade_is_denied() -> None:
    tenant_id = uid()
    current = identity(
        tenant_id,
        verification_status=VerificationStatus.IN_PROGRESS,
        assurance_level=AssuranceLevel.NID_AL3,
    )

    with pytest.raises(
        ValueError,
        match="ASSURANCE_LEVEL_DOWNGRADE_DENIED",
    ):
        IdentityVerificationService().approve(
            context=context(tenant_id),
            identity=current,
            expected_version=current.version,
            assurance_level=AssuranceLevel.NID_AL2,
        )


def test_nonverified_transition_cannot_change_assurance() -> None:
    tenant_id = uid()
    current = identity(tenant_id)

    with pytest.raises(
        ValueError,
        match="ASSURANCE_LEVEL_ONLY_ALLOWED_FOR_VERIFIED",
    ):
        IdentityVerificationService().transition(
            context=context(tenant_id),
            identity=current,
            target=VerificationStatus.PENDING,
            expected_version=current.version,
            assurance_level=AssuranceLevel.NID_AL1,
        )


def test_cross_tenant_verification_fails_closed() -> None:
    current = identity(uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        IdentityVerificationService().start(
            context=context(uid()),
            identity=current,
            expected_version=current.version,
        )


def test_stale_verification_decision_is_rejected() -> None:
    tenant_id = uid()
    current = identity(tenant_id)

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        IdentityVerificationService().start(
            context=context(tenant_id),
            identity=current,
            expected_version=current.version + 1,
        )


def test_rejected_identity_can_restart_verification() -> None:
    tenant_id = uid()
    current = identity(
        tenant_id,
        verification_status=VerificationStatus.REJECTED,
    )

    restarted = IdentityVerificationService().start(
        context=context(tenant_id),
        identity=current,
        expected_version=current.version,
    ).identity

    assert restarted.verification_status is VerificationStatus.PENDING


def test_verification_events_are_immutable() -> None:
    tenant_id = uid()
    current = identity(tenant_id)

    event = IdentityVerificationService().start(
        context=context(tenant_id),
        identity=current,
        expected_version=current.version,
    ).event

    assert isinstance(event, IdentityVerificationEvent)

    with pytest.raises(FrozenInstanceError):
        event.event_type = "CHANGED"  # type: ignore[misc]
