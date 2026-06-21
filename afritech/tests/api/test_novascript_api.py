from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novascript_api import build_novascript_public_router, build_novascript_router
from afritech.sdk.novascript import (
    evaluate_policy,
    submit_trust_exchange,
    validate_artifact,
    validate_certificate_chain,
    verify_audit_package,
    verify_receipt,
)
from afritech.novascript.v2.tools import ToolRegistry


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novascript_router())
    app.include_router(build_novascript_public_router())
    return TestClient(app)


def auth_headers(
    role: str = "DEVELOPER",
    user_id: str = "dev-1",
    organization_id: str = "org-nova",
) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_novascript_catalog_and_status_explain_product_boundary() -> None:
    client = build_client()

    status = client.get("/v1/novascript/status", headers=auth_headers(role="OBSERVER"))
    assert status.status_code == 200
    assert status.json()["product"] == "NovaScript"
    assert status.json()["governed_by"] == "NovaProgramming"
    assert "model_layer" in status.json()

    model_status = client.get("/v1/novascript/model/status", headers=auth_headers(role="OPERATOR"))
    assert model_status.status_code == 200
    assert model_status.json()["model_layer"]["available"] is True

    dashboard = client.get("/v1/novascript/dashboard", headers=auth_headers(role="OPERATOR"))
    assert dashboard.status_code == 200
    dashboard_body = dashboard.json()
    assert dashboard_body["view"] == "novascript_dashboard"
    assert dashboard_body["status"]["product"] == "NovaScript"
    assert dashboard_body["risk_dashboard"]["mode"] == "organization_risk_dashboard"
    assert dashboard_body["platform_integrations"]["mode"] == "platform_others_plug_into"
    assert dashboard_body["read_only"] is True

    catalog = client.get("/v1/novascript/catalog", headers=auth_headers(role="OPERATOR"))
    assert catalog.status_code == 200
    body = catalog.json()
    assert body["capabilities"][0] == "code_generation"
    assert body["relationship"]["builds"] == "NovaProgramming"
    assert "prompt_registry" in body["model_layer"]

    prompts = client.get("/v1/novascript/prompts", headers=auth_headers(role="DEVELOPER"))
    assert prompts.status_code == 200
    assert any(template["name"] == "generate" for template in prompts.json())


