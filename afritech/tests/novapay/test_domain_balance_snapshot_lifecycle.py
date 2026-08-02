from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay.domain.balance_snapshot import (
    BalanceComponent,
    BalanceSnapshot,
    BalanceSnapshotHistory,
    BalanceSnapshotStatus,
    LedgerPosition,
)
from afritech.novapay.domain.money import Money


BASE_TIME = datetime(
    2026,
    8,
    2,
    10,
    0,
    tzinfo=timezone.utc,
)


def snapshot(
    sequence: int,
    *,
    status: object = BalanceSnapshotStatus.CURRENT,
    currency: str = "AUD",
    wallet_id: str = "wallet-001",
    ledger_source: str = "canonical_ledger",
    as_of: datetime | None = None,
    captured_at: datetime | None = None,
    snapshot_id: str | None = None,
) -> BalanceSnapshot:
    normalized_as_of = (
        BASE_TIME + timedelta(minutes=sequence)
        if as_of is None
        else as_of
    )
    normalized_captured_at = (
        normalized_as_of
        if captured_at is None
        else captured_at
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
        as_of=normalized_as_of,
        captured_at=normalized_captured_at,
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
                status=BalanceSnapshotStatus.CURRENT,
            ),
        ),
        metadata={
            "projection": "canonical-ledger",
        },
    )


def test_mark_snapshot_superseded() -> None:
    original = snapshot(20)
    occurred_at = original.captured_at + timedelta(seconds=1)

    updated = original.mark_superseded(
        reason="newer ledger projection",
        occurred_at=occurred_at,
    )

    assert original.status is BalanceSnapshotStatus.CURRENT
    assert original.version == 1

    assert updated.status is (
        BalanceSnapshotStatus.SUPERSEDED
    )
    assert updated.version == 2
    assert updated.metadata.values[
        "lifecycle_reason"
    ] == "newer ledger projection"
    assert updated.metadata.values[
        "previous_status"
    ] == "current"
    assert updated.metadata.values[
        "current_status"
    ] == "superseded"


def test_mark_snapshot_stale() -> None:
    original = snapshot(20)

    updated = original.mark_stale(
        reason="projection lag detected",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
    )

    assert updated.status is BalanceSnapshotStatus.STALE
    assert updated.version == 2


def test_mark_reconciliation_required() -> None:
    original = snapshot(20)

    updated = original.mark_reconciliation_required(
        reason="balance difference detected",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
    )

    assert updated.status is (
        BalanceSnapshotStatus.RECONCILIATION_REQUIRED
    )


def test_invalidate_current_snapshot() -> None:
    original = snapshot(20)

    updated = original.invalidate(
        reason="source projection invalid",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
    )

    assert updated.status is (
        BalanceSnapshotStatus.INVALIDATED
    )


def test_stale_can_require_reconciliation() -> None:
    stale = snapshot(20).mark_stale(
        reason="projection lag",
        occurred_at=(
            snapshot(20).captured_at
            + timedelta(seconds=1)
        ),
    )

    updated = stale.mark_reconciliation_required(
        reason="manual review required",
        occurred_at=(
            stale.captured_at + timedelta(seconds=2)
        ),
    )

    assert updated.status is (
        BalanceSnapshotStatus.RECONCILIATION_REQUIRED
    )


def test_stale_can_be_invalidated() -> None:
    original = snapshot(20)
    stale = original.mark_stale(
        reason="stale",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
    )

    invalidated = stale.invalidate(
        reason="cannot reconcile",
        occurred_at=(
            original.captured_at + timedelta(seconds=2)
        ),
    )

    assert invalidated.status is (
        BalanceSnapshotStatus.INVALIDATED
    )


def test_reconciliation_required_can_be_invalidated() -> None:
    original = snapshot(20)
    review = original.mark_reconciliation_required(
        reason="difference",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
    )

    invalidated = review.invalidate(
        reason="projection rejected",
        occurred_at=(
            original.captured_at + timedelta(seconds=2)
        ),
    )

    assert invalidated.status is (
        BalanceSnapshotStatus.INVALIDATED
    )


