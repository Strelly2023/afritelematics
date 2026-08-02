from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.balance_snapshot import (
    BalanceComponent,
    BalanceComponentType,
    BalanceSnapshot,
    BalanceSnapshotId,
    BalanceSnapshotMetadata,
    BalanceSnapshotStatus,
    BalanceSnapshotType,
    LedgerPosition,
)
from afritech.novapay.domain.customer import CustomerId
from afritech.novapay.domain.financial_account import (
    FinancialAccountId,
)
from afritech.novapay.domain.journal_entry import (
    JournalEntryId,
)
from afritech.novapay.domain.ledger_account import (
    LedgerAccountId,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)
from afritech.novapay.domain.wallet import WalletId


AS_OF = datetime(
    2026,
    8,
    2,
    8,
    30,
    tzinfo=timezone.utc,
)
CAPTURED_AT = AS_OF + timedelta(seconds=5)


def component(
    component_type: object,
    amount: str,
    *,
    currency: str = "AUD",
    wallet_id: str | None = "wallet-001",
    ledger_account_id: str | None = (
        "ledger-account-001"
    ),
) -> BalanceComponent:
    return BalanceComponent.create(
        component_type=component_type,
        amount=Money.of(amount, currency),
        wallet_id=wallet_id,
        ledger_account_id=ledger_account_id,
    )


def wallet_snapshot(
    **overrides: object,
) -> BalanceSnapshot:
    values: dict[str, object] = {
        "snapshot_id": "balance-snapshot-001",
        "snapshot_type": "wallet",
        "status": "current",
        "currency": "AUD",
        "components": (
            component("posted", "100.00"),
            component("available", "75.00"),
            component("reserved", "25.00"),
        ),
        "ledger_position": 42,
        "as_of": AS_OF,
        "captured_at": CAPTURED_AT,
        "customer_id": "customer-001",
        "financial_account_id": (
            "financial-account-001"
        ),
        "wallet_id": "wallet-001",
        "ledger_account_id": (
            "ledger-account-001"
        ),
        "source_journal_entry_id": (
            "journal-entry-001"
        ),
        "source_reference_id": "projection-run-001",
        "metadata": {
            "projection_source": "canonical-ledger",
        },
    }
    values.update(overrides)

    return BalanceSnapshot.create(
        **values,  # type: ignore[arg-type]
    )


def test_create_wallet_balance_snapshot() -> None:
    snapshot = wallet_snapshot()

    assert snapshot.snapshot_id == BalanceSnapshotId(
        "balance-snapshot-001"
    )
    assert snapshot.snapshot_type is (
        BalanceSnapshotType.WALLET
    )
    assert snapshot.status is (
        BalanceSnapshotStatus.CURRENT
    )
    assert snapshot.currency == Currency.of("AUD")
    assert snapshot.ledger_position == LedgerPosition.of(
        42
    )
    assert snapshot.as_of == AS_OF
    assert snapshot.captured_at == CAPTURED_AT
    assert snapshot.customer_id == CustomerId(
        "customer-001"
    )
    assert snapshot.financial_account_id == (
        FinancialAccountId(
            "financial-account-001"
        )
    )
    assert snapshot.wallet_id == WalletId("wallet-001")
    assert snapshot.ledger_account_id == (
        LedgerAccountId("ledger-account-001")
    )
    assert snapshot.source_journal_entry_id == (
        JournalEntryId("journal-entry-001")
    )
    assert snapshot.source_reference_id == (
        "projection-run-001"
    )
    assert snapshot.metadata.values == {
        "projection_source": "canonical-ledger",
    }
    assert snapshot.version == 1
    assert snapshot.is_current is True


def test_snapshot_is_immutable() -> None:
    snapshot = wallet_snapshot()

    with pytest.raises(FrozenInstanceError):
        snapshot.version = 2  # type: ignore[misc]


def test_snapshot_uses_slots() -> None:
    assert not hasattr(wallet_snapshot(), "__dict__")


def test_snapshot_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(BalanceSnapshot)
    } == {
        "snapshot_id",
        "snapshot_type",
        "status",
        "currency",
        "components",
        "ledger_position",
        "as_of",
        "captured_at",
        "customer_id",
        "financial_account_id",
        "wallet_id",
        "ledger_account_id",
        "source_journal_entry_id",
        "source_reference_id",
        "metadata",
        "version",
    }


def test_components_are_deterministically_sorted() -> None:
    snapshot = wallet_snapshot(
        components=(
            component("reserved", "25.00"),
            component("posted", "100.00"),
            component("available", "75.00"),
        )
    )

    assert tuple(
        item.component_type
        for item in snapshot.components
    ) == (
        BalanceComponentType.AVAILABLE,
        BalanceComponentType.POSTED,
        BalanceComponentType.RESERVED,
    )


def test_snapshot_requires_components() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one component",
    ):
        wallet_snapshot(components=())


