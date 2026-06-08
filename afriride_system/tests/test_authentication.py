from __future__ import annotations

from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app


def bearer(role: str, user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token(user_id, role)}"}


def setup_function() -> None:
    reset_gateway()


def test_auth_token_endpoint_issues_role_token() -> None:
    client = TestClient(app)
    response = client.post("/auth/token", json={"user_id": "rider-1", "role": "RIDER"})

    assert response.status_code == 200
    assert response.json()["token"]


def test_missing_auth_is_rejected_for_protected_route() -> None:
    client = TestClient(app)
    response = client.post("/driver/status", json={"driver_id": "driver-1", "online": True})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "BEARER TOKEN REQUIRED"


def test_role_mismatch_is_rejected() -> None:
    client = TestClient(app)
    response = client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers=bearer("RIDER", "rider-1"),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_ROLE"


def test_operator_can_read_system_surface() -> None:
    client = TestClient(app)
    response = client.get("/system/evidence", headers=bearer("OPERATOR", "operator-1"))

    assert response.status_code == 200


def test_cors_preflight_is_not_blocked_by_auth() -> None:
    client = TestClient(app)
    response = client.options(
        "/system/evidence",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
