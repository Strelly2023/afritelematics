"""Deterministic mobility market governance for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.mobility.federation import FederatedParticipant


SCHEMA = "afritech.mobility.market_state.v1"
AUTHORITY_BOUNDARY = "market_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "market_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "market_validation_read_only"
INVARIANT_IDS = (
    "IA-MARKET-001",
    "IA-MARKET-002",
    "IA-MARKET-003",
    "IA-MARKET-004",
    "IA-MARKET-005",
    "IA-MARKET-006",
)

ALLOWED_INCENTIVES = (
    "driver_bonus_10%",
    "driver_bonus_20%",
    "allocation_rebalance_10%",
    "availability_bonus_5%",
    "federation_balance_5%",
)


class MarketGovernanceError(ValueError):
    """Raised when market governance inputs or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketGovernanceError(f"{label} is required")
    return value.strip()


def _require_int(value: object, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or value < minimum:
        raise MarketGovernanceError(f"{label} must be an integer >= {minimum}")
    return value


def _require_number(value: object, label: str, *, minimum: float, maximum: float, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise MarketGovernanceError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise MarketGovernanceError(f"{label} must be between {minimum} and {maximum}")
    return round(number, precision)


def _require_hash(value: object, label: str) -> str:
    value = _require_text(value, label)
    if len(value) != 64:
        raise MarketGovernanceError(f"{label} must be a 64-character hex digest")
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise MarketGovernanceError("mapping expected")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_text_tuple(values: Iterable[object], label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise MarketGovernanceError(f"{label} must be iterable")
    normalized = tuple(_require_text(value, label[:-1] if label.endswith("s") else label) for value in values)
    return tuple(sorted(set(normalized)))


def _decimal(value: object, label: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive
        raise MarketGovernanceError(f"{label} must be numeric") from exc


def _format_decimal(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, round(value, 6)))


@dataclass(frozen=True)
class MarketAllocation:
    allocation_id: str
    participant_id: str
    region_id: str
    assignment_count: int
    timestamp: int
    evidence_link: str
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "allocation_id", _require_text(self.allocation_id, "allocation_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "region_id", _require_text(self.region_id, "region_id"))
        object.__setattr__(self, "assignment_count", _require_int(self.assignment_count, "assignment_count", minimum=1))
        if not isinstance(self.timestamp, int):
            raise MarketGovernanceError("timestamp must be an integer")
        object.__setattr__(self, "evidence_link", _require_text(self.evidence_link, "evidence_link"))
        if not isinstance(self.verified, bool) or not self.verified:
            raise MarketGovernanceError("market allocations must be verified")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MarketAllocation":
        if not isinstance(payload, Mapping):
            raise MarketGovernanceError("allocation payload must be a mapping")
        return cls(
            allocation_id=_require_text(payload.get("allocation_id") or payload.get("id"), "allocation_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            region_id=_require_text(payload.get("region_id"), "region_id"),
            assignment_count=int(payload.get("assignment_count", 1)),
            timestamp=int(payload.get("timestamp", 0)),
            evidence_link=_require_text(payload.get("evidence_link") or payload.get("evidence"), "evidence_link"),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "allocation_hash": self.allocation_hash,
            "allocation_id": self.allocation_id,
            "assignment_count": self.assignment_count,
            "evidence_link": self.evidence_link,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "region_id": self.region_id,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }

    @property
    def allocation_hash(self) -> str:
        payload = {
            "allocation_id": self.allocation_id,
            "assignment_count": self.assignment_count,
            "evidence_link": self.evidence_link,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "region_id": self.region_id,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }
        return _canonical_hash(payload)


@dataclass(frozen=True)
class MarketState:
    market_id: str
    region_id: str
    demand: int
    supply: int
    base_price: Decimal
    currency: str
    participants: tuple[FederatedParticipant, ...] = field(default_factory=tuple)
    allocation_history: tuple[MarketAllocation, ...] = field(default_factory=tuple)
    active_incentives: tuple[str, ...] = field(default_factory=tuple)
    timestamp: int = 0
    price_multiplier_hint: float = 1.0
    price_floor: float = 0.75
    price_ceiling: float = 2.5
    max_allocation_share: float = 0.35
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_text(self.market_id, "market_id"))
        object.__setattr__(self, "region_id", _require_text(self.region_id, "region_id"))
        object.__setattr__(self, "demand", _require_int(self.demand, "demand"))
        object.__setattr__(self, "supply", _require_int(self.supply, "supply"))
        object.__setattr__(self, "base_price", _decimal(self.base_price, "base_price"))
        object.__setattr__(self, "currency", _require_text(self.currency, "currency"))
        participants = tuple(
            item if isinstance(item, FederatedParticipant) else FederatedParticipant.from_mapping(item)
            for item in self.participants
        )
        participants = tuple(sorted(participants, key=lambda participant: participant.participant_id))
        if not participants:
            raise MarketGovernanceError("at least one market participant is required")
        object.__setattr__(self, "participants", participants)
        allocations = tuple(
            item if isinstance(item, MarketAllocation) else MarketAllocation.from_mapping(item)
            for item in self.allocation_history
        )
        object.__setattr__(self, "allocation_history", tuple(sorted(allocations, key=lambda item: (item.timestamp, item.allocation_id))))
        object.__setattr__(self, "active_incentives", _normalize_incentives(self.active_incentives))
        if not isinstance(self.timestamp, int):
            raise MarketGovernanceError("timestamp must be an integer")
        object.__setattr__(self, "price_multiplier_hint", _require_number(self.price_multiplier_hint, "price_multiplier_hint", minimum=0.5, maximum=2.5))
        object.__setattr__(self, "price_floor", _require_number(self.price_floor, "price_floor", minimum=0.5, maximum=2.5))
        object.__setattr__(self, "price_ceiling", _require_number(self.price_ceiling, "price_ceiling", minimum=0.5, maximum=4.0))
        object.__setattr__(self, "max_allocation_share", _require_number(self.max_allocation_share, "max_allocation_share", minimum=0.0, maximum=1.0))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MarketState":
        if not isinstance(payload, Mapping):
            raise MarketGovernanceError("market state payload must be a mapping")
        return cls(
            market_id=_require_text(payload.get("market_id") or payload.get("id"), "market_id"),
            region_id=_require_text(payload.get("region_id"), "region_id"),
            demand=int(payload.get("demand", 0)),
            supply=int(payload.get("supply", 0)),
            base_price=_decimal(payload.get("base_price", 0), "base_price"),
            currency=_require_text(payload.get("currency", "AUD"), "currency"),
            participants=tuple(payload.get("participants", ())),  # type: ignore[arg-type]
            allocation_history=tuple(payload.get("allocation_history", ())),  # type: ignore[arg-type]
            active_incentives=tuple(payload.get("active_incentives", ())),  # type: ignore[arg-type]
            timestamp=int(payload.get("timestamp", 0)),
            price_multiplier_hint=float(payload.get("price_multiplier_hint", 1.0)),
            price_floor=float(payload.get("price_floor", 0.75)),
            price_ceiling=float(payload.get("price_ceiling", 2.5)),
            max_allocation_share=float(payload.get("max_allocation_share", 0.35)),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and len(self.market_hash) == 64
            and all(participant.verified for participant in self.participants)
            and all(allocation.verified for allocation in self.allocation_history)
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "active_incentives": list(self.active_incentives),
            "allocation_history": [allocation.canonical_dict() for allocation in self.allocation_history],
            "authority_boundary": self.authority_boundary,
            "base_price": _format_decimal(self.base_price),
            "currency": self.currency,
            "demand": self.demand,
            "market_hash": self.market_hash,
            "market_id": self.market_id,
            "max_allocation_share": round(self.max_allocation_share, 6),
            "participants": [participant.canonical_dict() for participant in self.participants],
            "price_ceiling": round(self.price_ceiling, 6),
            "price_floor": round(self.price_floor, 6),
            "price_multiplier_hint": round(self.price_multiplier_hint, 6),
            "region_id": self.region_id,
            "schema": SCHEMA,
            "supply": self.supply,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }

    @property
    def market_hash(self) -> str:
        payload = {
            "active_incentives": list(self.active_incentives),
            "allocation_history": [allocation.canonical_dict() for allocation in self.allocation_history],
            "authority_boundary": self.authority_boundary,
            "base_price": _format_decimal(self.base_price),
            "currency": self.currency,
            "demand": self.demand,
            "market_id": self.market_id,
            "max_allocation_share": round(self.max_allocation_share, 6),
            "participants": [participant.canonical_dict() for participant in self.participants],
            "price_ceiling": round(self.price_ceiling, 6),
            "price_floor": round(self.price_floor, 6),
            "price_multiplier_hint": round(self.price_multiplier_hint, 6),
            "region_id": self.region_id,
            "schema": SCHEMA,
            "supply": self.supply,
            "timestamp": self.timestamp,
        }
        return _canonical_hash(payload)


@dataclass(frozen=True)
class MarketDecision:
    market_id: str
    region_id: str
    state_hash: str
    adjusted_price: Decimal
    price_multiplier: float
    incentive_plan: tuple[str, ...]
    dispatch_bias: tuple[tuple[str, float], ...]
    fairness_metrics: tuple[tuple[str, Any], ...]
    evidence: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_text(self.market_id, "market_id"))
        object.__setattr__(self, "region_id", _require_text(self.region_id, "region_id"))
        object.__setattr__(self, "state_hash", _require_hash(self.state_hash, "state_hash"))
        object.__setattr__(self, "adjusted_price", _decimal(self.adjusted_price, "adjusted_price"))
        object.__setattr__(self, "price_multiplier", _require_number(self.price_multiplier, "price_multiplier", minimum=0.5, maximum=4.0))
        object.__setattr__(self, "incentive_plan", _normalize_incentives(self.incentive_plan))
        object.__setattr__(self, "dispatch_bias", _normalize_bias(self.dispatch_bias))
        object.__setattr__(self, "fairness_metrics", _freeze_pairs(self.fairness_metrics))
        object.__setattr__(self, "evidence", _freeze_pairs(self.evidence))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MarketDecision":
        if not isinstance(payload, Mapping):
            raise MarketGovernanceError("market decision payload must be a mapping")
        return cls(
            market_id=_require_text(payload.get("market_id"), "market_id"),
            region_id=_require_text(payload.get("region_id"), "region_id"),
            state_hash=_require_text(payload.get("state_hash"), "state_hash"),
            adjusted_price=_decimal(payload.get("adjusted_price"), "adjusted_price"),
            price_multiplier=float(payload.get("price_multiplier", 1.0)),
            incentive_plan=tuple(payload.get("incentive_plan", ())),  # type: ignore[arg-type]
            dispatch_bias=_normalize_bias(payload.get("dispatch_bias", ())),  # type: ignore[arg-type]
            fairness_metrics=_freeze_pairs(payload.get("fairness_metrics", {})),  # type: ignore[arg-type]
            evidence=_freeze_pairs(payload.get("evidence", {})),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and len(self.decision_hash) == 64
            and len(self.state_hash) == 64
            and bool(self.dispatch_bias)
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "adjusted_price": _format_decimal(self.adjusted_price),
            "authority_boundary": self.authority_boundary,
            "decision_hash": self.decision_hash,
            "dispatch_bias": [{"participant_id": participant_id, "bias": round(bias, 6)} for participant_id, bias in self.dispatch_bias],
            "evidence": dict(self.evidence),
            "fairness_metrics": dict(self.fairness_metrics),
            "incentive_plan": list(self.incentive_plan),
            "market_id": self.market_id,
            "price_multiplier": round(self.price_multiplier, 6),
            "region_id": self.region_id,
            "schema": "afritech.mobility.market_decision.v1",
            "state_hash": self.state_hash,
            "verified": self.verified,
        }

    @property
    def decision_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "adjusted_price": _format_decimal(self.adjusted_price),
            "authority_boundary": self.authority_boundary,
            "dispatch_bias": [{"participant_id": participant_id, "bias": round(bias, 6)} for participant_id, bias in self.dispatch_bias],
            "evidence": dict(self.evidence),
            "fairness_metrics": dict(self.fairness_metrics),
            "incentive_plan": list(self.incentive_plan),
            "market_id": self.market_id,
            "price_multiplier": round(self.price_multiplier, 6),
            "region_id": self.region_id,
            "schema": "afritech.mobility.market_decision.v1",
            "state_hash": self.state_hash,
        }

    def bias_for(self, participant_id: str) -> float:
        for entry_participant_id, bias in self.dispatch_bias:
            if entry_participant_id == participant_id:
                return bias
        raise MarketGovernanceError(f"unknown participant_id: {participant_id}")


@dataclass(frozen=True)
class MarketInvariantCheck:
    identifier: str
    satisfied: bool
    details: str
    evidence_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "details": self.details,
            "evidence_hash": self.evidence_hash,
            "identifier": self.identifier,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class MarketInvariantReport:
    market_hash: str
    decision_hash: str
    check_hash: str
    proof_hash: str
    checks: tuple[MarketInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "decision_hash": self.decision_hash,
            "market_hash": self.market_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.market_invariant_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class MarketValidationReport:
    market_hash: str
    decision_hash: str
    expected_decision_hash: str
    invariant_report_hash: str
    proof_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "decision_hash": self.decision_hash,
            "expected_decision_hash": self.expected_decision_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "market_hash": self.market_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.market_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def build_market_decision(state: MarketState | Mapping[str, Any]) -> MarketDecision:
    normalized = state if isinstance(state, MarketState) else MarketState.from_mapping(state)
    share_map = _allocation_share_map(normalized.allocation_history)
    network_share_map = _network_share_map(normalized.participants, normalized.allocation_history)
    avg_local_trust = _average(participant.trust_profile.trust_score for participant in normalized.participants)
    avg_federated_trust = _average(participant.federated_trust_score for participant in normalized.participants)
    participant_concentration = max(share_map.values(), default=0.0)
    network_concentration = max(network_share_map.values(), default=0.0)
    demand_gap = normalized.demand - normalized.supply
    supply_pressure = max(0.0, demand_gap) / max(1.0, float(normalized.supply))
    supply_surplus = max(0.0, -demand_gap) / max(1.0, float(normalized.demand or 1))
    trust_component = (((avg_local_trust + avg_federated_trust) / 2.0) - 50.0) / 500.0
    pressure_component = min(0.8, supply_pressure * 0.45) - min(0.15, supply_surplus * 0.10)
    fairness_component = -min(0.08, participant_concentration * 0.08) - min(0.05, network_concentration * 0.05)
    hint_component = (normalized.price_multiplier_hint - 1.0) * 0.5
    price_multiplier = _clamp(
        1.0 + pressure_component + trust_component + fairness_component + hint_component,
        normalized.price_floor,
        normalized.price_ceiling,
    )
    adjusted_price = (normalized.base_price * Decimal(str(price_multiplier))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    incentive_plan = _market_incentives(normalized, price_multiplier, supply_pressure, supply_surplus, participant_concentration, network_concentration)
    dispatch_bias = _dispatch_bias(normalized, share_map, network_share_map)
    fairness_metrics = _fairness_metrics(
        normalized,
        avg_local_trust=avg_local_trust,
        avg_federated_trust=avg_federated_trust,
        participant_concentration=participant_concentration,
        network_concentration=network_concentration,
        demand_gap=demand_gap,
        supply_pressure=supply_pressure,
        supply_surplus=supply_surplus,
        price_multiplier=price_multiplier,
        incentive_plan=incentive_plan,
    )
    evidence = _market_evidence(normalized, fairness_metrics, incentive_plan, dispatch_bias, price_multiplier, adjusted_price)
    return MarketDecision(
        market_id=normalized.market_id,
        region_id=normalized.region_id,
        state_hash=normalized.market_hash,
        adjusted_price=adjusted_price,
        price_multiplier=price_multiplier,
        incentive_plan=incentive_plan,
        dispatch_bias=dispatch_bias,
        fairness_metrics=tuple(sorted(fairness_metrics.items(), key=lambda item: item[0])),
        evidence=tuple(sorted(evidence.items(), key=lambda item: item[0])),
    )


compute_market_decision = build_market_decision


def validate_market_decision(
    state: MarketState | Mapping[str, Any],
    decision: MarketDecision | Mapping[str, Any],
) -> MarketValidationReport:
    supplied_hash = decision.get("decision_hash") if isinstance(decision, Mapping) else None
    normalized_state = state if isinstance(state, MarketState) else MarketState.from_mapping(state)
    actual = decision if isinstance(decision, MarketDecision) else MarketDecision.from_mapping(decision)
    expected = build_market_decision(normalized_state)
    invariant_report = evaluate_market_invariants(normalized_state, actual)
    validate_market_invariants(invariant_report)
    if actual.canonical_dict() != expected.canonical_dict():
        raise MarketGovernanceError("market decision mismatch")
    if actual.decision_hash != expected.decision_hash:
        raise MarketGovernanceError("market decision hash mismatch")
    if supplied_hash is not None and _require_hash(supplied_hash, "decision_hash") != actual.decision_hash:
        raise MarketGovernanceError("supplied market decision hash mismatch")
    proof = _market_proof_payload(normalized_state, actual, verified=actual.verified and invariant_report.verified)
    report = MarketValidationReport(
        market_hash=normalized_state.market_hash,
        decision_hash=actual.decision_hash,
        expected_decision_hash=expected.decision_hash,
        invariant_report_hash=invariant_report.report_hash(),
        proof_hash=proof["proof_hash"],
        verified=proof["verified"],
    )
    if not report.verified:
        raise MarketGovernanceError("market decision failed validation")
    return report


def build_market_decision_proof(
    state: MarketState | Mapping[str, Any],
    decision: MarketDecision | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_state = state if isinstance(state, MarketState) else MarketState.from_mapping(state)
    actual = build_market_decision(normalized_state) if decision is None else (decision if isinstance(decision, MarketDecision) else MarketDecision.from_mapping(decision))
    report = validate_market_decision(normalized_state, actual)
    return _market_proof_payload(normalized_state, actual, verified=report.verified)


def export_market_decision_proof(
    state: MarketState | Mapping[str, Any],
    output_dir: str | Path,
    decision: MarketDecision | Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    normalized_state = state if isinstance(state, MarketState) else MarketState.from_mapping(state)
    actual = build_market_decision(normalized_state) if decision is None else (decision if isinstance(decision, MarketDecision) else MarketDecision.from_mapping(decision))
    proof = build_market_decision_proof(normalized_state, actual)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "market_state.json"
    proof_path = target / "market_decision_proof.json"
    state_path.write_text(
        json.dumps(normalized_state.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    proof_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": state_path, "proof": proof_path}


def evaluate_market_invariants(
    state: MarketState | Mapping[str, Any],
    decision: MarketDecision | Mapping[str, Any] | None = None,
) -> MarketInvariantReport:
    normalized = state if isinstance(state, MarketState) else MarketState.from_mapping(state)
    actual = build_market_decision(normalized) if decision is None else (decision if isinstance(decision, MarketDecision) else MarketDecision.from_mapping(decision))
    expected = build_market_decision(normalized)
    checks = (
        _check_pricing_deterministic(normalized, actual, expected),
        _check_supply_demand_balance(normalized, actual),
        _check_incentives_evidence_backed(normalized, actual),
        _check_allocation_balanced_over_time(normalized, actual),
        _check_replayable(normalized, actual, expected),
        _check_no_authority(normalized, actual),
    )
    proof = _market_proof_payload(normalized, actual, verified=normalized.verified and actual.verified and all(check.satisfied for check in checks))
    return MarketInvariantReport(
        market_hash=normalized.market_hash,
        decision_hash=actual.decision_hash,
        check_hash=_hash_checks(checks),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_market_invariants(report: MarketInvariantReport) -> bool:
    if not isinstance(report, MarketInvariantReport):
        raise MarketGovernanceError("report must be a MarketInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise MarketGovernanceError("market invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise MarketGovernanceError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise MarketGovernanceError(f"{check.identifier} failed: {check.details}")
    return True


def _market_proof_payload(state: MarketState, decision: MarketDecision, *, verified: bool) -> dict[str, Any]:
    proof = {
        "schema": "afritech.mobility.market_decision_proof.v1",
        "authority_boundary": VALIDATION_AUTHORITY_BOUNDARY,
        "market_id": state.market_id,
        "region_id": state.region_id,
        "state_hash": state.market_hash,
        "decision_hash": decision.decision_hash,
        "adjusted_price": _format_decimal(decision.adjusted_price),
        "price_multiplier": round(decision.price_multiplier, 6),
        "incentive_plan": list(decision.incentive_plan),
        "dispatch_bias": [{"participant_id": participant_id, "bias": round(bias, 6)} for participant_id, bias in decision.dispatch_bias],
        "fairness_metrics": dict(decision.fairness_metrics),
        "verified": verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def _check_pricing_deterministic(
    state: MarketState,
    actual: MarketDecision,
    expected: MarketDecision,
) -> MarketInvariantCheck:
    satisfied = actual.canonical_dict() == expected.canonical_dict()
    return MarketInvariantCheck(
        identifier="IA-MARKET-001",
        satisfied=satisfied,
        details="same inputs produce the same price",
        evidence_hash=actual.decision_hash,
    )


def _check_supply_demand_balance(state: MarketState, decision: MarketDecision) -> MarketInvariantCheck:
    fairness = dict(decision.fairness_metrics)
    balanced = bool(fairness.get("supply_demand_balanced")) and fairness.get("demand_gap") == state.demand - state.supply
    if state.demand > state.supply:
        balanced = balanced and decision.price_multiplier > 1.0 and any(
            item in decision.incentive_plan for item in ("driver_bonus_10%", "driver_bonus_20%", "availability_bonus_5%")
        )
    return MarketInvariantCheck(
        identifier="IA-MARKET-002",
        satisfied=balanced,
        details="supply-demand balance is enforced",
        evidence_hash=decision.decision_hash,
    )


def _check_incentives_evidence_backed(state: MarketState, decision: MarketDecision) -> MarketInvariantCheck:
    evidence = dict(decision.evidence)
    incentives = tuple(evidence.get("incentive_plan", ()))
    allowed = set(ALLOWED_INCENTIVES) | set(state.active_incentives)
    satisfied = set(decision.incentive_plan).issubset(allowed) and tuple(sorted(decision.incentive_plan)) == tuple(sorted(incentives))
    return MarketInvariantCheck(
        identifier="IA-MARKET-003",
        satisfied=satisfied,
        details="incentives are evidence-backed",
        evidence_hash=decision.decision_hash,
    )


def _check_allocation_balanced_over_time(state: MarketState, decision: MarketDecision) -> MarketInvariantCheck:
    fairness = dict(decision.fairness_metrics)
    concentration = float(fairness.get("allocation_concentration", 0.0))
    rebalance_required = bool(fairness.get("rebalance_required"))
    dispatch_bias = dict(decision.dispatch_bias)
    if concentration <= state.max_allocation_share:
        satisfied = True
    else:
        if "allocation_rebalance_10%" not in decision.incentive_plan:
            satisfied = False
        else:
            min_bias = min(dispatch_bias.values(), default=0.0)
            max_bias = max(dispatch_bias.values(), default=0.0)
            satisfied = min_bias < max_bias and rebalance_required
    return MarketInvariantCheck(
        identifier="IA-MARKET-004",
        satisfied=satisfied,
        details="allocation remains balanced over time",
        evidence_hash=decision.decision_hash,
    )


def _check_replayable(state: MarketState, actual: MarketDecision, expected: MarketDecision) -> MarketInvariantCheck:
    satisfied = actual.canonical_dict() == expected.canonical_dict() and state.canonical_dict() == MarketState.from_mapping(state.canonical_dict()).canonical_dict()
    return MarketInvariantCheck(
        identifier="IA-MARKET-005",
        satisfied=satisfied,
        details="market rules are replayable",
        evidence_hash=state.market_hash,
    )


def _check_no_authority(state: MarketState, decision: MarketDecision) -> MarketInvariantCheck:
    satisfied = (
        state.authority_boundary == AUTHORITY_BOUNDARY
        and decision.authority_boundary == AUTHORITY_BOUNDARY
        and decision.verified
        and state.verified
    )
    return MarketInvariantCheck(
        identifier="IA-MARKET-006",
        satisfied=satisfied,
        details="market decisions do not override proof authority",
        evidence_hash=decision.decision_hash,
    )


def _hash_checks(checks: tuple[MarketInvariantCheck, ...]) -> str:
    return _canonical_hash([check.canonical_dict() for check in checks])


def _normalize_incentives(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise MarketGovernanceError("incentives must be iterable")
    normalized = tuple(_require_text(value, "incentive") for value in values)
    invalid = sorted(set(value for value in normalized if value not in ALLOWED_INCENTIVES))
    if invalid:
        raise MarketGovernanceError("unsupported incentive(s): " + ", ".join(invalid))
    return tuple(sorted(set(normalized)))


def _normalize_bias(values: Iterable[object] | Mapping[str, Any]) -> tuple[tuple[str, float], ...]:
    if isinstance(values, Mapping):
        items = values.items()
    elif isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise MarketGovernanceError("dispatch_bias must be iterable")
    else:
        items = values
    normalized: list[tuple[str, float]] = []
    for item in items:
        if isinstance(item, Mapping):
            participant_id = _require_text(item.get("participant_id"), "participant_id")
            bias = _require_number(item.get("bias", 0.0), "bias", minimum=0.0, maximum=1.0)
        else:
            participant_id, bias = item  # type: ignore[misc]
            participant_id = _require_text(participant_id, "participant_id")
            bias = _require_number(bias, "bias", minimum=0.0, maximum=1.0)
        normalized.append((participant_id, bias))
    return tuple(sorted(normalized, key=lambda entry: entry[0]))


def _freeze_pairs(values: Iterable[object] | Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    if isinstance(values, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in values.items()))
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise MarketGovernanceError("mapping expected")
    normalized: list[tuple[str, Any]] = []
    for item in values:
        if isinstance(item, Mapping):
            if "participant_id" in item and "bias" in item:
                normalized.append((str(item["participant_id"]), _freeze_value(item["bias"])))
            else:
                for key, val in item.items():
                    normalized.append((str(key), _freeze_value(val)))
        else:
            key, val = item  # type: ignore[misc]
            normalized.append((str(key), _freeze_value(val)))
    return tuple(sorted(normalized, key=lambda entry: entry[0]))


def _allocation_share_map(history: tuple[MarketAllocation, ...]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for allocation in history:
        counts[allocation.participant_id] = counts.get(allocation.participant_id, 0) + allocation.assignment_count
    total = sum(counts.values())
    if total <= 0:
        return {}
    return {participant_id: count / total for participant_id, count in counts.items()}


def _network_share_map(participants: tuple[FederatedParticipant, ...], history: tuple[MarketAllocation, ...]) -> dict[str, float]:
    participant_by_id = {participant.participant_id: participant for participant in participants}
    counts: dict[str, int] = {}
    for allocation in history:
        participant = participant_by_id.get(allocation.participant_id)
        if participant is None:
            continue
        counts[participant.home_network] = counts.get(participant.home_network, 0) + allocation.assignment_count
    total = sum(counts.values())
    if total <= 0:
        return {}
    return {network_id: count / total for network_id, count in counts.items()}


def _average(values: Iterable[float]) -> float:
    items = list(values)
    return round(sum(items) / len(items), 6) if items else 0.0


def _market_incentives(
    state: MarketState,
    price_multiplier: float,
    demand_pressure: float,
    supply_surplus: float,
    participant_concentration: float,
    network_concentration: float,
) -> tuple[str, ...]:
    incentives = set(state.active_incentives)
    if demand_pressure > 0.25:
        incentives.add("driver_bonus_20%" if demand_pressure > 0.5 else "driver_bonus_10%")
    if supply_surplus > 0.2:
        incentives.add("availability_bonus_5%")
    if participant_concentration > state.max_allocation_share or network_concentration > state.max_allocation_share:
        incentives.add("allocation_rebalance_10%")
    if price_multiplier > 1.1 and participant_concentration <= state.max_allocation_share:
        incentives.add("federation_balance_5%")
    return tuple(sorted(incentives))


def _dispatch_bias(
    state: MarketState,
    share_map: Mapping[str, float],
    network_share_map: Mapping[str, float],
) -> tuple[tuple[str, float], ...]:
    participant_by_id = {participant.participant_id: participant for participant in state.participants}
    raw_scores: dict[str, float] = {}
    for participant in state.participants:
        local_norm = participant.local_trust_score / 100.0
        federated_norm = participant.federated_trust_score / 100.0
        share = share_map.get(participant.participant_id, 0.0)
        network_share = network_share_map.get(participant.home_network, 0.0)
        verified_bonus = 1.0 if participant.verified else 0.0
        raw = (
            0.30 * local_norm
            + 0.30 * federated_norm
            + 0.15 * verified_bonus
            + 0.15 * (1.0 - share)
            + 0.10 * (1.0 - network_share)
        )
        raw = max(0.0, raw - max(0.0, share - state.max_allocation_share) * 0.5)
        raw_scores[participant.participant_id] = raw
    total = sum(raw_scores.values())
    if total <= 0:
        equal_weight = round(1.0 / len(participant_by_id), 6)
        return tuple(sorted(((participant.participant_id, equal_weight) for participant in state.participants), key=lambda entry: entry[0]))
    normalized = tuple(
        sorted(((participant_id, round(score / total, 6)) for participant_id, score in raw_scores.items()), key=lambda entry: entry[0])
    )
    return normalized


def _fairness_metrics(
    state: MarketState,
    *,
    avg_local_trust: float,
    avg_federated_trust: float,
    participant_concentration: float,
    network_concentration: float,
    demand_gap: int,
    supply_pressure: float,
    supply_surplus: float,
    price_multiplier: float,
    incentive_plan: tuple[str, ...],
) -> dict[str, Any]:
    supply_demand_balanced = demand_gap <= 0 or bool(incentive_plan)
    return {
        "active_incentives_count": len(state.active_incentives),
        "allocation_concentration": round(participant_concentration, 6),
        "average_federated_trust": round(avg_federated_trust, 6),
        "average_local_trust": round(avg_local_trust, 6),
        "demand_gap": demand_gap,
        "network_concentration": round(network_concentration, 6),
        "normalized_bias_sum": 1.0,
        "price_multiplier_hint": round(state.price_multiplier_hint, 6),
        "rebalance_required": participant_concentration > state.max_allocation_share or network_concentration > state.max_allocation_share,
        "supply_demand_balanced": supply_demand_balanced,
        "supply_pressure": round(supply_pressure, 6),
        "supply_surplus": round(supply_surplus, 6),
        "window_timestamp": state.timestamp,
        "price_multiplier": round(price_multiplier, 6),
    }


def _market_evidence(
    state: MarketState,
    fairness_metrics: Mapping[str, Any],
    incentive_plan: tuple[str, ...],
    dispatch_bias: tuple[tuple[str, float], ...],
    price_multiplier: float,
    adjusted_price: Decimal,
) -> dict[str, Any]:
    return {
        "base_price": _format_decimal(state.base_price),
        "demand": state.demand,
        "dispatch_bias": [{"participant_id": participant_id, "bias": round(bias, 6)} for participant_id, bias in dispatch_bias],
        "fairness_metrics": dict(fairness_metrics),
        "formula": "base_price * bounded_multiplier with fairness and trust adjustments",
        "incentive_plan": list(incentive_plan),
        "market_id": state.market_id,
        "participant_count": len(state.participants),
        "price_multiplier": round(price_multiplier, 6),
        "region_id": state.region_id,
        "state_hash": state.market_hash,
        "supply": state.supply,
        "adjusted_price": _format_decimal(adjusted_price),
    }


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive fallback for aliases
    if name == "run_market_governance":
        return build_market_decision
    raise AttributeError(name)


__all__ = [
    "ALLOWED_INCENTIVES",
    "AUTHORITY_BOUNDARY",
    "MarketAllocation",
    "MarketDecision",
    "MarketGovernanceError",
    "MarketInvariantCheck",
    "MarketInvariantReport",
    "MarketState",
    "MarketValidationReport",
    "build_market_decision",
    "build_market_decision_proof",
    "compute_market_decision",
    "export_market_decision_proof",
    "validate_market_decision",
    "validate_market_invariants",
    "evaluate_market_invariants",
]