@pytest.mark.parametrize(
    "terminal_status",
    [
        BalanceSnapshotStatus.SUPERSEDED,
        BalanceSnapshotStatus.INVALIDATED,
    ],
)
def test_terminal_snapshot_rejects_further_transitions(
    terminal_status: BalanceSnapshotStatus,
) -> None:
    original = snapshot(20)

    if terminal_status is BalanceSnapshotStatus.SUPERSEDED:
        terminal = original.mark_superseded(
            reason="new snapshot",
            occurred_at=(
                original.captured_at
                + timedelta(seconds=1)
            ),
        )
    else:
        terminal = original.invalidate(
            reason="invalid projection",
            occurred_at=(
                original.captured_at
                + timedelta(seconds=1)
            ),
        )

    with pytest.raises(
        ValueError,
        match="invalid balance snapshot status transition",
    ):
        terminal.mark_stale(
            reason="not allowed",
            occurred_at=(
                original.captured_at
                + timedelta(seconds=2)
            ),
        )


def test_lifecycle_rejects_earlier_timestamp() -> None:
    original = snapshot(20)

    with pytest.raises(
        ValueError,
        match="must not be earlier than captured_at",
    ):
        original.mark_stale(
            reason="invalid timestamp",
            occurred_at=(
                original.captured_at
                - timedelta(seconds=1)
            ),
        )


def test_lifecycle_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        snapshot(20).mark_stale(
            reason="invalid timestamp",
            occurred_at=datetime(2026, 8, 2, 10, 30),
        )


def test_lifecycle_metadata_merges_extra_values() -> None:
    original = snapshot(20)

    updated = original.mark_stale(
        reason="projection delayed",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
        metadata={
            "incident_id": "incident-001",
        },
    )

    assert updated.metadata.values[
        "incident_id"
    ] == "incident-001"


def test_snapshot_metadata_update_is_immutable() -> None:
    original = snapshot(20)

    updated = original.update_metadata(
        {
            "projection": "ledger",
            "reviewed": True,
        }
    )

    assert original.metadata.values == {}
    assert updated.metadata.values == {
        "projection": "ledger",
        "reviewed": True,
    }
    assert updated.version == 2


def test_snapshot_metadata_update_rejects_no_op() -> None:
    original = snapshot(20).update_metadata(
        {
            "projection": "ledger",
        }
    )

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        original.update_metadata(
            {
                "projection": "ledger",
            }
        )


def test_history_advance_adds_new_current_snapshot() -> None:
    original = history()
    incoming = snapshot(30)

    updated = original.advance(incoming)

    assert original.size == 2
    assert original.version == 1
    assert original.current is not None
    assert original.current.ledger_position.sequence == 20

    assert updated.size == 3
    assert updated.version == 2
    assert updated.current is incoming
    assert updated.latest is incoming
    assert updated.snapshots[-2].status is (
        BalanceSnapshotStatus.SUPERSEDED
    )


def test_history_advance_records_supersession_reference() -> None:
    updated = history().advance(snapshot(30))

    previous = updated.snapshots[-2]

    assert previous.metadata.values[
        "superseded_by_snapshot_id"
    ] == "balance-snapshot-030"
    assert previous.metadata.values[
        "superseded_by_ledger_position"
    ] == 30


def test_history_advance_increments_versions_once() -> None:
    original = history()
    previous_current = original.current

    assert previous_current is not None
    assert previous_current.version == 1

    updated = original.advance(snapshot(30))

    assert updated.version == 2
    assert updated.snapshots[-2].version == 2
    assert updated.latest.version == 1


def test_history_advance_preserves_existing_history() -> None:
    original = history()
    updated = original.advance(snapshot(30))

    assert original.snapshots[0] is updated.snapshots[0]
    assert original.snapshots[0].status is (
        BalanceSnapshotStatus.SUPERSEDED
    )


