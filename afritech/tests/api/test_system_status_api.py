from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.system_status import build_system_status_router


def test_system_status_exposes_public_rollout_summary() -> None:
    app = FastAPI()
    app.include_router(build_system_status_router())
    client = TestClient(app)

    response = client.get("/v1/system/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "active"
    assert payload["service"] == "NovaTech Deterministic MVP Pipeline"
    assert payload["deployment"]["stack"]["platform"] == "NovaTechSol"
    assert payload["deployment"]["stack"]["ready"] in {True, False}
    assert payload["deployment"]["settlement"]["available"] is True
    assert payload["deployment"]["settlement"]["corridor_matrix"]
    assert payload["deployment"]["settlement"]["corridor_matrix"][0]["execution_state"]
