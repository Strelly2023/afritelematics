from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from afritech.novapay import (
    Currency,
    DEFAULT_MINOR_UNITS,
    Money,
    freeze_money_payload,
)


def test_currency_normalizes_code() -> None:
    currency = Currency(" aud ")

    assert currency.code == "AUD"
    assert str(currency) == "AUD"
    assert currency.canonical() == "AUD"


@pytest.mark.parametrize(
    "value",
    (
        "",
        "AU",
        "AUSD",
        "12A",
        "A-D",
        "   ",
    ),
)
def test_currency_rejects_invalid_code(value: str) -> None:
    with pytest.raises(
        ValueError,
        match="exactly three alphabetic",
    ):
        Currency(value)


def test_currency_rejects_non_string_code() -> None:
    with pytest.raises(
        TypeError,
        match="currency code must be a string",
    ):
        Currency.of(123)


def test_currency_minor_units() -> None:
    assert Currency("AUD").minor_units == 2
    assert Currency("UGX").minor_units == 0
    assert Currency("BIF").minor_units == 0


def test_unknown_valid_currency_uses_default_minor_units() -> None:
    currency = Currency("XYZ")

    assert currency.minor_units == DEFAULT_MINOR_UNITS


def test_money_normalizes_amount_and_currency() -> None:
    money = Money.of("10", " aud ")

    assert money.amount == Decimal("10.00")
    assert money.currency == Currency("AUD")
    assert money.canonical_amount() == "10.00"
    assert money.canonical() == "AUD 10.00"


def test_zero_minor_unit_currency_quantization() -> None:
    assert Money.of("10.4", "UGX").amount == Decimal("10")
    assert Money.of("10.5", "UGX").amount == Decimal("10")
    assert Money.of("11.5", "UGX").amount == Decimal("12")


def test_money_uses_bankers_rounding() -> None:
    assert Money.of("1.005", "AUD").amount == Decimal("1.00")
    assert Money.of("1.015", "AUD").amount == Decimal("1.02")


@pytest.mark.parametrize(
    "value",
    (
        "NaN",
        "Infinity",
        "-Infinity",
    ),
)
def test_money_rejects_non_finite_amounts(value: str) -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        Money.of(value, "AUD")


def test_money_rejects_float_input() -> None:
    with pytest.raises(
        TypeError,
        match="floating-point monetary amounts",
    ):
        Money.of(10.25, "AUD")


def test_money_rejects_boolean_input() -> None:
    with pytest.raises(
        TypeError,
        match="cannot be a boolean",
    ):
        Money.of(True, "AUD")


def test_money_rejects_invalid_amount_string() -> None:
    with pytest.raises(
        ValueError,
        match="invalid monetary amount",
    ):
        Money.of("not-money", "AUD")


def test_money_rejects_empty_amount_string() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        Money.of("   ", "AUD")


def test_money_addition() -> None:
    result = Money.of("10.25", "AUD") + Money.of(
        "2.75",
        "AUD",
    )

    assert result == Money.of("13.00", "AUD")


def test_money_subtraction() -> None:
    result = Money.of("10.00", "AUD") - Money.of(
        "2.50",
        "AUD",
    )

    assert result == Money.of("7.50", "AUD")


def test_money_negation() -> None:
    assert -Money.of("10.00", "AUD") == Money.of(
        "-10.00",
        "AUD",
    )


def test_money_multiplication() -> None:
    assert Money.of("10.00", "AUD").multiply(
        "1.25"
    ) == Money.of("12.50", "AUD")


def test_money_rejects_float_multiplier() -> None:
    with pytest.raises(
        TypeError,
        match="floating-point monetary amounts",
    ):
        Money.of("10.00", "AUD").multiply(1.25)


@pytest.mark.parametrize(
    "operation",
    (
        lambda left, right: left + right,
        lambda left, right: left - right,
        lambda left, right: left.compare(right),
    ),
)
def test_money_operations_reject_currency_mismatch(
    operation,
) -> None:
    with pytest.raises(
        ValueError,
        match="matching currencies",
    ):
        operation(
            Money.of("10.00", "AUD"),
            Money.of("10.00", "USD"),
        )


def test_money_operations_reject_non_money_values() -> None:
    with pytest.raises(
        TypeError,
        match="requires another Money",
    ):
        Money.of("10.00", "AUD") + Decimal("1.00")


def test_money_comparison() -> None:
    lower = Money.of("9.99", "AUD")
    equal = Money.of("10.00", "AUD")
    higher = Money.of("10.01", "AUD")

    assert equal.compare(lower) == 1
    assert equal.compare(equal) == 0
    assert equal.compare(higher) == -1


def test_money_sign_properties() -> None:
    assert Money.zero("AUD").is_zero is True
    assert Money.of("1.00", "AUD").is_positive is True
    assert Money.of("-1.00", "AUD").is_negative is True


def test_require_non_negative() -> None:
    assert Money.zero("AUD").require_non_negative() == Money.zero(
        "AUD"
    )

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        Money.of("-0.01", "AUD").require_non_negative()


def test_require_positive() -> None:
    assert Money.of("0.01", "AUD").require_positive() == Money.of(
        "0.01",
        "AUD",
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        Money.zero("AUD").require_positive()


def test_money_is_immutable() -> None:
    money = Money.of("10.00", "AUD")

    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal("20.00")  # type: ignore[misc]


def test_currency_is_immutable() -> None:
    currency = Currency("AUD")

    with pytest.raises(FrozenInstanceError):
        currency.code = "USD"  # type: ignore[misc]


def test_canonical_dictionary_is_immutable() -> None:
    payload = Money.of(
        "10.00",
        "AUD",
    ).canonical_dict()

    assert payload == {
        "amount": "10.00",
        "currency": "AUD",
    }

    with pytest.raises(TypeError):
        payload["amount"] = "20.00"  # type: ignore[index]


def test_currency_dictionary_is_immutable() -> None:
    payload = Currency("AUD").canonical_dict()

    assert payload == {
        "code": "AUD",
        "minor_units": 2,
    }

    with pytest.raises(TypeError):
        payload["code"] = "USD"  # type: ignore[index]


def test_freeze_money_payload_defensively_copies_input() -> None:
    source = {
        "reference": "payment-1",
        "channel": "wallet",
    }

    frozen = freeze_money_payload(source)
    source["reference"] = "changed"

    assert frozen["reference"] == "payment-1"

    with pytest.raises(TypeError):
        frozen["reference"] = "other"  # type: ignore[index]


def test_freeze_money_payload_requires_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        freeze_money_payload(["invalid"])  # type: ignore[arg-type]


def test_top_level_novapay_exports_are_available() -> None:
    from afritech import novapay

    assert novapay.Currency is Currency
    assert novapay.Money is Money
    assert "Currency" in novapay.__all__
    assert "Money" in novapay.__all__
