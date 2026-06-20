from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afriprogramming_control_api import build_afriprogramming_control_router
from afritech.afriprogramming.assurance import (
    CryptoStorageHardeningService,
    RiskPredictionService,
    TrustFabricService,
)
from afritech.afriprogramming.persistence import PlatformStore


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_afriprogramming_control_router())
    return TestClient(app)


def auth_headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def build_store(tmp_path: Path) -> PlatformStore:
    return PlatformStore(db_path=tmp_path / "novaprogramming-v8.sqlite3")


def test_crypto_storage_hardening_registers_backends_and_certificates(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    service = CryptoStorageHardeningService(store)

    backend = service.register_backend(
        organization_id=org_id,
        key_family="audit",
        backend_name="vault-audit",
        provider_ref="vault://audit/keys",
        key_arn="arn:aws:kms:us-east-1:123:key/audit",
        hardware_bound=True,
    )
    chain = service.issue_certificate_chain(
        organization_id=org_id,
        key_family="audit",
        subject="node-a",
        issuer="NovaProgramming PKI",
    )
    verification = service.verify_certificate_chain(org_id)

    assert backend["backend_name"] == "vault-audit"
    assert chain["chain_hash"]
    assert verification["valid"] is True
    assert service.available_backends(org_id)["backends"][0]["backend_name"] == "vault-audit"


def test_trust_fabric_region_graph_identity_and_signed_http_flow(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    service = TrustFabricService(store)

    region_a = service.register_region(
        organization_id=org_id,
        region_name="melbourne",
        country_code="AU",
        provider="aws",
    )
    region_b = service.register_region(
        organization_id=org_id,
        region_name="singapore",
        country_code="SG",
        provider="aws",
    )
    link = service.link_regions(
        organization_id=org_id,
        source_region_id=region_a["region_id"],
        target_region_id=region_b["region_id"],
        latency_ms=72,
        trust_score=96,
    )
    binding = service.identity_bind(
        organization_id=org_id,
        user_id="human-1",
        device_id="device-1",
        human_trust_score=95,
        device_trust_score=93,
        attestation={"device": "managed", "user": "verified"},
    )
    graph = service.decentralized_trust_graph(org_id)
    signed = service.sign_request(
        organization_id=org_id,
        peer_organization_id="peer-org",
        method="POST",
        url="https://peer.example/api/trust",
        headers={"X-Test": "1"},
        body={"hello": "world"},
    )
    verified = service.verify_request(signed)
    negotiation = service.negotiate(
        organization_id=org_id,
        peer_organization_id="peer-org",
        proposed_terms={"receipt": "required"},
        trust_offer=92,
        trust_floor=80,
    )

    assert link["source_region_id"] == region_a["region_id"]
    assert binding["user_id"] == "human-1"
    assert graph["graph_score"] >= 30
    assert verified["valid"] is True
    assert negotiation["decision"] in {"accept", "counter"}
    assert service.identity_score(org_id)["identity_bound"] is True


def test_risk_prediction_uses_fabric_signals(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    fabric = TrustFabricService(store)
    fabric.register_region(
        organization_id=org_id,
        region_name="melbourne",
        country_code="AU",
        provider="aws",
    )
    risk_service = RiskPredictionService(store)

    prediction = risk_service.predict(
        organization_id=org_id,
        entity_type="organization",
        entity_id=org_id,
        horizon_days=30,
    )

    assert prediction["organization_id"] == org_id
    assert 0 <= prediction["risk_score"] <= 100
    assert risk_service.latest(org_id)["prediction_id"] == prediction["prediction"]["prediction_id"]


def test_v8_api_surface_exposes_crypto_fabric_and_risk_routes() -> None:
    client = build_client()
    org_id = f"org-{uuid4().hex[:8]}"
    headers = auth_headers("VERIFIER", "verifier-v8", org_id)

    crypto = client.post(
        "/v1/novaprogramming/crypto/backends",
        json={
            "backend_name": "kms-audit",
            "provider_ref": "aws-kms://audit",
            "key_family": "audit",
            "hardware_bound": True,
        },
        headers=headers,
    )
    assert crypto.status_code == 200

    issue = client.post(
        "/v1/novaprogramming/crypto/chains",
        json={"subject": "node-a", "issuer": "NovaProgramming PKI", "key_family": "audit"},
        headers=headers,
    )
    assert issue.status_code == 200

    stream = client.post(
        "/v1/novaprogramming/stream/backends",
        json={"topic_name": "trust-stream", "description": "redis-streams", "retention_days": 7},
        headers=headers,
    )
    assert stream.status_code == 200

    region_a = client.post(
        "/v1/novaprogramming/trust/fabric/regions",
        json={"region_name": "melbourne", "country_code": "AU", "provider": "aws"},
        headers=headers,
    )
    region_b = client.post(
        "/v1/novaprogramming/trust/fabric/regions",
        json={"region_name": "singapore", "country_code": "SG", "provider": "aws"},
        headers=headers,
    )
    assert region_a.status_code == 200
    assert region_b.status_code == 200

    link = client.post(
        "/v1/novaprogramming/trust/fabric/regions/link",
        json={
            "source_region_id": region_a.json()["region"]["region_id"],
            "target_region_id": region_b.json()["region"]["region_id"],
            "latency_ms": 66,
            "trust_score": 95,
        },
        headers=headers,
    )
    assert link.status_code == 200

    signed = client.post(
        "/v1/novaprogramming/trust/fabric/http-request",
        json={
            "peer_organization_id": "peer-org",
            "method": "POST",
            "url": "https://peer.example/api/trust",
            "headers": {"X-Test": "1"},
            "body": {"hello": "world"},
        },
        headers=headers,
    )
    assert signed.status_code == 200
    verify = client.post(
        "/v1/novaprogramming/trust/fabric/http-request/verify",
        json={"envelope": signed.json()["request"]},
        headers=headers,
    )
    assert verify.status_code == 200
    assert verify.json()["valid"] is True

    bind = client.post(
        "/v1/novaprogramming/identity/bind",
        json={
            "user_id": "human-1",
            "device_id": "device-1",
            "human_trust_score": 92,
            "device_trust_score": 94,
            "attestation": {"device": "managed"},
        },
        headers=headers,
    )
    assert bind.status_code == 200

    risk = client.post(
        "/v1/novaprogramming/risk/predict",
        json={"entity_type": "organization", "entity_id": org_id, "horizon_days": 30},
        headers=headers,
    )
    assert risk.status_code == 200
    assert "risk_score" in risk.json()

    negotiation = client.post(
        "/v1/novaprogramming/negotiation/start",
        json={
            "peer_organization_id": "peer-org",
            "proposed_terms": {"receipt": "required"},
            "trust_offer": 92,
            "trust_floor": 80,
        },
        headers=headers,
    )
    assert negotiation.status_code == 200

    assert client.get("/v1/novaprogramming/crypto/backends", headers=headers).status_code == 200
    assert client.post("/v1/novaprogramming/crypto/chains/verify", headers=headers).status_code == 200
    assert client.get("/v1/novaprogramming/stream/backends", headers=headers).status_code == 200
    assert client.get("/v1/novaprogramming/trust/fabric/graph", headers=headers).status_code == 200
    assert client.get("/v1/novaprogramming/identity/bindings", headers=headers).status_code == 200
    assert client.get("/v1/novaprogramming/risk/predictions", headers=headers).status_code == 200
    assert client.get("/v1/novaprogramming/negotiation/sessions", headers=headers).status_code == 200


def test_django_urlconf_import_smoke() -> None:
    import afritech.api.urls as urls

    paths = {str(pattern.pattern) for pattern in urls.urlpatterns}
    assert "novaprogramming/crypto/backends" in paths
    assert "novaprogramming/trust/fabric/graph" in paths
    assert "novaprogramming/negotiation/sessions" in paths
