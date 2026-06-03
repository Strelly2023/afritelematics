"""
afritech.distributed.api.recovery

Operative public interface for distributed recovery operations.

All external consumers should import recovery behavior from this module,
not directly from internal recovery modules.
"""

from __future__ import annotations

from typing import Iterable

from afritech.distributed.recovery.recovery_protocol import (
    RecoveryInput,
    RecoveryProtocolError,
    DistributedRecoveryProtocol,
    RecoveryResult,
    PartitionRecoveryState,
    RecoveredPartitionEntry,
    build_recovery_input as _build_recovery_input,
    recover_partition_from_ledger as _recover_partition_from_ledger,
    require_partition_recovered_from_ledger as _require_partition_recovered_from_ledger,
)

from afritech.distributed.recovery.partition_rebuild import (
    PartitionRebuildError,
    PartitionRebuildResult,
    require_partition_rebuilt_from_ledger as _require_partition_rebuilt_from_ledger,
)

from afritech.distributed.recovery.node_recovery import (
    NodeRecoveryError,
    NodeRecoveryRequest,
    NodeRecoveryResult,
    build_node_recovery_request as _build_node_recovery_request,
    require_node_recovered_from_ledger as _require_node_recovered_from_ledger,
)


# ============================================================
# PUBLIC ERROR
# ============================================================

class RecoveryAPIError(ValueError):
    """
    Public recovery API error.

    Internal recovery exceptions are wrapped so the API boundary remains stable.
    """


# ============================================================
# INTERNAL SAFE EXECUTOR
# ============================================================

def _execute_safe(fn, error_message: str):
    try:
        return fn()
    except (
        RecoveryProtocolError,
        PartitionRebuildError,
        NodeRecoveryError,
        ValueError,
        TypeError,
    ) as exc:
        raise RecoveryAPIError(error_message) from exc


# ============================================================
# BUILDERS
# ============================================================

def build_input(
    *,
    partition_id: str,
    ledger_snapshot,
    reason: str,
) -> RecoveryInput:
    return _execute_safe(
        lambda: _build_recovery_input(
            partition_id=partition_id,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        ),
        "build_input failed",
    )


def build_node_request(
    *,
    failed_worker_id: str,
    replacement_worker_id: str,
    partition_ids: Iterable[str],
    ledger_snapshot,
    reason: str,
) -> NodeRecoveryRequest:
    return _execute_safe(
        lambda: _build_node_recovery_request(
            failed_worker_id=failed_worker_id,
            replacement_worker_id=replacement_worker_id,
            partition_ids=partition_ids,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        ),
        "build_node_request failed",
    )


# ============================================================
# PARTITION RECOVERY
# ============================================================

def recover_partition(
    *,
    partition_id: str,
    ledger_snapshot,
    reason: str,
) -> RecoveryResult:
    return _execute_safe(
        lambda: _recover_partition_from_ledger(
            partition_id=partition_id,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        ),
        "recover_partition failed",
    )


def require_partition_recovered(
    *,
    partition_id: str,
    ledger_snapshot,
    reason: str,
) -> RecoveryResult:
    return _execute_safe(
        lambda: _require_partition_recovered_from_ledger(
            partition_id=partition_id,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        ),
        "partition recovery requirement failed",
    )


# ============================================================
# PARTITION REBUILD
# ============================================================

def require_partition_rebuilt(
    *,
    partition_id: str,
    ledger_snapshot,
    reason: str,
) -> PartitionRebuildResult:
    return _execute_safe(
        lambda: _require_partition_rebuilt_from_ledger(
            partition_id=partition_id,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        ),
        "partition rebuild requirement failed",
    )


# ============================================================
# NODE RECOVERY
# ============================================================

def require_node_recovered(
    *,
    failed_worker_id: str,
    replacement_worker_id: str,
    partition_ids: Iterable[str],
    ledger_snapshot,
    reason: str,
) -> NodeRecoveryResult:
    return _execute_safe(
        lambda: _require_node_recovered_from_ledger(
            failed_worker_id=failed_worker_id,
            replacement_worker_id=replacement_worker_id,
            partition_ids=partition_ids,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        ),
        "node recovery failed",
    )


# ============================================================
# ENGINE FACTORY
# ============================================================

def create_recovery_engine() -> DistributedRecoveryProtocol:
    return DistributedRecoveryProtocol()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # errors
    "RecoveryAPIError",

    # core types
    "RecoveryInput",
    "RecoveryProtocolError",
    "DistributedRecoveryProtocol",
    "RecoveryResult",
    "PartitionRecoveryState",
    "RecoveredPartitionEntry",

    # rebuild
    "PartitionRebuildError",
    "PartitionRebuildResult",

    # node recovery
    "NodeRecoveryError",
    "NodeRecoveryRequest",
    "NodeRecoveryResult",

    # api functions
    "build_input",
    "build_node_request",
    "recover_partition",
    "require_partition_recovered",
    "require_partition_rebuilt",
    "require_node_recovered",
    "create_recovery_engine",
]