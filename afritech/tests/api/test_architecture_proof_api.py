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
from afritech.api.afriride_next_gen_mobile_api import build_afriride_next_gen_mobile_router
from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.app import app as production_app
from afritech.ci.runtime_boundary_validator import RuntimeBoundaryValidator


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_architecture_proof_router())
    return TestClient(app)


def build_next_gen_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_afriride_next_gen_mobile_router())
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


def test_novaride_super_app_endpoint_exposes_global_shell_contract() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/super-app")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_super_app"
    assert payload["super_app"]["classification"] == "global_super_app_operating_system_contract"
    assert payload["super_app"]["authority_boundary"] == "super_app_is_interface_only_backend_services_keep_authority"
    assert {module["key"] for module in payload["super_app"]["modules"]} >= {
        "mobility",
        "delivery",
        "wallet",
        "finance",
        "app_store",
        "identity",
        "ai_assistant",
    }
    assert payload["super_app"]["profile"]["novaid"] == "NOVA-84729"
    assert payload["super_app"]["wallet"]["authority"] == "NovaPay"
    assert payload["super_app"]["governance"]["authority"] == "DAO_policy_gated"


def test_novaid_endpoint_exposes_global_identity_contract() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/novaid")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaid_global_identity"
    assert payload["identity"]["classification"] == "global_identity_layer_contract"
    assert payload["identity"]["positioning"] == "Login with NovaID"
    assert payload["identity"]["sample_profile"]["did"] == "did:nova:84729"
    assert payload["identity"]["login_button"]["contract"] == "novaride.identity.login.v1"
    assert "driver_verification" in payload["identity"]["use_cases"]


def test_novaid_gen_sovereign_endpoint_exposes_policy_gated_infrastructure_contract() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/novaid/gen-sovereign")

    assert response.status_code == 200
    payload = response.json()
    contract = payload["gen_sovereign"]
    assert payload["view"] == "novaid_gen_sovereign"
    assert contract["classification"] == "novaid_gen_sovereign_infrastructure_contract"
    assert contract["authority_boundary"] == (
        "gen_sovereign_is_architecture_and_policy_gated_infrastructure_not_live_state_authority"
    )
    assert contract["identity"]["sample_did_document"]["id"] == "did:nova:847392"
    assert "national_id_verification" in contract["government_integration"]["credential_types"]
    assert contract["crypto_finance"]["metrics"]["token_circulation"] == "50M NVT"
    assert contract["ai_governance"]["authority_boundary"] == "NovaAI_recommends_only_DAO_and_policy_execute"
    assert {api["path"] for api in contract["federation"]["apis"]} == {
        "/v1/federation/identity",
        "/v1/federation/payments",
        "/v1/federation/trust",
    }


def test_novaid_digital_nation_endpoint_exposes_platform_citizenship_contract() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/novaid/digital-nation")

    assert response.status_code == 200
    payload = response.json()
    contract = payload["digital_nation"]
    assert payload["view"] == "novaid_digital_nation"
    assert contract["classification"] == "novaid_gen_sovereign_plus_plus_digital_nation_contract"
    assert contract["positioning"] == "Digital Citizenship + NovaID Passport System"
    assert contract["authority_boundary"] == (
        "digital_nation_is_platform_citizenship_not_legal_nationality_or_immigration_authority"
    )
    assert "legal_passport" in contract["what_this_is_not"]
    assert contract["citizenship"]["profile"]["nova_id"] == "did:nova:00087423"
    assert contract["citizenship"]["profile"]["governance_power"] == 2450
    assert {tier["tier"] for tier in contract["citizenship"]["tiers"]} == {
        "Basic",
        "Verified",
        "Trusted",
        "Elite",
    }
    assert contract["passport"]["sample"]["passport_id"] == "NVP-992384"
    assert contract["passport"]["authority_boundary"] == (
        "novapassport_is_platform_access_not_a_legal_travel_document"
    )
    assert "licensed_driver" in contract["passport"]["sample"]["credentials"]
    assert contract["governance"]["formula"] == {"tokens": 0.5, "trust_score": 0.3, "activity": 0.2}
    assert "treasury_allocation" in contract["governance"]["proposal_types"]
    assert contract["dashboard"]["identity"]["novacitizens"] == "12M"
    assert contract["dashboard"]["economy"]["daily_transactions"] == "$25M"
    assert contract["ai_governance"]["sample_analysis"]["recommendation"] == "APPROVE"


