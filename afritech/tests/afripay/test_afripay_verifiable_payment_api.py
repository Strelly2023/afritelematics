from __future__ import annotations

from importlib import import_module

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from afritech.afripay.operations import create_payment_sync
from afritech.chain.types import ChainReceipt


def views():
    return import_module("afriride_system.django_app.apps.afripay.views")


def models():
    return import_module("afriride_system.django_app.apps.afripay.models")


def _authed_request(factory, method: str, path: str, scopes: set[str] | None = None, data: dict | None = None):
    request = getattr(factory, method)(path, data or {}, format="json")
    request.afripay_principal = type("P", (), {"subject": "ops", "scopes": tuple(scopes or ())})()
    request.afripay_scopes = set(scopes or set())
    return request


@pytest.mark.django_db
def test_proof_export_transaction_payload():
    create_payment_sync(
        {
            "payer_id": "proof.api.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "proof.api.payee",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "42.00",
            "currency": "AUD",
            "reference": "proof.api.tx.001",
            "preference": "balanced",
        }
    )

    request = _authed_request(
        APIRequestFactory(),
        "get",
        "/api/afripay/proofs/export?reference=proof.api.tx.001",
        {"proofs:read"},
    )

    response = views().proof_export_view(request)

    assert response.status_code == 200
    assert response.data["scope"] == "transaction"
    assert response.data["reference"] == "proof.api.tx.001"
    assert len(response.data["proof_hash"]) == 64
    assert response.data["transaction_inclusion_proof"]["verified"] is True
    assert response.data["transaction_zk_attestation"]["verified"] is True


@pytest.mark.django_db
def test_proof_export_global_payload():
    create_payment_sync(
        {
            "payer_id": "proof.api.global.payer",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "proof.api.global.payee",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "50.00",
            "currency": "AUD",
            "reference": "proof.api.global.tx.001",
            "preference": "balanced",
        }
    )

    request = _authed_request(
        APIRequestFactory(),
        "get",
        "/api/afripay/proofs/export",
        {"proofs:read"},
    )

    response = views().proof_export_view(request)

    assert response.status_code == 200
    assert response.data["scope"] == "global"
    assert response.data["report"]["verified"] is True
    assert len(response.data["global_proof_hash"]) == 64


@pytest.mark.django_db
def test_proof_anchor_mainnet_requests_live_publication(monkeypatch):
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

    monkeypatch.setattr("afriride_system.django_app.apps.afripay.views.publish_anchor", fake_publish)

    request = _authed_request(
        APIRequestFactory(),
        "post",
        "/api/afripay/proofs/anchor",
        {"proofs:write"},
        {"proof_hash": "a" * 64, "profile_name": "mainnet"},
    )

    response = views().proof_anchor_view(request)

    assert response.status_code == 200
    assert response.data["status"] == "anchored"
    assert captured["profile_name"] == "mainnet"
    assert captured["require_live"] is True
    assert response.data["chain_receipt"]["network"] == "mainnet"


@pytest.mark.django_db
def test_proof_anchor_rejects_invalid_profile():
    request = _authed_request(
        APIRequestFactory(),
        "post",
        "/api/afripay/proofs/anchor",
        {"proofs:write"},
        {"proof_hash": "a" * 64, "profile_name": "unknown"},
    )

    response = views().proof_anchor_view(request)

    assert response.status_code == 400

