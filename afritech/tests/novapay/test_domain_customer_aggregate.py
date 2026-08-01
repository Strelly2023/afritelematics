from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay.domain.customer import (
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerId,
    CustomerMetadata,
    CustomerName,
    CustomerPreferences,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)


NOW = datetime(2026, 8, 1, 20, 30, tzinfo=timezone.utc)


def individual_contact() -> CustomerContact:
    return CustomerContact(
        email="customer@example.com",
        phone="+61 400 123 456",
    )


def business_address() -> CustomerAddress:
    return CustomerAddress(
        country_code="AU",
        address_line_1="10 Main Street",
        locality="Melbourne",
        administrative_area="Victoria",
        postal_code="3000",
    )


def build_individual_customer(
    **overrides: object,
) -> Customer:
    values: dict[str, object] = {
        "customer_id": CustomerId("customer-001"),
        "customer_type": CustomerType.INDIVIDUAL,
        "status": CustomerStatus.PENDING,
        "tier": CustomerTier.BASIC,
        "name": CustomerName("Djuma Kikombe"),
        "novaid_identity_id": "novaid-identity-001",
        "tenant_id": "tenant-001",
        "contacts": (individual_contact(),),
        "addresses": (),
        "preferences": CustomerPreferences(
            {"language": "en"}
        ),
        "metadata": CustomerMetadata(
            {"channel": "mobile"}
        ),
        "created_at": NOW,
        "updated_at": NOW,
        "version": 1,
    }
    values.update(overrides)

    return Customer(**values)  # type: ignore[arg-type]


def test_customer_create_builds_individual_customer() -> None:
    customer = Customer.create(
        customer_id=" customer-001 ",
        customer_type=" INDIVIDUAL ",
        name=CustomerName(
            "  Djuma   Kikombe ",
            display_name=" Djuma ",
        ),
        novaid_identity_id=" novaid-identity-001 ",
        tenant_id=" tenant-001 ",
        contacts=[individual_contact()],
        occurred_at=NOW,
    )

    assert customer.customer_id == CustomerId(
        "customer-001"
    )
    assert customer.customer_type is CustomerType.INDIVIDUAL
    assert customer.status is CustomerStatus.PENDING
    assert customer.tier is CustomerTier.BASIC
    assert customer.name.legal_name == "Djuma Kikombe"
    assert customer.novaid_identity_id == (
        "novaid-identity-001"
    )
    assert customer.tenant_id == "tenant-001"
    assert customer.created_at == NOW
    assert customer.updated_at == NOW
    assert customer.version == 1


def test_customer_normalizes_enum_and_identifier_inputs() -> None:
    customer = Customer(
        customer_id=" customer-001 ",  # type: ignore[arg-type]
        customer_type=" individual ",  # type: ignore[arg-type]
        status=" active ",  # type: ignore[arg-type]
        tier=" standard ",  # type: ignore[arg-type]
        name=CustomerName("Djuma Kikombe"),
        novaid_identity_id=" novaid-001 ",
        tenant_id=" tenant-001 ",
        contacts=[individual_contact()],  # type: ignore[arg-type]
        created_at=NOW,
        updated_at=NOW,
    )

    assert customer.customer_id.value == "customer-001"
    assert customer.customer_type is CustomerType.INDIVIDUAL
    assert customer.status is CustomerStatus.ACTIVE
    assert customer.tier is CustomerTier.STANDARD
    assert customer.novaid_identity_id == "novaid-001"
    assert customer.tenant_id == "tenant-001"
    assert isinstance(customer.contacts, tuple)


def test_customer_is_immutable() -> None:
    customer = build_individual_customer()

    with pytest.raises(FrozenInstanceError):
        customer.status = CustomerStatus.ACTIVE  # type: ignore[misc]


def test_customer_uses_slots() -> None:
    customer = build_individual_customer()

    assert not hasattr(customer, "__dict__")


def test_customer_requires_customer_name_value_object() -> None:
    with pytest.raises(
        TypeError,
        match="customer name must be a CustomerName",
    ):
        build_individual_customer(
            name="Djuma Kikombe",
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "novaid_identity_id",
        "tenant_id",
    ],
)
def test_customer_requires_identity_and_tenant_references(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        build_individual_customer(
            **{field_name: " "}
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "novaid_identity_id",
        "tenant_id",
    ],
)
def test_customer_rejects_non_string_references(
    field_name: str,
) -> None:
    with pytest.raises(TypeError):
        build_individual_customer(
            **{field_name: 123}
        )


