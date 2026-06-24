from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)
from afritech.core_platform.persistence import InMemoryCorePlatformStore
from afritech.core_platform.signing import sign_packet, signing_key_ready
from afritech.core_platform.trust_node import (
    TrustNodeEnvelope,
    import_trust_envelope,
)
from afritech.fintech.webhook_security import sign_webhook


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    app.include_router(build_public_trust_explorer_router())
    return TestClient(app)


def _auth_headers() -> dict[str, str]:
    token = JWT.create_token(
        "boundary-operator",
        role="OPERATOR",
        organization_id="boundary-org",
    )
    return {"Authorization": f"Bearer {token}"}


def test_payment_intent_is_idempotent() -> None:
    client = _client()
    payload = {
        "intent_id": "idempotent-intent-001",
        "amount": "25.00",
        "destination": "merchant-1",
    }

    first = client.post(
        "/v1/core-platform/payments/execute",
        headers=_auth_headers(),
        json=payload,
    )
    second = client.post(
        "/v1/core-platform/payments/execute",
        headers=_auth_headers(),
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True
    assert (
        first.json()["result"]["trust"]["trust_id"]
        == second.json()["result"]["trust"]["trust_id"]
    )
    assert (
        first.json()["result"]["payment"]["payment_id"]
        == second.json()["result"]["payment"]["payment_id"]
    )


def test_payment_webhook_requires_signature_and_rejects_replay(monkeypatch) -> None:
    secret = "test-webhook-secret"
    monkeypatch.setenv("NOVAPAY_WEBHOOK_SECRET", secret)
    client = _client()
    payment_response = client.post(
        "/v1/core-platform/payments/execute",
        headers=_auth_headers(),
        json={
            "intent_id": "webhook-payment-001",
            "amount": "25.00",
            "destination": "merchant-1",
        },
    )
    payment = payment_response.json()["result"]["payment"]
    payload = {
        "event_id": "evt-settlement-001",
        "provider": payment["provider"],
        "provider_reference": payment["provider_reference"],
        "payment_id": payment["payment_id"],
        "status": "completed",
        "settlement_status": "settled",
    }

    unsigned = client.post("/webhooks/payments", json=payload)
    assert unsigned.status_code == 401

    timestamp = int(time.time())
    headers = {
        "X-NovaPay-Timestamp": str(timestamp),
        "X-NovaPay-Signature": sign_webhook(
            payload,
            timestamp=timestamp,
            secret=secret,
        ),
    }
    accepted = client.post("/webhooks/payments", headers=headers, json=payload)
    duplicate = client.post("/webhooks/payments", headers=headers, json=payload)

    assert accepted.status_code == 200
    assert accepted.json()["signature_verified"] is True
    assert accepted.json()["settlement_authority"] is False
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"
    assert duplicate.json()["trust_action"] == "none"


def test_signed_trust_import_is_verified_and_idempotent() -> None:
    store = InMemoryCorePlatformStore()
    packet = {
        "identity": {"identity_id": "node-actor"},
        "trust": {
            "trust_id": "trust-import-001",
            "organization_id": "node-org",
            "event_type": "core.payment.completed",
            "replay_status": "verified",
        },
    }
    signature = sign_packet(packet).canonical()
    envelope = TrustNodeEnvelope.from_payload(
        {
            "node_id": "validator-melbourne-001",
            "packet": packet,
            "signature": signature,
        }
    )

    first = import_trust_envelope(envelope, store=store)
    second = import_trust_envelope(envelope, store=store)

    assert first.status == "imported"
    assert first.signature_valid is True
    assert first.authority_boundary == "verification_only"
    assert second.status == "already_imported"


def test_federation_rejects_unregistered_node_key() -> None:
    store = InMemoryCorePlatformStore()
    packet = {
        "trust": {
            "trust_id": "trust-import-untrusted",
            "organization_id": "node-org",
            "event_type": "core.payment.completed",
        }
    }
    signature = sign_packet(packet).canonical()
    envelope = TrustNodeEnvelope.from_payload(
        {
            "node_id": "unknown-node",
            "packet": packet,
            "signature": signature,
        }
    )

    with pytest.raises(ValueError, match="untrusted_source_node"):
        import_trust_envelope(
            envelope,
            store=store,
            trusted_public_keys={"registered-node": signature["public_key"]},
        )


def test_production_signing_fails_closed_without_private_key(monkeypatch) -> None:
    monkeypatch.setenv("AFRITECH_ENV", "production")
    monkeypatch.delenv("NOVATRUST_ED25519_PRIVATE_KEY_B64", raising=False)

    assert signing_key_ready() is False
    with pytest.raises(RuntimeError, match="production_novatrust_signing_key_required"):
        sign_packet({"trust": {"trust_id": "must-not-sign-with-dev-key"}})


def test_production_token_issuance_requires_bootstrap_secret(monkeypatch) -> None:
    monkeypatch.setenv("AFRITECH_ENV", "production")
    monkeypatch.setenv("AFRITECH_ALLOW_PILOT_TOKEN_ISSUANCE", "true")
    monkeypatch.setenv("AFRITECH_AUTH_BOOTSTRAP_SECRET", "bootstrap-secret")
    app = FastAPI()
    app.include_router(build_auth_router())
    client = TestClient(app)

    rejected = client.post(
        "/v1/auth/token",
        json={"user_id": "operator", "role": "OPERATOR"},
    )
    accepted = client.post(
        "/v1/auth/token",
        headers={"X-AfriTech-Bootstrap-Secret": "bootstrap-secret"},
        json={"user_id": "operator", "role": "OPERATOR"},
    )

    assert rejected.status_code == 403
    assert accepted.status_code == 200
    assert accepted.json()["token"]
