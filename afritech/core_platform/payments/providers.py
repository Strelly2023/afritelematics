"""Provider adapters for NovaPay core platform payments.

The adapters expose production-shaped integration boundaries. PayID is
deterministic for local pilot use. Stripe can call the Stripe SDK when an API
key is supplied, while remaining safe in unconfigured test environments.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from afritech.core_platform.models import PaymentIntent
from afritech.core_platform.cbdc import CBDCProvider
from afritech.core_platform.payments.contracts import (
    PaymentProviderAdapter,
    PaymentProviderResult,
)


class PayIDProvider:
    name = "payid"

    def __init__(
        self,
        *,
        live: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.live = live and _env_bool("NOVAPAY_PAYID_LIVE_ENABLED")
        self.transport = transport

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        if not self.live:
            reference = f"PAYID-{intent.organization_id}-{intent.intent_id}".upper()
            return PaymentProviderResult(
                provider=self.name,
                provider_reference=reference,
                status="completed",
                settlement_status="settlement_pending",
                raw={
                    "rail": "payid",
                    "mode": "controlled_pilot",
                    "destination": intent.destination,
                    "amount": str(intent.amount),
                    "currency": intent.currency.upper(),
                },
            )

        collection_url = os.environ.get("NOVAPAY_PAYID_COLLECTION_URL", "").rstrip("/")
        api_token = os.environ.get("NOVAPAY_PAYID_API_TOKEN", "")
        merchant_id = os.environ.get("NOVAPAY_PAYID_MERCHANT_ID", "")
        callback_url = os.environ.get("NOVAPAY_PAYID_CALLBACK_URL", "")
        if not all((collection_url, api_token, merchant_id, callback_url)):
            raise RuntimeError("payid_live_configuration_incomplete")

        payload: dict[str, Any] = {
            "amount": str(intent.amount),
            "currency": intent.currency.upper(),
            "payid": intent.destination,
            "merchant_id": merchant_id,
            "merchant_reference": intent.intent_id,
            "callback_url": callback_url,
            "metadata": {
                "organization_id": intent.organization_id,
                "actor_id": intent.actor_id,
            },
        }
        extra = os.environ.get("NOVAPAY_PAYID_REQUEST_TEMPLATE_JSON")
        if extra:
            import json

            configured = json.loads(extra)
            if not isinstance(configured, dict):
                raise RuntimeError("payid_request_template_must_be_object")
            payload.update(configured)

        with httpx.Client(timeout=20.0, transport=self.transport) as client:
            response = client.post(
                collection_url,
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
        reference_field = os.environ.get(
            "NOVAPAY_PAYID_REFERENCE_FIELD",
            "transaction_id",
        )
        reference = str(raw.get(reference_field) or intent.intent_id)
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=reference,
            status=str(raw.get("status", "pending")),
            settlement_status=str(
                raw.get("settlement_status", "pending_provider_confirmation")
            ),
            raw={
                "mode": "live_gateway",
                "provider_status": str(raw.get("status", "submitted")),
                "currency": intent.currency.upper(),
                "merchant_id": merchant_id,
            },
        )


class StripeProvider:
    name = "stripe"

    def __init__(self, api_key: str | None = None, *, live: bool = False) -> None:
        self.api_key = api_key or os.environ.get("STRIPE_API_KEY")
        self.live = live or os.environ.get("STRIPE_LIVE_MODE", "").lower() in {"1", "true", "yes"}

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        if not self.live or not self.api_key:
            reference = f"STRIPE-PILOT-{intent.intent_id}".upper()
            return PaymentProviderResult(
                provider=self.name,
                provider_reference=reference,
                status="completed",
                settlement_status="requires_live_provider",
                raw={
                    "mode": "pilot_simulation",
                    "requires": "STRIPE_API_KEY and STRIPE_LIVE_MODE=true for network execution",
                    "amount": str(intent.amount),
                    "currency": intent.currency.upper(),
                },
            )

        try:
            import stripe  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on deploy image
            raise RuntimeError("stripe package is required for live Stripe execution") from exc

        stripe.api_key = self.api_key
        payment_intent = stripe.PaymentIntent.create(
            amount=int(intent.amount * 100),
            currency=intent.currency.lower(),
            idempotency_key=(
                f"novapay:{intent.organization_id}:{intent.intent_id}"
            ),
            metadata={
                "intent_id": intent.intent_id,
                "actor_id": intent.actor_id,
                "organization_id": intent.organization_id,
            },
        )
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=str(payment_intent["id"]),
            status=str(payment_intent["status"]),
            settlement_status="provider_created",
            raw={
                "provider_id": str(payment_intent["id"]),
                "client_secret_available": bool(payment_intent.get("client_secret")),
            },
        )


class MfsAfricaProvider:
    name = "mfs_africa"

    def __init__(
        self,
        *,
        live: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.live = live and _env_bool("MFS_AFRICA_LIVE_MODE")
        self.transport = transport

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        if not self.live:
            reference = f"MFS-PILOT-{intent.organization_id}-{intent.intent_id}".upper()
            return PaymentProviderResult(
                provider=self.name,
                provider_reference=reference,
                status="pending",
                settlement_status="requires_live_provider",
                raw={
                    "mode": "controlled_partner_pilot",
                    "network": "MFS Africa / Onafriq",
                    "live_network_called": False,
                    "destination": intent.destination,
                    "amount": str(intent.amount),
                    "currency": intent.currency.upper(),
                },
            )

        base_url = os.environ.get("MFS_AFRICA_API_BASE_URL", "").rstrip("/")
        token_url = os.environ.get("MFS_AFRICA_TOKEN_URL", "")
        transfer_path = os.environ.get("MFS_AFRICA_TRANSFER_PATH", "/v1/transfers")
        client_id = os.environ.get("MFS_AFRICA_CLIENT_ID", "")
        client_secret = os.environ.get("MFS_AFRICA_CLIENT_SECRET", "")
        approval_reference = os.environ.get("MFS_AFRICA_COMMERCIAL_APPROVAL_REFERENCE", "")
        callback_url = os.environ.get("MFS_AFRICA_CALLBACK_URL", "")
        if not all((base_url, token_url, client_id, client_secret, approval_reference, callback_url)):
            raise RuntimeError("mfs_africa_live_configuration_incomplete")
        if not str(intent.metadata.get("commercial_approval_reference") or approval_reference).strip():
            raise PermissionError("mfs_africa_commercial_approval_required")

        token_payload: dict[str, Any] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": os.environ.get("MFS_AFRICA_GRANT_TYPE", "client_credentials"),
        }
        with httpx.Client(timeout=20.0, transport=self.transport) as client:
            token_response = client.post(
                token_url,
                headers={"Content-Type": "application/json"},
                json=token_payload,
            )
            token_response.raise_for_status()
            token = str(token_response.json().get("access_token", ""))
            if not token:
                raise RuntimeError("mfs_africa_access_token_missing")

            payload = {
                "reference": intent.intent_id,
                "amount": str(intent.amount),
                "currency": intent.currency.upper(),
                "destination": intent.destination,
                "callback_url": callback_url,
                "metadata": {
                    "organization_id": intent.organization_id,
                    "actor_id": intent.actor_id,
                    "commercial_approval_reference": approval_reference,
                },
            }
            extra = os.environ.get("MFS_AFRICA_REQUEST_TEMPLATE_JSON")
            if extra:
                import json

                configured = json.loads(extra)
                if not isinstance(configured, dict):
                    raise RuntimeError("mfs_africa_request_template_must_be_object")
                payload.update(configured)
            response = client.post(
                f"{base_url}{transfer_path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": (
                        f"novapay:{intent.organization_id}:{intent.intent_id}"
                    ),
                },
                json=payload,
            )
        response.raise_for_status()
        raw = response.json()
        data = raw.get("data", {}) if isinstance(raw.get("data"), dict) else {}
        reference_field = os.environ.get("MFS_AFRICA_REFERENCE_FIELD", "transaction_id")
        reference = str(data.get(reference_field) or raw.get(reference_field) or intent.intent_id)
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=reference,
            status=str(data.get("status") or raw.get("status") or "submitted"),
            settlement_status=str(
                data.get("settlement_status")
                or raw.get("settlement_status")
                or "pending_provider_confirmation"
            ),
            raw={
                "mode": "live_partner_gateway",
                "network": "MFS Africa / Onafriq",
                "provider_status": str(data.get("status") or raw.get("status") or "submitted"),
            },
        )


def provider_for(
    name: str,
    *,
    live: bool = False,
    intent: PaymentIntent | None = None,
) -> PaymentProviderAdapter:
    normalized = name.strip().lower()
    if normalized == "stripe":
        return StripeProvider(live=live)
    if normalized in {"payid", "pay_id", "osko"}:
        return PayIDProvider(live=live)
    if normalized in {"cbdc", "central_bank_digital_currency", "digital_cash"}:
        return CBDCProvider(live=live)
    if normalized in {"mfs", "mfs_africa", "onafriq"}:
        return MfsAfricaProvider(live=live)
    if normalized in {
        "mobile_money",
        "mobile-money",
        "momo",
        "mpesa_ke",
        "airtel_money_ke",
        "lumicash_bi",
        "ecocash_bi",
        "orange_money_cd",
        "airtel_money_cd",
        "mpesa_cd",
    }:
        if intent is None:
            raise ValueError("payment intent required for mobile money provider")
        from afritech.core_platform.payments.mobile_money import (
            mobile_money_provider_for,
        )

        return mobile_money_provider_for(normalized, intent=intent, live=live)
    raise ValueError(f"unsupported payment provider: {name}")


def payid_status() -> dict[str, Any]:
    live_enabled = _env_bool("NOVAPAY_PAYID_LIVE_ENABLED")
    collection_url = os.environ.get("NOVAPAY_PAYID_COLLECTION_URL", "")
    api_token = os.environ.get("NOVAPAY_PAYID_API_TOKEN", "")
    merchant_id = os.environ.get("NOVAPAY_PAYID_MERCHANT_ID", "")
    callback_url = os.environ.get("NOVAPAY_PAYID_CALLBACK_URL", "")
    configured = bool(collection_url and api_token and merchant_id and callback_url)
    return {
        "available": True,
        "mode": "live_gateway" if live_enabled and configured else "controlled_pilot",
        "live_mode_enabled": live_enabled,
        "configured": configured,
        "ready_for_real_charge": live_enabled and configured,
        "merchant_id_configured": bool(merchant_id),
        "callback_url_configured": bool(callback_url),
    }


def mfs_africa_status() -> dict[str, Any]:
    live_enabled = _env_bool("MFS_AFRICA_LIVE_MODE")
    configured = all(
        os.environ.get(name)
        for name in (
            "MFS_AFRICA_API_BASE_URL",
            "MFS_AFRICA_TOKEN_URL",
            "MFS_AFRICA_CLIENT_ID",
            "MFS_AFRICA_CLIENT_SECRET",
            "MFS_AFRICA_CALLBACK_URL",
            "MFS_AFRICA_COMMERCIAL_APPROVAL_REFERENCE",
        )
    )
    return {
        "available": True,
        "provider": "mfs_africa",
        "network": "MFS Africa / Onafriq",
        "mode": "live_partner_gateway" if live_enabled and configured else "controlled_partner_pilot",
        "live_mode_enabled": live_enabled,
        "configured": configured,
        "ready_for_real_transaction": live_enabled and configured,
        "api_base_url_configured": bool(os.environ.get("MFS_AFRICA_API_BASE_URL")),
        "token_url_configured": bool(os.environ.get("MFS_AFRICA_TOKEN_URL")),
        "callback_url_configured": bool(os.environ.get("MFS_AFRICA_CALLBACK_URL")),
        "commercial_approval_configured": bool(
            os.environ.get("MFS_AFRICA_COMMERCIAL_APPROVAL_REFERENCE")
        ),
    }


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}