def test_novaride_constitution_endpoint_exposes_platform_governance_contract() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/constitution")

    assert response.status_code == 200
    payload = response.json()
    contract = payload["constitution"]
    assert payload["view"] == "novaride_digital_constitution"
    assert contract["classification"] == "novaride_digital_constitution_governance_contract"
    assert contract["positioning"] == "Digital Constitution + Legal Governance Framework"
    assert contract["authority_boundary"] == (
        "digital_constitution_is_platform_governance_not_statutory_law_or_regulator_substitute"
    )
    assert "identity is sovereign" in contract["core_statement"]
    assert {article["title"] for article in contract["articles"]} == {
        "Sovereign Identity",
        "Digital Citizenship",
        "Rights of Users",
    }
    assert contract["authority_structure"]["fundamental_rule"] == (
        "execution_authority_shall_remain_with_NovaPower_and_authorized_subsystems_only"
    )
    assert "approve_treasury_allocations" in contract["governance"]["powers"]
    assert "directly_vote" in contract["governance"]["ai_role"]["shall_not"]
    assert contract["trust_verification_law"]["legal_equivalent"] == "replay_is_digital_audit_record"
    assert "violations_shall_be_rejected_automatically" in contract["contract_law"]["enforcement"]
    assert contract["dispute_resolution"]["example_flow"] == [
        "transaction_dispute",
        "replay_verification",
        "ai_review",
        "dao_vote",
        "decision_enforced",
    ]
    assert contract["amendment_process"][-1] == "enactment_via_contract_update"
    assert contract["guarantees"]["ai_safety"] is True


def test_novaride_regulatory_alignment_endpoint_exposes_jurisdiction_aware_controls() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/regulatory-alignment")

    assert response.status_code == 200
    payload = response.json()
    contract = payload["regulatory_alignment"]
    assert payload["view"] == "novaride_regulatory_alignment"
    assert contract["classification"] == "novaride_regulatory_alignment_contract"
    assert contract["positioning"] == "Regulatory-Aligned Digital Infrastructure Layer"
    assert contract["authority_boundary"] == (
        "regulatory_alignment_is_control_mapping_not_legal_advice_certification_or_regulatory_approval"
    )
    assert "applicable legal frameworks" in contract["core_principle"]
    assert {domain["domain"] for domain in contract["alignment_model"]} == {
        "Identity",
        "Finance",
        "Token",
        "Governance",
        "Trust",
    }
    assert "W3C_DID" in contract["identity_compliance"]["aligns_with"]
    assert contract["identity_compliance"]["rule"] == (
        "identity_verification_required_for_high_risk_financial_or_governance_actions"
    )
    assert "suspicious_activity_shall_be_flagged" in contract["payments_regulation"]["requirements"]
    assert contract["token_regulation"]["classification_model"][2]["type"] == "payment_token"
    assert "GDPR" in contract["privacy_law"]["aligns_with"]
    assert contract["cross_border_framework"]["rule"] == (
        "novaride_shall_implement_jurisdiction_aware_compliance_layers"
    )
    assert {region["region"] for region in contract["cross_border_framework"]["regions"]} == {
        "EU",
        "US",
        "Africa",
    }
    assert contract["liability_model"]["rule"] == "liability_attributed_by_layer_of_control_and_authority"
    assert "ai_shall_not_execute_high_risk_actions_autonomously" in contract["ai_regulation_compliance"]["rules"]
    assert contract["dashboard"]["risk_monitor"]["audit_readiness"] == "HIGH"