def test_snapshot_rejects_non_component_values() -> None:
    with pytest.raises(
        TypeError,
        match="BalanceComponent",
    ):
        wallet_snapshot(
            components=(
                component("posted", "100.00"),
                component("available", "75.00"),
                "reserved",
            )
        )


def test_snapshot_requires_posted_component() -> None:
    with pytest.raises(
        ValueError,
        match="posted",
    ):
        wallet_snapshot(
            components=(
                component("available", "75.00"),
            )
        )


def test_snapshot_requires_available_component() -> None:
    with pytest.raises(
        ValueError,
        match="available",
    ):
        wallet_snapshot(
            components=(
                component("posted", "100.00"),
            )
        )


def test_snapshot_rejects_duplicate_component_types() -> None:
    with pytest.raises(
        ValueError,
        match="component types must be unique",
    ):
        wallet_snapshot(
            components=(
                component("posted", "100.00"),
                component("available", "75.00"),
                component("available", "70.00"),
            )
        )


def test_snapshot_rejects_mixed_currencies() -> None:
    with pytest.raises(
        ValueError,
        match="snapshot currency",
    ):
        wallet_snapshot(
            components=(
                component("posted", "100.00"),
                component(
                    "available",
                    "75.00",
                    currency="USD",
                ),
            )
        )


@pytest.mark.parametrize(
    ("snapshot_type", "required_field"),
    [
        ("wallet", "wallet_id"),
        ("financial_account", "financial_account_id"),
        ("ledger_account", "ledger_account_id"),
        ("customer", "customer_id"),
    ],
)
def test_snapshot_type_requires_owner(
    snapshot_type: str,
    required_field: str,
) -> None:
    overrides: dict[str, object] = {
        "snapshot_type": snapshot_type,
        required_field: None,
    }

    with pytest.raises(
        ValueError,
        match="requires",
    ):
        wallet_snapshot(**overrides)


def test_treasury_snapshot_does_not_require_account_owner() -> None:
    snapshot = wallet_snapshot(
        snapshot_type="treasury",
        wallet_id=None,
        financial_account_id=None,
        ledger_account_id=None,
        customer_id=None,
        components=(
            component(
                "posted",
                "1000.00",
                wallet_id=None,
                ledger_account_id=None,
            ),
            component(
                "available",
                "900.00",
                wallet_id=None,
                ledger_account_id=None,
            ),
        ),
    )

    assert snapshot.snapshot_type is (
        BalanceSnapshotType.TREASURY
    )


def test_component_wallet_must_match_snapshot_wallet() -> None:
    with pytest.raises(
        ValueError,
        match="component wallet id must match",
    ):
        wallet_snapshot(
            components=(
                component(
                    "posted",
                    "100.00",
                    wallet_id="wallet-other",
                ),
                component("available", "75.00"),
            )
        )


def test_component_ledger_account_must_match_snapshot() -> None:
    with pytest.raises(
        ValueError,
        match="component ledger account id must match",
    ):
        wallet_snapshot(
            components=(
                component(
                    "posted",
                    "100.00",
                    ledger_account_id=(
                        "ledger-account-other"
                    ),
                ),
                component("available", "75.00"),
            )
        )


def test_captured_at_defaults_to_as_of() -> None:
    snapshot = wallet_snapshot(
        captured_at=None,
    )

    assert snapshot.captured_at == snapshot.as_of


def test_snapshot_rejects_captured_at_before_as_of() -> None:
    with pytest.raises(
        ValueError,
        match="captured_at must not be earlier",
    ):
        wallet_snapshot(
            captured_at=AS_OF - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "as_of",
        "captured_at",
    ],
)
def test_snapshot_rejects_naive_datetime(
    field_name: str,
) -> None:
    overrides = {
        field_name: datetime(2026, 8, 2, 8, 30),
    }

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        wallet_snapshot(**overrides)


def test_snapshot_normalizes_datetime_to_utc() -> None:
    local_zone = timezone(timedelta(hours=10))
    local_as_of = datetime(
        2026,
        8,
        2,
        18,
        30,
        tzinfo=local_zone,
    )

    snapshot = wallet_snapshot(
        as_of=local_as_of,
        captured_at=local_as_of,
    )

    assert snapshot.as_of == AS_OF
    assert snapshot.as_of.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_snapshot_rejects_invalid_version(
    version: int,
) -> None:
    values = wallet_snapshot().canonical_dict()

    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        BalanceSnapshot(
            snapshot_id=BalanceSnapshotId(
                values["snapshot_id"]
            ),
            snapshot_type=BalanceSnapshotType.WALLET,
            status=BalanceSnapshotStatus.CURRENT,
            currency=Currency.of("AUD"),
            components=wallet_snapshot().components,
            ledger_position=LedgerPosition.of(42),
            as_of=AS_OF,
            captured_at=CAPTURED_AT,
            wallet_id=WalletId("wallet-001"),
            version=version,
        )


