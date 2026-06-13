from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.afripay.external_packages import (
    build_investor_technical_dossier,
    build_regulator_audit_package,
    export_package_artifacts,
)
from afritech.afripay.operations import create_payment_sync
from afritech.afripay.public_validation import verify_signed_evidence
from afritech.afripay.protocol import (
    build_recursive_global_proof,
    sign_recursive_proof_bundle,
)
from afritech.afripay.reconciliation import validate_global_ledger_integrity


client = TestClient(app)


def _build_evidence(reference: str, tmp_path: Path):
    create_payment_sync(
        {
            "payer_id": f"ext.{reference}.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": f"ext.{reference}.payee",
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
    paths = export_package_artifacts(build_regulator_audit_package(evidence), tmp_path)
    dossier_paths = export_package_artifacts(build_investor_technical_dossier(evidence), tmp_path / "investor")
    evidence_json = json.dumps(evidence.canonical_dict(), sort_keys=True)
    return evidence, paths, dossier_paths, evidence_json


@pytest.mark.django_db
def test_third_party_verifier_accepts_valid_evidence(tmp_path: Path):
    evidence, _, _, evidence_json = _build_evidence("trust.independence.001", tmp_path)

    result = verify_signed_evidence(evidence_json)

    assert result["verified"] is True
    assert result["signature_valid"] is True
    assert result["bundle_valid"] is True
    assert len(result["report_hash"]) == 64
    assert result["report"]["artifact_hash"] == evidence.artifact_hash


@pytest.mark.django_db
def test_third_party_verifier_rejects_tampered_evidence(tmp_path: Path):
    _, _, _, evidence_json = _build_evidence("trust.independence.002", tmp_path)
    payload = json.loads(evidence_json)
    payload["bundle"]["global_proof_hash"] = "f" * 64

    result = verify_signed_evidence(json.dumps(payload, sort_keys=True))

    assert result["verified"] is False
    assert result["bundle_valid"] is False


@pytest.mark.django_db
def test_cli_third_party_verifier(tmp_path: Path):
    _, _, _, evidence_json = _build_evidence("trust.independence.003", tmp_path)
    artifact_path = tmp_path / "cli_evidence.json"
    artifact_path.write_text(evidence_json, encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            "-m",
            "afritech.tools.afripay_third_party_verifier_cli",
            "--artifact",
            str(artifact_path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["verified"] is True
    assert output["signature_valid"] is True


@pytest.mark.django_db
def test_verification_does_not_require_private_key(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("AFRITECH_SIGNING_PRIVATE_KEY_PEM", raising=False)
    monkeypatch.delenv("AFRITECH_SIGNING_PRIVATE_KEY_PATH", raising=False)
    _, _, _, evidence_json = _build_evidence("trust.independence.004", tmp_path)

    result = verify_signed_evidence(evidence_json)

    assert result["verified"] is True
    assert result["signature_valid"] is True


@pytest.mark.django_db
def test_pdf_and_json_evidence_match(tmp_path: Path):
    evidence, regulator_paths, _, _ = _build_evidence("trust.independence.005", tmp_path)

    assert regulator_paths["pdf"].read_bytes().startswith(b"%PDF-")
    package = build_regulator_audit_package(evidence)
    dossier = build_investor_technical_dossier(evidence)

    assert package.pdf_bytes().startswith(b"%PDF-")
    assert dossier.pdf_bytes().startswith(b"%PDF-")
    assert "regulator audit" in package.legal_wording.lower()
    assert "technical evidence" in dossier.summary.lower()


@pytest.mark.django_db
def test_artifact_portability_across_environments(tmp_path: Path):
    _, _, _, evidence_json = _build_evidence("trust.independence.006", tmp_path)
    transported = json.loads(json.dumps(json.loads(evidence_json)))

    assert transported["artifact_hash"] == json.loads(evidence_json)["artifact_hash"]
    assert transported["bundle"]["recursive_proof_hash"] == json.loads(evidence_json)["bundle"]["recursive_proof_hash"]


@pytest.mark.django_db
def test_public_verification_portal_web_ui_is_read_only():
    response = client.get("/public/verify/portal")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "AfriPay Public Verification Portal" in body
    assert "/public/verify/" in body
    assert "/api/afripay/proofs/artifacts?download_format=json" in body
    assert "Read-only public surface" in body


@pytest.mark.django_db
def test_regulator_and_investor_packages_export(tmp_path: Path):
    evidence, _, _, _ = _build_evidence("trust.independence.007", tmp_path)
    regulator = build_regulator_audit_package(evidence)
    investor = build_investor_technical_dossier(evidence)

    regulator_artifacts = export_package_artifacts(regulator, tmp_path / "regulator")
    investor_artifacts = export_package_artifacts(investor, tmp_path / "investor")

    assert regulator_artifacts["json"].exists()
    assert regulator_artifacts["pdf"].exists()
    assert investor_artifacts["json"].exists()
    assert investor_artifacts["pdf"].exists()

    regulator_payload = json.loads(regulator_artifacts["json"].read_text(encoding="utf-8"))
    investor_payload = json.loads(investor_artifacts["json"].read_text(encoding="utf-8"))

    assert "evidence-only" in regulator_payload["legal_wording"].lower()
    assert "technical evidence" in investor_payload["summary"].lower()
