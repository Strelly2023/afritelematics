from __future__ import annotations

import json
import os
import shutil
from importlib import import_module
from pathlib import Path

import pytest
from rest_framework.test import APIRequestFactory

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.protocol import (
    anchor_and_verify_protocol_proof,
    build_recursive_global_proof,
    export_signed_proof_evidence,
    proof_artifact_download_payload,
    render_audit_pdf,
    sign_recursive_proof_bundle,
)
from afritech.afripay.reconciliation import validate_global_ledger_integrity


def views():
    return import_module("afriride_system.django_app.apps.afripay.views")


def _authed_request(factory, method: str, path: str, scopes: set[str] | None = None, data: dict | None = None):
    request = getattr(factory, method)(path, data or {}, format="json")
    request.afripay_principal = type("P", (), {"subject": "auditor", "scopes": tuple(scopes or ())})()
    request.afripay_scopes = set(scopes or set())
    return request


@pytest.mark.django_db
def test_recursive_proof_generates_auditable_artifacts(tmp_path: Path):
    create_payment_sync(
        {
            "payer_id": "evidence.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "evidence.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "120.00",
            "currency": "AUD",
            "reference": "evidence.tx.001",
            "preference": "balanced",
        }
    )

    report = validate_global_ledger_integrity(anchor_mode="external_log")
    bundle = build_recursive_global_proof(report)
    evidence = sign_recursive_proof_bundle(bundle)
    paths = export_signed_proof_evidence(evidence, tmp_path)

    assert bundle.verified is True
    assert evidence.verified is True
    assert paths["json"].exists()
    assert paths["pdf"].exists()

    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["bundle"]["global_proof_hash"] == report.global_proof_hash
    assert payload["bundle"]["recursive_merkle_root"] == bundle.recursive_merkle_root
    assert payload["signature_verified"] is True
    assert len(payload["artifact_hash"]) == 64
    assert len(payload["bundle"]["recursive_proof_hash"]) == 64
    assert paths["pdf"].read_bytes().startswith(b"%PDF-")


@pytest.mark.django_db
def test_recursive_proof_is_deterministic():
    create_payment_sync(
        {
            "payer_id": "deterministic.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "deterministic.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "55.00",
            "currency": "AUD",
            "reference": "deterministic.tx.001",
            "preference": "balanced",
        }
    )

    report1 = validate_global_ledger_integrity(anchor_mode="external_log")
    report2 = validate_global_ledger_integrity(anchor_mode="external_log")
    proof1 = sign_recursive_proof_bundle(build_recursive_global_proof(report1))
    proof2 = sign_recursive_proof_bundle(build_recursive_global_proof(report2))

    assert proof1.artifact_hash == proof2.artifact_hash
    assert proof1.bundle.report_hash() == proof2.bundle.report_hash()
    assert proof1.signature == proof2.signature


@pytest.mark.django_db
def test_downloadable_artifact_api_returns_attachment_json():
    create_payment_sync(
        {
            "payer_id": "download.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "download.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "75.00",
            "currency": "AUD",
            "reference": "download.tx.001",
            "preference": "balanced",
        }
    )

    request = _authed_request(
        APIRequestFactory(),
        "get",
        "/api/afripay/proofs/artifacts?download_format=json",
        {"proofs:read"},
    )
    response = views().proof_artifacts_view(request)

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith('attachment; filename="afripay_proof_bundle.json"')
    payload = json.loads(response.content.decode("utf-8"))
    assert payload["verified"] is True
    assert payload["bundle"]["verified"] is True
    assert len(payload["signature"]) > 0
    assert len(payload["artifact_hash"]) == 64


@pytest.mark.django_db
def test_downloadable_artifact_api_returns_pdf_attachment():
    create_payment_sync(
        {
            "payer_id": "download.user.003",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "download.user.004",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "95.00",
            "currency": "AUD",
            "reference": "download.tx.002",
            "preference": "balanced",
        }
    )

    request = _authed_request(
        APIRequestFactory(),
        "get",
        "/api/afripay/proofs/artifacts?download_format=pdf",
        {"proofs:read"},
    )
    response = views().proof_artifacts_view(request)

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith('attachment; filename="afripay_proof_bundle.pdf"')
    assert response.content.startswith(b"%PDF-")


