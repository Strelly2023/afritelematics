from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.pilot import public_pilot
from tests.public_pilot._helpers import PUBLIC_PILOT_ACCOUNTS, PUBLIC_PILOT_DOWNLOAD_PAGE_PATH, PUBLIC_PILOT_MONITORING_PATH, auth_header, public_pilot_approval_payload, token_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_monitoring]


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


def test_public_pilot_monitoring_and_support_endpoints_exist(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    token = _token(client, "operator")
    for path in ("/health", "/v1/public-pilot/registry", "/v1/public-pilot/geography", "/v1/public-pilot/release/status"):
        assert client.get(path, headers=auth_header(token)).status_code == 200
    openapi = app.openapi()
    text = str(openapi)
    assert "/v1/public-pilot/registry" in text
    assert "/v1/public-pilot/geography" in text
    monitoring = PUBLIC_PILOT_MONITORING_PATH.read_text(encoding="utf-8")
    assert "Sentry" in monitoring
    assert "OpenTelemetry" in monitoring
