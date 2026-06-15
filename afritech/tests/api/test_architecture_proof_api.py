from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.architecture import integrity_proof
from afritech.architecture.anchor_indexer import (
    ANCHOR_INDEX_STORE,
    AnchorIndexStore,
    AnchorIndexEntry,
    JsonFileAnchorIndexBackend,
)
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
    assert payload["promotion"]["promotion_path"][1]["profile"] == "base-sepolia"
    assert payload["promotion"]["promotion_path"][2]["profile"] == "mainnet"


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
    assert payload["anchors"]["dashboard"] == "/public/architecture/anchors/dashboard"


def test_public_anchor_dashboard_and_map_are_available() -> None:
    ANCHOR_INDEX_STORE.clear()
    client = build_client()

    status_response = client.get("/public/architecture/anchors/status")
    dashboard_response = client.get("/public/architecture/anchors/dashboard")
    map_response = client.get("/public/architecture/blockchain/map")

    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["classification"] == "BLOCKCHAIN_ANCHOR_STATUS"
    assert "backend" in status_payload["index"]
    assert "stream" in status_payload

    assert dashboard_response.status_code == 200
    assert "Architecture Anchor Dashboard" in dashboard_response.text

    assert map_response.status_code == 200
    payload = map_response.json()
    assert payload["classification"] == "AFRITECH_BLOCKCHAIN_ARCHITECTURE_MAP"
    assert "Anchor indexer" in payload["stack"]
    assert payload["promotion_plan"]["promotion_path"][1]["profile"] == "base-sepolia"
    assert "L2" in payload["promotion_plan"]["promotion_path"][1]["goal"]


def test_public_anchor_verification_report_exposes_etherscan_packet() -> None:
    ANCHOR_INDEX_STORE.clear()
    client = build_client()

    response = client.get("/public/architecture/anchors/verification")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "ETHERSCAN_CONTRACT_VERIFICATION_REPORT"
    assert "abi_fingerprint" in payload
    assert payload["architecture_map"] == "/public/architecture/blockchain/map"
    assert payload["anchor_abi"] == "/public/architecture/anchors/verification/abi"


def test_public_anchor_verification_abi_and_source_are_public() -> None:
    client = build_client()

    abi_response = client.get("/public/architecture/anchors/verification/abi")
    source_response = client.get("/public/architecture/anchors/verification/source")

    assert abi_response.status_code == 200
    assert abi_response.json()["classification"] == "ETHERSCAN_CONTRACT_ABI"
    assert source_response.status_code == 200
    source_payload = source_response.json()
    assert source_payload["classification"] == "ETHERSCAN_CONTRACT_SOURCE"
    assert "contract ArchitectureAnchor" in source_payload["source"]


