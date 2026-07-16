"""Webhook runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from typing import Any


@dataclass(frozen=True, slots=True)
class WebhookRuntimeResult:
    accepted: bool
    reason: str = ""
    metadata: dict[str, Any] | None = None


def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
