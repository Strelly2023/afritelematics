"""Authentication and replay protection for payment provider webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class VerifiedWebhook:
    event_id: str
    provider: str
    timestamp: int
    payload: Mapping[str, Any]


def canonical_webhook_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def sign_webhook(payload: Mapping[str, Any], *, timestamp: int, secret: str) -> str:
    message = str(timestamp).encode("ascii") + b"." + canonical_webhook_bytes(payload)
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_webhook(
    payload: Mapping[str, Any],
    *,
    timestamp: str,
    signature: str,
    secret: str,
    now: int | None = None,
    tolerance_seconds: int = 300,
) -> VerifiedWebhook:
    if not secret:
        raise ValueError("webhook_secret_not_configured")
    try:
        parsed_timestamp = int(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_webhook_timestamp") from exc

    current = int(time.time()) if now is None else now
    if abs(current - parsed_timestamp) > tolerance_seconds:
        raise ValueError("webhook_timestamp_outside_tolerance")

    expected = sign_webhook(payload, timestamp=parsed_timestamp, secret=secret)
    if not hmac.compare_digest(expected, signature):
        raise ValueError("invalid_webhook_signature")

    provider = str(payload.get("provider", "")).strip()
    event_id = str(payload.get("event_id", "")).strip()
    if not provider:
        raise ValueError("provider_required")
    if not event_id:
        raise ValueError("event_id_required")
    return VerifiedWebhook(
        event_id=event_id,
        provider=provider,
        timestamp=parsed_timestamp,
        payload=dict(payload),
    )


__all__ = [
    "VerifiedWebhook",
    "canonical_webhook_bytes",
    "sign_webhook",
    "verify_webhook",
]
