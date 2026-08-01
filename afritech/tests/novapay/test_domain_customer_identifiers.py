from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum

import pytest

from afritech.novapay.domain.customer import (
    CustomerId,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)


def test_customer_id_trims_surrounding_whitespace() -> None:
    customer_id = CustomerId("  customer-001  ")

    assert customer_id.value == "customer-001"


def test_customer_id_of_trims_surrounding_whitespace() -> None:
    customer_id = CustomerId.of("  customer-002  ")

    assert customer_id == CustomerId("customer-002")


def test_customer_id_of_returns_existing_instance() -> None:
    customer_id = CustomerId("customer-003")

    assert CustomerId.of(customer_id) is customer_id


@pytest.mark.parametrize(
    "value",
    [
        "customer-001",
        "customer_001",
        "customer.001",
        "tenant:customer-001",
        "customer/001",
        "customer@platform",
    ],
)
def test_customer_id_accepts_supported_characters(
    value: str,
) -> None:
    assert CustomerId(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_customer_id_rejects_empty_value(value: str) -> None:
    with pytest.raises(
        ValueError,
        match="customer id must not be empty",
    ):
        CustomerId(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
        ["customer-001"],
        {"value": "customer-001"},
    ],
)
def test_customer_id_rejects_non_string_value(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer id must be a string",
    ):
        CustomerId.of(value)


@pytest.mark.parametrize(
    "value",
    [
        "customer 001",
        "customer#001",
        "customer?001",
        "customer+001",
        "-customer-001",
    ],
)
def test_customer_id_rejects_unsupported_characters(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="customer id contains unsupported characters",
    ):
        CustomerId(value)


def test_customer_id_rejects_value_longer_than_128_characters() -> None:
    with pytest.raises(
        ValueError,
        match="customer id contains unsupported characters",
    ):
        CustomerId("c" * 129)


def test_customer_id_supports_stable_string_conversion() -> None:
    customer_id = CustomerId("customer-001")

    assert str(customer_id) == "customer-001"


def test_customer_id_has_value_equality_and_hashing() -> None:
    first = CustomerId("customer-001")
    second = CustomerId("customer-001")

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {CustomerId("customer-001")}


def test_customer_id_is_immutable() -> None:
    customer_id = CustomerId("customer-001")

    with pytest.raises(FrozenInstanceError):
        customer_id.value = "customer-002"  # type: ignore[misc]


def test_customer_id_uses_slots() -> None:
    customer_id = CustomerId("customer-001")

    assert not hasattr(customer_id, "__dict__")


def test_customer_id_canonical_dict_is_deterministic() -> None:
    customer_id = CustomerId("customer-001")

    assert customer_id.canonical_dict() == {
        "value": "customer-001",
    }


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (CustomerType.INDIVIDUAL, "individual"),
        (CustomerType.AGENT, "agent"),
        (CustomerType.MERCHANT, "merchant"),
        (CustomerType.BUSINESS, "business"),
        (CustomerType.ENTERPRISE, "enterprise"),
        (CustomerType.SYSTEM, "system"),
    ],
)
def test_customer_type_has_stable_serialized_values(
    member: CustomerType,
    serialized: str,
) -> None:
    assert member.value == serialized
    assert str(member.value) == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("individual", CustomerType.INDIVIDUAL),
        (" INDIVIDUAL ", CustomerType.INDIVIDUAL),
        ("Agent", CustomerType.AGENT),
        ("MERCHANT", CustomerType.MERCHANT),
        (" business ", CustomerType.BUSINESS),
        ("Enterprise", CustomerType.ENTERPRISE),
        ("SYSTEM", CustomerType.SYSTEM),
    ],
)
def test_customer_type_parse_normalizes_values(
    raw: str,
    expected: CustomerType,
) -> None:
    assert CustomerType.parse(raw) is expected


def test_customer_type_parse_returns_existing_instance() -> None:
    assert (
        CustomerType.parse(CustomerType.MERCHANT)
        is CustomerType.MERCHANT
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "unknown",
        "consumer",
        "customer",
    ],
)
def test_customer_type_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CustomerType.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_customer_type_rejects_non_string_values(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer type must be a string",
    ):
        CustomerType.parse(value)


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (CustomerStatus.PENDING, "pending"),
        (CustomerStatus.ACTIVE, "active"),
        (CustomerStatus.RESTRICTED, "restricted"),
        (CustomerStatus.SUSPENDED, "suspended"),
        (CustomerStatus.CLOSED, "closed"),
    ],
)
def test_customer_status_has_stable_serialized_values(
    member: CustomerStatus,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("pending", CustomerStatus.PENDING),
        (" PENDING ", CustomerStatus.PENDING),
        ("Active", CustomerStatus.ACTIVE),
        ("RESTRICTED", CustomerStatus.RESTRICTED),
        (" suspended ", CustomerStatus.SUSPENDED),
        ("Closed", CustomerStatus.CLOSED),
    ],
)
def test_customer_status_parse_normalizes_values(
    raw: str,
    expected: CustomerStatus,
) -> None:
    assert CustomerStatus.parse(raw) is expected


def test_customer_status_parse_returns_existing_instance() -> None:
    assert (
        CustomerStatus.parse(CustomerStatus.ACTIVE)
        is CustomerStatus.ACTIVE
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "inactive",
        "deleted",
        "blocked",
    ],
)
def test_customer_status_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CustomerStatus.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_customer_status_rejects_non_string_values(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer status must be a string",
    ):
        CustomerStatus.parse(value)


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (CustomerTier.BASIC, "basic"),
        (CustomerTier.STANDARD, "standard"),
        (CustomerTier.PREMIUM, "premium"),
        (CustomerTier.ENTERPRISE, "enterprise"),
    ],
)
def test_customer_tier_has_stable_serialized_values(
    member: CustomerTier,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("basic", CustomerTier.BASIC),
        (" BASIC ", CustomerTier.BASIC),
        ("Standard", CustomerTier.STANDARD),
        ("PREMIUM", CustomerTier.PREMIUM),
        (" enterprise ", CustomerTier.ENTERPRISE),
    ],
)
def test_customer_tier_parse_normalizes_values(
    raw: str,
    expected: CustomerTier,
) -> None:
    assert CustomerTier.parse(raw) is expected


def test_customer_tier_parse_returns_existing_instance() -> None:
    assert (
        CustomerTier.parse(CustomerTier.PREMIUM)
        is CustomerTier.PREMIUM
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "gold",
        "platinum",
        "vip",
    ],
)
def test_customer_tier_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CustomerTier.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_customer_tier_rejects_non_string_values(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer tier must be a string",
    ):
        CustomerTier.parse(value)


@pytest.mark.parametrize(
    "enum_type",
    [
        CustomerType,
        CustomerStatus,
        CustomerTier,
    ],
)
def test_customer_enums_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


def test_customer_module_declares_expected_public_symbols() -> None:
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
