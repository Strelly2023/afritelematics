from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from afritech.architecture.integrity_proof import build_architecture_integrity_proof, build_partner_demo_payload


def test_external_verifier_cli_verifies_local_files(tmp_path: Path) -> None:
    proof = build_architecture_integrity_proof().canonical_dict()
    proof_payload = {
        "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
        "authority_boundary": proof["authority_boundary"],
        "proof": proof,
    }
    chain_payload = {
        "classification": "CONTROLLED_PUBLIC_CHAIN_RECEIPT",
        "status": "READY",
        "anchor_id": proof["verification_packet"]["anchor_id"],
        "chain_receipt": proof["public_chain_receipt"],
        "authority_boundary": proof["authority_boundary"],
    }
    demo_payload = build_partner_demo_payload()

    proof_path = tmp_path / "proof.json"
    chain_path = tmp_path / "chain.json"
    demo_path = tmp_path / "demo.json"
    proof_path.write_text(json.dumps(proof_payload), encoding="utf-8")
    chain_path.write_text(json.dumps(chain_payload), encoding="utf-8")
    demo_path.write_text(json.dumps(demo_payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.tools.external_verifier_cli",
            "--proof",
            str(proof_path),
            "--chain",
            str(chain_path),
            "--demo",
            str(demo_path),
            "--format",
            "text",
        ],
        cwd=Path(__file__).resolve().parents[3],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech External Verifier: VERIFIED" in result.stdout
    assert "demo_readiness: PARTNER_READY" in result.stdout


def test_external_verifier_cli_writes_json_report(tmp_path: Path) -> None:
    proof = build_architecture_integrity_proof().canonical_dict()
    proof_payload = {
        "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
        "authority_boundary": proof["authority_boundary"],
        "proof": proof,
    }
    report_path = tmp_path / "verifier-report.json"
    proof_path = tmp_path / "proof.json"
    proof_path.write_text(json.dumps(proof_payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.tools.external_verifier_cli",
            "--proof",
            str(proof_path),
            "--format",
            "json",
            "--write-report",
            str(report_path),
        ],
        cwd=Path(__file__).resolve().parents[3],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["proof"]["verification_status"] == "VERIFIED"
