from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AuthenticationStrength,
    LegalEntity,
    RequestContext,
    Tenant,
    TenantBrand,
    TenantLifecycleEvent,
    TenantLifecycleService,
    TenantSecurityPolicy,
    TenantSettings,
    TenantStatus,
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
        authentication_strength=(
            AuthenticationStrength.PASSKEY.value
        ),
    )


def tenant(
    tenant_id: str,
    *,
    status: TenantStatus = TenantStatus.ACTIVE,
) -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name="NovaTech Tenant",
        status=status,
        legal_entity=LegalEntity(
            legal_name="NovaTech Australia Pty Ltd",
            registration_number="ACN-123456789",
            country_code="AU",
        ),
        brand=TenantBrand(
            display_name="NovaTech",
            primary_domain="afritechnology.com",
            support_email="support@afritechnology.com",
        ),
        settings=TenantSettings(
            federation_enabled=True,
            feature_flags=frozenset(
                {
                    "novaid",
                    "novapay",
                    "novaride",
                }
            ),
        ),
        security_policy=TenantSecurityPolicy(
            minimum_authentication_strength=(
                AuthenticationStrength.PASSKEY
            ),
            phishing_resistant_authentication_required=True,
        ),
        metadata={
            "environment": "controlled-pilot",
        },
    )


def test_suspend_returns_transitioned_tenant_and_event() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    result = TenantLifecycleService().suspend(
        context=context(tenant_id),
        tenant=current,
        expected_version=current.version,
        metadata={
            "reason": "security-review",
        },
    )

    assert result.tenant.status is TenantStatus.SUSPENDED
    assert result.tenant.version == current.version + 1

    assert result.event.event_type == "TENANT_SUSPENDED"
    assert result.event.previous_status is TenantStatus.ACTIVE
    assert result.event.current_status is TenantStatus.SUSPENDED
    assert result.event.tenant_version == result.tenant.version
    assert result.event.metadata == {
        "reason": "security-review",
    }


def test_reactivate_suspended_tenant() -> None:
    tenant_id = uid()
    suspended = tenant(
        tenant_id,
        status=TenantStatus.SUSPENDED,
    )

    result = TenantLifecycleService().reactivate(
        context=context(tenant_id),
        tenant=suspended,
        expected_version=suspended.version,
    )

    assert result.tenant.status is TenantStatus.ACTIVE
    assert result.event.event_type == "TENANT_REACTIVATED"


def test_reactivate_disabled_tenant() -> None:
    tenant_id = uid()
    disabled = tenant(
        tenant_id,
        status=TenantStatus.DISABLED,
    )

    result = TenantLifecycleService().reactivate(
        context=context(tenant_id),
        tenant=disabled,
        expected_version=disabled.version,
    )

    assert result.tenant.status is TenantStatus.ACTIVE
    assert result.event.previous_status is TenantStatus.DISABLED
    assert result.event.current_status is TenantStatus.ACTIVE


def test_disable_active_tenant() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    result = TenantLifecycleService().disable(
        context=context(tenant_id),
        tenant=current,
        expected_version=current.version,
    )

    assert result.tenant.status is TenantStatus.DISABLED
    assert result.event.event_type == "TENANT_DISABLED"


def test_disable_suspended_tenant() -> None:
    tenant_id = uid()
    suspended = tenant(
        tenant_id,
        status=TenantStatus.SUSPENDED,
    )

    result = TenantLifecycleService().disable(
        context=context(tenant_id),
        tenant=suspended,
        expected_version=suspended.version,
    )

    assert result.tenant.status is TenantStatus.DISABLED


def test_invalid_transition_is_rejected_by_aggregate() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    with pytest.raises(
        ValueError,
        match="INVALID_TENANT_TRANSITION",
    ):
        TenantLifecycleService().reactivate(
            context=context(tenant_id),
            tenant=current,
            expected_version=current.version,
        )


def test_cross_tenant_transition_fails_closed() -> None:
    current = tenant(uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        TenantLifecycleService().suspend(
            context=context(uid()),
            tenant=current,
            expected_version=current.version,
        )


def test_stale_version_is_rejected() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        TenantLifecycleService().suspend(
            context=context(tenant_id),
            tenant=current,
            expected_version=current.version + 1,
        )


def test_invalid_expected_version_is_rejected() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    with pytest.raises(
        ValueError,
        match="INVALID_EXPECTED_VERSION",
    ):
        TenantLifecycleService().suspend(
            context=context(tenant_id),
            tenant=current,
            expected_version=0,
        )


def test_transition_preserves_full_tenant_profile() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    result = TenantLifecycleService().suspend(
        context=context(tenant_id),
        tenant=current,
        expected_version=current.version,
    )

    transitioned = result.tenant

    assert transitioned.legal_entity is current.legal_entity
    assert transitioned.brand is current.brand
    assert transitioned.settings is current.settings
    assert (
        transitioned.security_policy
        is current.security_policy
    )
    assert transitioned.metadata == current.metadata


def test_event_contains_request_traceability() -> None:
    tenant_id = uid()
    request_context = context(tenant_id)
    current = tenant(tenant_id)

    event = TenantLifecycleService().suspend(
        context=request_context,
        tenant=current,
        expected_version=current.version,
    ).event

    assert event.actor_identity_id == (
        request_context.actor_identity_id
    )
    assert event.correlation_id == (
        request_context.correlation_id
    )
    assert event.request_id == (
        request_context.request_id
    )


def test_event_is_immutable() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    event = TenantLifecycleService().suspend(
        context=context(tenant_id),
        tenant=current,
        expected_version=current.version,
    ).event

    assert isinstance(
        event,
        TenantLifecycleEvent,
    )

    with pytest.raises(FrozenInstanceError):
        event.event_type = "CHANGED"  # type: ignore[misc]


def test_result_is_immutable() -> None:
    tenant_id = uid()
    current = tenant(tenant_id)

    result = TenantLifecycleService().suspend(
        context=context(tenant_id),
        tenant=current,
        expected_version=current.version,
    )

    with pytest.raises(FrozenInstanceError):
        result.tenant = current  # type: ignore[misc]
