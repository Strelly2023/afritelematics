from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay.domain.fx import (
    CurrencyPair,
    ExchangeRate,
    ExchangeRateSource,
    ExchangeRateStatus,
    FXQuote,
    FXQuoteStatus,
    FXValidityWindow,
)
from afritech.novapay.domain.money import Currency, Money


NOW = datetime(
    2026,
    8,
    2,
    8,
    0,
    tzinfo=timezone.utc,
)
OFFERED_AT = NOW + timedelta(minutes=1)
ACCEPTED_AT = NOW + timedelta(minutes=2)
CONSUMED_AT = NOW + timedelta(minutes=3)
EXPIRES = NOW + timedelta(minutes=10)
AFTER_EXPIRY = EXPIRES + timedelta(seconds=1)


def active_rate() -> ExchangeRate:
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
        occurred_at=NOW,
    )


def pending_quote() -> FXQuote:
    return FXQuote.create(
        fx_quote_id="fx-quote-001",
        exchange_rate=active_rate(),
        source_amount=Money.of(
            "100.00",
            Currency.of("AUD"),
        ),
        status=FXQuoteStatus.PENDING,
        customer_id="customer-001",
        metadata={"channel": "mobile"},
        occurred_at=NOW,
    )


def offered_quote() -> FXQuote:
    return pending_quote().offer(
        reason="quote ready",
        occurred_at=OFFERED_AT,
    )


def accepted_quote() -> FXQuote:
    return offered_quote().accept(
        reason="customer accepted",
        occurred_at=ACCEPTED_AT,
    )


def assert_identity_preserved(
    before: FXQuote,
    after: FXQuote,
) -> None:
    assert after.fx_quote_id == before.fx_quote_id
    assert after.exchange_rate_id == before.exchange_rate_id
    assert after.pair == before.pair
    assert after.source_amount == before.source_amount
    assert after.destination_amount == before.destination_amount
    assert after.rate == before.rate
    assert after.spread == before.spread
    assert after.provider == before.provider
    assert (
        after.provider_reference
        == before.provider_reference
    )
    assert after.validity == before.validity
    assert after.created_at == before.created_at


def assert_new_version(
    before: FXQuote,
    after: FXQuote,
    *,
    occurred_at: datetime,
) -> None:
    assert after is not before
    assert after.version == before.version + 1
    assert after.updated_at == occurred_at
    assert_identity_preserved(before, after)


def test_offer_pending_quote() -> None:
    quote = pending_quote()

    offered = quote.offer(
        reason="ready",
        occurred_at=OFFERED_AT,
    )

    assert quote.status is FXQuoteStatus.PENDING
    assert offered.status is FXQuoteStatus.OFFERED
    assert offered.metadata.values[
        "lifecycle_action"
    ] == "offer"
    assert offered.metadata.values[
        "lifecycle_reason"
    ] == "ready"
    assert_new_version(
        quote,
        offered,
        occurred_at=OFFERED_AT,
    )


def test_offer_requires_pending_status() -> None:
    with pytest.raises(
        ValueError,
        match="requires pending status",
    ):
        offered_quote().offer(
            occurred_at=ACCEPTED_AT,
        )


def test_offer_requires_active_validity() -> None:
    with pytest.raises(
        ValueError,
        match="active validity window",
    ):
        pending_quote().offer(
            occurred_at=AFTER_EXPIRY,
        )


def test_accept_offered_quote() -> None:
    quote = offered_quote()

    accepted = quote.accept(
        reason="approved",
        occurred_at=ACCEPTED_AT,
    )

    assert accepted.status is FXQuoteStatus.ACCEPTED
    assert accepted.metadata.values[
        "lifecycle_action"
    ] == "accept"
    assert_new_version(
        quote,
        accepted,
        occurred_at=ACCEPTED_AT,
    )


def test_accept_requires_offered_status() -> None:
    with pytest.raises(
        ValueError,
        match="requires offered status",
    ):
        pending_quote().accept(
            occurred_at=OFFERED_AT,
        )


def test_accept_requires_active_validity() -> None:
    with pytest.raises(
        ValueError,
        match="active validity window",
    ):
        offered_quote().accept(
            occurred_at=AFTER_EXPIRY,
        )


def test_consume_accepted_quote() -> None:
    quote = accepted_quote()

    consumed = quote.consume(
        transaction_id=" transaction-001 ",
        reason="payment initiated",
        occurred_at=CONSUMED_AT,
    )

    assert consumed.status is FXQuoteStatus.CONSUMED
    assert consumed.transaction_id == "transaction-001"
    assert consumed.is_terminal is True
    assert consumed.metadata.values[
        "lifecycle_action"
    ] == "consume"
    assert_new_version(
        quote,
        consumed,
        occurred_at=CONSUMED_AT,
    )


def test_consume_requires_accepted_status() -> None:
    with pytest.raises(
        ValueError,
        match="requires accepted status",
    ):
        offered_quote().consume(
            transaction_id="transaction-001",
            occurred_at=ACCEPTED_AT,
        )


