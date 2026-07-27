from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    Identity,
    IdentityStatus,
    RequestContext,
)
from afritech.novaid.domain.identity_events import (
    IdentityLifecycleEvent,
)
from afritech.novaid.domain.identity_service import (
    IdentityLifecycleService,
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
    status: IdentityStatus = IdentityStatus.PENDING_VERIFICATION,
) -> Identity:
    return Identity(
        identity_id=uid(),
        tenant_id=tenant_id,
        normalized_email="lifecycle@example.com",
        status=status,
    )


def test_activation_returns_transitioned_identity_and_event() -> None:
    tenant_id = uid()
    current = identity(tenant_id)
    service = IdentityLifecycleService()

    result = service.activate(
        context=context(tenant_id),
        identity=current,
        expected_version=current.version,
        metadata={"reason": "verification_completed"},
    )

    assert result.identity.status is IdentityStatus.ACTIVE
    assert result.identity.version == current.version + 1
    assert result.event.event_type == "IDENTITY_ACTIVATED"
    assert result.event.previous_status is IdentityStatus.PENDING_VERIFICATION
    assert result.event.current_status is IdentityStatus.ACTIVE
    assert result.event.identity_version == result.identity.version
    assert result.event.metadata == {
        "reason": "verification_completed"
    }


def test_invalid_transition_is_rejected_by_aggregate() -> None:
    tenant_id = uid()
    current = identity(
        tenant_id,
        IdentityStatus.PENDING_VERIFICATION,
    )

    with pytest.raises(
        ValueError,
        match="INVALID_IDENTITY_TRANSITION",
    ):
        IdentityLifecycleService().delete(
            context=context(tenant_id),
            identity=current,
            expected_version=current.version,
        )


def test_cross_tenant_transition_fails_closed() -> None:
    current = identity(uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        IdentityLifecycleService().activate(
            context=context(uid()),
            identity=current,
            expected_version=current.version,
        )


def test_stale_version_is_rejected() -> None:
    tenant_id = uid()
    current = identity(tenant_id)

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        IdentityLifecycleService().activate(
            context=context(tenant_id),
            identity=current,
            expected_version=current.version + 1,
        )


def test_lock_suspend_disable_and_delete_lifecycle() -> None:
    tenant_id = uid()
    service = IdentityLifecycleService()
    ctx = context(tenant_id)

    active = service.activate(
        context=ctx,
        identity=identity(tenant_id),
        expected_version=1,
    ).identity

    locked = service.lock(
        context=ctx,
        identity=active,
        expected_version=active.version,
    ).identity

    reactivated = service.activate(
        context=ctx,
        identity=locked,
        expected_version=locked.version,
    ).identity

    suspended = service.suspend(
        context=ctx,
        identity=reactivated,
        expected_version=reactivated.version,
    ).identity

    active_again = service.activate(
        context=ctx,
        identity=suspended,
        expected_version=suspended.version,
    ).identity

    disabled = service.disable(
        context=ctx,
        identity=active_again,
        expected_version=active_again.version,
    ).identity

    deleted = service.delete(
        context=ctx,
        identity=disabled,
        expected_version=disabled.version,
    ).identity

    assert deleted.status is IdentityStatus.DELETED
    assert deleted.version == 8


def test_lifecycle_events_are_immutable() -> None:
    tenant_id = uid()
    current = identity(tenant_id)

    event = IdentityLifecycleService().activate(
        context=context(tenant_id),
        identity=current,
        expected_version=current.version,
    ).event

    assert isinstance(event, IdentityLifecycleEvent)

    with pytest.raises(FrozenInstanceError):
        event.event_type = "CHANGED"  # type: ignore[misc]
