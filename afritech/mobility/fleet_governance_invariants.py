"""Formal invariants for autonomous fleet governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from afritech.mobility.fleet_governance import (
    AUTHORITY_BOUNDARY,
    FLEET_INVARIANT_IDS,
    INVARIANT_AUTHORITY_BOUNDARY,
    FleetGovernanceError,
    FleetGovernanceReport,
    FleetState,
    build_fleet_governance,
    build_fleet_governance_proof,
)


SCHEMA = "afritech.mobility.fleet_invariant_report.v1"
AUTHORITY_BOUNDARY_INVARIANT = INVARIANT_AUTHORITY_BOUNDARY


class FleetInvariantError(RuntimeError):
    """Raised when a fleet invariant fails."""


@dataclass(frozen=True)
class FleetInvariantCheck:
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
class FleetInvariantReport:
    fleet_hash: str
    report_hash: str
    proof_hash: str
    checks: tuple[FleetInvariantCheck, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY_INVARIANT

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY_INVARIANT and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "checks": [check.canonical_dict() for check in self.checks],
            "fleet_hash": self.fleet_hash,
            "proof_hash": self.proof_hash,
            "report_hash": self.report_hash,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def report_hash_value(self) -> str:
        from hashlib import sha256
        import json

        return sha256(
            json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


def evaluate_fleet_invariants(
    state: FleetState | Mapping[str, Any],
    report: FleetGovernanceReport | Mapping[str, Any] | None = None,
) -> FleetInvariantReport:
    normalized = state if isinstance(state, FleetState) else FleetState.from_mapping(state)
    actual = build_fleet_governance(normalized) if report is None else (report if isinstance(report, FleetGovernanceReport) else build_fleet_governance(normalized))
    expected = build_fleet_governance(normalized)
    checks = (
        _check_traceable_maintenance(normalized),
        _check_derived_trust(actual, expected),
        _check_replayable(normalized, actual, expected),
        _check_explicit_custody(normalized, actual),
        _check_trust_bounds(actual),
        _check_authority_boundary(normalized, actual),
    )
    proof = build_fleet_governance_proof(normalized, actual)
    return FleetInvariantReport(
        fleet_hash=normalized.fleet_hash,
        report_hash=actual.report_hash(),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_fleet_invariants(report: FleetInvariantReport) -> bool:
    if not isinstance(report, FleetInvariantReport):
        raise FleetInvariantError("report must be a FleetInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY_INVARIANT:
        raise FleetInvariantError("fleet invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in FLEET_INVARIANT_IDS if identifier not in observed)
    if missing:
        raise FleetInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise FleetInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_traceable_maintenance(state: FleetState) -> FleetInvariantCheck:
    satisfied = all(
        vehicle.maintenance_history
        and all(record.custody_link and record.evidence_link and record.verified for record in vehicle.maintenance_history)
        for vehicle in state.vehicles
    )
    return FleetInvariantCheck(
        identifier="IA-FLEET-001",
        satisfied=satisfied,
        details="maintenance history is traceable",
        evidence_hash=state.fleet_hash,
    )


def _check_derived_trust(actual: FleetGovernanceReport, expected: FleetGovernanceReport) -> FleetInvariantCheck:
    satisfied = actual.canonical_dict() == expected.canonical_dict() and 0.0 <= actual.fleet_trust_score <= 100.0
    return FleetInvariantCheck(
        identifier="IA-FLEET-002",
        satisfied=satisfied,
        details="fleet trust is derived from operator and vehicle evidence",
        evidence_hash=actual.report_hash(),
    )


def _check_replayable(state: FleetState, actual: FleetGovernanceReport, expected: FleetGovernanceReport) -> FleetInvariantCheck:
    round_tripped_state = FleetState.from_mapping(state.canonical_dict())
    satisfied = actual.canonical_dict() == expected.canonical_dict() and round_tripped_state.canonical_dict() == state.canonical_dict()
    return FleetInvariantCheck(
        identifier="IA-FLEET-003",
        satisfied=satisfied,
        details="vehicle state is replayable",
        evidence_hash=state.fleet_hash,
    )


def _check_explicit_custody(state: FleetState, report: FleetGovernanceReport) -> FleetInvariantCheck:
    custody_links = [record.custody_link for vehicle in state.vehicles for record in vehicle.maintenance_history]
    eligible_ok = all(vehicle.vehicle_id in set(report.eligible_vehicle_ids) for vehicle in state.vehicles if vehicle.eligible_for_dispatch)
    satisfied = bool(custody_links) and eligible_ok and all(link.strip() for link in custody_links)
    return FleetInvariantCheck(
        identifier="IA-FLEET-004",
        satisfied=satisfied,
        details="custody and service evidence are explicit",
        evidence_hash=report.report_hash(),
    )


def _check_trust_bounds(report: FleetGovernanceReport) -> FleetInvariantCheck:
    satisfied = 0.0 <= report.fleet_trust_score <= 100.0 and 0.0 <= report.vehicle_health_score <= 100.0 and 0.0 <= report.maintenance_score <= 100.0
    return FleetInvariantCheck(
        identifier="IA-FLEET-005",
        satisfied=satisfied,
        details="fleet trust remains bounded",
        evidence_hash=report.report_hash(),
    )


def _check_authority_boundary(state: FleetState, report: FleetGovernanceReport) -> FleetInvariantCheck:
    satisfied = state.authority_boundary == AUTHORITY_BOUNDARY and report.authority_boundary == AUTHORITY_BOUNDARY and state.verified and report.verified
    return FleetInvariantCheck(
        identifier="IA-FLEET-006",
        satisfied=satisfied,
        details="fleet governance preserves the authority boundary",
        evidence_hash=state.fleet_hash,
    )


__all__ = [
    "AUTHORITY_BOUNDARY_INVARIANT",
    "FleetInvariantCheck",
    "FleetInvariantError",
    "FleetInvariantReport",
    "SCHEMA",
    "evaluate_fleet_invariants",
    "validate_fleet_invariants",
]

