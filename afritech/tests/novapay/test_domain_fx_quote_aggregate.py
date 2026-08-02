from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.fx import (
    CurrencyPair,
    ExchangeRate,
    ExchangeRateSource,
    ExchangeRateStatus,
    FXMetadata,
    FXQuote,
    FXQuoteId,
    FXQuoteStatus,
    FXValidityWindow,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)


NOW = datetime(
    2026,
    8,
    2,
    7,
    0,
    tzinfo=timezone.utc,
)
EXPIRES = NOW + timedelta(minutes=10)
LATER = NOW + timedelta(minutes=1)


def active_exchange_rate() -> ExchangeRate:
    return ExchangeRate.create(
        exchange_rate_id="exchange-rate-001",
        pair=CurrencyPair.of("AUD", "USD"),
        rate="0.66",
        spread="25",
        source=ExchangeRateSource.PROVIDER,
        status=ExchangeRateStatus.ACTIVE,
        provider="AfriPay FX",
        provider_reference="fxlock-001",
        validity=FXValidityWindow(
            valid_from=NOW,
            expires_at=EXPIRES,
        ),
        metadata={
            "corridor": "AU-US",
        },
        occurred_at=NOW,
    )


def source_money() -> Money:
    return Money.of(
        "100.00",
        Currency.of("AUD"),
    )


def offered_quote(
    **overrides: object,
) -> FXQuote:
    rate = active_exchange_rate()

    values: dict[str, object] = {
        "fx_quote_id": FXQuoteId("fx-quote-001"),
        "exchange_rate_id": rate.exchange_rate_id,
        "pair": rate.pair,
        "source_amount": source_money(),
        "destination_amount": Money.of(
            "66.16",
            Currency.of("USD"),
        ),
        "rate": rate.customer_rate,
        "spread": rate.spread,
        "status": FXQuoteStatus.OFFERED,
        "provider": rate.provider,
        "provider_reference": rate.provider_reference,
        "validity": rate.validity,
        "customer_id": "customer-001",
        "transaction_id": None,
        "metadata": FXMetadata(
            {
                "corridor": "AU-US",
            }
        ),
        "created_at": NOW,
        "updated_at": NOW,
        "version": 1,
    }
    values.update(overrides)

    return FXQuote(**values)  # type: ignore[arg-type]


def test_create_fx_quote_from_exchange_rate() -> None:
    quote = FXQuote.create(
        fx_quote_id=" fx-quote-001 ",
        exchange_rate=active_exchange_rate(),
        source_amount=source_money(),
        customer_id=" customer-001 ",
        metadata={
            " channel ": "mobile",
        },
        occurred_at=LATER,
    )

    assert quote.fx_quote_id == FXQuoteId("fx-quote-001")
    assert quote.exchange_rate_id.value == (
        "exchange-rate-001"
    )
    assert quote.pair.symbol == "AUD/USD"
    assert quote.source_amount.amount == Decimal("100.00")
    assert quote.source_amount.currency == Currency.of("AUD")
    assert quote.destination_amount.amount == Decimal(
        "66.16"
    )
    assert quote.destination_amount.currency == Currency.of(
        "USD"
    )
    assert quote.rate.rate == Decimal("0.661650")
    assert quote.spread.basis_points == Decimal("25")
    assert quote.status is FXQuoteStatus.OFFERED
    assert quote.customer_id == "customer-001"
    assert quote.transaction_id is None
    assert quote.metadata.values == {
        "channel": "mobile",
    }
    assert quote.created_at == LATER
    assert quote.updated_at == LATER
    assert quote.version == 1


def test_created_quote_destination_is_canonical_money() -> None:
    rate = active_exchange_rate()
    source = source_money()

    quote = FXQuote.create(
        fx_quote_id="fx-quote-canonical-money",
        exchange_rate=rate,
        source_amount=source,
        occurred_at=LATER,
    )

    raw_destination = (
        source.amount
        * rate.customer_rate.rate
    )
    canonical_destination = Money.of(
        raw_destination,
        rate.pair.quote_currency,
    )

    assert raw_destination == Decimal("66.16500000")
    assert canonical_destination.amount == Decimal("66.16")
    assert quote.destination_amount == canonical_destination
    assert quote.destination_amount.currency == Currency.of(
        "USD"
    )


def test_manual_quote_uses_canonical_destination_money() -> None:
    rate = active_exchange_rate()

    supplied_destination = Money(
        amount=Decimal("66.165000"),
        currency=Currency.of("USD"),
    )

    assert supplied_destination.amount == Decimal("66.16")

    quote = FXQuote(
        fx_quote_id="fx-quote-canonical-manual",
        exchange_rate_id=rate.exchange_rate_id,
        pair=rate.pair,
        source_amount=source_money(),
        destination_amount=supplied_destination,
        rate=rate.customer_rate,
        spread=rate.spread,
        status=FXQuoteStatus.OFFERED,
        provider=rate.provider,
        provider_reference=rate.provider_reference,
        validity=rate.validity,
        created_at=NOW,
        updated_at=NOW,
    )

    expected_destination = Money.of(
        quote.source_amount.amount * quote.rate.rate,
        quote.pair.quote_currency,
    )

    assert quote.destination_amount == expected_destination
    assert quote.destination_amount.amount == Decimal("66.16")
    assert quote.destination_amount.currency == Currency.of(
        "USD"
    )


