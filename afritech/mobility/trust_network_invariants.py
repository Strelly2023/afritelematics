"""Formal invariants for the federated mobility trust network."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from afritech.mobility.trust_network import (
    TrustNetworkError,
    TrustProfile,
    build_trust_profile,
    build_trust_profile_proof,
)


SCHEMA = "afritech.mobility.trust_invariant_report.v1"
AUTHORITY_BOUNDARY = "trust_network_invariant_read_only"
INVARIANT_IDS = (
    "IA-TRUST-001",
    "IA-TRUST-002",
    "IA-TRUST-003",
    "IA-TRUST-004",
    "IA-TRUST-005",
    "IA-TRUST-006",
)


class TrustInvariantError(RuntimeError):
    """Raised when a trust invariant fails."""


@dataclass(frozen=True)
class TrustInvariantCheck:
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
class TrustInvariantReport:
    profile_hash: str
    check_hash: str
    proof_hash: str
    checks: tuple[TrustInvariantCheck, ...]
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
            "profile_hash": self.profile_hash,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        from hashlib import sha256
        import json

        return sha256(
            json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


def evaluate_trust_invariants(
    profile: TrustProfile | Mapping[str, Any],
) -> TrustInvariantReport:
    normalized = profile if isinstance(profile, TrustProfile) else TrustProfile.from_mapping(profile)
    replay = build_trust_profile(
        normalized.participant_id,
        normalized.event_history,
        evidence_links=normalized.evidence_links,
    )
    checks = (
        _check_same_sequence_same_score(normalized, replay),
        _check_verified_sources_only(normalized),
        _check_replayable(normalized, replay),
        _check_tamper_sensitivity(normalized),
        _check_bounds(normalized),
        _check_no_authority(normalized),
    )
    proof = build_trust_profile_proof(normalized)
    return TrustInvariantReport(
        profile_hash=normalized.profile_hash,
        check_hash=_hash_checks(checks),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_trust_invariants(report: TrustInvariantReport) -> bool:
    if not isinstance(report, TrustInvariantReport):
        raise TrustInvariantError("report must be a TrustInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise TrustInvariantError("trust invariant authority boundary mismatch")
    if not report.checks:
        raise TrustInvariantError("trust invariant report is empty")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise TrustInvariantError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise TrustInvariantError(f"{check.identifier} failed: {check.details}")
    return True


def _check_same_sequence_same_score(profile: TrustProfile, replay: TrustProfile) -> TrustInvariantCheck:
    return TrustInvariantCheck(
        identifier="IA-TRUST-001",
        satisfied=profile.trust_score == replay.trust_score,
        details="same verified event sequence produces the same trust score",
        evidence_hash=profile.profile_hash,
    )


def _check_verified_sources_only(profile: TrustProfile) -> TrustInvariantCheck:
    return TrustInvariantCheck(
        identifier="IA-TRUST-002",
        satisfied=all(
            event.verified and len(event.dispatch_hash) == 64 and len(event.custody_hash) == 64 and len(event.settlement_hash) == 64
            for event in profile.event_history
        ),
        details="trust derives only from verified operations",
        evidence_hash=profile.profile_hash,
    )


def _check_replayable(profile: TrustProfile, replay: TrustProfile) -> TrustInvariantCheck:
    return TrustInvariantCheck(
        identifier="IA-TRUST-003",
        satisfied=profile.canonical_dict() == replay.canonical_dict(),
        details="trust evolution is replayable",
        evidence_hash=replay.profile_hash,
    )


def _check_tamper_sensitivity(profile: TrustProfile) -> TrustInvariantCheck:
    if not profile.event_history:
        satisfied = True
    else:
        tampered = profile.event_history[0]
        from afritech.mobility.trust_network import TrustUpdateEvent

        alternate_type = "delay_reported" if tampered.event_type != "delay_reported" else "successful_delivery"
        tampered_event = TrustUpdateEvent(
            event_id=tampered.event_id,
            participant_id=tampered.participant_id,
            event_type=alternate_type,
            source_operation_id=tampered.source_operation_id,
            dispatch_hash=tampered.dispatch_hash,
            custody_hash=tampered.custody_hash,
            settlement_hash=tampered.settlement_hash,
            evidence_link=tampered.evidence_link,
            timestamp=tampered.timestamp,
            rating=tampered.rating,
            verified=True,
            metadata=tampered.metadata,
        )
        tampered_profile = build_trust_profile(
            profile.participant_id,
            (tampered_event,) + profile.event_history[1:],
            evidence_links=profile.evidence_links,
        )
        satisfied = tampered_profile.profile_hash != profile.profile_hash or tampered_profile.trust_score != profile.trust_score
    return TrustInvariantCheck(
        identifier="IA-TRUST-004",
        satisfied=satisfied,
        details="tampering with event history changes trust state",
        evidence_hash=profile.profile_hash,
    )


def _check_bounds(profile: TrustProfile) -> TrustInvariantCheck:
    return TrustInvariantCheck(
        identifier="IA-TRUST-005",
        satisfied=0.0 <= profile.trust_score <= 100.0,
        details="trust stays within defined bounds",
        evidence_hash=profile.profile_hash,
    )


def _check_no_authority(profile: TrustProfile) -> TrustInvariantCheck:
    payload = profile.canonical_dict()
    return TrustInvariantCheck(
        identifier="IA-TRUST-006",
        satisfied=(
            payload["identity_is_reference_only"] is True
            and payload["identity_is_truth_authority"] is False
            and payload["identity_overrides_payment"] is False
            and payload["identity_overrides_proof"] is False
            and payload["identity_overrides_replay"] is False
            and payload["identity_overrides_runtime_admissibility"] is False
            and profile.authority_boundary == "trust_network_reference_only"
        ),
        details="trust does not introduce a new authority surface",
        evidence_hash=profile.profile_hash,
    )


def _hash_checks(checks: tuple[TrustInvariantCheck, ...]) -> str:
    from hashlib import sha256
    import json

    return sha256(
        json.dumps([check.canonical_dict() for check in checks], sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "SCHEMA",
    "TrustInvariantCheck",
    "TrustInvariantError",
    "TrustInvariantReport",
    "evaluate_trust_invariants",
    "validate_trust_invariants",
]
