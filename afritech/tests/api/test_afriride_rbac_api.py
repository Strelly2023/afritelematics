from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore


def auth_headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_afriride_rbac_sessions_catalog_assignments_and_extranet_access(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "afriride-rbac.sqlite3")
    try:
        client = TestClient(app)

        customer_session = client.post(
            "/v1/mobile/auth/session",
            json={
                "actor_id": "customer-1",
                "role": "customer",
                "device_id": "device-customer-1",
                "app_version": "2.0.0",
                "platform": "ios",
            },
        )
        assert customer_session.status_code == 200
        customer_payload = customer_session.json()
        assert customer_payload["role"] == "CUSTOMER"
        assert customer_payload["rbac"]["role"] == "CUSTOMER"
        assert "Verify Ride" in customer_payload["rbac"]["visible_panels"]

        client_session = client.post(
            "/v1/mobile/auth/session",
            json={
                "actor_id": "client-1",
                "role": "CLIENT",
                "device_id": "device-client-1",
                "app_version": "2.0.0",
                "platform": "web",
            },
        )
        assert client_session.status_code == 200
        assert client_session.json()["role"] == "CLIENT"

        operator_headers = auth_headers(role="OPERATOR", user_id="operator-1", organization_id="org-rbac")
        admin_headers = auth_headers(role="ADMIN", user_id="admin-1", organization_id="org-rbac")
        client_headers = auth_headers(role="CLIENT", user_id="client-1", organization_id="org-rbac")

        catalog = client.get("/v1/afriride/rbac/catalog", headers=operator_headers)
        assert catalog.status_code == 200
        catalog_payload = catalog.json()
        assert catalog_payload["summary"]["core_role_count"] == 5
        assert any(item["role"] == "CUSTOMER" for item in catalog_payload["core_roles"])
        assert any(item["role"] == "CLIENT" for item in catalog_payload["legacy_roles"])

        assign = client.post(
            "/v1/afriride/rbac/assignments",
            headers=admin_headers,
            json={
                "organization_id": "org-rbac",
                "subject_type": "user",
                "subject_id": "driver-1",
                "role": "driver",
                "granted_by": "admin-1",
                "granted_role": "ADMIN",
                "status": "active",
                "notes": ["pilot", "manual-review"],
            },
        )
        assert assign.status_code == 200
        assignment_payload = assign.json()
        assert assignment_payload["role_key"] == "DRIVER"
        assert assignment_payload["subject_id"] == "driver-1"

        assignments = client.get("/v1/afriride/rbac/assignments", headers=admin_headers)
        assert assignments.status_code == 200
        assignments_payload = assignments.json()
        assert assignments_payload["summary"]["assignment_count"] == 1
        assert assignments_payload["assignments"][0]["role_profile"]["role"] == "DRIVER"

        role_dashboard = client.get("/v1/afriride/rbac/roles/driver/dashboard", headers=operator_headers)
        assert role_dashboard.status_code == 200
        role_dashboard_payload = role_dashboard.json()
        assert role_dashboard_payload["role"]["role"] == "DRIVER"
        assert role_dashboard_payload["assignment_count"] == 1

        access_check = client.get(
            "/v1/afriride/rbac/check",
            headers=operator_headers,
            params={"role": "fleet owner", "permission": "fleet.manage_drivers"},
        )
        assert access_check.status_code == 200
        assert access_check.json()["allowed"] is True

        extranet = client.get("/v1/novatech/extranet/status", headers=client_headers)
        assert extranet.status_code == 200
        extranet_payload = extranet.json()
        assert extranet_payload["audiences"] == ["CLIENT", "PARTNER", "SUPPLIER", "INVESTOR"]
        assert extranet_payload["public_verification"]["portal"] == "/public/verify/portal"
    finally:
        control_plane._STORE = original_store
