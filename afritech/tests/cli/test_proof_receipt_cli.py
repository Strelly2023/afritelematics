from __future__ import annotations

import json
from pathlib import Path

from afritech.cli.proof_receipt_cli import main
from afritech.core_platform.cryptographic_consensus import run_cryptographic_consensus
from afritech.core_platform.proof_receipts import build_proof_receipt
from afritech.core_platform.qr_proof import build_qr_artifact
from afritech.core_platform.signing import sign_packet


def test_proof_receipt_cli_verifies_receipt(tmp_path: Path, capsys) -> None:
    packet = {
        "trust_id": "trust-cli-receipt-001",
        "replay_status": "verified",
        "payload": {"sequence": 11},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    receipt = build_proof_receipt(result["trust_seal"], issuer="cli-test")
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    assert main([str(receipt_path)]) == 0
    assert "VALID" in capsys.readouterr().out


def test_proof_receipt_cli_supports_qr_mobile_and_onchain_modes(
    tmp_path: Path, capsys
) -> None:
    packet = {
        "trust_id": "trust-cli-receipt-002",
        "replay_status": "verified",
        "payload": {"sequence": 12},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    receipt = build_proof_receipt(result["trust_seal"], issuer="cli-test")
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    qr_output_path = tmp_path / "receipt.png"
    assert main([str(receipt_path), "--qr-output", str(qr_output_path)]) == 0
    assert qr_output_path.read_bytes().startswith(b"\x89PNG")
    capsys.readouterr()

    qr_artifact = build_qr_artifact(receipt)
    assert main(["--qr-data", qr_artifact["qr_payload"]]) == 0
    assert "VALID" in capsys.readouterr().out

    assert main([str(receipt_path), "--mobile", "--json"]) == 0
    mobile_output = json.loads(capsys.readouterr().out)
    assert mobile_output["status"] is True
    assert mobile_output["trust_level"] == "PARTIAL"

    assert main([str(receipt_path), "--onchain", "--json"]) == 0
    onchain_output = json.loads(capsys.readouterr().out)
    assert onchain_output["bundle_hash"]
