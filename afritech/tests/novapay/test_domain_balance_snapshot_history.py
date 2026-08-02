from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay.domain.balance_snapshot import (
    BalanceComponent,
    BalanceSnapshot,
    BalanceSnapshotHistory,
    BalanceSnapshotHistoryId,
    BalanceSnapshotStatus,
    LedgerPosition,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)


BASE_TIME = datetime(
    2026,
    8,
    2,
    9,
    30,
    tzinfo=timezone.utc,
)


def snapshot(
    sequence: int,
    *,
    status: object,
    currency: str = "AUD",
    wallet_id: str = "wallet-001",
    ledger_source: str = "canonical_ledger",
    as_of: datetime | None = None,
    snapshot_id: str | None = None,
) -> BalanceSnapshot:
    timestamp = (
        BASE_TIME + timedelta(minutes=sequence)
        if as_of is None
        else as_of
    )

    return BalanceSnapshot(
        snapshot_id=(
            snapshot_id
            or f"balance-snapshot-{sequence:03d}"
        ),
        snapshot_type="wallet",
        status=status,
        currency=currency,
        components=(
            BalanceComponent.create(
                component_type="posted",
                amount=Money.of(
                    str(100 + sequence),
                    currency,
                ),
                wallet_id=wallet_id,
                ledger_account_id="ledger-account-001",
            ),
            BalanceComponent.create(
                component_type="available",
                amount=Money.of(
                    str(100 + sequence),
                    currency,
                ),
                wallet_id=wallet_id,
                ledger_account_id="ledger-account-001",
            ),
        ),
        ledger_position=LedgerPosition(
            sequence=sequence,
            source=ledger_source,
        ),
        as_of=timestamp,
        captured_at=timestamp,
        wallet_id=wallet_id,
        ledger_account_id="ledger-account-001",
        version=1,
    )


def history() -> BalanceSnapshotHistory:
    return BalanceSnapshotHistory.create(
        history_id="balance-history-wallet-001",
        snapshots=(
            snapshot(
                10,
                status=BalanceSnapshotStatus.SUPERSEDED,
            ),
            snapshot(
                20,
                status=BalanceSnapshotStatus.SUPERSEDED,
            ),
            snapshot(
                30,
                status=BalanceSnapshotStatus.CURRENT,
            ),
        ),
        metadata={
            "projection": "canonical-ledger",
        },
    )


def test_create_balance_snapshot_history() -> None:
    value = history()

    assert value.history_id == BalanceSnapshotHistoryId(
        "balance-history-wallet-001"
    )
    assert value.size == 3
    assert len(value) == 3
    assert value.snapshot_type.value == "wallet"
    assert value.currency == Currency.of("AUD")
    assert value.ledger_source == "canonical_ledger"
    assert value.metadata.values == {
        "projection": "canonical-ledger",
    }
    assert value.version == 1


def test_history_is_immutable() -> None:
    value = history()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_history_uses_slots() -> None:
    assert not hasattr(history(), "__dict__")


def test_history_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(BalanceSnapshotHistory)
    } == {
        "history_id",
        "snapshots",
        "metadata",
        "version",
    }


def test_history_requires_snapshots() -> None:
    with pytest.raises(
        ValueError,
        match="at least one snapshot",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-empty",
            snapshots=(),
        )


def test_history_rejects_non_snapshot_values() -> None:
    with pytest.raises(
        TypeError,
        match="BalanceSnapshot",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-invalid",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.CURRENT,
                ),
                "invalid",
            ),
        )


def test_history_orders_by_ledger_position() -> None:
    value = BalanceSnapshotHistory.create(
        history_id="balance-history-wallet-001",
        snapshots=(
            snapshot(
                30,
                status=BalanceSnapshotStatus.CURRENT,
            ),
            snapshot(
                10,
                status=BalanceSnapshotStatus.SUPERSEDED,
            ),
            snapshot(
                20,
                status=BalanceSnapshotStatus.SUPERSEDED,
            ),
        ),
    )

    assert tuple(
        item.ledger_position.sequence
        for item in value.snapshots
    ) == (10, 20, 30)


def test_history_rejects_duplicate_snapshot_ids() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate snapshot ids",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                    snapshot_id="duplicate",
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.CURRENT,
                    snapshot_id="duplicate",
                ),
            ),
        )


def test_history_rejects_duplicate_positions() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate ledger positions",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                    snapshot_id="snapshot-a",
                ),
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.CURRENT,
                    snapshot_id="snapshot-b",
                ),
            ),
        )


def test_history_rejects_mixed_currencies() -> None:
    with pytest.raises(
        ValueError,
        match="one canonical currency",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                    currency="AUD",
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.CURRENT,
                    currency="USD",
                ),
            ),
        )


def test_history_rejects_mixed_owners() -> None:
    with pytest.raises(
        ValueError,
        match="one balance owner",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                    wallet_id="wallet-001",
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.CURRENT,
                    wallet_id="wallet-002",
                ),
            ),
        )


def test_history_rejects_mixed_ledger_sources() -> None:
    with pytest.raises(
        ValueError,
        match="one ledger-position source",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                    ledger_source="ledger-a",
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.CURRENT,
                    ledger_source="ledger-b",
                ),
            ),
        )


def test_history_rejects_backward_as_of_time() -> None:
    with pytest.raises(
        ValueError,
        match="must not move backwards",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                    as_of=BASE_TIME + timedelta(hours=2),
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.CURRENT,
                    as_of=BASE_TIME + timedelta(hours=1),
                ),
            ),
        )


