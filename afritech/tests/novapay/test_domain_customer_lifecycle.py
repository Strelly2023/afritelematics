from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay.domain.customer import (
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerMetadata,
    CustomerName,
    CustomerPreferences,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)


NOW = datetime(2026, 8, 1, 21, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=5)


def contact(
    email: str = "customer@example.com",
) -> CustomerContact:
    return CustomerContact(
        email=email,
        phone="+61 400 123 456",
    )


def address(
    line: str = "10 Main Street",
) -> CustomerAddress:
    return CustomerAddress(
        country_code="AU",
        address_line_1=line,
        locality="Melbourne",
        administrative_area="Victoria",
        postal_code="3000",
    )


def pending_customer() -> Customer:
    return Customer.create(
        customer_id="customer-001",
        customer_type=CustomerType.INDIVIDUAL,
        name=CustomerName("Djuma Kikombe"),
        novaid_identity_id="novaid-identity-001",
        tenant_id="tenant-001",
        contacts=[contact()],
        metadata={"channel": "mobile"},
        occurred_at=NOW,
    )


def customer_with_status(
    status: CustomerStatus,
) -> Customer:
    customer = pending_customer()

    if status is CustomerStatus.PENDING:
        return customer

    active = customer.activate(occurred_at=LATER)

    if status is CustomerStatus.ACTIVE:
        return active

    restricted = active.restrict(
        reason="risk review",
        occurred_at=LATER + timedelta(minutes=5),
    )

    if status is CustomerStatus.RESTRICTED:
        return restricted

    suspended = restricted.suspend(
        reason="manual investigation",
        occurred_at=LATER + timedelta(minutes=10),
    )

    if status is CustomerStatus.SUSPENDED:
        return suspended

    return suspended.close(
        reason="account closed",
        occurred_at=LATER + timedelta(minutes=15),
    )


def assert_identity_preserved(
    before: Customer,
    after: Customer,
) -> None:
    assert after.customer_id == before.customer_id
    assert after.novaid_identity_id == before.novaid_identity_id
    assert after.tenant_id == before.tenant_id
    assert after.created_at == before.created_at


def assert_new_version(
    before: Customer,
    after: Customer,
    *,
    expected_time: datetime,
) -> None:
    assert after is not before
    assert after.version == before.version + 1
    assert after.updated_at == expected_time
    assert_identity_preserved(before, after)


def test_activate_pending_customer() -> None:
    original = pending_customer()

    activated = original.activate(
        reason="KYC complete",
        occurred_at=LATER,
    )

    assert original.status is CustomerStatus.PENDING
    assert activated.status is CustomerStatus.ACTIVE
    assert activated.metadata.values["lifecycle_action"] == (
        "activate"
    )
    assert activated.metadata.values["lifecycle_reason"] == (
        "KYC complete"
    )
    assert_new_version(
        original,
        activated,
        expected_time=LATER,
    )


@pytest.mark.parametrize(
    "status",
    [
        CustomerStatus.ACTIVE,
        CustomerStatus.RESTRICTED,
        CustomerStatus.SUSPENDED,
        CustomerStatus.CLOSED,
    ],
)
def test_activate_rejects_non_pending_status(
    status: CustomerStatus,
) -> None:
    customer = customer_with_status(status)

    with pytest.raises(ValueError):
        customer.activate(
            occurred_at=customer.updated_at,
        )


def test_restrict_active_customer() -> None:
    active = pending_customer().activate(
        occurred_at=LATER
    )
    occurred_at = LATER + timedelta(minutes=1)

    restricted = active.restrict(
        reason="transaction monitoring review",
        occurred_at=occurred_at,
    )

    assert restricted.status is CustomerStatus.RESTRICTED
    assert restricted.metadata.values["lifecycle_action"] == (
        "restrict"
    )
    assert restricted.metadata.values["lifecycle_reason"] == (
        "transaction monitoring review"
    )
    assert_new_version(
        active,
        restricted,
        expected_time=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        CustomerStatus.PENDING,
        CustomerStatus.RESTRICTED,
        CustomerStatus.SUSPENDED,
        CustomerStatus.CLOSED,
    ],
)
def test_restrict_rejects_invalid_status(
    status: CustomerStatus,
) -> None:
    customer = customer_with_status(status)

    with pytest.raises(ValueError):
        customer.restrict(
            reason="review",
            occurred_at=customer.updated_at,
        )


