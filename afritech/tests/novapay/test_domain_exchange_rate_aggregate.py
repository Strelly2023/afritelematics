from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.fx import (
    CurrencyPair,
    ExchangeRate,
    ExchangeRateId,
    ExchangeRateSource,
    ExchangeRateStatus,
    ExchangeRateValue,
    FXMetadata,
    FXValidityWindow,
    RateSpread,
)


NOW = datetime(
    2026,
    8,
    2,
    5,
    0,
    tzinfo=timezone.utc,
)
EXPIRES = NOW + timedelta(minutes=10)


def validity() -> FXValidityWindow:
    return FXValidityWindow(
        valid_from=NOW,
        expires_at=EXPIRES,
    )


def draft_rate(
    **overrides: object,
) -> ExchangeRate:
    values: dict[str, object] = {
        "exchange_rate_id": ExchangeRateId(
            "exchange-rate-001"
        ),
        "pair": CurrencyPair.of("AUD", "USD"),
        "rate": ExchangeRateValue("0.66"),
        "spread": RateSpread("25"),
        "source": ExchangeRateSource.PROVIDER,
        "status": ExchangeRateStatus.DRAFT,
        "provider": "AfriPay FX",
        "provider_reference": "fxlock-001",
        "validity": validity(),
        "metadata": FXMetadata(
            {
                "corridor": "AU-US",
                "rate_type": "retail",
            }
        ),
        "created_at": NOW,
        "updated_at": NOW,
        "version": 1,
    }
    values.update(overrides)

    return ExchangeRate(**values)  # type: ignore[arg-type]


def test_create_exchange_rate() -> None:
    exchange_rate = ExchangeRate.create(
        exchange_rate_id=" exchange-rate-001 ",
        pair=" aud/usd ",
        rate="0.66",
        spread="25",
        source=" PROVIDER ",
        status=" DRAFT ",
        provider=" AfriPay   FX ",
        provider_reference=" fxlock-001 ",
        validity=validity(),
        metadata={
            " corridor ": "AU-US",
        },
        occurred_at=NOW,
    )

    assert exchange_rate.exchange_rate_id == (
        ExchangeRateId("exchange-rate-001")
    )
    assert exchange_rate.pair.symbol == "AUD/USD"
    assert exchange_rate.rate.rate == Decimal("0.66")
    assert exchange_rate.spread.basis_points == Decimal(
        "25"
    )
    assert exchange_rate.source is (
        ExchangeRateSource.PROVIDER
    )
    assert exchange_rate.status is (
        ExchangeRateStatus.DRAFT
    )
    assert exchange_rate.provider == "AfriPay FX"
    assert exchange_rate.provider_reference == "fxlock-001"
    assert exchange_rate.metadata.values == {
        "corridor": "AU-US",
    }
    assert exchange_rate.created_at == NOW
    assert exchange_rate.updated_at == NOW
    assert exchange_rate.version == 1


def test_exchange_rate_is_immutable() -> None:
    exchange_rate = draft_rate()

    with pytest.raises(FrozenInstanceError):
        exchange_rate.status = (  # type: ignore[misc]
            ExchangeRateStatus.ACTIVE
        )


def test_exchange_rate_uses_slots() -> None:
    assert not hasattr(draft_rate(), "__dict__")


@pytest.mark.parametrize(
    "field_name",
    [
        "exchange_rate_id",
        "pair",
        "rate",
        "spread",
        "source",
        "status",
        "provider",
        "provider_reference",
        "validity",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ],
)
def test_exchange_rate_declares_expected_fields(
    field_name: str,
) -> None:
    field_names = {
        item.name
        for item in fields(ExchangeRate)
    }

    assert field_name in field_names


def test_exchange_rate_field_contract_is_exact() -> None:
    assert {
        item.name
        for item in fields(ExchangeRate)
    } == {
        "exchange_rate_id",
        "pair",
        "rate",
        "spread",
        "source",
        "status",
        "provider",
        "provider_reference",
        "validity",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    }


