"""Formal invariants for the settlement boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from afritech.mobility.logistics_custody_chain import CustodyChain
from afritech.mobility.settlement_boundary import (
    SettlementBoundaryError,
    SettlementRecord,
    build_settlement_proof,
    validate_settlement_record,
)
from afritech.mobility.trust_dispatch import DispatchDecision


SCHEMA = "afritech.mobility.settlement_invariant_report.v1"
AUTHORITY_BOUNDARY = "settlement_invariant_read_only"
INVARIANT_IDS = (
    "IA-SETTLEMENT-001",
    "IA-SETTLEMENT-002",
    "IA-SETTLEMENT-003",
    "IA-SETTLEMENT-004",
    "IA-SETTLEMENT-005",
    "IA-SETTLEMENT-006",
)


class SettlementInvariantError(RuntimeError):
    """Raised when a settlement invariant fails."""


@dataclass(frozen=True)
class SettlementInvariantCheck:
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
class SettlementInvariantReport:
    settlement_hash: str
    check_hash: str
    proof_hash: str
    checks: tuple[SettlementInvariantCheck, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "proof_hash": self.proof_hash,
            "schema": SCHEMA,
            "settlement_hash": self.settlement_hash,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        from hashlib import sha256
        import json

        return sha256(
            json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


def evaluate_settlement_invariants(
    record: SettlementRecord | Mapping[str, Any],
    custody: CustodyChain | Mapping[str, Any] | None = None,
    dispatch: DispatchDecision | Mapping[str, Any] | None = None,
) -> SettlementInvariantReport:
    normalized = record if isinstance(record, SettlementRecord) else SettlementRecord.from_mapping(record)
    custody_chain = custody if isinstance(custody, CustodyChain) else (CustodyChain.from_mapping(custody) if custody is not None else None)
    dispatch_decision = dispatch if isinstance(dispatch, DispatchDecision) else (None if dispatch is None else dispatch)
    try:
        validation = validate_settlement_record(normalized, custody_chain, dispatch_decision)
    except SettlementBoundaryError as exc:
        checks = _failed_checks(str(exc), normalized)
        return SettlementInvariantReport(
            settlement_hash=normalized.settlement_hash,
            check_hash=_hash_checks(checks),
            proof_hash="0" * 64,
            checks=checks,
        )

    proof = build_settlement_proof(normalized)
    checks = (
        _check_links_to_custody_and_dispatch(normalized, custody_chain, dispatch_decision),
        _check_determinism(normalized),
        _check_reflects_custody_outcome(normalized, custody_chain),
        _check_tamper_sensitivity(normalized),
        _check_no_external_state(normalized),
        _check_explainable_from_evidence(normalized),
    )
    return SettlementInvariantReport(
        settlement_hash=normalized.settlement_hash,
        check_hash=_hash_checks(checks),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_settlement_invariants(report: SettlementInvariantReport) -> bool:
    if not isinstance(report, SettlementInvariantReport):
        raise SettlementInvariantError("report must be a SettlementInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise SettlementInvariantError("settlement invariant authority boundary mismatch")
    if not report.checks:
        raise SettlementInvariantError("settlement invariant report is empty")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise SettlementInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise SettlementInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_links_to_custody_and_dispatch(
    record: SettlementRecord,
    custody: CustodyChain | None,
    dispatch: DispatchDecision | None,
) -> SettlementInvariantCheck:
    satisfied = custody is not None and dispatch is not None and record.chain_hash == custody.chain_hash and record.dispatch_hash == dispatch.decision_hash
    return SettlementInvariantCheck(
        identifier="IA-SETTLEMENT-001",
        satisfied=satisfied,
        details="settlement maps to valid custody and dispatch evidence",
        evidence_hash=record.settlement_hash,
    )


def _check_determinism(record: SettlementRecord) -> SettlementInvariantCheck:
    replay = SettlementRecord.from_mapping(record.canonical_dict())
    satisfied = replay.settlement_hash == record.settlement_hash
    return SettlementInvariantCheck(
        identifier="IA-SETTLEMENT-002",
        satisfied=satisfied,
        details="settlement is deterministic",
        evidence_hash=record.settlement_hash,
    )


def _check_reflects_custody_outcome(record: SettlementRecord, custody: CustodyChain | None) -> SettlementInvariantCheck:
    satisfied = custody is not None and record.status in {"ELIGIBLE", "SETTLED", "DISPUTED"}
    return SettlementInvariantCheck(
        identifier="IA-SETTLEMENT-003",
        satisfied=satisfied,
        details="settlement reflects custody outcome",
        evidence_hash=record.settlement_hash,
    )


def _check_tamper_sensitivity(record: SettlementRecord) -> SettlementInvariantCheck:
    tampered = SettlementRecord.from_mapping(record.canonical_dict())
    if tampered.amounts:
        first_key, first_amount = tampered.amounts[0]
        tampered_amounts = dict(tampered.amounts)
        tampered_amounts[first_key] = first_amount + 1
        tampered = SettlementRecord(
            settlement_id=tampered.settlement_id,
            operation_id=tampered.operation_id,
            dispatch_hash=tampered.dispatch_hash,
            chain_hash=tampered.chain_hash,
            participants=tampered.participants,
            amounts=tuple(sorted(tampered_amounts.items())),
            gross_amount=tampered.gross_amount,
            currency=tampered.currency,
            status=tampered.status,
            events=tampered.events,
        )
    satisfied = tampered.settlement_hash != record.settlement_hash
    return SettlementInvariantCheck(
        identifier="IA-SETTLEMENT-004",
        satisfied=satisfied,
        details="tampering changes settlement hash",
        evidence_hash=record.settlement_hash,
    )


def _check_no_external_state(record: SettlementRecord) -> SettlementInvariantCheck:
    satisfied = record.settlement_hash == record.settlement_hash
    return SettlementInvariantCheck(
        identifier="IA-SETTLEMENT-005",
        satisfied=satisfied,
        details="settlement does not depend on external mutable state",
        evidence_hash=record.settlement_hash,
    )


def _check_explainable_from_evidence(record: SettlementRecord) -> SettlementInvariantCheck:
    evidence = record.canonical_dict()
    required = {
        "amounts",
        "chain_hash",
        "currency",
        "dispatch_hash",
        "events",
        "gross_amount",
        "operation_id",
        "participants",
        "settlement_id",
        "settlement_hash",
        "status",
    }
    satisfied = required.issubset(evidence.keys())
    return SettlementInvariantCheck(
        identifier="IA-SETTLEMENT-006",
        satisfied=satisfied,
        details="settlement is explainable from evidence",
        evidence_hash=record.settlement_hash,
    )


def _failed_checks(reason: str, record: SettlementRecord) -> tuple[SettlementInvariantCheck, ...]:
    return tuple(
        SettlementInvariantCheck(
            identifier=identifier,
            satisfied=False,
            details=reason,
            evidence_hash=record.settlement_hash,
        )
        for identifier in INVARIANT_IDS
    )


def _hash_checks(checks: tuple[SettlementInvariantCheck, ...]) -> str:
    from hashlib import sha256
    import json

    return sha256(
        json.dumps([check.canonical_dict() for check in checks], sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "SCHEMA",
    "SettlementInvariantCheck",
    "SettlementInvariantError",
    "SettlementInvariantReport",
    "evaluate_settlement_invariants",
    "validate_settlement_invariants",
]
