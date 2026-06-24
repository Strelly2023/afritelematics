"""Provider adapters for NovaPay core platform payments.

The adapters expose production-shaped integration boundaries. PayID is
deterministic for local pilot use. Stripe can call the Stripe SDK when an API
key is supplied, while remaining safe in unconfigured test environments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from afritech.core_platform.models import PaymentIntent


@dataclass(frozen=True)
class PaymentProviderResult:
    provider: str
    provider_reference: str
    status: str
    settlement_status: str
    raw: dict[str, object]


class PayIDProvider:
    name = "payid"

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        reference = f"PAYID-{intent.organization_id}-{intent.intent_id}".upper()
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=reference,
            status="completed",
            settlement_status="settlement_pending",
            raw={
                "rail": "payid",
                "destination": intent.destination,
                "amount": str(intent.amount),
                "currency": intent.currency.upper(),
            },
        )


class StripeProvider:
    name = "stripe"

    def __init__(self, api_key: str | None = None, *, live: bool = False) -> None:
        self.api_key = api_key or os.environ.get("STRIPE_API_KEY")
        self.live = live or os.environ.get("STRIPE_LIVE_MODE", "").lower() in {"1", "true", "yes"}

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        if not self.live or not self.api_key:
            reference = f"STRIPE-PILOT-{intent.intent_id}".upper()
            return PaymentProviderResult(
                provider=self.name,
                provider_reference=reference,
                status="completed",
                settlement_status="requires_live_provider",
                raw={
                    "mode": "pilot_simulation",
                    "requires": "STRIPE_API_KEY and STRIPE_LIVE_MODE=true for network execution",
                    "amount": str(intent.amount),
                    "currency": intent.currency.upper(),
                },
            )

        try:
            import stripe  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on deploy image
            raise RuntimeError("stripe package is required for live Stripe execution") from exc

        stripe.api_key = self.api_key
        payment_intent = stripe.PaymentIntent.create(
            amount=int(intent.amount * 100),
            currency=intent.currency.lower(),
            idempotency_key=(
                f"novapay:{intent.organization_id}:{intent.intent_id}"
            ),
            metadata={
                "intent_id": intent.intent_id,
                "actor_id": intent.actor_id,
                "organization_id": intent.organization_id,
            },
        )
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=str(payment_intent["id"]),
            status=str(payment_intent["status"]),
            settlement_status="provider_created",
            raw={
                "provider_id": str(payment_intent["id"]),
                "client_secret_available": bool(payment_intent.get("client_secret")),
            },
        )


def provider_for(name: str, *, live: bool = False) -> PayIDProvider | StripeProvider:
    normalized = name.strip().lower()
    if normalized == "stripe":
        return StripeProvider(live=live)
    if normalized in {"payid", "pay_id", "osko"}:
        return PayIDProvider()
    raise ValueError(f"unsupported payment provider: {name}")
