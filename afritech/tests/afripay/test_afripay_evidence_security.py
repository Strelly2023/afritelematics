from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.afripay.audit_sandbox import verify_independent_audit_sandbox
from afritech.afripay.operations import create_payment_sync
from afritech.afripay.public_validation import (
    validate_public_proof_artifact,
    validate_public_proof_file,
)
from afritech.afripay.protocol import (
    build_recursive_global_proof,
    export_signed_proof_evidence,
    proof_artifact_download_payload,
    sign_recursive_proof_bundle,
)
from afritech.afripay.reconciliation import validate_global_ledger_integrity
from afritech.tools.afripay_third_party_verifier_cli import main as verifier_main


def _build_evidence(reference: str, tmp_path: Path):
    create_payment_sync(
        {
            "payer_id": f"evidence.{reference}.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": f"evidence.{reference}.payee",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "120.00",
            "currency": "AUD",
            "reference": reference,
            "preference": "balanced",
        }
    )
    report = validate_global_ledger_integrity(anchor_mode="external_log")
    bundle = build_recursive_global_proof(report)
    evidence = sign_recursive_proof_bundle(bundle)
    paths = export_signed_proof_evidence(evidence, tmp_path)
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    return evidence, paths, payload


@pytest.mark.django_db
def test_public_validator_accepts_signed_artifact_and_exposes_public_key(tmp_path: Path):
    evidence, paths, payload = _build_evidence("trust.break.001", tmp_path)

    report = validate_public_proof_artifact(payload)

    assert report.verified is True
    assert report.signature_verified is True
    assert report.structural_verified is True
    assert payload["signer_public_key_pem"].startswith("-----BEGIN PUBLIC KEY-----")
    assert report.bundle_hash == evidence.bundle.report_hash()
    assert paths["pdf"].read_bytes().startswith(b"%PDF-")


@pytest.mark.django_db
def test_public_validator_detects_signature_forgery(tmp_path: Path):
    _, _, payload = _build_evidence("trust.break.002", tmp_path)
    forged = dict(payload)
    forged["signature"] = "deadbeef"

    report = validate_public_proof_artifact(forged)

    assert report.verified is False
    assert report.signature_verified is False
    assert "signature_verification_failed" in report.trust_breaks


@pytest.mark.django_db
def test_public_validator_detects_artifact_tampering(tmp_path: Path):
    _, _, payload = _build_evidence("trust.break.003", tmp_path)
    tampered = json.loads(json.dumps(payload))
    tampered["bundle"]["global_proof_hash"] = "f" * 64

    report = validate_public_proof_artifact(tampered)

    assert report.verified is False
    assert report.structural_verified is False
    assert "artifact_hash_mismatch" in report.trust_breaks


@pytest.mark.django_db
def test_public_validator_roundtrip_matches_file_loader(tmp_path: Path):
    _, paths, payload = _build_evidence("trust.break.004", tmp_path)

    report_from_payload = validate_public_proof_artifact(payload)
    report_from_file = validate_public_proof_file(paths["json"])

    assert report_from_payload.report_hash() == report_from_file.report_hash()
    assert report_from_file.verified is True


@pytest.mark.django_db
def test_independent_audit_sandbox_verifies_exported_artifacts(tmp_path: Path):
    _, paths, _ = _build_evidence("trust.break.005", tmp_path)

    sandbox_report = verify_independent_audit_sandbox(tmp_path)

    assert sandbox_report.verified is True
    assert sandbox_report.pdf_verified is True
    assert sandbox_report.proof_report.verified is True
    assert sandbox_report.artifact_path.endswith("recursive_proof_bundle.json")
    assert sandbox_report.pdf_path.endswith("recursive_proof_bundle.pdf")


@pytest.mark.django_db
def test_third_party_verifier_cli_with_explicit_public_key(tmp_path: Path, capsys):
    _, paths, payload = _build_evidence("trust.break.006", tmp_path)
    key_path = tmp_path / "public_key.pem"
    key_path.write_text(payload["signer_public_key_pem"], encoding="utf-8")
    report_path = tmp_path / "verification_report.json"

    exit_code = verifier_main(
        [
            "--artifact",
            str(paths["json"]),
            "--public-key",
            str(key_path),
            "--sandbox",
            "--write-report",
            str(report_path),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "verified" in captured.out.lower()
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["verified"] is True
    assert report["proof_report"]["verified"] is True


@pytest.mark.django_db
def test_download_payload_contains_signing_evidence(tmp_path: Path):
    evidence, _, _ = _build_evidence("trust.break.007", tmp_path)
    payload = proof_artifact_download_payload(evidence)

    assert payload["signature_verified"] is True
    assert payload["signer_public_key_pem"].startswith("-----BEGIN PUBLIC KEY-----")
    assert payload["download"]["json_filename"] == "recursive_proof_bundle.json"
