"""Controlled rehearsal provider for NovaPay."""

from __future__ import annotations

import hashlib

from afritech.fintech.payment_provider import (
    PaymentProvider,
    ProviderPaymentRequest,
    ProviderPaymentResult,
)


class ControlledPayIDProvider(PaymentProvider):
    provider_name = "controlled-payid"

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
                "intent_id": request.intent_id,
                "destination": request.destination,
                "amount": str(request.amount),
                "currency": request.currency,
            },
        )
