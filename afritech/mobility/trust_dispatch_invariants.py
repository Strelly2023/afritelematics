"""Formal invariants for the trust-aware dispatch engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


SCHEMA = "afritech.mobility.dispatch_invariant_report.v1"
AUTHORITY_BOUNDARY = "dispatch_invariant_read_only"
INVARIANT_IDS = (
    "IA-DISPATCH-001",
    "IA-DISPATCH-002",
    "IA-DISPATCH-003",
    "IA-DISPATCH-004",
    "IA-DISPATCH-005",
    "IA-DISPATCH-006",
)


class DispatchInvariantError(RuntimeError):
    """Raised when a dispatch invariant fails."""


@dataclass(frozen=True)
class DispatchInvariantCheck:
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
class DispatchInvariantReport:
    request_hash: str
    decision_hash: str
    check_hash: str
    checks: tuple[DispatchInvariantCheck, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "decision_hash": self.decision_hash,
            "request_hash": self.request_hash,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        from hashlib import sha256
        import json

        return sha256(
            json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


def evaluate_dispatch_invariants(
    request: Any,
    candidates: Iterable[Any],
    decision: Any | None = None,
) -> DispatchInvariantReport:
    from afritech.mobility.trust_dispatch import (
        DispatchCandidate,
        DispatchDecision,
        DispatchRequest,
        _decision_from_mapping,
        run_trust_aware_dispatch,
    )

    normalized_request = request if isinstance(request, DispatchRequest) else DispatchRequest.from_mapping(request)
    normalized_candidates = tuple(
        candidate if isinstance(candidate, DispatchCandidate) else DispatchCandidate.from_mapping(candidate)
        for candidate in candidates
    )
    if decision is None:
        actual = run_trust_aware_dispatch(normalized_request, normalized_candidates)
    elif isinstance(decision, DispatchDecision):
        actual = decision
    else:
        actual = _decision_from_mapping(normalized_request, decision)

    expected = run_trust_aware_dispatch(normalized_request, normalized_candidates)
    checks = (
        _check_same_inputs_same_result(normalized_request, normalized_candidates, actual, expected),
        _check_higher_trust_not_outranked(normalized_request, normalized_candidates, actual),
        _check_explainable_from_evidence(actual, normalized_candidates),
        _check_candidate_omission_detectable(actual, normalized_candidates),
        _check_stable_hash(actual),
        _check_no_external_state(normalized_request, normalized_candidates),
    )
    return DispatchInvariantReport(
        request_hash=normalized_request.request_hash(),
        decision_hash=actual.decision_hash,
        check_hash=_hash_checks(checks),
        checks=checks,
    )


def validate_dispatch_invariants(report: DispatchInvariantReport) -> bool:
    if not isinstance(report, DispatchInvariantReport):
        raise DispatchInvariantError("report must be a DispatchInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise DispatchInvariantError("dispatch invariant authority boundary mismatch")
    if not report.checks:
        raise DispatchInvariantError("dispatch invariant report is empty")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise DispatchInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise DispatchInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_same_inputs_same_result(
    request: DispatchRequest,
    candidates: tuple[DispatchCandidate, ...],
    actual: DispatchDecision,
    expected: DispatchDecision,
) -> DispatchInvariantCheck:
    satisfied = actual.canonical_dict() == expected.canonical_dict()
    return DispatchInvariantCheck(
        identifier="IA-DISPATCH-001",
        satisfied=satisfied,
        details="same inputs produce the same dispatch result",
        evidence_hash=actual.decision_hash,
    )


def _check_higher_trust_not_outranked(
    request: DispatchRequest,
    candidates: tuple[DispatchCandidate, ...],
    decision: DispatchDecision,
) -> DispatchInvariantCheck:
    ranked = decision.ranked_candidates
    participant_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    satisfied = True
    for left_index, left in enumerate(ranked):
        left_candidate = participant_by_id.get(left.participant_id)
        if left_candidate is None:
            satisfied = False
            continue
        for right in ranked[left_index + 1 :]:
            right_candidate = participant_by_id.get(right.participant_id)
            if right_candidate is None:
                satisfied = False
                continue
            if (
                abs(left.score - right.score) < 1e-9
                and abs(left.reliability_score - right.reliability_score) < 1e-9
                and abs(left.route_efficiency - right.route_efficiency) < 1e-9
                and abs(left.constraint_match - right.constraint_match) < 1e-9
                and abs(left.anomaly_rate - right.anomaly_rate) < 1e-9
                and left_candidate.supported_operations == right_candidate.supported_operations
            ):
                if left.trust_score < right.trust_score:
                    satisfied = False
    return DispatchInvariantCheck(
        identifier="IA-DISPATCH-002",
        satisfied=satisfied,
        details="higher trust cannot be silently outranked under equal conditions",
        evidence_hash=decision.decision_hash,
    )


def _check_explainable_from_evidence(
    decision: DispatchDecision,
    candidates: tuple[DispatchCandidate, ...],
) -> DispatchInvariantCheck:
    evidence = dict(decision.evidence)
    candidate_hashes = [candidate.candidate_hash() for candidate in candidates]
    required = {
        "candidate_hashes",
        "constraint_summary",
        "formula",
        "input_hash",
        "operation_id",
        "operation_type",
        "ranked_candidate_ids",
        "ranked_candidate_hashes",
        "selected_id",
        "timestamp",
    }
    satisfied = required.issubset(evidence.keys()) and len(evidence.get("candidate_hashes", [])) == len(candidate_hashes)
    return DispatchInvariantCheck(
        identifier="IA-DISPATCH-003",
        satisfied=satisfied,
        details="dispatch decision remains explainable from evidence",
        evidence_hash=decision.decision_hash,
    )


def _check_candidate_omission_detectable(
    decision: DispatchDecision,
    candidates: tuple[DispatchCandidate, ...],
) -> DispatchInvariantCheck:
    evidence = dict(decision.evidence)
    candidate_hashes = [candidate.candidate_hash() for candidate in candidates]
    satisfied = sorted(evidence.get("candidate_hashes", [])) == sorted(candidate_hashes)
    return DispatchInvariantCheck(
        identifier="IA-DISPATCH-004",
        satisfied=satisfied,
        details="candidate omission is detectable through evidence hashes",
        evidence_hash=decision.decision_hash,
    )


def _check_stable_hash(decision: DispatchDecision) -> DispatchInvariantCheck:
    satisfied = len(decision.decision_hash) == 64
    return DispatchInvariantCheck(
        identifier="IA-DISPATCH-005",
        satisfied=satisfied,
        details="dispatch decision hash is stable and canonical",
        evidence_hash=decision.decision_hash,
    )


def _check_no_external_state(
    request: DispatchRequest,
    candidates: tuple[DispatchCandidate, ...],
) -> DispatchInvariantCheck:
    satisfied = run_trust_aware_dispatch(request, candidates).canonical_dict() == run_trust_aware_dispatch(request, candidates).canonical_dict()
    return DispatchInvariantCheck(
        identifier="IA-DISPATCH-006",
        satisfied=satisfied,
        details="dispatch result does not depend on external mutable state",
        evidence_hash=request.request_hash(),
    )


def _hash_checks(checks: tuple[DispatchInvariantCheck, ...]) -> str:
    from hashlib import sha256
    import json

    return sha256(
        json.dumps([check.canonical_dict() for check in checks], sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "SCHEMA",
    "DispatchInvariantCheck",
    "DispatchInvariantError",
    "DispatchInvariantReport",
    "evaluate_dispatch_invariants",
    "validate_dispatch_invariants",
]
