"""Payment webhook handling contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PaymentWebhookEvent:
    provider: str
    provider_reference: str
    payment_id: str | None
    status: str
    settlement_status: str
    payload: dict[str, Any]


def normalize_payment_webhook(payload: dict[str, Any]) -> PaymentWebhookEvent:
    return PaymentWebhookEvent(
        provider=str(payload.get("provider", "unknown")),
        provider_reference=str(payload.get("provider_reference", "")),
        payment_id=payload.get("payment_id"),
        status=str(payload.get("status", "unknown")),
        settlement_status=str(payload.get("settlement_status", "unknown")),
        payload=payload,
    )
