from __future__ import annotations

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.remittance as remittance


REMITTANCE_SYMBOLS = (
    "Remittance",
    "RemittanceAmountBreakdown",
    "RemittanceCharge",
    "RemittanceCorridor",
    "RemittanceDirection",
    "RemittanceFee",
    "RemittanceFeeType",
    "RemittanceFundingReference",
    "RemittanceId",
    "RemittanceInstruction",
    "RemittanceInstructionId",
    "RemittanceInstructionMetadata",
    "RemittanceMetadata",
    "RemittancePricingMetadata",
    "RemittancePriority",
    "RemittancePurpose",
    "RemittanceRecipientReference",
    "RemittanceReference",
    "RemittanceStatus",
    "RemittanceType",
)


def test_remittance_module_export_inventory() -> None:
    assert tuple(remittance.__all__) == REMITTANCE_SYMBOLS
    assert remittance.__all__ == sorted(remittance.__all__)
    assert len(remittance.__all__) == 20
    assert len(remittance.__all__) == len(
        set(remittance.__all__)
    )


def test_domain_exports_all_remittance_symbols() -> None:
    for symbol in REMITTANCE_SYMBOLS:
        assert hasattr(domain, symbol)
        assert symbol in domain.__all__


def test_top_level_exports_all_remittance_symbols() -> None:
    for symbol in REMITTANCE_SYMBOLS:
        assert hasattr(novapay, symbol)
        assert symbol in novapay.__all__


def test_export_identity_is_preserved() -> None:
    for symbol in REMITTANCE_SYMBOLS:
        module_value = getattr(remittance, symbol)
        domain_value = getattr(domain, symbol)
        top_level_value = getattr(novapay, symbol)

        assert domain_value is module_value
        assert top_level_value is module_value


def test_public_all_contracts_are_sorted() -> None:
    assert domain.__all__ == sorted(domain.__all__)
    assert novapay.__all__ == sorted(novapay.__all__)


def test_public_all_contracts_are_unique() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))
    assert len(novapay.__all__) == len(set(novapay.__all__))


def test_existing_transfer_identity_is_preserved() -> None:
    from afritech.novapay.domain.transfer import Transfer

    assert domain.Transfer is Transfer
    assert novapay.Transfer is Transfer


def test_existing_balance_snapshot_identity_is_preserved() -> None:
    from afritech.novapay.domain.balance_snapshot import (
        BalanceSnapshot,
    )

    assert domain.BalanceSnapshot is BalanceSnapshot
    assert novapay.BalanceSnapshot is BalanceSnapshot


def test_existing_exchange_rate_provider_module_is_preserved() -> None:
    from afritech.novapay.domain.exchange_rate_provider import (
        ExchangeRateProvider,
    )

    assert ExchangeRateProvider.__module__ == (
        "afritech.novapay.domain.exchange_rate_provider"
    )
    assert "ExchangeRateProvider" not in domain.__all__
    assert "ExchangeRateProvider" not in novapay.__all__


def test_remittance_exports_have_no_runtime_singletons() -> None:
    for symbol in REMITTANCE_SYMBOLS:
        value = getattr(domain, symbol)

        assert not isinstance(value, dict)
        assert not isinstance(value, list)
        assert not isinstance(value, set)