@pytest.mark.parametrize(
    "starting_status",
    [
        CustomerStatus.ACTIVE,
        CustomerStatus.RESTRICTED,
    ],
)
def test_suspend_allowed_statuses(
    starting_status: CustomerStatus,
) -> None:
    customer = customer_with_status(starting_status)
    occurred_at = customer.updated_at + timedelta(minutes=1)

    suspended = customer.suspend(
        reason="fraud investigation",
        occurred_at=occurred_at,
    )

    assert suspended.status is CustomerStatus.SUSPENDED
    assert suspended.metadata.values["lifecycle_action"] == (
        "suspend"
    )
    assert_new_version(
        customer,
        suspended,
        expected_time=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        CustomerStatus.PENDING,
        CustomerStatus.SUSPENDED,
        CustomerStatus.CLOSED,
    ],
)
def test_suspend_rejects_invalid_status(
    status: CustomerStatus,
) -> None:
    customer = customer_with_status(status)

    with pytest.raises(ValueError):
        customer.suspend(
            reason="review",
            occurred_at=customer.updated_at,
        )


@pytest.mark.parametrize(
    "starting_status",
    [
        CustomerStatus.RESTRICTED,
        CustomerStatus.SUSPENDED,
    ],
)
def test_reinstate_returns_customer_to_active(
    starting_status: CustomerStatus,
) -> None:
    customer = customer_with_status(starting_status)
    occurred_at = customer.updated_at + timedelta(minutes=1)

    reinstated = customer.reinstate(
        reason="review complete",
        occurred_at=occurred_at,
    )

    assert reinstated.status is CustomerStatus.ACTIVE
    assert reinstated.metadata.values["lifecycle_action"] == (
        "reinstate"
    )
    assert_new_version(
        customer,
        reinstated,
        expected_time=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        CustomerStatus.PENDING,
        CustomerStatus.ACTIVE,
        CustomerStatus.CLOSED,
    ],
)
def test_reinstate_rejects_invalid_status(
    status: CustomerStatus,
) -> None:
    customer = customer_with_status(status)

    with pytest.raises(ValueError):
        customer.reinstate(
            occurred_at=customer.updated_at,
        )


@pytest.mark.parametrize(
    "status",
    [
        CustomerStatus.PENDING,
        CustomerStatus.ACTIVE,
        CustomerStatus.RESTRICTED,
        CustomerStatus.SUSPENDED,
    ],
)
def test_close_accepts_every_non_closed_status(
    status: CustomerStatus,
) -> None:
    customer = customer_with_status(status)
    occurred_at = customer.updated_at + timedelta(minutes=1)

    closed = customer.close(
        reason="customer request",
        occurred_at=occurred_at,
    )

    assert closed.status is CustomerStatus.CLOSED
    assert closed.metadata.values["lifecycle_action"] == "close"
    assert closed.metadata.values["lifecycle_reason"] == (
        "customer request"
    )
    assert_new_version(
        customer,
        closed,
        expected_time=occurred_at,
    )


def test_closed_customer_is_terminal() -> None:
    closed = customer_with_status(CustomerStatus.CLOSED)

    operations = (
        lambda: closed.activate(occurred_at=closed.updated_at),
        lambda: closed.restrict(
            reason="review",
            occurred_at=closed.updated_at,
        ),
        lambda: closed.suspend(
            reason="review",
            occurred_at=closed.updated_at,
        ),
        lambda: closed.reinstate(
            occurred_at=closed.updated_at,
        ),
        lambda: closed.close(
            reason="again",
            occurred_at=closed.updated_at,
        ),
        lambda: closed.change_tier(
            CustomerTier.PREMIUM,
            occurred_at=closed.updated_at,
        ),
        lambda: closed.rename(
            CustomerName("Changed"),
            occurred_at=closed.updated_at,
        ),
        lambda: closed.update_metadata(
            {"channel": "agent"},
            occurred_at=closed.updated_at,
        ),
    )

    for operation in operations:
        with pytest.raises(
            ValueError,
            match="closed customer",
        ):
            operation()


@pytest.mark.parametrize(
    "method_name",
    [
        "restrict",
        "suspend",
        "close",
    ],
)
def test_required_lifecycle_reason_rejects_empty_value(
    method_name: str,
) -> None:
    customer = pending_customer().activate(
        occurred_at=LATER
    )

    if method_name == "close":
        method = getattr(customer, method_name)
    else:
        method = getattr(customer, method_name)

    with pytest.raises(
        ValueError,
        match="lifecycle reason must not be empty",
    ):
        method(
            reason=" ",
            occurred_at=customer.updated_at,
        )


