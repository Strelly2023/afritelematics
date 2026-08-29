"""Out-of-band OTP delivery boundary for NovaID authentication."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Protocol
from urllib import error, request


class OTPDeliveryError(RuntimeError):
    """Raised when an OTP cannot be handed to the configured provider."""


@dataclass(frozen=True, slots=True)
class OTPDelivery:
    tenant_id: str
    destination: str
    purpose: str
    challenge_id: str
    code: str
    correlation_id: str


class OTPDeliveryProvider(Protocol):
    def deliver(self, delivery: OTPDelivery) -> None: ...


class HTTPSOTPDeliveryProvider:
    """Minimal provider adapter; credentials and codes are never logged."""

    def __init__(self, endpoint: str, api_key: str, *, timeout_seconds: float = 5.0) -> None:
        if not endpoint.startswith("https://"):
            raise ValueError("novaid_otp_provider_requires_https")
        if not api_key.strip():
            raise ValueError("missing_novaid_otp_provider_api_key")
        if timeout_seconds <= 0:
            raise ValueError("invalid_novaid_otp_provider_timeout")
        self.endpoint = endpoint
        self._api_key = api_key
        self.timeout_seconds = timeout_seconds

    def deliver(self, delivery: OTPDelivery) -> None:
        body = json.dumps(
            {
                "tenant_id": delivery.tenant_id,
                "destination": delivery.destination,
                "purpose": delivery.purpose,
                "challenge_id": delivery.challenge_id,
                "code": delivery.code,
                "correlation_id": delivery.correlation_id,
            }
        ).encode("utf-8")
        provider_request = request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(provider_request, timeout=self.timeout_seconds) as response:
                if not 200 <= response.status < 300:
                    raise OTPDeliveryError("novaid_otp_delivery_rejected")
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise OTPDeliveryError("novaid_otp_delivery_unavailable") from exc


__all__ = [
    "HTTPSOTPDeliveryProvider",
    "OTPDelivery",
    "OTPDeliveryError",
    "OTPDeliveryProvider",
]
