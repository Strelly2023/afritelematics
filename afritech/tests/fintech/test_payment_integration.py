from __future__ import annotations

from decimal import Decimal

from afritech.fintech.mock_provider import ControlledPayIDProvider
from afritech.fintech.payment_provider import ProviderPaymentRequest
from afritech.fintech.webhooks import normalize_payment_webhook


def test_controlled_payid_provider_executes_deterministic_rehearsal() -> None:
    provider = ControlledPayIDProvider()
    request = ProviderPaymentRequest(
        intent_id="intent-rehearsal-001",
        actor_id="rider-001",
        organization_id="org-novaride",
        amount=Decimal("24.50"),
        currency="AUD",
        destination="rider@example.com",
        metadata={"ride_id": "ride-001"},
    )

    first = provider.execute_payment(request)
    replay = provider.execute_payment(request)

    assert first == replay
    assert first.provider == "payid"
    assert first.provider_reference.startswith("PAYID-")
    assert first.raw["mode"] == "controlled_rehearsal"
    assert first.raw["live_network_called"] is False
    assert first.raw["metadata"] == {"ride_id": "ride-001"}


def test_webhook_normalizer_flattens_mpesa_callback_without_mutating_evidence() -> None:
    payload = {
        "provider": "mobile_money",
        "event_id": "event-mpesa-001",
        "Body": {
            "stkCallback": {
                "CheckoutRequestID": "checkout-001",
                "AccountReference": "payment-001",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
            }
        },
    }

    event = normalize_payment_webhook(payload)

    assert event.provider_reference == "checkout-001"
    assert event.payment_id == "payment-001"
    assert event.settlement_status == "settled"
    assert event.payload is payload
