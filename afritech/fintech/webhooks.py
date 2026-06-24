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
    provider_reference = (
        payload.get("provider_reference")
        or payload.get("transaction_id")
        or payload.get("CheckoutRequestID")
        or payload.get("checkout_request_id")
        or payload.get("reference")
        or ""
    )
    payment_id = (
        payload.get("payment_id")
        or payload.get("merchant_reference")
        or payload.get("AccountReference")
        or payload.get("account_reference")
    )
    status = (
        payload.get("status")
        or payload.get("ResultDesc")
        or payload.get("result_description")
        or "unknown"
    )
    settlement_status = (
        payload.get("settlement_status")
        or payload.get("transaction_status")
        or payload.get("ResultCode")
        or payload.get("result_code")
        or "unknown"
    )
    return PaymentWebhookEvent(
        provider=str(payload.get("provider", "unknown")),
        provider_reference=str(provider_reference),
        payment_id=str(payment_id) if payment_id is not None else None,
        status=str(status),
        settlement_status=_normalize_settlement_status(settlement_status),
        payload=payload,
    )


def _normalize_settlement_status(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"0", "success", "successful", "completed", "paid", "settled"}:
        return "settled"
    if normalized in {"pending", "processing", "submitted", "initiated"}:
        return "processing"
    if normalized in {"reversed", "refunded", "refund"}:
        return "reversed"
    if normalized in {"failed", "failure", "cancelled", "canceled", "declined"}:
        return "failed"
    return normalized or "unknown"
