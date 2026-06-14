"""Formal invariants for mobility market governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from afritech.mobility.market import (
    AUTHORITY_BOUNDARY,
    MarketGovernanceError,
    MarketState,
    build_market_decision,
    build_market_decision_proof,
)


SCHEMA = "afritech.mobility.market_invariant_report.v1"
AUTHORITY_BOUNDARY_INVARIANT = "market_invariant_read_only"
INVARIANT_IDS = (
    "IA-MARKET-001",
    "IA-MARKET-002",
    "IA-MARKET-003",
    "IA-MARKET-004",
    "IA-MARKET-005",
    "IA-MARKET-006",
)


class MarketInvariantError(RuntimeError):
    """Raised when a market invariant fails."""


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
    authority_boundary: str = AUTHORITY_BOUNDARY_INVARIANT

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY_INVARIANT and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "decision_hash": self.decision_hash,
            "market_hash": self.market_hash,
            "proof_hash": self.proof_hash,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        from hashlib import sha256
        import json

        return sha256(
            json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


def evaluate_market_invariants(
    state: MarketState | Mapping[str, Any],
    decision: Any | None = None,
) -> MarketInvariantReport:
    normalized = state if isinstance(state, MarketState) else MarketState.from_mapping(state)
    actual = build_market_decision(normalized) if decision is None else (decision if hasattr(decision, "canonical_dict") else build_market_decision(normalized))
    expected = build_market_decision(normalized)
    checks = (
        _check_pricing_deterministic(actual, expected),
        _check_supply_demand_balance(normalized, actual),
        _check_incentives_evidence_backed(normalized, actual),
        _check_allocation_balanced_over_time(normalized, actual),
        _check_replayable(normalized, actual, expected),
        _check_no_authority(normalized, actual),
    )
    proof = build_market_decision_proof(normalized, actual)
    return MarketInvariantReport(
        market_hash=normalized.market_hash,
        decision_hash=actual.decision_hash,
        check_hash=_hash_checks(checks),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_market_invariants(report: MarketInvariantReport) -> bool:
    if not isinstance(report, MarketInvariantReport):
        raise MarketInvariantError("report must be a MarketInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY_INVARIANT:
        raise MarketInvariantError("market invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise MarketInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise MarketInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_pricing_deterministic(actual: Any, expected: Any) -> MarketInvariantCheck:
    return MarketInvariantCheck(
        identifier="IA-MARKET-001",
        satisfied=actual.canonical_dict() == expected.canonical_dict(),
        details="pricing is deterministic",
        evidence_hash=actual.decision_hash,
    )


def _check_supply_demand_balance(state: MarketState, decision: Any) -> MarketInvariantCheck:
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


def _check_incentives_evidence_backed(state: MarketState, decision: Any) -> MarketInvariantCheck:
    evidence = dict(decision.evidence)
    incentives = tuple(evidence.get("incentive_plan", ()))
    allowed = set(state.active_incentives) | {
        "driver_bonus_10%",
        "driver_bonus_20%",
        "allocation_rebalance_10%",
        "availability_bonus_5%",
        "federation_balance_5%",
    }
    return MarketInvariantCheck(
        identifier="IA-MARKET-003",
        satisfied=set(decision.incentive_plan).issubset(allowed) and tuple(sorted(decision.incentive_plan)) == tuple(sorted(incentives)),
        details="incentives are evidence-backed",
        evidence_hash=decision.decision_hash,
    )


def _check_allocation_balanced_over_time(state: MarketState, decision: Any) -> MarketInvariantCheck:
    fairness = dict(decision.fairness_metrics)
    concentration = float(fairness.get("allocation_concentration", 0.0))
    rebalance_required = bool(fairness.get("rebalance_required"))
    dispatch_bias = dict(decision.dispatch_bias)
    if concentration <= state.max_allocation_share:
        satisfied = True
    else:
        satisfied = "allocation_rebalance_10%" in decision.incentive_plan and rebalance_required and min(dispatch_bias.values(), default=0.0) < max(dispatch_bias.values(), default=0.0)
    return MarketInvariantCheck(
        identifier="IA-MARKET-004",
        satisfied=satisfied,
        details="allocation remains balanced over time",
        evidence_hash=decision.decision_hash,
    )


def _check_replayable(state: MarketState, actual: Any, expected: Any) -> MarketInvariantCheck:
    return MarketInvariantCheck(
        identifier="IA-MARKET-005",
        satisfied=actual.canonical_dict() == expected.canonical_dict() and state.canonical_dict() == MarketState.from_mapping(state.canonical_dict()).canonical_dict(),
        details="market rules are replayable",
        evidence_hash=state.market_hash,
    )


def _check_no_authority(state: MarketState, decision: Any) -> MarketInvariantCheck:
    return MarketInvariantCheck(
        identifier="IA-MARKET-006",
        satisfied=state.authority_boundary == AUTHORITY_BOUNDARY and decision.authority_boundary == AUTHORITY_BOUNDARY and decision.verified and state.verified,
        details="market decisions do not override proof authority",
        evidence_hash=decision.decision_hash,
    )


def _hash_checks(checks: tuple[MarketInvariantCheck, ...]) -> str:
    from hashlib import sha256
    import json

    return sha256(
        json.dumps([check.canonical_dict() for check in checks], sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY_INVARIANT",
    "INVARIANT_IDS",
    "SCHEMA",
    "MarketInvariantCheck",
    "MarketInvariantError",
    "MarketInvariantReport",
    "evaluate_market_invariants",
    "validate_market_invariants",
]
