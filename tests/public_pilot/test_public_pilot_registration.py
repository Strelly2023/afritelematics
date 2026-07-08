from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import bind_device
from tests.public_pilot._helpers import PUBLIC_PILOT_ACCOUNTS, auth_header, public_pilot_approval_payload, token_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_access_control]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _, _ = PUBLIC_PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path, **overrides) -> None:
    payload = public_pilot_approval_payload(**overrides)
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_CONFIG_PATH", public_pilot.PUBLIC_PILOT_CONFIG_PATH)
    public_pilot.load_public_pilot_config.cache_clear()
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_access_control_allows_approved_user_and_blocks_region(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    rider_token = _token(client, "rider")
    rider_id, _, device_id, _ = PUBLIC_PILOT_ACCOUNTS["rider"]

    assert bind_device(rider_id, device_id)["status"] == "bound"

    allowed = client.post(
        "/v1/public-pilot/access/check",
        headers=auth_header(rider_token),
        json={"device_id": device_id, "region": "Melbourne CBD", "surface": "rider"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["allowed"] is True
    assert allowed.json()["reason"] == "approved"

    blocked = client.post(
        "/v1/public-pilot/access/check",
        headers=auth_header(rider_token),
        json={"device_id": device_id, "region": "Sydney", "surface": "rider"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["allowed"] is False
    assert blocked.json()["reason"] == "region_not_approved"


def test_public_pilot_access_control_blocks_unapproved_user(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    stranger_token = _token(client, "rider")

    denied = client.post(
        "/v1/public-pilot/access/check",
        headers=auth_header(stranger_token),
        json={"device_id": "not-approved-device", "region": "Melbourne CBD", "surface": "rider"},
    )
    assert denied.status_code == 200
    assert denied.json()["allowed"] is False
