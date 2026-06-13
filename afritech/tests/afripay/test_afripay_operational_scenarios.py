from __future__ import annotations

from decimal import Decimal
from importlib import import_module

import pytest
from rest_framework.test import APIRequestFactory

from afritech.afripay.config import EnvironmentConfig
from afritech.afripay.exceptions import DuplicateReference, ProviderFailure
from afritech.afripay.intelligence import FraudDetector
from afritech.afripay.models import Transaction, new_id
from afritech.afripay.money import Money
from afritech.afripay.orchestration import PaymentOrchestrator
from afritech.afripay.providers import SimulatedPaymentProvider
from afritech.afripay.treasury import TreasuryEngine
from afritech.simulation.scale.afripay_load import simulate_afripay_tps


def afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")


def afripay_views():
    return import_module("afriride_system.django_app.apps.afripay.views")


def afripay_security():
    return import_module("afriride_system.django_app.apps.afripay.security")


def auth_request(factory, method, path, data=None, scopes=None):
    request = getattr(factory, method)(path, data or {}, format="json")
    request.afripay_principal = type("P", (), {"subject": "tester"})()
    request.afripay_scopes = set(scopes or [])
    return request


@pytest.mark.django_db
def test_load_simulation_10k_tps_is_deterministic():
    first = simulate_afripay_tps(10000, duration_seconds=1, worker_count=16)
    second = simulate_afripay_tps(10000, duration_seconds=1, worker_count=16)

    assert first.event_count == 10000
    assert first.target_tps == 10000
    assert first.duration_seconds == 1
    assert len(first.checksum) == 64
    assert first == second


def test_fraud_detection_scores_large_offline_velocity():
    detector = FraudDetector()
    transaction = Transaction(
        transaction_id=new_id("tx"),
        reference="fraud.001",
        payer_id="payer.001",
        payee_id="merchant.001",
        amount=Money.of("6000.00", "USD"),
        transaction_type="payment",
        metadata={"channel": "offline"},
    )
    recent = tuple(
        Transaction(
            transaction_id=new_id("tx"),
            reference=f"fraud.history.{index}",
            payer_id=f"payer.{index}",
            payee_id="merchant.001",
            amount=Money.of("20.00", "USD"),
            transaction_type="payment",
        )
        for index in range(5)
    )

    signal = detector.score(transaction, recent_transactions=recent)

    assert signal.score >= Decimal("0.60")
    assert "large_amount" in signal.reasons
    assert "large_offline_payment" in signal.reasons
    assert "repeated_payee_velocity" in signal.reasons


def test_chaos_provider_failure_releases_treasury():
    treasury = TreasuryEngine()
    treasury.add_pool(
        pool_id="pool.bank.aud",
        provider="bank_partner",
        balance=Money.of("100.00", "AUD"),
        low_watermark=Money.of("10.00", "AUD"),
    )
    provider = SimulatedPaymentProvider(
        name="bank_partner",
        rail="bank",
        fee_rate="0.001",
        fixed_fee="0.01",
        latency_ms=120,
        reliability="0.99",
        fail=True,
    )
    orchestrator = PaymentOrchestrator(
        providers=(provider,),
        treasury=treasury,
        config=EnvironmentConfig(live_settlement_enabled=True, compliance_activation_reference="test-activation"),
    )

    with pytest.raises(ProviderFailure):
        orchestrator.process_payment(
            payer_id="payer.001",
            payee_id="payee.001",
            amount=Money.of("25.00", "AUD"),
            reference="chaos.payment.001",
        )

    assert treasury.available("bank_partner", "AUD") == Money.of("100.00", "AUD")


@pytest.mark.django_db
def test_end_to_end_payment_flow_updates_payment_ledger_and_metrics():
    client_secret = "e2e-secret"
    models = afripay_models()
    models.OAuthClient.objects.create(
        client_id="afripay-e2e",
        name="AfriPay E2E Client",
        secret_hash=models.OAuthClient.hash_secret(client_secret),
        scopes=[
            "payments:write",
            "payments:read",
            "events:read",
            "treasury:read",
            "monitoring:read",
        ],
        is_active=True,
    )

    token = afripay_security().OAuth2TokenService().issue_access_token(
        models.OAuthClient.objects.get(client_id="afripay-e2e"),
        ["payments:write", "payments:read", "events:read", "treasury:read", "monitoring:read"],
    )["access_token"]

    principal = afripay_security().OAuth2TokenService().verify_access_token(token)
    factory = APIRequestFactory()

    payment_request = factory.post(
        "/api/afripay/payments",
        {
            "payer_id": "diaspora.001",
            "payer_country": "AU",
            "payer_kyc_level": 2,
            "payee_id": "merchant.001",
            "payee_country": "BI",
            "payee_kyc_level": 2,
            "amount": "80.00",
            "currency": "AUD",
            "reference": "e2e.payment.001",
            "preference": "balanced",
        },
        format="json",
    )
    payment_request.afripay_principal = principal
    payment_request.afripay_scopes = set(principal.scopes)
    payment_response = afripay_views().payment_create_view(payment_request)

    assert payment_response.status_code == 201
    assert payment_response.data["status"] == "success"
    assert payment_response.data["journal_reference"] == "journal.e2e.payment.001"
    assert payment_response.data["routes"]

    detail_request = auth_request(
        factory,
        "get",
        "/api/afripay/payments/e2e.payment.001",
        scopes=["payments:read"],
    )
    detail_response = afripay_views().payment_detail_view(detail_request, "e2e.payment.001")
    assert detail_response.status_code == 200
    assert detail_response.data["reference"] == "e2e.payment.001"

    treasury_request = auth_request(
        factory,
        "get",
        "/api/afripay/treasury/pools",
        scopes=["treasury:read"],
    )
    treasury_response = afripay_views().treasury_pools_view(treasury_request)
    assert treasury_response.status_code == 200
    assert treasury_response.data["pools"]

    event_request = auth_request(
        factory,
        "get",
        "/api/afripay/events/e2e.payment.001",
        scopes=["events:read"],
    )
    event_response = afripay_views().event_replay_view(event_request, "e2e.payment.001")
    assert event_response.status_code == 200
    assert event_response.data["events"]

    metrics_request = auth_request(
        factory,
        "get",
        "/api/afripay/metrics",
        scopes=["monitoring:read"],
    )
    metrics_response = afripay_views().metrics_json_view(metrics_request)
    assert metrics_response.status_code == 200
    assert metrics_response.data["counters"]["transactions_total"] >= 1

    webhook_request = factory.post(
        "/api/afripay/webhooks/flutterwave",
        {"reference": "e2e.webhook.001"},
        format="json",
        HTTP_X_WEBHOOK_SECRET="e2e-secret",
    )
    response = afripay_views().webhook_view(webhook_request, "flutterwave")
    assert response.status_code == 202

    assert models.Transaction.objects.filter(reference="e2e.payment.001").exists()
