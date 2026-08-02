from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from afritech.novapay.domain.currency import (
    CurrencyCountryCodes,
    CurrencyDefinition,
    CurrencyMetadata,
    CurrencyName,
    CurrencyRoundingMode,
    CurrencyStatus,
    CurrencySymbol,
    CurrencyType,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)


def draft_definition() -> CurrencyDefinition:
    return CurrencyDefinition.create(
        currency_definition_id="currency-AUD",
        currency="AUD",
        name="Australian Dollar",
        symbol="$",
        currency_type=CurrencyType.FIAT,
        status=CurrencyStatus.DRAFT,
        country_codes=["AU"],
        numeric_code="036",
        metadata={
            "issuer": "Reserve Bank of Australia",
        },
    )


def active_definition() -> CurrencyDefinition:
    return draft_definition().activate(
        reason="approved",
    )


def suspended_definition() -> CurrencyDefinition:
    return active_definition().suspend(
        reason="temporary restriction",
    )


def assert_core_contract_preserved(
    before: CurrencyDefinition,
    after: CurrencyDefinition,
) -> None:
    assert (
        after.currency_definition_id
        == before.currency_definition_id
    )
    assert after.currency == before.currency
    assert after.currency_type is before.currency_type
    assert after.minor_units == before.minor_units
    assert after.rounding_mode is before.rounding_mode
    assert after.numeric_code == before.numeric_code
    assert after.fund_code == before.fund_code


def assert_new_version(
    before: CurrencyDefinition,
    after: CurrencyDefinition,
) -> None:
    assert after is not before
    assert after.version == before.version + 1
    assert_core_contract_preserved(before, after)


def test_activate_draft_definition() -> None:
    original = draft_definition()

    active = original.activate(
        reason="treasury approval",
    )

    assert original.status is CurrencyStatus.DRAFT
    assert active.status is CurrencyStatus.ACTIVE
    assert active.metadata.values[
        "lifecycle_action"
    ] == "activate"
    assert active.metadata.values[
        "lifecycle_reason"
    ] == "treasury approval"
    assert_new_version(original, active)


def test_activate_requires_draft_status() -> None:
    with pytest.raises(
        ValueError,
        match="requires draft status",
    ):
        active_definition().activate()


def test_suspend_active_definition() -> None:
    original = active_definition()

    suspended = original.suspend(
        reason="regulatory restriction",
    )

    assert suspended.status is CurrencyStatus.SUSPENDED
    assert suspended.metadata.values[
        "lifecycle_action"
    ] == "suspend"
    assert_new_version(original, suspended)


def test_suspend_requires_active_status() -> None:
    with pytest.raises(
        ValueError,
        match="requires active status",
    ):
        draft_definition().suspend(
            reason="invalid",
        )


def test_suspend_requires_non_empty_reason() -> None:
    with pytest.raises(
        ValueError,
        match="reason must not be empty",
    ):
        active_definition().suspend(
            reason=" ",
        )


def test_reactivate_suspended_definition() -> None:
    original = suspended_definition()

    active = original.reactivate(
        reason="restriction removed",
    )

    assert active.status is CurrencyStatus.ACTIVE
    assert active.metadata.values[
        "lifecycle_action"
    ] == "reactivate"
    assert_new_version(original, active)


def test_reactivate_requires_suspended_status() -> None:
    with pytest.raises(
        ValueError,
        match="requires suspended status",
    ):
        active_definition().reactivate()


@pytest.mark.parametrize(
    "factory",
    [
        draft_definition,
        active_definition,
        suspended_definition,
    ],
)
def test_retire_non_terminal_definition(
    factory: object,
) -> None:
    original = factory()  # type: ignore[operator]

    retired = original.retire(
        reason="currency withdrawn",
    )

    assert retired.status is CurrencyStatus.RETIRED
    assert retired.metadata.values[
        "lifecycle_action"
    ] == "retire"
    assert retired.metadata.values[
        "lifecycle_reason"
    ] == "currency withdrawn"
    assert_new_version(original, retired)


def test_retire_requires_non_empty_reason() -> None:
    with pytest.raises(
        ValueError,
        match="reason must not be empty",
    ):
        active_definition().retire(
            reason=" ",
        )


def test_retired_definition_is_terminal() -> None:
    retired = active_definition().retire(
        reason="withdrawn",
    )

    operations = (
        lambda: retired.activate(),
        lambda: retired.suspend(
            reason="again",
        ),
        lambda: retired.reactivate(),
        lambda: retired.retire(
            reason="again",
        ),
        lambda: retired.update_name(
            "Changed name"
        ),
        lambda: retired.update_symbol(
            "A$"
        ),
        lambda: retired.update_country_codes(
            ["AU", "NZ"]
        ),
        lambda: retired.update_metadata(
            {"issuer": "changed"}
        ),
    )

    for operation in operations:
        with pytest.raises(
            ValueError,
            match="retired currency definition",
        ):
            operation()


