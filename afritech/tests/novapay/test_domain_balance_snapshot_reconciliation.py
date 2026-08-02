from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.balance_snapshot import (
    BalanceComponent,
    BalanceComponentType,
    BalanceReconciliation,
    BalanceSnapshot,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)


NOW = datetime(
    2026,
    8,
    2,
    9,
    0,
    tzinfo=timezone.utc,
)


def component(
    component_type: object,
    amount: str,
    *,
    currency: str = "AUD",
) -> BalanceComponent:
    return BalanceComponent.create(
        component_type=component_type,
        amount=Money.of(amount, currency),
        wallet_id="wallet-001",
        ledger_account_id="ledger-account-001",
    )


def snapshot(
    *,
    posted: str = "100.00",
    available: str = "75.00",
    pending_debit: str | None = None,
    pending_credit: str | None = None,
    reserved: str | None = "25.00",
    hold: str | None = None,
    overdraft: str | None = None,
    uncleared: str | None = None,
    currency: str = "AUD",
) -> BalanceSnapshot:
    components = [
        component(
            BalanceComponentType.POSTED,
            posted,
            currency=currency,
        ),
        component(
            BalanceComponentType.AVAILABLE,
            available,
            currency=currency,
        ),
    ]

    optional = (
        (
            BalanceComponentType.PENDING_DEBIT,
            pending_debit,
        ),
        (
            BalanceComponentType.PENDING_CREDIT,
            pending_credit,
        ),
        (
            BalanceComponentType.RESERVED,
            reserved,
        ),
        (
            BalanceComponentType.HOLD,
            hold,
        ),
        (
            BalanceComponentType.OVERDRAFT,
            overdraft,
        ),
        (
            BalanceComponentType.UNCLEARED,
            uncleared,
        ),
    )

    for component_type, amount in optional:
        if amount is not None:
            components.append(
                component(
                    component_type,
                    amount,
                    currency=currency,
                )
            )

    return BalanceSnapshot.create(
        snapshot_id="balance-snapshot-001",
        snapshot_type="wallet",
        currency=currency,
        components=components,
        ledger_position=100,
        as_of=NOW,
        wallet_id="wallet-001",
        ledger_account_id="ledger-account-001",
    )


def test_balance_reconciliation_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(BalanceReconciliation)
    } == {
        "currency",
        "posted",
        "available",
        "pending_debit",
        "pending_credit",
        "reserved",
        "hold",
        "overdraft",
        "uncleared",
        "expected_available",
        "difference",
    }


def test_reconciliation_is_immutable() -> None:
    result = snapshot().reconcile()

    with pytest.raises(FrozenInstanceError):
        result.currency = Currency.of(  # type: ignore[misc]
            "USD"
        )


def test_component_amount_returns_existing_component() -> None:
    value = snapshot().component_amount("reserved")

    assert value == Money.of("25.00", "AUD")


def test_component_amount_returns_canonical_zero() -> None:
    value = snapshot().component_amount("hold")

    assert value == Money.of("0", "AUD")
    assert value.currency == Currency.of("AUD")


@pytest.mark.parametrize(
    ("component_type", "expected"),
    [
        ("pending_debit", "0.00"),
        ("pending_credit", "0.00"),
        ("reserved", "25.00"),
        ("hold", "0.00"),
        ("overdraft", "0.00"),
        ("uncleared", "0.00"),
    ],
)
def test_component_projection_properties(
    component_type: str,
    expected: str,
) -> None:
    balance_snapshot = snapshot()

    value = getattr(
        balance_snapshot,
        component_type,
    )

    assert isinstance(value, Money)
    assert str(value.amount) == expected


def test_expected_available_with_reserved_amount() -> None:
    balance_snapshot = snapshot(
        posted="100.00",
        available="75.00",
        reserved="25.00",
    )

    assert balance_snapshot.expected_available == (
        Money.of("75.00", "AUD")
    )


def test_expected_available_complete_formula() -> None:
    balance_snapshot = snapshot(
        posted="1000.00",
        available="855.00",
        pending_debit="100.00",
        pending_credit="50.00",
        reserved="40.00",
        hold="25.00",
        overdraft="20.00",
    )

    # 1000 - 100 + 50 - 40 - 25 + 20 = 905
    assert balance_snapshot.expected_available == (
        Money.of("905.00", "AUD")
    )
    assert balance_snapshot.reconciliation_difference == (
        Money.of("-50.00", "AUD")
    )


def test_reconciled_snapshot() -> None:
    balance_snapshot = snapshot(
        posted="1000.00",
        available="905.00",
        pending_debit="100.00",
        pending_credit="50.00",
        reserved="40.00",
        hold="25.00",
        overdraft="20.00",
    )

    assert balance_snapshot.is_reconciled is True
    assert balance_snapshot.reconciliation_difference == (
        Money.of("0", "AUD")
    )


