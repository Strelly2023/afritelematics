from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from afritech.afripay.audit_sandbox import verify_audit_package
from afritech.afripay.external_packages import (
    build_investor_technical_dossier,
    build_provider_certification_evidence,
    build_regulator_audit_package,
    export_package_artifacts,
    export_provider_certification_artifacts,
)
from afritech.afripay.operations import create_payment_sync
from afritech.afripay.public_validation import verify_signed_evidence
from afritech.afripay.protocol import (
    build_recursive_global_proof,
    sign_recursive_proof_bundle,
)
from afritech.afripay.reconciliation import validate_global_ledger_integrity
from afritech.api.app import app


client = TestClient(app)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _docs_path(*parts: str) -> Path:
    return _repo_root().joinpath(*parts)


def _build_evidence(reference: str, tmp_path: Path):
    create_payment_sync(
        {
            "payer_id": f"assurance.{reference}.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": f"assurance.{reference}.payee",
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
    regulator_package = build_regulator_audit_package(evidence)
    investor_dossier = build_investor_technical_dossier(evidence)
    provider_evidence = build_provider_certification_evidence(evidence)
    regulator_paths = export_package_artifacts(regulator_package, tmp_path / "regulator")
    investor_paths = export_package_artifacts(investor_dossier, tmp_path / "investor")
    provider_paths = export_provider_certification_artifacts(provider_evidence, tmp_path / "provider")
    return {
        "report": report,
        "bundle": bundle,
        "evidence": evidence,
        "regulator_package": regulator_package,
        "investor_dossier": investor_dossier,
        "provider_evidence": provider_evidence,
        "regulator_paths": regulator_paths,
        "investor_paths": investor_paths,
        "provider_paths": provider_paths,
    }


@pytest.mark.django_db
def test_independent_cryptography_review_package(tmp_path: Path):
    built = _build_evidence("regulatory.crypto.001", tmp_path)
    package = built["regulator_package"]

    assert package.package_hash and len(package.package_hash) == 64
    assert "evidence-only" in package.legal_wording.lower()
    assert package.canonical_dict()["schema"] == "afritech.afripay.regulator_audit_package.v1"
    assert package.pdf_bytes().startswith(b"%PDF-")


@pytest.mark.django_db
def test_threat_model_key_management_and_provider_docs_exist():
    docs = {
        "crypto": _docs_path("docs", "compliance", "AFRIPAY_CRYPTOGRAPHY_REVIEW_PACKAGE.md"),
        "threat": _docs_path("docs", "compliance", "AFRIPAY_THREAT_MODEL.md"),
        "pentest": _docs_path("docs", "compliance", "AFRIPAY_PENTEST_SCOPE.md"),
        "keys": _docs_path("docs", "compliance", "AFRIPAY_KEY_MANAGEMENT_REVIEW.md"),
        "provider": _docs_path("docs", "compliance", "AFRIPAY_PROVIDER_CERTIFICATION_EVIDENCE.md"),
        "soc2": _docs_path("docs", "compliance", "AFRIPAY_SOC2_CONTROL_MAPPING.md"),
        "iso": _docs_path("docs", "compliance", "AFRIPAY_ISO27001_CONTROL_ALIGNMENT.md"),
        "submission": _docs_path("docs", "compliance", "AFRIPAY_REGULATOR_SUBMISSION_PACK.md"),
        "narrative": _docs_path("docs", "pitch", "AFRIPAY_INVESTOR_NARRATIVE.md"),
    }

    for path in docs.values():
        assert path.exists()
        body = path.read_text(encoding="utf-8").lower()
        assert len(body) > 200

    assert "insider" in docs["threat"].read_text(encoding="utf-8").lower()
    assert "revocation" in docs["keys"].read_text(encoding="utf-8").lower()
    assert "callback" in docs["provider"].read_text(encoding="utf-8").lower()
    assert "soc2" in docs["soc2"].read_text(encoding="utf-8").lower()
    assert "iso27001" in docs["iso"].read_text(encoding="utf-8").lower()
    assert "fca" in docs["submission"].read_text(encoding="utf-8").lower()
    assert "evidence" in docs["narrative"].read_text(encoding="utf-8").lower()


@pytest.mark.django_db
def test_provider_certification_evidence_package_exports(tmp_path: Path):
    built = _build_evidence("regulatory.provider.001", tmp_path)
    package = built["provider_evidence"]
    paths = built["provider_paths"]

    assert package.package_hash and len(package.package_hash) == 64
    assert package.canonical_dict()["schema"] == "afritech.afripay.provider_certification_evidence.v1"
    assert paths["json"].exists()
    assert paths["pdf"].exists()

    provider_payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    providers = {entry["provider"] for entry in provider_payload["providers"]}

    assert providers == {"flutterwave_sandbox", "mpesa_sandbox"}
    for provider in provider_payload["providers"]:
        assert provider["sandbox_credentials"]
        assert provider["callback_validation"]
        assert provider["reconciliation_validation"]
        assert provider["failure_handling"]
        assert provider["duplicate_delivery_handling"]


@pytest.mark.django_db
def test_regulator_and_investor_packages_export(tmp_path: Path):
    built = _build_evidence("regulatory.export.001", tmp_path)
    regulator_paths = built["regulator_paths"]
    investor_paths = built["investor_paths"]

    assert regulator_paths["json"].exists()
    assert regulator_paths["pdf"].exists()
    assert investor_paths["json"].exists()
    assert investor_paths["pdf"].exists()

    regulator_payload = json.loads(regulator_paths["json"].read_text(encoding="utf-8"))
    investor_payload = json.loads(investor_paths["json"].read_text(encoding="utf-8"))

    assert "evidence-only" in regulator_payload["legal_wording"].lower()
    assert "technical evidence" in investor_payload["summary"].lower()


@pytest.mark.django_db
def test_public_verification_portal_web_ui_is_read_only():
    response = client.get("/public/verify/portal")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "AfriPay Public Verification Portal" in body
    assert "Read-only public surface" in body
    assert "/api/afripay/proofs/artifacts?download_format=json" in body
    assert "/public/trust/dashboard" in body


@pytest.mark.django_db
def test_public_verifier_accepts_valid_evidence(tmp_path: Path):
    built = _build_evidence("regulatory.verify.001", tmp_path)
    result = verify_signed_evidence(json.dumps(built["evidence"].canonical_dict(), sort_keys=True))

    assert result["verified"] is True
    assert result["signature_valid"] is True
    assert result["bundle_valid"] is True
    assert len(result["report_hash"]) == 64


@pytest.mark.django_db
def test_audit_sandbox_accepts_and_rejects_packages(tmp_path: Path):
    built = _build_evidence("regulatory.audit.001", tmp_path)
    evidence_dir = tmp_path / "audit_bundle"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_json = evidence_dir / "recursive_proof_bundle.json"
    evidence_json.write_text(
        json.dumps(built["evidence"].canonical_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    valid_report = verify_audit_package(evidence_dir)
    assert valid_report.verified is True
    assert valid_report.proof_report.verified is True

    tampered = json.loads(evidence_json.read_text(encoding="utf-8"))
    tampered["signature"] = "tampered"
    evidence_json.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    invalid_report = verify_audit_package(evidence_dir)
    assert invalid_report.verified is False


@pytest.mark.django_db
def test_regulator_package_is_self_consistent(tmp_path: Path):
    built = _build_evidence("regulatory.self.001", tmp_path)
    regulator_payload = json.loads(built["regulator_paths"]["json"].read_text(encoding="utf-8"))
    evidence_payload = regulator_payload["evidence"]

    assert regulator_payload["package_hash"] == built["regulator_package"].package_hash
    assert evidence_payload["artifact_hash"] == built["evidence"].artifact_hash
    assert evidence_payload["bundle"]["global_proof_hash"] == built["evidence"].bundle.global_proof_hash
