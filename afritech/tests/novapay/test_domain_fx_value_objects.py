from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain.fx import (
    CurrencyPair,
    ExchangeRateValue,
    FXMetadata,
    FXValidityWindow,
    RateSpread,
)
from afritech.novapay.domain.money import Currency


NOW = datetime(
    2026,
    8,
    2,
    4,
    0,
    tzinfo=timezone.utc,
)
LATER = NOW + timedelta(minutes=5)


def test_currency_pair_accepts_currency_objects() -> None:
    pair = CurrencyPair(
        Currency.of("AUD"),
        Currency.of("USD"),
    )

    assert pair.base_currency == Currency.of("AUD")
    assert pair.quote_currency == Currency.of("USD")
    assert pair.symbol == "AUD/USD"
    assert str(pair) == "AUD/USD"


def test_currency_pair_of_normalizes_codes() -> None:
    pair = CurrencyPair.of(
        " aud ",
        " usd ",
    )

    assert pair.base_currency.code == "AUD"
    assert pair.quote_currency.code == "USD"


@pytest.mark.parametrize(
    "value",
    [
        "AUD/USD",
        " aud/usd ",
        "AUD-USD",
        " aud-usd ",
    ],
)
def test_currency_pair_parse(
    value: str,
) -> None:
    pair = CurrencyPair.parse(value)

    assert pair.symbol == "AUD/USD"


def test_currency_pair_parse_returns_existing() -> None:
    pair = CurrencyPair.of("AUD", "USD")

    assert CurrencyPair.parse(pair) is pair


@pytest.mark.parametrize(
    "value",
    [
        "AUDUSD",
        "AUD/",
        "/USD",
        "AUD/USD/CDF",
        "",
    ],
)
def test_currency_pair_rejects_invalid_string(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        CurrencyPair.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_currency_pair_parse_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        CurrencyPair.parse(value)


def test_currency_pair_rejects_same_currency() -> None:
    with pytest.raises(
        ValueError,
        match="must be distinct",
    ):
        CurrencyPair.of("AUD", "AUD")


def test_currency_pair_requires_currency_instances() -> None:
    with pytest.raises(
        TypeError,
        match="base currency must be a Currency",
    ):
        CurrencyPair(
            "AUD",  # type: ignore[arg-type]
            Currency.of("USD"),
        )


def test_currency_pair_inverse() -> None:
    pair = CurrencyPair.of("AUD", "USD")

    inverse = pair.inverse()

    assert inverse.symbol == "USD/AUD"
    assert inverse.inverse() == pair


def test_currency_pair_canonical_dict() -> None:
    pair = CurrencyPair.of("AUD", "USD")

    assert pair.canonical_dict() == {
        "base_currency": "AUD",
        "quote_currency": "USD",
    }


def test_currency_pair_is_immutable() -> None:
    pair = CurrencyPair.of("AUD", "USD")

    with pytest.raises(FrozenInstanceError):
        pair.base_currency = Currency.of(  # type: ignore[misc]
            "CDF"
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0.66", Decimal("0.66")),
        (1, Decimal("1")),
        (1.25, Decimal("1.25")),
        (Decimal("1900.00"), Decimal("1900.00")),
    ],
)
def test_exchange_rate_value_normalizes(
    value: object,
    expected: Decimal,
) -> None:
    rate = ExchangeRateValue.of(value)

    assert rate.rate == expected


def test_exchange_rate_value_of_returns_existing() -> None:
    rate = ExchangeRateValue("0.66")

    assert ExchangeRateValue.of(rate) is rate


