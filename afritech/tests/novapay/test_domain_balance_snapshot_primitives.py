from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from enum import Enum
from types import MappingProxyType

import pytest

from afritech.novapay.domain.balance_snapshot import (
    BalanceComponent,
    BalanceComponentType,
    BalanceSnapshotId,
    BalanceSnapshotMetadata,
    BalanceSnapshotStatus,
    BalanceSnapshotType,
    LedgerPosition,
)
from afritech.novapay.domain.ledger_account import (
    LedgerAccountId,
)
from afritech.novapay.domain.money import (
    Currency,
    Money,
)
from afritech.novapay.domain.wallet import WalletId


def test_balance_snapshot_id_normalizes() -> None:
    identifier = BalanceSnapshotId.of(
        " balance-snapshot-001 "
    )

    assert identifier.value == "balance-snapshot-001"
    assert identifier.canonical() == "balance-snapshot-001"
    assert str(identifier) == "balance-snapshot-001"


def test_balance_snapshot_id_is_immutable() -> None:
    identifier = BalanceSnapshotId(
        "balance-snapshot-001"
    )

    with pytest.raises(FrozenInstanceError):
        identifier.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
    ],
)
def test_balance_snapshot_id_rejects_empty(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        BalanceSnapshotId(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        True,
    ],
)
def test_balance_snapshot_id_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        BalanceSnapshotId.of(value)


@pytest.mark.parametrize(
    "enum_type",
    [
        BalanceSnapshotType,
        BalanceSnapshotStatus,
        BalanceComponentType,
    ],
)
def test_balance_enums_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


@pytest.mark.parametrize(
    ("enum_type", "raw", "expected"),
    [
        (
            BalanceSnapshotType,
            " FINANCIAL ACCOUNT ",
            BalanceSnapshotType.FINANCIAL_ACCOUNT,
        ),
        (
            BalanceSnapshotStatus,
            " reconciliation-required ",
            BalanceSnapshotStatus.RECONCILIATION_REQUIRED,
        ),
        (
            BalanceComponentType,
            " pending debit ",
            BalanceComponentType.PENDING_DEBIT,
        ),
    ],
)
def test_balance_enums_parse_normalized_values(
    enum_type: object,
    raw: str,
    expected: object,
) -> None:
    assert enum_type.parse(raw) is expected  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "enum_type",
    [
        BalanceSnapshotType,
        BalanceSnapshotStatus,
        BalanceComponentType,
    ],
)
def test_balance_enums_reject_unknown_values(
    enum_type: object,
) -> None:
    with pytest.raises(ValueError):
        enum_type.parse("unknown")  # type: ignore[attr-defined]


def test_ledger_position_normalizes() -> None:
    position = LedgerPosition.of(
        42,
        source=" Canonical Ledger ",
    )

    assert position.sequence == 42
    assert position.source == "canonical_ledger"
    assert position.canonical_dict() == {
        "sequence": 42,
        "source": "canonical_ledger",
    }


def test_ledger_position_is_immutable() -> None:
    position = LedgerPosition.of(42)

    with pytest.raises(FrozenInstanceError):
        position.sequence = 43  # type: ignore[misc]


