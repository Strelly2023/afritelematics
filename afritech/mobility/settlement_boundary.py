"""Deterministic settlement boundary for Gen-3 mobility operations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.mobility.logistics_custody_chain import CustodyChain, validate_custody_chain
from afritech.mobility.trust_dispatch import DispatchDecision


SCHEMA = "afritech.mobility.settlement_record.v1"
AUTHORITY_BOUNDARY = "settlement_reference_only"
ALLOWED_STATUSES = ("PENDING", "ELIGIBLE", "SETTLED", "DISPUTED")


class SettlementBoundaryError(ValueError):
    """Raised when settlement boundary inputs or records are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SettlementBoundaryError(f"{label} is required")
    return value.strip()


def _decimal(value: object, label: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive
        raise SettlementBoundaryError(f"{label} must be numeric") from exc


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _freeze_mapping(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise SettlementBoundaryError("mapping expected")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _normalize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class SettlementEvent:
    event_id: str
    timestamp: int
    actor: str
    action: str
    evidence_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text(self.event_id, "event_id"))
        if not isinstance(self.timestamp, int):
            raise SettlementBoundaryError("event timestamp must be an integer")
        object.__setattr__(self, "actor", _require_text(self.actor, "actor"))
        object.__setattr__(self, "action", _require_text(self.action, "action"))
        if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
            raise SettlementBoundaryError("evidence_hash must be a 64-character hex digest")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SettlementEvent":
        if not isinstance(payload, Mapping):
            raise SettlementBoundaryError("settlement event payload must be a mapping")
        return cls(
            event_id=_require_text(payload.get("event_id") or payload.get("id"), "event_id"),
            timestamp=int(payload.get("timestamp", 0)),
            actor=_require_text(payload.get("actor"), "actor"),
            action=_require_text(payload.get("action"), "action"),
            evidence_hash=_require_text(payload.get("evidence_hash") or payload.get("hash"), "evidence_hash"),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "actor": self.actor,
            "evidence_hash": self.evidence_hash,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
        }

    def event_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    operation_id: str
    dispatch_hash: str
    chain_hash: str
    participants: tuple[str, ...]
    amounts: tuple[tuple[str, Decimal]]
    gross_amount: Decimal
    currency: str
    status: str
    events: tuple[SettlementEvent, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "settlement_id", _require_text(self.settlement_id, "settlement_id"))
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        if not isinstance(self.dispatch_hash, str) or len(self.dispatch_hash) != 64:
            raise SettlementBoundaryError("dispatch_hash must be a 64-character hex digest")
        if not isinstance(self.chain_hash, str) or len(self.chain_hash) != 64:
            raise SettlementBoundaryError("chain_hash must be a 64-character hex digest")
        if not self.participants:
            raise SettlementBoundaryError("participants are required")
        normalized_participants = tuple(sorted({ _require_text(value, "participant") for value in self.participants }))
        object.__setattr__(self, "participants", normalized_participants)
        amount_map = {}
        for participant, amount in self.amounts:
            key = _require_text(participant, "amount participant")
            amount_map[key] = _normalize_amount(_decimal(amount, f"amount for {key}"))
        if not amount_map:
            raise SettlementBoundaryError("amounts are required")
        object.__setattr__(self, "amounts", tuple(sorted(amount_map.items())))
        object.__setattr__(self, "gross_amount", _normalize_amount(_decimal(self.gross_amount, "gross_amount")))
        object.__setattr__(self, "currency", _require_text(self.currency, "currency"))
        if self.status not in ALLOWED_STATUSES:
            raise SettlementBoundaryError(f"unsupported settlement status: {self.status}")
        object.__setattr__(self, "events", tuple(_normalize_event(event) for event in self.events))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SettlementRecord":
        if not isinstance(payload, Mapping):
            raise SettlementBoundaryError("settlement record payload must be a mapping")
        return cls(
            settlement_id=_require_text(payload.get("settlement_id") or payload.get("id"), "settlement_id"),
            operation_id=_require_text(payload.get("operation_id"), "operation_id"),
            dispatch_hash=_require_text(payload.get("dispatch_hash"), "dispatch_hash"),
            chain_hash=_require_text(payload.get("chain_hash"), "chain_hash"),
            participants=tuple(payload.get("participants", ())),  # type: ignore[arg-type]
            amounts=tuple((str(key), value) for key, value in dict(payload.get("amounts", {})).items()),
            gross_amount=_decimal(payload.get("gross_amount"), "gross_amount"),
            currency=_require_text(payload.get("currency"), "currency"),
            status=_require_text(payload.get("status"), "status"),
            events=tuple(payload.get("events", ())),  # type: ignore[arg-type]
        )

    @property
    def amount_map(self) -> dict[str, Decimal]:
        return dict(self.amounts)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "amounts": {key: _format_decimal(value) for key, value in self.amounts},
            "authority_boundary": self.authority_boundary,
            "chain_hash": self.chain_hash,
            "currency": self.currency,
            "dispatch_hash": self.dispatch_hash,
            "events": [event.canonical_dict() for event in self.events],
            "gross_amount": _format_decimal(self.gross_amount),
            "operation_id": self.operation_id,
            "participants": list(self.participants),
            "schema": SCHEMA,
            "settlement_id": self.settlement_id,
            "settlement_hash": self.settlement_hash,
            "status": self.status,
        }

    @property
    def settlement_hash(self) -> str:
        return _canonical_hash(
            {
                "amounts": {key: _format_decimal(value) for key, value in self.amounts},
                "chain_hash": self.chain_hash,
                "currency": self.currency,
                "dispatch_hash": self.dispatch_hash,
                "events": [event.canonical_dict() for event in self.events],
                "gross_amount": _format_decimal(self.gross_amount),
                "operation_id": self.operation_id,
                "participants": list(self.participants),
                "settlement_id": self.settlement_id,
                "status": self.status,
            }
        )

    @property
    def verified(self) -> bool:
        return True


