from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from afritech.novapay.domain.customer import (
    CustomerAddress,
    CustomerContact,
    CustomerMetadata,
    CustomerName,
    CustomerPreferences,
)


def test_customer_name_normalizes_legal_name() -> None:
    name = CustomerName(
        legal_name="  Nova   Merchant   Limited  ",
    )

    assert name.legal_name == "Nova Merchant Limited"
    assert name.display_name is None


def test_customer_name_normalizes_display_name() -> None:
    name = CustomerName(
        legal_name="Nova Merchant Limited",
        display_name="  Nova   Merchant ",
    )

    assert name.display_name == "Nova Merchant"
    assert name.effective_display_name == "Nova Merchant"


def test_customer_name_uses_legal_name_as_effective_display() -> None:
    name = CustomerName(
        legal_name="Nova Merchant Limited",
    )

    assert name.effective_display_name == (
        "Nova Merchant Limited"
    )


def test_customer_name_of_creates_normalized_value() -> None:
    name = CustomerName.of(
        "  Djuma   Kikombe ",
        display_name=" Djuma ",
    )

    assert name.legal_name == "Djuma Kikombe"
    assert name.display_name == "Djuma"


def test_customer_name_of_returns_existing_instance() -> None:
    name = CustomerName("Djuma Kikombe")

    assert CustomerName.of(name) is name


def test_customer_name_of_rejects_display_for_existing() -> None:
    name = CustomerName("Djuma Kikombe")

    with pytest.raises(
        ValueError,
        match="display name must not be supplied",
    ):
        CustomerName.of(
            name,
            display_name="Djuma",
        )


@pytest.mark.parametrize(
    "value",
    ["", " ", "\t", "\n"],
)
def test_customer_name_rejects_empty_legal_name(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="customer legal name must not be empty",
    ):
        CustomerName(value)


@pytest.mark.parametrize(
    "value",
    [None, 123, object()],
)
def test_customer_name_rejects_non_string_legal_name(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer legal name must be a string",
    ):
        CustomerName.of(value)


def test_customer_name_rejects_long_legal_name() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 200 characters",
    ):
        CustomerName("x" * 201)


def test_customer_name_rejects_long_display_name() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 120 characters",
    ):
        CustomerName(
            legal_name="Nova Merchant Limited",
            display_name="x" * 121,
        )


def test_customer_name_is_immutable() -> None:
    name = CustomerName("Djuma Kikombe")

    with pytest.raises(FrozenInstanceError):
        name.legal_name = "Changed"  # type: ignore[misc]


def test_customer_name_canonical_dict() -> None:
    name = CustomerName(
        legal_name="Nova Merchant Limited",
        display_name="Nova Merchant",
    )

    assert name.canonical_dict() == {
        "legal_name": "Nova Merchant Limited",
        "display_name": "Nova Merchant",
    }


def test_customer_contact_normalizes_email() -> None:
    contact = CustomerContact(
        email="  USER@Example.COM ",
    )

    assert contact.email == "user@example.com"
    assert contact.phone is None


def test_customer_contact_normalizes_phone_whitespace() -> None:
    contact = CustomerContact(
        phone="  +61   400  123 456 ",
    )

    assert contact.phone == "+61 400 123 456"


def test_customer_contact_supports_email_and_phone() -> None:
    contact = CustomerContact(
        email="USER@example.com",
        phone="+61 400 123 456",
    )

    assert contact.email == "user@example.com"
    assert contact.phone == "+61 400 123 456"


