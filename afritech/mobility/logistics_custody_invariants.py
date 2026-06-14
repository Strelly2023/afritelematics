"""Formal invariants for the logistics custody chain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from afritech.mobility.logistics_custody_chain import (
    CustodyChain,
    CustodyStep,
    LogisticsCustodyError,
    build_custody_chain_proof,
    validate_custody_chain,
)


SCHEMA = "afritech.mobility.custody_invariant_report.v1"
AUTHORITY_BOUNDARY = "custody_invariant_read_only"
INVARIANT_IDS = (
    "IA-CUSTODY-001",
    "IA-CUSTODY-002",
    "IA-CUSTODY-003",
    "IA-CUSTODY-004",
    "IA-CUSTODY-005",
    "IA-CUSTODY-006",
)


class CustodyInvariantError(RuntimeError):
    """Raised when a custody invariant fails."""


@dataclass(frozen=True)
class CustodyInvariantCheck:
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
class CustodyInvariantReport:
    chain_hash: str
    check_hash: str
    checks: tuple[CustodyInvariantCheck, ...]
    proof_hash: str
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "chain_hash": self.chain_hash,
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


def evaluate_custody_invariants(
    chain: CustodyChain | Mapping[str, Any],
) -> CustodyInvariantReport:
    normalized = chain if isinstance(chain, CustodyChain) else CustodyChain.from_mapping(chain)
    try:
        validation = validate_custody_chain(normalized)
    except LogisticsCustodyError as exc:
        checks = _failed_checks(str(exc), normalized)
        return CustodyInvariantReport(
            chain_hash=normalized.chain_hash,
            check_hash=_hash_checks(checks),
            checks=checks,
            proof_hash="0" * 64,
        )

    proof = build_custody_chain_proof(normalized)
    checks = (
        _check_continuity(normalized),
        _check_single_owner(normalized),
        _check_deterministic_replay(normalized),
        _check_tamper_sensitivity(normalized),
        _check_missing_handoff_detectable(normalized),
        _check_explicit_handoff(normalized),
    )
    return CustodyInvariantReport(
        chain_hash=normalized.chain_hash,
        check_hash=_hash_checks(checks),
        checks=checks,
        proof_hash=proof["proof_hash"],
    )


def validate_custody_invariants(report: CustodyInvariantReport) -> bool:
    if not isinstance(report, CustodyInvariantReport):
        raise CustodyInvariantError("report must be a CustodyInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise CustodyInvariantError("custody invariant authority boundary mismatch")
    if not report.checks:
        raise CustodyInvariantError("custody invariant report is empty")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise CustodyInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise CustodyInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_continuity(chain: CustodyChain) -> CustodyInvariantCheck:
    ok = True
    previous_owner: str | None = None
    for index, step in enumerate(chain.custody_steps):
        if index == 0 and step.from_participant is not None:
            ok = False
        if index > 0 and step.from_participant != previous_owner:
            ok = False
        previous_owner = step.to_participant
    return CustodyInvariantCheck(
        identifier="IA-CUSTODY-001",
        satisfied=ok,
        details="custody is continuous with no gaps",
        evidence_hash=chain.chain_hash,
    )


def _check_single_owner(chain: CustodyChain) -> CustodyInvariantCheck:
    owners = [step.to_participant for step in chain.custody_steps]
    ok = len(owners) == len(chain.custody_steps) and all(owner for owner in owners)
    return CustodyInvariantCheck(
        identifier="IA-CUSTODY-002",
        satisfied=ok,
        details="each step has exactly one receiving owner",
        evidence_hash=chain.chain_hash,
    )


def _check_deterministic_replay(chain: CustodyChain) -> CustodyInvariantCheck:
    replay = CustodyChain.from_mapping(chain.canonical_dict())
    ok = replay.chain_hash == chain.chain_hash
    return CustodyInvariantCheck(
        identifier="IA-CUSTODY-003",
        satisfied=ok,
        details="custody chain is replayable deterministically",
        evidence_hash=chain.chain_hash,
    )


def _check_tamper_sensitivity(chain: CustodyChain) -> CustodyInvariantCheck:
    tampered = CustodyChain.from_mapping(chain.canonical_dict())
    if len(tampered.custody_steps) > 0:
        first = tampered.custody_steps[0]
        tampered_steps = list(tampered.custody_steps)
        tampered_steps[0] = CustodyStep(
            step_id=first.step_id,
            from_participant=first.from_participant,
            to_participant=first.to_participant,
            location=first.location,
            timestamp=first.timestamp,
            condition=first.condition,
            evidence_hash=("f" * 64),
        )
        tampered = CustodyChain(
            chain_id=tampered.chain_id,
            operation_id=tampered.operation_id,
            asset_type=tampered.asset_type,
            custody_steps=tuple(tampered_steps),
        )
    ok = tampered.chain_hash != chain.chain_hash
    return CustodyInvariantCheck(
        identifier="IA-CUSTODY-004",
        satisfied=ok,
        details="tampering changes the chain hash",
        evidence_hash=chain.chain_hash,
    )


def _check_missing_handoff_detectable(chain: CustodyChain) -> CustodyInvariantCheck:
    if len(chain.custody_steps) < 2:
        ok = False
    else:
        reduced = CustodyChain(
            chain_id=chain.chain_id,
            operation_id=chain.operation_id,
            asset_type=chain.asset_type,
            custody_steps=chain.custody_steps[:-1],
        )
        ok = reduced.chain_hash != chain.chain_hash
    return CustodyInvariantCheck(
        identifier="IA-CUSTODY-005",
        satisfied=ok,
        details="missing handoff is detectable",
        evidence_hash=chain.chain_hash,
    )


def _check_explicit_handoff(chain: CustodyChain) -> CustodyInvariantCheck:
    ok = all(step.from_participant is not None or index == 0 for index, step in enumerate(chain.custody_steps))
    return CustodyInvariantCheck(
        identifier="IA-CUSTODY-006",
        satisfied=ok,
        details="custody transfer is explicitly recorded",
        evidence_hash=chain.chain_hash,
    )


def _failed_checks(reason: str, chain: CustodyChain) -> tuple[CustodyInvariantCheck, ...]:
    return tuple(
        CustodyInvariantCheck(
            identifier=identifier,
            satisfied=False,
            details=reason,
            evidence_hash=chain.chain_hash,
        )
        for identifier in INVARIANT_IDS
    )


def _hash_checks(checks: tuple[CustodyInvariantCheck, ...]) -> str:
    from hashlib import sha256
    import json

    return sha256(
        json.dumps([check.canonical_dict() for check in checks], sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "SCHEMA",
    "CustodyInvariantCheck",
    "CustodyInvariantError",
    "CustodyInvariantReport",
    "evaluate_custody_invariants",
    "validate_custody_invariants",
]
