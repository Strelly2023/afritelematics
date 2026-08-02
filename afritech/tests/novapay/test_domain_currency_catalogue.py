from __future__ import annotations

from types import MappingProxyType

import pytest

from afritech.novapay.domain.currency import (
    STANDARD_CURRENCY_DEFINITIONS,
    CurrencyDefinition,
    CurrencyRegistry,
    CurrencyStatus,
    CurrencyType,
    standard_currency_definitions,
    standard_currency_registry,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)


EXPECTED_CODES = (
    "AUD",
    "BIF",
    "CAD",
    "CDF",
    "EUR",
    "GBP",
    "KES",
    "MWK",
    "NZD",
    "RWF",
    "TZS",
    "UGX",
    "USD",
    "ZAR",
    "ZMW",
)

EXPECTED_NUMERIC_CODES = {
    "AUD": "036",
    "BIF": "108",
    "CAD": "124",
    "CDF": "976",
    "EUR": "978",
    "GBP": "826",
    "KES": "404",
    "MWK": "454",
    "NZD": "554",
    "RWF": "646",
    "TZS": "834",
    "UGX": "800",
    "USD": "840",
    "ZAR": "710",
    "ZMW": "967",
}

ZERO_MINOR_UNIT_CODES = {
    "BIF",
    "RWF",
    "UGX",
}


def test_standard_definition_count() -> None:
    assert len(STANDARD_CURRENCY_DEFINITIONS) == 15


def test_standard_definitions_are_tuple() -> None:
    assert isinstance(
        STANDARD_CURRENCY_DEFINITIONS,
        tuple,
    )


def test_standard_definition_codes_are_sorted() -> None:
    assert tuple(
        definition.code
        for definition in STANDARD_CURRENCY_DEFINITIONS
    ) == EXPECTED_CODES


def test_standard_definitions_are_canonical() -> None:
    for definition in STANDARD_CURRENCY_DEFINITIONS:
        assert isinstance(
            definition,
            CurrencyDefinition,
        )
        assert definition.currency == Currency.of(
            definition.code
        )
        assert definition.currency_type is CurrencyType.FIAT
        assert definition.status is CurrencyStatus.ACTIVE
        assert definition.version == 1


def test_definition_ids_match_codes() -> None:
    for definition in STANDARD_CURRENCY_DEFINITIONS:
        assert (
            definition.currency_definition_id.value
            == f"currency-{definition.code}"
        )


def test_numeric_codes_are_complete_and_unique() -> None:
    numeric_codes = [
        definition.numeric_code
        for definition in STANDARD_CURRENCY_DEFINITIONS
    ]

    assert None not in numeric_codes
    assert len(numeric_codes) == len(set(numeric_codes))

    assert {
        definition.code: definition.numeric_code
        for definition in STANDARD_CURRENCY_DEFINITIONS
    } == EXPECTED_NUMERIC_CODES


def test_definition_codes_are_unique() -> None:
    codes = [
        definition.code
        for definition in STANDARD_CURRENCY_DEFINITIONS
    ]

    assert len(codes) == len(set(codes))


def test_definition_ids_are_unique() -> None:
    identifiers = [
        definition.currency_definition_id.value
        for definition in STANDARD_CURRENCY_DEFINITIONS
    ]

    assert len(identifiers) == len(set(identifiers))


def test_standard_minor_units_match_currency_contract() -> None:
    for definition in STANDARD_CURRENCY_DEFINITIONS:
        assert (
            definition.minor_units
            == definition.currency.minor_units
        )


@pytest.mark.parametrize(
    "code",
    sorted(ZERO_MINOR_UNIT_CODES),
)
def test_zero_minor_unit_currencies(
    code: str,
) -> None:
    definition = next(
        item
        for item in STANDARD_CURRENCY_DEFINITIONS
        if item.code == code
    )

    assert definition.minor_units == 0


@pytest.mark.parametrize(
    "code",
    [
        "AUD",
        "CDF",
        "EUR",
        "GBP",
        "KES",
        "MWK",
        "TZS",
        "USD",
        "ZAR",
        "ZMW",
    ],
)
def test_two_minor_unit_currencies(
    code: str,
) -> None:
    definition = next(
        item
        for item in STANDARD_CURRENCY_DEFINITIONS
        if item.code == code
    )

    assert definition.minor_units == 2


def test_standard_metadata_contract() -> None:
    for definition in STANDARD_CURRENCY_DEFINITIONS:
        assert definition.metadata.values == {
            "catalogue": "novapay-standard",
            "source": "canonical",
        }
        assert isinstance(
            definition.metadata.values,
            MappingProxyType,
        )


def test_standard_definitions_function_returns_immutable_catalogue() -> None:
    first = standard_currency_definitions()
    second = standard_currency_definitions()

    assert isinstance(first, tuple)
    assert isinstance(second, tuple)
    assert first == STANDARD_CURRENCY_DEFINITIONS
    assert second == STANDARD_CURRENCY_DEFINITIONS

    # Reusing the canonical tuple is safe because both the collection
    # and every CurrencyDefinition element are immutable.
    assert first is STANDARD_CURRENCY_DEFINITIONS
    assert second is STANDARD_CURRENCY_DEFINITIONS


