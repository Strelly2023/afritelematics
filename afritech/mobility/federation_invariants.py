"""Formal invariants for the federated mobility infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from afritech.mobility.federation import (
    AUTHORITY_BOUNDARY,
    FederationError,
    FederationState,
    build_federation_proof,
    build_federation_state,
)


SCHEMA = "afritech.mobility.federation_invariant_report.v1"
AUTHORITY_BOUNDARY_INVARIANT = "federation_invariant_read_only"
INVARIANT_IDS = (
    "IA-FEDERATION-001",
    "IA-FEDERATION-002",
    "IA-FEDERATION-003",
    "IA-FEDERATION-004",
    "IA-FEDERATION-005",
    "IA-FEDERATION-006",
)


class FederationInvariantError(RuntimeError):
    """Raised when a federation invariant fails."""


@dataclass(frozen=True)
class FederationInvariantCheck:
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
class FederationInvariantReport:
    federation_hash: str
    check_hash: str
    proof_hash: str
    checks: tuple[FederationInvariantCheck, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY_INVARIANT

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY_INVARIANT and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "federation_hash": self.federation_hash,
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


def evaluate_federation_invariants(state: FederationState | Mapping[str, Any]) -> FederationInvariantReport:
    normalized = state if isinstance(state, FederationState) else FederationState.from_mapping(state)
    replay = build_federation_state(
        normalized.federation_id,
        normalized.participants,
        units=normalized.units,
        transitions=normalized.transitions,
    )
    checks = (
        _check_membership_verifiable(normalized),
        _check_trust_transfer_bounded(normalized),
        _check_replayable(normalized, replay),
        _check_no_authority(normalized),
        _check_unique_identity(normalized),
        _check_hash_stable(normalized),
    )
    proof = build_federation_proof(normalized)
    return FederationInvariantReport(
        federation_hash=normalized.state_hash,
        check_hash=_hash_checks(checks),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_federation_invariants(report: FederationInvariantReport) -> bool:
    if not isinstance(report, FederationInvariantReport):
        raise FederationInvariantError("report must be a FederationInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY_INVARIANT:
        raise FederationInvariantError("federation invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise FederationInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise FederationInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_membership_verifiable(state: FederationState) -> FederationInvariantCheck:
    participant_ids = list(state.participant_ids)
    all_members_known = all(member in participant_ids for unit in state.units for member in unit.members)
    participants_verified = all(
        participant.verified and participant.trust_profile.verified and participant.federation_status == "verified"
        for participant in state.participants
    )
    units_verified = all(unit.verified for unit in state.units)
    transitions_verified = all(transition.verified for transition in state.transitions)
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-001",
        satisfied=all((all_members_known, participants_verified, units_verified, transitions_verified)),
        details="federation membership is verifiable",
        evidence_hash=state.state_hash,
    )


def _check_trust_transfer_bounded(state: FederationState) -> FederationInvariantCheck:
    satisfied = True
    for participant in state.participants:
        if participant.federated_trust_score > participant.local_trust_score:
            satisfied = False
        if not 0.0 <= participant.federated_trust_score <= 100.0:
            satisfied = False
    for transition in state.transitions:
        if not 0.0 <= transition.trust_transferred <= 100.0:
            satisfied = False
        participant = next((item for item in state.participants if item.participant_id == transition.participant_id), None)
        if participant is not None and transition.trust_transferred > participant.local_trust_score:
            satisfied = False
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-002",
        satisfied=satisfied,
        details="trust transfer is bounded",
        evidence_hash=state.state_hash,
    )


def _check_replayable(state: FederationState, replay: FederationState) -> FederationInvariantCheck:
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-003",
        satisfied=state.canonical_dict() == replay.canonical_dict(),
        details="cross-network operations are replayable",
        evidence_hash=state.state_hash,
    )


def _check_no_authority(state: FederationState) -> FederationInvariantCheck:
    payload = state.canonical_dict()
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-004",
        satisfied=(
            payload["authority_boundary"] == AUTHORITY_BOUNDARY
            and payload["verified"] is True
            and all(participant.canonical_dict()["identity_is_reference_only"] is True for participant in state.participants)
        ),
        details="federation cannot introduce authority over proof",
        evidence_hash=state.state_hash,
    )


def _check_unique_identity(state: FederationState) -> FederationInvariantCheck:
    participant_ids = list(state.participant_ids)
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-005",
        satisfied=len(participant_ids) == len(set(participant_ids)),
        details="participant identity remains unique across networks",
        evidence_hash=state.state_hash,
    )


def _check_hash_stable(state: FederationState) -> FederationInvariantCheck:
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-006",
        satisfied=len(state.state_hash) == 64 and FederationState.from_mapping(state.canonical_dict()).state_hash == state.state_hash,
        details="federation data hash is stable",
        evidence_hash=state.state_hash,
    )


def _hash_checks(checks: tuple[FederationInvariantCheck, ...]) -> str:
    from hashlib import sha256
    import json

    return sha256(
        json.dumps([check.canonical_dict() for check in checks], sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY_INVARIANT",
    "INVARIANT_IDS",
    "SCHEMA",
    "FederationInvariantCheck",
    "FederationInvariantError",
    "FederationInvariantReport",
    "evaluate_federation_invariants",
    "validate_federation_invariants",
]
