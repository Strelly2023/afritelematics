from __future__ import annotations

import base64
from decimal import Decimal
import hashlib
import hmac
import json
import os
import time
from importlib import import_module
from urllib.parse import parse_qs

import httpx
import pytest
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.test import APIRequestFactory

from afritech.afripay.money import Money
from afritech.afripay.models import PaymentRoute as DomainPaymentRoute
from afritech.afripay.providers_sandbox import FlutterwaveSandboxProvider, MfsAfricaProvider, MpesaSandboxProvider
from afritech.afriprogramming.rbac import canonical_role_name


os.environ.setdefault("AFRIRIDE_JWT_SECRET", "afripay-rbac-test-secret")


def afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")


def afripay_views():
    return import_module("afriride_system.django_app.apps.afripay.views")


def afripay_security():
    return import_module("afriride_system.django_app.apps.afripay.security")


def afripay_middleware():
    return import_module("afriride_system.django_app.apps.afripay.middleware")


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _afriride_test_token(subject: str, role: str) -> str:
    secret = os.environ["AFRIRIDE_JWT_SECRET"].encode("utf-8")
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": canonical_role_name(role),
        "exp": int(time.time()) + 12 * 60 * 60,
    }
    signing_input = ".".join(
        (
            _b64url_encode(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
            _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()),
        )
    )
    signature = hmac.new(secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _rbac_authed_request(factory, method: str, path: str, data: dict | None, subject: str, role: str, scopes: list[str]):
    token = _afriride_test_token(subject, role)
    request = getattr(factory, method)(
        path,
        data or {},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    middleware = afripay_middleware().AfriPaySecurityMiddleware(lambda req: HttpResponse(status=204))
    middleware(request)
    return request


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


@pytest.mark.django_db
def test_middleware_maps_afriride_role_tokens_to_payment_scopes():
    factory = APIRequestFactory()
    token = _afriride_test_token("driver-1", "DRIVER")
    request = factory.get("/api/afripay/payments", HTTP_AUTHORIZATION=f"Bearer {token}")
    middleware = afripay_middleware().AfriPaySecurityMiddleware(lambda req: HttpResponse(status=204))

    response = middleware(request)

    assert response.status_code == 204
    assert request.afripay_auth_scheme == "rbac_jwt"
    assert request.afripay_identity == "driver-1"
    assert "payments:read" in request.afripay_scopes
    assert "payouts:read" in request.afripay_scopes


@pytest.mark.django_db
def test_rbac_jwt_payment_create_requires_subject_bound_payer():
    factory = APIRequestFactory()
    allowed_request = _rbac_authed_request(
        factory,
        "post",
        "/api/afripay/payments",
        {
            "payer_id": "driver-1",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "merchant.001",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "18.00",
            "currency": "AUD",
            "reference": "rbac.payment.allowed",
            "preference": "balanced",
        },
        subject="driver-1",
        role="DRIVER",
        scopes=["payments:write", "payments:read", "wallets:read", "monitoring:read"],
    )
    allowed_response = afripay_views().payment_create_view(allowed_request)

    assert allowed_response.status_code == 201
    assert allowed_response.data["identity_context"]["identity_bound"] is True
    assert allowed_response.data["identity_context"]["binding_mode"] == "subject_bound"

    denied_request = _rbac_authed_request(
        factory,
        "post",
        "/api/afripay/payments",
        {
            "payer_id": "driver-1",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "merchant.001",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "18.00",
            "currency": "AUD",
            "reference": "rbac.payment.denied",
            "preference": "balanced",
        },
        subject="driver-2",
        role="DRIVER",
        scopes=["payments:write", "payments:read", "wallets:read", "monitoring:read"],
    )
    denied_response = afripay_views().payment_create_view(denied_request)

    assert denied_response.status_code == 403
    assert "subject-bound" in denied_response.data["detail"]


@pytest.mark.django_db
def test_rbac_jwt_payment_and_wallet_details_are_owner_bound():
    models = afripay_models()
    payer = models.AfriPayParty.objects.create(
        party_id="driver-1",
        country="AU",
        kyc_level=2,
        risk_score=Decimal("0"),
    )
    payee = models.AfriPayParty.objects.create(
        party_id="merchant.001",
        country="BI",
        kyc_level=2,
        risk_score=Decimal("0"),
    )
    wallet = models.Wallet.objects.create(
        wallet_id="wallet.driver.1",
        owner=payer,
        wallet_type="personal",
        home_country="AU",
    )
    models.Transaction.objects.create(
        transaction_id="tx.rbac.001",
        reference="rbac.payment.detail",
        payer=payer,
        payee=payee,
        amount=Decimal("18.00"),
        currency="AUD",
        transaction_type="payment",
        metadata={},
    )

    factory = APIRequestFactory()
    denied_payment_request = _rbac_authed_request(
        factory,
        "get",
        "/api/afripay/payments/rbac.payment.detail",
        None,
        subject="driver-2",
        role="DRIVER",
        scopes=["payments:read", "wallets:read", "monitoring:read"],
    )
    denied_payment_response = afripay_views().payment_detail_view(denied_payment_request, "rbac.payment.detail")
    assert denied_payment_response.status_code == 403

    allowed_payment_request = _rbac_authed_request(
        factory,
        "get",
        "/api/afripay/payments/rbac.payment.detail",
        None,
        subject="driver-1",
        role="DRIVER",
        scopes=["payments:read", "wallets:read", "monitoring:read"],
    )
    allowed_payment_response = afripay_views().payment_detail_view(allowed_payment_request, "rbac.payment.detail")
    assert allowed_payment_response.status_code == 200
    assert allowed_payment_response.data["reference"] == "rbac.payment.detail"

    denied_wallet_request = _rbac_authed_request(
        factory,
        "get",
        "/api/afripay/wallets/wallet.driver.1",
        None,
        subject="driver-2",
        role="DRIVER",
        scopes=["wallets:read", "monitoring:read"],
    )
    denied_wallet_response = afripay_views().wallet_detail_view(denied_wallet_request, "wallet.driver.1")
    assert denied_wallet_response.status_code == 403

    allowed_wallet_request = _rbac_authed_request(
        factory,
        "get",
        "/api/afripay/wallets/wallet.driver.1",
        None,
        subject="driver-1",
        role="DRIVER",
        scopes=["wallets:read", "monitoring:read"],
    )
    allowed_wallet_response = afripay_views().wallet_detail_view(allowed_wallet_request, "wallet.driver.1")
    assert allowed_wallet_response.status_code == 200
    assert allowed_wallet_response.data["wallet_id"] == "wallet.driver.1"


@pytest.mark.django_db
def test_novapay_wiring_surface_exposes_control_plane_links():
    factory = APIRequestFactory()
    request = factory.get(
        "/api/novapay/wiring",
        {"organization_id": "tenant-001", "role": "ADMIN", "limit": "4"},
    )
    request.afripay_principal = afripay_security().SecurityPrincipal(
        subject="afripay-console",
        scheme="oauth2",
        scopes=("monitoring:read",),
        client_name="afripay-console",
    )
    request.afripay_scopes = {"monitoring:read"}

    response = afripay_views().wiring_view(request)

    assert response.status_code == 200
    assert response.data["status"] == "wired"
    assert response.data["organization_id"] == "tenant-001"
    assert set(response.data["wiring"]) == {"novasync", "novatrust", "novaid", "novapay", "control_plane"}
    assert response.data["wiring"]["novasync"]["signed_audit_chain"]["read_only"] is True
    assert response.data["wiring"]["novapay"]["billing_preview"]["read_only"] is True
    assert response.data["wiring"]["control_plane"]["controlled_execution_activation"]["read_only"] is True
    assert any(link["path"] == "/api/novapay/wiring" for link in response.data["links"])


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


def test_mfs_africa_provider_builds_configurable_real_request():
    calls: list[tuple[str, str, dict[str, str] | None, dict[str, str] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.content:
            raw = request.content.decode("utf-8")
            body = json.loads(raw) if raw.lstrip().startswith("{") else {k: v[0] for k, v in parse_qs(raw).items()}
        else:
            body = {}
        calls.append((request.method, str(request.url), dict(request.headers), body))
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "mfs-token", "expires_in": 600})
        return httpx.Response(
            200,
            json={"status": "submitted", "data": {"id": "mfs.tx.001"}},
        )

    provider = MfsAfricaProvider(
        client_id="mfs-client",
        client_secret="mfs-secret",
        api_base_url="https://partner.example",
        token_url="https://partner.example/oauth/token",
        transfer_path="/payments",
        transport=_mock_transport(handler),
    )
    result = provider.send(
        DomainPaymentRoute(
            route_id="route.mfs.001",
            transaction_id="tx.mfs.001",
            provider="mfs_africa",
            rail="mobile_money",
            amount=Money.of("15.00", "KES"),
            fee=Money.of("0.00", "KES"),
        )
    )

    assert result.external_reference == "mfs.tx.001"
    assert calls[0][0] == "POST"
    assert calls[0][1].endswith("/oauth/token")
    assert calls[1][1].endswith("/payments")
    assert calls[1][2]["idempotency-key"] == "route.mfs.001"
    assert calls[1][3]["reference"] == "route.mfs.001"


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
