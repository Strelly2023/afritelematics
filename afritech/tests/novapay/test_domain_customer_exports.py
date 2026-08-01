from __future__ import annotations

import afritech.novapay as novapay
import afritech.novapay.domain as domain
from afritech.novapay.domain import customer as customer_module


EXPECTED_CUSTOMER_SYMBOLS = (
    "Customer",
    "CustomerAddress",
    "CustomerContact",
    "CustomerId",
    "CustomerMetadata",
    "CustomerName",
    "CustomerPreferences",
    "CustomerStatus",
    "CustomerTier",
    "CustomerType",
)


def test_customer_symbols_exported_from_domain_package() -> None:
    for symbol in EXPECTED_CUSTOMER_SYMBOLS:
        assert getattr(domain, symbol) is getattr(
            customer_module,
            symbol,
        )


def test_customer_symbols_exported_from_top_level_package() -> None:
    for symbol in EXPECTED_CUSTOMER_SYMBOLS:
        assert getattr(novapay, symbol) is getattr(
            customer_module,
            symbol,
        )


def test_customer_exports_appear_once_in_domain_all() -> None:
    for symbol in EXPECTED_CUSTOMER_SYMBOLS:
        assert domain.__all__.count(symbol) == 1


def test_customer_exports_appear_once_in_top_level_all() -> None:
    for symbol in EXPECTED_CUSTOMER_SYMBOLS:
        assert novapay.__all__.count(symbol) == 1


def test_customer_module_all_contract() -> None:
    assert customer_module.__all__ == list(
        EXPECTED_CUSTOMER_SYMBOLS
    )


def test_customer_class_identity_across_import_paths() -> None:
    from afritech.novapay import Customer
    from afritech.novapay.domain import Customer as DomainCustomer
    from afritech.novapay.domain.customer import (
        Customer as ModuleCustomer,
    )

    assert Customer is DomainCustomer
    assert DomainCustomer is ModuleCustomer


def test_existing_domain_exports_remain_available() -> None:
    expected = (
        "Money",
        "Currency",
        "Wallet",
        "WalletId",
        "LedgerAccount",
        "LedgerAccountId",
        "JournalEntry",
        "JournalEntryId",
        "Transaction",
        "TransactionId",
    )

    for symbol in expected:
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)


def test_domain_all_contains_no_duplicates() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))


def test_top_level_all_contains_no_duplicates() -> None:
    assert len(novapay.__all__) == len(
        set(novapay.__all__)
    )