def test_individual_customer_requires_contact() -> None:
    with pytest.raises(
        ValueError,
        match="individual customer requires at least one contact",
    ):
        build_individual_customer(
            contacts=(),
        )


@pytest.mark.parametrize(
    "customer_type",
    [
        CustomerType.AGENT,
        CustomerType.MERCHANT,
        CustomerType.BUSINESS,
        CustomerType.ENTERPRISE,
    ],
)
def test_commercial_customer_requires_address(
    customer_type: CustomerType,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one address",
    ):
        Customer.create(
            customer_id=f"{customer_type.value}-001",
            customer_type=customer_type,
            name=CustomerName(
                f"Nova {customer_type.value.title()}"
            ),
            novaid_identity_id=(
                f"novaid-{customer_type.value}-001"
            ),
            tenant_id="tenant-001",
            occurred_at=NOW,
        )


@pytest.mark.parametrize(
    "customer_type",
    [
        CustomerType.AGENT,
        CustomerType.MERCHANT,
        CustomerType.BUSINESS,
        CustomerType.ENTERPRISE,
    ],
)
def test_commercial_customer_accepts_address(
    customer_type: CustomerType,
) -> None:
    customer = Customer.create(
        customer_id=f"{customer_type.value}-001",
        customer_type=customer_type,
        name=CustomerName(
            f"Nova {customer_type.value.title()}"
        ),
        novaid_identity_id=(
            f"novaid-{customer_type.value}-001"
        ),
        tenant_id="tenant-001",
        addresses=[business_address()],
        occurred_at=NOW,
    )

    assert customer.customer_type is customer_type
    assert customer.addresses == (business_address(),)


def test_system_customer_rejects_personal_contacts() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain personal contacts",
    ):
        Customer.create(
            customer_id="system-001",
            customer_type=CustomerType.SYSTEM,
            name=CustomerName("NovaPay System"),
            novaid_identity_id="novaid-system-001",
            tenant_id="platform",
            contacts=[individual_contact()],
            occurred_at=NOW,
        )


def test_system_customer_accepts_no_contacts() -> None:
    customer = Customer.create(
        customer_id="system-001",
        customer_type=CustomerType.SYSTEM,
        name=CustomerName("NovaPay System"),
        novaid_identity_id="novaid-system-001",
        tenant_id="platform",
        occurred_at=NOW,
    )

    assert customer.contacts == ()
    assert customer.addresses == ()


def test_customer_rejects_duplicate_contacts() -> None:
    contact = individual_contact()

    with pytest.raises(
        ValueError,
        match="contacts must not contain duplicates",
    ):
        build_individual_customer(
            contacts=(contact, contact),
        )


def test_customer_rejects_duplicate_addresses() -> None:
    address = business_address()

    with pytest.raises(
        ValueError,
        match="addresses must not contain duplicates",
    ):
        Customer.create(
            customer_id="merchant-001",
            customer_type=CustomerType.MERCHANT,
            name=CustomerName("Nova Merchant"),
            novaid_identity_id="novaid-merchant-001",
            tenant_id="tenant-001",
            addresses=(address, address),
            occurred_at=NOW,
        )


def test_customer_rejects_invalid_contact_collection() -> None:
    with pytest.raises(
        TypeError,
        match="contacts must contain CustomerContact",
    ):
        build_individual_customer(
            contacts=("user@example.com",),
        )


def test_customer_rejects_invalid_address_collection() -> None:
    with pytest.raises(
        TypeError,
        match="addresses must contain CustomerAddress",
    ):
        Customer.create(
            customer_id="merchant-001",
            customer_type=CustomerType.MERCHANT,
            name=CustomerName("Nova Merchant"),
            novaid_identity_id="novaid-merchant-001",
            tenant_id="tenant-001",
            addresses=("10 Main Street",),
            occurred_at=NOW,
        )


def test_customer_contacts_collection_is_immutable_tuple() -> None:
    source = [individual_contact()]

    customer = build_individual_customer(
        contacts=source,
    )
    source.clear()

    assert len(customer.contacts) == 1
    assert isinstance(customer.contacts, tuple)


def test_customer_addresses_collection_is_immutable_tuple() -> None:
    source = [business_address()]

    customer = Customer.create(
        customer_id="merchant-001",
        customer_type=CustomerType.MERCHANT,
        name=CustomerName("Nova Merchant"),
        novaid_identity_id="novaid-merchant-001",
        tenant_id="tenant-001",
        addresses=source,
        occurred_at=NOW,
    )
    source.clear()

    assert len(customer.addresses) == 1
    assert isinstance(customer.addresses, tuple)


