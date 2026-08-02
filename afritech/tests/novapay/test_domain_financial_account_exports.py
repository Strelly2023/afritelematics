from __future__ import annotations

import afritech.novapay as novapay
import afritech.novapay.domain as domain
from afritech.novapay.domain import (
    financial_account as financial_account_module,
)


EXPECTED_SYMBOLS = (
    "FinancialAccount",
    "FinancialAccountId",
    "FinancialAccountMetadata",
    "FinancialAccountName",
    "FinancialAccountPurpose",
    "FinancialAccountRestrictions",
    "FinancialAccountStatus",
    "FinancialAccountTerms",
    "FinancialAccountType",
)


def test_symbols_exported_from_domain_package() -> None:
    for symbol in EXPECTED_SYMBOLS:
        assert hasattr(domain, symbol)
        assert getattr(domain, symbol) is getattr(
            financial_account_module,
            symbol,
        )


def test_symbols_exported_from_top_level_package() -> None:
    for symbol in EXPECTED_SYMBOLS:
        assert hasattr(novapay, symbol)
        assert getattr(novapay, symbol) is getattr(
            financial_account_module,
            symbol,
        )


def test_domain_all_contains_symbols_once() -> None:
    for symbol in EXPECTED_SYMBOLS:
        assert domain.__all__.count(symbol) == 1


def test_top_level_all_contains_symbols_once() -> None:
    for symbol in EXPECTED_SYMBOLS:
        assert novapay.__all__.count(symbol) == 1


def test_module_all_matches_contract() -> None:
    assert financial_account_module.__all__ == list(
        EXPECTED_SYMBOLS
    )


def test_financial_account_identity_across_import_paths() -> None:
    from afritech.novapay import FinancialAccount
    from afritech.novapay.domain import (
        FinancialAccount as DomainFinancialAccount,
    )
    from afritech.novapay.domain.financial_account import (
        FinancialAccount as ModuleFinancialAccount,
    )

    assert FinancialAccount is DomainFinancialAccount
    assert DomainFinancialAccount is ModuleFinancialAccount


def test_value_object_identity_across_import_paths() -> None:
    for symbol in EXPECTED_SYMBOLS[1:]:
        assert getattr(novapay, symbol) is getattr(
            domain,
            symbol,
        )
        assert getattr(domain, symbol) is getattr(
            financial_account_module,
            symbol,
        )


def test_existing_customer_exports_preserved() -> None:
    for symbol in (
        "Customer",
        "CustomerId",
        "CustomerStatus",
        "CustomerType",
    ):
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)


def test_existing_money_exports_preserved() -> None:
    for symbol in (
        "Currency",
        "Money",
    ):
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)


def test_existing_wallet_exports_preserved() -> None:
    for symbol in (
        "Wallet",
        "WalletId",
    ):
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)


def test_existing_ledger_exports_preserved() -> None:
    for symbol in (
        "LedgerAccount",
        "LedgerAccountId",
        "JournalEntry",
        "JournalEntryId",
    ):
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)


def test_existing_transaction_exports_preserved() -> None:
    for symbol in (
        "Transaction",
        "TransactionId",
    ):
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)


def test_domain_all_has_no_duplicates() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))


def test_top_level_all_has_no_duplicates() -> None:
    assert len(novapay.__all__) == len(
        set(novapay.__all__)
    )
