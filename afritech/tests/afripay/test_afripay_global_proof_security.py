from __future__ import annotations

from decimal import Decimal
from importlib import import_module

import pytest

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.reconciliation import (
    GlobalLedgerReconciliationEngine,
    validate_global_ledger_integrity,
)


def models():
    return import_module("afriride_system.django_app.apps.afripay.models")


@pytest.mark.django_db
def test_global_proof_contains_merkle_inclusion_and_zk_layers():
    create_payment_sync(
        {
            "payer_id": "proof.sec.payer.1",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "proof.sec.payee.1",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "50.00",
            "currency": "AUD",
            "reference": "proof.sec.tx.001",
            "preference": "balanced",
        }
    )
    create_payment_sync(
        {
            "payer_id": "proof.sec.payer.2",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "proof.sec.payee.2",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "25.00",
            "currency": "AUD",
            "reference": "proof.sec.tx.002",
            "preference": "balanced",
        }
    )

    report = GlobalLedgerReconciliationEngine(anchor_mode="external_log").reconcile_all()

    assert report.verified is True
    assert len(report.transaction_inclusion_proofs) == report.transaction_count
    assert len(report.transaction_zk_attestations) == report.transaction_count
    assert all(proof.verified for proof in report.transaction_inclusion_proofs)
    assert all(attestation.verified for attestation in report.transaction_zk_attestations)
    assert len(report.report_hash()) == 64


@pytest.mark.django_db
def test_global_proof_detects_ledger_tampering():
    create_payment_sync(
        {
            "payer_id": "tamper.ledger.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "tamper.ledger.payee",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "60.00",
            "currency": "AUD",
            "reference": "tamper.ledger.tx.001",
            "preference": "balanced",
        }
    )

    m = models()
    line = m.EntryLine.objects.first()
    line.debit = Decimal("999.00")
    line.save(update_fields=["debit"])

    report = GlobalLedgerReconciliationEngine(anchor_mode="external_log").reconcile_all()

    assert report.verified is False
    assert report.mismatches


@pytest.mark.django_db
def test_global_proof_detects_event_tampering():
    create_payment_sync(
        {
            "payer_id": "tamper.event.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "tamper.event.payee",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "30.00",
            "currency": "AUD",
            "reference": "tamper.event.tx.001",
            "preference": "balanced",
        }
    )

    m = models()
    event = m.EventRecord.objects.first()
    event.hash_chain = "invalid"
    event.save(update_fields=["hash_chain"])

    report = GlobalLedgerReconciliationEngine(anchor_mode="external_log").reconcile_all()

    assert report.verified is False
    assert report.mismatches


@pytest.mark.django_db
def test_global_proof_detects_route_tampering():
    create_payment_sync(
        {
            "payer_id": "tamper.route.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "tamper.route.payee",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "90.00",
            "currency": "AUD",
            "reference": "tamper.route.tx.001",
            "preference": "balanced",
        }
    )

    m = models()
    route = m.PaymentRoute.objects.first()
    route.amount = Decimal("999.00")
    route.save(update_fields=["amount"])

    report = GlobalLedgerReconciliationEngine(anchor_mode="external_log").reconcile_all()

    assert report.verified is False
    assert report.mismatches


@pytest.mark.django_db
def test_validate_global_ledger_integrity_success_and_merkle_sensitivity():
    create_payment_sync(
        {
            "payer_id": "validator.global.payer.1",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "validator.global.payee.1",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "70.00",
            "currency": "AUD",
            "reference": "validator.global.tx.001",
            "preference": "balanced",
        }
    )

    first = validate_global_ledger_integrity()
    second = validate_global_ledger_integrity()
    assert first.verified is True
    assert first.report_hash() == second.report_hash()

    create_payment_sync(
        {
            "payer_id": "validator.global.payer.2",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "validator.global.payee.2",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "11.00",
            "currency": "AUD",
            "reference": "validator.global.tx.002",
            "preference": "balanced",
        }
    )

    third = validate_global_ledger_integrity()
    assert third.audit_merkle_root != first.audit_merkle_root
    assert third.verified is True


@pytest.mark.django_db
def test_security_validator_proof_report_covers_rotation_revocation_and_rate_limiting():
    from afritech.ci.afripay_security_validator import validate

    report = validate()

    assert report.verified is True
    assert report.key_rotation_verified is True
    assert report.key_revocation_verified is True
    assert report.rate_limiting_verified is True
    assert report.security_audit_stream_verified is True
    assert report.audit_logging_verified is True
    assert len(report.audit_stream_hash) == 64


@pytest.mark.django_db
def test_observability_validator_proof_report_covers_slo_and_burn_rate():
    from afritech.ci.afripay_observability_validator import validate

    report = validate()

    assert report.verified is True
    assert report.slo_compliance_verified is True
    assert report.burn_rate_alert_verified is True
    assert report.error_budget_tracking_verified is True
    assert report.synthetic_uptime_verified is True
    assert len(report.snapshot_hash) == 64
    assert len(report.dashboard_hash) == 64
    assert len(report.prometheus_hash) == 64
