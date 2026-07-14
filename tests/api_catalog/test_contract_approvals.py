from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from dataclasses import replace

from afritech.api_catalog.approval import approval_is_publishable, default_contract_approval
from afritech.api_catalog.registry import get_api_catalog


client = TestClient(app)


def test_stable_contract_has_publishable_approval() -> None:
    contract = get_api_catalog().get("novapay")
    approval = default_contract_approval(contract)
    assert approval.status == "approved"
    assert approval_is_publishable(approval) is True


def test_approval_endpoint_exposes_evidence() -> None:
    response = client.get("/v1/platform/api-catalog/novapay/approval")
    assert response.status_code == 200
    payload = response.json()
    assert payload["publishable"] is True
    assert payload["adr_ids"]


def test_stable_publication_without_approval_gate_fails() -> None:
    contract = get_api_catalog().get("novapay")
    approval = replace(default_contract_approval(contract), status="pending")
    assert approval_is_publishable(approval) is False
