from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore
from afritech.guards.phase0_guard import validate_phase0_status


def _issue_token(client: TestClient, role: str = "OPERATOR") -> str:
    response = client.post(
        "/v1/auth/token",
        json={
            "user_id": "phase0-operator",
            "role": role,
            "organization_id": "org-phase0-001",
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_phase0_status_and_controls_are_exposed(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase0.sqlite3")

    try:
        client = TestClient(app)
        token = _issue_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        status = client.get("/v1/novatech/phase0/status", headers=headers)
        assert status.status_code == 200
        payload = status.json()
        assert payload["platform"] == "NovaRide Phase 0"
        assert payload["ready"] is False

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=headers,
            json={
                "organization_id": "org-phase0-001",
                "legal_name": "Phase 0 Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200
        assert onboard.json()["status"] == "onboarded"

        account = client.post(
            "/v1/novatech/phase0/accounts",
            headers=headers,
            json={
                "organization_id": "org-phase0-001",
                "user_id": "user-001",
                "role": "ADMIN",
                "is_primary": True,
            },
        )
        assert account.status_code == 200
        assert account.json()["account"]["role"] == "ADMIN"

        subscription = client.post(
            "/v1/novatech/phase0/subscriptions",
            headers=headers,
            json={
                "organization_id": "org-phase0-001",
                "plan": "enterprise",
                "status": "active",
                "billing_cycle": "monthly",
                "seats": 25,
            },
        )
        assert subscription.status_code == 200
        assert subscription.json()["subscription"]["plan"] == "enterprise"

        feature_flag = client.post(
            "/v1/novatech/phase0/feature-flags",
            headers=headers,
            json={
                "organization_id": "org-phase0-001",
                "feature_key": "fleet_management",
                "enabled": True,
                "reason": "pilot_enabled",
                "updated_by": "phase0-operator",
            },
        )
        assert feature_flag.status_code == 200
        assert feature_flag.json()["flag"]["enabled"] is True

        integration = client.post(
            "/v1/novatech/phase0/integrations",
            headers=headers,
            json={
                "organization_id": "org-phase0-001",
                "name": "mfs_africa",
                "type": "payments",
                "config": {"mode": "sandbox"},
            },
        )
        assert integration.status_code == 200
        assert integration.json()["integration"]["name"] == "mfs_africa"

        notification = client.post(
            "/v1/novatech/phase0/notifications",
            headers=headers,
            json={
                "organization_id": "org-phase0-001",
                "recipient_id": "user-001",
                "channel": "email",
                "message": "Phase 0 foundation is ready.",
            },
        )
        assert notification.status_code == 200
        assert notification.json()["notification"]["status"] == "queued"

        delivered = client.post(
            f"/v1/novatech/phase0/notifications/{notification.json()['notification']['notification_id']}/deliver",
            headers=headers,
        )
        assert delivered.status_code == 200
        assert delivered.json()["notification"]["status"] == "sent"

        blocked = client.post(
            "/v1/novatech/phase0/accounts",
            headers=headers,
            json={
                "organization_id": "org-phase0-other",
                "user_id": "user-002",
                "role": "ADMIN",
            },
        )
        assert blocked.status_code == 403
        assert "organization_isolation_violation" in blocked.text

        refreshed = client.get(
            "/v1/novatech/phase0/status",
            headers=headers,
        )
        assert refreshed.status_code == 200
        refreshed_payload = refreshed.json()
        assert refreshed_payload["organization_profile"]["organization_id"] == "org-phase0-001"
        assert refreshed_payload["readiness"]["backend_only_provider_access"] is True
        assert refreshed_payload["readiness"]["multi_tenant_registry"] is True
        assert refreshed_payload["readiness"]["subscription_entitlements"] is True
        assert refreshed_payload["readiness"]["feature_flags"] is True
        assert refreshed_payload["readiness"]["audit_logging"] is True
        assert refreshed_payload["readiness"]["notification_outbox"] is True
        assert refreshed_payload["readiness"]["integration_registry"] is True
        assert refreshed_payload["ready"] is True
        assert validate_phase0_status(refreshed_payload)
        assert refreshed_payload["organization_profile"]["default_plan"] in {"free", "enterprise"}
    finally:
        control_plane._STORE = original_store