def test_history_allows_equal_as_of_time() -> None:
    timestamp = BASE_TIME

    value = BalanceSnapshotHistory.create(
        history_id="balance-history-wallet-001",
        snapshots=(
            snapshot(
                10,
                status=BalanceSnapshotStatus.SUPERSEDED,
                as_of=timestamp,
            ),
            snapshot(
                20,
                status=BalanceSnapshotStatus.CURRENT,
                as_of=timestamp,
            ),
        ),
    )

    assert value.size == 2


def test_history_rejects_multiple_current_snapshots() -> None:
    with pytest.raises(
        ValueError,
        match="at most one current snapshot",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.CURRENT,
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.CURRENT,
                ),
            ),
        )


def test_current_snapshot_must_be_latest() -> None:
    with pytest.raises(
        ValueError,
        match="must be the latest",
    ):
        BalanceSnapshotHistory.create(
            history_id="balance-history-wallet-001",
            snapshots=(
                snapshot(
                    10,
                    status=BalanceSnapshotStatus.CURRENT,
                ),
                snapshot(
                    20,
                    status=BalanceSnapshotStatus.SUPERSEDED,
                ),
            ),
        )


def test_latest_and_current_lookup() -> None:
    value = history()

    assert value.latest.ledger_position.sequence == 30
    assert value.current is value.latest


def test_history_without_current_snapshot() -> None:
    value = BalanceSnapshotHistory.create(
        history_id="balance-history-wallet-001",
        snapshots=(
            snapshot(
                10,
                status=BalanceSnapshotStatus.SUPERSEDED,
            ),
            snapshot(
                20,
                status=BalanceSnapshotStatus.STALE,
            ),
        ),
    )

    assert value.latest.status is BalanceSnapshotStatus.STALE
    assert value.current is None


def test_iteration_is_deterministic() -> None:
    assert tuple(
        item.ledger_position.sequence
        for item in history()
    ) == (10, 20, 30)


def test_get_and_require_by_id() -> None:
    value = history()

    found = value.get_by_id("balance-snapshot-020")

    assert found is not None
    assert found.ledger_position.sequence == 20
    assert value.require_by_id(
        "balance-snapshot-020"
    ) is found
    assert value.get_by_id("missing") is None

    with pytest.raises(KeyError, match="missing"):
        value.require_by_id("missing")


def test_at_position() -> None:
    value = history()

    found = value.at_position(20)

    assert found is not None
    assert found.snapshot_id.value == (
        "balance-snapshot-020"
    )
    assert value.at_position(25) is None


def test_at_or_before_position() -> None:
    value = history()

    assert value.at_or_before(
        position=25
    ).ledger_position.sequence == 20

    assert value.at_or_before(
        position=5
    ) is None


def test_at_or_before_time() -> None:
    value = history()
    query_time = BASE_TIME + timedelta(minutes=25)

    found = value.at_or_before(as_of=query_time)

    assert found is not None
    assert found.ledger_position.sequence == 20


def test_at_or_before_requires_exactly_one_query() -> None:
    value = history()

    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        value.at_or_before()

    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        value.at_or_before(
            position=20,
            as_of=BASE_TIME,
        )


def test_between_positions() -> None:
    value = history()

    result = value.between_positions(
        start=15,
        end=30,
    )

    assert tuple(
        item.ledger_position.sequence
        for item in result
    ) == (20, 30)


def test_between_positions_rejects_reverse_range() -> None:
    with pytest.raises(
        ValueError,
        match="end must not precede start",
    ):
        history().between_positions(
            start=30,
            end=10,
        )


def test_between_times() -> None:
    value = history()

    result = value.between_times(
        start=BASE_TIME + timedelta(minutes=15),
        end=BASE_TIME + timedelta(minutes=30),
    )

    assert tuple(
        item.ledger_position.sequence
        for item in result
    ) == (20, 30)


def test_between_times_rejects_reverse_range() -> None:
    with pytest.raises(
        ValueError,
        match="end must not precede start",
    ):
        history().between_times(
            start=BASE_TIME + timedelta(minutes=30),
            end=BASE_TIME + timedelta(minutes=10),
        )


def test_history_preserves_snapshot_reconciliation() -> None:
    for item in history():
        assert item.is_reconciled is True
        assert item.reconcile().is_reconciled is True


def test_history_preserves_canonical_money() -> None:
    value = history()

    assert value.currency == Currency.of("AUD")

    for item in value:
        assert item.posted.currency == value.currency
        assert item.available.currency == value.currency


def test_history_canonical_dict() -> None:
    payload = history().canonical_dict()

    assert list(payload) == [
        "history_id",
        "snapshot_type",
        "currency",
        "ledger_source",
        "snapshots",
        "metadata",
        "version",
    ]
    assert payload["history_id"] == (
        "balance-history-wallet-001"
    )
    assert payload["snapshot_type"] == "wallet"
    assert payload["currency"] == "AUD"
    assert payload["ledger_source"] == (
        "canonical_ledger"
    )
    assert [
        item["ledger_position"]["sequence"]
        for item in payload["snapshots"]
    ] == [10, 20, 30]
    assert payload["metadata"] == {
        "projection": "canonical-ledger",
    }
    assert payload["version"] == 1


def test_history_canonical_dict_is_fresh() -> None:
    value = history()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["snapshots"] is not second["snapshots"]
    assert first["metadata"] is not second["metadata"]


def test_history_contains_no_mutation_authority() -> None:
    value = history()

    for forbidden in (
        "append",
        "add_snapshot",
        "replace_snapshot",
        "post",
        "debit",
        "credit",
        "calculate_balance",
        "mutate_balance",
        "save",
        "repository",
        "database",
        "provider_client",
        "settlement_engine",
    ):
        assert not hasattr(value, forbidden)


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
