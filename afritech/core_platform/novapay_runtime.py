"""Governed NovaPay transfer runtime.

This module introduces the next-generation NovaPay runtime model centered on a
single Transfer aggregate, with jurisdiction, licensing, corridor, compliance,
policy, routing, ledger, settlement, and receipt as distinct runtime domains.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from threading import RLock
from typing import Any, Mapping
from uuid import uuid4

from afritech.core_platform.canonical import hash_obj
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


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


EXPECTED_TRANSFER_EVENT_SEQUENCE = (
    "transfer.requested.v1",
    "transfer.admission.approved.v1",
    "transfer.executed.v1",
    "transfer.settled.v1",
    "receipt.generated.v1",
)
GENESIS_HASH = "0" * 64
AUDIT_PACKAGE_SCHEMA = "novapay.audit_package.v1"
CANONICAL_FORMAT = "canonical.v1"
HASH_DOMAIN_VERSION = 1
HASH_ALGORITHM = "sha256"
TRANSFER_STATE_MACHINE = {
    None: ("requested",),
    "requested": ("admission.approved", "admission.rejected"),
    "admission.approved": ("executed", "cancelled"),
    "executed": ("settled", "execution.failed"),
    "settled": ("receipt.generated",),
    "receipt.generated": (),
    "admission.rejected": (),
    "cancelled": (),
    "execution.failed": (),
}
MANDATORY_PREVIOUS_STATES = {
    "admission.approved": "requested",
    "executed": "admission.approved",
    "settled": "executed",
    "receipt.generated": "settled",
}
EVENT_STATE_MAP = {
    "transfer.requested.v1": "requested",
    "transfer.admission.approved.v1": "admission.approved",
    "transfer.admission.rejected.v1": "admission.rejected",
    "transfer.cancelled.v1": "cancelled",
    "transfer.executed.v1": "executed",
    "transfer.execution.failed.v1": "execution.failed",
    "transfer.settled.v1": "settled",
    "receipt.generated.v1": "receipt.generated",
}
EVENT_SCHEMA_REGISTRY = {
    event_type: frozenset({1})
    for event_type in EVENT_STATE_MAP
}
STATE_CHANGING_EVENTS = frozenset(EVENT_STATE_MAP)


def _merkle_parent(left: str, right: str) -> str:
    return hash_obj({"left": left, "right": right}, domain=HASH_DOMAINS["MERKLE_ROOT"])


def _merkle_root_from_hashes(hashes: list[str]) -> str:
    if not hashes:
        return hash_obj({"leaves": []}, domain=HASH_DOMAINS["MERKLE_ROOT"])
    level = list(hashes)
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(_merkle_parent(left, right))
        level = next_level
    return level[0]


def _merkle_proof_from_hashes(hashes: list[str], leaf_index: int) -> dict[str, Any]:
    if not hashes:
        raise NovaPayTransferAdmissionError("merkle_proof_empty")
    if leaf_index < 0 or leaf_index >= len(hashes):
        raise NovaPayTransferAdmissionError("merkle_proof_index_out_of_range")
    proof: list[dict[str, str]] = []
    index = leaf_index
    level = list(hashes)
    while len(level) > 1:
        sibling_index = index + 1 if index % 2 == 0 else index - 1
        if sibling_index >= len(level):
            sibling_index = index
        proof.append(
            {
                "position": "right" if index % 2 == 0 else "left",
                "hash": level[sibling_index],
            }
        )
        next_level: list[str] = []
        for level_index in range(0, len(level), 2):
            left = level[level_index]
            right = level[level_index + 1] if level_index + 1 < len(level) else left
            next_level.append(_merkle_parent(left, right))
        index //= 2
        level = next_level
    return {"leaf_index": leaf_index, "path": proof}


def _verify_merkle_proof(leaf_hash: str, proof: Mapping[str, Any], root_hash: str) -> bool:
    current = leaf_hash
    for step in proof.get("path") or []:
        sibling = str(step.get("hash"))
        if step.get("position") == "left":
            current = _merkle_parent(sibling, current)
        elif step.get("position") == "right":
            current = _merkle_parent(current, sibling)
        else:
            return False
    return current == root_hash
SNAPSHOT_INTERVAL = 100


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
    per_transfer_limit: str = "10000"
    allowed_transfer_types: tuple[str, ...] = field(default_factory=tuple)
    allowed_corridors: tuple[str, ...] = field(default_factory=tuple)

    def canonical(self) -> dict[str, Any]:
        return {
            "license_id": self.license_id,
            "jurisdiction_id": self.jurisdiction_id,
            "license_type": self.license_type,
            "entity_name": self.entity_name,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "status": self.status,
            "per_transfer_limit": self.per_transfer_limit,
            "allowed_transfer_types": list(self.allowed_transfer_types),
            "allowed_corridors": list(self.allowed_corridors),
        }


@dataclass(frozen=True)
class PolicyVersion:
    policy_id: str
    version: str
    effective_from: str
    effective_to: str | None
    rules: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "rules": list(self.rules),
        }


@dataclass(frozen=True)
class Region:
    region_id: str
    jurisdiction: str
    data_residency_rules: tuple[str, ...]
    failover_region_id: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "jurisdiction": self.jurisdiction,
            "data_residency_rules": list(self.data_residency_rules),
            "failover_region_id": self.failover_region_id,
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

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LedgerEntry":
        return cls(
            ledger_entry_id=str(payload["ledger_entry_id"]),
            transfer_id=str(payload["transfer_id"]),
            account_id=str(payload["account_id"]),
            entry_type=str(payload["entry_type"]),
            amount=str(_decimal(payload["amount"])),
            currency=str(payload["currency"]),
            balance_after=str(_decimal(payload["balance_after"])),
            created_at=str(payload.get("created_at") or _utcnow()),
        )


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
    sequence: int = 0
    schema_version: int = 1
    aggregate_version: int = 0
    previous_event_hash: str = GENESIS_HASH
    event_hash: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "transfer_id": self.transfer_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "sequence": self.sequence,
            "schema_version": self.schema_version,
            "aggregate_version": self.aggregate_version,
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
            "payload": dict(self.payload),
            "decision_trace": dict(self.decision_trace),
        }

    def commitment_payload(self) -> dict[str, Any]:
        payload = self.canonical()
        payload.pop("event_hash", None)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TransferEvent":
        return cls(
            event_id=str(payload["event_id"]),
            transfer_id=str(payload["transfer_id"]),
            event_type=str(payload["event_type"]),
            occurred_at=str(payload["occurred_at"]),
            payload=dict(payload.get("payload") or {}),
            decision_trace=dict(payload.get("decision_trace") or {}),
            sequence=int(payload.get("sequence") or 0),
            schema_version=int(payload.get("schema_version") or 1),
            aggregate_version=int(payload.get("aggregate_version") or 0),
            previous_event_hash=str(payload.get("previous_event_hash") or GENESIS_HASH),
            event_hash=str(payload.get("event_hash") or ""),
        )


@dataclass(frozen=True)
class OutboxRecord:
    outbox_id: str
    event_type: str
    aggregate_id: str
    aggregate_version: int
    payload_json: dict[str, Any]
    payload_hash: str
    status: str = "pending"
    retry_count: int = 0
    created_at: str = field(default_factory=_utcnow)
    published_at: str | None = None
    failed_at: str | None = None
    last_error: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "outbox_id": self.outbox_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_version": self.aggregate_version,
            "payload_json": dict(self.payload_json),
            "payload_hash": self.payload_hash,
            "status": self.status,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "published_at": self.published_at,
            "failed_at": self.failed_at,
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class TransferSnapshot:
    snapshot_id: str
    transfer_id: str
    version: int
    state: dict[str, Any]
    ledger_hash: str
    event_hash: str
    snapshot_root_hash: str
    created_at: str = field(default_factory=_utcnow)

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "transfer_id": self.transfer_id,
            "version": self.version,
            "state": dict(self.state),
            "ledger_hash": self.ledger_hash,
            "event_hash": self.event_hash,
            "snapshot_root_hash": self.snapshot_root_hash,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class Account:
    account_id: str
    account_type: str
    owner_id: str | None
    currency: str
    status: str = "active"

    def canonical(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_type": self.account_type,
            "owner_id": self.owner_id,
            "currency": self.currency,
            "status": self.status,
        }


@dataclass(frozen=True)
class JournalLine:
    journal_line_id: str
    account_id: str
    direction: str
    amount: str
    currency: str
    balance_after: str
    created_at: str = field(default_factory=_utcnow)

    def canonical(self) -> dict[str, Any]:
        return {
            "journal_line_id": self.journal_line_id,
            "account_id": self.account_id,
            "direction": self.direction,
            "amount": self.amount,
            "currency": self.currency,
            "balance_after": self.balance_after,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "JournalLine":
        return cls(
            journal_line_id=str(payload["journal_line_id"]),
            account_id=str(payload["account_id"]),
            direction=str(payload["direction"]),
            amount=str(_decimal(payload["amount"])),
            currency=str(payload["currency"]),
            balance_after=str(_decimal(payload["balance_after"])),
            created_at=str(payload.get("created_at") or _utcnow()),
        )


@dataclass(frozen=True)
class JournalEntry:
    journal_id: str
    transfer_id: str
    policy_version_used: str
    total_debit: str
    total_credit: str
    created_at: str
    lines: tuple[JournalLine, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "journal_id": self.journal_id,
            "transfer_id": self.transfer_id,
            "policy_version_used": self.policy_version_used,
            "total_debit": self.total_debit,
            "total_credit": self.total_credit,
            "created_at": self.created_at,
            "lines": [line.canonical() for line in self.lines],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "JournalEntry":
        return cls(
            journal_id=str(payload["journal_id"]),
            transfer_id=str(payload["transfer_id"]),
            policy_version_used=str(payload["policy_version_used"]),
            total_debit=str(_decimal(payload["total_debit"])),
            total_credit=str(_decimal(payload["total_credit"])),
            created_at=str(payload["created_at"]),
            lines=tuple(JournalLine.from_dict(item) for item in payload.get("lines", ())),
        )


@dataclass(frozen=True)
class LiquidityPosition:
    corridor_id: str
    currency: str
    available_balance: str
    reserved_balance: str
    updated_at: str = field(default_factory=_utcnow)

    def canonical(self) -> dict[str, Any]:
        return {
            "corridor_id": self.corridor_id,
            "currency": self.currency,
            "available_balance": self.available_balance,
            "reserved_balance": self.reserved_balance,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class PrefundingAccount:
    prefunding_account_id: str
    provider: str
    currency: str
    required_balance: str
    current_balance: str
    status: str = "healthy"

    def canonical(self) -> dict[str, Any]:
        return {
            "prefunding_account_id": self.prefunding_account_id,
            "provider": self.provider,
            "currency": self.currency,
            "required_balance": self.required_balance,
            "current_balance": self.current_balance,
            "status": self.status,
        }


@dataclass(frozen=True)
class SettlementExposure:
    exposure_id: str
    transfer_id: str
    corridor_id: str
    currency: str
    amount_pending: str
    expected_settlement_date: str
    status: str = "pending"

    def canonical(self) -> dict[str, Any]:
        return {
            "exposure_id": self.exposure_id,
            "transfer_id": self.transfer_id,
            "corridor_id": self.corridor_id,
            "currency": self.currency,
            "amount_pending": self.amount_pending,
            "expected_settlement_date": self.expected_settlement_date,
            "status": self.status,
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
    policy_version_used: str
    created_at: str
    updated_at: str
    timeline: tuple[TransferEvent, ...] = field(default_factory=tuple)
    receipt: Receipt | None = None
    aggregate_version: int = 0

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
            "policy_version_used": self.policy_version_used,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "timeline": [event.canonical() for event in self.timeline],
            "receipt": self.receipt.canonical() if self.receipt else None,
            "aggregate_version": self.aggregate_version,
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
    journal_entry: JournalEntry | None
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
            "journal_entry": self.journal_entry.canonical() if self.journal_entry else None,
            "ledger_entries": [entry.canonical() for entry in self.ledger_entries],
            "settlement": self.settlement.canonical() if self.settlement else None,
            "receipt": self.receipt.canonical() if self.receipt else None,
            "provider_receipt": dict(self.provider_receipt) if self.provider_receipt else None,
            "events": [event.canonical() for event in self.events],
        }


@dataclass(frozen=True)
class ReplayState:
    transfer_id: str
    replay_hash: str
    replay_valid: bool
    transfer: dict[str, Any] | None
    admission: dict[str, Any] | None
    journal_entry: JournalEntry | None
    ledger_entries: list[LedgerEntry]
    settlement: dict[str, Any] | None
    receipt: dict[str, Any] | None
    policy: dict[str, Any] | None
    snapshot: dict[str, Any] | None
    events: list[dict[str, Any]]

    def canonical(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "replay_hash": self.replay_hash,
            "replay_valid": self.replay_valid,
            "transfer": self.transfer,
            "admission": self.admission,
            "journal_entry": self.journal_entry.canonical() if self.journal_entry else None,
            "ledger_entries": [entry.canonical() for entry in self.ledger_entries],
            "settlement": self.settlement,
            "receipt": self.receipt,
            "policy": self.policy,
            "snapshot": self.snapshot,
            "events": list(self.events),
        }


class NovaPayTransferAdmissionError(ValueError):
    """Raised when the governed admission pipeline rejects a transfer."""


class NovaPayRegistry:
    """Static jurisdiction, license, and corridor registry."""

    def __init__(self) -> None:
        self._jurisdictions = self._seed_jurisdictions()
        self._licenses = self._seed_licenses()
        self._corridors = self._seed_corridors()
        self._policies = self._seed_policies()
        self._regions = self._seed_regions()

    def jurisdictions(self) -> tuple[Jurisdiction, ...]:
        return tuple(self._jurisdictions)

    def licenses(self) -> tuple[License, ...]:
        return tuple(self._licenses)

    def corridors(self) -> tuple[Corridor, ...]:
        return tuple(self._corridors)

    def policies(self) -> tuple[PolicyVersion, ...]:
        return tuple(self._policies)

    def regions(self) -> tuple[Region, ...]:
        return tuple(self._regions)

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

    def license_allows(
        self,
        license_record: License,
        *,
        transfer_type: str,
        amount: Decimal,
        corridor: "Corridor",
    ) -> None:
        if license_record.status != "active":
            raise NovaPayTransferAdmissionError(f"license_not_active:{license_record.license_id}")
        if amount > _decimal(license_record.per_transfer_limit):
            raise NovaPayTransferAdmissionError(f"license_transfer_limit_exceeded:{license_record.license_id}")
        if license_record.allowed_transfer_types and transfer_type not in license_record.allowed_transfer_types:
            raise NovaPayTransferAdmissionError(f"license_transfer_type_not_allowed:{transfer_type}")
        if license_record.allowed_corridors and corridor.corridor_id not in license_record.allowed_corridors:
            raise NovaPayTransferAdmissionError(f"license_corridor_not_allowed:{corridor.corridor_id}")

    def active_policy(self) -> PolicyVersion:
        return self._policies[-1]

    def resolve_policy(self, policy_id: str, version: str) -> PolicyVersion:
        for policy in self._policies:
            if policy.policy_id == policy_id and policy.version == version:
                return policy
        raise NovaPayTransferAdmissionError(f"policy_version_not_found:{policy_id}:{version}")

    def resolve_region(self, country_code: str) -> Region:
        normalized = str(country_code or "").strip().upper()
        for region in self._regions:
            if region.jurisdiction == normalized:
                return region
        raise NovaPayTransferAdmissionError(f"region_not_configured:{normalized}")

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
                per_transfer_limit="10000",
                allowed_transfer_types=("Cross-Border Remittance", "Wallet Transfer", "Merchant Payment", "Refund"),
                allowed_corridors=("corr_au_ke", "corr_au_bi", "corr_au_cd"),
            ),
            License(
                license_id="lic_us_remittance",
                jurisdiction_id="jur_us",
                license_type="money_service_business",
                entity_name="NovaPay US",
                valid_from=now,
                valid_to=expires,
                per_transfer_limit="10000",
                allowed_transfer_types=("Cross-Border Remittance", "Wallet Transfer", "Merchant Payment", "Refund"),
                allowed_corridors=("corr_us_ke",),
            ),
            License(
                license_id="lic_ke_partner",
                jurisdiction_id="jur_ke",
                license_type="partner_remittance",
                entity_name="NovaPay Kenya Partner",
                valid_from=now,
                valid_to=expires,
                per_transfer_limit="50000",
                allowed_transfer_types=("Domestic Transfer", "Wallet Transfer", "Merchant Payment", "Cash In", "Cash Out"),
                allowed_corridors=("corr_ke_ke",),
            ),
            License(
                license_id="lic_bi_partner",
                jurisdiction_id="jur_bi",
                license_type="partner_remittance",
                entity_name="NovaPay Burundi Partner",
                valid_from=now,
                valid_to=expires,
                per_transfer_limit="10000",
                allowed_transfer_types=("Cross-Border Remittance", "Wallet Transfer"),
            ),
            License(
                license_id="lic_cd_partner",
                jurisdiction_id="jur_cd",
                license_type="partner_remittance",
                entity_name="NovaPay DRC Partner",
                valid_from=now,
                valid_to=expires,
                per_transfer_limit="10000",
                allowed_transfer_types=("Cross-Border Remittance", "Wallet Transfer"),
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

    def _seed_policies(self) -> list[PolicyVersion]:
        return [
            PolicyVersion(
                policy_id="novapay.transfer.policy.v1",
                version="2026.06",
                effective_from="2026-06-01T00:00:00Z",
                effective_to=None,
                rules=(
                    "JURISDICTION-001",
                    "LICENSE-EXEC-001",
                    "CORRIDOR-001",
                    "COMPLIANCE-001",
                    "LIQUIDITY-001",
                    "ROUTING-SCORE-001",
                    "SOVEREIGN-REGION-001",
                    "LEDGER-BALANCE-001",
                ),
            )
        ]

    def _seed_regions(self) -> list[Region]:
        return [
            Region("region_au", "AU", ("au_pii_primary", "cross_border_receipt_hash_only"), "region_us"),
            Region("region_us", "US", ("us_msb_records_primary", "cross_border_receipt_hash_only"), "region_au"),
            Region("region_ke", "KE", ("east_africa_local_records", "regulated_export_by_proof"), None),
            Region("region_bi", "BI", ("east_africa_local_records", "regulated_export_by_proof"), None),
            Region("region_cd", "CD", ("central_africa_local_records", "regulated_export_by_proof"), None),
        ]


class InMemoryNovaPayRuntimeStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self.records: dict[str, RuntimeTransferRecord] = {}
        self.events: dict[str, list[TransferEvent]] = {}
        self.accounts: dict[str, Account] = {}
        self.journals: dict[str, JournalEntry] = {}
        self.liquidity_positions: dict[str, LiquidityPosition] = {}
        self.prefunding_accounts: dict[str, PrefundingAccount] = {}
        self.settlement_exposures: dict[str, SettlementExposure] = {}
        self.outbox: list[OutboxRecord] = []
        self.snapshots: dict[str, list[TransferSnapshot]] = {}

    @contextmanager
    def read_snapshot(self) -> Any:
        with self._lock:
            yield

    def save(self, record: RuntimeTransferRecord) -> None:
        with self._lock:
            self.records[record.transfer.transfer_id] = record
            self.events[record.transfer.transfer_id] = list(record.events)

    def get(self, transfer_id: str) -> RuntimeTransferRecord | None:
        with self._lock:
            return self.records.get(transfer_id)

    def append_event(self, transfer_id: str, event: TransferEvent) -> None:
        with self._lock:
            self.events.setdefault(transfer_id, []).append(event)
            record = self.records.get(transfer_id)
            if record is not None:
                self.records[transfer_id] = RuntimeTransferRecord(
                    transfer=record.transfer,
                    admission=record.admission,
                    funding_source=record.funding_source,
                    recipient=record.recipient,
                    compliance_case=record.compliance_case,
                    journal_entry=record.journal_entry,
                    ledger_entries=record.ledger_entries,
                    settlement=record.settlement,
                    receipt=record.receipt,
                    provider_receipt=record.provider_receipt,
                    events=tuple(self.events[transfer_id]),
                )

    def append_outbox(self, record: OutboxRecord) -> None:
        with self._lock:
            self.outbox.append(record)

    def mark_outbox_published(self, outbox_id: str) -> None:
        with self._lock:
            self.outbox = [
                OutboxRecord(
                    outbox_id=record.outbox_id,
                    event_type=record.event_type,
                    aggregate_id=record.aggregate_id,
                    aggregate_version=record.aggregate_version,
                    payload_hash=record.payload_hash,
                    payload_json=record.payload_json,
                    status="published",
                    retry_count=record.retry_count,
                    created_at=record.created_at,
                    published_at=_utcnow(),
                    failed_at=record.failed_at,
                    last_error=record.last_error,
                )
                if record.outbox_id == outbox_id
                else record
                for record in self.outbox
            ]

    def mark_outbox_failed(self, outbox_id: str, error: str) -> None:
        with self._lock:
            self.outbox = [
                OutboxRecord(
                    outbox_id=record.outbox_id,
                    event_type=record.event_type,
                    aggregate_id=record.aggregate_id,
                    aggregate_version=record.aggregate_version,
                    payload_json=record.payload_json,
                    payload_hash=record.payload_hash,
                    status="failed",
                    retry_count=record.retry_count + 1,
                    created_at=record.created_at,
                    published_at=record.published_at,
                    failed_at=_utcnow(),
                    last_error=error,
                )
                if record.outbox_id == outbox_id
                else record
                for record in self.outbox
            ]

    def save_snapshot(self, snapshot: TransferSnapshot) -> None:
        with self._lock:
            self.snapshots.setdefault(snapshot.transfer_id, []).append(snapshot)

    def latest_snapshot(self, transfer_id: str) -> TransferSnapshot | None:
        with self._lock:
            snapshots = self.snapshots.get(transfer_id) or []
            if not snapshots:
                return None
            return max(snapshots, key=lambda snapshot: snapshot.version)


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
        self._seed_treasury_state()

    def build_jurisdictions(self) -> list[dict[str, Any]]:
        return [jurisdiction.canonical() for jurisdiction in self.registry.jurisdictions()]

    def build_licenses(self) -> list[dict[str, Any]]:
        return [license_record.canonical() for license_record in self.registry.licenses()]

    def build_corridors(self) -> list[dict[str, Any]]:
        return [corridor.canonical() for corridor in self.registry.corridors()]

    def build_policies(self) -> list[dict[str, Any]]:
        return [policy.canonical() for policy in self.registry.policies()]

    def build_regions(self) -> list[dict[str, Any]]:
        return [region.canonical() for region in self.registry.regions()]

    def build_accounts(self) -> list[dict[str, Any]]:
        return [account.canonical() for account in self.store.accounts.values()]

    def build_liquidity_positions(self) -> list[dict[str, Any]]:
        return [position.canonical() for position in self.store.liquidity_positions.values()]

    def build_prefunding_accounts(self) -> list[dict[str, Any]]:
        return [account.canonical() for account in self.store.prefunding_accounts.values()]

    def build_settlement_exposures(self) -> list[dict[str, Any]]:
        return [exposure.canonical() for exposure in self.store.settlement_exposures.values()]

    def build_outbox(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for record in self.store.outbox:
            if hash_obj(record.payload_json, domain=HASH_DOMAINS["OUTBOX"]) != record.payload_hash:
                raise NovaPayTransferAdmissionError(f"outbox_payload_corrupted:{record.outbox_id}")
            records.append(record.canonical())
        return records

    def build_snapshots(self, transfer_id: str | None = None) -> list[dict[str, Any]]:
        if transfer_id is not None:
            return [snapshot.canonical() for snapshot in self.store.snapshots.get(transfer_id, ())]
        return [
            snapshot.canonical()
            for snapshots in self.store.snapshots.values()
            for snapshot in snapshots
        ]

    def build_treasury_snapshot(self) -> dict[str, Any]:
        ledger_checkpoint = self.build_ledger_checkpoint()
        reconciliation = self.build_reconciliation_report()
        return {
            "view": "novapay_treasury_snapshot",
            "accounts": self.build_accounts(),
            "liquidity_positions": self.build_liquidity_positions(),
            "prefunding_accounts": self.build_prefunding_accounts(),
            "settlement_exposures": self.build_settlement_exposures(),
            "journals": [journal.canonical() for journal in self.store.journals.values()],
            "outbox": self.build_outbox(),
            "snapshots": self.build_snapshots(),
            "global_ledger_root": ledger_checkpoint["ledger_root"],
            "ledger_checkpoint": ledger_checkpoint,
            "reconciliation": reconciliation,
        }

    def _event_merkle_leaf(self, event: TransferEvent) -> str:
        return hash_obj(event.canonical(), domain=HASH_DOMAINS["MERKLE_LEAF"])

    def _event_merkle_leaves(self, events: tuple[TransferEvent, ...]) -> list[str]:
        return [self._event_merkle_leaf(event) for event in events]

    def _transfer_merkle_root(self, events: tuple[TransferEvent, ...]) -> str:
        return _merkle_root_from_hashes(self._event_merkle_leaves(events))

    def _transfer_merkle_proofs(self, events: tuple[TransferEvent, ...]) -> list[dict[str, Any]]:
        leaves = self._event_merkle_leaves(events)
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "sequence": event.sequence,
                "aggregate_version": event.aggregate_version,
                "event_hash": event.event_hash,
                "leaf_hash": leaves[index],
                **_merkle_proof_from_hashes(leaves, index),
            }
            for index, event in enumerate(events)
        ]

    def _transfer_root_commitment(self, record: RuntimeTransferRecord) -> dict[str, Any]:
        event_hashes = [event.event_hash for event in record.events]
        transfer_merkle_root = self._transfer_merkle_root(record.events)
        return {
            "transfer_id": record.transfer.transfer_id,
            "aggregate_version": record.transfer.aggregate_version,
            "event_count": len(record.events),
            "last_event_hash": event_hashes[-1] if event_hashes else GENESIS_HASH,
            "event_hashes": event_hashes,
            "transfer_merkle_root": transfer_merkle_root,
        }

    def _global_ledger_root(self) -> dict[str, Any]:
        transfer_roots = [
            self._transfer_root_commitment(record)
            for record in self.store.records.values()
            if record.events
        ]
        transfer_roots = sorted(transfer_roots, key=lambda item: str(item["transfer_id"]))
        leaf_hashes = [
            hash_obj(root, domain=HASH_DOMAINS["MERKLE_LEAF"])
            for root in transfer_roots
        ]
        ledger_root = _merkle_root_from_hashes(leaf_hashes)
        return {
            "ledger_root": ledger_root,
            "total_transfers": len(transfer_roots),
            "transfer_roots": transfer_roots,
        }

    def build_ledger_checkpoint(self) -> dict[str, Any]:
        with self.store.read_snapshot():
            global_root = self._global_ledger_root()
            accounts = sorted(
                self.build_accounts(),
                key=lambda account: str(account["account_id"]),
            )
            balances_hash = hash_obj(accounts, domain=HASH_DOMAINS["LEDGER_ENTRY"])
            previous_snapshot_hash = self._latest_checkpoint_hash()
            block_height = len(self.store.outbox)
            checkpoint_body = {
                "ledger_root": global_root["ledger_root"],
                "accounts": accounts,
                "balances_hash": balances_hash,
                "block_height": block_height,
                "previous_snapshot_hash": previous_snapshot_hash,
            }
            checkpoint_hash = hash_obj(checkpoint_body, domain=HASH_DOMAINS["LEDGER_CHECKPOINT"])
            return {
                "snapshot_id": _stable_id("ledger_snap"),
                "ledger_root": global_root["ledger_root"],
                "accounts": accounts,
                "balances_hash": balances_hash,
                "block_height": block_height,
                "previous_snapshot_hash": previous_snapshot_hash,
                "snapshot_hash": checkpoint_hash,
                "total_transfers": global_root["total_transfers"],
                "transfer_roots": global_root["transfer_roots"],
                "created_at": _utcnow(),
            }

    def _latest_checkpoint_hash(self) -> str:
        latest_snapshots = [
            snapshot
            for snapshots in self.store.snapshots.values()
            for snapshot in snapshots
        ]
        if not latest_snapshots:
            return GENESIS_HASH
        latest = max(latest_snapshots, key=lambda snapshot: snapshot.created_at)
        return latest.snapshot_root_hash

    def build_reconciliation_report(self) -> dict[str, Any]:
        ledger_lines = [
            line
            for journal in self.store.journals.values()
            for line in journal.lines
        ]
        total_debit = sum(
            (_decimal(line.amount) for line in ledger_lines if line.direction == "DEBIT"),
            Decimal("0"),
        )
        total_credit = sum(
            (_decimal(line.amount) for line in ledger_lines if line.direction == "CREDIT"),
            Decimal("0"),
        )
        ledger_balanced = total_debit == total_credit
        transfer_roots = self._global_ledger_root()
        report_body = {
            "total_debit": str(total_debit),
            "total_credit": str(total_credit),
            "ledger_balanced": ledger_balanced,
            "ledger_root": transfer_roots["ledger_root"],
            "total_transfers": transfer_roots["total_transfers"],
        }
        return {
            **report_body,
            "status": "clear" if ledger_balanced else "critical",
            "alerts": [] if ledger_balanced else [
                {
                    "alert_type": "ledger_mismatch",
                    "severity": "critical",
                    "detected_at": _utcnow(),
                    "proof": report_body,
                }
            ],
            "report_hash": hash_obj(report_body, domain=HASH_DOMAINS["RECONCILIATION_REPORT"]),
        }

    def _compute_event_hash(self, event: TransferEvent) -> str:
        return hash_obj(event.commitment_payload(), domain=HASH_DOMAINS["TRANSFER_EVENT"])

    def _build_transfer_event(
        self,
        *,
        transfer_id: str,
        event_type: str,
        payload: dict[str, Any],
        decision_trace: dict[str, Any],
        sequence: int,
        previous_event_hash: str,
        previous_aggregate_version: int,
        state_changing: bool = True,
    ) -> TransferEvent:
        aggregate_version = previous_aggregate_version + 1 if state_changing else previous_aggregate_version
        event = TransferEvent(
            event_id=_stable_id("evt"),
            transfer_id=transfer_id,
            event_type=event_type,
            occurred_at=_utcnow(),
            payload=payload,
            decision_trace=decision_trace,
            sequence=sequence,
            schema_version=1,
            aggregate_version=aggregate_version,
            previous_event_hash=previous_event_hash,
        )
        return TransferEvent(
            event_id=event.event_id,
            transfer_id=event.transfer_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            payload=event.payload,
            decision_trace=event.decision_trace,
            sequence=event.sequence,
            schema_version=event.schema_version,
            aggregate_version=event.aggregate_version,
            previous_event_hash=event.previous_event_hash,
            event_hash=self._compute_event_hash(event),
        )

    def _available_liquidity(self, corridor: Corridor, currency: str) -> Decimal:
        key = f"{corridor.corridor_id}:{currency}"
        position = self.store.liquidity_positions.get(key)
        if position is None:
            return Decimal("0")
        return _decimal(position.available_balance)

    def _liquidity_score(self, corridor: Corridor, currency: str, amount: Decimal) -> Decimal:
        if amount <= Decimal("0"):
            return Decimal("0")
        available = self._available_liquidity(corridor, currency)
        return min(Decimal("1"), available / amount)

    def _provider_signal(self, provider: str) -> dict[str, Decimal]:
        signals = {
            "mpesa_ke": {"cost": Decimal("0.18"), "latency": Decimal("0.12"), "success_rate": Decimal("0.99")},
            "lumicash_bi": {"cost": Decimal("0.24"), "latency": Decimal("0.20"), "success_rate": Decimal("0.94")},
            "orange_money_cd": {"cost": Decimal("0.28"), "latency": Decimal("0.25"), "success_rate": Decimal("0.91")},
        }
        return signals.get(provider, {"cost": Decimal("0.35"), "latency": Decimal("0.30"), "success_rate": Decimal("0.88")})

    def _score_route(
        self,
        *,
        corridor: Corridor,
        provider: str,
        settlement_currency: str,
        destination_amount: Decimal,
        compliance_score: int,
    ) -> dict[str, Any]:
        signal = self._provider_signal(provider)
        liquidity_score = self._liquidity_score(corridor, settlement_currency, destination_amount)
        regulatory_score = Decimal("1.00") if corridor.allowed and compliance_score < 60 else Decimal("0.60")
        reliability_penalty = Decimal("1.00") - signal["success_rate"]
        weighted_score = (
            signal["cost"] * Decimal("0.25")
            + signal["latency"] * Decimal("0.20")
            + reliability_penalty * Decimal("0.25")
            + (Decimal("1.00") - liquidity_score) * Decimal("0.20")
            + (Decimal("1.00") - regulatory_score) * Decimal("0.10")
        )
        return {
            "score": str(weighted_score.quantize(Decimal("0.0001"))),
            "weights": {
                "cost": "0.25",
                "latency": "0.20",
                "success_rate": "0.25",
                "liquidity": "0.20",
                "regulatory": "0.10",
            },
            "signals": {
                "provider_uptime": str(signal["success_rate"]),
                "settlement_delay": str(signal["latency"]),
                "fx_margin": str(signal["cost"]),
                "liquidity_score": str(liquidity_score.quantize(Decimal("0.0001"))),
                "regulatory_score": str(regulatory_score.quantize(Decimal("0.0001"))),
            },
        }

    def _require_liquidity_for_routing(self, corridor: Corridor, currency: str, amount: Decimal) -> None:
        if self._available_liquidity(corridor, currency) < amount:
            raise NovaPayTransferAdmissionError(f"insufficient_liquidity:{corridor.corridor_id}:{currency}")

    def _seed_treasury_state(self) -> None:
        for corridor in self.registry.corridors():
            liquidity_key = f"{corridor.corridor_id}:{corridor.settlement_currency}"
            if liquidity_key not in self.store.liquidity_positions:
                available = Decimal("500000") if corridor.execution_state == "live_ready" else Decimal("100000")
                self.store.liquidity_positions[liquidity_key] = LiquidityPosition(
                    corridor_id=corridor.corridor_id,
                    currency=corridor.settlement_currency,
                    available_balance=str(available),
                    reserved_balance="0",
                )
            provider_key = f"{corridor.settlement_provider}:{corridor.settlement_currency}"
            if provider_key not in self.store.prefunding_accounts:
                required = Decimal("100000")
                self.store.prefunding_accounts[provider_key] = PrefundingAccount(
                    prefunding_account_id=_stable_id("pf"),
                    provider=corridor.settlement_provider,
                    currency=corridor.settlement_currency,
                    required_balance=str(required),
                    current_balance=str(required),
                )

    def _ensure_account(self, account_id: str, account_type: str, *, owner_id: str | None, currency: str) -> Account:
        account = self.store.accounts.get(account_id)
        if account is None:
            account = Account(
                account_id=account_id,
                account_type=account_type,
                owner_id=owner_id,
                currency=currency,
            )
            self.store.accounts[account_id] = account
        return account

    def _validate_balanced_journal(self, journal: JournalEntry) -> None:
        debit_total = Decimal("0")
        credit_total = Decimal("0")
        currencies: set[str] = set()
        for line in journal.lines:
            amount = _decimal(line.amount)
            currencies.add(line.currency)
            if line.direction == "DEBIT":
                debit_total += amount
            elif line.direction == "CREDIT":
                credit_total += amount
            else:
                raise NovaPayTransferAdmissionError(f"invalid_journal_direction:{line.direction}")
            account = self.store.accounts.get(line.account_id)
            if account is None:
                raise NovaPayTransferAdmissionError(f"journal_unknown_account:{line.account_id}")
            if account.currency != line.currency:
                raise NovaPayTransferAdmissionError(f"journal_account_currency_mismatch:{line.account_id}")
        if not journal.lines:
            raise NovaPayTransferAdmissionError("journal_requires_lines")
        if len(currencies) != 1:
            raise NovaPayTransferAdmissionError("journal_currency_mismatch")
        if debit_total != credit_total:
            raise NovaPayTransferAdmissionError("journal_not_balanced")
        if debit_total != _decimal(journal.total_debit) or credit_total != _decimal(journal.total_credit):
            raise NovaPayTransferAdmissionError("journal_totals_mismatch")

    def _reserve_liquidity(
        self,
        *,
        transfer_id: str,
        corridor: Corridor,
        currency: str,
        amount: Decimal,
    ) -> LiquidityPosition:
        key = f"{corridor.corridor_id}:{currency}"
        position = self.store.liquidity_positions.get(key)
        if position is None:
            position = LiquidityPosition(
                corridor_id=corridor.corridor_id,
                currency=currency,
                available_balance="0",
                reserved_balance="0",
            )
        available = _decimal(position.available_balance)
        if available < amount:
            raise NovaPayTransferAdmissionError(
                f"insufficient_liquidity:{corridor.corridor_id}:{currency}"
            )
        reserved = _decimal(position.reserved_balance)
        updated = LiquidityPosition(
            corridor_id=position.corridor_id,
            currency=position.currency,
            available_balance=str(available - amount),
            reserved_balance=str(reserved + amount),
            updated_at=_utcnow(),
        )
        self.store.liquidity_positions[key] = updated
        self.store.settlement_exposures[transfer_id] = SettlementExposure(
            exposure_id=_stable_id("exp"),
            transfer_id=transfer_id,
            corridor_id=corridor.corridor_id,
            currency=currency,
            amount_pending=str(amount),
            expected_settlement_date=_utcnow(),
            status="pending",
        )
        return updated

    def _settle_liquidity(
        self,
        *,
        transfer_id: str,
        corridor_id: str,
        currency: str,
        amount: Decimal,
    ) -> None:
        key = f"{corridor_id}:{currency}"
        position = self.store.liquidity_positions.get(key)
        if position is None:
            raise NovaPayTransferAdmissionError(f"liquidity_position_not_found:{corridor_id}:{currency}")
        reserved = _decimal(position.reserved_balance)
        if reserved < amount:
            raise NovaPayTransferAdmissionError(f"reserved_liquidity_mismatch:{corridor_id}:{currency}")
        self.store.liquidity_positions[key] = LiquidityPosition(
            corridor_id=position.corridor_id,
            currency=position.currency,
            available_balance=position.available_balance,
            reserved_balance=str(reserved - amount),
            updated_at=_utcnow(),
        )
        exposure = self.store.settlement_exposures.get(transfer_id)
        if exposure is not None:
            self.store.settlement_exposures[transfer_id] = SettlementExposure(
                exposure_id=exposure.exposure_id,
                transfer_id=exposure.transfer_id,
                corridor_id=exposure.corridor_id,
                currency=exposure.currency,
                amount_pending="0",
                expected_settlement_date=exposure.expected_settlement_date,
                status="settled",
            )

    def _ledger_hash(self, ledger_entries: tuple[LedgerEntry, ...] | list[LedgerEntry]) -> str:
        return hash_obj(
            [entry.canonical() for entry in ledger_entries],
            domain=HASH_DOMAINS["LEDGER_ENTRY"],
        )

    def _maybe_create_snapshot(self, record: RuntimeTransferRecord) -> TransferSnapshot | None:
        if not record.events:
            return None
        should_snapshot = record.receipt is not None or len(record.events) % SNAPSHOT_INTERVAL == 0
        if not should_snapshot:
            return None
        existing = self.store.latest_snapshot(record.transfer.transfer_id)
        if existing is not None and existing.version >= record.transfer.aggregate_version:
            return existing
        snapshot_state = {
            "transfer": record.transfer.canonical(),
            "admission": record.admission.canonical(),
            "settlement": record.settlement.canonical() if record.settlement else None,
            "receipt": record.receipt.canonical() if record.receipt else None,
        }
        ledger_hash = self._ledger_hash(list(record.ledger_entries))
        event_hash = record.events[-1].event_hash
        snapshot_root_hash = hash_obj(
            {
                "state": snapshot_state,
                "ledger_hash": ledger_hash,
                "event_hash": event_hash,
            },
            domain=HASH_DOMAINS["SNAPSHOT"],
        )
        snapshot = TransferSnapshot(
            snapshot_id=_stable_id("snap"),
            transfer_id=record.transfer.transfer_id,
            version=record.transfer.aggregate_version,
            state=snapshot_state,
            ledger_hash=ledger_hash,
            event_hash=event_hash,
            snapshot_root_hash=snapshot_root_hash,
        )
        self.store.save_snapshot(snapshot)
        return snapshot

    def _build_balanced_journal(
        self,
        *,
        transfer_id: str,
        identity: Identity,
        provider: str,
        currency: str,
        amount: Decimal,
        policy_version_used: str,
    ) -> tuple[JournalEntry, tuple[LedgerEntry, ...], tuple[Account, ...]]:
        customer_account_id = f"customer_wallet:{identity.identity_id}"
        settlement_account_id = f"settlement:{provider}"
        treasury_account_id = "treasury:pool"
        fee_account_id = "fee:novapay"
        fx_reserve_account_id = "fx_reserve:novapay"
        suspense_account_id = "suspense:novapay"
        accounts = (
            self._ensure_account(customer_account_id, "customer", owner_id=identity.identity_id, currency=currency),
            self._ensure_account(settlement_account_id, "settlement", owner_id=provider, currency=currency),
            self._ensure_account(treasury_account_id, "treasury", owner_id=None, currency=currency),
            self._ensure_account(fee_account_id, "fee", owner_id=None, currency=currency),
            self._ensure_account(fx_reserve_account_id, "fx_reserve", owner_id=None, currency=currency),
            self._ensure_account(suspense_account_id, "suspense", owner_id=None, currency=currency),
        )
        journal_id = _stable_id("jrnl")
        debit_line = LedgerEntry(
            ledger_entry_id=_stable_id("led"),
            transfer_id=transfer_id,
            account_id=customer_account_id,
            entry_type="DEBIT",
            amount=str(amount),
            currency=currency,
            balance_after=str(amount),
        )
        credit_line = LedgerEntry(
            ledger_entry_id=_stable_id("led"),
            transfer_id=transfer_id,
            account_id=settlement_account_id,
            entry_type="CREDIT",
            amount=str(amount),
            currency=currency,
            balance_after=str(amount),
        )
        journal = JournalEntry(
            journal_id=journal_id,
            transfer_id=transfer_id,
            policy_version_used=policy_version_used,
            total_debit=str(amount),
            total_credit=str(amount),
            created_at=_utcnow(),
            lines=(
                JournalLine(
                    journal_line_id=_stable_id("jln"),
                    account_id=debit_line.account_id,
                    direction=debit_line.entry_type,
                    amount=debit_line.amount,
                    currency=debit_line.currency,
                    balance_after=debit_line.balance_after,
                ),
                JournalLine(
                    journal_line_id=_stable_id("jln"),
                    account_id=credit_line.account_id,
                    direction=credit_line.entry_type,
                    amount=credit_line.amount,
                    currency=credit_line.currency,
                    balance_after=credit_line.balance_after,
                ),
            ),
        )
        self._validate_balanced_journal(journal)
        self.store.journals[transfer_id] = journal
        return journal, (debit_line, credit_line), accounts

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
        recipient_jurisdiction = self.registry.resolve_jurisdiction(destination_country)
        corridor = self.registry.resolve_corridor(source_country, destination_country)
        if not corridor.allowed:
            raise NovaPayTransferAdmissionError(f"corridor_not_allowed:{source_country}->{destination_country}")
        if amount > _decimal(corridor.max_amount):
            raise NovaPayTransferAdmissionError(f"corridor_limit_exceeded:{corridor.corridor_id}")
        license_record = self.registry.resolve_license(jurisdiction)
        source_region = self.registry.resolve_region(source_country)
        destination_region = self.registry.resolve_region(destination_country)

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
            jurisdiction_id=recipient_jurisdiction.jurisdiction_id,
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
        self.registry.license_allows(
            license_record,
            transfer_type=transfer_type_norm,
            amount=amount,
            corridor=corridor,
        )
        if compliance_case.review_required and transfer_type_norm not in {"Cash In", "Cash Out"}:
            # High-risk transfers remain admit-able but marked for review.
            policy_decision = "ALLOW_REVIEW"
        else:
            policy_decision = "ALLOW"
        active_policy = self.registry.active_policy()
        policy_version_used = active_policy.version

        payout_method = _normalize_method(payload.get("payout_method") or "mobile_money")
        quote = self.transfer_service.quote(
            identity=identity,
            recipient_name=recipient.name,
            recipient_identifier=recipient.phone_number,
            recipient_country=destination_country,
            amount=amount,
            source_currency=normalize_currency_code(str(payload.get("source_currency") or "AUD")),
            source_country=source_country,
            payout_method=payout_method,
            use_case=str(payload.get("use_case") or "transparent_pricing"),
            memo=payload.get("memo"),
            live_provider=bool(payload.get("live_provider") or False),
        ).canonical()
        compliance_case = replace(compliance_case, transfer_id=str(quote["transfer_id"]))
        destination_amount = _decimal(quote["destination_amount"])
        self._require_liquidity_for_routing(corridor, quote["destination_currency"], destination_amount)
        route = {
            "route_id": quote["transfer_id"],
            "provider": quote["route_hint"],
            "rail": quote["payout_method"],
            "corridor": quote["corridor"],
            "route_class": quote["route_class"],
            "settlement_currency": quote["destination_currency"],
        }
        route["score"] = self._score_route(
            corridor=corridor,
            provider=route["provider"],
            settlement_currency=quote["destination_currency"],
            destination_amount=destination_amount,
            compliance_score=compliance_score,
        )
        route["region_routing"] = {
            "primary_region": destination_region.region_id,
            "execution_region": destination_region.region_id,
            "origin_region": source_region.region_id,
            "failover_region": destination_region.failover_region_id,
            "destination_region": destination_region.region_id,
            "origin_data_residency_rules": list(source_region.data_residency_rules),
            "execution_data_residency_rules": list(destination_region.data_residency_rules),
        }
        decision_trace = {
            "policy_id": active_policy.policy_id,
            "policy_version": policy_version_used,
            "rule_ids": list(active_policy.rules),
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
                "version": policy_version_used,
                "effective_from": active_policy.effective_from,
                "rules": list(active_policy.rules),
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
            policy_version_used=str(admission.decision_trace.get("policy_version") or admission.policy.get("version") or "2026.06"),
            created_at=_utcnow(),
            updated_at=_utcnow(),
            aggregate_version=2,
        )
        requested_event = self._build_transfer_event(
                transfer_id=transfer.transfer_id,
                event_type="transfer.requested.v1",
                payload={
                    "transfer": transfer.canonical(),
                    "admission": admission.canonical(),
                },
                decision_trace=admission.decision_trace,
                sequence=1,
                previous_event_hash=GENESIS_HASH,
                previous_aggregate_version=0,
        )
        admission_event = self._build_transfer_event(
                transfer_id=transfer.transfer_id,
                event_type="transfer.admission.approved.v1",
                payload={"policy": admission.policy, "compliance": admission.compliance},
                decision_trace=admission.decision_trace,
                sequence=2,
                previous_event_hash=requested_event.event_hash,
                previous_aggregate_version=requested_event.aggregate_version,
        )
        timeline = (
            requested_event,
            admission_event,
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
            journal_entry=None,
            ledger_entries=(),
            settlement=None,
            receipt=None,
            provider_receipt=None,
            events=timeline,
        )
        self.store.save(record)
        self._publish("transfer.requested.v1", record, requested_event)
        self._publish("transfer.admission.approved.v1", record, admission_event)
        if auto_execute:
            record = self.execute_transfer(transfer.transfer_id, identity=identity, live_provider=live_provider)
        return record

    def execute_transfer(
        self,
        transfer_id: str,
        *,
        identity: Identity,
        live_provider: bool = False,
        expected_version: int | None = None,
    ) -> RuntimeTransferRecord:
        record = self.store.get(transfer_id)
        if record is None:
            raise NovaPayTransferAdmissionError(f"transfer_not_found:{transfer_id}")
        if record.transfer.sender_id != identity.identity_id:
            raise NovaPayTransferAdmissionError("transfer_sender_mismatch")
        if expected_version is not None and record.transfer.aggregate_version != expected_version:
            raise NovaPayTransferAdmissionError(
                f"aggregate_version_conflict:{record.transfer.aggregate_version}:expected:{expected_version}"
            )
        if record.receipt is not None and record.settlement is not None:
            return record

        decision = AuthorityDecision(
            decision="ALLOW",
            reason="governed_transfer_admission_passed",
            trace_id=f"novapay-transfer:{transfer_id}",
            checks=("jurisdiction", "license", "corridor", "compliance", "policy", "funding_source"),
        )
        corridor = record.admission.corridor
        settlement_currency = str(corridor.get("settlement_currency") or record.transfer.currency)
        settlement_amount = _decimal(record.admission.quote["destination_amount"])
        self._reserve_liquidity(
            transfer_id=transfer_id,
            corridor=self.registry.resolve_corridor(
                corridor["source_country"],
                corridor["destination_country"],
            ),
            currency=settlement_currency,
            amount=settlement_amount,
        )
        receipt = self.transfer_service.execute(
            record.admission.quote,
            identity=identity,
            decision=decision,
            provider=record.admission.routing["provider"],
            live_provider=live_provider,
        )
        provider_receipt = receipt.canonical()
        self._settle_liquidity(
            transfer_id=transfer_id,
            corridor_id=str(corridor["corridor_id"]),
            currency=settlement_currency,
            amount=settlement_amount,
        )
        policy_version_used = str(
            record.transfer.policy_version_used
            or record.admission.decision_trace.get("policy_version")
            or record.admission.policy.get("version")
            or "2026.06"
        )
        journal_entry, ledger_entries, accounts = self._build_balanced_journal(
            transfer_id=transfer_id,
            identity=identity,
            provider=record.admission.routing["provider"],
            currency=record.transfer.currency,
            amount=_decimal(record.transfer.amount),
            policy_version_used=policy_version_used,
        )
        settlement = SettlementRecord(
            settlement_id=_stable_id("set"),
            transfer_id=transfer_id,
            rail=record.admission.routing["rail"],
            provider=record.admission.routing["provider"],
            status=receipt.status,
            reference_id=str(receipt.payment.get("provider_reference") or receipt.payment.get("payment_id") or receipt.quote_id),
            settled_at=_utcnow(),
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
        previous_hash = timeline[-1].event_hash if timeline else GENESIS_HASH
        previous_aggregate_version = timeline[-1].aggregate_version if timeline else 0
        executed_event = self._build_transfer_event(
            transfer_id=transfer_id,
            event_type="transfer.executed.v1",
            payload={
                "transfer": {
                    **record.transfer.canonical(),
                    "status": "completed" if receipt.status == "completed" else "settled",
                    "updated_at": _utcnow(),
                    "receipt": receipt_record.canonical(),
                    "aggregate_version": 5,
                },
                "receipt": receipt.canonical(),
                "settlement": settlement.canonical(),
                "journal_entry": journal_entry.canonical(),
                "ledger_entries": [entry.canonical() for entry in ledger_entries],
            },
            decision_trace=record.admission.decision_trace,
            sequence=3,
            previous_event_hash=previous_hash,
            previous_aggregate_version=previous_aggregate_version,
        )
        settled_event = self._build_transfer_event(
            transfer_id=transfer_id,
            event_type="transfer.settled.v1",
            payload={"settlement": settlement.canonical()},
            decision_trace=record.admission.decision_trace,
            sequence=4,
            previous_event_hash=executed_event.event_hash,
            previous_aggregate_version=executed_event.aggregate_version,
        )
        receipt_event = self._build_transfer_event(
            transfer_id=transfer_id,
            event_type="receipt.generated.v1",
            payload={"receipt": receipt_record.canonical()},
            decision_trace=record.admission.decision_trace,
            sequence=5,
            previous_event_hash=settled_event.event_hash,
            previous_aggregate_version=settled_event.aggregate_version,
        )
        timeline.extend([executed_event, settled_event, receipt_event])
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
                policy_version_used=policy_version_used,
                created_at=record.transfer.created_at,
                updated_at=_utcnow(),
                timeline=tuple(timeline),
                receipt=receipt_record,
                aggregate_version=5,
            ),
            admission=record.admission,
            funding_source=record.funding_source,
            recipient=record.recipient,
            compliance_case=record.compliance_case,
            journal_entry=journal_entry,
            ledger_entries=ledger_entries,
            settlement=settlement,
            receipt=receipt_record,
            provider_receipt=provider_receipt,
            events=tuple(timeline),
        )
        self.store.journals[transfer_id] = journal_entry
        self.store.save(updated)
        self._maybe_create_snapshot(updated)
        self._publish("transfer.executed.v1", updated, executed_event)
        self._publish("transfer.settled.v1", updated, settled_event)
        self._publish("receipt.generated.v1", updated, receipt_event)
        return updated

    def get_transfer(self, transfer_id: str) -> RuntimeTransferRecord | None:
        return self.store.get(transfer_id)

    def get_timeline(self, transfer_id: str) -> list[dict[str, Any]]:
        record = self.store.get(transfer_id)
        if record is None:
            raise NovaPayTransferAdmissionError(f"transfer_not_found:{transfer_id}")
        return [event.canonical() for event in record.events]

    def _validate_event_sequence(self, events: tuple[TransferEvent, ...]) -> None:
        seen_event_ids: set[str] = set()
        seen_event_types: set[str] = set()
        previous_timestamp: datetime | None = None
        previous_hash = GENESIS_HASH
        previous_aggregate_version = 0
        current_state: str | None = None

        if not events:
            raise NovaPayTransferAdmissionError("event_sequence_empty")

        for index, event in enumerate(events, start=1):
            state = EVENT_STATE_MAP.get(event.event_type)
            if state is None:
                raise NovaPayTransferAdmissionError(f"event_type_not_registered:{event.event_type}")
            allowed_schema_versions = EVENT_SCHEMA_REGISTRY.get(event.event_type)
            if allowed_schema_versions is None or event.schema_version not in allowed_schema_versions:
                raise NovaPayTransferAdmissionError(
                    f"schema_version_invalid:{event.event_type}:{event.schema_version}"
                )
            if event.event_id in seen_event_ids:
                raise NovaPayTransferAdmissionError(f"event_duplicate_id:{event.event_id}")
            seen_event_ids.add(event.event_id)

            if event.event_type in seen_event_types:
                raise NovaPayTransferAdmissionError(f"event_duplicate_type:{event.event_type}")
            seen_event_types.add(event.event_type)

            allowed_states = TRANSFER_STATE_MACHINE.get(current_state, ())
            if state not in allowed_states:
                raise NovaPayTransferAdmissionError(f"invalid_transition:{current_state}->{state}")
            required_previous = MANDATORY_PREVIOUS_STATES.get(state)
            if required_previous is not None and current_state != required_previous:
                raise NovaPayTransferAdmissionError(f"missing_required_transition:{required_previous}->{state}")
            if event.sequence != index:
                raise NovaPayTransferAdmissionError(f"event_sequence_number_invalid:{event.event_id}")
            expected_aggregate_version = (
                previous_aggregate_version + 1
                if event.event_type in STATE_CHANGING_EVENTS
                else previous_aggregate_version
            )
            if event.aggregate_version != expected_aggregate_version:
                raise NovaPayTransferAdmissionError(f"event_aggregate_version_invalid:{event.event_id}")
            if event.transfer_id != events[0].transfer_id:
                raise NovaPayTransferAdmissionError("event_transfer_id_mismatch")
            if event.event_hash != self._compute_event_hash(event):
                raise NovaPayTransferAdmissionError(f"event_hash_invalid:{event.event_id}")
            if event.previous_event_hash != previous_hash:
                raise NovaPayTransferAdmissionError(f"event_hash_chain_broken:{event.event_id}")

            occurred_at = _parse_timestamp(event.occurred_at)
            if previous_timestamp is not None and occurred_at < previous_timestamp:
                raise NovaPayTransferAdmissionError(f"event_timestamp_regressed:{event.event_id}")
            previous_timestamp = occurred_at
            previous_hash = event.event_hash
            previous_aggregate_version = event.aggregate_version
            current_state = state

    def _validate_event_chain(self, events: tuple[TransferEvent, ...]) -> bool:
        self._validate_event_sequence(events)
        return True

    def replay_transfer(self, transfer_id: str) -> dict[str, Any]:
        record = self.store.get(transfer_id)
        if record is None:
            raise NovaPayTransferAdmissionError(f"transfer_not_found:{transfer_id}")
        self._validate_event_sequence(record.events)
        policy = self.registry.resolve_policy(
            record.transfer.policy_decision_id,
            record.transfer.policy_version_used,
        )
        snapshot = self.store.latest_snapshot(transfer_id)

        reconstructed: dict[str, Any] = {
            "transfer_id": transfer_id,
            "transfer": None,
            "admission": None,
            "journal_entry": None,
            "ledger_entries": [],
            "settlement": None,
            "receipt": None,
            "events": [],
        }
        for event in record.events:
            event_payload = event.canonical()
            reconstructed["events"].append(event_payload)
            if event.event_type == "transfer.requested.v1":
                transfer_payload = dict(event.payload.get("transfer") or {})
                admission_payload = dict(event.payload.get("admission") or {})
                reconstructed["transfer"] = transfer_payload
                reconstructed["admission"] = admission_payload
            elif event.event_type == "transfer.executed.v1":
                transfer_payload = dict(event.payload.get("transfer") or {})
                receipt_payload = dict(event.payload.get("receipt") or {})
                settlement_payload = dict(event.payload.get("settlement") or {})
                journal_payload = dict(event.payload.get("journal_entry") or {})
                ledger_payload = list(event.payload.get("ledger_entries") or [])
                normalized_journal = JournalEntry.from_dict(journal_payload) if journal_payload else None
                normalized_ledger = [
                    LedgerEntry.from_dict(item)
                    for item in ledger_payload
                ]
                reconstructed["transfer"] = transfer_payload
                reconstructed["receipt"] = receipt_payload
                reconstructed["settlement"] = settlement_payload
                reconstructed["journal_entry"] = normalized_journal
                reconstructed["ledger_entries"] = normalized_ledger
            elif event.event_type == "transfer.settled.v1":
                reconstructed["settlement"] = dict(event.payload.get("settlement") or {})
            elif event.event_type == "receipt.generated.v1":
                reconstructed["receipt"] = dict(event.payload.get("receipt") or {})

        reconstructed_policy = (reconstructed["admission"] or {}).get("policy") or {}
        if (
            reconstructed_policy.get("version") != policy.version
            or (reconstructed["admission"] or {}).get("decision_trace", {}).get("policy_id") != policy.policy_id
        ):
            raise NovaPayTransferAdmissionError(f"policy_replay_mismatch:{policy.policy_id}:{policy.version}")

        replay_hash = hash_obj(
            {
                "transfer_id": transfer_id,
                "transfer": reconstructed["transfer"],
                "admission": reconstructed["admission"],
                "journal_entry": reconstructed["journal_entry"].canonical() if reconstructed["journal_entry"] else None,
                "ledger_entries": [entry.canonical() for entry in reconstructed["ledger_entries"]],
                "settlement": reconstructed["settlement"],
                "receipt": reconstructed["receipt"],
                "events": reconstructed["events"],
            },
            domain=HASH_DOMAINS["TRANSFER_RECEIPT"],
        )
        comparable_transfer_fields = (
            "transfer_id",
            "transfer_type",
            "status",
            "amount",
            "currency",
            "sender_id",
            "recipient_id",
            "funding_source_id",
            "settlement_rail",
            "jurisdiction_id",
            "corridor_id",
            "quote_id",
            "route_id",
            "compliance_status",
            "policy_decision_id",
            "policy_version_used",
            "aggregate_version",
        )
        comparable_record_transfer = {
            key: record.transfer.canonical().get(key)
            for key in comparable_transfer_fields
        }
        comparable_replay_transfer = {
            key: (reconstructed["transfer"] or {}).get(key)
            for key in comparable_transfer_fields
        }
        replay_valid = (
            comparable_record_transfer == comparable_replay_transfer
            and record.admission.canonical() == reconstructed["admission"]
            and (record.journal_entry.canonical() if record.journal_entry else None)
            == (reconstructed["journal_entry"].canonical() if reconstructed["journal_entry"] else None)
            and [entry.canonical() for entry in record.ledger_entries]
            == [entry.canonical() for entry in reconstructed["ledger_entries"]]
            and (record.settlement.canonical() if record.settlement else None) == reconstructed["settlement"]
            and (record.receipt.canonical() if record.receipt else None) == reconstructed["receipt"]
        )
        state = ReplayState(
            transfer_id=transfer_id,
            replay_hash=replay_hash,
            replay_valid=replay_valid,
            transfer=reconstructed["transfer"],
            admission=reconstructed["admission"],
            journal_entry=reconstructed["journal_entry"],
            ledger_entries=list(reconstructed["ledger_entries"]),
            settlement=reconstructed["settlement"],
            receipt=reconstructed["receipt"],
            policy=policy.canonical(),
            snapshot=snapshot.canonical() if snapshot else None,
            events=list(reconstructed["events"]),
        )
        return state.canonical()

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

    def build_audit_package(self, transfer_id: str) -> dict[str, Any]:
        record = self.store.get(transfer_id)
        if record is None:
            raise NovaPayTransferAdmissionError(f"transfer_not_found:{transfer_id}")
        if record.receipt is None or record.settlement is None or record.journal_entry is None:
            raise NovaPayTransferAdmissionError(f"audit_package_not_ready:{transfer_id}")
        event_chain_valid = self._validate_event_chain(record.events)
        replay = self.replay_transfer(transfer_id)
        ledger_hash = self._ledger_hash(list(record.ledger_entries))
        transfer_root = self._transfer_root_commitment(record)
        merkle_proofs = self._transfer_merkle_proofs(record.events)
        ledger_checkpoint = self.build_ledger_checkpoint()
        reconciliation = self.build_reconciliation_report()
        source_body = {
            "schema": AUDIT_PACKAGE_SCHEMA,
            "canonical_format": CANONICAL_FORMAT,
            "hash_domain_version": HASH_DOMAIN_VERSION,
            "hash_algorithm": HASH_ALGORITHM,
            "transfer": record.transfer.canonical(),
            "admission": record.admission.canonical(),
            "receipt": record.receipt.canonical(),
            "ledger": [entry.canonical() for entry in record.ledger_entries],
            "journal_entry": record.journal_entry.canonical(),
            "settlement": record.settlement.canonical(),
            "events": [event.canonical() for event in record.events],
            "policy": self.registry.resolve_policy(
                record.transfer.policy_decision_id,
                record.transfer.policy_version_used,
            ).canonical(),
            "snapshot": self.store.latest_snapshot(transfer_id).canonical()
            if self.store.latest_snapshot(transfer_id)
            else None,
            "transfer_merkle_root": transfer_root["transfer_merkle_root"],
            "transfer_root_commitment": transfer_root,
            "merkle_proofs": merkle_proofs,
            "global_ledger_root": ledger_checkpoint["ledger_root"],
            "ledger_checkpoint": ledger_checkpoint,
            "reconciliation": reconciliation,
            "verification_instructions": "Verify protocol identifiers, audit root signature, event hash chain, per-event Merkle inclusion, ledger checkpoint root, reconciliation report, snapshot binding, and receipt signature using canonical.v1 and sha256.",
        }
        proof_body = {
            "event_chain_valid": event_chain_valid,
            "ledger_hash": ledger_hash,
            "replay_hash": replay["replay_hash"],
        }
        root_hash = hash_obj(source_body, domain=HASH_DOMAINS["AUDIT_PACKAGE"])
        signature = sign_packet({"root_hash": root_hash, "transfer_id": transfer_id}).canonical()
        return {
            **source_body,
            **proof_body,
            "root_hash": root_hash,
            "signature": signature,
        }

    def verify_audit_package(self, package: Mapping[str, Any]) -> dict[str, Any]:
        protocol_valid = (
            package.get("schema") == AUDIT_PACKAGE_SCHEMA
            and package.get("canonical_format") == CANONICAL_FORMAT
            and package.get("hash_domain_version") == HASH_DOMAIN_VERSION
            and package.get("hash_algorithm") == HASH_ALGORITHM
        )
        source_body = {
            key: package.get(key)
            for key in (
                "schema",
                "canonical_format",
                "hash_domain_version",
                "hash_algorithm",
                "transfer",
                "admission",
                "receipt",
                "ledger",
                "journal_entry",
                "settlement",
                "events",
                "policy",
                "snapshot",
                "transfer_merkle_root",
                "transfer_root_commitment",
                "merkle_proofs",
                "global_ledger_root",
                "ledger_checkpoint",
                "reconciliation",
                "verification_instructions",
            )
        }
        root_hash = hash_obj(source_body, domain=HASH_DOMAINS["AUDIT_PACKAGE"])
        signature_valid = verify_packet_signature(
            {"root_hash": root_hash, "transfer_id": (package.get("transfer") or {}).get("transfer_id")},
            package.get("signature") or {},
        )
        normalized_ledger = [
            LedgerEntry.from_dict(entry).canonical()
            for entry in (package.get("ledger") or [])
        ]
        recomputed_ledger_hash = hash_obj(
            normalized_ledger,
            domain=HASH_DOMAINS["LEDGER_ENTRY"],
        )
        ledger_hash_valid = package.get("ledger_hash") == recomputed_ledger_hash
        events = tuple(TransferEvent.from_dict(event) for event in (package.get("events") or []))
        try:
            event_chain_valid = self._validate_event_chain(events)
        except NovaPayTransferAdmissionError:
            event_chain_valid = False
        snapshot = package.get("snapshot") or {}
        snapshot_root_valid = True
        snapshot_ledger_valid = True
        if snapshot:
            snapshot_root_valid = snapshot.get("snapshot_root_hash") == hash_obj(
                {
                    "state": snapshot.get("state"),
                    "ledger_hash": snapshot.get("ledger_hash"),
                    "event_hash": snapshot.get("event_hash"),
                },
                domain=HASH_DOMAINS["SNAPSHOT"],
            )
            snapshot_ledger_valid = snapshot.get("ledger_hash") == package.get("ledger_hash")
        transfer_merkle_valid = self._verify_package_merkle(package, events)
        ledger_checkpoint_valid = self._verify_package_ledger_checkpoint(package)
        reconciliation_valid = self._verify_package_reconciliation(package)
        return {
            "valid": bool(
                root_hash == package.get("root_hash")
                and protocol_valid
                and signature_valid
                and ledger_hash_valid
                and snapshot_root_valid
                and snapshot_ledger_valid
                and event_chain_valid
                and transfer_merkle_valid
                and ledger_checkpoint_valid
                and reconciliation_valid
            ),
            "root_hash": root_hash,
            "protocol_valid": bool(protocol_valid),
            "signature_valid": bool(signature_valid),
            "ledger_hash_valid": bool(ledger_hash_valid),
            "snapshot_root_valid": bool(snapshot_root_valid),
            "snapshot_ledger_valid": bool(snapshot_ledger_valid),
            "event_chain_valid": bool(event_chain_valid),
            "transfer_merkle_valid": bool(transfer_merkle_valid),
            "ledger_checkpoint_valid": bool(ledger_checkpoint_valid),
            "reconciliation_valid": bool(reconciliation_valid),
        }

    def _verify_package_merkle(
        self,
        package: Mapping[str, Any],
        events: tuple[TransferEvent, ...],
    ) -> bool:
        if not events:
            return False
        leaves = [hash_obj(event.canonical(), domain=HASH_DOMAINS["MERKLE_LEAF"]) for event in events]
        root = _merkle_root_from_hashes(leaves)
        if package.get("transfer_merkle_root") != root:
            return False
        commitment = package.get("transfer_root_commitment") or {}
        if commitment.get("transfer_merkle_root") != root:
            return False
        proofs = package.get("merkle_proofs") or []
        if len(proofs) != len(events):
            return False
        for event, leaf, proof in zip(events, leaves, proofs):
            if proof.get("event_id") != event.event_id:
                return False
            if proof.get("event_type") != event.event_type:
                return False
            if proof.get("sequence") != event.sequence:
                return False
            if proof.get("aggregate_version") != event.aggregate_version:
                return False
            if proof.get("event_hash") != event.event_hash:
                return False
            if proof.get("leaf_hash") != leaf:
                return False
            if not _verify_merkle_proof(leaf, proof, root):
                return False
        return True

    def _verify_package_ledger_checkpoint(self, package: Mapping[str, Any]) -> bool:
        checkpoint = package.get("ledger_checkpoint") or {}
        if not checkpoint:
            return False
        transfer_roots = checkpoint.get("transfer_roots") or []
        leaf_hashes = [
            hash_obj(root, domain=HASH_DOMAINS["MERKLE_LEAF"])
            for root in sorted(transfer_roots, key=lambda item: str(item.get("transfer_id")))
        ]
        ledger_root = _merkle_root_from_hashes(leaf_hashes)
        accounts = checkpoint.get("accounts") or []
        balances_hash = hash_obj(accounts, domain=HASH_DOMAINS["LEDGER_ENTRY"])
        checkpoint_body = {
            "ledger_root": ledger_root,
            "accounts": accounts,
            "balances_hash": balances_hash,
            "block_height": checkpoint.get("block_height"),
            "previous_snapshot_hash": checkpoint.get("previous_snapshot_hash"),
        }
        return bool(
            package.get("global_ledger_root") == ledger_root
            and checkpoint.get("ledger_root") == ledger_root
            and checkpoint.get("balances_hash") == balances_hash
            and checkpoint.get("snapshot_hash") == hash_obj(
                checkpoint_body,
                domain=HASH_DOMAINS["LEDGER_CHECKPOINT"],
            )
        )

    def _verify_package_reconciliation(self, package: Mapping[str, Any]) -> bool:
        report = package.get("reconciliation") or {}
        if not report:
            return False
        report_body = {
            "total_debit": str(_decimal(report.get("total_debit", "0"))),
            "total_credit": str(_decimal(report.get("total_credit", "0"))),
            "ledger_balanced": bool(report.get("ledger_balanced")),
            "ledger_root": report.get("ledger_root"),
            "total_transfers": report.get("total_transfers"),
        }
        return bool(
            report.get("ledger_balanced") is True
            and report.get("ledger_root") == package.get("global_ledger_root")
            and report.get("report_hash") == hash_obj(
                report_body,
                domain=HASH_DOMAINS["RECONCILIATION_REPORT"],
            )
        )

    def _publish(self, event_type: str, record: RuntimeTransferRecord, event: TransferEvent) -> None:
        payload = {
            "transfer_id": record.transfer.transfer_id,
            "transfer_type": record.transfer.transfer_type,
            "status": record.transfer.status,
            "event_id": event.event_id,
            "event_hash": event.event_hash,
            "previous_event_hash": event.previous_event_hash,
            "event_sequence": event.sequence,
            "event_schema_version": event.schema_version,
            "aggregate_version": event.aggregate_version,
            "jurisdiction": record.admission.jurisdiction,
            "license": record.admission.license,
            "corridor": record.admission.corridor,
            "policy": record.admission.policy,
            "compliance": record.compliance_case.canonical(),
            "receipt": record.receipt.canonical() if record.receipt else None,
            "decision_trace": record.admission.decision_trace,
        }
        outbox_record = OutboxRecord(
            outbox_id=_stable_id("outbox"),
            event_type=f"novapay.{event_type}",
            aggregate_id=record.transfer.transfer_id,
            aggregate_version=event.aggregate_version,
            payload_json=payload,
            payload_hash=hash_obj(payload, domain=HASH_DOMAINS["OUTBOX"]),
        )
        self.store.append_outbox(outbox_record)
        try:
            self.event_bus.publish(
                f"novapay.{event_type}",
                payload,
            )
        except Exception as exc:
            self.store.mark_outbox_failed(outbox_record.outbox_id, str(exc))
            raise
        else:
            self.store.mark_outbox_published(outbox_record.outbox_id)


DEFAULT_NOVAPAY_RUNTIME = NovaPayRuntimeEngine()


def build_novapay_runtime() -> NovaPayRuntimeEngine:
    return DEFAULT_NOVAPAY_RUNTIME


__all__ = [
    "ComplianceCase",
    "Corridor",
    "Customer",
    "FundingSource",
    "Jurisdiction",
    "Account",
    "JournalEntry",
    "JournalLine",
    "LedgerEntry",
    "License",
    "LiquidityPosition",
    "NovaPayRegistry",
    "NovaPayRuntimeEngine",
    "NovaPayTransferAdmissionError",
    "OutboxRecord",
    "PolicyVersion",
    "PrefundingAccount",
    "Recipient",
    "Receipt",
    "Region",
    "ReplayState",
    "RuntimeTransferRecord",
    "SettlementExposure",
    "SettlementRail",
    "SettlementRecord",
    "Transfer",
    "TransferAdmissionRequest",
    "TransferAdmissionResult",
    "TransferEvent",
    "TransferSnapshot",
    "build_novapay_runtime",
]
