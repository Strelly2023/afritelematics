from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_api, pytest.mark.qa_smoke]


def test_internal_qa_server_health_and_authorized_snapshots() -> None:
    client = TestClient(app)
    token = client.post("/v1/auth/token", json={"user_id": "qa-operator", "role": "ADMIN"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    architecture = client.get("/v1/architecture/signature", headers=headers)
    assert architecture.status_code == 200
    assert architecture.json()["signature"] == "private-development-signature"
    assert architecture.json()["private_development"] is True

    corridors = client.get("/v1/corridors", headers=headers)
    assert corridors.status_code == 200
    assert corridors.json()["contract"] == "afriride.global.v1"

    treasury = client.get("/v1/treasury/snapshot", headers=headers)
    assert treasury.status_code == 200
    assert treasury.json()["simulated"] is True
    assert treasury.json()["mode"] == "SIMULATED"

    assert client.get("/v1/architecture/signature").status_code == 401
    assert client.get("/v1/corridors").status_code == 401
    assert client.get("/v1/treasury/snapshot").status_code == 401

    payload = treasury.json()
    assert "secret" not in str(payload).lower()
    assert payload["token_subject"] == "qa-operator"
    assert payload["token_role"] == "ADMIN"
