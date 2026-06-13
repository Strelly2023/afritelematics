from __future__ import annotations

import pytest

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.protocol import (
    anchor_and_verify_protocol_proof,
    build_recursive_global_proof,
)
from afritech.afripay.reconciliation import validate_global_ledger_integrity
from afritech.chain.types import ChainReceipt
from afritech.distributed.consensus.pbft import PBFTConsensusEngine
from afritech.distributed.proof import build_proof, hash_result


def _proof_payload(reference: str, proof_hash: str, global_proof_hash: str) -> dict[str, object]:
    return {
        "reference": reference,
        "proof_hash": proof_hash,
        "global_proof_hash": global_proof_hash,
        "scope": "protocol",
    }


@pytest.mark.django_db
def test_pbft_protocol_finality_requires_prepare_and_commit_quorum():
    payload = _proof_payload(
        reference="pbft.protocol.tx.001",
        proof_hash="a" * 64,
        global_proof_hash="b" * 64,
    )

    proofs = (
        build_proof(
            node_id="validator-0",
            result=payload,
            signature=b"sig-pre",
            metadata={"protocol_step": "pre_prepare", "round": 0, "height": 1},
        ),
        *(
            build_proof(
                node_id=f"validator-{index}",
                result=payload,
                signature=f"sig-prepare-{index}".encode("utf-8"),
                metadata={"protocol_step": "prepare", "round": 0, "height": 1},
            )
            for index in range(5)
        ),
        *(
            build_proof(
                node_id=f"validator-{index}",
                result=payload,
                signature=f"sig-commit-{index}".encode("utf-8"),
                metadata={"protocol_step": "commit", "round": 0, "height": 1},
            )
            for index in range(5)
        ),
    )

    certificate = PBFTConsensusEngine(validator_count=5, height=1, round=0).decide(proofs, total_nodes=5)

    assert certificate.verified is True
    assert certificate.proposal_hash == hash_result(payload)
    assert certificate.quorum == 3
    assert certificate.fault_tolerance == 1
    assert len(certificate.report_hash()) == 64


@pytest.mark.django_db
def test_recursive_global_proof_aggregates_child_commitments():
    create_payment_sync(
        {
            "payer_id": "recursive.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "recursive.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "75.00",
            "currency": "AUD",
            "reference": "recursive.protocol.tx.001",
            "preference": "balanced",
        }
    )
    create_payment_sync(
        {
            "payer_id": "recursive.user.003",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "recursive.user.004",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "25.00",
            "currency": "AUD",
            "reference": "recursive.protocol.tx.002",
            "preference": "balanced",
        }
    )

    global_report = validate_global_ledger_integrity(anchor_mode="external_log")
    recursive_bundle = build_recursive_global_proof(global_report)

    assert recursive_bundle.verified is True
    assert recursive_bundle.global_proof_hash == global_report.global_proof_hash
    assert len(recursive_bundle.recursive_proof_hash) == 64
    assert len(recursive_bundle.recursive_merkle_root) == 64
    assert recursive_bundle.global_proof_hash in recursive_bundle.child_proof_hashes
    assert len(recursive_bundle.child_proof_hashes) >= global_report.transaction_count + 4


@pytest.mark.django_db
def test_protocol_anchor_verification_calls_chain_verifier(monkeypatch):
    captured: dict[str, object] = {}

    def fake_publish(proof_hash: str, *, profile_name: str | None = None, require_live: bool = False):
        captured["proof_hash"] = proof_hash
        captured["profile_name"] = profile_name
        captured["require_live"] = require_live
        return ChainReceipt(
            tx_hash="0xabc123",
            network="mainnet",
            block_number=123,
            explorer_url="https://etherscan.io/tx/0xabc123",
            status="live",
            chain_id=1,
            chain_name="Ethereum Mainnet",
            proof_hash=proof_hash,
            authority="smart_contract",
            source="test",
        )

    def fake_verify(anchor_id: str, proof_hash: str, *, profile_name: str | None = None) -> bool:
        captured["anchor_id"] = anchor_id
        captured["verify_profile_name"] = profile_name
        return anchor_id == f"arch-{proof_hash[:12]}"

    monkeypatch.setattr("afritech.afripay.protocol.publish_anchor", fake_publish)
    monkeypatch.setattr("afritech.afripay.protocol.verify_anchor_on_chain", fake_verify)

    result = anchor_and_verify_protocol_proof(
        "c" * 64,
        profile_name="mainnet",
        require_live=True,
    )

    assert result.verified is True
    assert result.onchain_verified is True
    assert result.chain_receipt.network == "mainnet"
    assert captured["proof_hash"] == "c" * 64
    assert captured["require_live"] is True
    assert captured["anchor_id"] == "arch-cccccccccccc"