def test_novaride_global_expansion_endpoint_exposes_multi_country_rollout_strategy() -> None:
    client = build_next_gen_client()

    response = client.get("/v1/novaride/global-expansion")

    assert response.status_code == 200
    payload = response.json()
    contract = payload["expansion"]
    assert payload["view"] == "novaride_global_expansion"
    assert contract["classification"] == "novaride_global_regulatory_expansion_strategy_contract"
    assert contract["positioning"] == "Global Regulatory Expansion Strategy"
    assert (
        contract["authority_boundary"]
        == "expansion_strategy_is_rollout_planning_not_country_launch_authorization_or_legal_approval"
    )
    assert contract["objective"] == "globally_compliant_identity_mobility_fintech_protocol"
    assert "Global Core Platform" in contract["expansion_model"]
    assert "Regional Compliance Layer" in contract["expansion_model"]
    assert "Australia" in contract["dashboard"]["expansion_status"]
    assert "Kenya" in contract["dashboard"]["expansion_status"]
    assert "EU" in contract["dashboard"]["expansion_status"]
    assert "identify_financial_regulators" in contract["country_entry_playbook"]["regulatory_mapping"]
    assert "local_entity" in contract["country_entry_playbook"]["legal_structure"]
    assert "integrate_with_local_banks" in contract["country_entry_playbook"]["partnership_model"]
    assert contract["novaid_deployment"]["government_integration_path"][0] == "start_with_KYC_providers"
    assert contract["novapay_deployment"]["multi_currency_rollout"][0] == "fiat_only"
    assert contract["token_strategy"]["launch_model"][0]["region"] == "strict_regulation"
    assert contract["cross_border_architecture"]["region_examples"][0]["region"] == "EU"
    assert "explainability" in contract["ai_alignment"]["requirements"]
    assert contract["risk_management"]["top_risks"][0]["mitigation"] == "Partner model"
    assert contract["dashboard"]["compliance_status"]["token"] == "Restricted"
    assert [hub["hub"] for hub in contract["execution_blueprint"]["hub_model"]] == [
        "Melbourne",
        "Burundi",
        "DRC",
        "East Africa",
    ]
    assert contract["execution_blueprint"]["phase_sequence"][0]["market"] == "Melbourne"
    assert contract["execution_blueprint"]["phase_sequence"][1]["market"] == "Burundi"
    assert "airport_transfers" in contract["execution_blueprint"]["melbourne_pilot"]["target"]
    assert "mobile_money_payments" in contract["execution_blueprint"]["burundi_launch"]["services"]
    assert "motorbike_taxis" in contract["execution_blueprint"]["drc_launch"]["priorities"]
    assert "M_Pesa_integration" in contract["execution_blueprint"]["east_africa_expansion"]["kenya"]
    assert contract["execution_blueprint"]["team_structure"]["founder"] == "Australia"
    assert "launch_Melbourne_pilot" in contract["execution_blueprint"]["ninety_day_plan"]


