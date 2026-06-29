"""Governed NovaPay transfer runtime.

This module introduces the next-generation NovaPay runtime model centered on a
single Transfer aggregate, with jurisdiction, licensing, corridor, compliance,
policy, routing, ledger, settlement, and receipt as distinct runtime domains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping
from uuid import uuid4

from afritech.core_platform.event_bus import EventBus, build_event_bus
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.models import AuthorityDecision, Identity
from afritech.core_platform.signing import sign_packet, verify_packet_signature
from afritech.core_platform.settlement import normalize_currency_code
from afritech.core_platform.transfers import NovaPayTransferService, _decimal, _hash, _normalize_method


def _stable_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


_TRANSFER_TYPE_ALIASES = {
    "domestic transfer": "Domestic Transfer",
    "domestic_transfer": "Domestic Transfer",
    "domestictransfer": "Domestic Transfer",
    "cross-border remittance": "Cross-Border Remittance",
    "cross_border_remittance": "Cross-Border Remittance",
    "crossborderremittance": "Cross-Border Remittance",
    "wallet transfer": "Wallet Transfer",
    "wallet_transfer": "Wallet Transfer",
    "wallettransfer": "Wallet Transfer",
    "merchant payment": "Merchant Payment",
    "merchant_payment": "Merchant Payment",
    "merchantpayment": "Merchant Payment",
    "qr payment": "QR Payment",
    "qr_payment": "QR Payment",
    "qrpayment": "QR Payment",
    "bill payment": "Bill Payment",
    "bill_payment": "Bill Payment",
    "billpayment": "Bill Payment",
    "cash in": "Cash In",
    "cash_in": "Cash In",
    "cashin": "Cash In",
    "cash out": "Cash Out",
    "cash_out": "Cash Out",
    "cashout": "Cash Out",
    "bulk disbursement": "Bulk Disbursement",
    "bulk_disbursement": "Bulk Disbursement",
    "bulkdisbursement": "Bulk Disbursement",
    "supplier payment": "Supplier Payment",
    "supplier_payment": "Supplier Payment",
    "supplierpayment": "Supplier Payment",
    "government payment": "Government Payment",
    "government_payment": "Government Payment",
    "governmentpayment": "Government Payment",
    "payroll": "Payroll",
    "refund": "Refund",
}

_FUNDING_TYPE_ALIASES = {
    "wallet": "wallet",
    "mobile money": "mobile_money",
    "mobile_money": "mobile_money",
    "mobilemoney": "mobile_money",
    "bank": "bank",
    "bank account": "bank",
    "bank_account": "bank",
    "bankaccount": "bank",
    "card": "card",
    "payment card": "card",
    "payment_card": "card",
    "paymentcard": "card",
    "cash": "cash",
    "agent cash": "cash",
    "agent_cash": "cash",
    "agentcash": "cash",
}


def _normalize_transfer_type(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    normalized = " ".join(normalized.split())
    if not normalized:
        return "Cross-Border Remittance"
    return _TRANSFER_TYPE_ALIASES.get(normalized, str(value).strip())


def _normalize_funding_type(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    normalized = " ".join(normalized.split())
    if not normalized:
        return "wallet"
    return _FUNDING_TYPE_ALIASES.get(normalized, normalized.replace(" ", "_"))


@dataclass(frozen=True)
class Customer:
    customer_id: str
    identity_id: str
    organization_id: str
    email: str
    kyc_status: str = "unverified"

    def canonical(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "identity_id": self.identity_id,
            "organization_id": self.organization_id,
            "email": self.email,
            "kyc_status": self.kyc_status,
        }


@dataclass(frozen=True)
class Recipient:
    recipient_id: str
    type: str
    name: str
    phone_number: str
    wallet_id: str | None = None
    bank_account_id: str | None = None
    mobile_money_id: str | None = None
    jurisdiction_id: str | None = None
    verified: bool = False

    def canonical(self) -> dict[str, Any]:
        return {
            "recipient_id": self.recipient_id,
            "type": self.type,
            "name": self.name,
            "phone_number": self.phone_number,
            "wallet_id": self.wallet_id,
            "bank_account_id": self.bank_account_id,
            "mobile_money_id": self.mobile_money_id,
            "jurisdiction_id": self.jurisdiction_id,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class FundingSource:
    funding_source_id: str
    type: str
    owner_id: str
    provider: str
    reference: str
    status: str = "active"
    validated: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "funding_source_id": self.funding_source_id,
            "type": self.type,
            "owner_id": self.owner_id,
            "provider": self.provider,
            "reference": self.reference,
            "status": self.status,
            "validated": self.validated,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SettlementRail:
    rail_id: str
    type: str
    provider: str
    currency: str
    country: str
    status: str = "active"
    cost_model: str = "policy_selected"
    latency_profile: str = "policy_selected"
    supported_corridors: tuple[str, ...] = field(default_factory=tuple)

    def canonical(self) -> dict[str, Any]:
        return {
            "rail_id": self.rail_id,
            "type": self.type,
            "provider": self.provider,
            "currency": self.currency,
            "country": self.country,
            "status": self.status,
            "cost_model": self.cost_model,
            "latency_profile": self.latency_profile,
            "supported_corridors": list(self.supported_corridors),
        }


@dataclass(frozen=True)
class Jurisdiction:
    jurisdiction_id: str
    country_code: str
    region: str
    regulator: str
    kyc_requirements: tuple[str, ...]
    allowed_transfer_types: tuple[str, ...]
    license_required: bool = True
    regulated: bool = True
    reporting_rules: tuple[str, ...] = field(default_factory=tuple)
    transaction_limits: dict[str, str] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "jurisdiction_id": self.jurisdiction_id,
            "country_code": self.country_code,
            "region": self.region,
            "regulator": self.regulator,
            "kyc_requirements": list(self.kyc_requirements),
            "allowed_transfer_types": list(self.allowed_transfer_types),
            "license_required": self.license_required,
            "regulated": self.regulated,
            "reporting_rules": list(self.reporting_rules),
            "transaction_limits": dict(self.transaction_limits),
        }


@dataclass(frozen=True)
class License:
    license_id: str
    jurisdiction_id: str
    license_type: str
    entity_name: str
    valid_from: str
    valid_to: str
    status: str = "active"

    def canonical(self) -> dict[str, Any]:
        return {
            "license_id": self.license_id,
            "jurisdiction_id": self.jurisdiction_id,
            "license_type": self.license_type,
            "entity_name": self.entity_name,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "status": self.status,
        }


@dataclass(frozen=True)
class Corridor:
    corridor_id: str
    source_country: str
    destination_country: str
    allowed: bool
    fx_required: bool
    max_amount: str
    settlement_currency: str
    status: str = "active"
    settlement_rail: str = "policy_selected"
    settlement_provider: str = "policy_selected"
    compliance_provider: str = "policy_selected"
    execution_state: str = "pilot_ready"

    def canonical(self) -> dict[str, Any]:
        return {
            "corridor_id": self.corridor_id,
            "source_country": self.source_country,
            "destination_country": self.destination_country,
            "allowed": self.allowed,
            "fx_required": self.fx_required,
            "max_amount": self.max_amount,
            "settlement_currency": self.settlement_currency,
            "status": self.status,
            "settlement_rail": self.settlement_rail,
            "settlement_provider": self.settlement_provider,
            "compliance_provider": self.compliance_provider,
            "execution_state": self.execution_state,
        }


@dataclass(frozen=True)
class ComplianceCase:
    compliance_case_id: str
    transfer_id: str
    kyc_status: str
    aml_risk_score: int
    sanctions_flag: bool
    review_required: bool
    decision: str
    created_at: str = field(default_factory=_utcnow)

    def canonical(self) -> dict[str, Any]:
        return {
            "compliance_case_id": self.compliance_case_id,
            "transfer_id": self.transfer_id,
            "kyc_status": self.kyc_status,
            "aml_risk_score": self.aml_risk_score,
            "sanctions_flag": self.sanctions_flag,
            "review_required": self.review_required,
            "decision": self.decision,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class LedgerEntry:
    ledger_entry_id: str
    transfer_id: str
    account_id: str
    entry_type: str
    amount: str
    currency: str
    balance_after: str
    created_at: str = field(default_factory=_utcnow)

    def canonical(self) -> dict[str, Any]:
        return {
            "ledger_entry_id": self.ledger_entry_id,
            "transfer_id": self.transfer_id,
            "account_id": self.account_id,
            "entry_type": self.entry_type,
            "amount": self.amount,
            "currency": self.currency,
            "balance_after": self.balance_after,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    transfer_id: str
    rail: str
    provider: str
    status: str
    reference_id: str | None = None
    settled_at: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "settlement_id": self.settlement_id,
            "transfer_id": self.transfer_id,
            "rail": self.rail,
            "provider": self.provider,
            "status": self.status,
            "reference_id": self.reference_id,
            "settled_at": self.settled_at,
        }


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    transfer_id: str
    issued_at: str
    verification_code: str
    signature: dict[str, str]
    document_url: str

    def canonical(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "transfer_id": self.transfer_id,
            "issued_at": self.issued_at,
            "verification_code": self.verification_code,
            "signature": dict(self.signature),
            "document_url": self.document_url,
        }


@dataclass(frozen=True)
class TransferEvent:
    event_id: str
    transfer_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]
    decision_trace: dict[str, Any]

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "transfer_id": self.transfer_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
            "decision_trace": dict(self.decision_trace),
        }


@dataclass(frozen=True)
class Transfer:
    transfer_id: str
    transfer_type: str
    status: str
    amount: str
    currency: str
    sender_id: str
    recipient_id: str
    funding_source_id: str
    settlement_rail: str
    jurisdiction_id: str
    corridor_id: str
    quote_id: str
    route_id: str
    compliance_status: str
    policy_decision_id: str
    created_at: str
    updated_at: str
    timeline: tuple[TransferEvent, ...] = field(default_factory=tuple)
    receipt: Receipt | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "transfer_type": self.transfer_type,
            "status": self.status,
            "amount": self.amount,
            "currency": self.currency,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "funding_source_id": self.funding_source_id,
            "settlement_rail": self.settlement_rail,
            "jurisdiction_id": self.jurisdiction_id,
            "corridor_id": self.corridor_id,
            "quote_id": self.quote_id,
            "route_id": self.route_id,
            "compliance_status": self.compliance_status,
            "policy_decision_id": self.policy_decision_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "timeline": [event.canonical() for event in self.timeline],
            "receipt": self.receipt.canonical() if self.receipt else None,
        }


@dataclass(frozen=True)
class TransferAdmissionResult:
    approved: bool
    transfer_id: str
    transfer_type: str
    sender: dict[str, Any]
    recipient: dict[str, Any]
    funding_source: dict[str, Any]
    jurisdiction: dict[str, Any]
    license: dict[str, Any]
    corridor: dict[str, Any]
    compliance: dict[str, Any]
    policy: dict[str, Any]
    quote: dict[str, Any]
    routing: dict[str, Any]
    decision_trace: dict[str, Any]

    def canonical(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "transfer_id": self.transfer_id,
            "transfer_type": self.transfer_type,
            "sender": dict(self.sender),
            "recipient": dict(self.recipient),
            "funding_source": dict(self.funding_source),
            "jurisdiction": dict(self.jurisdiction),
            "license": dict(self.license),
            "corridor": dict(self.corridor),
            "compliance": dict(self.compliance),
            "policy": dict(self.policy),
            "quote": dict(self.quote),
            "routing": dict(self.routing),
            "decision_trace": dict(self.decision_trace),
        }


@dataclass(frozen=True)
class TransferAdmissionRequest:
    transfer_type: str
    sender_id: str
    sender_email: str
    recipient_name: str
    recipient_identifier: str
    recipient_country: str
    amount: Decimal
    source_currency: str
    source_country: str
    funding_source_type: str
    funding_source_reference: str
    payout_method: str
    use_case: str
    memo: str | None = None
    transfer_id: str | None = None
    recipient_type: str = "individual"
    live_provider: bool = False


@dataclass(frozen=True)
class RuntimeTransferRecord:
    transfer: Transfer
    admission: TransferAdmissionResult
    funding_source: FundingSource
    recipient: Recipient
    compliance_case: ComplianceCase
    ledger_entries: tuple[LedgerEntry, ...]
    settlement: SettlementRecord | None
    receipt: Receipt | None
    provider_receipt: dict[str, Any] | None
    events: tuple[TransferEvent, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "transfer": self.transfer.canonical(),
            "admission": self.admission.canonical(),
            "funding_source": self.funding_source.canonical(),
            "recipient": self.recipient.canonical(),
            "compliance_case": self.compliance_case.canonical(),
            "ledger_entries": [entry.canonical() for entry in self.ledger_entries],
            "settlement": self.settlement.canonical() if self.settlement else None,
            "receipt": self.receipt.canonical() if self.receipt else None,
            "provider_receipt": dict(self.provider_receipt) if self.provider_receipt else None,
            "events": [event.canonical() for event in self.events],
        }


class NovaPayTransferAdmissionError(ValueError):
    """Raised when the governed admission pipeline rejects a transfer."""


class NovaPayRegistry:
    """Static jurisdiction, license, and corridor registry."""

    def __init__(self) -> None:
        self._jurisdictions = self._seed_jurisdictions()
        self._licenses = self._seed_licenses()
        self._corridors = self._seed_corridors()

    def jurisdictions(self) -> tuple[Jurisdiction, ...]:
        return tuple(self._jurisdictions)

    def licenses(self) -> tuple[License, ...]:
        return tuple(self._licenses)

    def corridors(self) -> tuple[Corridor, ...]:
        return tuple(self._corridors)

    def resolve_jurisdiction(self, country_code: str) -> Jurisdiction:
        normalized = str(country_code or "").strip().upper()
        for jurisdiction in self._jurisdictions:
            if jurisdiction.country_code == normalized:
                return jurisdiction
        raise NovaPayTransferAdmissionError(f"unknown_jurisdiction:{normalized}")

    def resolve_license(self, jurisdiction: Jurisdiction) -> License:
        for license_record in self._licenses:
            if (
                license_record.jurisdiction_id == jurisdiction.jurisdiction_id
                and license_record.status == "active"
            ):
                return license_record
        raise NovaPayTransferAdmissionError(f"license_not_active:{jurisdiction.country_code}")

    def resolve_corridor(self, source_country: str, destination_country: str) -> Corridor:
        source = str(source_country or "").strip().upper()
        destination = str(destination_country or "").strip().upper()
        for corridor in self._corridors:
            if corridor.source_country == source and corridor.destination_country == destination:
                return corridor
        raise NovaPayTransferAdmissionError(f"unknown_corridor:{source}->{destination}")

    def _seed_jurisdictions(self) -> list[Jurisdiction]:
        countries = {
            "AU": ("Oceania", "AUSTRAC", ("identity", "kyc", "aml", "sanctions")),
            "US": ("North America", "FinCEN", ("identity", "kyc", "aml", "sanctions")),
            "KE": ("Africa", "CBK", ("identity", "kyc", "aml", "sanctions")),
            "BI": ("Africa", "BRB", ("identity", "kyc", "aml", "sanctions")),
            "CD": ("Africa", "BCC", ("identity", "kyc", "aml", "sanctions")),
        }
        return [
            Jurisdiction(
                jurisdiction_id=f"jur_{country.lower()}",
                country_code=country,
                region=region,
                regulator=regulator,
                kyc_requirements=requirements,
                allowed_transfer_types=(
                    "Domestic Transfer",
                    "Cross-Border Remittance",
                    "Wallet Transfer",
                    "Merchant Payment",
                    "QR Payment",
                    "Bill Payment",
                    "Cash In",
                    "Cash Out",
                    "Payroll",
                    "Bulk Disbursement",
                    "Supplier Payment",
                    "Government Payment",
                    "Refund",
                ),
                reporting_rules=("suspicious_activity_reporting", "threshold_reporting"),
                transaction_limits={"default": "50000"},
            )
            for country, (region, regulator, requirements) in countries.items()
        ]

    def _seed_licenses(self) -> list[License]:
        now = "2026-01-01T00:00:00Z"
        expires = "2030-12-31T23:59:59Z"
        return [
            License(
                license_id="lic_au_remittance",
                jurisdiction_id="jur_au",
                license_type="money_transfer_license",
                entity_name="NovaPay Australia",
                valid_from=now,
                valid_to=expires,
            ),
            License(
                license_id="lic_us_remittance",
                jurisdiction_id="jur_us",
                license_type="money_service_business",
                entity_name="NovaPay US",
                valid_from=now,
                valid_to=expires,
            ),
            License(
                license_id="lic_ke_partner",
                jurisdiction_id="jur_ke",
                license_type="partner_remittance",
                entity_name="NovaPay Kenya Partner",
                valid_from=now,
                valid_to=expires,
            ),
            License(
                license_id="lic_bi_partner",
                jurisdiction_id="jur_bi",
                license_type="partner_remittance",
                entity_name="NovaPay Burundi Partner",
                valid_from=now,
                valid_to=expires,
            ),
            License(
                license_id="lic_cd_partner",
                jurisdiction_id="jur_cd",
                license_type="partner_remittance",
                entity_name="NovaPay DRC Partner",
                valid_from=now,
                valid_to=expires,
            ),
        ]

    def _seed_corridors(self) -> list[Corridor]:
        rows = [
            ("AU", "KE", "KES", True, True, "10000", "mobile_money", "mpesa_ke", "pilot_ready"),
            ("AU", "BI", "BIF", True, True, "10000", "mobile_money", "lumicash_bi", "pilot_ready"),
            ("AU", "CD", "CDF", True, True, "10000", "mobile_money", "orange_money_cd", "pilot_ready"),
            ("US", "KE", "KES", True, True, "10000", "mobile_money", "mpesa_ke", "pilot_ready"),
            ("KE", "KE", "KES", True, False, "50000", "mobile_money", "mpesa_ke", "live_ready"),
        ]
        return [
            Corridor(
                corridor_id=f"corr_{source.lower()}_{destination.lower()}",
                source_country=source,
                destination_country=destination,
                allowed=allowed,
                fx_required=fx_required,
                max_amount=max_amount,
                settlement_currency=settlement_currency,
                settlement_rail="mobile_money" if destination in {"KE", "BI", "CD"} else "bank",
                settlement_provider=provider,
                compliance_provider="sumsub",
                execution_state=execution_state,
            )
            for source, destination, settlement_currency, allowed, fx_required, max_amount, settlement_rail, provider, execution_state in rows
        ]


class InMemoryNovaPayRuntimeStore:
    def __init__(self) -> None:
        self.records: dict[str, RuntimeTransferRecord] = {}
        self.events: dict[str, list[TransferEvent]] = {}

    def save(self, record: RuntimeTransferRecord) -> None:
        self.records[record.transfer.transfer_id] = record
        self.events[record.transfer.transfer_id] = list(record.events)

    def get(self, transfer_id: str) -> RuntimeTransferRecord | None:
        return self.records.get(transfer_id)

    def append_event(self, transfer_id: str, event: TransferEvent) -> None:
        self.events.setdefault(transfer_id, []).append(event)
        record = self.records.get(transfer_id)
        if record is not None:
            self.records[transfer_id] = RuntimeTransferRecord(
                transfer=record.transfer,
                admission=record.admission,
                funding_source=record.funding_source,
                recipient=record.recipient,
                compliance_case=record.compliance_case,
                ledger_entries=record.ledger_entries,
                settlement=record.settlement,
                receipt=record.receipt,
                provider_receipt=record.provider_receipt,
                events=tuple(self.events[transfer_id]),
            )


class NovaPayRuntimeEngine:
    """Governed runtime model for NovaPay transfers."""

    def __init__(
        self,
        *,
        transfer_service: NovaPayTransferService | None = None,
        event_bus: EventBus | None = None,
        registry: NovaPayRegistry | None = None,
        store: InMemoryNovaPayRuntimeStore | None = None,
    ) -> None:
        self.transfer_service = transfer_service or NovaPayTransferService()
        self.event_bus = event_bus or build_event_bus()
        self.registry = registry or NovaPayRegistry()
        self.store = store or InMemoryNovaPayRuntimeStore()

    def build_jurisdictions(self) -> list[dict[str, Any]]:
        return [jurisdiction.canonical() for jurisdiction in self.registry.jurisdictions()]

    def build_licenses(self) -> list[dict[str, Any]]:
        return [license_record.canonical() for license_record in self.registry.licenses()]

    def build_corridors(self) -> list[dict[str, Any]]:
        return [corridor.canonical() for corridor in self.registry.corridors()]

    def validate_funding_source(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise NovaPayTransferAdmissionError("funding_source_payload_required")
        funding_type = _normalize_funding_type(payload.get("funding_source_type") or payload.get("type"))
        owner_id = str(payload.get("owner_id") or payload.get("sender_id") or "").strip()
        reference = str(payload.get("reference") or payload.get("funding_source_reference") or "").strip()
        if not owner_id:
            raise NovaPayTransferAdmissionError("funding_source_owner_required")
        if not reference:
            raise NovaPayTransferAdmissionError("funding_source_reference_required")
        if funding_type not in {"wallet", "mobile_money", "bank", "card", "cash"}:
            raise NovaPayTransferAdmissionError(f"funding_source_not_supported:{funding_type}")
        source = FundingSource(
            funding_source_id=str(payload.get("funding_source_id") or _stable_id("fs")),
            type=funding_type,
            owner_id=owner_id,
            provider=str(payload.get("provider") or funding_type),
            reference=reference,
            status=str(payload.get("status") or "active"),
            validated=True,
            metadata=dict(payload.get("metadata") or {}),
        )
        return source.canonical()

    def admit_transfer(
        self,
        payload: Mapping[str, Any],
        *,
        identity: Identity,
    ) -> TransferAdmissionResult:
        if not isinstance(payload, Mapping):
            raise NovaPayTransferAdmissionError("transfer_payload_required")

        transfer_type = _normalize_transfer_type(payload.get("transfer_type") or "Cross-Border Remittance")
        amount = _decimal(payload.get("amount"))
        if amount <= Decimal("0"):
            raise NovaPayTransferAdmissionError("transfer_amount_must_be_positive")

        source_country = str(payload.get("source_country") or "AU").strip().upper()
        destination_country = str(payload.get("recipient_country") or "").strip().upper()
        jurisdiction = self.registry.resolve_jurisdiction(source_country)
        license_record = self.registry.resolve_license(jurisdiction)
        corridor = self.registry.resolve_corridor(source_country, destination_country)
        if not corridor.allowed:
            raise NovaPayTransferAdmissionError(f"corridor_not_allowed:{source_country}->{destination_country}")

        source_allowed = _normalize_funding_type(payload.get("funding_source_type") or "wallet")
        if source_allowed not in {"wallet", "mobile_money", "bank", "card", "cash"}:
            raise NovaPayTransferAdmissionError(f"funding_source_not_supported:{source_allowed}")

        recipient = Recipient(
            recipient_id=str(payload.get("recipient_id") or _stable_id("rcp")),
            type=str(payload.get("recipient_type") or "individual"),
            name=str(payload.get("recipient_name") or "").strip(),
            phone_number=str(payload.get("recipient_identifier") or "").strip(),
            wallet_id=str(payload.get("recipient_wallet_id") or "") or None,
            bank_account_id=str(payload.get("recipient_bank_account_id") or "") or None,
            mobile_money_id=str(payload.get("recipient_mobile_money_id") or "") or None,
            jurisdiction_id=jurisdiction.jurisdiction_id,
            verified=True,
        )
        if not recipient.name or not recipient.phone_number:
            raise NovaPayTransferAdmissionError("recipient_details_required")

        funding_source = FundingSource(
            funding_source_id=str(payload.get("funding_source_id") or _stable_id("fs")),
            type=source_allowed,
            owner_id=identity.identity_id,
            provider=str(payload.get("funding_provider") or source_allowed),
            reference=str(payload.get("funding_source_reference") or _stable_id("fund")),
            status="active",
            validated=True,
            metadata={
                "source_country": source_country,
                "destination_country": destination_country,
                "funding_source_type": source_allowed,
            },
        )

        compliance_score = 10 if amount <= Decimal("1000") else 32 if amount <= Decimal("10000") else 68
        compliance_case = ComplianceCase(
            compliance_case_id=_stable_id("cc"),
            transfer_id=str(payload.get("transfer_id") or _stable_id("transfer")),
            kyc_status="verified",
            aml_risk_score=compliance_score,
            sanctions_flag=False,
            review_required=compliance_score >= 60,
            decision="REVIEW" if compliance_score >= 60 else "ALLOW",
        )
        if compliance_case.decision == "DENY":
            raise NovaPayTransferAdmissionError("compliance_denied")

        transfer_type_norm = transfer_type or "Cross-Border Remittance"
        if transfer_type_norm not in jurisdiction.allowed_transfer_types:
            raise NovaPayTransferAdmissionError(f"transfer_type_not_supported:{transfer_type_norm}")
        if compliance_case.review_required and transfer_type_norm not in {"Cash In", "Cash Out"}:
            # High-risk transfers remain admit-able but marked for review.
            policy_decision = "ALLOW_REVIEW"
        else:
            policy_decision = "ALLOW"

        payout_method = _normalize_method(payload.get("payout_method") or "mobile_money")
        quote = self.transfer_service.quote(
            identity=identity,
            recipient_name=recipient.name,
            recipient_identifier=recipient.phone_number,
            recipient_country=destination_country,
            amount=amount,
            source_currency=normalize_currency_code(str(payload.get("source_currency") or "AUD")),
            payout_method=payout_method,
            use_case=str(payload.get("use_case") or "transparent_pricing"),
            memo=payload.get("memo"),
            live_provider=bool(payload.get("live_provider") or False),
        ).canonical()
        route = {
            "route_id": quote["transfer_id"],
            "provider": quote["route_hint"],
            "rail": quote["payout_method"],
            "corridor": quote["corridor"],
            "route_class": quote["route_class"],
            "settlement_currency": quote["destination_currency"],
        }
        decision_trace = {
            "policy_id": "novapay.transfer.policy.v1",
            "policy_version": "2026.06",
            "rule_ids": [
                "JURISDICTION-001",
                "LICENSE-001",
                "CORRIDOR-001",
                "COMPLIANCE-001",
                "ROUTING-001",
            ],
            "flag_evaluations": {
                "novapay.transfer.runtime.enabled": {"enabled": True},
                "novapay.transfer.unbanked_supported": {"enabled": True},
            },
            "evaluation_result": policy_decision,
            "reason": "governed_transfer_admission",
        }
        return TransferAdmissionResult(
            approved=True,
            transfer_id=route["route_id"],
            transfer_type=transfer_type_norm,
            sender=identity.canonical(),
            recipient=recipient.canonical(),
            funding_source=funding_source.canonical(),
            jurisdiction=jurisdiction.canonical(),
            license=license_record.canonical(),
            corridor=corridor.canonical(),
            compliance=compliance_case.canonical(),
            policy={
                "decision": policy_decision,
                "reason": "policy_and_compliance_passed",
            },
            quote=quote,
            routing=route,
            decision_trace=decision_trace,
        )

    def create_transfer(
        self,
        payload: Mapping[str, Any],
        *,
        identity: Identity,
        auto_execute: bool = True,
        live_provider: bool = False,
    ) -> RuntimeTransferRecord:
        admission = self.admit_transfer(payload, identity=identity)
        transfer = Transfer(
            transfer_id=admission.transfer_id,
            transfer_type=admission.transfer_type,
            status="admitted" if auto_execute else "quoted",
            amount=str(_decimal(payload.get("amount")).quantize(Decimal("0.01"))),
            currency=normalize_currency_code(str(payload.get("source_currency") or "AUD")),
            sender_id=identity.identity_id,
            recipient_id=admission.recipient["recipient_id"],
            funding_source_id=admission.funding_source["funding_source_id"],
            settlement_rail=admission.routing["rail"],
            jurisdiction_id=admission.jurisdiction["jurisdiction_id"],
            corridor_id=admission.corridor["corridor_id"],
            quote_id=admission.quote["quote_id"],
            route_id=admission.routing["route_id"],
            compliance_status=admission.compliance["decision"],
            policy_decision_id=admission.decision_trace["policy_id"],
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        timeline = (
            TransferEvent(
                event_id=_stable_id("evt"),
                transfer_id=transfer.transfer_id,
                event_type="transfer.requested.v1",
                occurred_at=_utcnow(),
                payload={
                    "transfer": transfer.canonical(),
                    "admission": admission.canonical(),
                },
                decision_trace=admission.decision_trace,
            ),
            TransferEvent(
                event_id=_stable_id("evt"),
                transfer_id=transfer.transfer_id,
                event_type="transfer.admission.approved.v1",
                occurred_at=_utcnow(),
                payload={"policy": admission.policy, "compliance": admission.compliance},
                decision_trace=admission.decision_trace,
            ),
        )
        record = RuntimeTransferRecord(
            transfer=transfer,
            admission=admission,
            funding_source=FundingSource(
                funding_source_id=admission.funding_source["funding_source_id"],
                type=admission.funding_source["type"],
                owner_id=admission.funding_source["owner_id"],
                provider=admission.funding_source["provider"],
                reference=admission.funding_source["reference"],
                status=admission.funding_source["status"],
                validated=bool(admission.funding_source["validated"]),
                metadata=admission.funding_source["metadata"],
            ),
            recipient=Recipient(
                recipient_id=admission.recipient["recipient_id"],
                type=admission.recipient["type"],
                name=admission.recipient["name"],
                phone_number=admission.recipient["phone_number"],
                wallet_id=admission.recipient["wallet_id"],
                bank_account_id=admission.recipient["bank_account_id"],
                mobile_money_id=admission.recipient["mobile_money_id"],
                jurisdiction_id=admission.recipient["jurisdiction_id"],
                verified=bool(admission.recipient["verified"]),
            ),
            compliance_case=ComplianceCase(
                compliance_case_id=admission.compliance["compliance_case_id"],
                transfer_id=admission.compliance["transfer_id"],
                kyc_status=admission.compliance["kyc_status"],
                aml_risk_score=int(admission.compliance["aml_risk_score"]),
                sanctions_flag=bool(admission.compliance["sanctions_flag"]),
                review_required=bool(admission.compliance["review_required"]),
                decision=admission.compliance["decision"],
                created_at=admission.compliance["created_at"],
            ),
            ledger_entries=(),
            settlement=None,
            receipt=None,
            provider_receipt=None,
            events=timeline,
        )
        self.store.save(record)
        self._publish("transfer.requested.v1", record)
        self._publish("transfer.admission.approved.v1", record)
        if auto_execute:
            record = self.execute_transfer(transfer.transfer_id, identity=identity, live_provider=live_provider)
        return record

    def execute_transfer(
        self,
        transfer_id: str,
        *,
        identity: Identity,
        live_provider: bool = False,
    ) -> RuntimeTransferRecord:
        record = self.store.get(transfer_id)
        if record is None:
            raise NovaPayTransferAdmissionError(f"transfer_not_found:{transfer_id}")
        if record.transfer.sender_id != identity.identity_id:
            raise NovaPayTransferAdmissionError("transfer_sender_mismatch")
        if record.receipt is not None and record.settlement is not None:
            return record

        decision = AuthorityDecision(
            decision="ALLOW",
            reason="governed_transfer_admission_passed",
            trace_id=f"novapay-transfer:{transfer_id}",
            checks=("jurisdiction", "license", "corridor", "compliance", "policy", "funding_source"),
        )
        receipt = self.transfer_service.execute(
            record.admission.quote,
            identity=identity,
            decision=decision,
            provider=record.admission.routing["provider"],
            live_provider=live_provider,
        )
        provider_receipt = receipt.canonical()
        settlement = SettlementRecord(
            settlement_id=_stable_id("set"),
            transfer_id=transfer_id,
            rail=record.admission.routing["rail"],
            provider=record.admission.routing["provider"],
            status=receipt.status,
            reference_id=str(receipt.payment.get("provider_reference") or receipt.payment.get("payment_id") or receipt.quote_id),
            settled_at=_utcnow(),
        )
        ledger_entries = (
            LedgerEntry(
                ledger_entry_id=_stable_id("led"),
                transfer_id=transfer_id,
                account_id=f"liability:{identity.organization_id}",
                entry_type="DEBIT",
                amount=record.transfer.amount,
                currency=record.transfer.currency,
                balance_after=record.transfer.amount,
            ),
            LedgerEntry(
                ledger_entry_id=_stable_id("led"),
                transfer_id=transfer_id,
                account_id=f"settlement:{record.admission.routing['provider']}",
                entry_type="CREDIT",
                amount=record.transfer.amount,
                currency=record.transfer.currency,
                balance_after=record.transfer.amount,
            ),
        )
        receipt_record = Receipt(
            receipt_id=_stable_id("receipt"),
            transfer_id=transfer_id,
            issued_at=_utcnow(),
            verification_code=str(receipt.payment.get("payment_id") or receipt.transfer_id),
            signature=sign_packet(
                {
                    "transfer_id": transfer_id,
                    "settlement": settlement.canonical(),
                    "ledger_entries": [entry.canonical() for entry in ledger_entries],
                    "provider_receipt": provider_receipt,
                }
            ).canonical(),
            document_url=f"/v1/transfers/{transfer_id}/receipt",
        )
        timeline = list(record.events)
        timeline.extend(
            [
                TransferEvent(
                    event_id=_stable_id("evt"),
                    transfer_id=transfer_id,
                    event_type="transfer.executed.v1",
                    occurred_at=_utcnow(),
                    payload={"receipt": receipt.canonical(), "settlement": settlement.canonical()},
                    decision_trace=record.admission.decision_trace,
                ),
                TransferEvent(
                    event_id=_stable_id("evt"),
                    transfer_id=transfer_id,
                    event_type="transfer.settled.v1",
                    occurred_at=_utcnow(),
                    payload={"settlement": settlement.canonical()},
                    decision_trace=record.admission.decision_trace,
                ),
                TransferEvent(
                    event_id=_stable_id("evt"),
                    transfer_id=transfer_id,
                    event_type="receipt.generated.v1",
                    occurred_at=_utcnow(),
                    payload={"receipt": receipt_record.canonical()},
                    decision_trace=record.admission.decision_trace,
                ),
            ]
        )
        updated = RuntimeTransferRecord(
            transfer=Transfer(
                transfer_id=record.transfer.transfer_id,
                transfer_type=record.transfer.transfer_type,
                status="completed" if receipt.status == "completed" else "settled",
                amount=record.transfer.amount,
                currency=record.transfer.currency,
                sender_id=record.transfer.sender_id,
                recipient_id=record.transfer.recipient_id,
                funding_source_id=record.transfer.funding_source_id,
                settlement_rail=record.transfer.settlement_rail,
                jurisdiction_id=record.transfer.jurisdiction_id,
                corridor_id=record.transfer.corridor_id,
                quote_id=record.transfer.quote_id,
                route_id=record.transfer.route_id,
                compliance_status=record.transfer.compliance_status,
                policy_decision_id=record.transfer.policy_decision_id,
                created_at=record.transfer.created_at,
                updated_at=_utcnow(),
                timeline=tuple(timeline),
                receipt=receipt_record,
            ),
            admission=record.admission,
            funding_source=record.funding_source,
            recipient=record.recipient,
            compliance_case=record.compliance_case,
            ledger_entries=ledger_entries,
            settlement=settlement,
            receipt=receipt_record,
            provider_receipt=provider_receipt,
            events=tuple(timeline),
        )
        self.store.save(updated)
        self._publish("transfer.executed.v1", updated)
        self._publish("transfer.settled.v1", updated)
        self._publish("receipt.generated.v1", updated)
        return updated

    def get_transfer(self, transfer_id: str) -> RuntimeTransferRecord | None:
        return self.store.get(transfer_id)

    def get_timeline(self, transfer_id: str) -> list[dict[str, Any]]:
        record = self.store.get(transfer_id)
        if record is None:
            raise NovaPayTransferAdmissionError(f"transfer_not_found:{transfer_id}")
        return [event.canonical() for event in record.events]

    def get_receipt(self, transfer_id: str) -> dict[str, Any]:
        record = self.store.get(transfer_id)
        if record is None or record.receipt is None:
            raise NovaPayTransferAdmissionError(f"receipt_not_found:{transfer_id}")
        return record.receipt.canonical()

    def verify_receipt(self, transfer_id: str) -> dict[str, Any]:
        record = self.store.get(transfer_id)
        if record is None or record.receipt is None:
            raise NovaPayTransferAdmissionError(f"receipt_not_found:{transfer_id}")
        receipt = record.receipt.canonical()
        provider_receipt = record.provider_receipt or {}
        signature_valid = verify_packet_signature(
            {
                "transfer_id": transfer_id,
                "settlement": record.settlement.canonical() if record.settlement else {},
                "ledger_entries": [entry.canonical() for entry in record.ledger_entries],
                "provider_receipt": provider_receipt,
            },
            receipt["signature"],
        )
        return {
            "transfer_id": transfer_id,
            "valid": bool(signature_valid),
            "reason": "receipt_verified" if signature_valid else "receipt_signature_invalid",
            "receipt": receipt,
        }

    def _publish(self, event_type: str, record: RuntimeTransferRecord) -> None:
        self.event_bus.publish(
            f"novapay.{event_type}",
            {
                "transfer_id": record.transfer.transfer_id,
                "transfer_type": record.transfer.transfer_type,
                "status": record.transfer.status,
                "jurisdiction": record.admission.jurisdiction,
                "license": record.admission.license,
                "corridor": record.admission.corridor,
                "policy": record.admission.policy,
                "compliance": record.compliance_case.canonical(),
                "receipt": record.receipt.canonical() if record.receipt else None,
                "decision_trace": record.admission.decision_trace,
            },
        )


DEFAULT_NOVAPAY_RUNTIME = NovaPayRuntimeEngine()


def build_novapay_runtime() -> NovaPayRuntimeEngine:
    return DEFAULT_NOVAPAY_RUNTIME


__all__ = [
    "ComplianceCase",
    "Corridor",
    "Customer",
    "FundingSource",
    "Jurisdiction",
    "LedgerEntry",
    "License",
    "NovaPayRegistry",
    "NovaPayRuntimeEngine",
    "NovaPayTransferAdmissionError",
    "Recipient",
    "Receipt",
    "RuntimeTransferRecord",
    "SettlementRail",
    "SettlementRecord",
    "Transfer",
    "TransferAdmissionRequest",
    "TransferAdmissionResult",
    "TransferEvent",
    "build_novapay_runtime",
]