def test_fx_quote_is_immutable() -> None:
    quote = offered_quote()

    with pytest.raises(FrozenInstanceError):
        quote.status = FXQuoteStatus.ACCEPTED  # type: ignore[misc]


def test_fx_quote_uses_slots() -> None:
    assert not hasattr(offered_quote(), "__dict__")


def test_fx_quote_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(FXQuote)
    } == {
        "fx_quote_id",
        "exchange_rate_id",
        "pair",
        "source_amount",
        "destination_amount",
        "rate",
        "spread",
        "status",
        "provider",
        "provider_reference",
        "validity",
        "customer_id",
        "transaction_id",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    }


def test_fx_quote_normalizes_pair_string() -> None:
    quote = offered_quote(pair="aud-usd")

    assert quote.pair == CurrencyPair.of("AUD", "USD")


def test_fx_quote_rejects_invalid_pair_type() -> None:
    with pytest.raises(
        TypeError,
        match="pair must be",
    ):
        offered_quote(
            pair={
                "base_currency": "AUD",
                "quote_currency": "USD",
            }
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "source_amount",
        "destination_amount",
    ],
)
def test_fx_quote_requires_money(
    field_name: str,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        offered_quote(
            **{field_name: "100.00"}
        )


def test_fx_quote_source_currency_must_match_pair() -> None:
    with pytest.raises(
        ValueError,
        match="source amount currency",
    ):
        offered_quote(
            source_amount=Money.of(
                "100.00",
                Currency.of("CDF"),
            )
        )


def test_fx_quote_destination_currency_must_match_pair() -> None:
    with pytest.raises(
        ValueError,
        match="destination amount currency",
    ):
        offered_quote(
            destination_amount=Money.of(
                "66.165000",
                Currency.of("CDF"),
            )
        )


def test_fx_quote_destination_amount_must_match_rate() -> None:
    with pytest.raises(
        ValueError,
        match="canonical Money result",
    ):
        offered_quote(
            destination_amount=Money.of(
                "65.00",
                Currency.of("USD"),
            )
        )


def test_fx_quote_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        offered_quote(
            metadata={
                "access_token": "secret",
            }
        )


def test_fx_quote_normalizes_references() -> None:
    quote = offered_quote(
        customer_id=" customer-001 ",
        transaction_id=" transaction-001 ",
    )

    assert quote.customer_id == "customer-001"
    assert quote.transaction_id == "transaction-001"


def test_fx_quote_allows_missing_optional_references() -> None:
    quote = offered_quote(
        customer_id=None,
        transaction_id=None,
    )

    assert quote.customer_id is None
    assert quote.transaction_id is None


def test_consumed_quote_requires_transaction_id() -> None:
    with pytest.raises(
        ValueError,
        match="requires transaction id",
    ):
        offered_quote(
            status=FXQuoteStatus.CONSUMED,
            transaction_id=None,
        )


def test_consumed_quote_accepts_transaction_id() -> None:
    quote = offered_quote(
        status=FXQuoteStatus.CONSUMED,
        transaction_id="transaction-001",
    )

    assert quote.status is FXQuoteStatus.CONSUMED
    assert quote.transaction_id == "transaction-001"
    assert quote.is_terminal is True


@pytest.mark.parametrize(
    "status",
    [
        FXQuoteStatus.CONSUMED,
        FXQuoteStatus.EXPIRED,
        FXQuoteStatus.CANCELLED,
        FXQuoteStatus.REJECTED,
    ],
)
def test_terminal_status_property(
    status: FXQuoteStatus,
) -> None:
    values: dict[str, object] = {
        "status": status,
    }

    if status is FXQuoteStatus.CONSUMED:
        values["transaction_id"] = "transaction-001"

    if status is FXQuoteStatus.EXPIRED:
        values["validity"] = FXValidityWindow(
            valid_from=NOW - timedelta(minutes=20),
            expires_at=NOW - timedelta(minutes=10),
        )

    quote = offered_quote(**values)

    assert quote.is_terminal is True


@pytest.mark.parametrize(
    "status",
    [
        FXQuoteStatus.PENDING,
        FXQuoteStatus.OFFERED,
        FXQuoteStatus.ACCEPTED,
    ],
)
def test_non_terminal_status_property(
    status: FXQuoteStatus,
) -> None:
    quote = offered_quote(status=status)

    assert quote.is_terminal is False


def test_offered_quote_requires_active_validity() -> None:
    expired = FXValidityWindow(
        valid_from=NOW - timedelta(minutes=20),
        expires_at=NOW - timedelta(minutes=10),
    )

    with pytest.raises(
        ValueError,
        match="must be valid",
    ):
        offered_quote(
            validity=expired,
        )


def test_expired_status_requires_expired_window() -> None:
    with pytest.raises(
        ValueError,
        match="must be expired",
    ):
        offered_quote(
            status=FXQuoteStatus.EXPIRED,
        )


def test_fx_quote_activity_boundary() -> None:
    quote = offered_quote()

    assert quote.is_active_at(NOW) is True
    assert quote.is_active_at(EXPIRES) is False


def test_fx_quote_expiry_boundary() -> None:
    quote = offered_quote()

    assert (
        quote.is_expired_at(
            EXPIRES - timedelta(microseconds=1)
        )
        is False
    )
    assert quote.is_expired_at(EXPIRES) is True


def test_quote_base_amount() -> None:
    quote = offered_quote()

    converted = quote.quote_base_amount("200.00")

    assert converted.amount == Decimal("132.33")
    assert converted.currency == Currency.of("USD")


def test_quote_destination_amount() -> None:
    quote = offered_quote()

    converted = quote.quote_destination_amount(
        "66.165000"
    )

    assert converted.amount == Decimal("100.00")
    assert converted.currency == Currency.of("AUD")


@pytest.mark.parametrize(
    "method_name",
    [
        "quote_base_amount",
        "quote_destination_amount",
    ],
)
def test_quote_amount_methods_reject_negative(
    method_name: str,
) -> None:
    method = getattr(offered_quote(), method_name)

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        method("-1")


def test_fx_quote_rejects_updated_before_created() -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        offered_quote(
            updated_at=NOW - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_fx_quote_rejects_invalid_version(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        offered_quote(version=version)


@pytest.mark.parametrize(
    "version",
    [
        True,
        "1",
        1.0,
        None,
    ],
)
def test_fx_quote_rejects_non_integer_version(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="version must be an integer",
    ):
        offered_quote(version=version)


def test_fx_quote_create_requires_exchange_rate() -> None:
    with pytest.raises(
        TypeError,
        match="must be an ExchangeRate",
    ):
        FXQuote.create(
            fx_quote_id="fx-quote-001",
            exchange_rate=object(),  # type: ignore[arg-type]
            source_amount=source_money(),
            occurred_at=LATER,
        )


def test_fx_quote_create_requires_active_rate() -> None:
    draft = ExchangeRate.create(
        exchange_rate_id="exchange-rate-draft",
        pair="AUD/USD",
        rate="0.66",
        source="provider",
        provider="AfriPay FX",
        provider_reference="fxlock-draft",
        validity=FXValidityWindow(
            valid_from=NOW,
            expires_at=EXPIRES,
        ),
        occurred_at=NOW,
    )

    with pytest.raises(
        ValueError,
        match="requires an active exchange rate",
    ):
        FXQuote.create(
            fx_quote_id="fx-quote-001",
            exchange_rate=draft,
            source_amount=source_money(),
            occurred_at=LATER,
        )


def test_fx_quote_create_rejects_wrong_source_currency() -> None:
    with pytest.raises(
        ValueError,
        match="source amount currency",
    ):
        FXQuote.create(
            fx_quote_id="fx-quote-001",
            exchange_rate=active_exchange_rate(),
            source_amount=Money.of(
                "100",
                Currency.of("CDF"),
            ),
            occurred_at=LATER,
        )


def test_fx_quote_canonical_dict() -> None:
    quote = offered_quote()

    payload = quote.canonical_dict()

    assert list(payload) == [
        "fx_quote_id",
        "exchange_rate_id",
        "pair",
        "source_amount",
        "destination_amount",
        "rate",
        "spread",
        "status",
        "provider",
        "provider_reference",
        "validity",
        "customer_id",
        "transaction_id",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]

    assert payload["fx_quote_id"] == "fx-quote-001"
    assert payload["exchange_rate_id"] == "exchange-rate-001"
    assert payload["pair"] == {
        "base_currency": "AUD",
        "quote_currency": "USD",
    }
    assert payload["source_amount"] == {
        "amount": "100.00",
        "currency": "AUD",
    }
    assert payload["destination_amount"] == {
        "amount": "66.16",
        "currency": "USD",
    }
    assert payload["rate"] == "0.661650"
    assert payload["spread"] == {
        "basis_points": "25",
    }
    assert payload["status"] == "offered"
    assert payload["version"] == 1


def test_fx_quote_canonical_dict_is_fresh() -> None:
    quote = offered_quote()

    first = quote.canonical_dict()
    second = quote.canonical_dict()

    assert first == second
    assert first is not second
    assert first["pair"] is not second["pair"]
    assert first["source_amount"] is not second[
        "source_amount"
    ]
    assert first["metadata"] is not second["metadata"]


def test_fx_quote_contains_no_runtime_authority() -> None:
    quote = offered_quote()

    for forbidden in (
        "wallet_id",
        "ledger_account_id",
        "journal_entry_id",
        "settlement_id",
        "balance",
        "postings",
        "provider_client",
        "fx_engine",
        "conversion_service",
    ):
        assert not hasattr(quote, forbidden)


def test_fx_quote_does_not_replace_afripay_conversion() -> None:
    from afritech.afripay.models import FXConversion

    assert FXQuote is not FXConversion


def test_fx_quote_module_contract() -> None:
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