def test_architecture_compliance_endpoint_exposes_governed_report() -> None:
    client = build_client()

    response = client.get(
        "/v1/architecture/compliance",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "NOVARIDE_ARCHITECTURE_COMPLIANCE_REPORT"
    assert payload["status"] == "pass"
    assert payload["score"] == 100
    assert payload["rules_total"] >= 10
    assert "multi_language_ast_validation" in payload["capabilities"]
    assert "semantic_openapi_diff" in payload["capabilities"]
    assert "architecture_anchor_v2_verification" in payload["capabilities"]
    assert any(rule["name"] == "Multi-Language AST Validation" for rule in payload["report"])
    assert any(rule["name"] == "Blockchain Proof Verification" for rule in payload["report"])


def test_architecture_compliance_endpoint_can_run_live_validator() -> None:
    client = build_client()

    response = client.get(
        "/v1/architecture/compliance?live=true",
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "live_validator_scan"
    assert payload["live_scan"] is True
    assert payload["status"] == "pass"
    assert any(rule["name"] == "Semantic OpenAPI Diff" for rule in payload["report"])


def test_architecture_compliance_prometheus_metrics_endpoint() -> None:
    client = build_client()

    response = client.get("/metrics/architecture/compliance")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "novaride_compliance_score" in text
    assert "novaride_compliance_rules_failed" in text
    assert 'novaride_compliance_rule_passed{rule="Architecture Invariants"}' in text
    assert 'novaride_compliance_report_info{mode="' in text


def test_architecture_remediation_endpoint_exposes_autofix_plan() -> None:
    client = build_client()

    response = client.get(
        "/v1/architecture/remediation",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "NOVARIDE_AUTONOMOUS_REMEDIATION_REPORT"
    assert payload["mode"] == "plan"
    assert payload["final_passed"] is True
    assert payload["fixes_total"] == 0
    assert payload["manual_review_required"] == 0


def test_architecture_learning_endpoint_exposes_continuous_learning_surface() -> None:
    client = build_client()

    response = client.get(
        "/v1/architecture/learning",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "NOVARIDE_CONTINUOUS_LEARNING_REPORT"
    assert "risk_profile" in payload
    assert "patterns" in payload
    assert "knowledge_graph" in payload
    assert "optimizer_suggestions" in payload
    assert "remediation" in payload


def test_architecture_learning_prometheus_metrics_endpoint() -> None:
    client = build_client()

    response = client.get("/metrics/architecture/learning")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "novaride_ai_fix_accuracy" in text
    assert "novaride_architecture_violation_rate" in text
    assert "novaride_learning_total_events" in text
    assert "novaride_learning_suggestions_total" in text


def test_architecture_predictive_governance_endpoint_exposes_digital_twin() -> None:
    client = build_client()

    response = client.get(
        "/v1/architecture/predictive-governance",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "NOVARIDE_PREDICTIVE_GOVERNANCE_REPORT"
    assert payload["authority_boundary"] == "predictive_governance_is_advisory_and_simulation_only"
    assert "digital_twin" in payload
    assert "scenarios" in payload
    assert "predictions" in payload
    assert "preventive_actions" in payload
    assert "risk_score" in payload


def test_architecture_predictive_governance_prometheus_metrics_endpoint() -> None:
    client = build_client()

    response = client.get("/metrics/architecture/predictive-governance")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "novaride_predictive_risk_score" in text
    assert "novaride_digital_twin_health_score" in text
    assert "novaride_predicted_risks_total" in text
    assert "novaride_preventive_actions_total" in text


def test_architecture_autonomous_governance_endpoint_exposes_multi_agent_crisis_and_economic_layers() -> None:
    client = build_client()

    response = client.get(
        "/v1/architecture/autonomous-governance",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "NOVARIDE_AUTONOMOUS_MULTI_AGENT_GOVERNANCE_REPORT"
    assert payload["authority_boundary"] == "multi_agent_governance_is_advisory_and_simulation_only"
    assert "multi_agent" in payload
    assert "crisis" in payload
    assert "crisis_summary" in payload
    assert "economic_optimization" in payload
    assert "refactor_suggestions" in payload
    assert "predictive" in payload


def test_architecture_autonomous_governance_prometheus_metrics_endpoint() -> None:
    client = build_client()

    response = client.get("/metrics/architecture/autonomous-governance")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "novaride_multi_agent_findings_total" in text
    assert "novaride_crisis_max_risk_score" in text
    assert "novaride_crisis_critical_scenarios_total" in text
    assert "novaride_economic_efficiency" in text
    assert "novaride_refactor_suggestions_total" in text


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


def test_public_anchor_v2_contract_metadata_is_public() -> None:
    client = build_client()

    report_response = client.get("/public/architecture/anchors/verification")
    abi_response = client.get("/public/architecture/anchors/verification/v2/abi")
    source_response = client.get("/public/architecture/anchors/verification/v2/source")

    assert report_response.status_code == 200
    assert report_response.json()["anchor_v2_abi"].endswith("/verification/v2/abi")

    assert abi_response.status_code == 200
    abi_payload = abi_response.json()
    assert abi_payload["contract_name"] == "ArchitectureAnchorV2"
    assert any(item.get("name") == "anchorBatch" for item in abi_payload["abi"])

    assert source_response.status_code == 200
    source_payload = source_response.json()
    assert source_payload["contract_name"] == "ArchitectureAnchorV2"
    assert "contract ArchitectureAnchorV2" in source_payload["source"]
    assert "function anchorBatch(" in source_payload["source"]


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
