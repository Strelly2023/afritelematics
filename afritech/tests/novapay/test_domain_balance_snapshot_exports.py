from __future__ import annotations

import importlib

import pytest

import afritech.novapay as novapay
import afritech.novapay.domain as domain
from afritech.novapay.domain import balance_snapshot


BALANCE_SNAPSHOT_SYMBOLS = (
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
)


@pytest.mark.parametrize(
    "symbol",
    BALANCE_SNAPSHOT_SYMBOLS,
)
def test_domain_exports_balance_snapshot_symbol(
    symbol: str,
) -> None:
    assert hasattr(domain, symbol)
    assert getattr(
        domain,
        symbol,
    ) is getattr(
        balance_snapshot,
        symbol,
    )


@pytest.mark.parametrize(
    "symbol",
    BALANCE_SNAPSHOT_SYMBOLS,
)
def test_top_level_exports_balance_snapshot_symbol(
    symbol: str,
) -> None:
    assert hasattr(novapay, symbol)
    assert getattr(
        novapay,
        symbol,
    ) is getattr(
        balance_snapshot,
        symbol,
    )


@pytest.mark.parametrize(
    "symbol",
    BALANCE_SNAPSHOT_SYMBOLS,
)
def test_public_export_identity_is_consistent(
    symbol: str,
) -> None:
    module_value = getattr(
        balance_snapshot,
        symbol,
    )
    domain_value = getattr(domain, symbol)
    top_level_value = getattr(novapay, symbol)

    assert module_value is domain_value
    assert domain_value is top_level_value


@pytest.mark.parametrize(
    "symbol",
    BALANCE_SNAPSHOT_SYMBOLS,
)
def test_symbols_declared_in_all_contracts(
    symbol: str,
) -> None:
    assert symbol in balance_snapshot.__all__
    assert symbol in domain.__all__
    assert symbol in novapay.__all__


def test_balance_snapshot_module_contract_is_complete() -> None:
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


def test_public_all_contracts_are_sorted() -> None:
    assert domain.__all__ == sorted(domain.__all__)
    assert novapay.__all__ == sorted(novapay.__all__)


def test_public_all_contracts_have_no_duplicates() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))
    assert len(novapay.__all__) == len(set(novapay.__all__))


def test_existing_core_exports_are_preserved() -> None:
    required = (
        "Currency",
        "Money",
        "Wallet",
        "LedgerAccount",
        "JournalEntry",
        "Transaction",
        "Customer",
        "FinancialAccount",
        "ExchangeRate",
        "FXQuote",
        "CurrencyDefinition",
        "CurrencyRegistry",
    )

    for symbol in required:
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)
        assert symbol in domain.__all__
        assert symbol in novapay.__all__


def test_reimport_preserves_export_identity() -> None:
    reloaded_domain = importlib.reload(domain)
    reloaded_novapay = importlib.reload(novapay)

    for symbol in BALANCE_SNAPSHOT_SYMBOLS:
        module_value = getattr(
            balance_snapshot,
            symbol,
        )

        assert getattr(
            reloaded_domain,
            symbol,
        ) is module_value

        assert getattr(
            reloaded_novapay,
            symbol,
        ) is module_value


def test_public_symbols_contain_no_runtime_instances() -> None:
    from afritech.afripay.fx import FXEngine

    for symbol in BALANCE_SNAPSHOT_SYMBOLS:
        assert not isinstance(
            getattr(novapay, symbol),
            FXEngine,
        )