def test_novascript_generation_and_explanation_are_development_time_only() -> None:
    client = build_client()

    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Build a FastAPI endpoint with tests",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "code",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-2"),
    )
    assert generated.status_code == 200
    generated_body = generated.json()
    assert generated_body["view"] == "novascript_generation"
    assert generated_body["generated_files"]
    assert generated_body["execution_preview"]["sandboxed"] is True
    assert generated_body["model_layer"]["model_name"]
    assert generated_body["model_routing"]["selected_model"].startswith("novascript-v3")
    assert generated_body["planning_engine"]["mode"] == "true_agent_behavior"
    assert generated_body["memory_evolution"]["mode"] == "persistent_evolving_memory"
    assert generated_body["policy_trust"]["engine"] == "policy_driven_trust"
    assert generated_body["multi_provider_orchestration"]["strategy"] in {
        "local_specialized",
        "openai_local_hybrid",
        "explicit_provider_override",
    }
    assert generated_body["federation"]["verified"] is True
    assert generated_body["trust_forecast"]["direction"] in {"stable", "improving", "declining"}
    assert generated_body["engineering_risk"]["risk_level"] in {"low", "medium", "high"}
    assert generated_body["technical_debt_prediction"]["direction"] in {"stable", "rising"}
    assert generated_body["enterprise_knowledge_graph"]["graph_id"].startswith("kg-")
    assert generated_body["autonomous_engineering_workflows"]
    assert generated_body["policy_decision"]["policy_version"] >= 1
    assert generated_body["certificate_chain"]["chain_id"].startswith("chain-")
    assert generated_body["trust_exchange"]["mode"] == "cross_organization_trust_exchange"
    assert generated_body["continuous_assurance"]["mode"] == "continuous_assurance"
    assert generated_body["architecture_evolution_ledger"]["mode"] == "architecture_evolution_ledger"
    assert generated_body["autonomous_remediation"]["self_healing"] is True
    assert generated_body["deployment_ai_agents"]["mode"] == "deployment_ai_agents"
    assert generated_body["canonical_persistence"]["backend"] == "postgresql_canonical"
    assert generated_body["persistence_status"]["ready_for_postgresql"] is True
    assert generated_body["assurance_monitoring"]["mode"] == "continuous_assurance_monitoring_service"
    assert generated_body["organization_risk_dashboard"]["mode"] == "organization_risk_dashboard"
    assert generated_body["evidence_retention"]["mode"] == "evidence_retention_governance"
    assert generated_body["formal_assurance_report"]["mode"] == "formal_assurance_reporting"
    assert generated_body["regulatory_compliance"]["mode"] == "ai_regulatory_compliance_layer"
    assert generated_body["trust_token"]["mode"] == "tokenized_trust_economy"
    assert generated_body["global_trust_network"]["mode"] == "global_trust_network"
    assert generated_body["self_upgrade_plan"]["mode"] == "autonomous_self_upgrading_system"
    assert generated_body["opentelemetry"]["mode"] == "opentelemetry_bridge"
    assert generated_body["standard_profile"]["mode"] == "novascript_trust_standard"
    assert generated_body["standard_profile"]["standards_family"][0]["standard_id"] == "NOVASCRIPT-TRUST-STD-001"
    assert generated_body["platform_integrations"]["mode"] == "platform_others_plug_into"
    assert generated_body["field_adoption"]["mode"] == "field_adoption_status"
    assert generated_body["production_evidence"]["mode"] == "real_production_evidence"
    assert generated_body["audit_marketplace_package"]["mode"] == "external_audit_marketplace_package"
    assert generated_body["decision_explainability"]["mode"] == "decision_explainability"
    assert generated_body["trust_graph"]["mode"] == "federated_trust_graph"
    assert generated_body["assurance_drift"]["mode"] == "assurance_drift_detection"
    assert generated_body["portable_verification_package"]["mode"] == "portable_verification_package"
    assert generated_body["adoption_certification"]["mode"] == "adoption_certification_program"
    assert generated_body["architecture_observatory"]["mode"] == "architecture_evolution_observatory"
    assert generated_body["governance_receipt"]["trust_score"] >= 0
    assert not _contains_timestamp_field(generated_body)

    verification = client.post(
        "/v1/novascript/receipts/verify",
        json=generated_body["governance_receipt"],
        headers=auth_headers(role="VERIFIER", user_id="verifier-verify"),
    )
    assert verification.status_code == 200
    assert verification.json()["verified"] is True

    audit = client.post(
        "/v1/novascript/audit/verify",
        json={
            "receipt": generated_body["governance_receipt"],
            "certificate_chain": generated_body["certificate_chain"],
        },
        headers=auth_headers(role="VERIFIER", user_id="auditor-1"),
    )
    assert audit.status_code == 200
    assert audit.json()["mode"] == "external_audit_verification"
    assert audit.json()["verified"] is True

    artifact_validation = client.post(
        "/v1/novascript/validate/artifact",
        json={"artifact_type": "governance_receipt", "artifact": generated_body["governance_receipt"]},
        headers=auth_headers(role="VERIFIER", user_id="validator-1"),
    )
    assert artifact_validation.status_code == 200
    assert artifact_validation.json()["mode"] == "novascript_artifact_validation"
    assert artifact_validation.json()["verified"] is True

    explanation = client.post(
        "/v1/novascript/explain",
        json={"code": "from fastapi import FastAPI\napp = FastAPI()", "context": "demo"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert explanation.status_code == 200
    assert explanation.json()["summary"]["purpose"] == "API surface or route handler"


def test_novascript_debug_architecture_docs_and_repo_intelligence() -> None:
    client = build_client()

    debug = client.post(
        "/v1/novascript/debug",
        json={"error": "ImportError: module not found", "context": "bootstrap"},
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert debug.status_code == 200
    assert "missing dependency" in debug.json()["findings"][0]

    architecture = client.post(
        "/v1/novascript/architecture",
        json={"description": "Design a secure API with auth and events", "stack": "FastAPI + PostgreSQL"},
        headers=auth_headers(role="DEVELOPER", user_id="dev-3"),
    )
    assert architecture.status_code == 200
    assert "identity" in architecture.json()["recommended_components"]

    docs = client.post(
        "/v1/novascript/docs",
        json={"topic": "NovaScript product brief", "audience": "developer", "format": "README"},
        headers=auth_headers(role="DEVELOPER", user_id="dev-3"),
    )
    assert docs.status_code == 200
    assert docs.json()["outline"][0] == "Overview of NovaScript product brief"

    repo = client.get(
        "/v1/novascript/repo/project-employee-rbac/intelligence?focus=repo intelligence",
        headers=auth_headers(role="VERIFIER", user_id="verifier-2"),
    )
    assert repo.status_code == 200
    assert repo.json()["product"] == "NovaScript"
    assert repo.json()["relationship"]["builds"] == "NovaProgramming"

    memory = client.get(
        "/v1/novascript/memory/project-employee-rbac",
        headers=auth_headers(role="OPERATOR"),
    )
    assert memory.status_code == 200
    assert memory.json()["project_id"] == "project-employee-rbac"
    assert memory.json()["long_term_organizational_memory"]["institutional_memory"]["mode"] == "institutional_memory"

    receipts = client.get(
        "/v1/novascript/receipts/project-employee-rbac",
        headers=auth_headers(role="OPERATOR"),
    )
    assert receipts.status_code == 200
    assert isinstance(receipts.json(), list)

    trust = client.get(
        "/v1/novascript/trust/project-employee-rbac/analytics",
        headers=auth_headers(role="VERIFIER", user_id="verifier-2"),
    )
    assert trust.status_code == 200
    assert trust.json()["trend"]["direction"] in {"stable", "improving", "declining"}


def test_novascript_federation_and_deployment_feedback_loop() -> None:
    client = build_client()

    federation = client.get(
        "/v1/novascript/federation/status",
        headers=auth_headers(role="OPERATOR"),
    )
    assert federation.status_code == 200
    assert federation.json()["mode"] == "multi_node_novascript"
    assert federation.json()["node_count"] >= 3

    feedback = client.post(
        "/v1/novascript/deployment/project-employee-rbac/feedback",
        json={
            "environment": "staging",
            "status": "validated",
            "validation_score": 91,
            "evidence": {"smoke_tests": "passed"},
        },
        headers=auth_headers(role="OPERATOR"),
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback_id"].startswith("deployfb-")

    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Build deployment automation with governance receipt checks",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "code",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-feedback"),
    )
    assert generated.status_code == 200
    assert generated.json()["deployment_feedback"]["feedback_count"] >= 1
    assert generated.json()["continuous_repository_intelligence"]["mode"] == "continuous_repository_intelligence"


def test_novascript_policy_dsl_and_cross_org_trust_exchange() -> None:
    client = build_client()

    policy = client.post(
        "/v1/novascript/policies",
        json={
            "source": """
            policy production_release_trust
            require trust_score >= 75
            require risk_score <= 55
            require federation_verified == true
            require receipt_verified == true
            """
        },
        headers=auth_headers(role="VERIFIER"),
    )
    assert policy.status_code == 200
    assert policy.json()["name"] == "production_release_trust"
    assert policy.json()["version"] == 1
    assert policy.json()["policy_hash"]

    transition = client.post(
        f"/v1/novascript/policies/{policy.json()['policy_id']}/transition",
        json={"status": "deprecated"},
        headers=auth_headers(role="VERIFIER"),
    )
    assert transition.status_code == 200
    assert transition.json()["mode"] == "policy_registry_lifecycle_management"
    assert transition.json()["status"] == "deprecated"

    exchange = client.post(
        "/v1/novascript/federation/trust-exchange",
        json={
            "issuer_org": "org-nova",
            "subject_org": "org-partner",
            "receipt_hash": "abc123",
            "trust_score": 88,
        },
        headers=auth_headers(role="OPERATOR"),
    )
    assert exchange.status_code == 200
    assert exchange.json()["mode"] == "cross_organization_trust_exchange"
    assert exchange.json()["verified"] is True


def test_novascript_v6_global_trust_and_risk_dashboard() -> None:
    client = build_client()

    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Assess regulated production deployment readiness",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "analysis",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-v6"),
    )
    assert generated.status_code == 200

    global_trust = client.get(
        "/v1/novascript/trust/global",
        headers=auth_headers(role="VERIFIER"),
    )
    assert global_trust.status_code == 200
    assert global_trust.json()["mode"] == "global_trust_network"
    assert global_trust.json()["member_count"] >= 2

    dashboard = client.get(
        "/v1/novascript/risk/dashboard",
        headers=auth_headers(role="OPERATOR"),
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["mode"] == "organization_risk_dashboard"
    assert dashboard.json()["sample_count"] >= 1


def test_novascript_standard_platform_adoption_and_production_evidence() -> None:
    client = build_client()
    field_headers = auth_headers(role="OPERATOR", user_id="operator-field", organization_id="org-field")

    standard = client.get(
        "/v1/novascript/standard/profile",
        headers=auth_headers(role="VERIFIER", user_id="verifier-standard"),
    )
    assert standard.status_code == 200
    assert standard.json()["mode"] == "novascript_trust_standard"
    assert "external_audit_verification" in standard.json()["controls"]

    adoption = client.post(
        "/v1/novascript/organizations/onboard",
        json={
            "organization_id": "org-field",
            "legal_name": "Field Trust Systems Pty Ltd",
            "sector": "regulated_engineering",
            "trust_domain": "field-adoption",
        },
        headers=auth_headers(role="OPERATOR", user_id="operator-adopt"),
    )
    assert adoption.status_code == 200
    assert adoption.json()["mode"] == "field_adoption_registry"
    assert adoption.json()["organization_id"] == "org-field"

    integration = client.post(
        "/v1/novascript/integrations",
        json={
            "integration_name": "audit-partner-connector",
            "integration_type": "external_audit_api",
            "scopes": ["receipt_verify", "assurance_report", "trust_exchange"],
        },
        headers=field_headers,
    )
    assert integration.status_code == 200
    assert integration.json()["mode"] == "platform_plugin_registry"
    assert integration.json()["status"] == "active"

    integrations = client.get("/v1/novascript/integrations", headers=field_headers)
    assert integrations.status_code == 200
    assert integrations.json()["mode"] == "platform_others_plug_into"
    assert len(integrations.json()["integrations"]) >= 1

    evidence = client.post(
        "/v1/novascript/production/project-employee-rbac/evidence",
        json={
            "environment": "production",
            "evidence_type": "real_audit_validation",
            "validation_status": "verified",
            "evidence_hash": "field-evidence-hash-001",
        },
        headers=field_headers,
    )
    assert evidence.status_code == 200
    assert evidence.json()["mode"] == "production_evidence_registry"
    assert evidence.json()["verified"] is True

    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Prepare real audit exchange evidence for production deployment",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "analysis",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-field", organization_id="org-field"),
    )
    assert generated.status_code == 200
    body = generated.json()
    assert body["platform_integrations"]["integrations"][0]["integration_name"] == "audit-partner-connector"
    assert body["production_evidence"]["evidence_count"] >= 1
    assert body["production_evidence"]["verified_count"] >= 1
    assert body["audit_marketplace_package"]["sellable_verification"] is True
    assert body["field_adoption"]["organization_count"] >= 1
    assert not _contains_timestamp_field(body)


