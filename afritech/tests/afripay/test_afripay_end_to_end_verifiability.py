from __future__ import annotations

import os
import shutil
from importlib import import_module
from pathlib import Path

import pytest
from rest_framework.test import APIRequestFactory

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.reconciliation import (
    GlobalLedgerReconciliationEngine,
    validate_global_ledger_integrity,
)
from afritech.distributed.consensus.pbft import PBFTConsensusEngine
from afritech.chain.types import ChainReceipt
from afritech.distributed.proof import build_proof, hash_result
from afritech.runtime.multiregion.proof import run_multiregion_proof
from afritech.zk.groth16_prover import Groth16Prover
from afritech.zk.groth16_verifier import Groth16Verifier


def views():
    return import_module("afriride_system.django_app.apps.afripay.views")


def _authed_request(
    factory: APIRequestFactory,
    method: str,
    path: str,
    scopes: set[str] | None = None,
    data: dict | None = None,
):
    request = getattr(factory, method)(path, data or {}, format="json")
    request.afripay_principal = type("P", (), {"subject": "ops", "scopes": tuple(scopes or ())})()
    request.afripay_scopes = set(scopes or set())
    return request


def _proof_payload(reference: str, proof_hash: str, global_proof_hash: str) -> dict[str, object]:
    return {
        "reference": reference,
        "proof_hash": proof_hash,
        "global_proof_hash": global_proof_hash,
        "scope": "transaction",
    }


@pytest.mark.django_db
def test_end_to_end_payment_export_anchor_and_validation_are_consistent(monkeypatch):
    create_payment_sync(
        {
            "payer_id": "e2e.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "e2e.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "100.00",
            "currency": "AUD",
            "reference": "e2e.verifiable.tx.001",
            "preference": "balanced",
        }
    )

    engine = GlobalLedgerReconciliationEngine(anchor_mode="external_log")
    global_report = engine.reconcile_all()

    export_request = _authed_request(
        APIRequestFactory(),
        "get",
        "/api/afripay/proofs/export?reference=e2e.verifiable.tx.001",
        {"proofs:read"},
    )
    export_response = views().proof_export_view(export_request)

    assert export_response.status_code == 200
    assert export_response.data["scope"] == "transaction"
    assert export_response.data["reference"] == "e2e.verifiable.tx.001"
    assert export_response.data["transaction_report_hash"] == global_report.transaction_reports[0].report_hash()
    assert export_response.data["transaction_inclusion_proof"]["verified"] is True
    assert export_response.data["transaction_zk_attestation"]["verified"] is True

    captured: dict[str, object] = {}

    def fake_publish(proof_hash: str, *, profile_name: str | None = None, require_live: bool = False):
        captured["proof_hash"] = proof_hash
        captured["profile_name"] = profile_name
        captured["require_live"] = require_live
        return ChainReceipt(
            tx_hash="0xfeedbeef",
            network="mainnet",
            block_number=12345678,
            explorer_url="https://etherscan.io/tx/0xfeedbeef",
            status="live",
            chain_id=1,
            chain_name="Ethereum Mainnet",
            proof_hash=proof_hash,
            authority="smart_contract",
            source="test",
        )

    monkeypatch.setattr("afriride_system.django_app.apps.afripay.views.publish_anchor", fake_publish)

    anchor_request = _authed_request(
        APIRequestFactory(),
        "post",
        "/api/afripay/proofs/anchor",
        {"proofs:write"},
        {
            "proof_hash": export_response.data["proof_hash"],
            "profile_name": "mainnet",
        },
    )
    anchor_response = views().proof_anchor_view(anchor_request)

    assert anchor_response.status_code == 200
    assert anchor_response.data["status"] == "anchored"
    assert anchor_response.data["chain_receipt"]["proof_hash"] == export_response.data["proof_hash"]
    assert captured["proof_hash"] == export_response.data["proof_hash"]
    assert captured["profile_name"] == "mainnet"
    assert captured["require_live"] is True

    validation_report = validate_global_ledger_integrity(anchor_mode="external_log")
    assert validation_report.verified is True
    assert validation_report.report_hash() == global_report.report_hash()