@dataclass(frozen=True)
class SettlementValidationReport:
    settlement_hash: str
    dispatch_hash: str
    chain_hash: str
    verified: bool
    authority_boundary: str = AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "chain_hash": self.chain_hash,
            "dispatch_hash": self.dispatch_hash,
            "schema": "afritech.mobility.settlement_validation_report.v1",
            "settlement_hash": self.settlement_hash,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def compute_settlement_record(
    dispatch: DispatchDecision | Mapping[str, Any],
    custody: CustodyChain | Mapping[str, Any],
    pricing_rules: Mapping[str, Any] | dict[str, Any],
    *,
    settlement_id: str | None = None,
    status: str = "ELIGIBLE",
    events: Iterable[SettlementEvent | Mapping[str, Any]] = (),
) -> SettlementRecord:
    try:
        dispatch_decision = dispatch if isinstance(dispatch, DispatchDecision) else _dispatch_from_mapping(dispatch)
        custody_chain = custody if isinstance(custody, CustodyChain) else CustodyChain.from_mapping(custody)
    except Exception as exc:
        raise SettlementBoundaryError(str(exc)) from exc
    if not dispatch_decision.verified:
        raise SettlementBoundaryError("dispatch evidence must be verified")
    try:
        validate_custody_chain(custody_chain)
    except Exception as exc:
        raise SettlementBoundaryError(str(exc)) from exc

    rules = _coerce_mapping(pricing_rules)
    gross_amount = _normalize_amount(_decimal(rules.get("gross_amount"), "gross_amount"))
    splits = rules.get("splits")
    if not isinstance(splits, Mapping) or not splits:
        raise SettlementBoundaryError("pricing_rules must define splits")

    normalized_splits = { _require_text(key, "split participant"): _decimal(value, f"split for {key}") for key, value in splits.items() }
    if any(value < 0 for value in normalized_splits.values()):
        raise SettlementBoundaryError("split values must be non-negative")
    total = sum(normalized_splits.values(), Decimal("0.00"))
    if _normalize_amount(total) != Decimal("1.00"):
        raise SettlementBoundaryError("split values must sum to 1.00")

    amounts = {
        participant: _normalize_amount(gross_amount * fraction)
        for participant, fraction in normalized_splits.items()
    }
    settlement_id = settlement_id or f"settlement-{dispatch_decision.request.operation_id}"
    normalized_events = tuple(_normalize_event(event) for event in events) or (
        SettlementEvent(
            event_id=f"{settlement_id}.created",
            timestamp=dispatch_decision.request.timestamp,
            actor="system",
            action="created",
            evidence_hash=dispatch_decision.decision_hash,
        ),
        SettlementEvent(
            event_id=f"{settlement_id}.eligible",
            timestamp=dispatch_decision.request.timestamp + 1,
            actor="system",
            action="eligible",
            evidence_hash=custody_chain.chain_hash,
        ),
    )
    record = SettlementRecord(
        settlement_id=settlement_id,
        operation_id=dispatch_decision.request.operation_id,
        dispatch_hash=dispatch_decision.decision_hash,
        chain_hash=custody_chain.chain_hash,
        participants=tuple(sorted(amounts.keys())),
        amounts=tuple(sorted(amounts.items())),
        gross_amount=gross_amount,
        currency=_require_text(rules.get("currency") or "USD", "currency"),
        status=status,
        events=normalized_events,
    )
    validate_settlement_record(record, custody_chain, dispatch_decision)
    return record