@pytest.mark.parametrize(
    "value",
    [
        "0",
        0,
        Decimal("0"),
        "-0.01",
        -1,
    ],
)
def test_exchange_rate_value_rejects_non_positive(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        ExchangeRateValue.of(value)


@pytest.mark.parametrize(
    "value",
    [
        "NaN",
        "Infinity",
        "-Infinity",
    ],
)
def test_exchange_rate_value_rejects_non_finite(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        ExchangeRateValue.of(value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        object(),
        "not-a-rate",
        None,
    ],
)
def test_exchange_rate_value_rejects_non_numeric(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        ExchangeRateValue.of(value)


def test_exchange_rate_value_inverse() -> None:
    rate = ExchangeRateValue("0.50")

    inverse = rate.inverse()

    assert inverse.rate == Decimal("2")


def test_exchange_rate_value_apply() -> None:
    rate = ExchangeRateValue("0.66")

    assert rate.apply("100.00") == Decimal("66.0000")


def test_exchange_rate_value_apply_zero() -> None:
    rate = ExchangeRateValue("0.66")

    assert rate.apply(0) == Decimal("0.00")


def test_exchange_rate_value_apply_rejects_negative() -> None:
    rate = ExchangeRateValue("0.66")

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        rate.apply("-1")


def test_exchange_rate_value_serialization() -> None:
    rate = ExchangeRateValue("1900.00")

    assert rate.canonical() == "1900.00"
    assert str(rate) == "1900.00"
    assert rate.canonical_dict() == {
        "rate": "1900.00",
    }


def test_exchange_rate_value_is_immutable() -> None:
    rate = ExchangeRateValue("0.66")

    with pytest.raises(FrozenInstanceError):
        rate.rate = Decimal("1")  # type: ignore[misc]


def test_rate_spread_defaults_zero() -> None:
    spread = RateSpread()

    assert spread.basis_points == Decimal("0")
    assert spread.fraction == Decimal("0")
    assert spread.percentage == Decimal("0")


@pytest.mark.parametrize(
    ("value", "basis_points", "fraction", "percentage"),
    [
        (
            "25",
            Decimal("25"),
            Decimal("0.0025"),
            Decimal("0.25"),
        ),
        (
            "100",
            Decimal("100"),
            Decimal("0.01"),
            Decimal("1"),
        ),
        (
            Decimal("12.5"),
            Decimal("12.5"),
            Decimal("0.00125"),
            Decimal("0.125"),
        ),
    ],
)
def test_rate_spread_normalizes(
    value: object,
    basis_points: Decimal,
    fraction: Decimal,
    percentage: Decimal,
) -> None:
    spread = RateSpread.of(value)

    assert spread.basis_points == basis_points
    assert spread.fraction == fraction
    assert spread.percentage == percentage


def test_rate_spread_of_returns_existing() -> None:
    spread = RateSpread("25")

    assert RateSpread.of(spread) is spread


def test_rate_spread_rejects_negative() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        RateSpread("-0.01")


def test_rate_spread_rejects_over_10000() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 10000",
    ):
        RateSpread("10000.01")


def test_rate_spread_add_to_rate() -> None:
    rate = ExchangeRateValue("1.00")
    spread = RateSpread("100")

    result = spread.add_to(rate)

    assert result.rate == Decimal("1.0100")


def test_rate_spread_subtract_from_rate() -> None:
    rate = ExchangeRateValue("1.00")
    spread = RateSpread("100")

    result = spread.subtract_from(rate)

    assert result.rate == Decimal("0.9900")


def test_rate_spread_requires_rate_value_object() -> None:
    with pytest.raises(
        TypeError,
        match="requires an ExchangeRateValue",
    ):
        RateSpread("10").add_to(
            Decimal("1")  # type: ignore[arg-type]
        )


def test_rate_spread_rejects_non_positive_discount_result() -> None:
    with pytest.raises(
        ValueError,
        match="non-positive rate",
    ):
        RateSpread("10000").subtract_from(
            ExchangeRateValue("1")
        )


def test_rate_spread_canonical_dict() -> None:
    spread = RateSpread("25.5")

    assert spread.canonical_dict() == {
        "basis_points": "25.5",
    }


def test_fx_validity_window_normalizes_timezone() -> None:
    melbourne = timezone(timedelta(hours=10))
    local_start = datetime(
        2026,
        8,
        2,
        14,
        0,
        tzinfo=melbourne,
    )
    local_end = local_start + timedelta(minutes=5)

    window = FXValidityWindow(
        local_start,
        local_end,
    )

    assert window.valid_from == NOW
    assert window.expires_at == LATER
    assert window.valid_from.tzinfo is timezone.utc
    assert window.expires_at.tzinfo is timezone.utc


def test_fx_validity_window_rejects_equal_times() -> None:
    with pytest.raises(
        ValueError,
        match="must be later",
    ):
        FXValidityWindow(NOW, NOW)


def test_fx_validity_window_rejects_reverse_times() -> None:
    with pytest.raises(
        ValueError,
        match="must be later",
    ):
        FXValidityWindow(
            NOW,
            NOW - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "valid_from",
        "expires_at",
    ],
)
def test_fx_validity_window_rejects_naive_time(
    field_name: str,
) -> None:
    values = {
        "valid_from": NOW,
        "expires_at": LATER,
    }
    values[field_name] = datetime(2026, 8, 2, 4, 0)

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        FXValidityWindow(**values)


