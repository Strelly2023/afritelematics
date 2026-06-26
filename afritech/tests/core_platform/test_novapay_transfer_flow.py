from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import build_core_platform_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    return TestClient(app)


def _headers(role: str = "RIDER", user_id: str = "sender-1", organization_id: str = "org-pay") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_novapay_transfer_quote_execute_and_verify() -> None:
    client = _client()

    features = client.get("/v1/core-platform/transfers/features")
    limits = client.get("/v1/core-platform/transfers/limits")
    rails = client.get("/v1/core-platform/transfers/rails")
    assert features.status_code == 200
    assert limits.status_code == 200
    assert rails.status_code == 200
    assert features.json()["best_money_transfer_app"] == "NovaPay"
    assert "bank_deposit" in features.json()["payout_methods"]

    quote = client.post(
        "/v1/core-platform/transfers/quote",
        headers=_headers(),
        json={
            "recipient_name": "Amina Okello",
            "recipient_identifier": "+254700000001",
            "recipient_country": "KE",
            "amount": "100.00",
            "source_currency": "AUD",
            "payout_method": "bank_deposit",
            "use_case": "transparent_pricing",
            "memo": "family support",
        },
    )
    assert quote.status_code == 200
    quote_body = quote.json()["quote"]
    assert quote_body["quote_hash"]
    assert quote_body["transfer_limit"]
    assert quote_body["mid_market_rate"]

    execute = client.post(
        "/v1/core-platform/transfers/execute",
        headers=_headers(),
        json={"quote": quote_body, "provider": "mobile_money", "live_provider": False},
    )
    assert execute.status_code == 200
    receipt = execute.json()["receipt"]
    assert receipt["receipt_hash"]
    assert receipt["audit_signature"]["scheme"]
    assert receipt["payment"]["provider"]

    verify = client.post(
        "/v1/core-platform/transfers/verify",
        headers=_headers(),
        json={"receipt": receipt},
    )
    assert verify.status_code == 200
    assert verify.json()["valid"] is True
    assert verify.json()["reason"] == "transfer_receipt_verified"
