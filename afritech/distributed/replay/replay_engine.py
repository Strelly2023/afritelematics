"""
afritech.distributed.replay.replay_engine
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple, List

from afritech.distributed.api.queue import DistributedQueueRecord
from afritech.distributed.api.worker import build_default_worker_node


# ============================================================
# ERROR
# ============================================================

class DistributedReplayError(ValueError):
    pass


# ============================================================
# SNAPSHOT ✅
# ============================================================

@dataclass(frozen=True)
class ReplaySnapshot:
    records: Tuple[DistributedQueueRecord, ...]
    expected_results: Tuple

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            raise DistributedReplayError("records must be tuple")

        if not isinstance(self.expected_results, tuple):
            raise DistributedReplayError("expected_results must be tuple")

        if len(self.records) != len(self.expected_results):
            raise DistributedReplayError("length mismatch")

        # ✅ RECORD VALIDATION
        for record in self.records:
            if record is None:
                raise DistributedReplayError("invalid record")

            for field in (
                "event_id",
                "partition_id",
                "sequence",
                "normalized_payload_hash",
                "assignment_hash",
            ):
                if not hasattr(record, field):
                    raise DistributedReplayError(
                        f"invalid record: missing {field}"
                    )

        # ✅ RESULT VALIDATION
        for result in self.expected_results:
            if result is None:
                raise DistributedReplayError("invalid result")

            for field in (
                "execution_hash",
                "partition_id",
                "partition_sequence",
            ):
                if not hasattr(result, field):
                    raise DistributedReplayError(
                        f"invalid expected result: missing {field}"
                    )


# ============================================================
# ENGINE ✅ FIXED
# ============================================================

class DistributedReplayEngine:

    def replay(self, snapshot: ReplaySnapshot) -> Tuple:

        if snapshot is None or not hasattr(snapshot, "records"):
            raise DistributedReplayError("invalid snapshot")

        # ---------------------------------------------------------
        # DETERMINE WORKER PARTITIONS
        # ---------------------------------------------------------
        partition_ids = tuple(
            sorted({r.partition_id for r in snapshot.records})
        )

        worker = build_default_worker_node(
            worker_id="afritech.replay.worker",
            partition_ids=partition_ids,
        )

        # ---------------------------------------------------------
        # CANONICAL ORDER ✅ (CRITICAL)
        # ---------------------------------------------------------
        ordered_records = tuple(
            sorted(
                snapshot.records,
                key=lambda r: (
                    r.partition_id,
                    r.sequence,
                    r.event_id,
                ),
            )
        )

        results: List = []

        for record in ordered_records:
            outcome = worker.execute(record)

            if not hasattr(outcome, "result"):
                raise DistributedReplayError("worker outcome malformed")

            results.append(outcome.result)

        return tuple(results)

    # ---------------------------------------------------------
    # VERIFY ✅ FIXED
    # ---------------------------------------------------------

    def verify(self, snapshot: ReplaySnapshot) -> bool:

        replayed = self.replay(snapshot)
        expected = snapshot.expected_results

        if len(replayed) != len(expected):
            return False

        # ✅ sort expected the SAME WAY as replay
        expected_sorted = tuple(
            sorted(
                expected,
                key=lambda r: (
                    r.partition_id,
                    r.partition_sequence,
                    getattr(r, "event_id", ""),
                ),
            )
        )

        for a, b in zip(replayed, expected_sorted):
            if not self._equal_results(a, b):
                return False

        return True

    # ---------------------------------------------------------
    # STRUCTURAL COMPARISON ✅
    # ---------------------------------------------------------

    def _equal_results(self, a, b) -> bool:
        if a is None or b is None:
            return False

        required_fields = (
            "execution_hash",
            "partition_id",
            "partition_sequence",
        )

        for field in required_fields:
            if not hasattr(a, field) or not hasattr(b, field):
                return False

        return (
            a.execution_hash == b.execution_hash
            and a.partition_id == b.partition_id
            and a.partition_sequence == b.partition_sequence
        )


# ============================================================
# UTIL ✅
# ============================================================

def build_replay_snapshot(
    records: Iterable[DistributedQueueRecord],
    results: Iterable,
) -> ReplaySnapshot:

    records_tuple = tuple(records)
    results_tuple = tuple(results)

    if len(records_tuple) != len(results_tuple):
        raise DistributedReplayError("records/results length mismatch")

    return ReplaySnapshot(
        records=records_tuple,
        expected_results=results_tuple,
    )