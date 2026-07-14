from __future__ import annotations

import subprocess

from fastapi.testclient import TestClient

from afritech.api.app import app


client = TestClient(app)


def test_catalog_lists_required_domains() -> None:
    response = client.get("/v1/platform/api-catalog")
    assert response.status_code == 200
    domains = {item["domain"] for item in response.json()["domains"]}
    assert {
        "platform",
        "novaride",
        "novapay",
        "novaid",
        "novatrust",
        "novaprogramming",
        "operations",
        "public-verification",
        "partner",
    }.issubset(domains)


def test_domain_openapi_has_governance_extensions_and_standard_envelopes() -> None:
    response = client.get("/openapi/novaride.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["x-novatech-domain"] == "novaride"
    assert "NovaTechEnvelope" in spec["components"]["schemas"]
    assert "NovaTechErrorEnvelope" in spec["components"]["schemas"]
    create_ride = spec["paths"]["/v1/rides"]["post"]
    assert create_ride["x-novatech-domain"] == "novaride"
    assert create_ride["x-novatech-risk"]["idempotency-required"] is True
    assert create_ride["x-novatech-evidence"]["replay-required"] is True


def test_high_risk_novapay_endpoint_declares_authority_evidence_and_idempotency() -> None:
    spec = client.get("/openapi/novapay.json").json()
    operation = spec["paths"]["/v1/novapay/payment-intents"]["post"]
    assert operation["x-novatech-authority"]["policy-engine"] == "NovaPower"
    assert operation["x-novatech-authority"]["approval-required"] is True
    assert operation["x-novatech-evidence"]["receipt-required"] is True
    assert operation["x-novatech-risk"]["idempotency-required"] is True


def test_deprecated_route_has_migration_metadata() -> None:
    spec = client.get("/openapi/novaride.json").json()
    operation = spec["paths"]["/passenger/status/{ride_id}"]["get"]
    assert operation["deprecated"] is True
    assert operation["x-replaced-by"] == "/v1/rides/{ride_id}"
    assert operation["x-removal-version"] == "2027.01.0"


def test_signed_publication_contains_contract_hashes() -> None:
    response = client.get("/v1/platform/api-catalog/novapay/publication")
    assert response.status_code == 200
    publication = response.json()
    assert publication["domain"] == "novapay"
    assert publication["openapi_hash"].startswith("sha256:")
    assert publication["schema_hash"].startswith("sha256:")
    assert publication["signature"]["scheme"] == "ed25519"
    assert publication["signature"]["key_id"] == "novatrust-api-contract-dev-01"
    assert publication["sdk_versions"]["novapay-sdk-python"]["contract_version"] == "2026.07.0"


def test_partner_certification_facade_is_contract_driven() -> None:
    status = client.get("/v1/partner/certification/status")
    assert status.status_code == 200
    assert status.json()["production_enabled"] is False
    run = client.post("/v1/partner/certification/run")
    assert run.status_code == 200
    assert run.json()["status"] == "Contract Compatible"
    evidence = client.get("/v1/partner/certification/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["publication"]["domain"] == "partner"


def test_api_catalog_guards_pass() -> None:
    for module in (
        "afritech.guards.guard_api_catalog",
        "afritech.guards.guard_openapi_governance",
        "afritech.guards.guard_api_compatibility",
    ):
        result = subprocess.run(["python3", "-m", module], check=False, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


def test_api_contract_verifier_passes() -> None:
    result = subprocess.run(["python3", "scripts/api/verify_api_contracts.py"], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
