from __future__ import annotations

import pytest

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.reconciliation import GlobalLedgerReconciliationEngine
from afritech.chain.types import ChainReceipt


@pytest.mark.django_db
def test_global_ledger_reconciliation_is_merkle_stable():
    create_payment_sync(
        {
            "payer_id": "global.payer.1",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "global.payee.1",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "40.00",
            "currency": "AUD",
            "reference": "global.recon.001",
            "preference": "balanced",
        }
    )
    create_payment_sync(
        {
            "payer_id": "global.payer.2",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "global.payee.2",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "55.00",
            "currency": "AUD",
            "reference": "global.recon.002",
            "preference": "balanced",
        }
    )

    engine = GlobalLedgerReconciliationEngine(anchor_mode="external_log")
    report_1 = engine.reconcile_all()
    report_2 = engine.reconcile_all()

    assert report_1.verified is True
    assert report_1.report_hash() == report_2.report_hash()
    assert len(report_1.audit_merkle_root) == 64
    assert len(report_1.global_proof_hash) == 64
    assert report_1.external_anchor_commitment is not None
    assert report_1.external_anchor_commitment.anchor_id.startswith("anchor-")


@pytest.mark.django_db
def test_global_ledger_reconciliation_can_anchor_to_blockchain(monkeypatch):
    create_payment_sync(
        {
            "payer_id": "global.payer.3",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "global.payee.3",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "25.00",
            "currency": "AUD",
            "reference": "global.recon.003",
            "preference": "balanced",
        }
    )

    fake_receipt = ChainReceipt(
        tx_hash="0xabc123",
        network="sepolia",
        status="live",
        proof_hash="b" * 64,
        authority="smart_contract",
        source="test",
    )
    monkeypatch.setattr(
        "afritech.afripay.reconciliation.publish_anchor",
        lambda proof_hash, profile_name=None, require_live=False: fake_receipt,
    )

    report = GlobalLedgerReconciliationEngine(anchor_mode="blockchain").reconcile_all()

    assert report.verified is True
    assert report.chain_receipt is not None
    assert report.chain_receipt.tx_hash == "0xabc123"
    assert report.external_anchor_commitment is not None
    assert report.external_anchor_commitment.commitment_hash
