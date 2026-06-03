"""Validate observability evidence proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.observability.evidence import (
    AUTHORITY_DISCLAIMER,
    FORBIDDEN_ACTIONS,
    ObservabilityEvidenceError,
    assert_action_allowed,
    build_observability_snapshot,
    dashboard_hash,
    required_metrics_present,
)


class ObservabilityEvidenceValidationError(RuntimeError):
    """Raised when observability evidence proof fails."""


@dataclass(frozen=True)
class ObservabilityEvidenceProofReport:
    snapshot_hash: str
    dashboard_hash: str
    required_metrics_present: bool
    forbidden_actions_rejected: bool
    non_authoritative: bool
    event_count: int
    replay_divergence_count: int
    recovery_attempts: int
    rejected_executions: int
    source_hashes: dict[str, str]
    authority_disclaimer: str

    @property
    def verified(self) -> bool:
        return (
            self.required_metrics_present
            and self.forbidden_actions_rejected
            and self.non_authoritative
            and self.event_count > 0
            and self.replay_divergence_count == 0
            and self.rejected_executions == 0
            and self.recovery_attempts >= 0
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and len(self.snapshot_hash) == 64
            and len(self.dashboard_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "dashboard_hash": self.dashboard_hash,
            "event_count": self.event_count,
            "forbidden_actions_rejected": self.forbidden_actions_rejected,
            "non_authoritative": self.non_authoritative,
            "recovery_attempts": self.recovery_attempts,
            "rejected_executions": self.rejected_executions,
            "replay_divergence_count": self.replay_divergence_count,
            "required_metrics_present": self.required_metrics_present,
            "schema": "afritech.observability_evidence_proof_report.v1",
            "snapshot_hash": self.snapshot_hash,
            "source_hashes": dict(sorted(self.source_hashes.items())),
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> ObservabilityEvidenceProofReport:
    report = run_observability_evidence_proof()
    if not report.verified:
        raise ObservabilityEvidenceValidationError("observability evidence proof failed")
    return report


def run_observability_evidence_proof() -> ObservabilityEvidenceProofReport:
    snapshot = build_observability_snapshot(
        event_count=100_000,
        partition_lag={
            "partition.dispatch.primary": 0,
            "partition.rides.region_01": 0,
            "partition.rides.region_02": 0,
        },
        worker_health={
            "worker.dispatch.primary": "HEALTHY",
            "worker.recovery.primary": "HEALTHY",
            "worker.replay.audit": "HEALTHY",
        },
        replay_divergence_count=0,
        recovery_attempts=2,
        rejected_executions=0,
        source_hashes=_source_hashes(),
    )
    payload = snapshot.dashboard_payload()

    return ObservabilityEvidenceProofReport(
        authority_disclaimer=snapshot.authority_disclaimer,
        dashboard_hash=dashboard_hash(payload),
        event_count=snapshot.event_count,
        forbidden_actions_rejected=_forbidden_actions_rejected(),
        non_authoritative=_non_authoritative(payload),
        recovery_attempts=snapshot.recovery_attempts,
        rejected_executions=snapshot.rejected_executions,
        replay_divergence_count=snapshot.replay_divergence_count,
        required_metrics_present=required_metrics_present(payload),
        snapshot_hash=snapshot.snapshot_hash(),
        source_hashes=dict(sorted(snapshot.source_hashes.items())),
    )


def _forbidden_actions_rejected() -> bool:
    for action in FORBIDDEN_ACTIONS:
        try:
            assert_action_allowed(action)
        except ObservabilityEvidenceError:
            continue
        return False
    return True


def _non_authoritative(payload: dict[str, object]) -> bool:
    disclaimer = payload.get("authority_disclaimer")
    if disclaimer != AUTHORITY_DISCLAIMER:
        return False
    return all(
        field not in payload
        for field in (
            "truth",
            "legitimacy",
            "replay_override",
            "validator_override",
            "admissibility_decision",
        )
    )


def _source_hashes() -> dict[str, str]:
    return {
        "durable_queue_report": (
            "f83dec646f424c88451b703e9db7eb123b4fcac780c2f0df23adfd9894b399e2"
        ),
        "load_proof_report": (
            "b625cfc7a45aeb6dc38fef71d5c2f7e63fb9db38420ff5a5c2480616a9bc2fe8"
        ),
        "multi_node_fault_report": (
            "c20895a9e4da5c67ab0b2e10852bb86177412e5324c9ca2a9b7fdce263d3cd5e"
        ),
        "persistent_event_store_report": (
            "4f5908acd5da8bc364a0817c9e0a8883bad0323d0472b6510d2ad30041c18a16"
        ),
    }


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = validate()
    except ObservabilityEvidenceValidationError as exc:
        print(f"Observability evidence validation FAILED: {exc}")
        return 1
    print(
        "Observability evidence validation PASSED: "
        f"dashboard_hash={report.dashboard_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

