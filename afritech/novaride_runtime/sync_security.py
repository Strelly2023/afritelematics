"""Signed mobile synchronization validation."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(slots=True)
class DeviceRegistry:
    device_secrets: dict[str, str]
    used_nonces: set[str] = field(default_factory=set)
    max_clock_skew_seconds: int = 300

    def validate(
        self,
        *,
        device_id: str,
        tenant_id: str,
        timestamp: str,
        nonce: str,
        signature: str,
        payload: dict[str, Any],
    ) -> None:
        secret = self.device_secrets.get(device_id)
        if secret is None:
            raise ValueError("unknown_device")
        try:
            timestamp_value = int(timestamp)
        except ValueError as exc:
            raise ValueError("invalid_timestamp") from exc
        if abs(int(time()) - timestamp_value) > self.max_clock_skew_seconds:
            raise ValueError("stale_signature")
        nonce_key = f"{tenant_id}:{device_id}:{nonce}"
        if nonce_key in self.used_nonces:
            raise ValueError("reused_nonce")
        expected = sign_sync_payload(
            secret=secret, timestamp=timestamp, nonce=nonce, payload=payload
        )
        if not hmac.compare_digest(expected, signature):
            raise ValueError("invalid_signature")
        self.used_nonces.add(nonce_key)


def sign_sync_payload(*, secret: str, timestamp: str, nonce: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    message = f"{timestamp}.{nonce}.{encoded}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