def test_customer_contact_requires_contact_method() -> None:
    with pytest.raises(
        ValueError,
        match="requires email or phone",
    ):
        CustomerContact()


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-an-email",
        "missing-domain@",
        "@missing-local.example",
        "has space@example.com",
    ],
)
def test_customer_contact_rejects_invalid_email(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CustomerContact(email=value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "abc",
        "+61",
        "12345",
        "1234567890123456",
    ],
)
def test_customer_contact_rejects_invalid_phone(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CustomerContact(phone=value)


def test_customer_contact_canonical_dict() -> None:
    contact = CustomerContact(
        email="user@example.com",
        phone="+61 400 123 456",
    )

    assert contact.canonical_dict() == {
        "email": "user@example.com",
        "phone": "+61 400 123 456",
    }


def test_customer_address_normalizes_fields() -> None:
    address = CustomerAddress(
        country_code=" au ",
        address_line_1=" 10   Main Street ",
        address_line_2=" Unit   4 ",
        locality=" Melbourne ",
        administrative_area=" Victoria ",
        postal_code=" 3000 ",
    )

    assert address.country_code == "AU"
    assert address.address_line_1 == "10 Main Street"
    assert address.address_line_2 == "Unit 4"
    assert address.locality == "Melbourne"
    assert address.administrative_area == "Victoria"
    assert address.postal_code == "3000"


@pytest.mark.parametrize(
    "value",
    ["A", "AUS", "12", "", " "],
)
def test_customer_address_rejects_invalid_country_code(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="two-letter ISO code",
    ):
        CustomerAddress(
            country_code=value,
            address_line_1="10 Main Street",
            locality="Melbourne",
        )


@pytest.mark.parametrize(
    "field_name",
    ["address_line_1", "locality"],
)
def test_customer_address_requires_core_fields(
    field_name: str,
) -> None:
    values = {
        "country_code": "AU",
        "address_line_1": "10 Main Street",
        "locality": "Melbourne",
    }
    values[field_name] = " "

    with pytest.raises(ValueError):
        CustomerAddress(**values)


def test_customer_address_rejects_invalid_postal_code() -> None:
    with pytest.raises(
        ValueError,
        match="postal code format is invalid",
    ):
        CustomerAddress(
            country_code="AU",
            address_line_1="10 Main Street",
            locality="Melbourne",
            postal_code="#3000",
        )


def test_customer_address_canonical_dict_order() -> None:
    address = CustomerAddress(
        country_code="AU",
        address_line_1="10 Main Street",
        locality="Melbourne",
        postal_code="3000",
    )

    assert list(address.canonical_dict()) == [
        "country_code",
        "address_line_1",
        "address_line_2",
        "locality",
        "administrative_area",
        "postal_code",
    ]


def test_customer_preferences_default_empty() -> None:
    preferences = CustomerPreferences()

    assert dict(preferences.values) == {}
    assert isinstance(
        preferences.values,
        MappingProxyType,
    )


def test_customer_preferences_normalize_keys() -> None:
    preferences = CustomerPreferences(
        {
            " language ": "en",
            "notifications": True,
        }
    )

    assert preferences.values == {
        "language": "en",
        "notifications": True,
    }


def test_customer_preferences_defensive_copy() -> None:
    source = {"language": "en"}
    preferences = CustomerPreferences(source)

    source["language"] = "fr"

    assert preferences.get("language") == "en"


def test_customer_preferences_with_value_is_immutable() -> None:
    original = CustomerPreferences(
        {"language": "en"}
    )

    updated = original.with_value(
        "language",
        "fr",
    )

    assert original.get("language") == "en"
    assert updated.get("language") == "fr"


def test_customer_preferences_without_is_immutable() -> None:
    original = CustomerPreferences(
        {
            "language": "en",
            "marketing": False,
        }
    )

    updated = original.without("marketing")

    assert "marketing" in original.values
    assert "marketing" not in updated.values


def test_customer_preferences_canonical_dict_is_immutable() -> None:
    preferences = CustomerPreferences(
        {"language": "en"}
    )

    payload = preferences.canonical_dict()

    assert isinstance(payload, MappingProxyType)

    with pytest.raises(TypeError):
        payload["language"] = "fr"  # type: ignore[index]


@pytest.mark.parametrize(
    "value",
    [123, object(), ["language"]],
)
def test_customer_preferences_reject_non_mapping(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer preferences must be a mapping",
    ):
        CustomerPreferences.of(value)


def test_customer_preferences_reject_non_string_key() -> None:
    with pytest.raises(
        TypeError,
        match="keys must be strings",
    ):
        CustomerPreferences(
            {1: "en"}  # type: ignore[dict-item]
        )


def test_customer_metadata_default_empty() -> None:
    metadata = CustomerMetadata()

    assert dict(metadata.values) == {}
    assert isinstance(metadata.values, MappingProxyType)


def test_customer_metadata_normalizes_keys() -> None:
    metadata = CustomerMetadata(
        {
            " channel ": "mobile",
            "corridor": "AU-BI",
        }
    )

    assert metadata.values == {
        "channel": "mobile",
        "corridor": "AU-BI",
    }


def test_customer_metadata_defensive_copy() -> None:
    source = {"channel": "mobile"}
    metadata = CustomerMetadata(source)

    source["channel"] = "agent"

    assert metadata.get("channel") == "mobile"


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "access_token",
        "refresh_token",
        "api_key",
        "private_key",
        "pin",
        "cvv",
        "card_number",
        "biometric_template",
        "identity_document",
        "document_image",
        "credential_payload",
    ],
)
def test_customer_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        CustomerMetadata({key: "secret"})


def test_customer_metadata_sensitive_check_is_case_insensitive() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        CustomerMetadata(
            {"Access_Token": "secret"}
        )


def test_customer_metadata_with_value_revalidates_keys() -> None:
    metadata = CustomerMetadata(
        {"channel": "mobile"}
    )

    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        metadata.with_value(
            "refresh_token",
            "secret",
        )


def test_customer_metadata_without_is_immutable() -> None:
    original = CustomerMetadata(
        {
            "channel": "mobile",
            "corridor": "AU-BI",
        }
    )

    updated = original.without("corridor")

    assert "corridor" in original.values
    assert "corridor" not in updated.values


def test_customer_metadata_canonical_dict_is_immutable() -> None:
    metadata = CustomerMetadata(
        {"channel": "mobile"}
    )

    payload = metadata.canonical_dict()

    assert isinstance(payload, MappingProxyType)

    with pytest.raises(TypeError):
        payload["channel"] = "agent"  # type: ignore[index]


@pytest.mark.parametrize(
    "value",
    [123, object(), ["channel"]],
)
def test_customer_metadata_rejects_non_mapping(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="customer metadata must be a mapping",
    ):
        CustomerMetadata.of(value)


def test_customer_value_objects_are_slotted() -> None:
    objects = (
        CustomerName("Djuma Kikombe"),
        CustomerContact(email="user@example.com"),
        CustomerAddress(
            country_code="AU",
            address_line_1="10 Main Street",
            locality="Melbourne",
        ),
        CustomerPreferences(),
        CustomerMetadata(),
    )

    for value in objects:
        assert not hasattr(value, "__dict__")


def test_customer_module_declares_value_objects() -> None:
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