def validate_settlement_record(
    record: SettlementRecord | Mapping[str, Any],
    custody: CustodyChain | Mapping[str, Any] | None = None,
    dispatch: DispatchDecision | Mapping[str, Any] | None = None,
) -> SettlementValidationReport:
    try:
        normalized = record if isinstance(record, SettlementRecord) else SettlementRecord.from_mapping(record)
        custody_chain = custody if isinstance(custody, CustodyChain) else (CustodyChain.from_mapping(custody) if custody is not None else None)
        dispatch_decision = dispatch if isinstance(dispatch, DispatchDecision) else (_dispatch_from_mapping(dispatch) if dispatch is not None else None)
    except Exception as exc:
        raise SettlementBoundaryError(str(exc)) from exc
    checks = _validate_settlement(normalized, custody_chain, dispatch_decision)
    if not checks["verified"]:
        raise SettlementBoundaryError(checks["reason"])
    return SettlementValidationReport(
        settlement_hash=normalized.settlement_hash,
        dispatch_hash=normalized.dispatch_hash,
        chain_hash=normalized.chain_hash,
        verified=True,
    )


def build_settlement_proof(
    record: SettlementRecord | Mapping[str, Any],
) -> dict[str, Any]:
    normalized = record if isinstance(record, SettlementRecord) else SettlementRecord.from_mapping(record)
    proof = {
        "schema": "afritech.mobility.settlement_proof.v1",
        "authority_boundary": "settlement_proof_read_only",
        "settlement_id": normalized.settlement_id,
        "settlement_hash": normalized.settlement_hash,
        "chain_hash": normalized.chain_hash,
        "dispatch_hash": normalized.dispatch_hash,
        "amounts": {key: _format_decimal(value) for key, value in normalized.amounts},
        "verified": True,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def export_settlement_proof(
    record: SettlementRecord | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    normalized = record if isinstance(record, SettlementRecord) else SettlementRecord.from_mapping(record)
    proof = build_settlement_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "settlement_record.json"
    proof_path = target / "settlement_proof.json"
    json_path.write_text(
        json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    proof_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path, "proof": proof_path}


def _validate_settlement(
    record: SettlementRecord,
    custody: CustodyChain | None,
    dispatch: DispatchDecision | None,
) -> dict[str, Any]:
    if custody is None or dispatch is None:
        return {"verified": False, "reason": "settlement requires custody and dispatch evidence"}
    if record.chain_hash != custody.chain_hash:
        return {"verified": False, "reason": "settlement chain hash mismatch"}
    if record.dispatch_hash != dispatch.decision_hash:
        return {"verified": False, "reason": "settlement dispatch hash mismatch"}
    if record.status not in ALLOWED_STATUSES:
        return {"verified": False, "reason": "invalid settlement status"}
    if not record.events:
        return {"verified": False, "reason": "settlement requires events"}
    if len({event.event_id for event in record.events}) != len(record.events):
        return {"verified": False, "reason": "duplicate settlement event detected"}
    if any(event.timestamp < 0 for event in record.events):
        return {"verified": False, "reason": "invalid settlement event timestamp"}
    if sorted(event.timestamp for event in record.events) != [event.timestamp for event in record.events]:
        return {"verified": False, "reason": "settlement events must be timestamp ordered"}
    if not record.participants:
        return {"verified": False, "reason": "participants required"}
    if set(record.participants) != set(record.amount_map.keys()):
        return {"verified": False, "reason": "participant coverage mismatch"}
    if any(amount < 0 for amount in record.amount_map.values()):
        return {"verified": False, "reason": "negative settlement amount"}
    expected_total = _normalize_amount(sum(record.amount_map.values(), Decimal("0.00")))
    if expected_total != record.gross_amount:
        return {"verified": False, "reason": "settlement amount integrity failure"}
    if record.status == "SETTLED" and not any(event.action == "settled" for event in record.events):
        return {"verified": False, "reason": "settled status requires settled event"}
    if record.status == "SETTLED" and sum(event.action == "settled" for event in record.events) > 1:
        return {"verified": False, "reason": "double settlement detected"}
    if record.status == "PENDING" and any(event.action == "settled" for event in record.events):
        return {"verified": False, "reason": "pending settlement cannot contain settled event"}
    if record.status == "DISPUTED" and not any(event.action == "disputed" for event in record.events):
        return {"verified": False, "reason": "disputed status requires disputed event"}
    if record.settlement_hash != _canonical_hash(
        {
            "amounts": {key: _format_decimal(value) for key, value in record.amounts},
            "chain_hash": record.chain_hash,
            "currency": record.currency,
            "dispatch_hash": record.dispatch_hash,
            "events": [event.canonical_dict() for event in record.events],
            "gross_amount": _format_decimal(record.gross_amount),
            "operation_id": record.operation_id,
            "participants": list(record.participants),
            "settlement_id": record.settlement_id,
            "status": record.status,
        }
    ):
        return {"verified": False, "reason": "settlement hash mismatch"}
    return {"verified": True, "reason": "ok"}


def _dispatch_from_mapping(payload: Mapping[str, Any] | None) -> DispatchDecision:
    if payload is None:
        raise SettlementBoundaryError("dispatch evidence is required")
    if not isinstance(payload, Mapping):
        raise SettlementBoundaryError("dispatch evidence must be a mapping")
    return DispatchDecision.from_mapping(payload)


def _coerce_mapping(value: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return dict(value)


def _normalize_event(event: SettlementEvent | Mapping[str, Any]) -> SettlementEvent:
    if isinstance(event, SettlementEvent):
        return event
    if not isinstance(event, Mapping):
        raise SettlementBoundaryError("settlement events must be mappings or SettlementEvent objects")
    return SettlementEvent.from_mapping(event)


def _format_decimal(value: Decimal) -> str:
    return format(_normalize_amount(value), "f")


__all__ = [
    "ALLOWED_STATUSES",
    "AUTHORITY_BOUNDARY",
    "SCHEMA",
    "SettlementBoundaryError",
    "SettlementEvent",
    "SettlementRecord",
    "SettlementValidationReport",
    "build_settlement_proof",
    "compute_settlement_record",
    "export_settlement_proof",
    "validate_settlement_record",
]
