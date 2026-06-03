"""
afritech.distributed.testing.fault_injection

Deterministic fault injection utilities for AfriTech distributed system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from afritech.distributed.api.queue import (
    DistributedQueueRecord,
    build_queue_record,
)

from afritech.distributed.api.partition import default_partition_registry


# ============================================================
# ERROR
# ============================================================

class FaultInjectionError(ValueError):
    pass


# ============================================================
# FAULT TYPES
# ============================================================

class FaultType:
    DROP_LAST = "drop_last"
    DUPLICATE_LAST = "duplicate_last"
    REVERSE_ORDER = "reverse_order"
    CORRUPT_SEQUENCE = "corrupt_sequence"


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class FaultInjectionResult:
    original_count: int
    modified_count: int
    fault_type: str
    records: Tuple[DistributedQueueRecord, ...]


# ============================================================
# VALIDATION
# ============================================================

def _validate_records(
    records: Iterable[DistributedQueueRecord],
) -> Tuple[DistributedQueueRecord, ...]:

    records = tuple(records)

    if not records:
        raise FaultInjectionError("records cannot be empty")

    for r in records:
        if r is None:
            raise FaultInjectionError("invalid record: None")

        for field in (
            "event_id",
            "partition_id",
            "sequence",
            "normalized_payload_hash",
            "assignment_hash",
        ):
            if not hasattr(r, field):
                raise FaultInjectionError(f"invalid record: missing {field}")

    return records


# ============================================================
# INJECTOR
# ============================================================

class FaultInjector:
    """
    Deterministic fault injector.

    Applies controlled transformations to record streams.
    """

    def inject(
        self,
        records: Iterable[DistributedQueueRecord],
        fault: str,
    ) -> FaultInjectionResult:

        records_tuple = _validate_records(records)

        if fault == FaultType.DROP_LAST:
            modified = records_tuple[:-1]

        elif fault == FaultType.DUPLICATE_LAST:
            last = records_tuple[-1]
            modified = records_tuple + (last,)

        elif fault == FaultType.REVERSE_ORDER:
            modified = tuple(reversed(records_tuple))

        elif fault == FaultType.CORRUPT_SEQUENCE:
            modified = self._corrupt_sequence(records_tuple)

        else:
            raise FaultInjectionError(f"unknown fault: {fault}")

        return FaultInjectionResult(
            original_count=len(records_tuple),
            modified_count=len(modified),
            fault_type=fault,
            records=modified,
        )

    # ---------------------------------------------------------
    # INTERNAL CORRUPTION ✅ FIXED
    # ---------------------------------------------------------

    def _corrupt_sequence(
        self,
        records: Tuple[DistributedQueueRecord, ...],
    ) -> Tuple[DistributedQueueRecord, ...]:

        corrupted = list(records)

        target = corrupted[0]

        # ✅ deterministic corruption
        bad_sequence = target.sequence + 999

        registry = default_partition_registry()

        corrupted[0] = build_queue_record(
            event_id=target.event_id,
            sequence=bad_sequence,
            normalized_payload_hash=target.normalized_payload_hash,
            event=getattr(target, "event"),
            assignment=getattr(target, "assignment"),
            registry=registry,
        )

        return tuple(corrupted)


# ============================================================
# UTILITIES
# ============================================================

def apply_fault(
    records: Iterable[DistributedQueueRecord],
    fault: str,
) -> Tuple[DistributedQueueRecord, ...]:

    injector = FaultInjector()
    return injector.inject(records, fault).records