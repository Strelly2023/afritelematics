from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novapay_ecosystem_api import build_novapay_ecosystem_router
from afritech.novapay import NovaPayEcosystem, NovaPayRepository


def _client(service: NovaPayEcosystem) -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novapay_ecosystem_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_agent_app_contract_surfaces_are_exposed(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    headers = _headers("OPERATOR", "ops-1", "org-agent")

    profile = client.get("/v1/novapay/agents/profile", headers=headers)
    float_summary = client.get("/v1/novapay/agents/float", headers=headers)
    history = client.get("/v1/novapay/agents/history", headers=headers)
    offline_queue = client.get("/v1/novapay/agents/offline-queue", headers=headers)
    compliance = client.get("/v1/novapay/agents/compliance", headers=headers)
    receipts = client.get("/v1/novapay/agents/receipts", headers=headers)
    supervisor = client.get("/v1/novapay/agents/supervisor-review", headers=headers)

    assert profile.status_code == 200
    assert profile.json()["view"] == "novapay_agent_profile"
    assert float_summary.status_code == 200
    assert float_summary.json()["view"] == "novapay_agent_float"
    assert history.status_code == 200
    assert offline_queue.status_code == 200
    assert compliance.status_code == 200
    assert receipts.status_code == 200
    assert supervisor.status_code == 200


def test_agent_app_preview_routes_remain_governed_and_non_authoritative(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    headers = _headers("OPERATOR", "ops-1", "org-agent")

    send_money = client.post(
        "/v1/novapay/agents/send-money",
        headers=headers,
        json={"recipient": "0700000001", "amount": "50000", "currency": "UGX"},
    )
    receive_money = client.post(
        "/v1/novapay/agents/receive-money",
        headers=headers,
        json={"wallet_id": "wallet-1", "amount": "10000", "currency": "UGX"},
    )
    cash_in = client.post(
        "/v1/novapay/agents/cash-in",
        headers=headers,
        json={"customer": "customer-1", "amount": "25000", "currency": "UGX"},
    )
    cash_out = client.post(
        "/v1/novapay/agents/cash-out",
        headers=headers,
        json={"customer": "customer-1", "amount": "25000", "currency": "UGX"},
    )
    sync = client.post(
        "/v1/novapay/agents/sync",
        headers=headers,
        json={"idempotency_key": "idem-1", "queued": True},
    )

    for response in (send_money, receive_money, cash_in, cash_out, sync):
        assert response.status_code == 200
        assert response.json()["status"] in {"preview", "queued"}
        assert "NovaPower" in response.json()["policy"]
