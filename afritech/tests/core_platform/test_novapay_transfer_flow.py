from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import build_core_platform_router
from decimal import Decimal

from afritech.core_platform.cryptographic_consensus import _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.models import Identity
from afritech.core_platform.transfers import NovaPayTransferService


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
        json={"quote": quote_body, "live_provider": False},
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


def test_novapay_transfer_execute_rejects_tampered_quote() -> None:
    client = _client()
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
        },
    ).json()["quote"]
    quote["quote_hash"] = "tampered"

    execute = client.post(
        "/v1/core-platform/transfers/execute",
        headers=_headers(),
        json={"quote": quote},
    )
    assert execute.status_code == 400
    assert execute.json()["detail"] == "transfer_quote_hash_mismatch"


def test_novapay_transfer_execute_rejects_provider_override() -> None:
    client = _client()
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
        },
    ).json()["quote"]

    execute = client.post(
        "/v1/core-platform/transfers/execute",
        headers=_headers(),
        json={"quote": quote, "provider": "mobile_money"},
    )
    assert execute.status_code == 400
    assert execute.json()["detail"] == "transfer_provider_mismatch"


def test_novapay_transfer_rejects_invalid_route_hint_provider() -> None:
    client = _client()
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
        },
    ).json()["quote"]

    tampered = dict(quote)
    tampered["route_hint"] = "fake_provider_xyz"
    tampered["quote_hash"] = _hash(
        {key: value for key, value in tampered.items() if key != "quote_hash"},
        domain=HASH_DOMAINS["TRANSFER_QUOTE"],
    )

    execute = client.post(
        "/v1/core-platform/transfers/execute",
        headers=_headers(),
        json={"quote": tampered},
    )
    assert execute.status_code == 400
    assert execute.json()["detail"] == "invalid_transfer_provider"


def test_novapay_transfer_rejects_missing_route_hint() -> None:
    client = _client()
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
        },
    ).json()["quote"]

    tampered = dict(quote)
    tampered.pop("route_hint", None)
    tampered["quote_hash"] = _hash(
        {key: value for key, value in tampered.items() if key != "quote_hash"},
        domain=HASH_DOMAINS["TRANSFER_QUOTE"],
    )

    execute = client.post(
        "/v1/core-platform/transfers/execute",
        headers=_headers(),
        json={"quote": tampered},
    )
    assert execute.status_code == 400
    assert execute.json()["detail"] == "missing_route_hint"


def test_novapay_transfer_execution_context_is_read_only() -> None:
    service = NovaPayTransferService()
    identity = Identity(
        identity_id="sender-1",
        email="sender@example.com",
        roles=("RIDER",),
        organization_id="org-pay",
    )
    quote = service.quote(
        identity=identity,
        recipient_name="Amina Okello",
        recipient_identifier="+254700000001",
        recipient_country="KE",
        amount=Decimal("100.00"),
        source_currency="AUD",
        payout_method="bank_deposit",
        use_case="transparent_pricing",
        memo="family support",
    )

    context = service.validate_quote(quote)

    try:
        context.unsigned_quote["source_amount"] = "999.00"  # type: ignore[index]
        raised = False
    except TypeError:
        raised = True

    assert raised is True


def test_novapay_transfer_execution_context_nested_is_read_only() -> None:
    service = NovaPayTransferService()
    identity = Identity(
        identity_id="sender-1",
        email="sender@example.com",
        roles=("RIDER",),
        organization_id="org-pay",
    )
    quote = service.quote(
        identity=identity,
        recipient_name="Amina Okello",
        recipient_identifier="+254700000001",
        recipient_country="KE",
        amount=Decimal("100.00"),
        source_currency="AUD",
        payout_method="bank_deposit",
        use_case="transparent_pricing",
        memo="family support",
    )

    context = service.validate_quote(quote)

    assert isinstance(context.unsigned_quote["features"]["use_cases"], tuple)  # type: ignore[index]

    try:
        context.unsigned_quote["features"]["use_cases"][0]["label"] = "tampered"  # type: ignore[index]
        raised = False
    except TypeError:
        raised = True

    assert raised is True
