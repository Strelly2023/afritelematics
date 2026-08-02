from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from enum import Enum
from types import MappingProxyType

import pytest

from afritech.novapay.domain.currency import (
    CurrencyCountryCodes,
    CurrencyDefinition,
    CurrencyDefinitionId,
    CurrencyMetadata,
    CurrencyName,
    CurrencyRoundingMode,
    CurrencyStatus,
    CurrencySymbol,
    CurrencyType,
)
from afritech.novapay.domain.money import Currency


def aud_definition(
    **overrides: object,
) -> CurrencyDefinition:
    values: dict[str, object] = {
        "currency_definition_id": (
            CurrencyDefinitionId("currency-AUD")
        ),
        "currency": Currency.of("AUD"),
        "name": CurrencyName("Australian Dollar"),
        "symbol": CurrencySymbol("$"),
        "currency_type": CurrencyType.FIAT,
        "status": CurrencyStatus.ACTIVE,
        "minor_units": 2,
        "rounding_mode": (
            CurrencyRoundingMode.HALF_EVEN
        ),
        "country_codes": CurrencyCountryCodes(
            ("AU",)
        ),
        "numeric_code": "036",
        "fund_code": None,
        "metadata": CurrencyMetadata(
            {
                "issuer": "Reserve Bank of Australia",
            }
        ),
        "version": 1,
    }
    values.update(overrides)

    return CurrencyDefinition(**values)  # type: ignore[arg-type]


def test_create_currency_definition() -> None:
    definition = CurrencyDefinition.create(
        currency_definition_id=" currency-AUD ",
        currency=" aud ",
        name=" Australian   Dollar ",
        symbol=" $ ",
        currency_type=" FIAT ",
        status=" ACTIVE ",
        country_codes=["au", "AU"],
        numeric_code="036",
        metadata={
            " Issuer ": "Reserve Bank of Australia",
        },
    )

    assert definition.currency_definition_id == (
        CurrencyDefinitionId("currency-AUD")
    )
    assert definition.currency == Currency.of("AUD")
    assert definition.code == "AUD"
    assert definition.name == CurrencyName(
        "Australian Dollar"
    )
    assert definition.symbol == CurrencySymbol("$")
    assert definition.currency_type is CurrencyType.FIAT
    assert definition.status is CurrencyStatus.ACTIVE
    assert definition.minor_units == 2
    assert definition.rounding_mode is (
        CurrencyRoundingMode.HALF_EVEN
    )
    assert definition.country_codes.values == ("AU",)
    assert definition.numeric_code == "036"
    assert definition.metadata.values == {
        "issuer": "Reserve Bank of Australia",
    }
    assert definition.version == 1
    assert definition.is_active is True
    assert definition.is_fiat is True


def test_currency_definition_is_immutable() -> None:
    definition = aud_definition()

    with pytest.raises(FrozenInstanceError):
        definition.status = (  # type: ignore[misc]
            CurrencyStatus.SUSPENDED
        )


def test_currency_definition_uses_slots() -> None:
    assert not hasattr(aud_definition(), "__dict__")


def test_currency_definition_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(CurrencyDefinition)
    } == {
        "currency_definition_id",
        "currency",
        "name",
        "symbol",
        "currency_type",
        "status",
        "minor_units",
        "rounding_mode",
        "country_codes",
        "numeric_code",
        "fund_code",
        "metadata",
        "version",
    }


@pytest.mark.parametrize(
    "enum_type",
    [
        CurrencyStatus,
        CurrencyType,
        CurrencyRoundingMode,
    ],
)
def test_currency_enums_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


@pytest.mark.parametrize(
    ("enum_type", "raw", "expected"),
    [
        (
            CurrencyStatus,
            " ACTIVE ",
            CurrencyStatus.ACTIVE,
        ),
        (
            CurrencyType,
            "commodity-backed",
            CurrencyType.COMMODITY_BACKED,
        ),
        (
            CurrencyRoundingMode,
            " HALF EVEN ",
            CurrencyRoundingMode.HALF_EVEN,
        ),
    ],
)
def test_currency_enums_parse_normalized_values(
    enum_type: object,
    raw: str,
    expected: object,
) -> None:
    assert enum_type.parse(raw) is expected  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("enum_type", "raw"),
    [
        (CurrencyStatus, "unknown"),
        (CurrencyType, "unknown"),
        (CurrencyRoundingMode, "unknown"),
    ],
)
def test_currency_enums_reject_unknown_values(
    enum_type: object,
    raw: str,
) -> None:
    with pytest.raises(ValueError):
        enum_type.parse(raw)  # type: ignore[attr-defined]


