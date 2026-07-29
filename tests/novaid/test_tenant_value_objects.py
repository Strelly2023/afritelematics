from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from afritech.novaid.domain import (
    LegalEntity,
    Tenant,
    TenantBrand,
)


def test_legal_entity_normalizes_values() -> None:
    legal_entity = LegalEntity(
        legal_name="  NovaTech Australia Pty Ltd  ",
        registration_number="  ACN-123456789  ",
        tax_identifier="  ABN-12345678901  ",
        country_code=" au ",
    )

    assert (
        legal_entity.legal_name
        == "NovaTech Australia Pty Ltd"
    )
    assert (
        legal_entity.registration_number
        == "ACN-123456789"
    )
    assert (
        legal_entity.tax_identifier
        == "ABN-12345678901"
    )
    assert legal_entity.country_code == "AU"


def test_legal_entity_normalizes_blank_optional_values() -> None:
    legal_entity = LegalEntity(
        legal_name="NovaTech Australia Pty Ltd",
        registration_number="   ",
        tax_identifier="   ",
        country_code="AU",
    )

    assert legal_entity.registration_number is None
    assert legal_entity.tax_identifier is None


@pytest.mark.parametrize(
    "country_code",
    [
        "",
        "A",
        "AUS",
        "12",
        "A1",
        " australia ",
    ],
)
def test_legal_entity_rejects_invalid_country_code(
    country_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_COUNTRY_CODE",
    ):
        LegalEntity(
            legal_name="NovaTech Australia Pty Ltd",
            registration_number="ACN-123456789",
            country_code=country_code,
        )


@pytest.mark.parametrize(
    "legal_name",
    [
        "",
        " ",
        "   ",
    ],
)
def test_legal_entity_rejects_missing_legal_name(
    legal_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="LEGAL_ENTITY_NAME_REQUIRED",
    ):
        LegalEntity(
            legal_name=legal_name,
            registration_number="ACN-123456789",
            country_code="AU",
        )


def test_tenant_brand_normalizes_values() -> None:
    brand = TenantBrand(
        display_name="  NovaTech  ",
        short_name="  Nova  ",
        support_email=(
            "  SUPPORT@AFRITECHNOLOGY.COM  "
        ),
        primary_domain="  AFRITECHNOLOGY.COM  ",
    )

    assert brand.display_name == "NovaTech"
    assert brand.short_name == "Nova"
    assert (
        brand.support_email
        == "support@afritechnology.com"
    )
    assert (
        brand.primary_domain
        == "afritechnology.com"
    )


def test_tenant_brand_normalizes_blank_optional_values() -> None:
    brand = TenantBrand(
        display_name="NovaTech",
        short_name="   ",
        support_email="   ",
        primary_domain="   ",
    )

    assert brand.short_name is None
    assert brand.support_email is None
    assert brand.primary_domain is None


@pytest.mark.parametrize(
    "display_name",
    [
        "",
        " ",
        "   ",
    ],
)
def test_tenant_brand_rejects_missing_display_name(
    display_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="TENANT_BRAND_NAME_REQUIRED",
    ):
        TenantBrand(
            display_name=display_name,
        )


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        (
            "AFRITECHNOLOGY.COM",
            "afritechnology.com",
        ),
        (
            " NovaRide.AFRITECHNOLOGY.COM ",
            "novaride.afritechnology.com",
        ),
        (
            "IDENTITY.NOVATECH.COM",
            "identity.novatech.com",
        ),
    ],
)
def test_tenant_brand_lowercases_domains(
    domain: str,
    expected: str,
) -> None:
    brand = TenantBrand(
        display_name="NovaTech",
        support_email=(
            "support@afritechnology.com"
        ),
        primary_domain=domain,
    )

    assert brand.primary_domain == expected


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        (
            "SUPPORT@AFRITECHNOLOGY.COM",
            "support@afritechnology.com",
        ),
        (
            " Identity@NovaTech.COM ",
            "identity@novatech.com",
        ),
    ],
)
def test_tenant_brand_lowercases_email(
    email: str,
    expected: str,
) -> None:
    brand = TenantBrand(
        display_name="NovaTech",
        support_email=email,
        primary_domain="afritechnology.com",
    )

    assert brand.support_email == expected


@pytest.mark.parametrize(
    ("value_object", "field_name", "replacement"),
    [
        (
            LegalEntity(
                legal_name=(
                    "NovaTech Australia Pty Ltd"
                ),
                registration_number=(
                    "ACN-123456789"
                ),
                country_code="AU",
            ),
            "legal_name",
            "Changed Legal Name",
        ),
        (
            TenantBrand(
                display_name="NovaTech",
                support_email=(
                    "support@afritechnology.com"
                ),
                primary_domain=(
                    "afritechnology.com"
                ),
            ),
            "display_name",
            "Changed Brand",
        ),
    ],
)
def test_value_objects_are_immutable(
    value_object: object,
    field_name: str,
    replacement: str,
) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(
            value_object,
            field_name,
            replacement,
        )


def test_tenant_stores_legal_entity() -> None:
    legal_entity = LegalEntity(
        legal_name="NovaTech Australia Pty Ltd",
        registration_number="ACN-123456789",
        country_code="AU",
    )

    brand = TenantBrand(
        display_name="NovaTech",
        support_email=(
            "support@afritechnology.com"
        ),
        primary_domain="afritechnology.com",
    )

    tenant = Tenant(
        tenant_id="tenant-novatech-au",
        name="NovaTech Australia",
        legal_entity=legal_entity,
        brand=brand,
    )

    assert tenant.legal_entity is legal_entity
    assert tenant.legal_entity is not None
    assert (
        tenant.legal_entity.legal_name
        == "NovaTech Australia Pty Ltd"
    )
    assert tenant.legal_entity.country_code == "AU"


def test_tenant_stores_tenant_brand() -> None:
    legal_entity = LegalEntity(
        legal_name="NovaTech Australia Pty Ltd",
        registration_number="ACN-123456789",
        country_code="AU",
    )

    brand = TenantBrand(
        display_name="NovaTech",
        support_email=(
            "SUPPORT@AFRITECHNOLOGY.COM"
        ),
        primary_domain="AFRITECHNOLOGY.COM",
    )

    tenant = Tenant(
        tenant_id="tenant-novatech-au",
        name="NovaTech Australia",
        legal_entity=legal_entity,
        brand=brand,
    )

    assert tenant.brand is brand
    assert tenant.brand is not None
    assert tenant.brand.display_name == "NovaTech"
    assert (
        tenant.brand.support_email
        == "support@afritechnology.com"
    )
    assert (
        tenant.brand.primary_domain
        == "afritechnology.com"
    )


def test_tenant_transition_preserves_profile_objects() -> None:
    legal_entity = LegalEntity(
        legal_name="NovaTech Australia Pty Ltd",
        registration_number="ACN-123456789",
        country_code="AU",
    )

    brand = TenantBrand(
        display_name="NovaTech",
        primary_domain="afritechnology.com",
    )

    tenant = Tenant(
        tenant_id="tenant-novatech-au",
        name="NovaTech Australia",
        legal_entity=legal_entity,
        brand=brand,
        metadata={
            "environment": "controlled-pilot",
        },
    )

    suspended = tenant.transition("SUSPENDED")

    assert suspended.legal_entity is legal_entity
    assert suspended.brand is brand
    assert suspended.metadata == tenant.metadata
    assert suspended.version == tenant.version + 1
