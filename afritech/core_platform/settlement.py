"""Settlement routing and FX normalization for NovaPay.

The settlement planner is deterministic. It chooses a rail, normalizes the
currency, and records the corridor that will be used for execution. Provider
adapters still own external execution; this module only prepares the route and
the normalized intent that downstream payment providers consume.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
import hashlib
import os
import re
from typing import Any, Mapping

from afritech.afripay.fx import FXEngine, default_fx_engine
from afritech.afripay.money import Money
from afritech.core_platform.models import PaymentIntent
from afritech.core_platform.payments.mobile_money import (
    COUNTRY_CURRENCIES,
    DEFAULT_PROVIDER_BY_COUNTRY,
    normalize_country,
    normalize_msisdn,
)


COUNTRY_CURRENCY_BY_REGION = {
    "AU": "AUD",
    "BI": "BIF",
    "CD": "CDF",
    "KE": "KES",
    "US": "USD",
}

DOMESTIC_RAIL_BY_CURRENCY = {
    "AUD": "payid",
    "USD": "stripe",
    "KES": "mobile_money",
    "BIF": "mobile_money",
    "CDF": "mobile_money",
}


@dataclass(frozen=True)
class SettlementPlan:
    route_id: str
    route_class: str
    corridor: str
    source_country: str
    settlement_country: str
    source_currency: str
    settlement_currency: str
    source_amount: str
    settlement_amount: str
    provider: str
    rail: str
    route_hint: str
    fx_provider: str | None
    fx_reference: str | None
    fx_rate: str | None
    fx_locked: bool
    metadata: Mapping[str, Any]

    def canonical(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "route_class": self.route_class,
            "corridor": self.corridor,
            "source_country": self.source_country,
            "settlement_country": self.settlement_country,
            "source_currency": self.source_currency,
            "settlement_currency": self.settlement_currency,
            "source_amount": self.source_amount,
            "settlement_amount": self.settlement_amount,
            "provider": self.provider,
            "rail": self.rail,
            "route_hint": self.route_hint,
            "fx_provider": self.fx_provider,
            "fx_reference": self.fx_reference,
            "fx_rate": self.fx_rate,
            "fx_locked": self.fx_locked,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SettlementResult:
    plan: SettlementPlan
    intent: PaymentIntent

    def canonical(self) -> dict[str, Any]:
        return {"plan": self.plan.canonical(), "intent": self.intent.canonical()}


@dataclass(frozen=True)
class SettlementRolloutConfig:
    mode: str
    primary_corridor: str
    corridors: tuple[str, ...]
    settlement_mode: str
    mobile_money_live_enabled: bool
    compliance_provider: str
    compliance_live_enabled: bool

    def canonical(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "primary_corridor": self.primary_corridor,
            "corridors": list(self.corridors),
            "settlement_mode": self.settlement_mode,
            "mobile_money_live_enabled": self.mobile_money_live_enabled,
            "compliance_provider": self.compliance_provider,
            "compliance_live_enabled": self.compliance_live_enabled,
        }


def normalize_currency_code(value: str) -> str:
    normalized = re.sub(r"[^A-Z]", "", value.upper())
    if normalized in COUNTRY_CURRENCY_BY_REGION:
        return COUNTRY_CURRENCY_BY_REGION[normalized]
    return normalized


class SettlementRouter:
    def __init__(self, *, fx_engine: FXEngine | None = None) -> None:
        self.fx_engine = fx_engine or default_fx_engine()

    def plan(
        self,
        intent: PaymentIntent,
        *,
        provider: str,
        live_provider: bool = False,
    ) -> SettlementResult:
        source_currency = normalize_currency_code(intent.currency)
        source_country = _infer_country(intent, source_currency)
        settlement_country = _infer_settlement_country(intent, provider, source_country)
        settlement_currency = _infer_settlement_currency(
            intent,
            provider,
            settlement_country,
            source_currency,
        )
        route_hint = _infer_route_hint(provider, settlement_country, settlement_currency)
        route_class = (
            "domestic"
            if source_currency == settlement_currency and source_country == settlement_country
            else "cross_border"
        )
        corridor = f"{source_country or 'GLOBAL'}->{settlement_country or 'GLOBAL'}:{source_currency}->{settlement_currency}"
        settlement_amount = intent.amount
        fx_provider = None
        fx_reference = None
        fx_rate = None
        fx_locked = False
        if source_currency != settlement_currency:
            conversion = self.fx_engine.convert(
                transaction_id=intent.intent_id,
                amount=Money.of(intent.amount, source_currency),
                to_currency=settlement_currency,
            )
            settlement_amount = conversion.amount_out.amount
            fx_provider = conversion.rate.provider
            fx_reference = conversion.rate.locked_reference
            fx_rate = format(conversion.rate.rate, ".8f")
            fx_locked = True
        route_id = _route_id(
            intent.intent_id,
            provider,
            source_country,
            settlement_country,
            source_currency,
            settlement_currency,
            settlement_amount,
        )
        metadata: dict[str, Any] = dict(intent.metadata)
        metadata.update(
            {
                "route_id": route_id,
                "route_class": route_class,
                "corridor": corridor,
                "source_country": source_country,
                "settlement_country": settlement_country,
                "source_currency": source_currency,
                "settlement_currency": settlement_currency,
                "source_amount": format(intent.amount, ".2f"),
                "settlement_amount": format(settlement_amount, ".2f"),
                "route_hint": route_hint,
                "fx_provider": fx_provider,
                "fx_reference": fx_reference,
                "fx_rate": fx_rate,
                "fx_locked": fx_locked,
                "live_provider_requested": live_provider,
            }
        )
        if settlement_country and "country" not in metadata:
            metadata["country"] = settlement_country
        if settlement_country and not metadata.get("settlement_country"):
            metadata["settlement_country"] = settlement_country
        if settlement_currency and not metadata.get("settlement_currency"):
            metadata["settlement_currency"] = settlement_currency
        normalized_intent = replace(
            intent,
            amount=settlement_amount,
            currency=settlement_currency,
            metadata=metadata,
        )
        return SettlementResult(
            plan=SettlementPlan(
                route_id=route_id,
                route_class=route_class,
                corridor=corridor,
                source_country=source_country,
                settlement_country=settlement_country,
                source_currency=source_currency,
                settlement_currency=settlement_currency,
                source_amount=format(intent.amount, ".2f"),
                settlement_amount=format(settlement_amount, ".2f"),
                provider=route_hint,
                rail=route_hint,
                route_hint=route_hint,
                fx_provider=fx_provider,
                fx_reference=fx_reference,
                fx_rate=fx_rate,
                fx_locked=fx_locked,
                metadata=metadata,
            ),
            intent=normalized_intent,
        )


def build_settlement_status() -> dict[str, Any]:
    fx_engine = default_fx_engine()
    rollout = _load_rollout_config()
    return {
        "available": True,
        "fx_engine": "afripay_deterministic_fx",
        "supported_currencies": sorted(
            {
                currency
                for currency in COUNTRY_CURRENCIES.values()
            }
            | {"AUD", "USD", "BIF", "CDF", "KES"}
        ),
        "country_currency_map": dict(COUNTRY_CURRENCIES),
        "domestic_rails": dict(DOMESTIC_RAIL_BY_CURRENCY),
        "cross_border_supported": True,
        "fx_reference": fx_engine.lock_rate("AUD", "USD").locked_reference,
        "cbdc_ready": False,
        "corridor_matrix": build_settlement_corridor_matrix(rollout),
        "rollout": rollout.canonical(),
    }


def build_settlement_corridor_matrix(
    rollout: SettlementRolloutConfig | None = None,
) -> list[dict[str, Any]]:
    rollout = rollout or _load_rollout_config()
    rows: list[dict[str, Any]] = []
    for corridor in rollout.corridors:
        source_country, settlement_country = _parse_corridor(corridor)
        settlement_currency = COUNTRY_CURRENCY_BY_REGION.get(settlement_country, "")
        default_provider = (
            DEFAULT_PROVIDER_BY_COUNTRY.get(settlement_country)
            if settlement_country in DEFAULT_PROVIDER_BY_COUNTRY
            else DOMESTIC_RAIL_BY_CURRENCY.get(settlement_currency, "payid")
        )
        mobile_money_ready = (
            settlement_country in DEFAULT_PROVIDER_BY_COUNTRY
            and rollout.mobile_money_live_enabled
            and rollout.compliance_live_enabled
        )
        execution_state = (
            "live_ready"
            if mobile_money_ready and rollout.settlement_mode == "pre_funded"
            else "pilot_ready"
            if settlement_country in DEFAULT_PROVIDER_BY_COUNTRY
            else "available"
        )
        rows.append(
            {
                "corridor": corridor,
                "source_country": source_country,
                "settlement_country": settlement_country,
                "settlement_currency": settlement_currency,
                "provider": default_provider,
                "rail": DOMESTIC_RAIL_BY_CURRENCY.get(
                    settlement_currency,
                    default_provider,
                ),
                "primary": corridor == rollout.primary_corridor,
                "settlement_mode": rollout.settlement_mode,
                "mobile_money_live_enabled": rollout.mobile_money_live_enabled,
                "compliance_provider": rollout.compliance_provider,
                "compliance_live_enabled": rollout.compliance_live_enabled,
                "mobile_money_ready": mobile_money_ready,
                "execution_state": execution_state,
            }
        )
    return rows


def _load_rollout_config() -> SettlementRolloutConfig:
    mode = os.environ.get("NOVAPAY_ROLLOUT_MODE", "canary").strip().lower() or "canary"
    primary_corridor = os.environ.get("NOVAPAY_PRIMARY_CORRIDOR", "AU->KE").strip() or "AU->KE"
    corridors = tuple(
        corridor.strip()
        for corridor in os.environ.get(
            "NOVAPAY_CORRIDORS",
            "AU->KE,AU->BI,AU->CD,USA->KE",
        ).split(",")
        if corridor.strip()
    )
    settlement_mode = os.environ.get("NOVAPAY_SETTLEMENT_MODE", "pre_funded").strip().lower() or "pre_funded"
    mobile_money_live_enabled = os.environ.get("NOVAPAY_MOBILE_MONEY_LIVE_ENABLED", "").lower() in {"1", "true", "yes"}
    compliance_provider = os.environ.get("NOVAPAY_COMPLIANCE_PROVIDER", "sumsub").strip().lower() or "sumsub"
    compliance_live_enabled = os.environ.get("NOVAPAY_COMPLIANCE_LIVE_ENABLED", "").lower() in {"1", "true", "yes"}
    return SettlementRolloutConfig(
        mode=mode,
        primary_corridor=primary_corridor,
        corridors=corridors,
        settlement_mode=settlement_mode,
        mobile_money_live_enabled=mobile_money_live_enabled,
        compliance_provider=compliance_provider,
        compliance_live_enabled=compliance_live_enabled,
    )


def _parse_corridor(corridor: str) -> tuple[str, str]:
    left, _, right = corridor.partition("->")
    return left.strip().upper(), right.strip().upper()


def _infer_country(intent: PaymentIntent, source_currency: str) -> str:
    metadata = intent.metadata
    for key in ("settlement_country", "country", "destination_country", "merchant_country", "payer_country"):
        candidate = str(metadata.get(key, "")).strip()
        if candidate:
            return normalize_country(candidate)
    if source_currency in {"AUD", "USD"}:
        return "AU"
    return ""


def _infer_settlement_country(
    intent: PaymentIntent,
    provider: str,
    source_country: str,
) -> str:
    metadata = intent.metadata
    for key in ("settlement_country", "destination_country", "country", "merchant_country"):
        candidate = str(metadata.get(key, "")).strip()
        if candidate:
            return normalize_country(candidate)
    normalized_provider = provider.strip().lower()
    if normalized_provider in DEFAULT_PROVIDER_BY_COUNTRY.values():
        for country, default_provider in DEFAULT_PROVIDER_BY_COUNTRY.items():
            if default_provider == normalized_provider:
                return country
    if normalized_provider == "payid":
        return "AU"
    if normalized_provider == "stripe":
        return "US" if source_country == "" else source_country
    if normalized_provider == "cbdc":
        return str(metadata.get("settlement_country", "")).strip().upper()
    return source_country


def _infer_settlement_currency(
    intent: PaymentIntent,
    provider: str,
    settlement_country: str,
    source_currency: str,
) -> str:
    metadata = intent.metadata
    explicit = str(metadata.get("settlement_currency", "")).strip()
    if explicit:
        return normalize_currency_code(explicit)
    if settlement_country in COUNTRY_CURRENCY_BY_REGION:
        return COUNTRY_CURRENCY_BY_REGION[settlement_country]
    normalized_provider = provider.strip().lower()
    if normalized_provider == "payid":
        return "AUD"
    if normalized_provider == "stripe":
        return source_currency if source_currency in {"USD", "AUD"} else "USD"
    if normalized_provider == "cbdc":
        return source_currency
    return source_currency


def _infer_route_hint(provider: str, settlement_country: str, settlement_currency: str) -> str:
    normalized_provider = provider.strip().lower()
    if normalized_provider in {"payid", "stripe", "cbdc"}:
        return normalized_provider
    if normalized_provider in {"mobile_money", "mobile-money", "momo"}:
        return DEFAULT_PROVIDER_BY_COUNTRY.get(settlement_country, "mobile_money")
    if normalized_provider in {
        "mpesa_ke",
        "airtel_money_ke",
        "lumicash_bi",
        "ecocash_bi",
        "orange_money_cd",
        "airtel_money_cd",
        "mpesa_cd",
    }:
        return normalized_provider
    if settlement_currency in DOMESTIC_RAIL_BY_CURRENCY:
        return DOMESTIC_RAIL_BY_CURRENCY[settlement_currency]
    return normalized_provider


def _route_id(
    intent_id: str,
    provider: str,
    source_country: str,
    settlement_country: str,
    source_currency: str,
    settlement_currency: str,
    settlement_amount: Decimal,
) -> str:
    digest = hashlib.sha256(
        ":".join(
            [
                intent_id,
                provider.strip().lower(),
                source_country or "GLOBAL",
                settlement_country or "GLOBAL",
                source_currency,
                settlement_currency,
                format(settlement_amount, ".2f"),
            ]
        ).encode("utf-8")
    ).hexdigest()[:20]
    return f"route_{digest}"
