from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    Tenant,
    TenantStatus,
    TenantTier,
    TenantType,
)


def uid() -> str:
    return str(uuid4())


def test_existing_positional_tenant_constructor_remains_compatible() -> None:
    now = datetime.now(UTC)

    tenant = Tenant(
        uid(),
        "Legacy Tenant",
        "ACTIVE",
        now,
        now,
        1,
    )

    assert tenant.status is TenantStatus.ACTIVE
    assert tenant.tenant_type is TenantType.ORGANISATION
    assert tenant.tier is TenantTier.STANDARD


def test_canonical_tenant_accepts_extended_profile() -> None:
    tenant = Tenant(
        tenant_id=uid(),
        name="NovaTech Australia",
        tenant_type=TenantType.BUSINESS,
        tier=TenantTier.ENTERPRISE,
        metadata={
            "environment": "controlled-pilot",
            "platform": "novatech",
        },
    )

    assert tenant.name == "NovaTech Australia"
    assert tenant.tenant_type is TenantType.BUSINESS
    assert tenant.tier is TenantTier.ENTERPRISE
    assert tenant.metadata == {
        "environment": "controlled-pilot",
        "platform": "novatech",
    }


def test_tenant_values_are_normalized() -> None:
    tenant = Tenant(
        tenant_id=f"  {uid()}  ",
        name="  NovaTech  ",
        status="ACTIVE",
        tenant_type="BUSINESS",
        tier="ENTERPRISE",
    )

    assert tenant.tenant_id == tenant.tenant_id.strip()
    assert tenant.name == "NovaTech"
    assert tenant.status is TenantStatus.ACTIVE
    assert tenant.tenant_type is TenantType.BUSINESS
    assert tenant.tier is TenantTier.ENTERPRISE


def test_tenant_transition_is_versioned() -> None:
    tenant = Tenant(
        tenant_id=uid(),
        name="Lifecycle Tenant",
        metadata={"source": "tenant-aggregate"},
    )

    suspended = tenant.transition(
        TenantStatus.SUSPENDED,
    )

    assert suspended.status is TenantStatus.SUSPENDED
    assert suspended.version == tenant.version + 1
    assert suspended.updated_at >= tenant.updated_at
    assert suspended.metadata == tenant.metadata

    reactivated = suspended.transition(
        TenantStatus.ACTIVE,
    )

    assert reactivated.status is TenantStatus.ACTIVE
    assert reactivated.version == tenant.version + 2


def test_invalid_tenant_transition_fails_closed() -> None:
    tenant = Tenant(
        tenant_id=uid(),
        name="Transition Tenant",
    )

    with pytest.raises(
        ValueError,
        match="INVALID_TENANT_TRANSITION",
    ):
        tenant.transition(
            TenantStatus.ACTIVE,
        )


def test_disabled_tenant_can_be_reactivated() -> None:
    tenant = Tenant(
        tenant_id=uid(),
        name="Disabled Tenant",
        status=TenantStatus.DISABLED,
    )

    restored = tenant.transition(
        TenantStatus.ACTIVE,
    )

    assert restored.status is TenantStatus.ACTIVE
    assert restored.version == tenant.version + 1


def test_empty_tenant_name_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="TENANT_NAME_REQUIRED",
    ):
        Tenant(
            tenant_id=uid(),
            name="   ",
        )


def test_invalid_version_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_AGGREGATE_VERSION",
    ):
        Tenant(
            tenant_id=uid(),
            name="Version Tenant",
            version=0,
        )


def test_tenant_is_frozen() -> None:
    tenant = Tenant(
        tenant_id=uid(),
        name="Immutable Tenant",
    )

    with pytest.raises(FrozenInstanceError):
        tenant.name = "Changed"  # type: ignore[misc]
