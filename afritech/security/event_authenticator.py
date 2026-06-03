from __future__ import annotations

import hmac
from typing import Any

from afritech.security.integrity_trace import IntegrityTrace


class EventAuthenticator:
    """Deterministic HMAC-style authenticator for mutation candidates."""

    def generate_signature(self, event: dict[str, Any], secret: str) -> str:
        payload = IntegrityTrace.canonical_json(self._signed_payload(event))
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            "sha256",
        ).hexdigest()

    def verify(self, event: dict[str, Any], signature: str, secret: str) -> bool:
        expected = self.generate_signature(event, secret)
        return hmac.compare_digest(expected, str(signature))

    def _signed_payload(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": event["id"],
            "lineage": tuple(event.get("lineage", ())),
            "payload": event["payload"],
            "timestamp": event["timestamp"],
        }