def test_exchange_rate_normalizes_pair_string() -> None:
    exchange_rate = draft_rate(
        pair="aud-usd",
    )

    assert exchange_rate.pair == CurrencyPair.of(
        "AUD",
        "USD",
    )


def test_exchange_rate_rejects_invalid_pair_type() -> None:
    with pytest.raises(
        TypeError,
        match="pair must be",
    ):
        draft_rate(
            pair={
                "base_currency": "AUD",
                "quote_currency": "USD",
            },
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        (
            "rate",
            "0",
            "greater than zero",
        ),
        (
            "spread",
            "-1",
            "must not be negative",
        ),
        (
            "provider",
            " ",
            "must not be empty",
        ),
        (
            "provider_reference",
            " ",
            "must not be empty",
        ),
    ],
)
def test_exchange_rate_rejects_invalid_values(
    field_name: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        draft_rate(
            **{field_name: value}
        )


def test_exchange_rate_rejects_invalid_validity_type() -> None:
    with pytest.raises(
        TypeError,
        match="FXValidityWindow",
    ):
        draft_rate(
            validity={
                "valid_from": NOW,
                "expires_at": EXPIRES,
            },
        )


def test_exchange_rate_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        draft_rate(
            metadata={
                "access_token": "secret",
            }
        )


def test_exchange_rate_normalizes_metadata_mapping() -> None:
    exchange_rate = draft_rate(
        metadata={
            " corridor ": "AU-US",
        }
    )

    assert exchange_rate.metadata.values == {
        "corridor": "AU-US",
    }


def test_exchange_rate_normalizes_timezone() -> None:
    melbourne = timezone(timedelta(hours=10))
    local_time = datetime(
        2026,
        8,
        2,
        15,
        0,
        tzinfo=melbourne,
    )

    exchange_rate = draft_rate(
        created_at=local_time,
        updated_at=local_time,
    )

    assert exchange_rate.created_at == NOW
    assert exchange_rate.updated_at == NOW
    assert exchange_rate.created_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "updated_at",
    ],
)
def test_exchange_rate_rejects_naive_timestamp(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        draft_rate(
            **{
                field_name: datetime(
                    2026,
                    8,
                    2,
                    5,
                    0,
                )
            }
        )


def test_exchange_rate_rejects_updated_before_created() -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        draft_rate(
            updated_at=NOW - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_exchange_rate_rejects_invalid_version(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        draft_rate(version=version)


@pytest.mark.parametrize(
    "version",
    [
        True,
        "1",
        1.0,
        None,
    ],
)
def test_exchange_rate_rejects_non_integer_version(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="version must be an integer",
    ):
        draft_rate(version=version)


def test_active_exchange_rate_requires_current_validity() -> None:
    expired_window = FXValidityWindow(
        valid_from=NOW - timedelta(minutes=20),
        expires_at=NOW - timedelta(minutes=10),
    )

    with pytest.raises(
        ValueError,
        match="must be valid",
    ):
        draft_rate(
            status=ExchangeRateStatus.ACTIVE,
            validity=expired_window,
        )


def test_active_exchange_rate_accepts_active_window() -> None:
    exchange_rate = draft_rate(
        status=ExchangeRateStatus.ACTIVE,
    )

    assert exchange_rate.status is ExchangeRateStatus.ACTIVE
    assert exchange_rate.is_active_at(NOW) is True


def test_expired_status_requires_expired_window() -> None:
    with pytest.raises(
        ValueError,
        match="must be expired",
    ):
        draft_rate(
            status=ExchangeRateStatus.EXPIRED,
        )


def test_expired_status_accepts_expired_window() -> None:
    window = FXValidityWindow(
        valid_from=NOW - timedelta(minutes=20),
        expires_at=NOW - timedelta(minutes=10),
    )

    exchange_rate = draft_rate(
        status=ExchangeRateStatus.EXPIRED,
        validity=window,
    )

    assert exchange_rate.status is ExchangeRateStatus.EXPIRED
    assert exchange_rate.is_expired_at(NOW) is True


def test_draft_rate_is_not_active() -> None:
    exchange_rate = draft_rate()

    assert exchange_rate.is_active_at(NOW) is False


def test_validity_expiry_is_reported_for_draft() -> None:
    window = FXValidityWindow(
        valid_from=NOW - timedelta(minutes=20),
        expires_at=NOW - timedelta(minutes=10),
    )

    exchange_rate = draft_rate(
        validity=window,
    )

    assert exchange_rate.is_expired_at(NOW) is True


def test_customer_rate_applies_spread() -> None:
    exchange_rate = draft_rate(
        rate=ExchangeRateValue("1.00"),
        spread=RateSpread("100"),
    )

    assert exchange_rate.customer_rate.rate == Decimal(
        "1.0100"
    )


def test_zero_spread_preserves_rate() -> None:
    exchange_rate = draft_rate(
        spread=RateSpread("0"),
    )

    assert exchange_rate.customer_rate == exchange_rate.rate


def test_inverse_rate_uses_customer_rate() -> None:
    exchange_rate = draft_rate(
        rate=ExchangeRateValue("0.50"),
        spread=RateSpread("0"),
    )

    assert exchange_rate.inverse_rate.rate == Decimal(
        "2"
    )


def test_convert_base_amount() -> None:
    exchange_rate = draft_rate(
        rate=ExchangeRateValue("0.66"),
        spread=RateSpread("0"),
    )

    assert exchange_rate.convert_base_amount(
        "100.00"
    ) == Decimal("66.0000")


def test_convert_quote_amount() -> None:
    exchange_rate = draft_rate(
        rate=ExchangeRateValue("0.50"),
        spread=RateSpread("0"),
    )

    assert exchange_rate.convert_quote_amount(
        "50.00"
    ) == Decimal("100.0")


@pytest.mark.parametrize(
    "method_name",
    [
        "convert_base_amount",
        "convert_quote_amount",
    ],
)
def test_exchange_rate_conversion_rejects_negative(
    method_name: str,
) -> None:
    exchange_rate = draft_rate()
    method = getattr(exchange_rate, method_name)

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        method("-1")


def test_exchange_rate_canonical_dict() -> None:
    exchange_rate = draft_rate()

    payload = exchange_rate.canonical_dict()

    assert list(payload) == [
        "exchange_rate_id",
        "pair",
        "rate",
        "spread",
        "customer_rate",
        "inverse_rate",
        "source",
        "status",
        "provider",
        "provider_reference",
        "validity",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]

    assert payload["exchange_rate_id"] == (
        "exchange-rate-001"
    )
    assert payload["pair"] == {
        "base_currency": "AUD",
        "quote_currency": "USD",
    }
    assert payload["rate"] == "0.66"
    assert payload["spread"] == {
        "basis_points": "25",
    }
    assert payload["customer_rate"] == "0.661650"
    assert payload["source"] == "provider"
    assert payload["status"] == "draft"
    assert payload["provider"] == "AfriPay FX"
    assert payload["provider_reference"] == "fxlock-001"
    assert payload["version"] == 1


def test_exchange_rate_canonical_dict_is_fresh() -> None:
    exchange_rate = draft_rate()

    first = exchange_rate.canonical_dict()
    second = exchange_rate.canonical_dict()

    assert first == second
    assert first is not second
    assert first["pair"] is not second["pair"]
    assert first["spread"] is not second["spread"]
    assert first["metadata"] is not second["metadata"]


def test_exchange_rate_contains_no_runtime_authority() -> None:
    exchange_rate = draft_rate()

    for forbidden in (
        "wallet_id",
        "ledger_account_id",
        "transaction_id",
        "journal_entry_id",
        "settlement_id",
        "balance",
        "postings",
        "transactions",
        "provider_client",
        "fx_engine",
    ):
        assert not hasattr(exchange_rate, forbidden)


def test_exchange_rate_does_not_replace_afripay_rate() -> None:
    from afritech.afripay.models import FXRate

    assert ExchangeRate is not FXRate
    assert ExchangeRateValue is not FXRate


def test_exchange_rate_module_contract() -> None:
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