@pytest.mark.parametrize(
    "value",
    [
        -1,
        -100,
    ],
)
def test_ledger_position_rejects_negative_sequence(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 0",
    ):
        LedgerPosition.of(value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        "1",
        1.0,
        None,
    ],
)
def test_ledger_position_rejects_non_integer(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        LedgerPosition.of(value)


def test_ledger_position_ordering_helper() -> None:
    first = LedgerPosition.of(10)
    second = LedgerPosition.of(11)

    assert second.is_after(first) is True
    assert first.is_after(second) is False


def test_ledger_position_rejects_cross_source_ordering() -> None:
    first = LedgerPosition.of(
        10,
        source="ledger-a",
    )
    second = LedgerPosition.of(
        11,
        source="ledger-b",
    )

    with pytest.raises(
        ValueError,
        match="different sources",
    ):
        second.is_after(first)


def test_balance_snapshot_metadata_normalizes_keys() -> None:
    metadata = BalanceSnapshotMetadata(
        {
            " Projection Source ": "ledger",
            " Reconciled ": True,
        }
    )

    assert metadata.values == {
        "projection_source": "ledger",
        "reconciled": True,
    }
    assert isinstance(
        metadata.values,
        MappingProxyType,
    )


def test_balance_snapshot_metadata_is_defensive() -> None:
    source = {
        "projection_source": "ledger",
    }

    metadata = BalanceSnapshotMetadata(source)
    source["projection_source"] = "changed"

    assert metadata.values == {
        "projection_source": "ledger",
    }


def test_balance_snapshot_metadata_updates_immutably() -> None:
    original = BalanceSnapshotMetadata(
        {
            "source": "ledger",
        }
    )

    updated = original.with_updates(
        {
            "reconciled": True,
        }
    )

    assert original.values == {
        "source": "ledger",
    }
    assert updated.values == {
        "reconciled": True,
        "source": "ledger",
    }


@pytest.mark.parametrize(
    "key",
    [
        "access_token",
        "password",
        "private_key",
        "card_number",
    ],
)
def test_balance_snapshot_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        BalanceSnapshotMetadata(
            {
                key: "secret",
            }
        )


def test_balance_snapshot_metadata_rejects_unsupported_values() -> None:
    with pytest.raises(
        TypeError,
        match="unsupported value type",
    ):
        BalanceSnapshotMetadata(
            {
                "unsupported": object(),
            }
        )


def test_create_balance_component() -> None:
    component = BalanceComponent.create(
        component_type=" posted ",
        amount=Money.of("100.125", "AUD"),
        ledger_account_id="ledger-account-001",
        wallet_id="wallet-001",
        reference_id=" journal-entry-001 ",
        metadata={
            "source": "journal",
        },
    )

    assert component.component_type is (
        BalanceComponentType.POSTED
    )
    assert component.amount == Money.of("100.125", "AUD")
    assert component.currency == Currency.of("AUD")
    assert component.decimal_amount == Decimal("100.12")
    assert component.ledger_account_id == (
        LedgerAccountId("ledger-account-001")
    )
    assert component.wallet_id == WalletId("wallet-001")
    assert component.reference_id == "journal-entry-001"
    assert component.metadata.values == {
        "source": "journal",
    }


def test_balance_component_is_immutable() -> None:
    component = BalanceComponent.create(
        component_type="available",
        amount=Money.of("10.00", "USD"),
    )

    with pytest.raises(FrozenInstanceError):
        component.reference_id = "changed"  # type: ignore[misc]


def test_balance_component_uses_slots() -> None:
    component = BalanceComponent.create(
        component_type="available",
        amount=Money.of("10.00", "USD"),
    )

    assert not hasattr(component, "__dict__")


def test_balance_component_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(BalanceComponent)
    } == {
        "component_type",
        "amount",
        "ledger_account_id",
        "wallet_id",
        "reference_id",
        "metadata",
    }


def test_balance_component_requires_money() -> None:
    with pytest.raises(
        TypeError,
        match="amount must be Money",
    ):
        BalanceComponent(
            component_type=BalanceComponentType.POSTED,
            amount=Decimal("10.00"),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("code", "raw", "expected"),
    [
        ("AUD", "10.125", "10.12"),
        ("USD", "66.175", "66.18"),
        ("BIF", "1234.5", "1234"),
        ("RWF", "1234.5", "1234"),
        ("UGX", "1234.5", "1234"),
    ],
)
def test_balance_component_preserves_money_precision(
    code: str,
    raw: str,
    expected: str,
) -> None:
    component = BalanceComponent.create(
        component_type="posted",
        amount=Money.of(raw, code),
    )

    assert component.currency == Currency.of(code)
    assert str(component.decimal_amount) == expected


def test_balance_component_allows_negative_projection_values() -> None:
    component = BalanceComponent.create(
        component_type="posted",
        amount=Money.of("-25.50", "AUD"),
    )

    assert component.decimal_amount == Decimal("-25.50")


def test_balance_component_canonical_dict() -> None:
    component = BalanceComponent.create(
        component_type="reserved",
        amount=Money.of("25.00", "AUD"),
        ledger_account_id="ledger-account-001",
        wallet_id="wallet-001",
        reference_id="hold-001",
        metadata={
            "reason": "card authorisation",
        },
    )

    assert component.canonical_dict() == {
        "component_type": "reserved",
        "amount": "25.00",
        "currency": "AUD",
        "ledger_account_id": "ledger-account-001",
        "wallet_id": "wallet-001",
        "reference_id": "hold-001",
        "metadata": {
            "reason": "card authorisation",
        },
    }


def test_balance_component_has_no_mutation_authority() -> None:
    component = BalanceComponent.create(
        component_type="posted",
        amount=Money.of("100.00", "AUD"),
    )

    for forbidden in (
        "post",
        "debit",
        "credit",
        "apply",
        "settle",
        "reserve",
        "release",
        "mutate_balance",
        "save",
        "repository",
        "database",
    ):
        assert not hasattr(component, forbidden)


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


def test_balance_snapshot_aggregate_is_available_in_module() -> None:
    from afritech.novapay.domain import balance_snapshot

    assert hasattr(
        balance_snapshot,
        "BalanceSnapshot",
    )
