from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.dashboard_gateway_api import build_dashboard_gateway_router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_dashboard_gateway_router())
    return TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "operator-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_gateway_http_route_serves_html() -> None:
    client = build_client()

    response = client.get("/afritech/dashboard/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AfriTech Dashboard" in response.text
    assert "/afroprog/dashboard/" in response.text


def test_dashboard_gateway_http_status_route_serves_status_payload() -> None:
    client = build_client()

    response = client.get("/afritech/dashboard/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["dashboard"]["route"] == "/afritech/dashboard/"


def test_dashboard_gateway_json_route_requires_authentication() -> None:
    client = build_client()

    response = client.get("/v1/dashboard/gateway")
    assert response.status_code == 401


def test_dashboard_gateway_overview_exposes_live_wiring_and_role_surface() -> None:
    client = build_client()

    response = client.get(
        "/v1/dashboard/gateway?role=operator&ride_id=ride-001",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dashboard"]["title"] == "AfriTech Dashboard"
    assert body["role_surface"]["active_role"] == "operator"
    assert len(body["live_data_wiring"]) == 4
    assert body["cross_system_context"]["context_id"] == "ride-001"


def test_dashboard_gateway_role_endpoint_filters_visible_dashboards() -> None:
    client = build_client()

    response = client.get("/v1/dashboard/gateway/roles/partner", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    names = [entry["name"] for entry in body["role_surface"]["visible_dashboards"]]
    assert names == ["AfriRide Dashboard"]


def test_dashboard_gateway_context_exposes_deep_links() -> None:
    client = build_client()

    response = client.get(
        "/v1/dashboard/gateway/context/ride-777?role=auditor",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cross_system_context"]["context_id"] == "ride-777"
    assert body["deep_links"][0]["path"] == "/ride/ride-777/replay"
    assert body["read_only"] is True
