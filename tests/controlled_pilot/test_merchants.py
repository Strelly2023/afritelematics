from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, read_json, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.novapay, pytest.mark.merchant]


def test_controlled_pilot_merchant_population_and_access() -> None:
    registry = read_json("docs/pilot/approved_pilot_registry.json")
    assert len(registry["approved_merchants"]) == 2
    assert set(registry["approved_merchants"]) == {"merchant-001", "merchant-002"}

    client = TestClient(app)
    user_id, role, _ = PILOT_ACCOUNTS["merchant"]
    token = client.post("/auth/token", json=token_payload(user_id, role)).json()["token"]
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(token), json={"device_id": "device-031"}).status_code == 200
    access = client.post("/v1/pilot/access/check", headers=auth_header(token), json={"device_id": "device-031", "surface": "merchant"})
    assert access.status_code == 200
    assert access.json()["allowed"] is True

