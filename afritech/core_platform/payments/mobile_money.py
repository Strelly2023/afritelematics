"""Country-aware mobile-money adapters for NovaPay.

Only Safaricom Daraja exposes a stable public contract used directly here.
Other operators require country-specific commercial onboarding, so their
connectors are configurable partner contracts and fail closed in live mode.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Mapping, Protocol

import httpx

from afritech.core_platform.models import PaymentIntent
from afritech.core_platform.payments.contracts import PaymentProviderResult


COUNTRY_CURRENCIES = {
    "BI": "BIF",
    "CD": "CDF",
    "KE": "KES",
}

COUNTRY_ALIASES = {
    "BDI": "BI",
    "BURUNDI": "BI",
    "COD": "CD",
    "DRC": "CD",
    "DRCONGO": "CD",
    "CONGOKINSHASA": "CD",
    "KEN": "KE",
    "KENYA": "KE",
}


@dataclass(frozen=True)
class MobileMoneyRail:
    provider: str
    country: str
    currency: str
    operator: str
    integration: str
    environment_prefix: str
    live_requires_commercial_approval: bool = True

    def canonical(self) -> dict[str, Any]:
        configured = _credentials_configured(self.environment_prefix)
        live_enabled = _env_bool(f"{self.environment_prefix}_LIVE_MODE")
        return {
            "provider": self.provider,
            "country": self.country,
            "currency": self.currency,
            "operator": self.operator,
            "integration": self.integration,
            "credentials_configured": configured,
            "live_mode_enabled": live_enabled,
            "ready_for_live": configured and live_enabled,
            "commercial_approval_required": self.live_requires_commercial_approval,
        }


MOBILE_MONEY_RAILS = (
    MobileMoneyRail(
        provider="mpesa_ke",
        country="KE",
        currency="KES",
        operator="Safaricom M-PESA",
        integration="daraja_stk_push",
        environment_prefix="NOVAPAY_MPESA_KE",
    ),
    MobileMoneyRail(
        provider="airtel_money_ke",
        country="KE",
        currency="KES",
        operator="Airtel Money Kenya",
        integration="partner_contract",
        environment_prefix="NOVAPAY_AIRTEL_KE",
    ),
    MobileMoneyRail(
        provider="lumicash_bi",
        country="BI",
        currency="BIF",
        operator="Lumicash Burundi",
        integration="partner_contract",
        environment_prefix="NOVAPAY_LUMICASH_BI",
    ),
    MobileMoneyRail(
        provider="ecocash_bi",
        country="BI",
        currency="BIF",
        operator="EcoCash Burundi",
        integration="partner_contract",
        environment_prefix="NOVAPAY_ECOCASH_BI",
    ),
    MobileMoneyRail(
        provider="orange_money_cd",
        country="CD",
        currency="CDF",
        operator="Orange Money RDC",
        integration="orange_money_web_payment",
        environment_prefix="NOVAPAY_ORANGE_CD",
    ),
    MobileMoneyRail(
        provider="airtel_money_cd",
        country="CD",
        currency="CDF",
        operator="Airtel Money RDC",
        integration="partner_contract",
        environment_prefix="NOVAPAY_AIRTEL_CD",
    ),
    MobileMoneyRail(
        provider="mpesa_cd",
        country="CD",
        currency="CDF",
        operator="Vodacom M-PESA RDC",
        integration="partner_contract",
        environment_prefix="NOVAPAY_MPESA_CD",
    ),
)

RAILS_BY_PROVIDER = {rail.provider: rail for rail in MOBILE_MONEY_RAILS}
DEFAULT_PROVIDER_BY_COUNTRY = {
    "BI": "lumicash_bi",
    "CD": "orange_money_cd",
    "KE": "mpesa_ke",
}


class MobileMoneyProvider(Protocol):
    name: str

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        ...


def normalize_country(value: str) -> str:
    normalized = re.sub(r"[^A-Z]", "", value.upper())
    return COUNTRY_ALIASES.get(normalized, normalized)


def normalize_msisdn(value: str) -> str:
    normalized = re.sub(r"[^\d+]", "", value)
    if normalized.startswith("00"):
        normalized = f"+{normalized[2:]}"
    if not normalized.startswith("+"):
        normalized = f"+{normalized}"
    if not re.fullmatch(r"\+[1-9]\d{7,14}", normalized):
        raise ValueError("mobile_money_destination_must_be_e164")
    return normalized


def mobile_money_catalog() -> dict[str, Any]:
    return {
        "rail": "mobile_money",
        "countries": {
            country: {
                "currency": currency,
                "default_provider": DEFAULT_PROVIDER_BY_COUNTRY[country],
                "providers": [
                    rail.canonical()
                    for rail in MOBILE_MONEY_RAILS
                    if rail.country == country
                ],
            }
            for country, currency in COUNTRY_CURRENCIES.items()
        },
        "live_payments_require_operator_contract": True,
        "settlement_source": "authenticated_provider_webhook",
    }


def mobile_money_provider_for(
    name: str,
    *,
    intent: PaymentIntent,
    live: bool,
    transport: httpx.BaseTransport | None = None,
) -> MobileMoneyProvider:
    country = normalize_country(str(intent.metadata.get("country", "")))
    normalized_name = name.strip().lower()
    if normalized_name in {"mobile_money", "mobile-money", "momo"}:
        if country not in DEFAULT_PROVIDER_BY_COUNTRY:
            raise ValueError("supported_mobile_money_country_required")
        normalized_name = DEFAULT_PROVIDER_BY_COUNTRY[country]
    rail = RAILS_BY_PROVIDER.get(normalized_name)
    if rail is None:
        raise ValueError(f"unsupported mobile money provider: {name}")
    if country and country != rail.country:
        raise ValueError("provider_country_mismatch")
    if intent.currency.upper() != rail.currency:
        raise ValueError(
            f"{rail.provider} requires {rail.currency} for domestic collection"
        )
    if rail.provider == "mpesa_ke":
        return MpesaDarajaProvider(rail=rail, live=live, transport=transport)
    return PartnerContractMobileMoneyProvider(
        rail=rail,
        live=live,
        transport=transport,
    )


class _BaseMobileMoneyProvider:
    def __init__(
        self,
        *,
        rail: MobileMoneyRail,
        live: bool,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.rail = rail
        self.name = rail.provider
        self.live = (
            live
            and _env_bool("NOVAPAY_MOBILE_MONEY_LIVE_ENABLED")
            and _env_bool(f"{rail.environment_prefix}_LIVE_MODE")
        )
        self.transport = transport

    def _request(self, intent: PaymentIntent) -> tuple[str, str]:
        msisdn = normalize_msisdn(intent.destination)
        country = normalize_country(str(intent.metadata.get("country", self.rail.country)))
        if country != self.rail.country:
            raise ValueError("provider_country_mismatch")
        if self.live and not str(
            intent.metadata.get("commercial_approval_reference", "")
        ).strip():
            raise PermissionError("mobile_money_commercial_approval_required")
        return msisdn, country

    def _simulation(self, intent: PaymentIntent, msisdn: str) -> PaymentProviderResult:
        digest = hashlib.sha256(
            f"{self.name}:{intent.organization_id}:{intent.intent_id}".encode()
        ).hexdigest()[:20].upper()
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=f"{self.name.upper()}-{digest}",
            status="pending",
            settlement_status="pending_user_authorization",
            raw={
                "mode": "controlled_mobile_money_pilot",
                "country": self.rail.country,
                "currency": self.rail.currency,
                "operator": self.rail.operator,
                "msisdn_masked": _mask_msisdn(msisdn),
                "live_network_called": False,
                "commercial_approval_required": True,
            },
        )


class MpesaDarajaProvider(_BaseMobileMoneyProvider):
    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        msisdn, _ = self._request(intent)
        if not self.live:
            return self._simulation(intent, msisdn)

        prefix = self.rail.environment_prefix
        consumer_key = os.environ.get(f"{prefix}_CONSUMER_KEY", "")
        consumer_secret = os.environ.get(f"{prefix}_CONSUMER_SECRET", "")
        short_code = os.environ.get(f"{prefix}_SHORT_CODE", "")
        passkey = os.environ.get(f"{prefix}_PASSKEY", "")
        callback_url = os.environ.get(f"{prefix}_CALLBACK_URL", "")
        if not all((consumer_key, consumer_secret, short_code, passkey, callback_url)):
            raise RuntimeError("mpesa_ke_live_credentials_incomplete")

        base_url = os.environ.get(
            f"{prefix}_API_BASE_URL",
            "https://api.safaricom.co.ke",
        ).rstrip("/")
        basic = base64.b64encode(
            f"{consumer_key}:{consumer_secret}".encode("utf-8")
        ).decode("ascii")
        with httpx.Client(timeout=20.0, transport=self.transport) as client:
            token_response = client.get(
                f"{base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {basic}"},
            )
            token_response.raise_for_status()
            token = str(token_response.json().get("access_token", ""))
            if not token:
                raise RuntimeError("mpesa_ke_access_token_missing")

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            password = base64.b64encode(
                f"{short_code}{passkey}{timestamp}".encode("utf-8")
            ).decode("ascii")
            response = client.post(
                f"{base_url}/mpesa/stkpush/v1/processrequest",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": (
                        f"novapay:{intent.organization_id}:{intent.intent_id}"
                    ),
                },
                json={
                    "BusinessShortCode": short_code,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": os.environ.get(
                        f"{prefix}_TRANSACTION_TYPE",
                        "CustomerPayBillOnline",
                    ),
                    "Amount": int(intent.amount),
                    "PartyA": msisdn.lstrip("+"),
                    "PartyB": short_code,
                    "PhoneNumber": msisdn.lstrip("+"),
                    "CallBackURL": callback_url,
                    "AccountReference": intent.intent_id[:12],
                    "TransactionDesc": str(
                        intent.metadata.get("description", "NovaPay payment")
                    )[:20],
                },
            )
        response.raise_for_status()
        raw = response.json()
        reference = str(
            raw.get("CheckoutRequestID")
            or raw.get("MerchantRequestID")
            or intent.intent_id
        )
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=reference,
            status="pending",
            settlement_status="pending_user_authorization",
            raw={
                "mode": "live",
                "country": self.rail.country,
                "operator": self.rail.operator,
                "response_code": str(raw.get("ResponseCode", "")),
                "response_description": str(raw.get("ResponseDescription", "")),
            },
        )


class PartnerContractMobileMoneyProvider(_BaseMobileMoneyProvider):
    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        msisdn, _ = self._request(intent)
        if not self.live:
            return self._simulation(intent, msisdn)

        prefix = self.rail.environment_prefix
        api_url = os.environ.get(f"{prefix}_COLLECTION_URL", "")
        api_token = os.environ.get(f"{prefix}_API_TOKEN", "")
        merchant_id = os.environ.get(f"{prefix}_MERCHANT_ID", "")
        callback_url = os.environ.get(f"{prefix}_CALLBACK_URL", "")
        if not all((api_url, api_token, merchant_id, callback_url)):
            raise RuntimeError(f"{self.name}_live_partner_contract_incomplete")

        payload = {
            "amount": str(intent.amount),
            "currency": intent.currency.upper(),
            "customer_msisdn": msisdn,
            "merchant_id": merchant_id,
            "merchant_reference": intent.intent_id,
            "callback_url": callback_url,
            "metadata": {
                "organization_id": intent.organization_id,
                "actor_id": intent.actor_id,
            },
        }
        extra = os.environ.get(f"{prefix}_REQUEST_TEMPLATE_JSON")
        if extra:
            configured = json.loads(extra)
            if not isinstance(configured, Mapping):
                raise RuntimeError(f"{self.name}_request_template_must_be_object")
            payload.update(configured)

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
        reference_field = os.environ.get(
            f"{prefix}_REFERENCE_FIELD",
            "transaction_id",
        )
        reference = str(raw.get(reference_field) or intent.intent_id)
        return PaymentProviderResult(
            provider=self.name,
            provider_reference=reference,
            status="pending",
            settlement_status="pending_provider_confirmation",
            raw={
                "mode": "live_partner_contract",
                "country": self.rail.country,
                "operator": self.rail.operator,
                "provider_status": str(raw.get("status", "submitted")),
            },
        )


def _credentials_configured(prefix: str) -> bool:
    if prefix == "NOVAPAY_MPESA_KE":
        keys = (
            "CONSUMER_KEY",
            "CONSUMER_SECRET",
            "SHORT_CODE",
            "PASSKEY",
            "CALLBACK_URL",
        )
    else:
        keys = ("COLLECTION_URL", "API_TOKEN", "MERCHANT_ID", "CALLBACK_URL")
    return all(os.environ.get(f"{prefix}_{key}") for key in keys)


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}


def _mask_msisdn(msisdn: str) -> str:
    return f"{msisdn[:4]}{'*' * max(4, len(msisdn) - 7)}{msisdn[-3:]}"


__all__ = [
    "COUNTRY_CURRENCIES",
    "DEFAULT_PROVIDER_BY_COUNTRY",
    "MOBILE_MONEY_RAILS",
    "MobileMoneyRail",
    "mobile_money_catalog",
    "mobile_money_provider_for",
    "normalize_country",
    "normalize_msisdn",
]