def test_novascript_v7_explainability_public_trust_portal_and_observatory() -> None:
    client = build_client()

    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Create explainable assurance package for public trust portal",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "analysis",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-v7", organization_id="org-v7"),
    )
    assert generated.status_code == 200
    body = generated.json()
    receipt = body["governance_receipt"]
    certificate_id = body["certificate_chain"]["receipt_certificate"]["certificate_id"]
    report_id = body["formal_assurance_report"]["report_id"]

    graph = client.get("/v1/novascript/trust/graph", headers=auth_headers(role="VERIFIER"))
    assert graph.status_code == 200
    assert graph.json()["mode"] == "federated_trust_graph"
    assert graph.json()["edge_count"] >= 1

    public_receipt = client.get(f"/public/trust/{receipt['receipt_id']}")
    assert public_receipt.status_code == 200
    assert public_receipt.json()["mode"] == "public_trust_receipt"
    assert public_receipt.json()["verification"]["verified"] is True

    public_certificate = client.get(f"/public/certificates/{certificate_id}")
    assert public_certificate.status_code == 200
    assert public_certificate.json()["mode"] == "public_certificate_verification"

    public_assurance = client.get(f"/public/assurance/{report_id}")
    assert public_assurance.status_code == 200
    assert public_assurance.json()["mode"] == "public_assurance_report"

    portable = client.get(f"/public/trust/{receipt['receipt_id']}/package")
    assert portable.status_code == 200
    assert portable.json()["mode"] == "portable_verification_package"
    assert portable.json()["verification_manifest"]["offline_verification"] is True
    assert portable.json()["verification_manifest"]["requires_novascript_runtime"] is False


