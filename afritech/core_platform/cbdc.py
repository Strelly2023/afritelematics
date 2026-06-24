"""Optional CBDC adapter surface for future NovaPay settlement rails."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

import httpx

from afritech.core_platform.models import PaymentIntent
from afritech.core_platform.payments.contracts import (
    PaymentProviderAdapter,
    PaymentProviderResult,
)


@dataclass(frozen=True)
class CBDCRail:
    provider: str
    network: str
    currency: str
    environment_prefix: str = "NOVAPAY_CBDC"

    def canonical(self) -> dict[str, Any]:
        live_enabled = _env_bool(f"{self.environment_prefix}_LIVE_ENABLED")
        api_url = os.environ.get(f"{self.environment_prefix}_API_URL", "")
        api_token = os.environ.get(f"{self.environment_prefix}_API_TOKEN", "")
        merchant_id = os.environ.get(f"{self.environment_prefix}_MERCHANT_ID", "")
        callback_url = os.environ.get(f"{self.environment_prefix}_CALLBACK_URL", "")
        return {
            "provider": self.provider,
            "network": self.network,
            "currency": self.currency,
            "live_mode_enabled": live_enabled,
            "configured": bool(api_url and api_token and merchant_id and callback_url),
            "ready_for_live": live_enabled
            and bool(api_url and api_token and merchant_id and callback_url),
        }


class CBDCProvider:
    name = "cbdc"

    def __init__(
        self,
        *,
        live: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.live = live and _env_bool("NOVAPAY_CBDC_LIVE_ENABLED")
        self.transport = transport

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        reference = f"CBDC-{hashlib.sha256(intent.intent_id.encode()).hexdigest()[:20].upper()}"
        if not self.live:
            return PaymentProviderResult(
                provider=self.name,
                provider_reference=reference,
                status="completed",
                settlement_status="provider_created",
                raw={
                    "mode": "controlled_cbdc_pilot",
                    "network": os.environ.get("NOVAPAY_CBDC_NETWORK", "pilot-ledger"),
                    "currency": intent.currency.upper(),
                },
            )

        api_url = os.environ.get("NOVAPAY_CBDC_API_URL", "").rstrip("/")
        api_token = os.environ.get("NOVAPAY_CBDC_API_TOKEN", "")
        merchant_id = os.environ.get("NOVAPAY_CBDC_MERCHANT_ID", "")
        callback_url = os.environ.get("NOVAPAY_CBDC_CALLBACK_URL", "")
        if not all((api_url, api_token, merchant_id, callback_url)):
            raise RuntimeError("cbdc_live_configuration_incomplete")

        payload: dict[str, Any] = {
            "amount": str(intent.amount),
            "currency": intent.currency.upper(),
            "merchant_id": merchant_id,
            "merchant_reference": intent.intent_id,
            "callback_url": callback_url,
            "metadata": {
                "organization_id": intent.organization_id,
                "actor_id": intent.actor_id,
            },
        }
        with httpx.Client(timeout=20.0, transport=self.transport) as client:
            response = client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": (
                        f"novapay:{intent.organization_id}:{intent.intent_id}"
                    ),
                },
                json=payload,
            )
        response.raise_for_status()
        raw = response.json()
        provider_reference = str(raw.get("transaction_id") or raw.get("reference") or reference)
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=provider_reference,
            status=str(raw.get("status", "pending")),
            settlement_status=str(raw.get("settlement_status", "pending_provider_confirmation")),
            raw={
                "mode": "live_cbdc_gateway",
                "network": str(raw.get("network", os.environ.get("NOVAPAY_CBDC_NETWORK", "unknown"))),
                "currency": intent.currency.upper(),
            },
        )


def cbdc_status() -> dict[str, Any]:
    live_enabled = _env_bool("NOVAPAY_CBDC_LIVE_ENABLED")
    api_url = os.environ.get("NOVAPAY_CBDC_API_URL", "")
    api_token = os.environ.get("NOVAPAY_CBDC_API_TOKEN", "")
    merchant_id = os.environ.get("NOVAPAY_CBDC_MERCHANT_ID", "")
    callback_url = os.environ.get("NOVAPAY_CBDC_CALLBACK_URL", "")
    configured = bool(api_url and api_token and merchant_id and callback_url)
    return {
        "available": True,
        "mode": "live_gateway" if live_enabled and configured else "controlled_pilot",
        "live_mode_enabled": live_enabled,
        "configured": configured,
        "ready_for_real_charge": live_enabled and configured,
        "network": os.environ.get("NOVAPAY_CBDC_NETWORK", "pilot-ledger"),
    }


def cbdc_provider_for(*, live: bool = False) -> PaymentProviderAdapter:
    return CBDCProvider(live=live)


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}

