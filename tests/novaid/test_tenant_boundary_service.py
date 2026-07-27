from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    Identity,
    RequestContext,
)
from afritech.novaid.domain.tenant_boundary import (
    TenantBoundaryService,
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


def identity(tenant_id: str) -> Identity:
    return Identity(
        identity_id=uid(),
        tenant_id=tenant_id,
        normalized_email="boundary@example.com",
    )


def test_valid_context_is_accepted() -> None:
    TenantBoundaryService().assert_valid_context(
        context(uid())
    )


def test_matching_identity_tenant_is_accepted() -> None:
    tenant_id = uid()

    TenantBoundaryService().assert_identity_access(
        context(tenant_id),
        identity(tenant_id),
    )


def test_cross_tenant_identity_access_fails_closed() -> None:
    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        TenantBoundaryService().assert_identity_access(
            context(uid()),
            identity(uid()),
        )


def test_matching_version_is_accepted() -> None:
    TenantBoundaryService().assert_expected_version(
        actual_version=4,
        expected_version=4,
    )


def test_stale_version_is_rejected() -> None:
    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        TenantBoundaryService().assert_expected_version(
            actual_version=4,
            expected_version=3,
        )


def test_boundary_service_is_immutable() -> None:
    service = TenantBoundaryService()

    with pytest.raises(FrozenInstanceError):
        service.some_state = "changed"  # type: ignore[attr-defined]
