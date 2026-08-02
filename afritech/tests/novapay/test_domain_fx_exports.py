from __future__ import annotations

import importlib

import pytest

import afritech.novapay as novapay
import afritech.novapay.domain as domain
from afritech.novapay.domain import fx


FX_SYMBOLS = (
    "CurrencyPair",
    "ExchangeRate",
    "ExchangeRateId",
    "ExchangeRateSource",
    "ExchangeRateStatus",
    "ExchangeRateValue",
    "FXMetadata",
    "FXQuote",
    "FXQuoteId",
    "FXQuoteStatus",
    "FXValidityWindow",
    "RateSpread",
)


@pytest.mark.parametrize("symbol", FX_SYMBOLS)
def test_domain_package_exports_fx_symbol(
    symbol: str,
) -> None:
    assert hasattr(domain, symbol)
    assert getattr(domain, symbol) is getattr(fx, symbol)


@pytest.mark.parametrize("symbol", FX_SYMBOLS)
def test_top_level_package_exports_fx_symbol(
    symbol: str,
) -> None:
    assert hasattr(novapay, symbol)
    assert getattr(novapay, symbol) is getattr(fx, symbol)


@pytest.mark.parametrize("symbol", FX_SYMBOLS)
def test_export_identity_is_consistent(
    symbol: str,
) -> None:
    module_value = getattr(fx, symbol)
    domain_value = getattr(domain, symbol)
    top_level_value = getattr(novapay, symbol)

    assert module_value is domain_value
    assert domain_value is top_level_value


@pytest.mark.parametrize("symbol", FX_SYMBOLS)
def test_fx_symbol_declared_in_all_contracts(
    symbol: str,
) -> None:
    assert symbol in fx.__all__
    assert symbol in domain.__all__
    assert symbol in novapay.__all__


def test_fx_export_contract_is_complete() -> None:
    assert set(FX_SYMBOLS) == set(fx.__all__)


def test_package_all_contracts_have_no_duplicates() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))
    assert len(novapay.__all__) == len(set(novapay.__all__))


def test_package_all_contracts_are_sorted() -> None:
    assert domain.__all__ == sorted(domain.__all__)
    assert novapay.__all__ == sorted(novapay.__all__)


def test_existing_domain_exports_remain_available() -> None:
    required = (
        "Money",
        "Currency",
        "Wallet",
        "LedgerAccount",
        "JournalEntry",
        "Transaction",
        "Customer",
        "FinancialAccount",
    )

    for symbol in required:
        assert hasattr(domain, symbol)
        assert symbol in domain.__all__


def test_existing_top_level_exports_remain_available() -> None:
    required = (
        "Money",
        "Currency",
        "Wallet",
        "LedgerAccount",
        "JournalEntry",
        "Transaction",
        "Customer",
        "FinancialAccount",
    )

    for symbol in required:
        assert hasattr(novapay, symbol)
        assert symbol in novapay.__all__


def test_reimport_preserves_fx_identity() -> None:
    reloaded_domain = importlib.reload(domain)
    reloaded_novapay = importlib.reload(novapay)

    for symbol in FX_SYMBOLS:
        assert getattr(
            reloaded_domain,
            symbol,
        ) is getattr(fx, symbol)

        assert getattr(
            reloaded_novapay,
            symbol,
        ) is getattr(fx, symbol)


def test_fx_exports_do_not_shadow_afripay() -> None:
    from afritech.afripay.fx import FXEngine
    from afritech.afripay.models import (
        FXConversion,
        FXRate,
    )

    assert novapay.ExchangeRate is not FXRate
    assert novapay.FXQuote is not FXConversion
    assert novapay.ExchangeRate is not FXEngine
    assert novapay.FXQuote is not FXEngine


def test_fx_exports_contain_no_runtime_instances() -> None:
    from afritech.afripay.fx import FXEngine

    for symbol in FX_SYMBOLS:
        value = getattr(novapay, symbol)
        assert not isinstance(value, FXEngine)
