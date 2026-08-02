from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from afritech.novapay.domain.currency import (
    CurrencyDefinition,
    CurrencyMetadata,
    CurrencyRegistry,
    CurrencyRegistryId,
    CurrencyRoundingMode,
    CurrencyStatus,
    CurrencyType,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)


def currency_definition(
    code: str,
    *,
    definition_id: str | None = None,
    name: str | None = None,
    symbol: str | None = None,
    status: CurrencyStatus = CurrencyStatus.ACTIVE,
    currency_type: CurrencyType = CurrencyType.FIAT,
    countries: tuple[str, ...] = (),
    numeric_code: str | None = None,
) -> CurrencyDefinition:
    defaults = {
        "AUD": (
            "Australian Dollar",
            "$",
            ("AU",),
            "036",
        ),
        "BIF": (
            "Burundian Franc",
            "FBu",
            ("BI",),
            "108",
        ),
        "CDF": (
            "Congolese Franc",
            "FC",
            ("CD",),
            "976",
        ),
        "USD": (
            "US Dollar",
            "$",
            ("US",),
            "840",
        ),
        "EUR": (
            "Euro",
            "€",
            (
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
            ),
            "978",
        ),
    }

    default_name, default_symbol, default_countries, default_numeric = (
        defaults[code]
    )

    return CurrencyDefinition.create(
        currency_definition_id=(
            definition_id
            or f"currency-{code}"
        ),
        currency=code,
        name=name or default_name,
        symbol=symbol or default_symbol,
        currency_type=currency_type,
        status=status,
        country_codes=(
            countries or default_countries
        ),
        numeric_code=(
            numeric_code
            if numeric_code is not None
            else default_numeric
        ),
    )


def empty_registry() -> CurrencyRegistry:
    return CurrencyRegistry.create(
        currency_registry_id="registry-global",
        metadata={
            "scope": "global",
        },
    )


def populated_registry() -> CurrencyRegistry:
    return CurrencyRegistry.create(
        currency_registry_id="registry-global",
        definitions=(
            currency_definition("USD"),
            currency_definition("AUD"),
            currency_definition("BIF"),
            currency_definition(
                "CDF",
                status=CurrencyStatus.SUSPENDED,
            ),
        ),
        metadata={
            "scope": "global",
        },
    )


def test_create_empty_registry() -> None:
    registry = empty_registry()

    assert registry.currency_registry_id == (
        CurrencyRegistryId("registry-global")
    )
    assert registry.definitions == ()
    assert registry.metadata.values == {
        "scope": "global",
    }
    assert registry.version == 1
    assert registry.size == 0
    assert registry.is_empty is True
    assert len(registry) == 0


def test_create_populated_registry_sorts_definitions() -> None:
    registry = populated_registry()

    assert tuple(
        definition.code
        for definition in registry.definitions
    ) == (
        "AUD",
        "BIF",
        "CDF",
        "USD",
    )
    assert registry.size == 4
    assert registry.is_empty is False


def test_registry_is_immutable() -> None:
    registry = populated_registry()

    with pytest.raises(FrozenInstanceError):
        registry.version = 99  # type: ignore[misc]


def test_registry_uses_slots() -> None:
    assert not hasattr(populated_registry(), "__dict__")


def test_registry_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(CurrencyRegistry)
    } == {
        "currency_registry_id",
        "definitions",
        "metadata",
        "version",
    }


def test_registry_id_normalization() -> None:
    registry_id = CurrencyRegistryId.of(
        " registry-global "
    )

    assert registry_id.value == "registry-global"
    assert str(registry_id) == "registry-global"


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
    ],
)
def test_registry_id_rejects_empty(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CurrencyRegistryId(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        True,
    ],
)
def test_registry_id_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        CurrencyRegistryId.of(value)


def test_registry_rejects_non_definition_values() -> None:
    with pytest.raises(
        TypeError,
        match="CurrencyDefinition",
    ):
        CurrencyRegistry.create(
            currency_registry_id="registry-global",
            definitions=("AUD",),
        )


def test_registry_rejects_duplicate_definition_id() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate definition id",
    ):
        CurrencyRegistry.create(
            currency_registry_id="registry-global",
            definitions=(
                currency_definition(
                    "AUD",
                    definition_id="currency-001",
                ),
                currency_definition(
                    "USD",
                    definition_id="currency-001",
                ),
            ),
        )


def test_registry_rejects_duplicate_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate currency code",
    ):
        CurrencyRegistry.create(
            currency_registry_id="registry-global",
            definitions=(
                currency_definition(
                    "AUD",
                    definition_id="currency-AUD-1",
                ),
                currency_definition(
                    "AUD",
                    definition_id="currency-AUD-2",
                ),
            ),
        )


def test_registry_rejects_duplicate_numeric_code() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate numeric code",
    ):
        CurrencyRegistry.create(
            currency_registry_id="registry-global",
            definitions=(
                currency_definition("AUD"),
                currency_definition(
                    "USD",
                    numeric_code="036",
                ),
            ),
        )