def test_standard_definition_objects_are_reused() -> None:
    first = standard_currency_definitions()
    second = standard_currency_definitions()

    for left, right, canonical in zip(
        first,
        second,
        STANDARD_CURRENCY_DEFINITIONS,
        strict=True,
    ):
        assert left is canonical
        assert right is canonical


def test_standard_registry_factory() -> None:
    registry = standard_currency_registry()

    assert isinstance(registry, CurrencyRegistry)
    assert registry.currency_registry_id.value == (
        "novapay-standard-currency-registry"
    )
    assert registry.version == 1
    assert registry.size == 15

    assert tuple(
        definition.code
        for definition in registry.definitions
    ) == EXPECTED_CODES


def test_standard_registry_factory_is_fresh() -> None:
    first = standard_currency_registry()
    second = standard_currency_registry()

    assert first == second
    assert first is not second
    assert first.definitions == second.definitions


def test_standard_registry_metadata() -> None:
    registry = standard_currency_registry()

    assert registry.metadata.values == {
        "catalogue": "novapay-standard",
        "definition_count": 15,
    }


def test_standard_registry_metadata_override() -> None:
    registry = standard_currency_registry(
        metadata={
            "owner": "NovaPay Treasury",
        }
    )

    assert registry.metadata.values == {
        "catalogue": "novapay-standard",
        "definition_count": 15,
        "owner": "NovaPay Treasury",
    }


def test_standard_registry_custom_id() -> None:
    registry = standard_currency_registry(
        currency_registry_id="registry-africa"
    )

    assert registry.currency_registry_id.value == (
        "registry-africa"
    )


def test_standard_registry_rejects_non_mapping_metadata() -> None:
    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        standard_currency_registry(
            metadata="invalid"
        )


@pytest.mark.parametrize(
    ("code", "country_code"),
    [
        ("AUD", "AU"),
        ("BIF", "BI"),
        ("CDF", "CD"),
        ("GBP", "GB"),
        ("KES", "KE"),
        ("MWK", "MW"),
        ("NZD", "NZ"),
        ("RWF", "RW"),
        ("TZS", "TZ"),
        ("UGX", "UG"),
        ("USD", "US"),
        ("ZAR", "ZA"),
        ("ZMW", "ZM"),
    ],
)
def test_standard_country_support(
    code: str,
    country_code: str,
) -> None:
    definition = standard_currency_registry().require_by_code(
        code
    )

    assert definition.supports_country(country_code)


def test_euro_supports_multiple_countries() -> None:
    euro = standard_currency_registry().require_by_code(
        "EUR"
    )

    for country in (
        "AT",
        "BE",
        "DE",
        "ES",
        "FI",
        "FR",
        "IE",
        "IT",
        "LU",
        "NL",
        "PT",
    ):
        assert euro.supports_country(country)


def test_african_country_filtering() -> None:
    registry = standard_currency_registry()

    expected = {
        "BI": "BIF",
        "CD": "CDF",
        "KE": "KES",
        "MW": "MWK",
        "RW": "RWF",
        "TZ": "TZS",
        "UG": "UGX",
        "ZA": "ZAR",
        "ZM": "ZMW",
    }

    for country, code in expected.items():
        definitions = registry.definitions_for_country(
            country,
            active_only=True,
        )

        assert tuple(
            definition.code
            for definition in definitions
        ) == (code,)


def test_standard_registry_all_definitions_active() -> None:
    registry = standard_currency_registry()

    assert registry.active_definitions() == (
        registry.definitions
    )


def test_standard_registry_all_definitions_fiat() -> None:
    registry = standard_currency_registry()

    assert registry.definitions_by_type(
        CurrencyType.FIAT,
        active_only=True,
    ) == registry.definitions


@pytest.mark.parametrize(
    ("code", "raw", "expected"),
    [
        ("AUD", "66.165", "66.16"),
        ("BIF", "1234.5", "1234"),
        ("CDF", "1234.4", "1234.40"),
        ("RWF", "1234.5", "1234"),
        ("UGX", "1234.5", "1234"),
        ("USD", "66.175", "66.18"),
    ],
)
def test_standard_money_precision(
    code: str,
    raw: str,
    expected: str,
) -> None:
    definition = standard_currency_registry().require_by_code(
        code
    )

    money = Money.of(
        raw,
        definition.currency,
    )

    assert str(money.amount) == expected


def test_standard_registry_serialization_is_deterministic() -> None:
    first = standard_currency_registry().canonical_dict()
    second = standard_currency_registry().canonical_dict()

    assert first == second
    assert [
        definition["currency"]["code"]
        for definition in first["definitions"]
    ] == list(EXPECTED_CODES)


def test_catalogue_contains_no_runtime_authority() -> None:
    registry = standard_currency_registry()

    for forbidden in (
        "repository",
        "database",
        "save",
        "load",
        "provider_client",
        "fx_engine",
        "wallet_id",
        "ledger_account_id",
        "transaction_id",
        "exchange_rate_id",
        "settlement_id",
    ):
        assert not hasattr(registry, forbidden)


def test_currency_module_catalogue_contract() -> None:
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
