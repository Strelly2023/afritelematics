"""Controlled rehearsal provider for NovaPay."""

from __future__ import annotations

import hashlib

from afritech.fintech.payment_provider import (
    PaymentProvider,
    ProviderPaymentRequest,
    ProviderPaymentResult,
)


class ControlledPayIDProvider(PaymentProvider):
    # Keep the rail identity stable across rehearsal and live execution. The
    # execution mode belongs in evidence, not in the provider identifier.
    provider_name = "payid"

    def execute_payment(self, request: ProviderPaymentRequest) -> ProviderPaymentResult:
        ref = "PAYID-" + hashlib.sha256(
            f"{request.organization_id}:{request.intent_id}".encode()
        ).hexdigest()[:18].upper()

        return ProviderPaymentResult(
            provider=self.provider_name,
            provider_reference=ref,
            status="completed",
            settlement_status="settlement_pending",
            raw={
                "mode": "controlled_rehearsal",
                "rail": "payid",
                "live_network_called": False,
                "intent_id": request.intent_id,
                "destination": request.destination,
                "amount": str(request.amount),
                "currency": request.currency,
                "metadata": dict(request.metadata),
            },
        )