def test_customer_normalizes_preferences_and_metadata() -> None:
    customer = build_individual_customer(
        preferences={" language ": "en"},
        metadata={" channel ": "mobile"},
    )

    assert customer.preferences.values == {
        "language": "en",
    }
    assert customer.metadata.values == {
        "channel": "mobile",
    }


def test_customer_metadata_rejects_sensitive_data() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        build_individual_customer(
            metadata={"access_token": "secret"}
        )


def test_customer_timestamps_are_normalized_to_utc() -> None:
    melbourne = timezone(timedelta(hours=10))
    timestamp = datetime(
        2026,
        8,
        2,
        6,
        30,
        tzinfo=melbourne,
    )

    customer = build_individual_customer(
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert customer.created_at.tzinfo is timezone.utc
    assert customer.updated_at.tzinfo is timezone.utc
    assert customer.created_at.hour == 20


def test_customer_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="created at must be timezone-aware",
    ):
        build_individual_customer(
            created_at=datetime(2026, 8, 1, 20, 30),
        )


def test_customer_rejects_naive_updated_at() -> None:
    with pytest.raises(
        ValueError,
        match="updated at must be timezone-aware",
    ):
        build_individual_customer(
            updated_at=datetime(2026, 8, 1, 20, 30),
        )


def test_customer_rejects_updated_at_before_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier than created at",
    ):
        build_individual_customer(
            created_at=NOW,
            updated_at=NOW - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_customer_rejects_invalid_version(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        build_individual_customer(version=value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        1.0,
        "1",
        None,
    ],
)
def test_customer_rejects_non_integer_version(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer version must be an integer",
    ):
        build_individual_customer(version=value)


def test_customer_create_uses_same_timestamp() -> None:
    customer = Customer.create(
        customer_id="customer-001",
        customer_type=CustomerType.INDIVIDUAL,
        name=CustomerName("Djuma Kikombe"),
        novaid_identity_id="novaid-001",
        tenant_id="tenant-001",
        contacts=[individual_contact()],
        occurred_at=NOW,
    )

    assert customer.created_at == NOW
    assert customer.updated_at == NOW


def test_customer_canonical_dict_is_deterministic() -> None:
    customer = build_individual_customer()

    payload = customer.canonical_dict()

    assert list(payload) == [
        "customer_id",
        "customer_type",
        "status",
        "tier",
        "name",
        "novaid_identity_id",
        "tenant_id",
        "contacts",
        "addresses",
        "preferences",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]
    assert payload["customer_id"] == "customer-001"
    assert payload["customer_type"] == "individual"
    assert payload["status"] == "pending"
    assert payload["tier"] == "basic"
    assert payload["name"] == {
        "legal_name": "Djuma Kikombe",
        "display_name": None,
    }
    assert payload["novaid_identity_id"] == (
        "novaid-identity-001"
    )
    assert payload["tenant_id"] == "tenant-001"
    assert payload["contacts"] == [
        {
            "email": "customer@example.com",
            "phone": "+61 400 123 456",
        }
    ]
    assert payload["preferences"] == {
        "language": "en",
    }
    assert payload["metadata"] == {
        "channel": "mobile",
    }
    assert payload["created_at"] == NOW.isoformat()
    assert payload["updated_at"] == NOW.isoformat()
    assert payload["version"] == 1


def test_customer_canonical_dict_returns_fresh_collections() -> None:
    customer = build_individual_customer()

    first = customer.canonical_dict()
    second = customer.canonical_dict()

    assert first == second
    assert first is not second
    assert first["contacts"] is not second["contacts"]
    assert first["preferences"] is not second["preferences"]


def test_customer_aggregate_has_no_secret_fields() -> None:
    forbidden = {
        "password",
        "password_hash",
        "pin",
        "access_token",
        "refresh_token",
        "private_key",
        "biometric_template",
        "document_image",
        "identity_document",
    }

    for attribute in forbidden:
        assert not hasattr(
            build_individual_customer(),
            attribute,
        )


def test_customer_module_declares_customer_aggregate() -> None:
    from afritech.novapay.domain import customer

    assert customer.__all__ == [
        "Customer",
        "CustomerAddress",
        "CustomerContact",
        "CustomerId",
        "CustomerMetadata",
        "CustomerName",
        "CustomerPreferences",
        "CustomerStatus",
        "CustomerTier",
        "CustomerType",
    ]
