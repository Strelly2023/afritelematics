"""
afritech.ci.invariant_runtime_guard
"""

from __future__ import annotations

import os
import ast
from typing import Iterable

# afritech.ci.invariant_runtime_guard
# ============================================================
# ERROR
# ============================================================

class InvariantViolationError(RuntimeError):
    pass


# ============================================================
# CONSTANTS ✅ TARGETED I31
# ============================================================

FORBIDDEN_TYPES = {
    "DistributedQueueRecord",
    "WorkerResult",
    "PartitionRegistry",
    "PartitionDefinition",
    "DistributedLedgerEntry",
    "DistributedLedgerSnapshot",
    "RecoveryInput",
    "RecoveryResult",
    "DeterministicWorkerNode",
}


# ============================================================
# CORE GUARD
# ============================================================

class InvariantRuntimeGuard:

    # ---------------------------------------------------------
    # RECORD VALIDATION
    # ---------------------------------------------------------

    def validate_records(self, records: Iterable) -> None:

        records = tuple(records)

        if not records:
            raise InvariantViolationError("empty record set")

        last_seen = {}

        ordered = sorted(
            records,
            key=lambda r: (
                getattr(r, "partition_id", None),
                getattr(r, "sequence", None),
                getattr(r, "event_id", None),
            ),
        )

        for record in ordered:

            self._require_record_shape(record)

            pid = record.partition_id
            seq = record.sequence

            if pid in last_seen:
                if seq != last_seen[pid] + 1:
                    raise InvariantViolationError(
                        f"non-contiguous sequence for {pid}: {seq}"
                    )
            else:
                if seq != 0:
                    raise InvariantViolationError(
                        f"first sequence must be 0 for {pid}"
                    )

            last_seen[pid] = seq

    # ---------------------------------------------------------
    # RESULT VALIDATION
    # ---------------------------------------------------------

    def validate_results(self, results: Iterable) -> None:

        results = tuple(results)

        if not results:
            raise InvariantViolationError("empty results")

        seen_hashes = set()

        for r in results:

            if r is None:
                raise InvariantViolationError("invalid result")

            if not hasattr(r, "execution_hash"):
                raise InvariantViolationError("missing execution_hash")

            # ✅ Strong hash integrity check
            h = r.execution_hash

            if not isinstance(h, str) or len(h) != 64:
                raise InvariantViolationError("invalid execution_hash")

            try:
                int(h, 16)
            except ValueError:
                raise InvariantViolationError("execution_hash not hex")

            if h in seen_hashes:
                raise InvariantViolationError("duplicate execution hash")

            seen_hashes.add(h)

    # ---------------------------------------------------------
    # TRACE VALIDATION
    # ---------------------------------------------------------

    def validate_traces(self, traces: Iterable) -> None:

        traces = tuple(traces)

        if not traces:
            raise InvariantViolationError("empty traces")

        seen = set()

        for t in traces:
            if t is None:
                raise InvariantViolationError("invalid trace")

            for field in (
                "event_id",
                "partition_id",
                "sequence",
                "record_hash",
                "execution_hash",
                "receipt_hash",
            ):
                if not hasattr(t, field):
                    raise InvariantViolationError(f"trace missing {field}")

            identity = (t.partition_id, t.sequence)

            if identity in seen:
                raise InvariantViolationError(
                    f"duplicate trace identity: {identity}"
                )

            seen.add(identity)

    # ---------------------------------------------------------
    # DETERMINISM CHECK
    # ---------------------------------------------------------

    def validate_determinism(
        self,
        results_a: Iterable,
        results_b: Iterable,
    ) -> None:

        a = tuple(results_a)
        b = tuple(results_b)

        if len(a) != len(b):
            raise InvariantViolationError("result length mismatch")

        for i, (ra, rb) in enumerate(zip(a, b)):

            if not self._equal_results(ra, rb):
                raise InvariantViolationError(
                    f"non-deterministic result at index {i}"
                )

    # ---------------------------------------------------------
    # ✅ I31 — AST ENFORCEMENT
    # ---------------------------------------------------------

    def validate_no_isinstance_usage(
        self,
        root_path: str = "afritech/distributed",
    ) -> None:

        violations = []

        for root, _, files in os.walk(root_path):
            for f in files:

                if not f.endswith(".py"):
                    continue

                path = os.path.join(root, f)

                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        tree = ast.parse(fh.read())
                except Exception:
                    continue

                for node in ast.walk(tree):

                    if not isinstance(node, ast.Call):
                        continue

                    func = node.func

                    if isinstance(func, ast.Name) and func.id == "isinstance":

                        # must have exactly 2 args
                        if len(node.args) != 2:
                            continue

                        type_node = node.args[1]

                        # CASE 1: isinstance(x, Type)
                        if isinstance(type_node, ast.Name):
                            if type_node.id in FORBIDDEN_TYPES:
                                violations.append(f"{path} → {type_node.id}")

                        # CASE 2: isinstance(x, (A, B))
                        elif isinstance(type_node, ast.Tuple):
                            for elt in type_node.elts:
                                if isinstance(elt, ast.Name):
                                    if elt.id in FORBIDDEN_TYPES:
                                        violations.append(
                                            f"{path} → {elt.id}"
                                        )

        if violations:
            raise InvariantViolationError(
                "Forbidden isinstance usage detected:\n"
                + "\n".join(sorted(set(violations)))
            )

    # ---------------------------------------------------------
    # PRIVATE
    # ---------------------------------------------------------

    def _require_record_shape(self, record) -> None:

        if record is None:
            raise InvariantViolationError("invalid record")

        for field in (
            "event_id",
            "partition_id",
            "sequence",
            "normalized_payload_hash",
            "assignment_hash",
        ):
            if not hasattr(record, field):
                raise InvariantViolationError(
                    f"invalid record: missing {field}"
                )

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
# CI ENTRYPOINT
# ============================================================

def run_invariant_checks() -> None:

    guard = InvariantRuntimeGuard()

    # ✅ core invariant enforcement
    guard.validate_no_isinstance_usage()

    print("✅ Invariant runtime guard PASSED")


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run_invariant_checks()