from __future__ import annotations

from decimal import Decimal
from importlib import import_module

import pytest

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.reconciliation import LedgerReconciliationEngine
from afritech.ci.afripay_financial_integrity_validator import validate as validate_financial_integrity


def models():
    return import_module("afriride_system.django_app.apps.afripay.models")


@pytest.mark.django_db
def test_reconciliation_report_is_stable_across_independent_readers():
    create_payment_sync(
        {
            "payer_id": "dist.payer.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "dist.payee.001",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "80.00",
            "currency": "AUD",
            "reference": "dist.consistency.001",
            "preference": "balanced",
        }
    )

    first = LedgerReconciliationEngine().reconcile_transaction("dist.consistency.001")
    second = LedgerReconciliationEngine().reconcile_transaction("dist.consistency.001")

    assert first.verified is True
    assert second.verified is True
    assert first.report_hash() == second.report_hash()
    assert first.ledger_hash == second.ledger_hash
    assert first.provider_hash == second.provider_hash
    assert first.event_hash == second.event_hash
    assert first.treasury_hash == second.treasury_hash


@pytest.mark.django_db
def test_reconciliation_detects_ledger_imbalance():
    create_payment_sync(
        {
            "payer_id": "dist.payer.002",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "dist.payee.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "60.00",
            "currency": "AUD",
            "reference": "dist.imbalance.001",
            "preference": "balanced",
        }
    )

    m = models()
    line = m.EntryLine.objects.filter(journal__transaction__reference="dist.imbalance.001").first()
    assert line is not None
    line.debit = Decimal("0.00")
    line.save(update_fields=["debit"])

    report = LedgerReconciliationEngine().reconcile_transaction("dist.imbalance.001")

    assert report.verified is False
    assert any(mismatch.code == "imbalanced_journal" for mismatch in report.mismatches)


@pytest.mark.django_db
def test_reconciliation_detects_provider_route_mismatch():
    create_payment_sync(
        {
            "payer_id": "dist.payer.003",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "dist.payee.003",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "90.00",
            "currency": "AUD",
            "reference": "dist.provider.001",
            "preference": "balanced",
        }
    )

    m = models()
    tx = m.Transaction.objects.get(reference="dist.provider.001")
    m.PaymentRoute.objects.create(
        route_id="route.dist.mismatch",
        transaction=tx,
        provider="bogus_provider",
        rail="bank",
        amount=Decimal("5.00"),
        currency="AUD",
        fee=Decimal("0.00"),
        status="confirmed",
        external_reference="bogus.external.reference",
    )

    report = LedgerReconciliationEngine().reconcile_transaction("dist.provider.001")

    assert report.verified is False
    assert any(
        mismatch.code in {"provider_route_mismatch", "provider_reference_mismatch"}
        for mismatch in report.mismatches
    )


@pytest.mark.django_db
def test_reconciliation_detects_missing_event_chain():
    create_payment_sync(
        {
            "payer_id": "dist.payer.004",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "dist.payee.004",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "70.00",
            "currency": "AUD",
            "reference": "dist.events.001",
            "preference": "balanced",
        }
    )

    m = models()
    m.EventRecord.objects.filter(aggregate_id="dist.events.001").delete()

    report = LedgerReconciliationEngine().reconcile_transaction("dist.events.001")

    assert report.verified is False
    assert any(mismatch.code == "missing_events" for mismatch in report.mismatches)


@pytest.mark.django_db
def test_financial_integrity_validator_emits_auditable_proof():
    report = validate_financial_integrity()

    assert report.verified is True
    assert len(report.report_hash()) == 64
    assert len(report.ledger_hash) == 64
    assert len(report.provider_hash) == 64
    assert len(report.event_hash) == 64
    assert len(report.treasury_hash) == 64
