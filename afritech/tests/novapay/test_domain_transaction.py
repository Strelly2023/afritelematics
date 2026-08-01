"""Tests for the canonical NovaPay Transaction domain."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain import (
    Money,
    Transaction,
    TransactionDirection,
    TransactionId,
    TransactionMetadata,
    TransactionStatus,
    TransactionType,
)


UTC = timezone.utc
CREATED_AT = datetime(
    2026,
    8,
    1,
    0,
    0,
    tzinfo=UTC,
)


def internal_transaction(
    *,
    transaction_id: str = "txn-internal-001",
    transaction_type: object = "transfer",
    amount: Money | None = None,
    metadata: object = None,
    occurred_at: datetime = CREATED_AT,
) -> Transaction:
    return Transaction.create(
        transaction_id=transaction_id,
        transaction_type=transaction_type,
        direction="internal",
        amount=amount or Money.of("100.00", "AUD"),
        source_wallet_id="wallet-source-001",
        destination_wallet_id="wallet-destination-001",
        description=" NovaPay wallet transfer ",
        external_reference="provider-reference-001",
        idempotency_key="transaction-idempotency-001",
        metadata=metadata,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("txn-001", "txn-001"),
        (" txn-002 ", "txn-002"),
        ("transaction_003", "transaction_003"),
        ("transaction.004", "transaction.004"),
        ("transaction:005", "transaction:005"),
    ],
)
def test_transaction_id_normalizes(
    raw: str,
    expected: str,
) -> None:
    assert TransactionId.of(raw).value == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "ab",
        "transaction with spaces",
        "transaction/invalid",
        None,
        123,
    ],
)
def test_transaction_id_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        TransactionId.of(value)


def test_transaction_id_is_immutable() -> None:
    transaction_id = TransactionId("txn-immutable-001")

    with pytest.raises(FrozenInstanceError):
        transaction_id.value = "txn-changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "transaction_type",
    list(TransactionType),
)
def test_all_transaction_types_parse(
    transaction_type: TransactionType,
) -> None:
    raw = transaction_type.value.upper().replace("_", "-")

    assert TransactionType.parse(raw) is transaction_type


@pytest.mark.parametrize(
    "status",
    list(TransactionStatus),
)
def test_all_transaction_statuses_parse(
    status: TransactionStatus,
) -> None:
    assert (
        TransactionStatus.parse(
            f" {status.value.upper()} "
        )
        is status
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("inbound", TransactionDirection.INBOUND),
        (" CREDIT ", TransactionDirection.INBOUND),
        ("incoming", TransactionDirection.INBOUND),
        ("outbound", TransactionDirection.OUTBOUND),
        ("DEBIT", TransactionDirection.OUTBOUND),
        ("outgoing", TransactionDirection.OUTBOUND),
        ("internal", TransactionDirection.INTERNAL),
        ("self", TransactionDirection.INTERNAL),
    ],
)
def test_transaction_direction_parses_aliases(
    raw: str,
    expected: TransactionDirection,
) -> None:
    assert TransactionDirection.parse(raw) is expected


@pytest.mark.parametrize(
    "value",
    ["", "unknown", "sideways", None, 100],
)
def test_transaction_type_status_and_direction_reject_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        TransactionType.parse(value)

    with pytest.raises((TypeError, ValueError)):
        TransactionStatus.parse(value)

    with pytest.raises((TypeError, ValueError)):
        TransactionDirection.parse(value)


@pytest.mark.parametrize(
    ("status", "terminal", "successful"),
    [
        (TransactionStatus.PENDING, False, False),
        (TransactionStatus.AUTHORIZED, False, False),
        (TransactionStatus.PROCESSING, False, False),
        (TransactionStatus.COMPLETED, True, True),
        (TransactionStatus.FAILED, True, False),
        (TransactionStatus.CANCELLED, True, False),
        (TransactionStatus.REVERSED, True, False),
    ],
)
def test_transaction_status_semantics(
    status: TransactionStatus,
    terminal: bool,
    successful: bool,
) -> None:
    assert status.is_terminal is terminal
    assert status.is_successful is successful


def test_transaction_metadata_is_defensively_copied() -> None:
    source = {
        " channel ": "mobile",
        "correlation_id": "corr-001",
    }

    metadata = TransactionMetadata.of(source)

    source[" channel "] = "changed"
    source["correlation_id"] = "changed"

    assert metadata.values == {
        "channel": "mobile",
        "correlation_id": "corr-001",
    }
    assert isinstance(metadata.values, MappingProxyType)


def test_transaction_metadata_updates_are_immutable() -> None:
    original = TransactionMetadata.of(
        {"channel": "mobile"}
    )

    updated = original.with_value(
        " corridor ",
        "AU-BI",
    )
    removed = updated.without("channel")

    assert original.values == {
        "channel": "mobile",
    }
    assert updated.values == {
        "channel": "mobile",
        "corridor": "AU-BI",
    }
    assert removed.values == {
        "corridor": "AU-BI",
    }


@pytest.mark.parametrize(
    "metadata",
    [
        [],
        "metadata",
        123,
    ],
)
def test_transaction_metadata_rejects_non_mappings(
    metadata: object,
) -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        TransactionMetadata.of(metadata)


def test_transaction_metadata_rejects_invalid_keys() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        TransactionMetadata({1: "invalid"})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must not be empty"):
        TransactionMetadata({"   ": "invalid"})


def test_internal_transaction_create_normalizes_values() -> None:
    transaction = internal_transaction(
        metadata={
            " channel ": "mobile",
        }
    )

    assert transaction.transaction_id == TransactionId(
        "txn-internal-001"
    )
    assert transaction.transaction_type is (
        TransactionType.TRANSFER
    )
    assert transaction.status is TransactionStatus.PENDING
    assert transaction.direction is (
        TransactionDirection.INTERNAL
    )

    assert transaction.amount == Money.of(
        "100.00",
        "AUD",
    )
    assert transaction.amount.amount == Decimal("100.00")
    assert transaction.currency.code == "AUD"

    assert transaction.source_wallet_id is not None
    assert transaction.source_wallet_id.value == (
        "wallet-source-001"
    )

    assert transaction.destination_wallet_id is not None
    assert transaction.destination_wallet_id.value == (
        "wallet-destination-001"
    )

    assert transaction.description == (
        "NovaPay wallet transfer"
    )
    assert transaction.external_reference == (
        "provider-reference-001"
    )
    assert transaction.idempotency_key == (
        "transaction-idempotency-001"
    )
    assert transaction.metadata.values == {
        "channel": "mobile",
    }

    assert transaction.created_at == CREATED_AT
    assert transaction.updated_at == CREATED_AT
    assert transaction.version == 1
    assert transaction.journal_entry_id is None


def test_inbound_transaction_requires_destination_wallet() -> None:
    with pytest.raises(
        ValueError,
        match="destination_wallet_id",
    ):
        Transaction.create(
            transaction_id="txn-inbound-invalid",
            transaction_type="funding",
            direction="inbound",
            amount=Money.of("25", "AUD"),
            occurred_at=CREATED_AT,
        )


def test_inbound_transaction_accepts_destination_wallet() -> None:
    transaction = Transaction.create(
        transaction_id="txn-inbound-valid",
        transaction_type="funding",
        direction="inbound",
        amount=Money.of("25", "AUD"),
        destination_wallet_id="wallet-destination-001",
        occurred_at=CREATED_AT,
    )

    assert transaction.source_wallet_id is None
    assert transaction.destination_wallet_id is not None


def test_outbound_transaction_requires_source_wallet() -> None:
    with pytest.raises(
        ValueError,
        match="source_wallet_id",
    ):
        Transaction.create(
            transaction_id="txn-outbound-invalid",
            transaction_type="withdrawal",
            direction="outbound",
            amount=Money.of("25", "AUD"),
            occurred_at=CREATED_AT,
        )


def test_outbound_transaction_accepts_source_wallet() -> None:
    transaction = Transaction.create(
        transaction_id="txn-outbound-valid",
        transaction_type="withdrawal",
        direction="outbound",
        amount=Money.of("25", "AUD"),
        source_wallet_id="wallet-source-001",
        occurred_at=CREATED_AT,
    )

    assert transaction.source_wallet_id is not None
    assert transaction.destination_wallet_id is None


@pytest.mark.parametrize(
    ("source_wallet_id", "destination_wallet_id", "message"),
    [
        (None, "wallet-destination-001", "source_wallet_id"),
        ("wallet-source-001", None, "destination_wallet_id"),
        ("wallet-same-001", "wallet-same-001", "must differ"),
    ],
)
def test_internal_transaction_wallet_invariants(
    source_wallet_id: object | None,
    destination_wallet_id: object | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        Transaction.create(
            transaction_id="txn-internal-invalid",
            transaction_type="transfer",
            direction="internal",
            amount=Money.of("25", "AUD"),
            source_wallet_id=source_wallet_id,
            destination_wallet_id=destination_wallet_id,
            occurred_at=CREATED_AT,
        )


def test_transaction_requires_money_amount() -> None:
    with pytest.raises(
        TypeError,
        match="amount must be Money",
    ):
        Transaction.create(
            transaction_id="txn-invalid-amount",
            transaction_type="payment",
            direction="outbound",
            amount="10 AUD",  # type: ignore[arg-type]
            source_wallet_id="wallet-source-001",
            occurred_at=CREATED_AT,
        )


def test_transaction_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        internal_transaction(
            occurred_at=datetime(
                2026,
                8,
                1,
                0,
                0,
            )
        )


def test_transaction_normalizes_datetime_to_utc() -> None:
    plus_ten = timezone(timedelta(hours=10))

    transaction = internal_transaction(
        occurred_at=datetime(
            2026,
            8,
            1,
            10,
            0,
            tzinfo=plus_ten,
        )
    )

    assert transaction.created_at == CREATED_AT
    assert transaction.updated_at == CREATED_AT


def test_transaction_is_immutable() -> None:
    transaction = internal_transaction()

    with pytest.raises(FrozenInstanceError):
        transaction.status = (  # type: ignore[misc]
            TransactionStatus.COMPLETED
        )


def test_pending_transaction_can_be_authorized() -> None:
    pending = internal_transaction()
    authorized_at = CREATED_AT + timedelta(minutes=1)

    authorized = pending.authorize(
        occurred_at=authorized_at,
        metadata={"authorization_id": "auth-001"},
    )

    assert pending.status is TransactionStatus.PENDING
    assert authorized.status is (
        TransactionStatus.AUTHORIZED
    )
    assert authorized.version == 2
    assert authorized.updated_at == authorized_at
    assert authorized.metadata.values == {
        "authorization_id": "auth-001",
    }


def test_authorized_transaction_can_start_processing() -> None:
    authorized = internal_transaction().authorize(
        occurred_at=CREATED_AT + timedelta(minutes=1)
    )

    processing = authorized.start_processing(
        occurred_at=CREATED_AT + timedelta(minutes=2)
    )

    assert processing.status is (
        TransactionStatus.PROCESSING
    )
    assert processing.version == 3


def test_processing_transaction_requires_journal_on_completion() -> None:
    processing = (
        internal_transaction()
        .authorize(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )
        .start_processing(
            occurred_at=CREATED_AT
            + timedelta(minutes=2)
        )
    )

    with pytest.raises((TypeError, ValueError)):
        processing.complete(
            journal_entry_id=None,
            occurred_at=CREATED_AT
            + timedelta(minutes=3),
        )


def test_processing_transaction_can_complete() -> None:
    processing = (
        internal_transaction()
        .authorize(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )
        .start_processing(
            occurred_at=CREATED_AT
            + timedelta(minutes=2)
        )
    )

    completed = processing.complete(
        journal_entry_id="journal-entry-transaction-001",
        occurred_at=CREATED_AT + timedelta(minutes=3),
        metadata={"provider_reference": "provider-001"},
    )

    assert completed.status is (
        TransactionStatus.COMPLETED
    )
    assert completed.version == 4
    assert completed.is_terminal
    assert completed.is_successful
    assert completed.has_journal_entry
    assert completed.journal_entry_id is not None
    assert completed.journal_entry_id.value == (
        "journal-entry-transaction-001"
    )
    assert completed.metadata.values == {
        "provider_reference": "provider-001",
    }


def test_completed_transaction_can_be_reversed() -> None:
    completed = (
        internal_transaction()
        .authorize(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )
        .start_processing(
            occurred_at=CREATED_AT
            + timedelta(minutes=2)
        )
        .complete(
            journal_entry_id=(
                "journal-entry-transaction-001"
            ),
            occurred_at=CREATED_AT
            + timedelta(minutes=3),
        )
    )

    reversed_transaction = completed.reverse(
        journal_entry_id="journal-entry-reversal-001",
        occurred_at=CREATED_AT + timedelta(minutes=4),
        metadata={"reason": "duplicate processing"},
    )

    assert reversed_transaction.status is (
        TransactionStatus.REVERSED
    )
    assert reversed_transaction.version == 5
    assert reversed_transaction.is_terminal
    assert not reversed_transaction.is_successful
    assert reversed_transaction.journal_entry_id is not None
    assert reversed_transaction.journal_entry_id.value == (
        "journal-entry-reversal-001"
    )


def test_pending_transaction_can_fail() -> None:
    failed = internal_transaction().fail(
        occurred_at=CREATED_AT + timedelta(minutes=1),
        metadata={"reason": "risk rejection"},
    )

    assert failed.status is TransactionStatus.FAILED
    assert failed.version == 2
    assert failed.is_terminal


def test_pending_transaction_can_be_cancelled() -> None:
    cancelled = internal_transaction().cancel(
        occurred_at=CREATED_AT + timedelta(minutes=1),
        metadata={"reason": "customer cancelled"},
    )

    assert cancelled.status is (
        TransactionStatus.CANCELLED
    )
    assert cancelled.version == 2
    assert cancelled.is_terminal


@pytest.mark.parametrize(
    ("setup", "operation"),
    [
        ("pending", "complete"),
        ("pending", "reverse"),
        ("authorized", "complete"),
        ("authorized", "reverse"),
        ("processing", "authorize"),
        ("processing", "cancel"),
        ("completed", "authorize"),
        ("completed", "start_processing"),
        ("completed", "complete"),
        ("failed", "authorize"),
        ("failed", "start_processing"),
        ("failed", "cancel"),
        ("cancelled", "authorize"),
        ("cancelled", "start_processing"),
        ("reversed", "authorize"),
        ("reversed", "fail"),
    ],
)
def test_invalid_transaction_transitions_fail(
    setup: str,
    operation: str,
) -> None:
    transaction = internal_transaction()

    if setup in {
        "authorized",
        "processing",
        "completed",
        "reversed",
    }:
        transaction = transaction.authorize(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )

    if setup in {
        "processing",
        "completed",
        "reversed",
    }:
        transaction = transaction.start_processing(
            occurred_at=CREATED_AT
            + timedelta(minutes=2)
        )

    if setup in {
        "completed",
        "reversed",
    }:
        transaction = transaction.complete(
            journal_entry_id=(
                "journal-entry-transaction-001"
            ),
            occurred_at=CREATED_AT
            + timedelta(minutes=3),
        )

    if setup == "reversed":
        transaction = transaction.reverse(
            journal_entry_id=(
                "journal-entry-reversal-001"
            ),
            occurred_at=CREATED_AT
            + timedelta(minutes=4),
        )

    if setup == "failed":
        transaction = transaction.fail(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )

    if setup == "cancelled":
        transaction = transaction.cancel(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )

    method = getattr(transaction, operation)

    kwargs = {
        "occurred_at": (
            CREATED_AT + timedelta(minutes=10)
        )
    }

    if operation in {
        "complete",
        "reverse",
    }:
        kwargs["journal_entry_id"] = (
            "journal-entry-invalid-transition"
        )

    with pytest.raises(ValueError):
        method(**kwargs)


def test_backdated_transition_is_rejected() -> None:
    transaction = internal_transaction()

    with pytest.raises(
        ValueError,
        match="earlier than updated_at",
    ):
        transaction.authorize(
            occurred_at=CREATED_AT
            - timedelta(seconds=1)
        )


def test_with_metadata_returns_new_version() -> None:
    transaction = internal_transaction(
        metadata={"channel": "mobile"}
    )

    updated = transaction.with_metadata(
        {
            "channel": "mobile",
            "reviewed": True,
        },
        occurred_at=CREATED_AT + timedelta(seconds=30),
    )

    assert updated is not transaction
    assert transaction.version == 1
    assert updated.version == 2
    assert updated.status is transaction.status
    assert updated.amount is transaction.amount
    assert updated.metadata.values == {
        "channel": "mobile",
        "reviewed": True,
    }


def test_transaction_canonical_dict() -> None:
    transaction = internal_transaction(
        metadata={"corridor": "AU-BI"}
    )

    payload = transaction.canonical_dict()

    assert payload["transaction_id"] == (
        "txn-internal-001"
    )
    assert payload["transaction_type"] == "transfer"
    assert payload["status"] == "pending"
    assert payload["direction"] == "internal"
    assert payload["amount"] == "100.00"
    assert payload["currency"] == "AUD"
    assert payload["source_wallet_id"] == (
        "wallet-source-001"
    )
    assert payload["destination_wallet_id"] == (
        "wallet-destination-001"
    )
    assert payload["journal_entry_id"] is None
    assert payload["description"] == (
        "NovaPay wallet transfer"
    )
    assert payload["external_reference"] == (
        "provider-reference-001"
    )
    assert payload["idempotency_key"] == (
        "transaction-idempotency-001"
    )
    assert payload["metadata"] == {
        "corridor": "AU-BI",
    }
    assert payload["version"] == 1


def test_transaction_has_no_authoritative_balance() -> None:
    transaction = internal_transaction()

    forbidden = {
        "balance",
        "wallet_balance",
        "available_balance",
        "current_balance",
        "ledger_balance",
    }

    for attribute in forbidden:
        assert not hasattr(transaction, attribute)


def test_canonical_domain_exports_are_available() -> None:
    from afritech.novapay import domain

    required = {
        "Transaction",
        "TransactionDirection",
        "TransactionId",
        "TransactionMetadata",
        "TransactionStatus",
        "TransactionType",
    }

    assert required.issubset(set(domain.__all__))

    for name in required:
        assert getattr(domain, name) is not None


def test_top_level_novapay_exports_are_available() -> None:
    from afritech import novapay

    required = {
        "Transaction",
        "TransactionDirection",
        "TransactionId",
        "TransactionMetadata",
        "TransactionStatus",
        "TransactionType",
    }

    assert required.issubset(set(novapay.__all__))

    assert novapay.Transaction is Transaction
    assert (
        novapay.TransactionDirection
        is TransactionDirection
    )
    assert novapay.TransactionId is TransactionId
    assert (
        novapay.TransactionMetadata
        is TransactionMetadata
    )
    assert (
        novapay.TransactionStatus
        is TransactionStatus
    )
    assert (
        novapay.TransactionType
        is TransactionType
    )
