from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app


client = TestClient(app)


def test_api_scorecard_reports_pass_for_catalog() -> None:
    response = client.get("/v1/platform/api-scorecard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PASS"
    assert len(payload["domains"]) >= 9


def test_domain_scorecard_available() -> None:
    response = client.get("/v1/platform/api-scorecard/novapay")
    assert response.status_code == 200
    assert response.json()["score"] >= 90
