from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.architecture import integrity_proof
from afritech.api import architecture_proof_api
from afritech.api.architecture_proof_api import build_architecture_proof_router
from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.app import app as production_app
from afritech.ci.runtime_boundary_validator import RuntimeBoundaryValidator


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_architecture_proof_router())
    return TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "operator-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_public_architecture_health_is_ready() -> None:
    client = build_client()

    response = client.get("/public/architecture/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF"
    assert payload["runtime_boundary_status"] == "VERIFIED"
    assert payload["anchor_id"].startswith("anchor-")


def test_public_architecture_proof_returns_anchored_packet() -> None:
    client = build_client()

    response = client.get("/public/architecture/proof")

    assert response.status_code == 200
    payload = response.json()
    proof = payload["proof"]
    assert payload["classification"] == "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF"
    assert proof["runtime_boundary_status"] == "VERIFIED"
    assert proof["verification_packet"]["verification_status"] == "VERIFIED"
    assert proof["public_chain_receipt"]["chain_receipt_id"].startswith("chain-")
    assert proof["registry_entry"]["anchor_id"] == proof["anchor_commitment"]["anchor_id"]


def test_public_architecture_proof_response_is_json_serializable() -> None:
    client = build_client()

    response = client.get("/public/architecture/proof")

    assert response.status_code == 200
    payload = json.loads(response.text)
    json.dumps(payload)
    assert payload["status"] == "generated"
    assert payload["proof_id"] == payload["proof"]["proof_id"]
    assert payload["runtime_boundary_status"] == "VERIFIED"


def test_public_architecture_proof_returns_controlled_payload_when_generation_fails(monkeypatch) -> None:
    def fail_builder():
        raise FileNotFoundError("/app/docs/missing.md")

    monkeypatch.setattr("afritech.api.architecture_proof_api.build_architecture_integrity_proof", fail_builder)
    client = build_client()

    response = client.get("/public/architecture/proof")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "generation_failed"
    assert payload["classification"] == "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF"
    assert payload["runtime_boundary_status"] == "UNKNOWN"
    assert payload["proof"] is None
    assert payload["error"]["code"] == "ARCHITECTURE_PROOF_GENERATION_FAILED"
    assert payload["error"]["type"] == "FileNotFoundError"


def test_production_app_proof_route_never_returns_generic_server_error(monkeypatch) -> None:
    def fail_payload():
        raise RuntimeError("forced production route failure")

    monkeypatch.setattr(architecture_proof_api, "_public_architecture_proof_payload", fail_payload)
    client = TestClient(production_app, raise_server_exceptions=False)

    response = client.get("/public/architecture/proof")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "generation_failed"
    assert payload["error"]["code"] == "ARCHITECTURE_PROOF_GENERATION_FAILED"
    assert payload["error"]["type"] == "RuntimeError"


def test_public_architecture_proof_survives_missing_runtime_artifacts(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(integrity_proof, "BOUNDARY_CONTRACT", tmp_path / "missing-boundary.md")
    monkeypatch.setattr(integrity_proof, "SAFE_IMPORT_CHECKLIST", tmp_path / "missing-checklist.md")
    monkeypatch.setattr(integrity_proof, "GOVERNANCE_ADR", tmp_path / "missing-adr.yaml")
    monkeypatch.setattr(integrity_proof, "GOVERNANCE_RULE", tmp_path / "missing-rule.yaml")
    monkeypatch.setattr(integrity_proof, "GOVERNANCE_BIND", tmp_path / "missing-bind.yaml")
    monkeypatch.setattr(integrity_proof, "SCAN_REPORT", tmp_path / "missing-scan.md")
    monkeypatch.setattr(integrity_proof, "GRAPH_REPORT", tmp_path / "missing-graph.md")

    client = build_client()

    response = client.get("/public/architecture/proof")

    assert response.status_code == 200
    payload = response.json()
    assert payload["proof"]["runtime_boundary_status"] == "VERIFIED"
    assert len(payload["proof"]["artifact_hashes"]) == 7
    assert payload["proof"]["artifact_hashes"][0]["path"] == str(Path(tmp_path / "missing-boundary.md"))


def test_public_architecture_proof_accepts_serialized_boundary_report(monkeypatch) -> None:
    serialized_report = asdict(RuntimeBoundaryValidator().build_report())
    monkeypatch.setattr("afritech.architecture.integrity_proof.build_report", lambda: serialized_report)
    monkeypatch.setattr("afritech.architecture.full_architecture_graph.build_report", lambda: serialized_report)

    client = build_client()

    response = client.get("/public/architecture/proof")

    assert response.status_code == 200
    proof = response.json()["proof"]
    assert proof["runtime_boundary_status"] == "VERIFIED"
    assert proof["startup_safe_closure_size"] == len(serialized_report["startup_modules"])


def test_public_architecture_chain_receipt_resolves_for_anchor() -> None:
    client = build_client()

    proof_response = client.get("/public/architecture/proof")
    anchor_id = proof_response.json()["proof"]["verification_packet"]["anchor_id"]

    response = client.get(f"/public/architecture/chain/{anchor_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "CONTROLLED_PUBLIC_CHAIN_RECEIPT"
    assert payload["status"] == "READY"
    assert payload["chain_receipt"]["anchor_id"] == anchor_id


def test_public_system_integrity_demo_exposes_walkthrough() -> None:
    client = build_client()

    response = client.get("/public/demo/system-integrity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "PARTNER_LIVE_SYSTEM_INTEGRITY_DEMO"
    assert payload["demo_readiness"] == "PARTNER_READY"
    assert payload["walkthrough"][0]["endpoint"] == "/public/architecture/health"


def test_public_chain_networks_expose_promotion_path() -> None:
    client = build_client()

    response = client.get("/public/architecture/chain/networks")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "PUBLIC_CHAIN_PROMOTION_PLAN"
    assert payload["promotion"]["promotion_path"][0]["profile"] == "sepolia"
    assert payload["promotion"]["promotion_path"][1]["profile"] == "mainnet"


def test_system_integrity_dashboard_requires_authentication() -> None:
    client = build_client()

    response = client.get("/v1/system/integrity/dashboard")

    assert response.status_code == 401


def test_system_integrity_dashboard_is_partner_ready() -> None:
    client = build_client()

    response = client.get(
        "/v1/system/integrity/dashboard",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "system_integrity_dashboard"
    assert payload["proof_surface"]["verification_status"] == "VERIFIED"
    assert payload["partner_demo"]["public_demo_ready"] is True


def test_public_trust_dashboard_exposes_public_surfaces() -> None:
    client = build_client()

    response = client.get("/public/trust/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "PUBLIC_TRUST_DASHBOARD"
    assert payload["integrity"]["runtime_boundary_status"] == "VERIFIED"
    assert payload["surfaces"][0]["path"] == "/public/architecture/proof"


def test_blockchain_anchor_publish_endpoint_returns_publication(monkeypatch) -> None:
    client = build_client()

    def fake_publish(**_: object):
        class Publication:
            anchor_id = "anchor-live-001"
            publication_id = "publish-live-001"

            def canonical_dict(self) -> dict[str, object]:
                return {
                    "anchor_id": self.anchor_id,
                    "publication_id": self.publication_id,
                    "chain_receipt_id": "chain-live-001",
                    "transaction_hash": "0xabc123",
                    "status": "CONFIRMED",
                }

        return Publication()

    monkeypatch.setattr(
        "afritech.api.architecture_proof_api.publish_architecture_anchor_with_profile",
        fake_publish,
    )

    response = client.post(
        "/v1/architecture/anchor/blockchain",
        json={"profile": "sepolia", "rpc_url": "https://rpc.example", "signed_tx_hex": "0xsigned"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "BLOCKCHAIN_ARCHITECTURE_ANCHOR_PUBLICATION"
    assert payload["profile"] == "sepolia"
    assert payload["publication"]["status"] == "CONFIRMED"


def test_blockchain_anchor_publish_endpoint_supports_contract_mode(monkeypatch) -> None:
    client = build_client()

    captured: dict[str, object] = {}

    def fake_contract_publish(**kwargs: object):
        captured.update(kwargs)

        class Publication:
            anchor_mode = "smart_contract"
            anchor_id = str(kwargs["anchor_id"])
            publication_id = str(kwargs["publication_id"])

            def canonical_dict(self) -> dict[str, object]:
                return {
                    "anchor_id": kwargs["anchor_id"],
                    "publication_id": kwargs["publication_id"],
                    "anchor_mode": "smart_contract",
                    "method": "anchorProof",
                    "network": "sepolia",
                    "status": "live",
                    "transaction_hash": "0xcontract",
                    "proof_hash": kwargs["proof_hash"],
                }

        return Publication()

    monkeypatch.setattr(
        "afritech.api.architecture_proof_api.publish_architecture_anchor_contract_with_profile",
        fake_contract_publish,
    )

    response = client.post(
        "/v1/architecture/anchor/blockchain",
        json={"profile": "sepolia", "mode": "contract"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "smart_contract"
    assert payload["publication"]["method"] == "anchorProof"
    assert payload["publication"]["status"] == "live"
    assert captured["profile_name"] == "sepolia"
    assert str(captured["proof_hash"])