@pytest.mark.parametrize(
    "transaction_id",
    [
        None,
        "",
        " ",
    ],
)
def test_consume_requires_transaction_id(
    transaction_id: object,
) -> None:
    with pytest.raises(ValueError):
        accepted_quote().consume(
            transaction_id=transaction_id,
            occurred_at=CONSUMED_AT,
        )


def test_consume_rejects_different_bound_transaction() -> None:
    quote = accepted_quote().update_transaction_reference(
        "transaction-001",
        occurred_at=ACCEPTED_AT,
    )

    with pytest.raises(
        ValueError,
        match="different transaction",
    ):
        quote.consume(
            transaction_id="transaction-002",
            occurred_at=CONSUMED_AT,
        )


@pytest.mark.parametrize(
    "factory",
    [
        pending_quote,
        offered_quote,
        accepted_quote,
    ],
)
def test_expire_open_quote(
    factory: object,
) -> None:
    quote = factory()  # type: ignore[operator]

    expired = quote.expire(
        reason="validity ended",
        occurred_at=AFTER_EXPIRY,
    )

    assert expired.status is FXQuoteStatus.EXPIRED
    assert expired.is_terminal is True
    assert expired.metadata.values[
        "lifecycle_action"
    ] == "expire"
    assert_new_version(
        quote,
        expired,
        occurred_at=AFTER_EXPIRY,
    )


def test_expire_rejects_early_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="cannot expire before",
    ):
        offered_quote().expire(
            occurred_at=ACCEPTED_AT,
        )


@pytest.mark.parametrize(
    "factory",
    [
        pending_quote,
        offered_quote,
        accepted_quote,
    ],
)
def test_cancel_open_quote(
    factory: object,
) -> None:
    quote = factory()  # type: ignore[operator]
    occurred_at = max(
        quote.updated_at,
        CONSUMED_AT,
    )

    cancelled = quote.cancel(
        reason="customer request",
        occurred_at=occurred_at,
    )

    assert cancelled.status is FXQuoteStatus.CANCELLED
    assert cancelled.is_terminal is True
    assert cancelled.metadata.values[
        "lifecycle_action"
    ] == "cancel"
    assert_new_version(
        quote,
        cancelled,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "factory",
    [
        pending_quote,
        offered_quote,
    ],
)
def test_reject_pending_or_offered_quote(
    factory: object,
) -> None:
    quote = factory()  # type: ignore[operator]
    occurred_at = max(
        quote.updated_at,
        ACCEPTED_AT,
    )

    rejected = quote.reject(
        reason="risk policy",
        occurred_at=occurred_at,
    )

    assert rejected.status is FXQuoteStatus.REJECTED
    assert rejected.is_terminal is True
    assert rejected.metadata.values[
        "lifecycle_action"
    ] == "reject"
    assert_new_version(
        quote,
        rejected,
        occurred_at=occurred_at,
    )


def test_reject_disallows_accepted_quote() -> None:
    with pytest.raises(
        ValueError,
        match="pending or offered",
    ):
        accepted_quote().reject(
            reason="late rejection",
            occurred_at=CONSUMED_AT,
        )


@pytest.mark.parametrize(
    "method_name",
    [
        "cancel",
        "reject",
    ],
)
def test_reason_required_for_reasoned_transitions(
    method_name: str,
) -> None:
    quote = offered_quote()
    method = getattr(quote, method_name)

    with pytest.raises(
        ValueError,
        match="reason must not be empty",
    ):
        method(
            reason=" ",
            occurred_at=ACCEPTED_AT,
        )


@pytest.mark.parametrize(
    "terminal_factory",
    [
        lambda: accepted_quote().consume(
            transaction_id="transaction-001",
            occurred_at=CONSUMED_AT,
        ),
        lambda: offered_quote().expire(
            occurred_at=AFTER_EXPIRY,
        ),
        lambda: offered_quote().cancel(
            reason="cancelled",
            occurred_at=ACCEPTED_AT,
        ),
        lambda: offered_quote().reject(
            reason="rejected",
            occurred_at=ACCEPTED_AT,
        ),
    ],
)
def test_terminal_quotes_reject_changes(
    terminal_factory: object,
) -> None:
    quote = terminal_factory()  # type: ignore[operator]

    operations = (
        lambda: quote.update_customer_reference(
            "customer-002",
            occurred_at=quote.updated_at,
        ),
        lambda: quote.update_metadata(
            {"channel": "web"},
            occurred_at=quote.updated_at,
        ),
        lambda: quote.cancel(
            reason="again",
            occurred_at=quote.updated_at,
        ),
    )

    for operation in operations:
        with pytest.raises(
            ValueError,
            match="terminal FX quote",
        ):
            operation()


def test_update_customer_reference() -> None:
    quote = offered_quote()

    updated = quote.update_customer_reference(
        " customer-002 ",
        occurred_at=ACCEPTED_AT,
    )

    assert quote.customer_id == "customer-001"
    assert updated.customer_id == "customer-002"
    assert_new_version(
        quote,
        updated,
        occurred_at=ACCEPTED_AT,
    )


