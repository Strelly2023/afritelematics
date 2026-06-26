"""NovaPay transfer protocol, quotes, and execution receipts.

This module converts the existing payment rails into a product-level transfer
surface with:

- transparent fee and rate quotes
- payout method selection
- transfer limits
- local verification artifacts
- immutable audit receipts

It is intentionally deterministic so mobile apps, operator consoles, and API
clients can render the same transfer truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Mapping
from uuid import uuid4

from afritech.core_platform.cryptographic_consensus import _canonicalize_seal, _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.models import AuthorityDecision, Identity, PaymentIntent, PaymentReceipt
from afritech.core_platform.payments.mobile_money import mobile_money_catalog
from afritech.core_platform.payments.providers import payid_status
from afritech.core_platform.settlement import SettlementRouter, normalize_currency_code
from afritech.core_platform.signing import AuditSignature, sign_packet, verify_packet_signature
from afritech.core_platform.trust_node import build_trust_node_network_status
from afritech.core_platform.cbdc import cbdc_status

if TYPE_CHECKING:  # pragma: no cover
    from afritech.core_platform.services import NovaPayService


def _stable_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def _decimal(value: Any, fallback: str = "0") -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(fallback)


def _normalize_method(value: str | None) -> str:
    method = str(value or "bank_deposit").strip().lower().replace("-", "_")
    if method in {"bank", "bank_deposit", "bankdeposit"}:
        return "bank_deposit"
    if method in {"cash", "cash_pickup", "cashpickup"}:
        return "cash_pickup"
    if method in {"wallet", "mobile_wallet"}:
        return "wallet"
    if method in {"domestic", "domestic_transfer"}:
        return "domestic_transfer"
    if method in {"mobile_money", "mobilemoney", "momo"}:
        return "mobile_money"
    return method


def _use_case_profile(use_case: str) -> dict[str, Any]:
    normalized = str(use_case or "transparent_pricing").strip().lower().replace("-", "_")
    profiles = {
        "transparent_pricing": {
            "label": "Transparent pricing & mid-market exchange rates",
            "fee_pct": Decimal("0.008"),
            "fixed_fee": Decimal("1.00"),
            "priority": "pricing_clarity",
            "eta": "minutes_to_hours",
        },
        "fast_low_cost_international": {
            "label": "Fast and low-cost international transfers",
            "fee_pct": Decimal("0.007"),
            "fixed_fee": Decimal("0.75"),
            "priority": "speed_cost_balance",
            "eta": "minutes",
        },
        "frequent_traveler": {
            "label": "Frequent travelers and multi-currency budgeting",
            "fee_pct": Decimal("0.006"),
            "fixed_fee": Decimal("0.50"),
            "priority": "multi_currency_budgeting",
            "eta": "minutes_to_hours",
        },
        "large_international": {
            "label": "Large international transfers",
            "fee_pct": Decimal("0.0045"),
            "fixed_fee": Decimal("2.50"),
            "priority": "high_value_transfer",
            "eta": "hours_to_business_day",
        },
        "domestic_transfer": {
            "label": "Domestic transfers",
            "fee_pct": Decimal("0.0025"),
            "fixed_fee": Decimal("0.25"),
            "priority": "domestic_speed",
            "eta": "minutes",
        },
    }
    return profiles.get(normalized, profiles["transparent_pricing"]) | {
        "key": normalized,
    }


def _payout_profile(method: str) -> dict[str, Any]:
    normalized = _normalize_method(method)
    profiles = {
        "bank_deposit": {
            "label": "Bank deposit",
            "fee_adjustment": Decimal("0.000"),
            "fixed_adjustment": Decimal("0.00"),
            "limit": Decimal("25000"),
            "cash_pickup": False,
            "bank_deposit": True,
            "wallet": False,
            "eta": "same_day_or_next_business_day",
            "route_hint": "payid",
        },
        "cash_pickup": {
            "label": "Cash pickup",
            "fee_adjustment": Decimal("0.004"),
            "fixed_adjustment": Decimal("1.50"),
            "limit": Decimal("5000"),
            "cash_pickup": True,
            "bank_deposit": False,
            "wallet": False,
            "eta": "minutes_to_hours",
            "route_hint": "mobile_money",
        },
        "mobile_money": {
            "label": "Mobile money",
            "fee_adjustment": Decimal("0.002"),
            "fixed_adjustment": Decimal("0.75"),
            "limit": Decimal("10000"),
            "cash_pickup": False,
            "bank_deposit": False,
            "wallet": True,
            "eta": "minutes",
            "route_hint": "mobile_money",
        },
        "wallet": {
            "label": "Wallet transfer",
            "fee_adjustment": Decimal("0.0015"),
            "fixed_adjustment": Decimal("0.50"),
            "limit": Decimal("15000"),
            "cash_pickup": False,
            "bank_deposit": False,
            "wallet": True,
            "eta": "instant",
            "route_hint": "payid",
        },
        "domestic_transfer": {
            "label": "Domestic transfer",
            "fee_adjustment": Decimal("0.000"),
            "fixed_adjustment": Decimal("0.20"),
            "limit": Decimal("50000"),
            "cash_pickup": False,
            "bank_deposit": True,
            "wallet": False,
            "eta": "minutes",
            "route_hint": "payid",
        },
    }
    return profiles.get(normalized, profiles["bank_deposit"]) | {"key": normalized}


def _transfer_features() -> dict[str, Any]:
    countries = mobile_money_catalog()["countries"]
    return {
        "global_coverage": True,
        "global_reach": {
            "countries": sorted(countries.keys()),
            "country_count": len(countries),
            "coverage": "Australia, Kenya, Burundi, Democratic Republic of Congo",
        },
        "cash_pickups": True,
        "payout_methods": [
            "bank_deposit",
            "cash_pickup",
            "mobile_money",
            "wallet",
            "domestic_transfer",
        ],
        "ease_of_use": [
            "one quote",
            "one signature",
            "one receipt",
        ],
        "bank_deposit": True,
        "transparent_pricing": True,
        "mid_market_exchange_rates": True,
        "fast_low_cost_international": True,
        "frequent_travel_budgeting": True,
        "large_international_transfer_support": True,
        "domestic_transfers": True,
    }


def _transfer_limits() -> dict[str, Any]:
    return {
        "bank_deposit": {"default_limit": "25000", "currency": "AUD"},
        "cash_pickup": {"default_limit": "5000", "currency": "AUD"},
        "mobile_money": {"default_limit": "10000", "currency": "AUD"},
        "wallet": {"default_limit": "15000", "currency": "AUD"},
        "domestic_transfer": {"default_limit": "50000", "currency": "AUD"},
    }


def _transfer_rails() -> dict[str, Any]:
    return {
        "payid": payid_status(),
        "mobile_money": mobile_money_catalog(),
        "cbdc": cbdc_status(),
        "trust_node": build_trust_node_network_status(),
    }


def _normalize_transfer_provider(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    allowed = {
        "payid",
        "cbdc",
        "mobile_money",
        "mpesa_ke",
        "airtel_money_ke",
        "lumicash_bi",
        "ecocash_bi",
        "orange_money_cd",
        "airtel_money_cd",
        "mpesa_cd",
    }
    if normalized in {"payid", "pay_id", "osko"}:
        return "payid"
    if normalized in {"cbdc", "central_bank_digital_currency", "digital_cash"}:
        return "cbdc"
    if normalized in {"mobile_money", "mobile-money", "momo"}:
        return "mobile_money"
    if normalized in allowed:
        return normalized
    raise ValueError("invalid_transfer_provider")


@dataclass(frozen=True)
class TransferQuote:
    quote_id: str
    transfer_id: str
    sender_id: str
    organization_id: str
    recipient_name: str
    recipient_identifier: str
    recipient_country: str
    payout_method: str
    use_case: str
    memo: str | None
    source_amount: str
    source_currency: str
    destination_amount: str
    destination_currency: str
    exchange_rate: str
    mid_market_rate: str
    fee_amount: str
    total_debit: str
    transfer_limit: str
    route_class: str
    corridor: str
    route_hint: str
    eta: str
    cash_pickup_available: bool
    bank_deposit_available: bool
    global_coverage: bool
    features: dict[str, Any]
    rails: dict[str, Any]
    quote_hash: str

    def canonical(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "transfer_id": self.transfer_id,
            "sender_id": self.sender_id,
            "organization_id": self.organization_id,
            "recipient_name": self.recipient_name,
            "recipient_identifier": self.recipient_identifier,
            "recipient_country": self.recipient_country,
            "payout_method": self.payout_method,
            "use_case": self.use_case,
            "memo": self.memo,
            "source_amount": self.source_amount,
            "source_currency": self.source_currency,
            "destination_amount": self.destination_amount,
            "destination_currency": self.destination_currency,
            "exchange_rate": self.exchange_rate,
            "mid_market_rate": self.mid_market_rate,
            "fee_amount": self.fee_amount,
            "total_debit": self.total_debit,
            "transfer_limit": self.transfer_limit,
            "route_class": self.route_class,
            "corridor": self.corridor,
            "route_hint": self.route_hint,
            "eta": self.eta,
            "cash_pickup_available": self.cash_pickup_available,
            "bank_deposit_available": self.bank_deposit_available,
            "global_coverage": self.global_coverage,
            "features": self.features,
            "rails": self.rails,
            "quote_hash": self.quote_hash,
        }


@dataclass(frozen=True)
class TransferReceipt:
    transfer_id: str
    quote_id: str
    status: str
    receipt_body: dict[str, Any]
    payment: dict[str, Any]
    trust: dict[str, Any]
    receipt_hash: str
    audit_signature: dict[str, Any]
    verification_message: str
    transfer_quote: dict[str, Any]
    features: dict[str, Any]
    rails: dict[str, Any]
    payout_method: str
    route_class: str
    corridor: str

    def canonical(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "quote_id": self.quote_id,
            "status": self.status,
            "receipt_body": self.receipt_body,
            "payment": self.payment,
            "trust": self.trust,
            "receipt_hash": self.receipt_hash,
            "audit_signature": self.audit_signature,
            "verification_message": self.verification_message,
            "transfer_quote": self.transfer_quote,
            "features": self.features,
            "rails": self.rails,
            "payout_method": self.payout_method,
            "route_class": self.route_class,
            "corridor": self.corridor,
        }


@dataclass(frozen=True)
class TransferExecutionContext:
    quote: dict[str, Any]
    unsigned_quote: dict[str, Any]
    quote_hash: str
    source_amount: Decimal
    provider: str


def _quote_fee(
    amount: Decimal,
    *,
    use_case: str,
    payout_method: str,
) -> Decimal:
    use_case_profile = _use_case_profile(use_case)
    payout_profile = _payout_profile(payout_method)
    fee_pct = _decimal(use_case_profile["fee_pct"]) + _decimal(payout_profile["fee_adjustment"])
    fixed_fee = _decimal(use_case_profile["fixed_fee"]) + _decimal(payout_profile["fixed_adjustment"])
    fee = (amount * fee_pct) + fixed_fee
    if fee < Decimal("0.50"):
        fee = Decimal("0.50")
    return fee.quantize(Decimal("0.01"))


def _transfer_limit(
    *,
    payout_method: str,
    source_currency: str,
    destination_currency: str,
    route_class: str,
) -> Decimal:
    payout_profile = _payout_profile(payout_method)
    limit = _decimal(payout_profile["limit"], "1000")
    if route_class == "cross_border":
        limit = min(limit, Decimal("25000"))
    if source_currency != destination_currency and payout_method == "cash_pickup":
        limit = min(limit, Decimal("5000"))
    return limit


def _quote_route_hint(payout_method: str, route_class: str) -> str:
    payout_profile = _payout_profile(payout_method)
    if route_class == "domestic" and payout_method in {"bank_deposit", "domestic_transfer"}:
        return "payid"
    return str(payout_profile["route_hint"])


def _transfer_use_case_summary(use_case: str) -> str:
    return str(_use_case_profile(use_case)["label"])


def _quote_message(payload: Mapping[str, Any]) -> str:
    return f"{HASH_DOMAINS['SIGNED_PAYLOAD']}::{_hash(payload, domain=HASH_DOMAINS['TRANSFER_QUOTE'])}"


class NovaPayTransferService:
    """Quote, execute, and verify NovaPay transfers."""

    def __init__(
        self,
        *,
        payments: "NovaPayService" | None = None,
        settlement_router: SettlementRouter | None = None,
    ) -> None:
        if payments is None:
            from afritech.core_platform.services import NovaPayService

            payments = NovaPayService()
        self.payments = payments
        self.settlement_router = settlement_router or SettlementRouter()

    def build_features(self) -> dict[str, Any]:
        features = _transfer_features()
        features["use_cases"] = [
            {
                "key": "transparent_pricing",
                "label": "For transparent pricing & mid-market exchange rates",
            },
            {
                "key": "fast_low_cost_international",
                "label": "For fast and low-cost international transfers",
            },
            {
                "key": "frequent_traveler",
                "label": "For frequent travelers and multi-currency budgeting",
            },
            {
                "key": "large_international",
                "label": "For large international transfers",
            },
            {
                "key": "domestic_transfer",
                "label": "For domestic transfers",
            },
        ]
        features["best_money_transfer_app"] = "NovaPay"
        return _canonicalize_seal(features)

    def build_limits(self) -> dict[str, Any]:
        return _canonicalize_seal(_transfer_limits())

    def build_rails(self) -> dict[str, Any]:
        return _canonicalize_seal(_transfer_rails())

    def validate_quote(self, quote: TransferQuote | Mapping[str, Any]) -> TransferExecutionContext:
        quote_payload = quote.canonical() if hasattr(quote, "canonical") else _canonicalize_seal(dict(quote))
        if not isinstance(quote_payload, Mapping) or not quote_payload:
            raise ValueError("transfer_quote_required")

        quote_hash = str(quote_payload.get("quote_hash", "")).strip()
        if not quote_hash:
            raise ValueError("missing_transfer_quote_hash")

        unsigned_quote = dict(quote_payload)
        unsigned_quote.pop("quote_hash", None)
        computed_hash = _hash(unsigned_quote, domain=HASH_DOMAINS["TRANSFER_QUOTE"])
        if computed_hash != quote_hash:
            raise ValueError("transfer_quote_hash_mismatch")

        source_amount_raw = unsigned_quote.get("source_amount")
        if not isinstance(source_amount_raw, (str, int, float, Decimal)):
            raise ValueError("invalid_quote_source_amount")
        source_amount = _decimal(source_amount_raw)
        if source_amount <= Decimal("0"):
            raise ValueError("invalid_quote_source_amount")

        if "route_hint" not in unsigned_quote:
            raise ValueError("missing_route_hint")
        resolved_provider = str(unsigned_quote.get("route_hint") or "").strip().lower()
        if not resolved_provider:
            raise ValueError("missing_route_hint")
        resolved_provider = _normalize_transfer_provider(resolved_provider)
        return TransferExecutionContext(
            quote=quote_payload,
            unsigned_quote=unsigned_quote,
            quote_hash=quote_hash,
            source_amount=source_amount,
            provider=resolved_provider,
        )

    def secure_execute(
        self,
        quote: TransferQuote | Mapping[str, Any],
        *,
        identity: Identity,
        decision: AuthorityDecision,
        provider: str | None = None,
        live_provider: bool = False,
    ) -> TransferReceipt:
        context = self.validate_quote(quote)
        if provider is not None:
            requested_provider = _normalize_transfer_provider(provider)
            if requested_provider != context.provider:
                raise ValueError("transfer_provider_mismatch")
        return self._execute_validated_quote(
            context,
            identity=identity,
            decision=decision,
            live_provider=live_provider,
        )

    def quote(
        self,
        *,
        identity: Identity,
        recipient_name: str,
        recipient_identifier: str,
        amount: Decimal,
        source_currency: str,
        recipient_country: str,
        payout_method: str = "bank_deposit",
        use_case: str = "transparent_pricing",
        memo: str | None = None,
        live_provider: bool = False,
    ) -> TransferQuote:
        normalized_method = _normalize_method(payout_method)
        normalized_source_currency = normalize_currency_code(source_currency)
        normalized_destination_country = str(recipient_country or "").strip().upper()
        use_case_profile = _use_case_profile(use_case)

        settlement_intent = PaymentIntent(
            intent_id=_stable_id("transfer"),
            actor_id=identity.identity_id,
            organization_id=identity.organization_id,
            amount=_decimal(amount),
            currency=normalized_source_currency,
            destination=recipient_identifier,
            metadata={
                "recipient_name": recipient_name,
                "recipient_identifier": recipient_identifier,
                "recipient_country": normalized_destination_country,
                "payout_method": normalized_method,
                "use_case": use_case,
                "memo": memo,
                "country": normalized_destination_country or None,
            },
        )
        settlement = self.settlement_router.plan(
            settlement_intent,
            provider=_quote_route_hint(normalized_method, "domestic" if normalized_destination_country == "AU" and normalized_source_currency == "AUD" else "cross_border"),
            live_provider=live_provider,
        )

        source_amount = _decimal(amount)
        destination_amount = settlement.intent.amount
        exchange_rate = Decimal("1.00")
        if source_amount > 0:
            exchange_rate = (destination_amount / source_amount).quantize(Decimal("0.0001"))
        fee_amount = _quote_fee(source_amount, use_case=use_case, payout_method=normalized_method)
        total_debit = (source_amount + fee_amount).quantize(Decimal("0.01"))
        payout_profile = _payout_profile(normalized_method)
        transfer_limit = _transfer_limit(
            payout_method=normalized_method,
            source_currency=normalized_source_currency,
            destination_currency=settlement.intent.currency,
            route_class=settlement.plan.route_class,
        )
        quote_id = _stable_id("quote")
        quote_payload = {
            "quote_id": quote_id,
            "transfer_id": settlement_intent.intent_id,
            "sender_id": identity.identity_id,
            "organization_id": identity.organization_id,
            "recipient_name": recipient_name,
            "recipient_identifier": recipient_identifier,
            "recipient_country": normalized_destination_country,
            "payout_method": normalized_method,
            "use_case": use_case,
            "memo": memo,
            "source_amount": str(source_amount.quantize(Decimal("0.01"))),
            "source_currency": normalized_source_currency,
            "destination_amount": str(destination_amount),
            "destination_currency": settlement.intent.currency,
            "exchange_rate": str(exchange_rate),
            "mid_market_rate": settlement.plan.fx_rate or "1.00",
            "fee_amount": str(fee_amount),
            "total_debit": str(total_debit),
            "transfer_limit": str(transfer_limit),
            "route_class": settlement.plan.route_class,
            "corridor": settlement.plan.corridor,
            "route_hint": settlement.plan.route_hint,
            "eta": use_case_profile["eta"],
            "cash_pickup_available": bool(payout_profile["cash_pickup"]),
            "bank_deposit_available": bool(payout_profile["bank_deposit"]),
            "global_coverage": True,
            "features": self.build_features(),
            "rails": self.build_rails(),
        }
        quote_hash = _hash(quote_payload, domain=HASH_DOMAINS["TRANSFER_QUOTE"])
        return TransferQuote(
            quote_id=quote_id,
            transfer_id=settlement_intent.intent_id,
            sender_id=identity.identity_id,
            organization_id=identity.organization_id,
            recipient_name=recipient_name,
            recipient_identifier=recipient_identifier,
            recipient_country=normalized_destination_country,
            payout_method=normalized_method,
            use_case=use_case,
            memo=memo,
            source_amount=str(source_amount.quantize(Decimal("0.01"))),
            source_currency=normalized_source_currency,
            destination_amount=str(destination_amount.quantize(Decimal("0.01"))),
            destination_currency=settlement.intent.currency,
            exchange_rate=str(exchange_rate),
            mid_market_rate=str(settlement.plan.fx_rate or "1.00"),
            fee_amount=str(fee_amount),
            total_debit=str(total_debit),
            transfer_limit=str(transfer_limit),
            route_class=settlement.plan.route_class,
            corridor=settlement.plan.corridor,
            route_hint=settlement.plan.route_hint,
            eta=use_case_profile["eta"],
            cash_pickup_available=bool(payout_profile["cash_pickup"]),
            bank_deposit_available=bool(payout_profile["bank_deposit"]),
            global_coverage=True,
            features=self.build_features(),
            rails=self.build_rails(),
            quote_hash=quote_hash,
        )

    def _execute_validated_quote(
        self,
        context: TransferExecutionContext,
        *,
        identity: Identity,
        decision: AuthorityDecision,
        live_provider: bool = False,
    ) -> TransferReceipt:
        quote_payload = context.quote
        unsigned_quote = context.unsigned_quote
        quote_hash = context.quote_hash

        if not decision.allowed:
            raise PermissionError(f"transfer rejected by authority: {decision.reason}")

        transfer_intent = PaymentIntent(
            intent_id=str(quote_payload.get("transfer_id") or _stable_id("transfer")),
            actor_id=identity.identity_id,
            organization_id=identity.organization_id,
            amount=context.source_amount,
            currency=str(quote_payload.get("source_currency") or "AUD"),
            destination=str(quote_payload.get("recipient_identifier") or ""),
            metadata={
                "recipient_name": quote_payload.get("recipient_name"),
                "recipient_country": quote_payload.get("recipient_country"),
                "country": quote_payload.get("recipient_country"),
                "settlement_country": quote_payload.get("recipient_country"),
                "payout_method": quote_payload.get("payout_method"),
                "use_case": quote_payload.get("use_case"),
                "corridor": quote_payload.get("corridor"),
                "transfer_quote_hash": quote_hash,
            },
        )
        payment = self.payments.execute(
            transfer_intent,
            identity=identity,
            decision=decision,
            provider=context.provider,
            live_provider=live_provider,
        )
        receipt_core = {
            "transfer_id": transfer_intent.intent_id,
            "quote_id": str(quote_payload.get("quote_id", "")).strip(),
            "sender_id": identity.identity_id,
            "organization_id": identity.organization_id,
            "recipient_name": quote_payload.get("recipient_name"),
            "recipient_identifier": quote_payload.get("recipient_identifier"),
            "recipient_country": quote_payload.get("recipient_country"),
            "payout_method": quote_payload.get("payout_method"),
            "use_case": quote_payload.get("use_case"),
            "corridor": quote_payload.get("corridor"),
            "route_class": quote_payload.get("route_class"),
            "payment": payment.canonical(),
            "quote": quote_payload,
            "features": self.build_features(),
            "rails": self.build_rails(),
        }
        trust = self.payments.event_bus.status()
        trust_receipt = {
            "trust_id": _stable_id("trust"),
            "subject_id": identity.identity_id,
            "organization_id": identity.organization_id,
            "event_type": "novapay.transfer.completed",
            "event_hash": _hash(receipt_core, domain=HASH_DOMAINS["TRANSFER_RECEIPT"]),
            "replay_status": "verified",
            "packet": receipt_core,
        }
        receipt_body = {
            **receipt_core,
            "trust": trust_receipt,
            "audit": trust,
        }
        receipt_hash = _hash(receipt_body, domain=HASH_DOMAINS["TRANSFER_RECEIPT"])
        audit_signature = sign_packet(receipt_body).canonical()
        verification_message = _quote_message(unsigned_quote)
        return TransferReceipt(
            transfer_id=transfer_intent.intent_id,
            quote_id=str(quote_payload.get("quote_id", "")).strip() or _stable_id("quote"),
            status=payment.status,
            receipt_body=receipt_body,
            payment=payment.canonical(),
            trust=trust_receipt,
            receipt_hash=receipt_hash,
            audit_signature=audit_signature,
            verification_message=verification_message,
            transfer_quote=quote_payload,
            features=self.build_features(),
            rails=self.build_rails(),
            payout_method=str(quote_payload.get("payout_method", "bank_deposit")),
            route_class=str(quote_payload.get("route_class", "unknown")),
            corridor=str(quote_payload.get("corridor", "")),
        )

    def execute(
        self,
        quote: TransferQuote | Mapping[str, Any],
        *,
        identity: Identity,
        decision: AuthorityDecision,
        provider: str | None = None,
        live_provider: bool = False,
    ) -> TransferReceipt:
        context = self.validate_quote(quote)
        if provider is not None:
            requested_provider = _normalize_transfer_provider(provider)
            if requested_provider != context.provider:
                raise ValueError("transfer_provider_mismatch")
        return self._execute_validated_quote(
            context,
            identity=identity,
            decision=decision,
            live_provider=live_provider,
        )

    def verify(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(receipt, Mapping) or not receipt:
            return {"valid": False, "reason": "transfer_receipt_required"}

        expected_hash = str(receipt.get("receipt_hash", "")).strip()
        if not expected_hash:
            return {"valid": False, "reason": "missing_transfer_receipt_hash"}

        receipt_body = receipt.get("receipt_body")
        if isinstance(receipt_body, Mapping) and receipt_body:
            unsigned = dict(receipt_body)
        else:
            unsigned = dict(receipt)
            for key in ("receipt_hash", "audit_signature", "verification_message"):
                unsigned.pop(key, None)
        computed_hash = _hash(unsigned, domain=HASH_DOMAINS["TRANSFER_RECEIPT"])
        if computed_hash != expected_hash:
            return {
                "valid": False,
                "reason": "transfer_receipt_hash_mismatch",
                "expected_hash": computed_hash,
                "receipt_hash": expected_hash,
            }

        audit_signature = receipt.get("audit_signature")
        if isinstance(audit_signature, Mapping):
            valid_signature = verify_packet_signature(
                unsigned,
                audit_signature,
            )
        else:
            valid_signature = False

        return {
            "valid": valid_signature and computed_hash == expected_hash,
            "reason": "transfer_receipt_verified" if valid_signature else "transfer_signature_invalid",
            "receipt_hash": expected_hash,
            "audit_signature_valid": valid_signature,
        }


__all__ = [
    "NovaPayTransferService",
    "TransferQuote",
    "TransferReceipt",
]
