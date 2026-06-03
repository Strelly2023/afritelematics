"""Non-authoritative observability evidence for production proof gates."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


AUTHORITY_DISCLAIMER = (
    "Observability may report system state and influence operations. It does "
    "not define truth; replay validation and validators remain authority."
)

REQUIRED_DASHBOARD_METRICS = (
    "event_count",
    "partition_lag",
    "worker_health",
    "replay_divergence_count",
    "recovery_attempts",
    "rejected_executions",
)

ALLOWED_ACTIONS = frozenset(
    {
        "report_system_state",
        "influence_operations",
        "surface_replay_divergence",
        "show_event_count",
        "show_partition_lag",
        "show_worker_health",
        "show_recovery_attempts",
        "show_rejected_executions",
    }
)

FORBIDDEN_ACTIONS = frozenset(
    {
        "define_truth",
        "override_replay",
        "ratify_legitimacy",
        "mutate_evidence",
        "suppress_failure",
        "change_validator_result",
        "declare_execution_admissible",
    }
)

VALID_WORKER_HEALTH = frozenset({"HEALTHY", "DEGRADED", "RECOVERING", "DOWN"})


class ObservabilityEvidenceError(ValueError):
    """Raised when observability evidence violates non-authority boundaries."""


@dataclass(frozen=True)
class ObservabilityEvidenceSnapshot:
    event_count: int
    partition_lag: Mapping[str, int]
    worker_health: Mapping[str, str]
    replay_divergence_count: int
    recovery_attempts: int
    rejected_executions: int
    source_hashes: Mapping[str, str]
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    def __post_init__(self) -> None:
        _require_non_negative_int(self.event_count, "event_count")
        _require_non_negative_int(
            self.replay_divergence_count,
            "replay_divergence_count",
        )
        _require_non_negative_int(self.recovery_attempts, "recovery_attempts")
        _require_non_negative_int(self.rejected_executions, "rejected_executions")
        _require_partition_lag(self.partition_lag)
        _require_worker_health(self.worker_health)
        _require_source_hashes(self.source_hashes)
        if self.authority_disclaimer != AUTHORITY_DISCLAIMER:
            raise ObservabilityEvidenceError("observability authority disclaimer mismatch")

    def dashboard_payload(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "event_count": self.event_count,
            "partition_lag": dict(sorted(self.partition_lag.items())),
            "recovery_attempts": self.recovery_attempts,
            "rejected_executions": self.rejected_executions,
            "replay_divergence_count": self.replay_divergence_count,
            "source_hashes": dict(sorted(self.source_hashes.items())),
            "worker_health": dict(sorted(self.worker_health.items())),
        }

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "dashboard_payload": self.dashboard_payload(),
            "schema": "afritech.observability_evidence_snapshot.v1",
        }

    def snapshot_hash(self) -> str:
        return _canonical_hash(self.to_canonical_dict())


def build_observability_snapshot(
    *,
    event_count: int,
    partition_lag: Mapping[str, int],
    worker_health: Mapping[str, str],
    replay_divergence_count: int,
    recovery_attempts: int,
    rejected_executions: int,
    source_hashes: Mapping[str, str],
) -> ObservabilityEvidenceSnapshot:
    return ObservabilityEvidenceSnapshot(
        event_count=event_count,
        partition_lag=dict(partition_lag),
        worker_health=dict(worker_health),
        replay_divergence_count=replay_divergence_count,
        recovery_attempts=recovery_attempts,
        rejected_executions=rejected_executions,
        source_hashes=dict(source_hashes),
    )


def assert_action_allowed(action: str) -> bool:
    if action in FORBIDDEN_ACTIONS:
        raise ObservabilityEvidenceError(
            f"observability action is non-authoritative: {action}"
        )
    if action not in ALLOWED_ACTIONS:
        raise ObservabilityEvidenceError(f"unknown observability action: {action}")
    return True


def required_metrics_present(payload: Mapping[str, object]) -> bool:
    return all(metric in payload for metric in REQUIRED_DASHBOARD_METRICS)


def dashboard_hash(payload: Mapping[str, object]) -> str:
    return _canonical_hash(dict(payload))


def _require_partition_lag(partition_lag: Mapping[str, int]) -> None:
    if not isinstance(partition_lag, Mapping) or not partition_lag:
        raise ObservabilityEvidenceError("partition_lag must be non-empty mapping")
    for partition_id, lag in partition_lag.items():
        _require_identity(partition_id, "partition_id")
        _require_non_negative_int(lag, "partition_lag")


def _require_worker_health(worker_health: Mapping[str, str]) -> None:
    if not isinstance(worker_health, Mapping) or not worker_health:
        raise ObservabilityEvidenceError("worker_health must be non-empty mapping")
    for worker_id, status in worker_health.items():
        _require_identity(worker_id, "worker_id")
        if status not in VALID_WORKER_HEALTH:
            raise ObservabilityEvidenceError("worker_health status unsupported")


def _require_source_hashes(source_hashes: Mapping[str, str]) -> None:
    if not isinstance(source_hashes, Mapping) or not source_hashes:
        raise ObservabilityEvidenceError("source_hashes must be non-empty mapping")
    for source_name, source_hash in source_hashes.items():
        _require_identity(source_name, "source_name")
        _require_hash(source_hash, "source_hash")


def _require_non_negative_int(value: object, field: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ObservabilityEvidenceError(f"{field} must be non-negative int")
    return value


def _require_identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ObservabilityEvidenceError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise ObservabilityEvidenceError(f"{field} contains forbidden path syntax")
    return value


def _require_hash(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ObservabilityEvidenceError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ObservabilityEvidenceError(f"{field} must be sha256") from exc
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