def test_public_anchor_stream_status_is_read_only() -> None:
    client = build_client()

    response = client.get("/public/architecture/anchors/stream/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "BLOCKCHAIN_ANCHOR_EVENT_SUBSCRIPTION_STATUS"
    assert payload["authority_boundary"] == "event_subscription_is_read_only_and_indexing_only"
    assert payload["broadcast"]["classification"] == "BLOCKCHAIN_ANCHOR_STREAM_STATUS"


def test_public_anchor_stream_replay_is_read_only() -> None:
    client = build_client()

    response = client.get("/public/architecture/anchors/stream/replay?after_sequence=0&limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "BLOCKCHAIN_ANCHOR_STREAM_REPLAY"
    assert payload["status"] == "READY"
    assert payload["after_sequence"] == 0
    assert "events" in payload


def test_public_anchor_stream_websocket_reports_status() -> None:
    client = build_client()

    with client.websocket_connect("/public/architecture/anchors/stream/ws") as websocket:
        payload = websocket.receive_json()
        assert payload["classification"] == "BLOCKCHAIN_ANCHOR_STREAM_SOCKET"
        assert payload["status"] == "CONNECTED"
        websocket.send_text("status")
        status_payload = websocket.receive_json()
        assert status_payload["status"] == "READY"
        assert status_payload["stream"]["classification"] == "BLOCKCHAIN_ANCHOR_EVENT_SUBSCRIPTION_STATUS"


def test_public_anchor_reconciliation_reports_cross_network_state() -> None:
    client = build_client()

    response = client.get("/public/architecture/anchors/reconciliation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "BLOCKCHAIN_ANCHOR_CROSS_NETWORK_RECONCILIATION"
    assert "entries" in payload
    assert payload["invariants"][0]["id"].startswith("RECONCILIATION-")
    assert "DIVERGENT" in payload["resolution_strategies"]


def test_public_evidence_consistency_policy_is_formalized() -> None:
    client = build_client()

    response = client.get("/public/architecture/evidence/policy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "BLOCKCHAIN_EVIDENCE_CONSISTENCY_POLICY"
    assert payload["streaming_policy"]["primary_transport"] == "websocket"
    assert payload["streaming_policy"]["poll_endpoint_role"] == "operator_backfill_only"
    assert payload["mainnet_gate"]["requires_no_divergence"] is True
    assert any(item["id"] == "RECONCILIATION-002" for item in payload["invariants"])


def test_public_evidence_operational_semantics_is_machine_readable() -> None:
    client = build_client()

    response = client.get("/public/architecture/evidence/semantics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "BLOCKCHAIN_EVIDENCE_OPERATIONAL_SEMANTICS"
    assert payload["truth_model"]["truth_authority"] == "Replay/Proof"
    assert len(payload["semantics_hash"]) == 64
    assert payload["lifecycle"]["initial_state"] == "GOVERNED_DECISION"
    assert "ADR_TO_PROOF" in {transition["id"] for transition in payload["transitions"]}
    assert payload["terminal_states"]["DIVERGENT"]["mainnet_blocking"] is True


def test_public_governed_evidence_protocol_combines_platform_protocol_and_governance() -> None:
    client = build_client()

    response = client.get("/public/architecture/evidence/protocol")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "GOVERNED_EVIDENCE_OPERATING_PROTOCOL"
    assert payload["status"] == "READY"
    assert payload["protocol_version"] == "1.0.0"
    assert len(payload["protocol_hash"]) == 64
    assert len(payload["semantics_hash"]) == 64
    assert len(payload["policy_hash"]) == 64
    assert payload["system_identity"]["name"] == "Governed Evidence Operating Platform"
    assert payload["authority_model"]["truth_authority"] == "Replay/Proof"
    assert payload["public_surfaces"]["protocol"] == "/public/architecture/evidence/protocol"
    assert {artifact["id"] for artifact in payload["governance_artifacts"]} == {
        "ADR-0047",
        "RULE-067",
        "BIND-045",
    }
    assert all(len(artifact["sha256"]) == 64 for artifact in payload["governance_artifacts"])
    assert (
        "afritech.ci.afritech_governed_evidence_protocol_validator"
        in payload["governance_model"]["required_validators"]
    )


def test_public_anchor_reconciliation_preserves_same_anchor_across_networks() -> None:
    ANCHOR_INDEX_STORE.clear()
    client = build_client()
    proof_hash = "b" * 64

    for sequence, network, chain_id, tx_hash in (
        (1, "sepolia", 11155111, "0xsepolia"),
        (2, "base-sepolia", 84532, "0xbase"),
    ):
        ANCHOR_INDEX_STORE.remember(
            AnchorIndexEntry(
                anchor_id="anchor-cross-network-001",
                publication_id=f"publish-cross-network-{sequence}",
                proof_hash=proof_hash,
                network=network,
                chain_id=chain_id,
                chain_name=network,
                contract_address="0x0000000000000000000000000000000000000001",
                transaction_hash=tx_hash,
                block_number=sequence,
                explorer_url=f"https://example.test/{tx_hash}",
                anchor_mode="smart_contract",
                status="live",
                source="test",
                sequence=sequence,
                contract_explorer_url="https://example.test/address/1",
                etherscan_verification_stage="EVENT_STREAMED",
                authority_boundary="anchor_index_is_read_only",
                meta={},
            )
        )

    index_response = client.get("/public/architecture/anchors")
    detail_response = client.get("/public/architecture/anchors/anchor-cross-network-001")
    reconciliation_response = client.get("/public/architecture/anchors/reconciliation")

    assert index_response.status_code == 200
    assert index_response.json()["count"] == 2
    assert detail_response.status_code == 200
    assert len(detail_response.json()["related_entries"]) == 2
    payload = reconciliation_response.json()
    row = payload["entries"][0]
    assert row["network_count"] == 2
    assert row["observed_networks"] == ["base-sepolia", "sepolia"]
    assert row["reconciliation_status"] == "RECONCILED"
    assert row["reconciled"] is True
    assert row["mainnet_blocking"] is False

    gate_response = client.get("/public/architecture/anchors/mainnet-promotion-gate")
    assert gate_response.status_code == 200
    gate = gate_response.json()
    assert gate["classification"] == "BLOCKCHAIN_MAINNET_PROMOTION_GATE"
    assert gate["approved"] is True
    assert gate["status"] == "APPROVED_FOR_MAINNET_PUBLICATION"


def test_public_anchor_reconciliation_divergence_has_resolution_strategy() -> None:
    ANCHOR_INDEX_STORE.clear()
    client = build_client()
    proof_hash = "c" * 64

    for sequence, anchor_id, tx_hash in (
        (1, "anchor-divergent-001", "0xdivergent1"),
        (2, "anchor-divergent-002", "0xdivergent2"),
    ):
        ANCHOR_INDEX_STORE.remember(
            AnchorIndexEntry(
                anchor_id=anchor_id,
                publication_id=f"publish-divergent-{sequence}",
                proof_hash=proof_hash,
                network="sepolia" if sequence == 1 else "base-sepolia",
                chain_id=11155111 if sequence == 1 else 84532,
                chain_name="divergent",
                contract_address="0x0000000000000000000000000000000000000001",
                transaction_hash=tx_hash,
                block_number=sequence,
                explorer_url=f"https://example.test/{tx_hash}",
                anchor_mode="smart_contract",
                status="live",
                source="test",
                sequence=sequence,
                contract_explorer_url="https://example.test/address/1",
                etherscan_verification_stage="EVENT_STREAMED",
                authority_boundary="anchor_index_is_read_only",
                meta={},
            )
        )

    reconciliation_response = client.get("/public/architecture/anchors/reconciliation")
    resolution_response = client.get("/public/architecture/anchors/reconciliation/resolution")
    gate_response = client.get("/public/architecture/anchors/mainnet-promotion-gate")

    row = reconciliation_response.json()["entries"][0]
    assert row["reconciliation_status"] == "DIVERGENT"
    assert row["resolution_strategy"]["resolution_state"] == "GOVERNANCE_REVIEW_REQUIRED"
    assert row["mainnet_blocking"] is True

    resolution = resolution_response.json()
    assert resolution["classification"] == "BLOCKCHAIN_ANCHOR_RECONCILIATION_RESOLUTION"
    assert resolution["entries"][0]["resolution_strategy"]["forbidden_actions"][0] == "promote_to_mainnet"

    gate = gate_response.json()
    assert gate["approved"] is False
    assert gate["status"] == "BLOCKED"
    assert gate["blocking_findings"][0]["code"] == "DIVERGENT_EVIDENCE"


def test_public_adr_hash_preview_is_public() -> None:
    client = build_client()

    response = client.get("/public/architecture/adr/ADR-0045/hash")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "ADR_HASH_RECORD"
    assert payload["adr_id"] == "ADR-0045"
    assert len(payload["content_hash"]) == 64


def test_public_adr_contract_link_packet_is_public() -> None:
    client = build_client()

    response = client.get("/public/architecture/adr/ADR-0045/contract-link?profile=base-sepolia")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "ADR_CONTRACT_LINK_PACKET"
    assert payload["contract_signature"] == "anchorProof(string,bytes32)"
    assert payload["verification_call"]["signature"] == "verifyAnchor(string,bytes32)"
    assert payload["network"] == "base-sepolia"
    assert payload["contract_arguments"]["anchorId"] == "adr-adr-0045"
    assert payload["contract_arguments"]["proofHash"].startswith("0x")


def test_public_anchor_explorer_shell_is_available() -> None:
    client = build_client()

    response = client.get("/public/architecture/anchors/explorer")

    assert response.status_code == 200
    assert "AfriTech Anchor Explorer" in response.text
    assert "/public/architecture/adr/ADR-0045/contract-link" in response.text


def test_blockchain_anchor_publish_endpoint_returns_publication(monkeypatch) -> None:
    ANCHOR_INDEX_STORE.clear()
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
    assert payload["index_record"]["anchor_id"] == "anchor-live-001"
    assert payload["etherscan"]["classification"] == "ETHERSCAN_CONTRACT_VERIFICATION_REPORT"

    index_response = client.get("/public/architecture/anchors")
    assert index_response.status_code == 200
    index_payload = index_response.json()
    assert index_payload["classification"] == "BLOCKCHAIN_ANCHOR_INDEX"
    assert index_payload["count"] >= 1


def test_blockchain_anchor_publish_endpoint_supports_contract_mode(monkeypatch) -> None:
    ANCHOR_INDEX_STORE.clear()
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
    assert payload["index_record"]["anchor_id"] == payload["anchor_id"]


def test_governed_adr_anchor_publish_endpoint(monkeypatch) -> None:
    client = build_client()

    class Record:
        def canonical_dict(self) -> dict[str, object]:
            return {
                "adr_id": "ADR-0045",
                "title": "Realtime Anchor Streaming and ADR Hashing",
                "state": "accepted",
                "path": "afritech/governance/adr/ADR-0045-blockchain-architecture-anchor-system.yaml",
                "content_hash": "a" * 64,
                "anchor_id": "adr-adr-0045",
                "publication_id": "adr-adr-0045:aaaaaaaaaaaa",
                "network": "sepolia",
                "chain_id": 11155111,
                "contract_address": "0x0000000000000000000000000000000000000001",
                "transaction_hash": "0xabc123",
                "block_number": 1,
                "explorer_url": "https://sepolia.etherscan.io/tx/abc123",
                "status": "live",
                "anchor_mode": "smart_contract",
            }

    monkeypatch.setattr(
        "afritech.api.architecture_proof_api.anchor_adr_to_chain",
        lambda adr_id, profile_name="sepolia", require_live=False: Record(),
    )

    response = client.post(
        "/v1/governance/adr/ADR-0045/anchor",
        json={"profile": "sepolia", "require_live": False},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "ADR_ANCHOR_PUBLICATION"
    assert payload["record"]["adr_id"] == "ADR-0045"


def test_public_anchor_index_file_backend_persists_entries(tmp_path) -> None:
    backend = JsonFileAnchorIndexBackend(str(tmp_path / "anchor-index.json"))
    store = AnchorIndexStore(backend)
    store.clear()
    store.remember(
        AnchorIndexEntry(
            anchor_id="anchor-persist-001",
            publication_id="publish-persist-001",
            proof_hash="a" * 64,
            network="sepolia",
            chain_id=11155111,
            chain_name="Ethereum Sepolia",
            contract_address="0x0000000000000000000000000000000000000001",
            transaction_hash="0xabc123",
            block_number=1,
            explorer_url="https://sepolia.etherscan.io/tx/abc123",
            anchor_mode="smart_contract",
            status="live",
            source="test",
            sequence=1,
            contract_explorer_url="https://sepolia.etherscan.io/address/1",
            etherscan_verification_stage="READY_FOR_SUBMISSION",
            authority_boundary="anchor_index_is_read_only",
            meta={},
        )
    )

    restored = AnchorIndexStore(backend)

    assert restored.latest() is not None
    assert restored.latest().anchor_id == "anchor-persist-001"
