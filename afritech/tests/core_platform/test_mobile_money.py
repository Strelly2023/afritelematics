from __future__ import annotations

from decimal import Decimal
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)
from afritech.core_platform.models import PaymentIntent
from afritech.core_platform.payments.mobile_money import (
    MpesaDarajaProvider,
    RAILS_BY_PROVIDER,
    mobile_money_catalog,
    mobile_money_provider_for,
)
from afritech.fintech.webhook_security import sign_webhook


def _intent(
    *,
    country: str,
    currency: str,
    destination: str,
    intent_id: str = "mobile-money-001",
    commercial_approval_reference: str | None = None,
) -> PaymentIntent:
    metadata = {"country": country, "description": "NovaRide trip"}
    if commercial_approval_reference:
        metadata["commercial_approval_reference"] = commercial_approval_reference
    return PaymentIntent(
        intent_id=intent_id,
        actor_id="mobile-operator",
        organization_id="mobile-org",
        amount=Decimal("125"),
        currency=currency,
        destination=destination,
        metadata=metadata,
    )


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    app.include_router(build_public_trust_explorer_router())
    return TestClient(app)


def _headers() -> dict[str, str]:
    token = JWT.create_token(
        "mobile-operator",
        role="OPERATOR",
        organization_id="mobile-org",
    )
    return {"Authorization": f"Bearer {token}"}


def test_mobile_money_catalog_covers_burundi_kenya_and_drc() -> None:
    catalog = mobile_money_catalog()

    assert set(catalog["countries"]) == {"BI", "CD", "KE"}
    assert catalog["countries"]["BI"]["currency"] == "BIF"
    assert catalog["countries"]["KE"]["default_provider"] == "mpesa_ke"
    assert catalog["countries"]["CD"]["default_provider"] == "orange_money_cd"
    providers = {
        provider["provider"]
        for country in catalog["countries"].values()
        for provider in country["providers"]
    }
    assert {
        "mpesa_ke",
        "airtel_money_ke",
        "lumicash_bi",
        "ecocash_bi",
        "orange_money_cd",
        "airtel_money_cd",
        "mpesa_cd",
    }.issubset(providers)


@pytest.mark.parametrize(
    ("country", "currency", "destination", "expected_provider"),
    (
        ("KE", "KES", "+254700000001", "mpesa_ke"),
        ("BI", "BIF", "+25779000001", "lumicash_bi"),
        ("CD", "CDF", "+243810000001", "orange_money_cd"),
    ),
)
def test_mobile_money_default_routing_is_country_aware(
    country: str,
    currency: str,
    destination: str,
    expected_provider: str,
) -> None:
    intent = _intent(
        country=country,
        currency=currency,
        destination=destination,
    )

    provider = mobile_money_provider_for(
        "mobile_money",
        intent=intent,
        live=False,
    )
    result = provider.authorize(intent)

    assert result.provider == expected_provider
    assert result.status == "pending"
    assert result.settlement_status == "pending_user_authorization"
    assert result.raw["live_network_called"] is False


def test_mobile_money_rejects_wrong_currency_and_invalid_msisdn() -> None:
    wrong_currency = _intent(
        country="KE",
        currency="USD",
        destination="+254700000001",
    )
    with pytest.raises(ValueError, match="requires KES"):
        mobile_money_provider_for(
            "mpesa_ke",
            intent=wrong_currency,
            live=False,
        )

    bad_phone = _intent(country="BI", currency="BIF", destination="123")
    provider = mobile_money_provider_for(
        "lumicash_bi",
        intent=bad_phone,
        live=False,
    )
    with pytest.raises(ValueError, match="must_be_e164"):
        provider.authorize(bad_phone)


def test_mpesa_live_adapter_builds_daraja_stk_push(monkeypatch) -> None:
    monkeypatch.setenv("NOVAPAY_MOBILE_MONEY_LIVE_ENABLED", "true")
    monkeypatch.setenv("NOVAPAY_MPESA_KE_LIVE_MODE", "true")
    monkeypatch.setenv("NOVAPAY_MPESA_KE_CONSUMER_KEY", "consumer")
    monkeypatch.setenv("NOVAPAY_MPESA_KE_CONSUMER_SECRET", "secret")
    monkeypatch.setenv("NOVAPAY_MPESA_KE_SHORT_CODE", "174379")
    monkeypatch.setenv("NOVAPAY_MPESA_KE_PASSKEY", "passkey")
    monkeypatch.setenv(
        "NOVAPAY_MPESA_KE_CALLBACK_URL",
        "https://api.example.com/webhooks/payments",
    )
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "daraja-token"})
        return httpx.Response(
            200,
            json={
                "ResponseCode": "0",
                "CheckoutRequestID": "ws_CO_123",
                "ResponseDescription": "Success. Request accepted for processing",
            },
        )

    provider = MpesaDarajaProvider(
        rail=RAILS_BY_PROVIDER["mpesa_ke"],
        live=True,
        transport=httpx.MockTransport(handler),
    )
    result = provider.authorize(
        _intent(
            country="KE",
            currency="KES",
            destination="+254700000001",
            commercial_approval_reference="safaricom-contract-001",
        )
    )

    assert result.provider_reference == "ws_CO_123"
    assert result.status == "pending"
    assert requests[1].url.path == "/mpesa/stkpush/v1/processrequest"
    assert requests[1].headers["idempotency-key"] == (
        "novapay:mobile-org:mobile-money-001"
    )


def test_mobile_money_api_and_settlement_create_separate_trust_receipt(
    monkeypatch,
) -> None:
    secret = "mpesa-webhook-secret"
    monkeypatch.setenv("NOVAPAY_MPESA_KE_WEBHOOK_SECRET", secret)
    client = _client()
    payment_response = client.post(
        "/v1/core-platform/payments/execute",
        headers=_headers(),
        json={
            "intent_id": "mpesa-api-001",
            "amount": "125",
            "currency": "KES",
            "destination": "+254700000001",
            "provider": "mobile_money",
            "metadata": {"country": "KE", "description": "NovaRide trip"},
        },
    )

    assert payment_response.status_code == 200
    payment = payment_response.json()["result"]["payment"]
    assert payment["provider"] == "mpesa_ke"
    assert payment["status"] == "pending"

    payload = {
        "event_id": "mpesa-callback-001",
        "provider": "mpesa_ke",
        "provider_reference": payment["provider_reference"],
        "payment_id": payment["payment_id"],
        "status": "completed",
        "settlement_status": "settled",
    }
    timestamp = int(time.time())
    webhook = client.post(
        "/webhooks/payments",
        headers={
            "X-NovaPay-Timestamp": str(timestamp),
            "X-NovaPay-Signature": sign_webhook(
                payload,
                timestamp=timestamp,
                secret=secret,
            ),
        },
        json=payload,
    )

    assert webhook.status_code == 200
    body = webhook.json()
    assert body["settlement_status"] == "settled"
    assert body["settlement_authority"] is False
    assert body["settlement_trust"]["event_type"] == "core.payment.settled"
    explorer = client.get(
        body["trust_explorer"],
        headers={"Accept": "application/json"},
    )
    assert explorer.status_code == 200
    assert explorer.json()["packet"]["settlement"]["provider"] == "mpesa_ke"