def test_unreconciled_snapshot() -> None:
    balance_snapshot = snapshot(
        posted="100.00",
        available="70.00",
        reserved="25.00",
    )

    assert balance_snapshot.expected_available == (
        Money.of("75.00", "AUD")
    )
    assert balance_snapshot.reconciliation_difference == (
        Money.of("-5.00", "AUD")
    )
    assert balance_snapshot.is_reconciled is False


def test_reconcile_returns_complete_report() -> None:
    result = snapshot().reconcile()

    assert isinstance(result, BalanceReconciliation)
    assert result.currency == Currency.of("AUD")
    assert result.posted == Money.of("100.00", "AUD")
    assert result.available == Money.of("75.00", "AUD")
    assert result.reserved == Money.of("25.00", "AUD")
    assert result.expected_available == (
        Money.of("75.00", "AUD")
    )
    assert result.difference == Money.of("0", "AUD")
    assert result.is_reconciled is True


def test_require_reconciled_returns_report() -> None:
    result = snapshot().require_reconciled()

    assert result.is_reconciled is True


def test_require_reconciled_rejects_difference() -> None:
    balance_snapshot = snapshot(
        posted="100.00",
        available="70.00",
        reserved="25.00",
    )

    with pytest.raises(
        ValueError,
        match=r"difference=-5\.00 AUD",
    ):
        balance_snapshot.require_reconciled()


def test_uncleared_is_informational_only() -> None:
    balance_snapshot = snapshot(
        posted="100.00",
        available="75.00",
        reserved="25.00",
        uncleared="500.00",
    )

    assert balance_snapshot.uncleared == (
        Money.of("500.00", "AUD")
    )
    assert balance_snapshot.expected_available == (
        Money.of("75.00", "AUD")
    )
    assert balance_snapshot.is_reconciled is True


def test_negative_posted_and_available_values() -> None:
    balance_snapshot = snapshot(
        posted="-50.00",
        available="-75.00",
        reserved="25.00",
    )

    assert balance_snapshot.expected_available == (
        Money.of("-75.00", "AUD")
    )
    assert balance_snapshot.is_reconciled is True


def test_overdraft_increases_expected_availability() -> None:
    balance_snapshot = snapshot(
        posted="-50.00",
        available="-25.00",
        reserved=None,
        overdraft="25.00",
    )

    assert balance_snapshot.expected_available == (
        Money.of("-25.00", "AUD")
    )
    assert balance_snapshot.is_reconciled is True


@pytest.mark.parametrize(
    ("currency", "posted", "available", "reserved"),
    [
        ("AUD", "100.125", "75.125", "25"),
        ("USD", "66.175", "56.175", "10"),
        ("BIF", "1234.5", "1000.5", "234"),
        ("RWF", "1234.5", "1000.5", "234"),
        ("UGX", "1234.5", "1000.5", "234"),
    ],
)
def test_reconciliation_preserves_money_precision(
    currency: str,
    posted: str,
    available: str,
    reserved: str,
) -> None:
    balance_snapshot = snapshot(
        posted=posted,
        available=available,
        reserved=reserved,
        currency=currency,
    )

    assert balance_snapshot.currency == Currency.of(
        currency
    )
    assert balance_snapshot.is_reconciled is True


def test_reconciliation_canonical_dict() -> None:
    payload = snapshot().reconcile().canonical_dict()

    assert payload == {
        "currency": "AUD",
        "posted": "100.00",
        "available": "75.00",
        "pending_debit": "0.00",
        "pending_credit": "0.00",
        "reserved": "25.00",
        "hold": "0.00",
        "overdraft": "0.00",
        "uncleared": "0.00",
        "expected_available": "75.00",
        "difference": "0.00",
        "is_reconciled": True,
    }


def test_reconciliation_contains_no_mutation_authority() -> None:
    result = snapshot().reconcile()

    for forbidden in (
        "post",
        "debit",
        "credit",
        "apply",
        "reserve",
        "release",
        "settle",
        "mutate_balance",
        "replace_components",
        "save",
        "repository",
        "database",
        "provider_client",
    ):
        assert not hasattr(result, forbidden)


def test_snapshot_reconciliation_methods_are_read_only() -> None:
    balance_snapshot = snapshot()
    original_payload = balance_snapshot.canonical_dict()

    balance_snapshot.reconcile()
    balance_snapshot.require_reconciled()

    assert balance_snapshot.canonical_dict() == (
        original_payload
    )
    assert balance_snapshot.version == 1


def test_balance_snapshot_module_contract() -> None:
    from afritech.novapay.domain import balance_snapshot

    assert balance_snapshot.__all__ == [
        "BalanceComponent",
        "BalanceComponentType",
        "BalanceReconciliation",
        "BalanceSnapshot",
        "BalanceSnapshotHistory",
        "BalanceSnapshotHistoryId",
        "BalanceSnapshotId",
        "BalanceSnapshotMetadata",
        "BalanceSnapshotStatus",
        "BalanceSnapshotType",
        "LedgerPosition",
    ]
