"""Tests for the NovaPay journal-entry double-entry domain."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain import (
    JournalEntry,
    JournalEntryId,
    JournalEntryMetadata,
    JournalEntryStatus,
    JournalEntryType,
    PostingLine,
    PostingLineId,
    PostingLineMetadata,
    PostingSide,
)


UTC = timezone.utc
CREATED_AT = datetime(2026, 7, 31, 2, 0, tzinfo=UTC)


def debit_line(
    *,
    line_id: str = "posting-line-debit-001",
    account_id: str = "ledger-account-asset-001",
    amount: object = "100.00",
    currency: object = "AUD",
) -> PostingLine:
    return PostingLine.debit(
        line_id=line_id,
        account_id=account_id,
        amount=amount,
        currency=currency,
    )


def credit_line(
    *,
    line_id: str = "posting-line-credit-001",
    account_id: str = "ledger-account-liability-001",
    amount: object = "100.00",
    currency: object = "AUD",
) -> PostingLine:
    return PostingLine.credit(
        line_id=line_id,
        account_id=account_id,
        amount=amount,
        currency=currency,
    )


def balanced_entry(
    *,
    entry_id: str = "journal-entry-001",
    entry_type: object = "transfer",
    occurred_at: datetime = CREATED_AT,
    metadata: object = None,
) -> JournalEntry:
    return JournalEntry.create(
        entry_id=entry_id,
        entry_type=entry_type,
        lines=[
            debit_line(),
            credit_line(),
        ],
        description=" NovaPay transfer journal ",
        reference_id="transfer-reference-001",
        idempotency_key="journal-idempotency-001",
        metadata=metadata,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("posting-line-001", "posting-line-001"),
        (" posting-line-002 ", "posting-line-002"),
        ("line_003", "line_003"),
        ("line.004", "line.004"),
        ("line:005", "line:005"),
    ],
)
def test_posting_line_id_normalizes(
    raw: str,
    expected: str,
) -> None:
    assert PostingLineId.of(raw).value == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "ab",
        "line with spaces",
        "line/invalid",
        None,
        123,
    ],
)
def test_posting_line_id_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        PostingLineId.of(value)


def test_posting_line_id_is_immutable() -> None:
    line_id = PostingLineId("posting-line-001")

    with pytest.raises(FrozenInstanceError):
        line_id.value = "posting-line-002"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("debit", PostingSide.DEBIT),
        (" DEBIT ", PostingSide.DEBIT),
        ("credit", PostingSide.CREDIT),
        (" CREDIT ", PostingSide.CREDIT),
    ],
)
def test_posting_side_parses(
    raw: str,
    expected: PostingSide,
) -> None:
    assert PostingSide.parse(raw) is expected


@pytest.mark.parametrize(
    "value",
    ["", "unknown", "dr", "cr", None, 1],
)
def test_posting_side_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        PostingSide.parse(value)


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("1", Decimal("1")),
        ("1.00", Decimal("1.00")),
        (1, Decimal("1")),
        (Decimal("99.95"), Decimal("99.95")),
        ("0.01", Decimal("0.01")),
    ],
)
def test_posting_line_accepts_positive_decimal_amounts(
    amount: object,
    expected: Decimal,
) -> None:
    line = debit_line(amount=amount)

    assert line.amount == expected


@pytest.mark.parametrize(
    "amount",
    [
        "0",
        "0.00",
        "-1",
        Decimal("-0.01"),
        "",
        "invalid",
        float("nan"),
        1.5,
        True,
        None,
    ],
)
def test_posting_line_rejects_invalid_amounts(
    amount: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        debit_line(amount=amount)


def test_posting_line_debit_constructor() -> None:
    line = PostingLine.debit(
        line_id="posting-line-debit-100",
        account_id="ledger-account-asset-100",
        amount="45.50",
        currency="aud",
        description=" Cash received ",
        reference_id="transfer-100",
        metadata={" source ": "bank"},
    )

    assert line.side is PostingSide.DEBIT
    assert line.is_debit
    assert not line.is_credit
    assert line.amount == Decimal("45.50")
    assert line.signed_amount == Decimal("45.50")
    assert line.currency.code == "AUD"
    assert line.description == "Cash received"
    assert line.reference_id == "transfer-100"
    assert line.metadata.values == {"source": "bank"}


def test_posting_line_credit_constructor() -> None:
    line = PostingLine.credit(
        line_id="posting-line-credit-100",
        account_id="ledger-account-liability-100",
        amount="45.50",
        currency="AUD",
    )

    assert line.side is PostingSide.CREDIT
    assert line.is_credit
    assert not line.is_debit
    assert line.signed_amount == Decimal("-45.50")


def test_posting_line_is_immutable() -> None:
    line = debit_line()

    with pytest.raises(FrozenInstanceError):
        line.amount = Decimal("200")  # type: ignore[misc]


def test_posting_line_metadata_is_defensively_copied() -> None:
    source = {" corridor ": "AU-BI"}

    metadata = PostingLineMetadata.of(source)
    source[" corridor "] = "CHANGED"

    assert metadata.values == {"corridor": "AU-BI"}
    assert isinstance(metadata.values, MappingProxyType)


def test_posting_line_metadata_updates_are_immutable() -> None:
    original = PostingLineMetadata.of({"source": "bank"})
    updated = original.with_value(" corridor ", "AU-BI")
    removed = updated.without("source")

    assert original.values == {"source": "bank"}
    assert updated.values == {
        "source": "bank",
        "corridor": "AU-BI",
    }
    assert removed.values == {"corridor": "AU-BI"}


def test_posting_line_canonical_dict() -> None:
    payload = PostingLine.debit(
        line_id="posting-line-001",
        account_id="ledger-account-001",
        amount="100.00",
        currency="AUD",
        metadata={"source": "bank"},
    ).canonical_dict()

    assert payload == {
        "line_id": "posting-line-001",
        "account_id": "ledger-account-001",
        "side": "debit",
        "amount": "100",
        "currency": "AUD",
        "description": None,
        "reference_id": None,
        "metadata": {"source": "bank"},
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("journal-entry-001", "journal-entry-001"),
        (" journal-entry-002 ", "journal-entry-002"),
        ("journal_entry_003", "journal_entry_003"),
    ],
)
def test_journal_entry_id_normalizes(
    raw: str,
    expected: str,
) -> None:
    assert JournalEntryId.of(raw).value == expected


@pytest.mark.parametrize(
    "value",
    ["", " ", "ab", "entry with spaces", None, 123],
)
def test_journal_entry_id_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        JournalEntryId.of(value)


@pytest.mark.parametrize(
    "entry_type",
    list(JournalEntryType),
)
def test_all_journal_entry_types_parse(
    entry_type: JournalEntryType,
) -> None:
    assert (
        JournalEntryType.parse(
            f" {entry_type.value.upper()} "
        )
        is entry_type
    )


@pytest.mark.parametrize(
    "status",
    list(JournalEntryStatus),
)
def test_all_journal_entry_statuses_parse(
    status: JournalEntryStatus,
) -> None:
    assert (
        JournalEntryStatus.parse(
            f" {status.value.upper()} "
        )
        is status
    )


@pytest.mark.parametrize(
    "value",
    ["", "unknown", None, 100],
)
def test_journal_entry_type_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        JournalEntryType.parse(value)


@pytest.mark.parametrize(
    "value",
    ["", "pending", "cancelled", None, 100],
)
def test_journal_entry_status_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        JournalEntryStatus.parse(value)


def test_journal_metadata_is_defensively_copied() -> None:
    source = {" correlation_id ": "correlation-001"}

    metadata = JournalEntryMetadata.of(source)
    source[" correlation_id "] = "changed"

    assert metadata.values == {
        "correlation_id": "correlation-001",
    }
    assert isinstance(metadata.values, MappingProxyType)


def test_journal_metadata_updates_are_immutable() -> None:
    original = JournalEntryMetadata.of(
        {"correlation_id": "correlation-001"}
    )

    updated = original.with_value(
        " corridor ",
        "AU-BI",
    )
    removed = updated.without("correlation_id")

    assert original.values == {
        "correlation_id": "correlation-001",
    }
    assert updated.values == {
        "correlation_id": "correlation-001",
        "corridor": "AU-BI",
    }
    assert removed.values == {"corridor": "AU-BI"}


def test_journal_entry_create_normalizes_values() -> None:
    entry = balanced_entry(
        metadata={" source ": "wallet-service"},
    )

    assert entry.entry_id == JournalEntryId(
        "journal-entry-001"
    )
    assert entry.entry_type is JournalEntryType.TRANSFER
    assert entry.status is JournalEntryStatus.DRAFT
    assert entry.description == "NovaPay transfer journal"
    assert entry.reference_id == "transfer-reference-001"
    assert (
        entry.idempotency_key
        == "journal-idempotency-001"
    )
    assert entry.metadata.values == {
        "source": "wallet-service",
    }
    assert entry.version == 1


def test_journal_entry_is_balanced() -> None:
    entry = balanced_entry()

    assert entry.total_debits == Decimal("100.00")
    assert entry.total_credits == Decimal("100.00")
    assert entry.is_balanced
    assert entry.currency.code == "AUD"


def test_journal_entry_stores_lines_as_tuple() -> None:
    lines = [debit_line(), credit_line()]

    entry = JournalEntry.create(
        entry_id="journal-entry-tuple-001",
        entry_type="transfer",
        lines=lines,
        occurred_at=CREATED_AT,
    )

    lines.clear()

    assert isinstance(entry.lines, tuple)
    assert len(entry.lines) == 2


def test_journal_entry_supports_multiple_debit_lines() -> None:
    entry = JournalEntry.create(
        entry_id="journal-entry-multiple-debits",
        entry_type="settlement",
        lines=[
            debit_line(
                line_id="debit-line-001",
                account_id="ledger-account-cash-001",
                amount="60",
            ),
            debit_line(
                line_id="debit-line-002",
                account_id="ledger-account-fee-001",
                amount="40",
            ),
            credit_line(
                line_id="credit-line-001",
                amount="100",
            ),
        ],
        occurred_at=CREATED_AT,
    )

    assert len(entry.debit_lines) == 2
    assert len(entry.credit_lines) == 1
    assert entry.total_debits == Decimal("100")
    assert entry.total_credits == Decimal("100")


def test_journal_entry_supports_multiple_credit_lines() -> None:
    entry = JournalEntry.create(
        entry_id="journal-entry-multiple-credits",
        entry_type="payment",
        lines=[
            debit_line(
                line_id="debit-line-001",
                amount="100",
            ),
            credit_line(
                line_id="credit-line-001",
                account_id="ledger-account-merchant-001",
                amount="90",
            ),
            credit_line(
                line_id="credit-line-002",
                account_id="ledger-account-fee-001",
                amount="10",
            ),
        ],
        occurred_at=CREATED_AT,
    )

    assert len(entry.debit_lines) == 1
    assert len(entry.credit_lines) == 2
    assert entry.is_balanced


def test_journal_entry_rejects_one_line() -> None:
    with pytest.raises(ValueError, match="at least two"):
        JournalEntry.create(
            entry_id="journal-entry-one-line",
            entry_type="adjustment",
            lines=[debit_line()],
            occurred_at=CREATED_AT,
        )


def test_journal_entry_rejects_unbalanced_lines() -> None:
    with pytest.raises(ValueError, match="not balanced"):
        JournalEntry.create(
            entry_id="journal-entry-unbalanced",
            entry_type="transfer",
            lines=[
                debit_line(amount="100"),
                credit_line(amount="99"),
            ],
            occurred_at=CREATED_AT,
        )


def test_journal_entry_rejects_missing_debit() -> None:
    with pytest.raises(ValueError, match="debit"):
        JournalEntry.create(
            entry_id="journal-entry-no-debit",
            entry_type="adjustment",
            lines=[
                credit_line(
                    line_id="credit-line-001",
                    amount="50",
                ),
                credit_line(
                    line_id="credit-line-002",
                    amount="50",
                ),
            ],
            occurred_at=CREATED_AT,
        )


def test_journal_entry_rejects_missing_credit() -> None:
    with pytest.raises(ValueError, match="credit"):
        JournalEntry.create(
            entry_id="journal-entry-no-credit",
            entry_type="adjustment",
            lines=[
                debit_line(
                    line_id="debit-line-001",
                    amount="50",
                ),
                debit_line(
                    line_id="debit-line-002",
                    amount="50",
                ),
            ],
            occurred_at=CREATED_AT,
        )


def test_journal_entry_rejects_multiple_currencies() -> None:
    with pytest.raises(ValueError, match="same currency"):
        JournalEntry.create(
            entry_id="journal-entry-multi-currency",
            entry_type="transfer",
            lines=[
                debit_line(currency="AUD"),
                credit_line(currency="USD"),
            ],
            occurred_at=CREATED_AT,
        )


def test_journal_entry_rejects_duplicate_line_ids() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        JournalEntry.create(
            entry_id="journal-entry-duplicate-lines",
            entry_type="transfer",
            lines=[
                debit_line(
                    line_id="duplicate-line-001",
                ),
                credit_line(
                    line_id="duplicate-line-001",
                ),
            ],
            occurred_at=CREATED_AT,
        )


@pytest.mark.parametrize(
    "lines",
    [
        None,
        "invalid",
        {"line": "invalid"},
        [object(), object()],
    ],
)
def test_journal_entry_rejects_invalid_line_collections(
    lines: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        JournalEntry.create(
            entry_id="journal-entry-invalid-lines",
            entry_type="transfer",
            lines=lines,
            occurred_at=CREATED_AT,
        )


def test_journal_entry_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        balanced_entry(
            occurred_at=datetime(2026, 7, 31, 2, 0),
        )


def test_journal_entry_normalizes_datetime_to_utc() -> None:
    plus_ten = timezone(timedelta(hours=10))

    entry = balanced_entry(
        occurred_at=datetime(
            2026,
            7,
            31,
            12,
            0,
            tzinfo=plus_ten,
        )
    )

    assert entry.created_at == datetime(
        2026,
        7,
        31,
        2,
        0,
        tzinfo=UTC,
    )


def test_journal_entry_is_immutable() -> None:
    entry = balanced_entry()

    with pytest.raises(FrozenInstanceError):
        entry.status = JournalEntryStatus.POSTED  # type: ignore[misc]


def test_draft_can_be_posted() -> None:
    draft = balanced_entry()
    posted_at = CREATED_AT + timedelta(minutes=1)

    posted = draft.post(occurred_at=posted_at)

    assert posted is not draft
    assert draft.status is JournalEntryStatus.DRAFT
    assert posted.status is JournalEntryStatus.POSTED
    assert posted.version == 2
    assert posted.created_at == CREATED_AT
    assert posted.updated_at == posted_at
    assert posted.lines is draft.lines


def test_draft_can_be_voided() -> None:
    draft = balanced_entry()
    voided_at = CREATED_AT + timedelta(minutes=1)

    voided = draft.void(
        occurred_at=voided_at,
        metadata={"reason": "cancelled"},
    )

    assert voided.status is JournalEntryStatus.VOIDED
    assert voided.version == 2
    assert voided.metadata.values == {
        "reason": "cancelled",
    }


def test_posted_entry_can_be_reversed() -> None:
    posted = balanced_entry().post(
        occurred_at=CREATED_AT + timedelta(minutes=1)
    )

    reversed_entry = posted.reverse(
        occurred_at=CREATED_AT + timedelta(minutes=2),
        metadata={
            "reversal_entry_id": "journal-reversal-001",
        },
    )

    assert reversed_entry.status is JournalEntryStatus.REVERSED
    assert reversed_entry.version == 3
    assert reversed_entry.lines is posted.lines
    assert reversed_entry.metadata.values == {
        "reversal_entry_id": "journal-reversal-001",
    }


@pytest.mark.parametrize(
    ("start_status", "operation"),
    [
        ("posted", "post"),
        ("posted", "void"),
        ("draft", "reverse"),
        ("voided", "post"),
        ("voided", "reverse"),
        ("reversed", "post"),
        ("reversed", "void"),
    ],
)
def test_invalid_lifecycle_transitions_fail(
    start_status: str,
    operation: str,
) -> None:
    entry = balanced_entry()

    if start_status == "posted":
        entry = entry.post(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )
    elif start_status == "voided":
        entry = entry.void(
            occurred_at=CREATED_AT
            + timedelta(minutes=1)
        )
    elif start_status == "reversed":
        entry = (
            entry.post(
                occurred_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .reverse(
                occurred_at=CREATED_AT
                + timedelta(minutes=2)
            )
        )

    method = getattr(entry, operation)

    with pytest.raises(ValueError):
        method(
            occurred_at=CREATED_AT
            + timedelta(minutes=5)
        )


def test_backdated_transition_is_rejected() -> None:
    entry = balanced_entry()

    with pytest.raises(
        ValueError,
        match="earlier than updated_at",
    ):
        entry.post(
            occurred_at=CREATED_AT
            - timedelta(seconds=1)
        )


def test_with_metadata_returns_new_version() -> None:
    entry = balanced_entry(
        metadata={"source": "transfer-service"},
    )

    updated = entry.with_metadata(
        {
            "source": "transfer-service",
            "reviewed": True,
        },
        occurred_at=CREATED_AT + timedelta(seconds=1),
    )

    assert updated is not entry
    assert entry.version == 1
    assert updated.version == 2
    assert updated.status is entry.status
    assert updated.lines is entry.lines
    assert updated.metadata.values == {
        "source": "transfer-service",
        "reviewed": True,
    }


def test_journal_account_ids_preserve_first_seen_order() -> None:
    entry = JournalEntry.create(
        entry_id="journal-entry-account-order",
        entry_type="adjustment",
        lines=[
            debit_line(
                line_id="debit-line-001",
                account_id="ledger-account-001",
                amount="60",
            ),
            debit_line(
                line_id="debit-line-002",
                account_id="ledger-account-001",
                amount="40",
            ),
            credit_line(
                line_id="credit-line-001",
                account_id="ledger-account-002",
                amount="100",
            ),
        ],
        occurred_at=CREATED_AT,
    )

    assert tuple(
        account_id.value
        for account_id in entry.account_ids
    ) == (
        "ledger-account-001",
        "ledger-account-002",
    )


def test_journal_entry_canonical_dict() -> None:
    entry = balanced_entry(
        metadata={"corridor": "AU-BI"},
    )

    payload = entry.canonical_dict()

    assert payload["entry_id"] == "journal-entry-001"
    assert payload["entry_type"] == "transfer"
    assert payload["status"] == "draft"
    assert payload["currency"] == "AUD"
    assert payload["total_debits"] == "100"
    assert payload["total_credits"] == "100"
    assert payload["description"] == (
        "NovaPay transfer journal"
    )
    assert payload["reference_id"] == (
        "transfer-reference-001"
    )
    assert payload["idempotency_key"] == (
        "journal-idempotency-001"
    )
    assert payload["version"] == 1
    assert payload["metadata"] == {
        "corridor": "AU-BI",
    }
    assert len(payload["lines"]) == 2


def test_journal_entry_has_no_authoritative_balance() -> None:
    entry = balanced_entry()

    forbidden = {
        "balance",
        "account_balance",
        "journal_balance",
        "available_balance",
        "current_balance",
    }

    for attribute in forbidden:
        assert not hasattr(entry, attribute)


def test_public_domain_exports_are_available() -> None:
    from afritech.novapay import domain

    expected = {
        "JournalEntry",
        "JournalEntryId",
        "JournalEntryMetadata",
        "JournalEntryStatus",
        "JournalEntryType",
        "PostingLine",
        "PostingLineId",
        "PostingLineMetadata",
        "PostingSide",
    }

    assert expected.issubset(set(domain.__all__))

    for name in expected:
        assert getattr(domain, name) is not None
