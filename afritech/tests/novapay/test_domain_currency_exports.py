from __future__ import annotations

import importlib

import pytest

import afritech.novapay as novapay
import afritech.novapay.domain as domain
from afritech.novapay.domain import currency


CURRENCY_SYMBOLS = (
    "CurrencyCountryCodes",
    "CurrencyDefinition",
    "CurrencyDefinitionId",
    "CurrencyMetadata",
    "CurrencyName",
    "CurrencyRegistry",
    "CurrencyRegistryId",
    "CurrencyRoundingMode",
    "CurrencyStatus",
    "CurrencySymbol",
    "CurrencyType",
    "STANDARD_CURRENCY_DEFINITIONS",
    "standard_currency_definitions",
    "standard_currency_registry",
)


@pytest.mark.parametrize("symbol", CURRENCY_SYMBOLS)
def test_domain_package_exports_currency_symbol(
    symbol: str,
) -> None:
    assert hasattr(domain, symbol)
    assert getattr(domain, symbol) is getattr(currency, symbol)


@pytest.mark.parametrize("symbol", CURRENCY_SYMBOLS)
def test_top_level_package_exports_currency_symbol(
    symbol: str,
) -> None:
    assert hasattr(novapay, symbol)
    assert getattr(novapay, symbol) is getattr(currency, symbol)


@pytest.mark.parametrize("symbol", CURRENCY_SYMBOLS)
def test_currency_export_identity_is_consistent(
    symbol: str,
) -> None:
    module_value = getattr(currency, symbol)
    domain_value = getattr(domain, symbol)
    top_level_value = getattr(novapay, symbol)

    assert module_value is domain_value
    assert domain_value is top_level_value


@pytest.mark.parametrize("symbol", CURRENCY_SYMBOLS)
def test_currency_symbol_declared_in_all_contracts(
    symbol: str,
) -> None:
    assert symbol in currency.__all__
    assert symbol in domain.__all__
    assert symbol in novapay.__all__


def test_currency_module_contract_is_complete() -> None:
    assert set(CURRENCY_SYMBOLS) == set(currency.__all__)


def test_public_all_contracts_are_sorted() -> None:
    assert domain.__all__ == sorted(domain.__all__)
    assert novapay.__all__ == sorted(novapay.__all__)


def test_public_all_contracts_have_no_duplicates() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))
    assert len(novapay.__all__) == len(set(novapay.__all__))


def test_existing_currency_and_money_exports_are_preserved() -> None:
    from afritech.novapay.domain.money import Currency, Money

    assert domain.Currency is Currency
    assert novapay.Currency is Currency
    assert domain.Money is Money
    assert novapay.Money is Money


def test_existing_domain_exports_remain_available() -> None:
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
    )

    for symbol in required:
        assert hasattr(domain, symbol)
        assert symbol in domain.__all__


def test_existing_top_level_exports_remain_available() -> None:
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
    )

    for symbol in required:
        assert hasattr(novapay, symbol)
        assert symbol in novapay.__all__


def test_standard_catalogue_public_identity() -> None:
    assert (
        novapay.STANDARD_CURRENCY_DEFINITIONS
        is currency.STANDARD_CURRENCY_DEFINITIONS
    )

    assert (
        domain.standard_currency_registry
        is currency.standard_currency_registry
    )


def test_reimport_preserves_currency_identity() -> None:
    reloaded_domain = importlib.reload(domain)
    reloaded_novapay = importlib.reload(novapay)

    for symbol in CURRENCY_SYMBOLS:
        assert getattr(
            reloaded_domain,
            symbol,
        ) is getattr(currency, symbol)

        assert getattr(
            reloaded_novapay,
            symbol,
        ) is getattr(currency, symbol)


def test_public_catalogue_factory_builds_valid_registry() -> None:
    registry = novapay.standard_currency_registry()

    assert registry.size == 15
    assert registry.require_by_code("AUD").code == "AUD"
    assert registry.require_by_code("BIF").minor_units == 0
    assert registry.require_by_code("RWF").minor_units == 0
    assert registry.require_by_code("UGX").minor_units == 0


def test_currency_exports_contain_no_runtime_instances() -> None:
    from afritech.afripay.fx import FXEngine

    for symbol in CURRENCY_SYMBOLS:
        value = getattr(novapay, symbol)
        assert not isinstance(value, FXEngine)
