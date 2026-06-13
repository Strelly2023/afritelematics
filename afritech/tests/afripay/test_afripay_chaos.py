from __future__ import annotations

from decimal import Decimal
from importlib import import_module

import httpx
import pytest

from afritech.afripay.config import EnvironmentConfig
from afritech.afripay.exceptions import ProviderFailure
from afritech.afripay.money import Money
from afritech.afripay.orchestration import PaymentOrchestrator
from afritech.afripay.providers import SimulatedPaymentProvider
from afritech.afripay.providers_sandbox import FlutterwaveSandboxProvider, MpesaSandboxProvider
from afritech.afripay.treasury import TreasuryEngine


def models():
    return import_module("afriride_system.django_app.apps.afripay.models")


def _mock_transport(callback):
    return httpx.MockTransport(callback)


def test_provider_outage_releases_reserved_liquidity():
    treasury = TreasuryEngine()
    treasury.add_pool(
        pool_id="pool.chaos.bank",
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
        config=EnvironmentConfig(live_settlement_enabled=True, compliance_activation_reference="chaos-test"),
    )

    with pytest.raises(ProviderFailure):
        orchestrator.process_payment(
            payer_id="payer.001",
            payee_id="payee.001",
            amount=Money.of("25.00", "AUD"),
            reference="chaos.payment.001",
        )

    assert treasury.available("bank_partner", "AUD") == Money.of("100.00", "AUD")


def test_flutterwave_sandbox_transport_failure_bubbles_as_provider_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("flutterwave sandbox down", request=request)

    provider = FlutterwaveSandboxProvider(
        client_id="flw-client",
        client_secret="flw-secret",
        transport=_mock_transport(handler),
    )

    route_model = models()
    route_model = route_model.PaymentRoute(
        route_id="route.flw.chaos",
        transaction_id="tx.flw.chaos",
        provider="flutterwave_sandbox",
        rail="bank",
        amount=Money.of("12.00", "USD"),
        fee=Money.of("0.00", "USD"),
    )

    with pytest.raises(httpx.ConnectError):
        provider.send(route_model)


def test_mpesa_sandbox_token_failure_bubbles_as_provider_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    provider = MpesaSandboxProvider(
        consumer_key="mpesa-key",
        consumer_secret="mpesa-secret",
        short_code="174379",
        passkey="passkey",
        callback_url="https://example.com/callback",
        transport=_mock_transport(handler),
    )

    route_model = models().PaymentRoute(
        route_id="route.mpesa.chaos",
        transaction_id="tx.mpesa.chaos",
        provider="mpesa_sandbox",
        rail="mobile_money",
        amount=Money.of("15.00", "KES"),
        fee=Money.of("0.00", "KES"),
    )

    with pytest.raises(ProviderFailure):
        provider.send(route_model)


def test_chaos_provider_failure_does_not_mutate_treasury_state():
    treasury = TreasuryEngine()
    treasury.add_pool(
        pool_id="pool.chaos.mobile",
        provider="mtn_mobile_money",
        balance=Money.of("70.00", "AUD"),
        low_watermark=Money.of("10.00", "AUD"),
    )
    provider = SimulatedPaymentProvider(
        name="mtn_mobile_money",
        rail="mobile_money",
        fee_rate="0.012",
        fixed_fee="0.20",
        latency_ms=900,
        reliability="0.97",
        fail=True,
    )

    with pytest.raises(ProviderFailure):
        provider.send(
            models().PaymentRoute(
                route_id="route.mtn.chaos",
                transaction_id="tx.mtn.chaos",
                provider="mtn_mobile_money",
                rail="mobile_money",
                amount=Money.of("20.00", "AUD"),
                fee=Money.of("0.00", "AUD"),
            )
        )

    assert treasury.available("mtn_mobile_money", "AUD") == Money.of("70.00", "AUD")

