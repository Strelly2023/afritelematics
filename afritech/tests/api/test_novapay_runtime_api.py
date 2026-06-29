from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novapay_runtime_api import build_novapay_runtime_router
from afritech.core_platform.novapay_runtime import NovaPayRuntimeEngine


def _client() -> TestClient:
    app = FastAPI()
    runtime = NovaPayRuntimeEngine()
    app.include_router(build_auth_router())
    app.include_router(build_novapay_runtime_router(runtime=runtime))
    return TestClient(app)


def _headers(role: str = "CUSTOMER", user_id: str = "sender-1", organization_id: str = "org-pay") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def _transfer_payload() -> dict[str, object]:
    return {
        "transfer_type": "Cross-Border Remittance",
        "recipient_name": "Amina Okello",
        "recipient_identifier": "+254700000001",
        "recipient_country": "KE",
        "amount": "100.00",
        "source_currency": "AUD",
        "source_country": "AU",
        "funding_source_type": "wallet",
        "funding_source_reference": "wallet-ref-1",
        "payout_method": "mobile_money",
        "use_case": "family_support",
        "memo": "school fees",
        "recipient_type": "individual",
        "live_provider": False,
        "auto_execute": False,
    }


def test_novapay_runtime_admission_and_execution_flow() -> None:
    client = _client()

    jurisdictions = client.get("/v1/jurisdictions", headers=_headers())
    assert jurisdictions.status_code == 200
    assert jurisdictions.json()["jurisdictions"]

    funding_source = client.post(
        "/v1/funding-sources/validate",
        headers=_headers(),
        json={
            "funding_source_type": "wallet",
            "owner_id": "sender-1",
            "provider": "novapay-wallet",
            "reference": "wallet-ref-1",
        },
    )
    assert funding_source.status_code == 200
    assert funding_source.json()["funding_source"]["type"] == "wallet"

    quote = client.post("/v1/transfers/quote", headers=_headers(), json=_transfer_payload())
    assert quote.status_code == 200
    quote_body = quote.json()
    assert quote_body["transfer"]["quote"]["quote_id"]
    assert quote_body["transfer"]["decision_trace"]["policy_id"] == "novapay.transfer.policy.v1"

    create = client.post("/v1/transfers", headers=_headers(), json=_transfer_payload())
    assert create.status_code == 200
    create_body = create.json()
    transfer_id = create_body["transfer_id"]
    assert create_body["transfer"]["status"] == "quoted"
    assert create_body["receipt"] is None

    execute = client.post(f"/v1/transfers/{transfer_id}/execute", headers=_headers(role="OPERATOR"))
    assert execute.status_code == 200
    execute_body = execute.json()
    assert execute_body["transfer"]["status"] in {"settled", "completed"}
    assert execute_body["receipt"]["signature"]["scheme"] == "ed25519"
    assert execute_body["verification"]["valid"] is True

    receipt = client.get(f"/v1/transfers/{transfer_id}/receipt", headers=_headers())
    assert receipt.status_code == 200
    assert receipt.json()["receipt"]["verification_code"]

    verification = client.get(f"/v1/transfers/{transfer_id}/verification", headers=_headers())
    assert verification.status_code == 200
    assert verification.json()["valid"] is True

    timeline = client.get(f"/v1/transfers/{transfer_id}/timeline", headers=_headers())
    assert timeline.status_code == 200
    assert len(timeline.json()["timeline"]) >= 2


def test_novapay_runtime_rejects_unsupported_transfer_type() -> None:
    client = _client()
    payload = _transfer_payload()
    payload["transfer_type"] = "Unsupported Rail"

    response = client.post("/v1/transfers", headers=_headers(), json=payload)
    assert response.status_code == 400
    assert response.json()["detail"].startswith("transfer_type_not_supported")