def test_novascript_sdk_reference_validators_match_nts_contract() -> None:
    client = build_client()
    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Build NTS reference SDK validation fixture",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "analysis",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-sdk", organization_id="org-sdk"),
    )
    assert generated.status_code == 200
    body = generated.json()
    receipt = body["governance_receipt"]
    chain = body["certificate_chain"]

    assert verify_receipt(receipt)["verified"] is True
    assert validate_certificate_chain(receipt=receipt, certificate_chain=chain)["verified"] is True
    assert verify_audit_package({"receipt": receipt, "certificate_chain": chain})["verified"] is True
    assert validate_artifact({"artifact_type": "governance_receipt", "artifact": receipt})["verified"] is True
    assert validate_artifact(
        {
            "artifact_type": "novascript_execution",
            "artifact": {
                "artifact_type": "novascript_execution",
                "policy_decision_id": body["policy_decision"]["decision_id"],
                "certificate_chain_id": chain["chain_id"],
                "assurance_status": body["continuous_assurance"]["assurance_status"],
            },
        }
    )["verified"] is True
    policy = evaluate_policy(
        source="""
        policy production_release_trust
        require trust_score >= 75
        require federation_verified == true
        """,
        context={"trust_score": 91, "federation_verified": True},
    )
    assert policy["allowed"] is True
    exchange = submit_trust_exchange(
        issuer_org="org-sdk",
        subject_org="org-auditor",
        receipt_hash=receipt["output_hash"],
        trust_score=91,
    )
    assert exchange["mode"] == "cross_organization_trust_exchange"
    assert exchange["verified"] is True


def test_novascript_tool_errors_are_structured() -> None:
    result = ToolRegistry().execute("missing_tool", project_id="project-employee-rbac")

    assert result.status == "error"
    assert result.output["status"] == "tool_error"
    assert result.output["error"]["type"] == "unknown_tool"
    assert "available_tools" in result.output["error"]


def _contains_timestamp_field(value) -> bool:
    if isinstance(value, dict):
        return any(
            key in {"created_at", "updated_at", "generated_at", "timestamp"}
            or _contains_timestamp_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_timestamp_field(item) for item in value)
    return False