def test_currency_definition_id_normalization() -> None:
    identifier = CurrencyDefinitionId.of(
        " currency-definition-001 "
    )

    assert identifier.value == "currency-definition-001"
    assert str(identifier) == "currency-definition-001"


@pytest.mark.parametrize(
    "value_type",
    [
        CurrencyDefinitionId,
        CurrencyName,
        CurrencySymbol,
    ],
)
def test_text_value_objects_are_immutable(
    value_type: object,
) -> None:
    value = value_type(" value ")  # type: ignore[operator]

    assert not hasattr(value, "__dict__")

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("value_type", "value"),
    [
        (CurrencyDefinitionId, ""),
        (CurrencyName, " "),
        (CurrencySymbol, ""),
    ],
)
def test_text_value_objects_reject_empty(
    value_type: object,
    value: str,
) -> None:
    with pytest.raises(ValueError):
        value_type(value)  # type: ignore[operator]


def test_country_codes_normalize_sort_and_deduplicate() -> None:
    countries = CurrencyCountryCodes.of(
        ["cd", "BI", "au", "CD"]
    )

    assert countries.values == (
        "AU",
        "BI",
        "CD",
    )
    assert countries.contains("cd") is True
    assert countries.contains("US") is False


@pytest.mark.parametrize(
    "country_code",
    [
        "",
        "A",
        "AUS",
        "1A",
        "ÄU",
    ],
)
def test_country_codes_reject_invalid_values(
    country_code: str,
) -> None:
    with pytest.raises(ValueError):
        CurrencyCountryCodes.of(
            [country_code]
        )


def test_country_codes_are_immutable() -> None:
    countries = CurrencyCountryCodes.of(
        ["AU"]
    )

    assert countries.values == ("AU",)

    with pytest.raises(FrozenInstanceError):
        countries.values = ("US",)  # type: ignore[misc]


def test_currency_metadata_normalizes_keys() -> None:
    metadata = CurrencyMetadata(
        {
            " Central Bank ": "RBA",
            " Domestic Only ": True,
        }
    )

    assert metadata.values == {
        "central_bank": "RBA",
        "domestic_only": True,
    }
    assert isinstance(metadata.values, MappingProxyType)


def test_currency_metadata_is_defensive() -> None:
    source = {
        "issuer": "RBA",
    }

    metadata = CurrencyMetadata(source)
    source["issuer"] = "changed"

    assert metadata.values == {
        "issuer": "RBA",
    }


def test_currency_metadata_with_updates() -> None:
    metadata = CurrencyMetadata(
        {
            "issuer": "RBA",
        }
    )

    updated = metadata.with_updates(
        {
            "region": "Oceania",
        }
    )

    assert metadata.values == {
        "issuer": "RBA",
    }
    assert updated.values == {
        "issuer": "RBA",
        "region": "Oceania",
    }


@pytest.mark.parametrize(
    "key",
    [
        "access_token",
        "password",
        "private_key",
        "card_number",
    ],
)
def test_currency_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        CurrencyMetadata(
            {
                key: "secret",
            }
        )


def test_currency_metadata_rejects_unsupported_values() -> None:
    with pytest.raises(
        TypeError,
        match="unsupported value type",
    ):
        CurrencyMetadata(
            {
                "object": object(),
            }
        )


@pytest.mark.parametrize(
    ("currency", "minor_units"),
    [
        ("AUD", 0),
        ("AUD", 3),
        ("BIF", 2),
    ],
)
def test_definition_minor_units_must_match_currency(
    currency: str,
    minor_units: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must match",
    ):
        aud_definition(
            currency=Currency.of(currency),
            minor_units=minor_units,
        )


def test_bif_definition_uses_zero_minor_units() -> None:
    definition = CurrencyDefinition.create(
        currency_definition_id="currency-BIF",
        currency="BIF",
        name="Burundian Franc",
        symbol="FBu",
        currency_type="fiat",
        status="active",
        country_codes=["BI"],
        numeric_code="108",
    )

    assert definition.currency == Currency.of("BIF")
    assert definition.minor_units == 0


@pytest.mark.parametrize(
    "minor_units",
    [
        -1,
        9,
    ],
)
def test_minor_units_reject_out_of_range(
    minor_units: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 8",
    ):
        aud_definition(
            minor_units=minor_units,
        )


