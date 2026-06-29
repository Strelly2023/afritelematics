from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore
from afritech.api.app import app
from afritech.tests.api.test_novaride_phase12_api import _seed_phase12_store


def _issue_token(client: TestClient, *, role: str, organization_id: str, user_id: str) -> str:
    response = client.post(
        "/v1/auth/token",
        json={
            "user_id": user_id,
            "role": role,
            "organization_id": organization_id,
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


def _seed_phase13_store(store: PlatformStore, *, org_id: str) -> None:
    _seed_phase12_store(store, org_id=org_id)

    request = store.request_deployment(
        organization_id=org_id,
        service="novaride-api",
        environment="production",
        image="ghcr.io/novaride/api:2026.06",
        rationale="Controlled global deployment plan rollout",
        requested_by="operator-1",
        requested_role="OPERATOR",
    )
    store.approve_deployment_request(
        request_id=request["request_id"],
        organization_id=org_id,
        approved_by="admin-1",
        decision="approved",
        notes="Phase 13 deployment plan reviewed and approved",
    )
    store.create_deployment_from_request(
        request_id=request["request_id"],
        organization_id=org_id,
        deployed_by="operator-1",
    )

    control_plane.record_dashboard_decision_snapshot(
        payload={
            "source": "phase13-test",
            "global_execution": "controlled",
            "city": "Melbourne",
        },
        source="afriride_phase13_global_execution",
        decision_type="global_execution_decision",
        organization_id=org_id,
    )


def test_phase13_global_execution_is_tenant_scoped_and_ready(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase13.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase13-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        admin_token = _issue_token(client, role="ADMIN", organization_id=org_id, user_id="admin-1")

        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 13 Global Execution Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        subscription = client.post(
            "/v1/novatech/phase0/subscriptions",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "plan": "enterprise",
                "status": "active",
                "billing_cycle": "monthly",
                "seats": 16,
            },
        )
        assert subscription.status_code == 200

        store = control_plane._STORE
        _seed_phase13_store(store, org_id=org_id)

        response = client.get(
            "/v1/novaride/phase13/status",
            headers=operator_headers,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["view"] == "novaride_phase13_status"
        assert payload["ready"] is True
        assert payload["readiness"]["global_deployment_plan_ready"] is True
        assert payload["readiness"]["controlled_ai_engine_ready"] is True
        assert payload["readiness"]["aws_infra_ready"] is True
        assert payload["readiness"]["real_execution_ready"] is True
        assert payload["readiness"]["ai_optimization_ready"] is True
        assert payload["readiness"]["nova_connect_ready"] is True
        assert payload["readiness"]["novapay_ready"] is True
        assert payload["readiness"]["subscription_active"] is True

        workspace = payload["global_execution_workspace"]
        assert workspace["global_deployment_plan"]["deployment_plan_ready"] is True
        assert workspace["controlled_ai_decision_engine"]["safe_to_execute"] is True
        assert workspace["aws_production_infra"]["aws_infra_ready"] is True
        assert workspace["real_execution_layer"]["execution_mode"] == "controlled_actions"
        assert workspace["ai_optimization"]["optimization_ready"] is True
        assert workspace["novaconnect_expansion"]["surface_ready"] is True
        assert workspace["novaconnect_expansion"]["lifecycle_ready"] is True
        assert workspace["novapay_expansion"]["ready"] is True
        assert workspace["global_execution_score"] >= 70

        activation = client.post(
            "/v1/novaride/phase13/controlled-execution",
            headers=admin_headers,
            json={
                "organization_id": org_id,
                "operator_acknowledged": True,
                "requested_tier": "controlled",
                "action_type": "controlled_global_execution_activation",
                "notes": "Activated after plan and readiness review",
            },
        )
        assert activation.status_code == 200
        activation_payload = activation.json()
        assert activation_payload["activation"]["activation_status"] == "activated"
        assert activation_payload["activation"]["activation_ready"] is True
        assert activation_payload["controlled_execution"] is True

        contract = client.get(
            "/v1/novaride/phase13/global-execution-contract",
            headers=operator_headers,
        )
        assert contract.status_code == 200
        contract_payload = contract.json()
        assert contract_payload["status"] == "controlled_global_execution_ready"
        module_names = {module["name"] for module in contract_payload["modules"]}
        assert "Global Deployment Plan" in module_names
        assert "Controlled AI Decision Engine" in module_names
        assert "AWS Production Infra" in module_names
        assert "Real Execution Layer" in module_names
        assert "AI Optimization" in module_names
        assert "NovaConnect Expansion" in module_names
        assert "NovaPay Expansion" in module_names
    finally:
        control_plane._STORE = original_store