@pytest.mark.django_db
def test_protocol_anchor_verification_can_be_evidenced(monkeypatch):
    captured: dict[str, object] = {}

    def fake_publish(proof_hash: str, *, profile_name: str | None = None, require_live: bool = False):
        captured["proof_hash"] = proof_hash
        captured["profile_name"] = profile_name
        captured["require_live"] = require_live
        from afritech.chain.types import ChainReceipt

        return ChainReceipt(
            tx_hash="0xdeadbeef",
            network="mainnet",
            block_number=123456,
            explorer_url="https://etherscan.io/tx/0xdeadbeef",
            status="live",
            chain_id=1,
            chain_name="Ethereum Mainnet",
            proof_hash=proof_hash,
            authority="smart_contract",
            source="test",
        )

    monkeypatch.setattr("afritech.afripay.protocol.publish_anchor", fake_publish)
    monkeypatch.setattr("afritech.afripay.protocol.verify_anchor_on_chain", lambda anchor_id, proof_hash, profile_name=None: True)

    result = anchor_and_verify_protocol_proof("d" * 64, profile_name="mainnet", require_live=True)

    assert result.verified is True
    assert result.onchain_verified is True
    assert captured["proof_hash"] == "d" * 64
    assert captured["require_live"] is True


@pytest.mark.django_db
def test_groth16_evidence_is_archived_when_assets_configured(tmp_path: Path):
    wasm_path = os.environ.get("AFRIPAY_GROTH16_WASM_PATH")
    zkey_path = os.environ.get("AFRIPAY_GROTH16_ZKEY_PATH")
    verification_key_path = os.environ.get("AFRIPAY_GROTH16_VERIFICATION_KEY_PATH")
    snarkjs_path = os.environ.get("AFRIPAY_SNARKJS_PATH", "snarkjs")

    if not wasm_path or not zkey_path or not verification_key_path:
        pytest.skip("real Groth16 assets are not configured")
    if not Path(wasm_path).exists() or not Path(zkey_path).exists() or not Path(verification_key_path).exists():
        pytest.skip("real Groth16 assets are missing")
    if shutil.which(snarkjs_path) is None:
        pytest.skip("snarkjs binary is missing")

    create_payment_sync(
        {
            "payer_id": "zk.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "zk.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "101.00",
            "currency": "AUD",
            "reference": "zk.tx.001",
            "preference": "balanced",
        }
    )

    report = validate_global_ledger_integrity(anchor_mode="external_log")
    bundle = build_recursive_global_proof(report)
    evidence = sign_recursive_proof_bundle(bundle)
    paths = export_signed_proof_evidence(evidence, tmp_path)

    assert bundle.backend == "groth16"
    assert bundle.backend_verified is True
    assert evidence.verified is True
    assert paths["json"].exists()
    assert paths["pdf"].exists()
    archived = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert archived["bundle"]["backend"] == "groth16"
    assert archived["bundle"]["recursive_proof"]["scheme"] == "groth16"


@pytest.mark.django_db
def test_download_payload_exposes_download_metadata():
    create_payment_sync(
        {
            "payer_id": "meta.user.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "meta.user.002",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "45.00",
            "currency": "AUD",
            "reference": "meta.tx.001",
            "preference": "balanced",
        }
    )

    report = validate_global_ledger_integrity(anchor_mode="external_log")
    bundle = build_recursive_global_proof(report)
    evidence = sign_recursive_proof_bundle(bundle)
    payload = proof_artifact_download_payload(evidence)

    assert payload["download"]["json_filename"] == "recursive_proof_bundle.json"
    assert payload["download"]["pdf_filename"] == "recursive_proof_bundle.pdf"
    assert payload["signature_verified"] is True
