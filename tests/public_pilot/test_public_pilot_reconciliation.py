from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.pilot import public_pilot
from tests.public_pilot._helpers import PUBLIC_PILOT_ACCOUNTS, auth_header, public_pilot_approval_payload, token_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_payments]


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
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_reconciliation_reports_balance(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    token = _token(client, "operator")
    response = client.post(
        "/v1/public-pilot/reconciliation",
        headers=auth_header(token),
        json={"recorded_aud": 100, "ledger_aud": 100, "transactions": 4},
    )
    assert response.status_code == 200
    assert response.json()["balanced"] is True
    assert response.json()["status"] == "reconciled"


def test_public_pilot_reconciliation_flags_drift() -> None:
    report = public_pilot.reconciliation_report(recorded_aud=100, ledger_aud=90, transactions=4)
    assert report["balanced"] is False
    assert report["status"] == "reconciliation_needed"
