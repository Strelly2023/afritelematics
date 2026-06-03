from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.security.integrity_trace import IntegrityTrace


@dataclass(frozen=True)
class PaymentIntentRequest:
    ride_id: str
    amount_minor: int
    currency: str = "aud"


class StripePilotService:
    """Deterministic payment-intent adapter for pilot integration tests.

    This does not contact Stripe. It creates a stable pilot intent envelope that
    can be replaced by a live provider adapter after compliance approval.
    """

    def create_payment(self, request: PaymentIntentRequest) -> dict[str, Any]:
        if request.amount_minor <= 0:
            raise ValueError("amount_minor must be positive")
        fingerprint = IntegrityTrace.hash_event(
            {
                "amount_minor": request.amount_minor,
                "currency": request.currency,
                "ride_id": request.ride_id,
            }
        )[:24]
        return {
            "provider": "stripe",
            "mode": "pilot_stub",
            "payment_intent_id": f"pi_pilot_{fingerprint}",
            "client_secret": f"pi_pilot_{fingerprint}_secret",
            "amount_minor": request.amount_minor,
            "currency": request.currency,
            "ride_id": request.ride_id,
        }


class PaymentEventFactory:
    """Convert provider/payment callbacks into AfriTech events."""

    def payment_triggered(
        self,
        *,
        event_id: str,
        ride_id: str,
        device_id: str,
        amount_minor: int,
        logical_clock: int,
        timestamp: int,
    ) -> dict[str, Any]:
        return {
            "event_id": event_id,
            "event_type": "PAYMENT_TRIGGERED",
            "device_id": device_id,
            "entity_id": ride_id,
            "timestamp": timestamp,
            "logical_clock": logical_clock,
            "payload": {
                "ride_id": ride_id,
                "amount_minor": amount_minor,
            },
        }

    def payment_confirmed_from_provider(
        self,
        *,
        event_id: str,
        provider: str,
        transaction_id: str,
        ride_id: str,
        status: str,
        amount_minor: int,
        timestamp: int,
    ) -> dict[str, Any]:
        return {
            "event_id": event_id,
            "event_type": "PAYMENT_CONFIRMED",
            "device_id": f"{provider}_webhook",
            "entity_id": ride_id,
            "timestamp": timestamp,
            "logical_clock": 0,
            "payload": {
                "amount_minor": amount_minor,
                "provider": provider,
                "ride_id": ride_id,
                "status": status,
                "transaction_id": transaction_id,
            },
        }

    def mobile_money_confirmed(
        self,
        *,
        event_id: str,
        transaction_id: str,
        ride_id: str,
        status: str,
        amount_minor: int,
        timestamp: int,
    ) -> dict[str, Any]:
        return self.payment_confirmed_from_provider(
            event_id=event_id,
            provider="mobile_money",
            transaction_id=transaction_id,
            ride_id=ride_id,
            status=status,
            amount_minor=amount_minor,
            timestamp=timestamp,
        )