@pytest.mark.django_db
def test_cross_region_reconciliation_proof_is_stable():
    report_a = run_multiregion_proof()
    report_b = run_multiregion_proof()

    assert report_a.verified is True
    assert report_b.verified is True
    assert report_a.multiregion_convergence_hash == report_b.multiregion_convergence_hash
    assert len(report_a.multiregion_convergence_hash) == 64
    assert len(report_a.scenarios) == 5


@pytest.mark.django_db
def test_multi_node_consensus_proves_same_exported_payload():
    create_payment_sync(
        {
            "payer_id": "consensus.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "consensus.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "55.00",
            "currency": "AUD",
            "reference": "e2e.consensus.tx.001",
            "preference": "balanced",
        }
    )

    export_request = _authed_request(
        APIRequestFactory(),
        "get",
        "/api/afripay/proofs/export",
        {"proofs:read"},
    )
    export_response = views().proof_export_view(export_request)

    payload = _proof_payload(
        reference="e2e.consensus.tx.001",
        proof_hash=export_response.data["proof_hash"],
        global_proof_hash=export_response.data["global_proof_hash"],
    )

    proofs = (
        build_proof(
            node_id="node-0",
            result=payload,
            signature=b"signature-0",
            metadata={
                "region": "region-0",
                "request_id": "consensus-0",
                "protocol_step": "pre_prepare",
            },
        ),
        *(
            build_proof(
                node_id=f"node-{index}",
                result=payload,
                signature=f"signature-{index}".encode("utf-8"),
                metadata={
                    "region": f"region-{index % 3}",
                    "request_id": f"consensus-{index}",
                    "protocol_step": "prepare",
                },
            )
            for index in range(5)
        ),
        *(
            build_proof(
                node_id=f"node-{index}",
                result=payload,
                signature=f"signature-commit-{index}".encode("utf-8"),
                metadata={
                    "region": f"region-{index % 3}",
                    "request_id": f"consensus-commit-{index}",
                    "protocol_step": "commit",
                },
            )
            for index in range(5)
        ),
    )

    consensus = PBFTConsensusEngine(validator_count=5, height=1, round=0).decide(proofs, total_nodes=5)

    assert consensus.proposal_hash == hash_result(payload)
    assert consensus.verified is True
    assert consensus.quorum == 3
    assert len(consensus.prepare_nodes) == 5
    assert len(consensus.commit_nodes) == 5
    assert len(consensus.report_hash()) == 64


@pytest.mark.django_db
def test_real_groth16_zk_round_trip_if_assets_configured():
    wasm_path = os.environ.get("AFRIPAY_GROTH16_WASM_PATH")
    zkey_path = os.environ.get("AFRIPAY_GROTH16_ZKEY_PATH")
    verification_key_path = os.environ.get("AFRIPAY_GROTH16_VERIFICATION_KEY_PATH")
    snarkjs_path = os.environ.get("AFRIPAY_SNARKJS_PATH", "snarkjs")

    if not wasm_path or not zkey_path or not verification_key_path:
        pytest.skip("real Groth16 assets are not configured")

    if not Path(wasm_path).exists():
        pytest.skip(f"missing Groth16 wasm: {wasm_path}")
    if not Path(zkey_path).exists():
        pytest.skip(f"missing Groth16 zkey: {zkey_path}")
    if not Path(verification_key_path).exists():
        pytest.skip(f"missing Groth16 verification key: {verification_key_path}")
    if shutil.which(snarkjs_path) is None:
        pytest.skip(f"missing snarkjs binary: {snarkjs_path}")

    prover = Groth16Prover(
        wasm_path=wasm_path,
        zkey_path=zkey_path,
        snarkjs_path=snarkjs_path,
    )
    verifier = Groth16Verifier(
        verification_key_path=verification_key_path,
        snarkjs_path=snarkjs_path,
    )

    input_data = {
        "payload": {
            "amount": "100.00",
            "currency": "AUD",
            "reference": "e2e.zk.tx.001",
        },
        "authority_profile": {
            "subject": "zk-e2e",
            "scope": "proofs:read",
        },
        "replay_requirements": {
            "nonce": "zk-e2e-001",
            "region": "global",
        },
    }
    output_data = {
        "result_hash": "f" * 64,
        "status": "ok",
        "verified": True,
    }

    proof = prover.prove(input_data, output_data)

    assert proof.verify() is True
    assert verifier.verify(proof) is True