def test_get_and_require_by_id() -> None:
    registry = populated_registry()

    found = registry.get_by_id(
        " currency-AUD "
    )

    assert found is not None
    assert found.code == "AUD"
    assert registry.require_by_id(
        "currency-AUD"
    ) is found
    assert registry.get_by_id(
        "currency-EUR"
    ) is None

    with pytest.raises(
        KeyError,
        match="currency-EUR",
    ):
        registry.require_by_id(
            "currency-EUR"
        )


def test_get_and_require_by_code() -> None:
    registry = populated_registry()

    found = registry.get_by_code(" aud ")

    assert found is not None
    assert found.code == "AUD"
    assert registry.require_by_code(
        Currency.of("AUD")
    ) is found
    assert registry.get_by_code("EUR") is None

    with pytest.raises(
        KeyError,
        match="EUR",
    ):
        registry.require_by_code("EUR")


def test_contains_contracts() -> None:
    registry = populated_registry()

    assert registry.contains_code("AUD") is True
    assert registry.contains_code("EUR") is False
    assert registry.contains_id(
        "currency-AUD"
    ) is True
    assert registry.contains_id(
        "currency-EUR"
    ) is False


def test_registry_iteration_is_deterministic() -> None:
    registry = populated_registry()

    assert tuple(
        definition.code
        for definition in registry
    ) == (
        "AUD",
        "BIF",
        "CDF",
        "USD",
    )


def test_active_definitions() -> None:
    registry = populated_registry()

    assert tuple(
        definition.code
        for definition in registry.active_definitions()
    ) == (
        "AUD",
        "BIF",
        "USD",
    )


def test_definitions_for_country() -> None:
    registry = populated_registry()

    assert tuple(
        definition.code
        for definition in registry.definitions_for_country(
            " cd "
        )
    ) == ("CDF",)

    assert registry.definitions_for_country(
        "AU",
        active_only=True,
    )[0].code == "AUD"


def test_country_lookup_can_exclude_suspended() -> None:
    registry = populated_registry()

    assert registry.definitions_for_country(
        "CD",
        active_only=False,
    )[0].code == "CDF"

    assert registry.definitions_for_country(
        "CD",
        active_only=True,
    ) == ()


@pytest.mark.parametrize(
    "active_only",
    [
        None,
        1,
        "true",
    ],
)
def test_country_lookup_requires_boolean_active_only(
    active_only: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a boolean",
    ):
        populated_registry().definitions_for_country(
            "AU",
            active_only=active_only,  # type: ignore[arg-type]
        )


def test_definitions_by_type() -> None:
    registry = CurrencyRegistry.create(
        currency_registry_id="registry-global",
        definitions=(
            currency_definition("AUD"),
            currency_definition(
                "USD",
                currency_type=CurrencyType.TEST,
            ),
        ),
    )

    assert tuple(
        definition.code
        for definition in registry.definitions_by_type(
            "fiat"
        )
    ) == ("AUD",)

    assert tuple(
        definition.code
        for definition in registry.definitions_by_type(
            CurrencyType.TEST
        )
    ) == ("USD",)


def test_register_definition() -> None:
    registry = empty_registry()
    aud = currency_definition("AUD")

    updated = registry.register(aud)

    assert registry.is_empty is True
    assert updated.size == 1
    assert updated.require_by_code("AUD") is aud
    assert updated.version == 2
    assert updated.currency_registry_id == (
        registry.currency_registry_id
    )


def test_register_preserves_deterministic_order() -> None:
    registry = (
        empty_registry()
        .register(currency_definition("USD"))
        .register(currency_definition("AUD"))
        .register(currency_definition("BIF"))
    )

    assert tuple(
        definition.code
        for definition in registry.definitions
    ) == (
        "AUD",
        "BIF",
        "USD",
    )


def test_register_requires_definition() -> None:
    with pytest.raises(
        TypeError,
        match="CurrencyDefinition",
    ):
        empty_registry().register(
            "AUD"  # type: ignore[arg-type]
        )


def test_register_rejects_duplicate_id() -> None:
    registry = populated_registry()

    duplicate = currency_definition(
        "EUR",
        definition_id="currency-AUD",
    )

    with pytest.raises(
        ValueError,
        match="definition id",
    ):
        registry.register(duplicate)


def test_register_rejects_duplicate_code() -> None:
    registry = populated_registry()

    duplicate = currency_definition(
        "AUD",
        definition_id="currency-AUD-2",
    )

    with pytest.raises(
        ValueError,
        match="currency code",
    ):
        registry.register(duplicate)


def test_register_rejects_duplicate_numeric_code() -> None:
    registry = populated_registry()

    duplicate = currency_definition(
        "EUR",
        numeric_code="036",
    )

    with pytest.raises(
        ValueError,
        match="numeric code",
    ):
        registry.register(duplicate)


def test_update_definition() -> None:
    registry = populated_registry()
    original = registry.require_by_code("AUD")

    renamed = original.update_name(
        "Australian Dollar Currency"
    )

    updated = registry.update_definition(
        renamed
    )

    assert registry.require_by_code(
        "AUD"
    ).name.value == "Australian Dollar"

    assert updated.require_by_code(
        "AUD"
    ).name.value == "Australian Dollar Currency"

    assert updated.version == registry.version + 1


