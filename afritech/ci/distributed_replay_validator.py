from __future__ import annotations

from dataclasses import dataclass
import hashlib
import sys
from typing import Any

# ✅ INTERNAL IMPORT (NO API)
from afritech.distributed.worker.worker_result import WorkerResult

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    DistributedReplayVerificationError,
    build_worker_result,
    require_distributed_replay_verified,
    verify_distributed_replay,
)


# ============================================================
# ERROR
# ============================================================

class DistributedReplayValidatorError(ValueError):
    pass


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedReplayValidationResult:
    passed: bool
    checked_records: int
    checked_results: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed replay validation PASSED\n"
                f"✅ Checked records: {self.checked_records}\n"
                f"✅ Checked results: {self.checked_results}"
            )

        return (
            "❌ Distributed replay validation FAILED\n"
            f"❌ Checked records: {self.checked_records}\n"
            f"❌ Checked results: {self.checked_results}\n\n"
            + "\n".join(self.failures)
        )


# ============================================================
# HELPERS
# ============================================================

def _validate_worker_result_type(result: object) -> WorkerResult:
    if not isinstance(result, WorkerResult):
        raise DistributedReplayValidatorError(
            f"Non-canonical worker result detected: {type(result)}"
        )
    return result


# ============================================================
# CORE VALIDATION
# ============================================================

def validate_distributed_replay() -> DistributedReplayValidationResult:
    failures: list[str] = []

    registry = default_partition_registry()

    # ---------------------------------------------------------
    # RECORDS
    # ---------------------------------------------------------
    record_one = _build_record(
        event_id="event.ride.request.001",
        routing_key="ride.request.001",
        routing_scope="rides",
        sequence=0,
        registry=registry,
    )

    record_two = _build_record(
        event_id="event.ride.request.002",
        routing_key="ride.request.002",
        routing_scope="rides",
        sequence=1,
        registry=registry,
    )

    # ---------------------------------------------------------
    # VALID RESULTS ✅ FIXED (ADD REQUIRED HASHES)
    # ---------------------------------------------------------
    result_one = build_worker_result(
        worker_id="worker_01",
        record=record_one,
        output_payload=_output_payload(record_one),
        normalized_input_hash=record_one.normalized_payload_hash,
        canonical_event_hash=record_one.canonical_event_hash,
    )

    result_two = build_worker_result(
        worker_id="worker_01",
        record=record_two,
        output_payload=_output_payload(record_two),
        normalized_input_hash=record_two.normalized_payload_hash,
        canonical_event_hash=record_two.canonical_event_hash,
    )

    try:
        _validate_worker_result_type(result_one)
        _validate_worker_result_type(result_two)
    except DistributedReplayValidatorError as exc:
        failures.append(str(exc))

    valid_transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(record_one, record_two),
        worker_results=(result_one, result_two),
    )

    # ✅ VALID CASE
    try:
        require_distributed_replay_verified(valid_transcript)
    except DistributedReplayVerificationError as exc:
        failures.append(f"valid transcript failed: {exc}")

    # ---------------------------------------------------------
    # DIVERGENCE CASE ✅ FIXED
    # ---------------------------------------------------------
    divergent_result = build_worker_result(
        worker_id="worker_01",
        record=record_two,
        output_payload={
            **_output_payload(record_two),
            "result": "DIVERTED",  # must change hash deterministically
        },
        normalized_input_hash=record_two.normalized_payload_hash,
        canonical_event_hash=record_two.canonical_event_hash,
    )

    divergent_transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(record_one, record_two),
        worker_results=(result_one, divergent_result),
    )

    report = verify_distributed_replay(divergent_transcript)

    if report.verified:
        failures.append("divergent transcript was accepted")

    try:
        require_distributed_replay_verified(divergent_transcript)
        failures.append("require accepted divergence")
    except DistributedReplayVerificationError:
        pass

    # ---------------------------------------------------------
    # MISSING RESULT CASE
    # ---------------------------------------------------------
    missing_transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(record_one, record_two),
        worker_results=(result_one,),
    )

    try:
        require_distributed_replay_verified(missing_transcript)
        failures.append("missing result accepted")
    except DistributedReplayVerificationError:
        pass

    # ---------------------------------------------------------
    # DUPLICATE RESULT CASE
    # ---------------------------------------------------------
    duplicate_transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(record_one,),
        worker_results=(result_one, result_one),
    )

    try:
        require_distributed_replay_verified(duplicate_transcript)
        failures.append("duplicate result accepted")
    except DistributedReplayVerificationError:
        pass

    return DistributedReplayValidationResult(
        passed=not failures,
        checked_records=2,
        checked_results=4,
        failures=tuple(failures),
    )


# ============================================================
# BUILDERS
# ============================================================

def _build_record(
    *,
    event_id: str,
    routing_key: str,
    routing_scope: str,
    sequence: int,
    registry: Any,
):
    assignment = assign_partition(
        routing_key=routing_key,
        routing_scope=routing_scope,
        registry=registry,
    )

    event = {
        "event_id": event_id,
        "routing_key": routing_key,
        "routing_scope": routing_scope,
        "payload": {
            "rider_id": f"rider.{event_id}",
            "pickup": "melbourne.cbd",
            "dropoff": "melbourne.airport",
        },
    }

    return build_queue_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash=_sha256(f"normalized.{event_id}"),
        event=event,
        assignment=assignment,
        registry=registry,
    )


def _output_payload(record) -> dict[str, object]:
    return {
        "event_id": record.event_id,
        "partition_id": record.partition_id,
        "partition_sequence": record.sequence,
        "result": "accepted_for_replay_bound_execution",
    }


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:
    result = validate_distributed_replay()
    print(result.report())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())