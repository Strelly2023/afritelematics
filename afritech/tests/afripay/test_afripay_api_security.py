from __future__ import annotations

from decimal import Decimal
import json
from importlib import import_module
from urllib.parse import parse_qs

import httpx
import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from afritech.afripay.money import Money
from afritech.afripay.models import PaymentRoute as DomainPaymentRoute
from afritech.afripay.providers_sandbox import FlutterwaveSandboxProvider, MpesaSandboxProvider


def afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")


def afripay_views():
    return import_module("afriride_system.django_app.apps.afripay.views")


def afripay_security():
    return import_module("afriride_system.django_app.apps.afripay.security")


def afripay_middleware():
    return import_module("afriride_system.django_app.apps.afripay.middleware")


@pytest.mark.django_db
def test_oauth_token_issue_and_api_key_flow():
    client_secret = "super-secret"
    models = afripay_models()
    models.OAuthClient.objects.create(
        client_id="afripay-client",
        name="AfriPay API",
        secret_hash=models.OAuthClient.hash_secret(client_secret),
        scopes=["payments:write", "api_keys:write", "monitoring:read"],
        is_active=True,
    )

    factory = APIRequestFactory()
    request = factory.post(
        "/api/afripay/auth/oauth/token",
        {
            "grant_type": "client_credentials",
            "client_id": "afripay-client",
            "client_secret": client_secret,
            "scope": "payments:write api_keys:write monitoring:read",
        },
        format="json",
    )
    token_response = afripay_views().oauth_token_view(request)

    assert token_response.status_code == 200
    assert token_response.data["token_type"] == "Bearer"
    principal = afripay_security().OAuth2TokenService().verify_access_token(token_response.data["access_token"])
    assert principal.subject == "afripay-client"
    assert "payments:write" in principal.scopes

    authed_request = factory.post(
        "/api/afripay/auth/api-keys",
        {"name": "ops-console", "scopes": ["monitoring:read"]},
        format="json",
    )
    authed_request.afripay_principal = principal
    authed_request.afripay_scopes = {"api_keys:write", "payments:write", "monitoring:read"}
    key_response = afripay_views().api_key_issue_view(authed_request)

    assert key_response.status_code == 201
    raw_key = key_response.data["api_key"]
    key_principal = afripay_security().APIKeyService().authenticate(raw_key)
    assert key_principal.client_name == "ops-console"
    assert key_principal.scheme == "api_key"


@pytest.mark.django_db
def test_protected_metrics_and_middleware_gate():
    factory = APIRequestFactory()
    request = factory.get("/api/afripay/payments")
    middleware = afripay_middleware().AfriPaySecurityMiddleware(lambda req: None)

    response = middleware(request)

    assert response.status_code == 401

    snapshot_request = factory.get("/api/afripay/metrics")
    snapshot_request.afripay_principal = type("P", (), {"subject": "ops", "scopes": ("monitoring:read",)})()
    snapshot_request.afripay_scopes = {"monitoring:read"}
    snapshot = afripay_views().metrics_json_view(snapshot_request)

    assert snapshot.status_code == 200
    assert "counters" in snapshot.data

    prom = afripay_views().metrics_prometheus_view(snapshot_request)
    assert prom.status_code == 200
    assert "afripay_transactions_total" in prom.data


@pytest.mark.django_db
def test_middleware_allows_webhook_prefix_without_bearer():
    factory = APIRequestFactory()
    request = factory.post("/api/afripay/webhooks/flutterwave", {"reference": "wh.001"}, format="json")
    middleware = afripay_middleware().AfriPaySecurityMiddleware(lambda req: type("R", (), {"status_code": 204})())

    response = middleware(request)

    assert response.status_code == 204


def _mock_transport(callback):
    return httpx.MockTransport(callback)


def test_flutterwave_sandbox_provider_builds_real_request():
    calls: list[tuple[str, str, dict[str, str] | None, dict[str, str] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.content:
            raw = request.content.decode("utf-8")
            body = json.loads(raw) if raw.lstrip().startswith("{") else {k: v[0] for k, v in parse_qs(raw).items()}
        else:
            body = {}
        calls.append((request.method, str(request.url), dict(request.headers), body))
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "flw-token", "expires_in": 600})
        return httpx.Response(200, json={"status": "success", "data": {"id": "flw.tx.001"}})

    provider = FlutterwaveSandboxProvider(
        client_id="flw-client",
        client_secret="flw-secret",
        transport=_mock_transport(handler),
    )
    result = provider.send(
        DomainPaymentRoute(
            route_id="route.flw.001",
            transaction_id="tx.flw.001",
            provider="flutterwave_sandbox",
            rail="bank",
            amount=Money.of("12.00", "USD"),
            fee=Money.of("0.00", "USD"),
        )
    )

    assert result.external_reference == "flw.tx.001"
    assert calls[0][0] == "POST"
    assert calls[0][1].endswith("/token")
    assert calls[1][1].endswith("/transfers")
    assert calls[1][3]["reference"] == "route.flw.001"


def test_mpesa_sandbox_provider_builds_real_request():
    calls: list[tuple[str, str, dict[str, str] | None, dict[str, str] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.content:
            raw = request.content.decode("utf-8")
            body = json.loads(raw) if raw.lstrip().startswith("{") else {k: v[0] for k, v in parse_qs(raw).items()}
        else:
            body = {}
        calls.append((request.method, str(request.url), dict(request.headers), body))
        if request.url.path.endswith("/generate"):
            return httpx.Response(200, json={"access_token": "mpesa-token", "expires_in": 600})
        return httpx.Response(
            200,
            json={"ResponseCode": "0", "CheckoutRequestID": "mpesa.checkout.001"},
        )

    provider = MpesaSandboxProvider(
        consumer_key="mpesa-key",
        consumer_secret="mpesa-secret",
        short_code="174379",
        passkey="passkey",
        callback_url="https://example.com/callback",
        transport=_mock_transport(handler),
    )
    result = provider.send(
        DomainPaymentRoute(
            route_id="route.mpesa.001",
            transaction_id="tx.mpesa.001",
            provider="mpesa_sandbox",
            rail="mobile_money",
            amount=Money.of("15.00", "KES"),
            fee=Money.of("0.00", "KES"),
        )
    )

    assert result.external_reference == "mpesa.checkout.001"
    assert calls[0][0] == "GET"
    assert calls[0][1].endswith("/oauth/v1/generate?grant_type=client_credentials")
    assert calls[1][1].endswith("/mpesa/stkpush/v1/processrequest")
    assert calls[1][3]["AccountReference"] == "route.mpesa.001"


@pytest.mark.django_db
def test_expired_idempotency_keys_show_up_in_alerts():
    models = afripay_models()
    models.LiquidityPool.objects.create(
        pool_id="pool.mtn.aud",
        provider="mtn_mobile_money",
        currency="AUD",
        balance=Decimal("100.00"),
        reserved=Decimal("10.00"),
        low_watermark=Decimal("95.00"),
    )
    models.IdempotencyKey.objects.create(
        key="idem.001",
        request_hash="a" * 64,
        response={},
        status="stored",
        expires_at=timezone.now() - timezone.timedelta(days=1),
    )

    request = APIRequestFactory().get("/api/afripay/alerts")
    request.afripay_principal = type("P", (), {"subject": "ops", "scopes": ("monitoring:read",)})()
    request.afripay_scopes = {"monitoring:read"}

    response = afripay_views().alerts_view(request)

    assert response.status_code == 200
    assert any(alert["name"] == "low_liquidity" for alert in response.data["alerts"])