def test_update_definition_can_apply_lifecycle_change() -> None:
    registry = populated_registry()
    original = registry.require_by_code("AUD")

    suspended = original.suspend(
        reason="temporary control",
    )

    updated = registry.update_definition(
        suspended
    )

    assert updated.require_by_code(
        "AUD"
    ).status is CurrencyStatus.SUSPENDED

    assert "AUD" not in {
        definition.code
        for definition in updated.active_definitions()
    }


def test_update_definition_rejects_unknown_id() -> None:
    registry = populated_registry()

    with pytest.raises(
        KeyError,
        match="unknown definition",
    ):
        registry.update_definition(
            currency_definition("EUR")
        )


def test_update_definition_preserves_currency_code() -> None:
    registry = populated_registry()
    original = registry.require_by_code("AUD")

    changed_currency = CurrencyDefinition(
        currency_definition_id=(
            original.currency_definition_id
        ),
        currency=Currency.of("USD"),
        name=original.name,
        symbol=original.symbol,
        currency_type=original.currency_type,
        status=original.status,
        minor_units=2,
        rounding_mode=original.rounding_mode,
        country_codes=original.country_codes,
        numeric_code="999",
        metadata=original.metadata,
        version=original.version + 1,
    )

    with pytest.raises(
        ValueError,
        match="preserve.*currency code",
    ):
        registry.update_definition(
            changed_currency
        )


def test_update_definition_rejects_no_op() -> None:
    registry = populated_registry()
    original = registry.require_by_code("AUD")

    with pytest.raises(
        ValueError,
        match="must change",
    ):
        registry.update_definition(original)


def test_update_definition_rejects_numeric_collision() -> None:
    registry = populated_registry()
    original = registry.require_by_code("AUD")

    conflicting = CurrencyDefinition(
        currency_definition_id=(
            original.currency_definition_id
        ),
        currency=original.currency,
        name=original.name,
        symbol=original.symbol,
        currency_type=original.currency_type,
        status=original.status,
        minor_units=original.minor_units,
        rounding_mode=original.rounding_mode,
        country_codes=original.country_codes,
        numeric_code="840",
        metadata=original.metadata,
        version=original.version + 1,
    )

    with pytest.raises(
        ValueError,
        match="duplicate.*numeric code",
    ):
        registry.update_definition(conflicting)


def test_update_registry_metadata() -> None:
    registry = populated_registry()

    updated = registry.update_metadata(
        {
            "scope": "global",
            "owner": "NovaPay Treasury",
        }
    )

    assert registry.metadata.values == {
        "scope": "global",
    }
    assert updated.metadata.values == {
        "owner": "NovaPay Treasury",
        "scope": "global",
    }
    assert updated.version == registry.version + 1


def test_update_registry_metadata_rejects_no_op() -> None:
    registry = populated_registry()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        registry.update_metadata(
            registry.metadata
        )


def test_update_registry_metadata_rejects_sensitive_data() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        populated_registry().update_metadata(
            {
                "access_token": "secret",
            }
        )


def test_registry_version_increments_once_per_change() -> None:
    original = empty_registry()
    with_aud = original.register(
        currency_definition("AUD")
    )
    renamed = with_aud.update_definition(
        with_aud.require_by_code(
            "AUD"
        ).update_name(
            "Australian Dollar Currency"
        )
    )
    metadata_updated = renamed.update_metadata(
        {
            "scope": "global",
            "owner": "NovaPay Treasury",
        }
    )

    assert original.version == 1
    assert with_aud.version == 2
    assert renamed.version == 3
    assert metadata_updated.version == 4


def test_registry_preserves_canonical_money_contract() -> None:
    definition = populated_registry().require_by_code(
        "BIF"
    )

    money = Money.of(
        "1234.5",
        definition.currency,
    )

    assert definition.minor_units == 0
    assert definition.rounding_mode is (
        CurrencyRoundingMode.HALF_EVEN
    )
    assert str(money.amount) == "1234"


def test_registry_canonical_dict() -> None:
    registry = populated_registry()

    payload = registry.canonical_dict()

    assert list(payload) == [
        "currency_registry_id",
        "definitions",
        "metadata",
        "version",
    ]
    assert payload["currency_registry_id"] == (
        "registry-global"
    )
    assert [
        definition["currency"]["code"]
        for definition in payload["definitions"]
    ] == [
        "AUD",
        "BIF",
        "CDF",
        "USD",
    ]
    assert payload["metadata"] == {
        "scope": "global",
    }
    assert payload["version"] == 1


def test_registry_canonical_dict_is_fresh() -> None:
    registry = populated_registry()

    first = registry.canonical_dict()
    second = registry.canonical_dict()

    assert first == second
    assert first is not second
    assert first["definitions"] is not second["definitions"]
    assert first["metadata"] is not second["metadata"]


def test_registry_contains_no_external_authority() -> None:
    registry = populated_registry()

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
        "balance",
        "postings",
        "settlement_id",
    ):
        assert not hasattr(registry, forbidden)


def test_registry_module_contract() -> None:
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