def test_history_advance_when_latest_is_not_current() -> None:
    original = BalanceSnapshotHistory.create(
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

    updated = original.advance(snapshot(30))

    assert updated.size == 3
    assert updated.snapshots[-2].status is (
        BalanceSnapshotStatus.STALE
    )
    assert updated.current is updated.latest


def test_history_advance_rejects_non_snapshot() -> None:
    with pytest.raises(
        TypeError,
        match="requires a BalanceSnapshot",
    ):
        history().advance("invalid")  # type: ignore[arg-type]


def test_history_advance_requires_current_snapshot() -> None:
    incoming = snapshot(
        30,
        status=BalanceSnapshotStatus.STALE,
    )

    with pytest.raises(
        ValueError,
        match="must be current",
    ):
        history().advance(incoming)


@pytest.mark.parametrize(
    "sequence",
    [
        20,
        15,
    ],
)
def test_history_advance_requires_higher_position(
    sequence: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be greater",
    ):
        history().advance(
            snapshot(
                sequence,
                snapshot_id=f"incoming-{sequence}",
            )
        )


def test_history_advance_rejects_duplicate_id() -> None:
    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        history().advance(
            snapshot(
                30,
                snapshot_id="balance-snapshot-020",
            )
        )


def test_history_advance_rejects_backward_time() -> None:
    incoming = snapshot(
        30,
        as_of=BASE_TIME,
        captured_at=BASE_TIME,
    )

    with pytest.raises(
        ValueError,
        match="must not move backwards",
    ):
        history().advance(incoming)


def test_history_advance_rejects_mixed_currency() -> None:
    with pytest.raises(
        ValueError,
        match="currency must match",
    ):
        history().advance(
            snapshot(
                30,
                currency="USD",
            )
        )


def test_history_advance_rejects_mixed_owner() -> None:
    with pytest.raises(
        ValueError,
        match="owner must match",
    ):
        history().advance(
            snapshot(
                30,
                wallet_id="wallet-002",
            )
        )


def test_history_advance_rejects_mixed_ledger_source() -> None:
    with pytest.raises(
        ValueError,
        match="ledger source must match",
    ):
        history().advance(
            snapshot(
                30,
                ledger_source="other_ledger",
            )
        )


def test_history_advance_rejects_late_transition_time() -> None:
    incoming = snapshot(30)

    with pytest.raises(
        ValueError,
        match="must not be later",
    ):
        history().advance(
            incoming,
            occurred_at=(
                incoming.captured_at + timedelta(seconds=1)
            ),
        )


def test_history_advance_merges_metadata() -> None:
    updated = history().advance(
        snapshot(30),
        metadata={
            "projection_run_id": "run-030",
        },
    )

    assert updated.metadata.values[
        "projection"
    ] == "canonical-ledger"
    assert updated.metadata.values[
        "projection_run_id"
    ] == "run-030"
    assert updated.metadata.values[
        "latest_snapshot_id"
    ] == "balance-snapshot-030"
    assert updated.metadata.values[
        "latest_ledger_position"
    ] == 30


def test_history_metadata_update_is_immutable() -> None:
    original = history()

    updated = original.update_metadata(
        {
            "projection": "canonical-ledger",
            "reviewed": True,
        }
    )

    assert original.version == 1
    assert updated.version == 2
    assert updated.metadata.values[
        "reviewed"
    ] is True


def test_history_metadata_update_rejects_no_op() -> None:
    original = history()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        original.update_metadata(
            {
                "projection": "canonical-ledger",
            }
        )


def test_lifecycle_preserves_financial_values() -> None:
    original = snapshot(20)

    updated = original.mark_stale(
        reason="projection delay",
        occurred_at=(
            original.captured_at + timedelta(seconds=1)
        ),
    )

    assert updated.currency == original.currency
    assert updated.components == original.components
    assert updated.posted == original.posted
    assert updated.available == original.available
    assert (
        updated.ledger_position
        == original.ledger_position
    )
    assert updated.is_reconciled is original.is_reconciled


def test_history_advance_contains_no_ledger_authority() -> None:
    updated = history().advance(snapshot(30))

    for forbidden in (
        "post",
        "debit",
        "credit",
        "apply_posting",
        "mutate_ledger",
        "calculate_balance",
        "settle",
        "save",
        "repository",
        "database",
        "provider_client",
    ):
        assert not hasattr(updated, forbidden)