@pytest.mark.parametrize(
    "version",
    [
        True,
        "1",
        1.0,
        None,
    ],
)
def test_snapshot_rejects_non_integer_version(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="version must be an integer",
    ):
        BalanceSnapshot(
            snapshot_id=BalanceSnapshotId(
                "balance-snapshot-001"
            ),
            snapshot_type=BalanceSnapshotType.WALLET,
            status=BalanceSnapshotStatus.CURRENT,
            currency=Currency.of("AUD"),
            components=wallet_snapshot().components,
            ledger_position=LedgerPosition.of(42),
            as_of=AS_OF,
            captured_at=CAPTURED_AT,
            wallet_id=WalletId("wallet-001"),
            version=version,  # type: ignore[arg-type]
        )


def test_component_lookup() -> None:
    snapshot = wallet_snapshot()

    posted = snapshot.get_component("posted")

    assert posted is not None
    assert posted.amount == Money.of("100.00", "AUD")
    assert snapshot.get_component("hold") is None


def test_require_component_rejects_missing_type() -> None:
    with pytest.raises(
        KeyError,
        match="hold",
    ):
        wallet_snapshot().require_component("hold")


def test_posted_and_available_properties() -> None:
    snapshot = wallet_snapshot()

    assert snapshot.posted == Money.of("100.00", "AUD")
    assert snapshot.available == Money.of("75.00", "AUD")


def test_negative_projected_balance_is_preserved() -> None:
    snapshot = wallet_snapshot(
        components=(
            component("posted", "-50.00"),
            component("available", "-75.00"),
            component("overdraft", "25.00"),
        )
    )

    assert snapshot.posted.amount == Decimal("-50.00")
    assert snapshot.available.amount == Decimal("-75.00")


@pytest.mark.parametrize(
    ("currency_code", "raw", "expected"),
    [
        ("AUD", "66.175", "66.18"),
        ("BIF", "1234.5", "1234"),
        ("RWF", "1234.5", "1234"),
        ("UGX", "1234.5", "1234"),
    ],
)
def test_snapshot_preserves_money_precision(
    currency_code: str,
    raw: str,
    expected: str,
) -> None:
    snapshot = wallet_snapshot(
        currency=currency_code,
        components=(
            component(
                "posted",
                raw,
                currency=currency_code,
            ),
            component(
                "available",
                raw,
                currency=currency_code,
            ),
        ),
    )

    assert snapshot.currency == Currency.of(currency_code)
    assert str(snapshot.posted.amount) == expected
    assert str(snapshot.available.amount) == expected


def test_snapshot_canonical_dict() -> None:
    snapshot = wallet_snapshot()

    payload = snapshot.canonical_dict()

    assert list(payload) == [
        "snapshot_id",
        "snapshot_type",
        "status",
        "currency",
        "components",
        "ledger_position",
        "as_of",
        "captured_at",
        "customer_id",
        "financial_account_id",
        "wallet_id",
        "ledger_account_id",
        "source_journal_entry_id",
        "source_reference_id",
        "metadata",
        "version",
    ]
    assert payload["snapshot_id"] == (
        "balance-snapshot-001"
    )
    assert payload["snapshot_type"] == "wallet"
    assert payload["status"] == "current"
    assert payload["currency"] == "AUD"
    assert payload["ledger_position"] == {
        "sequence": 42,
        "source": "canonical_ledger",
    }
    assert payload["as_of"] == AS_OF.isoformat()
    assert payload["captured_at"] == (
        CAPTURED_AT.isoformat()
    )
    assert payload["customer_id"] == "customer-001"
    assert payload["financial_account_id"] == (
        "financial-account-001"
    )
    assert payload["wallet_id"] == "wallet-001"
    assert payload["ledger_account_id"] == (
        "ledger-account-001"
    )
    assert payload["source_journal_entry_id"] == (
        "journal-entry-001"
    )
    assert payload["source_reference_id"] == (
        "projection-run-001"
    )
    assert payload["metadata"] == {
        "projection_source": "canonical-ledger",
    }
    assert payload["version"] == 1


def test_snapshot_canonical_dict_is_fresh() -> None:
    snapshot = wallet_snapshot()

    first = snapshot.canonical_dict()
    second = snapshot.canonical_dict()

    assert first == second
    assert first is not second
    assert first["components"] is not second["components"]
    assert first["metadata"] is not second["metadata"]


def test_snapshot_contains_no_mutation_authority() -> None:
    snapshot = wallet_snapshot()

    for forbidden in (
        "post",
        "debit",
        "credit",
        "apply",
        "settle",
        "reserve",
        "release",
        "mutate_balance",
        "calculate_balance",
        "recalculate",
        "save",
        "repository",
        "database",
        "provider_client",
        "settlement_engine",
    ):
        assert not hasattr(snapshot, forbidden)


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