def test_update_name() -> None:
    original = active_definition()

    updated = original.update_name(
        " Australian   Dollar Currency "
    )

    assert original.name == CurrencyName(
        "Australian Dollar"
    )
    assert updated.name == CurrencyName(
        "Australian Dollar Currency"
    )
    assert_new_version(original, updated)


def test_update_name_rejects_no_op() -> None:
    definition = active_definition()

    with pytest.raises(
        ValueError,
        match="must change name",
    ):
        definition.update_name(
            definition.name
        )


def test_update_symbol() -> None:
    original = active_definition()

    updated = original.update_symbol(
        "A$"
    )

    assert original.symbol == CurrencySymbol("$")
    assert updated.symbol == CurrencySymbol("A$")
    assert_new_version(original, updated)


def test_update_symbol_rejects_no_op() -> None:
    definition = active_definition()

    with pytest.raises(
        ValueError,
        match="must change symbol",
    ):
        definition.update_symbol(
            definition.symbol
        )


def test_update_country_codes() -> None:
    original = active_definition()

    updated = original.update_country_codes(
        ["nz", "AU", "NZ"]
    )

    assert original.country_codes == (
        CurrencyCountryCodes(("AU",))
    )
    assert updated.country_codes.values == (
        "AU",
        "NZ",
    )
    assert updated.supports_country("NZ") is True
    assert_new_version(original, updated)


def test_update_country_codes_rejects_no_op() -> None:
    definition = active_definition()

    with pytest.raises(
        ValueError,
        match="must change country codes",
    ):
        definition.update_country_codes(
            ["AU"]
        )


def test_update_metadata() -> None:
    original = active_definition()

    updated = original.update_metadata(
        {
            "issuer": "Reserve Bank of Australia",
            "region": "Oceania",
        }
    )

    assert updated.metadata.values == {
        "issuer": "Reserve Bank of Australia",
        "region": "Oceania",
    }
    assert_new_version(original, updated)


def test_update_metadata_rejects_sensitive_key() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        active_definition().update_metadata(
            {
                "access_token": "secret",
            }
        )


def test_update_metadata_rejects_no_op() -> None:
    definition = active_definition()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        definition.update_metadata(
            definition.metadata
        )


def test_each_change_increments_once() -> None:
    original = draft_definition()

    active = original.activate()
    renamed = active.update_name(
        "Australian Dollar Currency"
    )
    resymbolled = renamed.update_symbol(
        "A$"
    )
    suspended = resymbolled.suspend(
        reason="temporary restriction",
    )
    reactivated = suspended.reactivate()

    assert original.version == 1
    assert active.version == 2
    assert renamed.version == 3
    assert resymbolled.version == 4
    assert suspended.version == 5
    assert reactivated.version == 6


def test_original_definition_remains_unchanged() -> None:
    original = draft_definition()
    active = original.activate()

    assert original.status is CurrencyStatus.DRAFT
    assert original.version == 1
    assert active.status is CurrencyStatus.ACTIVE
    assert active.version == 2


def test_definition_remains_immutable() -> None:
    definition = active_definition()

    with pytest.raises(FrozenInstanceError):
        definition.version = 99  # type: ignore[misc]


def test_locked_currency_contract_never_changes() -> None:
    original = draft_definition()

    changed = (
        original.activate()
        .update_name("Australian Dollar Currency")
        .update_symbol("A$")
        .update_country_codes(["AU", "NZ"])
        .update_metadata(
            {
                "issuer": "RBA",
            }
        )
    )

    assert changed.currency == original.currency
    assert changed.code == original.code
    assert changed.minor_units == original.minor_units
    assert (
        changed.rounding_mode
        is original.rounding_mode
    )
    assert changed.currency_type is original.currency_type
    assert changed.numeric_code == original.numeric_code


def test_money_precision_remains_canonical() -> None:
    definition = (
        draft_definition()
        .activate()
        .update_name("Australian Dollar Currency")
    )

    money = Money.of(
        "66.165",
        definition.currency,
    )

    assert definition.currency == Currency.of("AUD")
    assert definition.minor_units == 2
    assert definition.rounding_mode is (
        CurrencyRoundingMode.HALF_EVEN
    )
    assert str(money.amount) == "66.16"


def test_serialization_reflects_lifecycle() -> None:
    active = draft_definition().activate(
        reason="approved",
    )

    payload = active.canonical_dict()

    assert payload["status"] == "active"
    assert payload["version"] == 2
    assert payload["metadata"][
        "lifecycle_action"
    ] == "activate"
    assert payload["metadata"][
        "lifecycle_reason"
    ] == "approved"


def test_lifecycle_methods_are_available() -> None:
    methods = (
        "activate",
        "suspend",
        "reactivate",
        "retire",
        "update_name",
        "update_symbol",
        "update_country_codes",
        "update_metadata",
    )

    for method in methods:
        assert callable(
            getattr(CurrencyDefinition, method)
        )
