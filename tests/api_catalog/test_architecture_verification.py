from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app


client = TestClient(app)


def test_architecture_verification_reports_distinct_states() -> None:
    response = client.get("/v1/platform/architecture/verify")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "VERIFIED"
    assert payload["api_contracts"]["all_signed"] is True
    assert payload["api_contracts"]["all_approved"] is True
    assert payload["sdks"]["generated"] is True
    assert payload["sdks"]["published"] is False


def test_api_metrics_endpoint_exposes_contract_metrics() -> None:
    response = client.get("/v1/platform/api-metrics")
    assert response.status_code == 200
    assert "novatech_api_contract_validations_total" in response.text