def test_lifecycle_reason_rejects_sensitive_metadata_key_injection() -> None:
    customer = pending_customer().activate(
        occurred_at=LATER
    )

    with pytest.raises(TypeError):
        customer.restrict(
            reason={"access_token": "secret"},
            occurred_at=LATER,
        )


def test_change_tier_returns_new_version() -> None:
    original = pending_customer()

    updated = original.change_tier(
        CustomerTier.PREMIUM,
        occurred_at=LATER,
    )

    assert original.tier is CustomerTier.BASIC
    assert updated.tier is CustomerTier.PREMIUM
    assert_new_version(
        original,
        updated,
        expected_time=LATER,
    )


def test_change_tier_parses_string() -> None:
    updated = pending_customer().change_tier(
        " PREMIUM ",
        occurred_at=LATER,
    )

    assert updated.tier is CustomerTier.PREMIUM


def test_change_tier_rejects_no_op() -> None:
    customer = pending_customer()

    with pytest.raises(
        ValueError,
        match="must change tier",
    ):
        customer.change_tier(
            CustomerTier.BASIC,
            occurred_at=LATER,
        )


def test_rename_returns_new_version() -> None:
    original = pending_customer()
    new_name = CustomerName(
        "Djuma M. Kikombe",
        display_name="Djuma",
    )

    updated = original.rename(
        new_name,
        occurred_at=LATER,
    )

    assert original.name != updated.name
    assert updated.name == new_name
    assert_new_version(
        original,
        updated,
        expected_time=LATER,
    )


def test_rename_rejects_non_name_value() -> None:
    with pytest.raises(
        TypeError,
        match="CustomerName",
    ):
        pending_customer().rename(
            "Changed",  # type: ignore[arg-type]
            occurred_at=LATER,
        )


def test_rename_rejects_no_op() -> None:
    customer = pending_customer()

    with pytest.raises(
        ValueError,
        match="must change name",
    ):
        customer.rename(
            customer.name,
            occurred_at=LATER,
        )


def test_replace_contacts_returns_new_version() -> None:
    original = pending_customer()
    replacement = CustomerContact(
        email="new@example.com"
    )

    updated = original.replace_contacts(
        [replacement],
        occurred_at=LATER,
    )

    assert original.contacts != updated.contacts
    assert updated.contacts == (replacement,)
    assert_new_version(
        original,
        updated,
        expected_time=LATER,
    )


def test_replace_contacts_revalidates_individual_invariant() -> None:
    with pytest.raises(
        ValueError,
        match="individual customer requires at least one contact",
    ):
        pending_customer().replace_contacts(
            [],
            occurred_at=LATER,
        )


def test_replace_contacts_rejects_duplicates() -> None:
    duplicate = contact()

    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        pending_customer().replace_contacts(
            [duplicate, duplicate],
            occurred_at=LATER,
        )


def test_replace_contacts_rejects_no_op() -> None:
    customer = pending_customer()

    with pytest.raises(
        ValueError,
        match="must change contacts",
    ):
        customer.replace_contacts(
            customer.contacts,
            occurred_at=LATER,
        )


def merchant_customer() -> Customer:
    return Customer.create(
        customer_id="merchant-001",
        customer_type=CustomerType.MERCHANT,
        name=CustomerName("Nova Merchant"),
        novaid_identity_id="novaid-merchant-001",
        tenant_id="tenant-001",
        addresses=[address()],
        occurred_at=NOW,
    )


def test_replace_addresses_returns_new_version() -> None:
    original = merchant_customer()
    replacement = address("20 Collins Street")

    updated = original.replace_addresses(
        [replacement],
        occurred_at=LATER,
    )

    assert original.addresses != updated.addresses
    assert updated.addresses == (replacement,)
    assert_new_version(
        original,
        updated,
        expected_time=LATER,
    )


def test_replace_addresses_revalidates_commercial_invariant() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one address",
    ):
        merchant_customer().replace_addresses(
            [],
            occurred_at=LATER,
        )


def test_replace_addresses_rejects_no_op() -> None:
    customer = merchant_customer()

    with pytest.raises(
        ValueError,
        match="must change addresses",
    ):
        customer.replace_addresses(
            customer.addresses,
            occurred_at=LATER,
        )