@pytest.mark.parametrize(
    "minor_units",
    [
        True,
        "2",
        2.0,
        None,
    ],
)
def test_minor_units_reject_non_integer(
    minor_units: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        aud_definition(
            minor_units=minor_units,
        )


@pytest.mark.parametrize(
    "numeric_code",
    [
        "",
        "36",
        "0036",
        "A36",
    ],
)
def test_numeric_code_rejects_invalid_values(
    numeric_code: str,
) -> None:
    with pytest.raises(ValueError):
        aud_definition(
            numeric_code=numeric_code,
        )


def test_numeric_code_is_optional() -> None:
    definition = aud_definition(
        numeric_code=None,
    )

    assert definition.numeric_code is None


@pytest.mark.parametrize(
    "fund_code",
    [
        "",
        "A",
        "AB",
        "ABCD",
        "A1D",
    ],
)
def test_fund_code_rejects_invalid_values(
    fund_code: str,
) -> None:
    with pytest.raises(ValueError):
        aud_definition(
            fund_code=fund_code,
        )


def test_fund_code_normalizes_uppercase() -> None:
    definition = aud_definition(
        fund_code=" aud ",
    )

    assert definition.fund_code == "AUD"


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_version_rejects_invalid_values(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        aud_definition(
            version=version,
        )


@pytest.mark.parametrize(
    "version",
    [
        True,
        "1",
        1.0,
        None,
    ],
)
def test_version_rejects_non_integer(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        aud_definition(
            version=version,
        )


def test_supports_country() -> None:
    definition = aud_definition()

    assert definition.supports_country("au") is True
    assert definition.supports_country("US") is False


def test_definition_canonical_dict() -> None:
    definition = aud_definition()

    payload = definition.canonical_dict()

    assert list(payload) == [
        "currency_definition_id",
        "currency",
        "name",
        "symbol",
        "currency_type",
        "status",
        "minor_units",
        "rounding_mode",
        "country_codes",
        "numeric_code",
        "fund_code",
        "metadata",
        "version",
    ]
    assert payload["currency_definition_id"] == (
        "currency-AUD"
    )
    assert payload["currency"] == {
        "code": "AUD",
        "minor_units": 2,
    }
    assert payload["name"] == "Australian Dollar"
    assert payload["symbol"] == "$"
    assert payload["currency_type"] == "fiat"
    assert payload["status"] == "active"
    assert payload["minor_units"] == 2
    assert payload["rounding_mode"] == "half_even"
    assert payload["country_codes"] == ["AU"]
    assert payload["numeric_code"] == "036"
    assert payload["version"] == 1


def test_definition_canonical_dict_is_fresh() -> None:
    definition = aud_definition()

    first = definition.canonical_dict()
    second = definition.canonical_dict()

    assert first == second
    assert first is not second
    assert first["currency"] is not second["currency"]
    assert first["metadata"] is not second["metadata"]


def test_currency_definition_reuses_canonical_currency() -> None:
    definition = aud_definition()

    assert type(definition.currency) is Currency
    assert definition.currency is Currency.of(
        definition.currency
    )


def test_definition_contains_no_external_authority() -> None:
    definition = aud_definition()

    for forbidden in (
        "registry",
        "definitions",
        "register",
        "repository",
        "database",
        "provider_client",
        "wallet_id",
        "ledger_account_id",
        "transaction_id",
        "exchange_rate_id",
        "postings",
        "balance",
    ):
        assert not hasattr(definition, forbidden)


def test_definition_owns_its_lifecycle_contract() -> None:
    definition = aud_definition()

    for method_name in (
        "activate",
        "suspend",
        "reactivate",
        "retire",
        "update_name",
        "update_symbol",
        "update_country_codes",
        "update_metadata",
    ):
        assert callable(getattr(definition, method_name))


def test_currency_module_public_contract() -> None:
    from afritech.novapay.domain import currency

    assert currency.__all__ == [
        "CurrencyCountryCodes",
        "CurrencyDefinition",
        "CurrencyDefinitionId",
        "CurrencyMetadata",
        "CurrencyName",
        "CurrencyRegistry",
        "CurrencyRegistryId",
        "CurrencyRoundingMode",
        "CurrencyStatus",
        "CurrencySymbol",
        "CurrencyType",
        "STANDARD_CURRENCY_DEFINITIONS",
        "standard_currency_definitions",
        "standard_currency_registry",
    ]
