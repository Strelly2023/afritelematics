"""
afritech.distributed.recovery.node_recovery

Deterministic node recovery for the AfriTech distributed layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Any

from afritech.distributed.recovery.recovery_protocol import (
    DistributedRecoveryProtocol,
    RecoveryInput,
)
from afritech.distributed.api.worker import (
    build_default_worker_node,
    build_worker_assignment,
)


# ============================================================
# ERROR
# ============================================================

class NodeRecoveryError(ValueError):
    pass


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_NODE_RECOVERY_STATUSES = {
    "NODE_RECOVERED",
    "NODE_RECOVERY_INVALID",
    "MISSING_LEDGER_EVIDENCE",
    "ASSIGNMENT_MISMATCH",
}


# ============================================================
# HELPERS
# ============================================================

def _canonical_payload_hash(payload: Any) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise NodeRecoveryError(f"{field} invalid")

    if "/" in value or "\\" in value or ".." in value:
        raise NodeRecoveryError(f"{field} invalid")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise NodeRecoveryError(f"{field} invalid")
    try:
        int(value, 16)
    except ValueError:
        raise NodeRecoveryError(f"{field} invalid")


def _worker_id(worker: Any) -> str:
    if hasattr(worker, "worker_id"):
        return worker.worker_id

    identity = getattr(worker, "identity", None)
    if identity is not None and hasattr(identity, "worker_id"):
        return identity.worker_id

    raise NodeRecoveryError("invalid worker")


def _require_request(obj) -> None:
    for field in ("failed_worker_id", "replacement_worker_id", "partition_ids", "ledger_snapshot", "reason"):
        if not hasattr(obj, field):
            raise NodeRecoveryError(f"invalid request: missing {field}")


def _require_assignment(obj) -> None:
    for field in ("replacement_worker_id", "partition_id", "assignment_hash"):
        if not hasattr(obj, field):
            raise NodeRecoveryError("invalid assignment")


# ============================================================
# REQUEST
# ============================================================

@dataclass(frozen=True)
class NodeRecoveryRequest:
    failed_worker_id: str
    replacement_worker_id: str
    partition_ids: tuple[str, ...]
    ledger_snapshot: object
    reason: str

    def __post_init__(self) -> None:
        _require_identity(self.failed_worker_id, "failed_worker_id")
        _require_identity(self.replacement_worker_id, "replacement_worker_id")

        if self.failed_worker_id == self.replacement_worker_id:
            raise NodeRecoveryError("worker ids must differ")

        if not isinstance(self.partition_ids, tuple) or not self.partition_ids:
            raise NodeRecoveryError("invalid partition_ids")

        if tuple(sorted(self.partition_ids)) != self.partition_ids:
            raise NodeRecoveryError("partition_ids must be sorted")

        if len(set(self.partition_ids)) != len(self.partition_ids):
            raise NodeRecoveryError("duplicate partition_ids")

        for partition_id in self.partition_ids:
            _require_identity(partition_id, "partition_id")

        if not hasattr(self.ledger_snapshot, "canonical_entries"):
            raise NodeRecoveryError("invalid ledger_snapshot")

        if not callable(getattr(self.ledger_snapshot, "snapshot_hash", None)):
            raise NodeRecoveryError("invalid ledger_snapshot")

        if not isinstance(self.reason, str) or not self.reason:
            raise NodeRecoveryError("invalid reason")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "failed_worker_id": self.failed_worker_id,
            "replacement_worker_id": self.replacement_worker_id,
            "partition_ids": list(self.partition_ids),
            "ledger_snapshot_hash": self.ledger_snapshot.snapshot_hash(),
            "reason": self.reason,
        }

    def request_hash(self) -> str:
        return _canonical_payload_hash(self.to_canonical_dict())


# ============================================================
# ASSIGNMENT
# ============================================================

@dataclass(frozen=True)
class NodeRecoveryAssignment:
    replacement_worker_id: str
    partition_id: str
    assignment_hash: str

    def __post_init__(self) -> None:
        _require_assignment(self)
        _require_identity(self.replacement_worker_id, "replacement_worker_id")
        _require_identity(self.partition_id, "partition_id")
        _require_sha256(self.assignment_hash, "assignment_hash")

    @classmethod
    def create(cls, *, replacement_worker_id: str, partition_id: str):
        assignment = build_worker_assignment(
            worker_id=replacement_worker_id,
            partition_id=partition_id,
        )

        return cls(
            replacement_worker_id=replacement_worker_id,
            partition_id=partition_id,
            assignment_hash=assignment.assignment_hash,
        )


# ============================================================
# PLAN
# ============================================================

@dataclass(frozen=True)
class NodeRecoveryPlan:
    request_hash: str
    assignments: tuple[NodeRecoveryAssignment, ...]
    plan_hash: str

    def __post_init__(self) -> None:
        _require_sha256(self.request_hash, "request_hash")
        _require_sha256(self.plan_hash, "plan_hash")

        seen = set()

        for a in self.assignments:
            _require_assignment(a)

            if a.partition_id in seen:
                raise NodeRecoveryError("duplicate partition assignment")

            seen.add(a.partition_id)


# ============================================================
# REPORT
# ============================================================

@dataclass(frozen=True)
class NodeRecoveryReport:
    recovered: bool
    status: str
    request_hash: str
    plan_hash: str
    recovered_worker_id: str
    partition_recovery_hashes: tuple[str, ...]
    reasons: tuple[str, ...]
    report_hash: str


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class NodeRecoveryResult:
    replacement_worker: object
    plan: NodeRecoveryPlan
    partition_results: tuple
    report: NodeRecoveryReport

    def __post_init__(self) -> None:
        if _worker_id(self.replacement_worker) != self.report.recovered_worker_id:
            raise NodeRecoveryError("worker mismatch")


# ============================================================
# ENGINE
# ============================================================

class DistributedNodeRecovery:

    def __init__(self) -> None:
        self._partition_recovery = DistributedRecoveryProtocol()

    def build_plan(self, request: NodeRecoveryRequest) -> NodeRecoveryPlan:
        _require_request(request)

        assignments = tuple(
            NodeRecoveryAssignment.create(
                replacement_worker_id=request.replacement_worker_id,
                partition_id=p,
            )
            for p in request.partition_ids
        )

        payload = {
            "request_hash": request.request_hash(),
            "assignments": [a.assignment_hash for a in assignments],
        }

        return NodeRecoveryPlan(
            request_hash=request.request_hash(),
            assignments=assignments,
            plan_hash=_canonical_payload_hash(payload),
        )

    def recover_node(self, request: NodeRecoveryRequest) -> NodeRecoveryResult:
        _require_request(request)

        plan = self.build_plan(request)

        partition_results = []
        reasons: list[str] = []

        for partition_id in request.partition_ids:
            result = self._partition_recovery.recover_partition(
                RecoveryInput(
                    partition_id=partition_id,
                    ledger_snapshot=request.ledger_snapshot,
                    reason=request.reason,
                )
            )

            partition_results.append(result)

            if not result.report.recovered:
                reasons.extend(
                    f"{partition_id}:{r}" for r in result.report.reasons
                )

        recovered = not reasons

        worker = build_default_worker_node(
            worker_id=request.replacement_worker_id,
            partition_ids=request.partition_ids,
        )

        if recovered:
            status = "NODE_RECOVERED"
        elif any("missing_ledger_evidence" in r for r in reasons):
            status = "MISSING_LEDGER_EVIDENCE"
        else:
            status = "NODE_RECOVERY_INVALID"

        partition_hashes = tuple(
            sorted(r.recovery_state.recovery_hash for r in partition_results)
        )

        reasons = tuple(sorted(set(reasons)))

        report_payload = {
            "request_hash": request.request_hash(),
            "plan_hash": plan.plan_hash,
            "recovered_worker_id": request.replacement_worker_id,
            "partition_recovery_hashes": list(partition_hashes),
            "reasons": list(reasons),
            "recovered": recovered,
            "status": status,
        }

        report = NodeRecoveryReport(
            recovered=recovered,
            status=status,
            request_hash=request.request_hash(),
            plan_hash=plan.plan_hash,
            recovered_worker_id=request.replacement_worker_id,
            partition_recovery_hashes=partition_hashes,
            reasons=reasons,
            report_hash=_canonical_payload_hash(report_payload),
        )

        return NodeRecoveryResult(
            replacement_worker=worker,
            plan=plan,
            partition_results=tuple(partition_results),
            report=report,
        )


# ============================================================
# HELPERS
# ============================================================

def build_node_recovery_request(
    *,
    failed_worker_id: str,
    replacement_worker_id: str,
    partition_ids: Iterable[str],
    ledger_snapshot,
    reason: str,
) -> NodeRecoveryRequest:
    return NodeRecoveryRequest(
        failed_worker_id=failed_worker_id,
        replacement_worker_id=replacement_worker_id,
        partition_ids=tuple(sorted(partition_ids)),
        ledger_snapshot=ledger_snapshot,
        reason=reason,
    )


def require_node_recovered_from_ledger(**kwargs) -> NodeRecoveryResult:
    engine = DistributedNodeRecovery()

    request = build_node_recovery_request(**kwargs)

    result = engine.recover_node(request)

    if not result.report.recovered:
        raise NodeRecoveryError(
            "node recovery failed: " + ",".join(result.report.reasons)
        )

    return result


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "NodeRecoveryError",
    "NodeRecoveryRequest",
    "NodeRecoveryAssignment",
    "NodeRecoveryPlan",
    "NodeRecoveryReport",
    "NodeRecoveryResult",
    "DistributedNodeRecovery",
    "build_node_recovery_request",
    "require_node_recovered_from_ledger",
]