def test_update_preferences_returns_new_version() -> None:
    original = pending_customer()

    updated = original.update_preferences(
        {
            "language": "fr",
            "notifications": False,
        },
        occurred_at=LATER,
    )

    assert dict(original.preferences.values) == {}
    assert updated.preferences.values == {
        "language": "fr",
        "notifications": False,
    }
    assert_new_version(
        original,
        updated,
        expected_time=LATER,
    )


def test_update_preferences_rejects_no_op() -> None:
    customer = pending_customer()

    with pytest.raises(
        ValueError,
        match="must change preferences",
    ):
        customer.update_preferences(
            customer.preferences,
            occurred_at=LATER,
        )


def test_update_metadata_returns_new_version() -> None:
    original = pending_customer()

    updated = original.update_metadata(
        {
            "channel": "agent",
            "corridor": "AU-BI",
        },
        occurred_at=LATER,
    )

    assert original.metadata.values == {
        "channel": "mobile",
    }
    assert updated.metadata.values == {
        "channel": "agent",
        "corridor": "AU-BI",
    }
    assert_new_version(
        original,
        updated,
        expected_time=LATER,
    )


def test_update_metadata_rejects_sensitive_keys() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        pending_customer().update_metadata(
            {"refresh_token": "secret"},
            occurred_at=LATER,
        )


def test_update_metadata_rejects_no_op() -> None:
    customer = pending_customer()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        customer.update_metadata(
            customer.metadata,
            occurred_at=LATER,
        )


@pytest.mark.parametrize(
    "operation",
    [
        lambda customer: customer.change_tier(
            CustomerTier.PREMIUM,
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda customer: customer.rename(
            CustomerName("Changed"),
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda customer: customer.replace_contacts(
            [CustomerContact(email="new@example.com")],
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda customer: customer.update_preferences(
            {"language": "fr"},
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda customer: customer.update_metadata(
            {"channel": "agent"},
            occurred_at=NOW - timedelta(seconds=1),
        ),
    ],
)
def test_updates_reject_timestamp_before_current_updated_at(
    operation: object,
) -> None:
    customer = pending_customer()

    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        operation(customer)  # type: ignore[operator]


def test_update_allows_timestamp_equal_to_current_updated_at() -> None:
    customer = pending_customer()

    updated = customer.change_tier(
        CustomerTier.PREMIUM,
        occurred_at=customer.updated_at,
    )

    assert updated.updated_at == customer.updated_at
    assert updated.version == customer.version + 1


def test_multiple_updates_increment_version_once_each() -> None:
    customer = pending_customer()

    activated = customer.activate(
        occurred_at=LATER
    )
    promoted = activated.change_tier(
        CustomerTier.STANDARD,
        occurred_at=LATER,
    )
    renamed = promoted.rename(
        CustomerName("Djuma M. Kikombe"),
        occurred_at=LATER,
    )

    assert customer.version == 1
    assert activated.version == 2
    assert promoted.version == 3
    assert renamed.version == 4


def test_lifecycle_metadata_preserves_existing_metadata() -> None:
    customer = pending_customer()

    activated = customer.activate(
        reason="verification complete",
        occurred_at=LATER,
    )

    assert activated.metadata.values == {
        "channel": "mobile",
        "lifecycle_action": "activate",
        "lifecycle_reason": "verification complete",
    }


def test_canonical_serialization_reflects_latest_version() -> None:
    customer = pending_customer().activate(
        reason="verification complete",
        occurred_at=LATER,
    )

    payload = customer.canonical_dict()

    assert payload["status"] == "active"
    assert payload["version"] == 2
    assert payload["updated_at"] == LATER.isoformat()
    assert payload["metadata"]["lifecycle_action"] == (
        "activate"
    )


def test_original_customer_remains_unchanged() -> None:
    original = pending_customer()

    updated = original.activate(
        reason="verification complete",
        occurred_at=LATER,
    )

    assert original.status is CustomerStatus.PENDING
    assert original.version == 1
    assert original.updated_at == NOW
    assert original.metadata.values == {
        "channel": "mobile",
    }

    assert updated.status is CustomerStatus.ACTIVE
    assert updated.version == 2


def test_customer_lifecycle_methods_are_public() -> None:
    methods = (
        "activate",
        "restrict",
        "suspend",
        "reinstate",
        "close",
        "change_tier",
        "rename",
        "replace_contacts",
        "replace_addresses",
        "update_preferences",
        "update_metadata",
    )

    for method in methods:
        assert callable(getattr(Customer, method))