def test_fx_validity_window_activity_boundary() -> None:
    window = FXValidityWindow(NOW, LATER)

    assert window.is_active_at(NOW) is True
    assert (
        window.is_active_at(
            LATER - timedelta(microseconds=1)
        )
        is True
    )
    assert window.is_active_at(LATER) is False


def test_fx_validity_window_expiry_boundary() -> None:
    window = FXValidityWindow(NOW, LATER)

    assert (
        window.is_expired_at(
            LATER - timedelta(microseconds=1)
        )
        is False
    )
    assert window.is_expired_at(LATER) is True


def test_fx_validity_window_duration() -> None:
    window = FXValidityWindow(NOW, LATER)

    assert window.duration_seconds == Decimal("300.0")


def test_fx_validity_window_canonical_dict() -> None:
    window = FXValidityWindow(NOW, LATER)

    assert window.canonical_dict() == {
        "valid_from": NOW.isoformat(),
        "expires_at": LATER.isoformat(),
    }


def test_fx_metadata_defaults_empty() -> None:
    metadata = FXMetadata()

    assert metadata.values == {}
    assert isinstance(metadata.values, MappingProxyType)


def test_fx_metadata_normalizes_keys() -> None:
    metadata = FXMetadata(
        {
            " provider_reference ": "provider-001",
            "corridor": "AU-US",
        }
    )

    assert metadata.values == {
        "provider_reference": "provider-001",
        "corridor": "AU-US",
    }


def test_fx_metadata_of_returns_existing() -> None:
    metadata = FXMetadata(
        {"provider": "afripay"}
    )

    assert FXMetadata.of(metadata) is metadata


def test_fx_metadata_defensive_copy() -> None:
    source = {
        "routing": {
            "provider": "afripay",
        }
    }

    metadata = FXMetadata(source)

    source["routing"]["provider"] = "changed"

    assert metadata.values["routing"] == {
        "provider": "afripay",
    }


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
        "credential_payload",
        "document_image",
        "identity_document",
    ],
)
def test_fx_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        FXMetadata(
            {key: "sensitive"}
        )


def test_fx_metadata_sensitive_check_is_case_insensitive() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        FXMetadata(
            {"Access_Token": "sensitive"}
        )


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
        ["provider"],
    ],
)
def test_fx_metadata_rejects_non_mapping(
    value: object,
) -> None:
    if value is None:
        assert FXMetadata.of(value).values == {}
        return

    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        FXMetadata.of(value)


def test_fx_metadata_rejects_non_string_key() -> None:
    with pytest.raises(
        TypeError,
        match="keys must be strings",
    ):
        FXMetadata(
            {1: "provider"}  # type: ignore[dict-item]
        )


def test_fx_metadata_with_value_is_immutable() -> None:
    original = FXMetadata(
        {"provider": "afripay"}
    )

    updated = original.with_value(
        "corridor",
        "AU-US",
    )

    assert original.values == {
        "provider": "afripay",
    }
    assert updated.values == {
        "provider": "afripay",
        "corridor": "AU-US",
    }


def test_fx_metadata_with_value_revalidates_sensitive_key() -> None:
    metadata = FXMetadata(
        {"provider": "afripay"}
    )

    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        metadata.with_value(
            "access_token",
            "secret",
        )


def test_fx_metadata_without_is_immutable() -> None:
    original = FXMetadata(
        {
            "provider": "afripay",
            "corridor": "AU-US",
        }
    )

    updated = original.without("corridor")

    assert "corridor" in original.values
    assert "corridor" not in updated.values


def test_fx_metadata_canonical_dict_is_immutable() -> None:
    metadata = FXMetadata(
        {"provider": "afripay"}
    )

    payload = metadata.canonical_dict()

    assert isinstance(payload, MappingProxyType)

    with pytest.raises(TypeError):
        payload["provider"] = "changed"  # type: ignore[index]


def test_fx_value_objects_are_slotted() -> None:
    values = (
        CurrencyPair.of("AUD", "USD"),
        ExchangeRateValue("0.66"),
        RateSpread("25"),
        FXValidityWindow(NOW, LATER),
        FXMetadata(),
    )

    for value in values:
        assert not hasattr(value, "__dict__")


def test_fx_module_public_contract() -> None:
    from afritech.novapay.domain import fx

    assert fx.__all__ == [
        "CurrencyPair",
        "ExchangeRate",
        "ExchangeRateId",
        "ExchangeRateSource",
        "ExchangeRateStatus",
        "ExchangeRateValue",
        "FXMetadata",
        "FXQuote",
        "FXQuoteId",
        "FXQuoteStatus",
        "FXValidityWindow",
        "RateSpread",
    ]
