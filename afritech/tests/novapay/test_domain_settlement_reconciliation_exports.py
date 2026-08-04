from __future__ import annotations

import importlib

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.settlement_reconciliation as reconciliation


EXPECTED_RECONCILIATION_EXPORTS = [
    "ReconciliationDifference",
    "ReconciliationDifferenceId",
    "ReconciliationDifferenceType",
    "ReconciliationEvidence",
    "ReconciliationEvidenceId",
    "ReconciliationEvidenceType",
    "ReconciliationItem",
    "ReconciliationItemId",
    "ReconciliationItemStatus",
    "ReconciliationMetadata",
    "ReconciliationObservation",
    "ReconciliationObservationId",
    "ReconciliationObservationSource",
    "ReconciliationResult",
    "ReconciliationStatus",
    "ReconciliationSummary",
    "ReconciliationType",
    "SettlementReconciliation",
    "SettlementReconciliationId",
]


def test_canonical_module_inventory() -> None:
    assert (
        reconciliation.__all__
        == EXPECTED_RECONCILIATION_EXPORTS
    )


def test_domain_package_exports_every_canonical_symbol() -> None:
    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert hasattr(domain, symbol)
        assert symbol in domain.__all__


def test_top_level_package_exports_every_canonical_symbol() -> None:
    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert hasattr(novapay, symbol)
        assert symbol in novapay.__all__


def test_three_layer_symbol_identity() -> None:
    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        module_value = getattr(
            reconciliation,
            symbol,
        )
        domain_value = getattr(
            domain,
            symbol,
        )
        top_level_value = getattr(
            novapay,
            symbol,
        )

        assert module_value is domain_value
        assert domain_value is top_level_value


def test_domain_export_ordering_is_deterministic() -> None:
    assert domain.__all__ == sorted(domain.__all__)


def test_top_level_export_ordering_is_deterministic() -> None:
    assert novapay.__all__ == sorted(novapay.__all__)


def test_domain_exports_are_unique() -> None:
    assert len(domain.__all__) == len(
        set(domain.__all__)
    )


def test_top_level_exports_are_unique() -> None:
    assert len(novapay.__all__) == len(
        set(novapay.__all__)
    )


def test_reconciliation_symbols_appear_once_in_domain_contract() -> None:
    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert domain.__all__.count(symbol) == 1


def test_reconciliation_symbols_appear_once_in_top_level_contract() -> None:
    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert novapay.__all__.count(symbol) == 1


def test_domain_star_import_contract() -> None:
    for symbol in domain.__all__:
        assert hasattr(domain, symbol)

    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert symbol in domain.__all__
        assert getattr(domain, symbol) is getattr(
            reconciliation,
            symbol,
        )


def test_top_level_star_import_contract() -> None:
    for symbol in novapay.__all__:
        assert hasattr(novapay, symbol)

    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert symbol in novapay.__all__
        assert getattr(novapay, symbol) is getattr(
            reconciliation,
            symbol,
        )


def test_repeated_import_preserves_identity() -> None:
    reloaded_domain = importlib.import_module(
        "afritech.novapay.domain"
    )

    reloaded_top = importlib.import_module(
        "afritech.novapay"
    )

    for symbol in EXPECTED_RECONCILIATION_EXPORTS:
        assert getattr(
            reloaded_domain,
            symbol,
        ) is getattr(
            reconciliation,
            symbol,
        )

        assert getattr(
            reloaded_top,
            symbol,
        ) is getattr(
            reconciliation,
            symbol,
        )


def test_public_exports_do_not_add_execution_authority() -> None:
    aggregate = novapay.SettlementReconciliation

    for method_name in (
        "compare",
        "match",
        "reconcile",
        "resolve",
        "execute",
        "settle",
        "authorize",
        "reserve",
        "debit",
        "credit",
        "post",
        "submit",
        "send",
        "persist",
        "save",
        "repository",
        "database",
    ):
        assert not hasattr(
            aggregate,
            method_name,
        )


def test_public_result_records_do_not_add_execution_authority() -> None:
    for record_type in (
        novapay.ReconciliationResult,
        novapay.ReconciliationSummary,
    ):
        for method_name in (
            "compare",
            "match",
            "reconcile",
            "resolve",
            "execute",
            "settle",
            "persist",
            "save",
            "submit",
            "post",
            "debit",
            "credit",
        ):
            assert not hasattr(
                record_type,
                method_name,
            )
