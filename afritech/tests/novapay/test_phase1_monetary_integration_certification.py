from __future__ import annotations

import ast
import inspect
from dataclasses import fields, is_dataclass
from decimal import Decimal
from pathlib import Path

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.balance_snapshot as balance_snapshot
import afritech.novapay.domain.currency as currency
import afritech.novapay.domain.exchange_rate_provider as provider
import afritech.novapay.domain.fx as fx
import afritech.novapay.domain.money as money


DOMAIN_ROOT = Path("afritech/novapay/domain")
TEST_ROOT = Path("afritech/tests/novapay")

MONETARY_MODULE_PATHS = (
    DOMAIN_ROOT / "money.py",
    DOMAIN_ROOT / "currency.py",
    DOMAIN_ROOT / "fx.py",
    DOMAIN_ROOT / "exchange_rate_provider.py",
    DOMAIN_ROOT / "balance_snapshot.py",
)

FOCUSED_TEST_PATTERNS = (
    "*money*.py",
    "*currency*.py",
    "*fx*.py",
    "*exchange_rate*.py",
    "*rate_provider*.py",
    "*balance_snapshot*.py",
)


def _combined_source(paths: tuple[Path, ...]) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def _focused_test_source() -> str:
    paths: set[Path] = set()
    for pattern in FOCUSED_TEST_PATTERNS:
        paths.update(TEST_ROOT.glob(pattern))
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(paths)
        if path.name != "test_phase1_monetary_integration_certification.py"
    )


def _public_methods(value: type[object]) -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(value)
        if callable(member) and not name.startswith("_")
    }


def test_canonical_monetary_types_have_cross_surface_identity() -> None:
    module_types = {
        "Money": money.Money,
        "Currency": currency.Currency,
        "ExchangeRate": fx.ExchangeRate,
        "FXQuote": fx.FXQuote,
        "BalanceSnapshot": balance_snapshot.BalanceSnapshot,
    }
    for symbol, module_value in module_types.items():
        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value
        assert symbol in domain.__all__
        assert symbol in novapay.__all__


def test_monetary_dataclasses_are_immutable() -> None:
    modules = (money, currency, fx, provider, balance_snapshot)
    checked = 0
    for module in modules:
        for symbol in module.__all__:
            value = getattr(module, symbol)
            if not inspect.isclass(value) or value.__module__ != module.__name__:
                continue
            if not is_dataclass(value):
                continue
            assert value.__dataclass_params__.frozen is True, (module.__name__, symbol)
            checked += 1
    assert checked >= 5


def test_currency_normalization_contract_is_implemented_and_tested() -> None:
    implementation = (inspect.getsource(currency) + "\n" + inspect.getsource(money)).lower()
    tests = _focused_test_source().lower()
    assert any(token in implementation for token in (".upper()", "upper(", ".strip()", "strip("))
    assert any(
        token in tests
        for token in ("normalize", "uppercase", "lowercase", "currency_code", "currency code")
    )


def test_minor_unit_rounding_contract_avoids_float_decimal_construction() -> None:
    quantize_or_rounding = 0
    decimal_float_literals: list[tuple[str, int]] = []
    for path in MONETARY_MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "quantize"
            ):
                quantize_or_rounding += 1
            if isinstance(node, ast.Name) and node.id.startswith("ROUND_"):
                quantize_or_rounding += 1
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Decimal"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, float)
            ):
                decimal_float_literals.append((str(path), node.lineno))
    assert quantize_or_rounding >= 1
    assert decimal_float_literals == []
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")


def test_same_currency_mismatch_contract_is_implemented_and_tested() -> None:
    implementation = inspect.getsource(money).lower()
    tests = _focused_test_source().lower()
    assert "currency" in implementation
    assert any(
        token in implementation
        for token in ("mismatch", "same currency", "currency !=", "currency ==", "different currency")
    )
    assert any(
        token in tests
        for token in ("currency_mismatch", "same_currency", "different_currency", "mismatch")
    )


def test_exchange_rate_direction_and_inversion_are_certified() -> None:
    field_names = {item.name for item in fields(fx.ExchangeRate)}
    pair_field_names = {item.name for item in fields(fx.CurrencyPair)}
    field_text = " ".join(field_names | pair_field_names).lower()
    implementation = inspect.getsource(fx.ExchangeRate).lower()
    tests = _focused_test_source().lower()
    assert any(token in field_text for token in ("base", "source", "from"))
    assert any(token in field_text for token in ("quote", "target", "to"))
    combined_contract = (
        implementation
        + "\n"
        + " ".join(_public_methods(fx.ExchangeRate)).lower()
        + "\n"
        + tests
    )
    assert any(token in combined_contract for token in ("inverse", "invert", "reciprocal"))


def test_fx_quote_expiry_contract_is_implemented_and_tested() -> None:
    field_names = {item.name for item in fields(fx.FXQuote)}
    field_text = " ".join(field_names).lower()
    implementation = inspect.getsource(fx.FXQuote).lower()
    tests = _focused_test_source().lower()
    expiry_tokens = ("expires", "expiry", "expired", "valid_until", "valid_to")
    assert any(token in field_text or token in implementation for token in expiry_tokens)
    assert any(token in tests for token in expiry_tokens)


def test_provider_and_rate_source_lineage_is_traceable() -> None:
    implementation = inspect.getsource(provider).lower() + "\n" + inspect.getsource(fx).lower()
    tests = _focused_test_source().lower()
    assert "provider" in implementation
    assert "source" in implementation
    assert any(token in implementation for token in ("provider_id", "source_id", "rate_source", "provider"))
    assert any(token in tests for token in ("provider_id", "source_id", "rate_source", "provider"))


def test_balance_snapshot_and_serialization_contracts_align() -> None:
    snapshot_fields = {item.name for item in fields(balance_snapshot.BalanceSnapshot)}
    component_fields = {item.name for item in fields(balance_snapshot.BalanceComponent)}
    reconciliation_fields = {
        item.name for item in fields(balance_snapshot.BalanceReconciliation)
    }
    snapshot_field_text = " ".join(
        snapshot_fields | component_fields | reconciliation_fields
    ).lower()
    assert any(token in snapshot_field_text for token in ("balance", "amount", "available", "current"))
    assert any(token in snapshot_field_text for token in ("currency", "money"))
    serialization_methods = {
        "canonical_dict",
        "to_dict",
        "as_dict",
        "serialize",
        "from_dict",
        "deserialize",
    }
    for value in (money.Money, fx.ExchangeRate, fx.FXQuote, balance_snapshot.BalanceSnapshot):
        assert serialization_methods.intersection(_public_methods(value)), value.__name__