def test_update_customer_reference_rejects_no_op() -> None:
    quote = offered_quote()

    with pytest.raises(
        ValueError,
        match="must change customer id",
    ):
        quote.update_customer_reference(
            quote.customer_id,
            occurred_at=ACCEPTED_AT,
        )


def test_update_customer_reference_rejects_empty() -> None:
    with pytest.raises(ValueError):
        offered_quote().update_customer_reference(
            " ",
            occurred_at=ACCEPTED_AT,
        )


def test_update_transaction_reference_on_accepted() -> None:
    quote = accepted_quote()

    updated = quote.update_transaction_reference(
        " transaction-001 ",
        occurred_at=ACCEPTED_AT,
    )

    assert updated.transaction_id == "transaction-001"
    assert_new_version(
        quote,
        updated,
        occurred_at=ACCEPTED_AT,
    )


def test_update_transaction_reference_requires_accepted() -> None:
    with pytest.raises(
        ValueError,
        match="requires accepted status",
    ):
        offered_quote().update_transaction_reference(
            "transaction-001",
            occurred_at=ACCEPTED_AT,
        )


def test_transaction_reference_cannot_be_rebound() -> None:
    quote = accepted_quote().update_transaction_reference(
        "transaction-001",
        occurred_at=ACCEPTED_AT,
    )

    with pytest.raises(
        ValueError,
        match="cannot be rebound",
    ):
        quote.update_transaction_reference(
            "transaction-002",
            occurred_at=CONSUMED_AT,
        )


def test_update_metadata() -> None:
    quote = offered_quote()

    updated = quote.update_metadata(
        {
            "channel": "web",
            "device_reference": "device-001",
        },
        occurred_at=ACCEPTED_AT,
    )

    assert updated.metadata.values == {
        "channel": "web",
        "device_reference": "device-001",
    }
    assert_new_version(
        quote,
        updated,
        occurred_at=ACCEPTED_AT,
    )


def test_update_metadata_rejects_sensitive_key() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        offered_quote().update_metadata(
            {"access_token": "secret"},
            occurred_at=ACCEPTED_AT,
        )


def test_update_metadata_rejects_no_op() -> None:
    quote = offered_quote()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        quote.update_metadata(
            quote.metadata,
            occurred_at=ACCEPTED_AT,
        )


@pytest.mark.parametrize(
    "operation",
    [
        lambda quote: quote.update_customer_reference(
            "customer-002",
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda quote: quote.update_metadata(
            {"channel": "web"},
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda quote: quote.cancel(
            reason="cancelled",
            occurred_at=NOW - timedelta(seconds=1),
        ),
    ],
)
def test_changes_reject_earlier_timestamp(
    operation: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        operation(pending_quote())  # type: ignore[operator]


def test_equal_timestamp_is_allowed() -> None:
    quote = pending_quote()

    updated = quote.update_customer_reference(
        "customer-002",
        occurred_at=quote.updated_at,
    )

    assert updated.updated_at == quote.updated_at
    assert updated.version == quote.version + 1


def test_each_change_increments_version_once() -> None:
    original = pending_quote()

    offered = original.offer(
        occurred_at=OFFERED_AT,
    )
    accepted = offered.accept(
        occurred_at=ACCEPTED_AT,
    )
    consumed = accepted.consume(
        transaction_id="transaction-001",
        occurred_at=CONSUMED_AT,
    )

    assert original.version == 1
    assert offered.version == 2
    assert accepted.version == 3
    assert consumed.version == 4


def test_original_quote_remains_unchanged() -> None:
    original = pending_quote()

    offered = original.offer(
        occurred_at=OFFERED_AT,
    )

    assert original.status is FXQuoteStatus.PENDING
    assert original.version == 1
    assert original.updated_at == NOW

    assert offered.status is FXQuoteStatus.OFFERED
    assert offered.version == 2


def test_locked_commercial_values_never_change() -> None:
    original = pending_quote()
    offered = original.offer(
        occurred_at=OFFERED_AT,
    )
    accepted = offered.accept(
        occurred_at=ACCEPTED_AT,
    )

    for changed in (offered, accepted):
        assert changed.source_amount == original.source_amount
        assert (
            changed.destination_amount
            == original.destination_amount
        )
        assert changed.rate == original.rate
        assert changed.spread == original.spread
        assert changed.pair == original.pair


def test_serialization_reflects_lifecycle() -> None:
    offered = pending_quote().offer(
        reason="ready",
        occurred_at=OFFERED_AT,
    )

    payload = offered.canonical_dict()

    assert payload["status"] == "offered"
    assert payload["version"] == 2
    assert payload["updated_at"] == OFFERED_AT.isoformat()
    assert payload["metadata"]["lifecycle_action"] == (
        "offer"
    )


def test_fx_quote_lifecycle_methods_available() -> None:
    methods = (
        "offer",
        "accept",
        "consume",
        "expire",
        "cancel",
        "reject",
        "update_customer_reference",
        "update_transaction_reference",
        "update_metadata",
    )

    for method in methods:
        assert callable(getattr(FXQuote, method))
