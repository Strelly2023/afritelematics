from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.api.auth import AuthClaims
from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import bind_device, check_access
from tests.public_pilot._helpers import PUBLIC_PILOT_ACCOUNTS, auth_header, load_source_text, public_pilot_approval_payload, token_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.novaid, pytest.mark.identity]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _, _ = PUBLIC_PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(public_pilot_approval_payload(), indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_novaid_identity_flows(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    personal_token = _token(client, "identity")
    business_token = _token(client, "business")
    employee_token = _token(client, "employee")
    partner_token = _token(client, "partner")
    inspector_token = _token(client, "inspector")

    assert bind_device("public-verifier-1", "public-device-verifier-1")["status"] == "bound"

    personal_access = check_access(AuthClaims(sub="public-verifier-1", role="VERIFIER", exp=9999999999), "public-device-verifier-1", "identity", "Melbourne")
    assert personal_access["allowed"] is True

    response = client.post(
        "/v1/public-pilot/access/check",
        headers=auth_header(personal_token),
        json={"device_id": "public-device-verifier-1", "region": "Melbourne", "surface": "identity"},
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True

    for key, surface in (
        ("business", "business"),
        ("employee", "identity"),
        ("partner", "identity"),
        ("inspector", "identity"),
    ):
        subject, _, device_id, _ = PUBLIC_PILOT_ACCOUNTS[key]
        assert bind_device(subject, device_id)["status"] == "bound"
        user_token = _token(client, key)
        data = {"device_id": device_id, "region": "Melbourne", "surface": surface}
        assert client.post("/v1/public-pilot/access/check", headers=auth_header(user_token), json=data).status_code == 200

    assert client.get("/v1/public-pilot/release/status", headers=auth_header(personal_token)).status_code == 200

    for app_key in ("novaid_personal", "novaid_business", "novaid_employee", "novaid_partner", "novaid_inspector"):
        source = load_source_text(app_key)
        assert "Profile" in source
        assert "Logout" in source
