from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.pilot.controlled_pilot import audit_log, record_event
from tests.controlled_pilot._helpers import auth_header, read_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_security]


def test_controlled_pilot_monitoring_and_audit_hooks_exist() -> None:
    client = TestClient(app)
    operator_token = client.post("/auth/token", json=token_payload("employee-001", "OPERATOR")).json()["token"]
    assert client.get("/health").status_code == 200
    assert client.get("/v1/architecture/signature", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/corridors", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/treasury/snapshot", headers=auth_header(operator_token)).status_code == 200

    start = len(audit_log())
    record_event(actor="rider-001", role="CUSTOMER", device="device-011", action="monitoring_test", result="ok")
    event = audit_log()[start]
    for key in ["timestamp", "actor", "role", "device", "action", "result", "environment"]:
        assert key in event
    assert event["environment"] == "CONTROLLED_PILOT"

    doc = read_text("docs/pilot/CONTROLLED_PILOT_OPERATIONS.md")
    assert "Monitoring is enabled." in doc
    assert "Support is enabled." in doc

