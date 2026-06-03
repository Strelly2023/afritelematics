"""
afritech.ci.distributed_recovery_validator

CI validator for AfriTech distributed recovery layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import sys

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record

from afritech.distributed.api.recovery import (
    RecoveryAPIError,
    build_node_request,
    require_partition_recovered,
    require_partition_rebuilt,
    require_node_recovered,
)

from afritech.distributed.replay.distributed_ledger import (
    DistributedLedgerError,
    DistributedReplayLedger,
)

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
)

from afritech.distributed.worker.worker_result import build_worker_result


# ============================================================
# ERROR
# ============================================================

class DistributedRecoveryValidatorError(ValueError):
    pass


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedRecoveryValidationResult:
    passed: bool
    checked_recoveries: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed recovery validation PASSED\n"
                f"✅ Checked recoveries: {self.checked_recoveries}"
            )

        return (
            "❌ Distributed recovery validation FAILED\n"
            f"❌ Checked recoveries: {self.checked_recoveries}\n"
            + "\n".join(f" - {failure}" for failure in self.failures)
        )


# ============================================================
# VALIDATOR
# ============================================================

def validate_distributed_recovery() -> DistributedRecoveryValidationResult:

    failures: list[str] = []
    checked = 0

    registry = default_partition_registry()

    # ---------------------------------------------------------
    # BUILD RECORDS
    # ---------------------------------------------------------

    record_one = _build_record(
        event_id="event.recovery.001",
        routing_key="ride.recovery.shared",
        routing_scope="rides",
        sequence=0,
        registry=registry,
    )

    record_two = _build_record(
        event_id="event.recovery.002",
        routing_key="ride.recovery.shared",
        routing_scope="rides",
        sequence=1,
        registry=registry,
    )

    result_one = _build_worker(record_one)
    result_two = _build_worker(record_two)

    # ---------------------------------------------------------
    # TRANSCRIPT
    # ---------------------------------------------------------

    try:
        transcript = DistributedReplayTranscript.from_iterables(
            queue_records=(record_one, record_two),
            worker_results=(result_one, result_two),
        )
    except Exception as exc:
        return DistributedRecoveryValidationResult(
            passed=False,
            checked_recoveries=0,
            failures=(f"transcript construction failed: {exc}",),
        )

    # ---------------------------------------------------------
    # LEDGER APPEND
    # ---------------------------------------------------------

    ledger = DistributedReplayLedger()

    try:
        ledger.append_verified_transcript(transcript)
    except DistributedLedgerError as exc:
        failures.append(f"ledger append failed: {exc}")

    snapshot = ledger.snapshot()

    # ---------------------------------------------------------
    # PARTITION RECOVERY
    # ---------------------------------------------------------

    checked += 1
    try:
        recovery = require_partition_recovered(
            partition_id=record_one.partition_id,
            ledger_snapshot=snapshot,
            reason="ci_partition_recovery",
        )

        if not recovery.report.recovered:
            failures.append("partition recovery did not report recovered")

    except RecoveryAPIError as exc:
        failures.append(f"partition recovery failed: {exc}")

    # ---------------------------------------------------------
    # PARTITION REBUILD
    # ---------------------------------------------------------

    checked += 1
    try:
        rebuild = require_partition_rebuilt(
            partition_id=record_one.partition_id,
            ledger_snapshot=snapshot,
            reason="ci_partition_rebuild",
        )

        if not rebuild.report.rebuilt:
            failures.append("partition rebuild did not report rebuilt")

    except RecoveryAPIError as exc:
        failures.append(f"partition rebuild failed: {exc}")

    # ---------------------------------------------------------
    # NODE RECOVERY
    # ---------------------------------------------------------

    checked += 1
    try:
        request = build_node_request(
            failed_worker_id="afritech.distributed.worker.node.worker_01",
            replacement_worker_id="afritech.distributed.worker.node.worker_02",
            partition_ids=(record_one.partition_id,),
            ledger_snapshot=snapshot,
            reason="ci_node_recovery",
        )

        node_recovery = require_node_recovered(
            failed_worker_id=request.failed_worker_id,
            replacement_worker_id=request.replacement_worker_id,
            partition_ids=request.partition_ids,
            ledger_snapshot=request.ledger_snapshot,
            reason=request.reason,
        )

        if not node_recovery.report.recovered:
            failures.append("node recovery did not report recovered")

    except RecoveryAPIError as exc:
        failures.append(f"node recovery failed: {exc}")

    # ---------------------------------------------------------
    # NEGATIVE TEST: MISSING PARTITION RECOVERY
    # ---------------------------------------------------------

    checked += 1
    try:
        require_partition_recovered(
            partition_id="partition.missing",
            ledger_snapshot=snapshot,
            reason="ci_missing_recovery",
        )
        failures.append("missing partition recovery accepted")

    except RecoveryAPIError:
        pass

    # ---------------------------------------------------------
    # NEGATIVE TEST: MISSING PARTITION REBUILD
    # ---------------------------------------------------------

    checked += 1
    try:
        require_partition_rebuilt(
            partition_id="partition.missing",
            ledger_snapshot=snapshot,
            reason="ci_missing_rebuild",
        )
        failures.append("missing partition rebuild accepted")

    except RecoveryAPIError:
        pass

    # ---------------------------------------------------------
    # NEGATIVE TEST: DUPLICATE TRANSCRIPT APPEND
    # ---------------------------------------------------------

    checked += 1
    try:
        ledger.append_verified_transcript(transcript)
        failures.append("duplicate transcript append accepted")

    except DistributedLedgerError:
        pass

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    return DistributedRecoveryValidationResult(
        passed=not failures,
        checked_recoveries=checked,
        failures=tuple(failures),
    )


# ============================================================
# HELPERS
# ============================================================

def _build_record(
    *,
    event_id: str,
    routing_key: str,
    routing_scope: str,
    sequence: int,
    registry,
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


def _build_worker(record):
    return build_worker_result(
        worker_id="afritech.distributed.worker.node.worker_01",
        record=record,
        output_payload=_output_payload(record),
        normalized_input_hash=record.normalized_payload_hash,
        canonical_event_hash=record.canonical_event_hash,
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
    result = validate_distributed_recovery()
    print(result.report())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
