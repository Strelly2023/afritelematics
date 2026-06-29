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
    # Providers commonly wrap the useful callback fields in ``data`` or, for
    # M-Pesa-compatible callbacks, ``Body.stkCallback``. Flatten only these
    # transport envelopes and retain the untouched payload as evidence.
    data = payload.get("data")
    body = payload.get("Body")
    stk_callback = body.get("stkCallback") if isinstance(body, dict) else None
    normalized_payload: dict[str, Any] = dict(payload)
    if isinstance(data, dict):
        normalized_payload.update(data)
    if isinstance(stk_callback, dict):
        normalized_payload.update(stk_callback)

    provider_reference = (
        normalized_payload.get("provider_reference")
        or normalized_payload.get("transaction_id")
        or normalized_payload.get("CheckoutRequestID")
        or normalized_payload.get("checkout_request_id")
        or normalized_payload.get("reference")
        or ""
    )
    payment_id = (
        normalized_payload.get("payment_id")
        or normalized_payload.get("merchant_reference")
        or normalized_payload.get("AccountReference")
        or normalized_payload.get("account_reference")
    )
    status = (
        normalized_payload.get("status")
        or normalized_payload.get("ResultDesc")
        or normalized_payload.get("result_description")
        or "unknown"
    )
    settlement_status = _first_present(
        normalized_payload,
        "settlement_status",
        "transaction_status",
        "ResultCode",
        "result_code",
        default="unknown",
    )
    provider = str(payload.get("provider", "unknown")).strip().lower()
    if provider in {"controlled-payid", "pay_id", "osko"}:
        provider = "payid"
    return PaymentWebhookEvent(
        provider=provider,
        provider_reference=str(provider_reference),
        payment_id=str(payment_id) if payment_id is not None else None,
        status=str(status),
        settlement_status=_normalize_settlement_status(settlement_status),
        payload=payload,
    )


def _first_present(
    payload: dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != "":
            return value
    return default


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
