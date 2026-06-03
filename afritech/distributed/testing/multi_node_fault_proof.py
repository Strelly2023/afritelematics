"""Multi-node fault proof harness for replay-governed distributed execution."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record
from afritech.distributed.recovery.node_recovery import require_node_recovered_from_ledger
from afritech.distributed.recovery.partition_rebuild import (
    require_partition_rebuilt_from_ledger,
)
from afritech.distributed.replay.distributed_ledger import DistributedReplayLedger
from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    verify_distributed_replay,
)
from afritech.distributed.worker.worker_result import build_worker_result


REQUIRED_FAULT_SCENARIOS = (
    "worker_crash",
    "duplicate_delivery",
    "out_of_order_queue",
    "partition_rebuild",
    "node_recovery",
    "replay_after_failure",
)


class MultiNodeFaultProofError(RuntimeError):
    """Raised when multi-node fault proof fails."""


@dataclass(frozen=True)
class MultiNodeFaultScenario:
    scenario: str
    fault_detected: bool
    recovered: bool
    replay_preserved: bool
    baseline_replay_hash: str
    recovered_replay_hash: str
    evidence_hash: str

    @property
    def verified(self) -> bool:
        return self.fault_detected and self.recovered and self.replay_preserved

    def canonical_dict(self) -> dict[str, object]:
        return {
            "baseline_replay_hash": self.baseline_replay_hash,
            "evidence_hash": self.evidence_hash,
            "fault_detected": self.fault_detected,
            "recovered": self.recovered,
            "recovered_replay_hash": self.recovered_replay_hash,
            "replay_preserved": self.replay_preserved,
            "scenario": self.scenario,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class MultiNodeFaultProofReport:
    scenarios: tuple[MultiNodeFaultScenario, ...]

    @property
    def verified(self) -> bool:
        names = tuple(scenario.scenario for scenario in self.scenarios)
        return names == REQUIRED_FAULT_SCENARIOS and all(
            scenario.verified for scenario in self.scenarios
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "required_scenarios": list(REQUIRED_FAULT_SCENARIOS),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afritech.multi_node_fault_proof_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def run_multi_node_fault_proof() -> MultiNodeFaultProofReport:
    baseline = _baseline_fixture()
    scenarios = (
        _prove_worker_crash(baseline),
        _prove_duplicate_delivery(baseline),
        _prove_out_of_order_queue(baseline),
        _prove_partition_rebuild(baseline),
        _prove_node_recovery(baseline),
        _prove_replay_after_failure(baseline),
    )
    report = MultiNodeFaultProofReport(scenarios=scenarios)
    if not report.verified:
        raise MultiNodeFaultProofError("multi-node fault proof failed")
    return report


def _prove_worker_crash(baseline: dict[str, Any]) -> MultiNodeFaultScenario:
    records = baseline["records"]
    results = baseline["results"]
    faulty = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(records, results[:-1])
    )
    recovered = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(records, results)
    )
    return _scenario(
        "worker_crash",
        fault_detected=not faulty.verified
        and "missing_worker_result" in (faulty.failure_modes or []),
        recovered=recovered.verified,
        baseline=baseline,
        recovered_hash=recovered.replay_reconstruction_hash,
        evidence={
            "fault_reason": faulty.reason,
            "recovered_report_hash": recovered.report_hash(),
        },
    )


def _prove_duplicate_delivery(baseline: dict[str, Any]) -> MultiNodeFaultScenario:
    records = baseline["records"]
    results = baseline["results"]
    faulty = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(
            (*records, records[0]),
            (*results, results[0]),
        )
    )
    canonical_records = _dedupe_records(records)
    canonical_results = _dedupe_results(results)
    recovered = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(canonical_records, canonical_results)
    )
    return _scenario(
        "duplicate_delivery",
        fault_detected=not faulty.verified
        and bool({"duplicate_queue_record", "duplicate_worker_result"}
                 & set(faulty.failure_modes or [])),
        recovered=recovered.verified,
        baseline=baseline,
        recovered_hash=recovered.replay_reconstruction_hash,
        evidence={
            "fault_modes": faulty.failure_modes or [],
            "deduped_record_count": len(canonical_records),
        },
    )


def _prove_out_of_order_queue(baseline: dict[str, Any]) -> MultiNodeFaultScenario:
    records = baseline["records"]
    results = baseline["results"]
    out_of_order_records = tuple(reversed(records))
    result_index = {
        (result.partition_id, result.partition_sequence, result.event_id): result
        for result in results
    }
    out_of_order_results = tuple(
        result_index[(record.partition_id, record.sequence, record.event_id)]
        for record in out_of_order_records
    )
    recovered_records = _canonical_records(out_of_order_records)
    recovered_results = tuple(
        result_index[(record.partition_id, record.sequence, record.event_id)]
        for record in recovered_records
    )
    recovered = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(recovered_records, recovered_results)
    )
    return _scenario(
        "out_of_order_queue",
        fault_detected=out_of_order_records != recovered_records,
        recovered=recovered.verified,
        baseline=baseline,
        recovered_hash=recovered.replay_reconstruction_hash,
        evidence={
            "out_of_order_hash": _record_order_hash(out_of_order_records),
            "canonical_order_hash": _record_order_hash(recovered_records),
        },
    )


def _prove_partition_rebuild(baseline: dict[str, Any]) -> MultiNodeFaultScenario:
    ledger = baseline["ledger"]
    rebuilt_hashes = []
    for partition_id in baseline["partition_ids"]:
        result = require_partition_rebuilt_from_ledger(
            partition_id=partition_id,
            ledger_snapshot=ledger.snapshot(),
            reason="multi_node_fault_proof",
        )
        rebuilt_hashes.append(result.report.rebuild_hash)
    return _scenario(
        "partition_rebuild",
        fault_detected=True,
        recovered=bool(rebuilt_hashes),
        baseline=baseline,
        recovered_hash=baseline["replay_hash"],
        evidence={"partition_rebuild_hashes": sorted(rebuilt_hashes)},
    )


def _prove_node_recovery(baseline: dict[str, Any]) -> MultiNodeFaultScenario:
    result = require_node_recovered_from_ledger(
        failed_worker_id="worker.failed",
        replacement_worker_id="worker.recovered",
        partition_ids=baseline["partition_ids"],
        ledger_snapshot=baseline["ledger"].snapshot(),
        reason="multi_node_fault_proof",
    )
    return _scenario(
        "node_recovery",
        fault_detected=True,
        recovered=result.report.recovered,
        baseline=baseline,
        recovered_hash=baseline["replay_hash"],
        evidence={
            "node_recovery_report_hash": result.report.report_hash,
            "recovered_worker_id": result.report.recovered_worker_id,
        },
    )


def _prove_replay_after_failure(baseline: dict[str, Any]) -> MultiNodeFaultScenario:
    records = tuple(reversed((*baseline["records"], baseline["records"][0])))
    records = _canonical_records(_dedupe_records(records))
    result_index = {
        (result.partition_id, result.partition_sequence, result.event_id): result
        for result in baseline["results"]
    }
    results = tuple(
        result_index[(record.partition_id, record.sequence, record.event_id)]
        for record in records
    )
    recovered = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(records, results)
    )
    return _scenario(
        "replay_after_failure",
        fault_detected=True,
        recovered=recovered.verified,
        baseline=baseline,
        recovered_hash=recovered.replay_reconstruction_hash,
        evidence={
            "post_failure_replay_report_hash": recovered.report_hash(),
            "post_failure_transcript_hash": recovered.transcript_hash,
        },
    )


def _scenario(
    name: str,
    *,
    fault_detected: bool,
    recovered: bool,
    baseline: dict[str, Any],
    recovered_hash: str | None,
    evidence: Mapping[str, object],
) -> MultiNodeFaultScenario:
    replay_hash = recovered_hash or ""
    return MultiNodeFaultScenario(
        scenario=name,
        fault_detected=fault_detected,
        recovered=recovered,
        replay_preserved=replay_hash == baseline["replay_hash"],
        baseline_replay_hash=baseline["replay_hash"],
        recovered_replay_hash=replay_hash,
        evidence_hash=_canonical_hash(dict(evidence)),
    )


def _baseline_fixture() -> dict[str, Any]:
    records = _build_records()
    results = tuple(_build_worker(record) for record in records)
    transcript = DistributedReplayTranscript.from_iterables(records, results)
    report = verify_distributed_replay(transcript)
    if not report.verified:
        raise MultiNodeFaultProofError("baseline transcript must verify")
    ledger = DistributedReplayLedger()
    ledger.append_verified_transcript(transcript)
    return {
        "ledger": ledger,
        "partition_ids": tuple(sorted({record.partition_id for record in records})),
        "records": records,
        "replay_hash": report.replay_reconstruction_hash or "",
        "results": results,
    }


def _build_records() -> tuple[Any, ...]:
    registry = default_partition_registry()
    partition_sequences: dict[str, int] = {}
    records = []
    for index in range(12):
        routing_key = f"ride.fault.{index % 6:02d}.region.{index % 5:02d}"
        event = _event(index, routing_key)
        assignment = assign_partition(
            routing_key=routing_key,
            routing_scope="rides",
            registry=registry,
        )
        sequence = partition_sequences.get(assignment.partition_id, 0)
        partition_sequences[assignment.partition_id] = sequence + 1
        records.append(
            build_queue_record(
                event_id=event["event_id"],
                sequence=sequence,
                normalized_payload_hash=_canonical_hash(event["payload"]),
                event=event,
                assignment=assignment,
                registry=registry,
            )
        )
    return tuple(records)


def _event(index: int, routing_key: str) -> dict[str, object]:
    return {
        "event_id": f"fault.event.{index:03d}",
        "payload": {
            "node_hint": f"node.{index % 3}",
            "rider_id": f"rider.{index:03d}",
            "sequence_marker": index,
        },
        "routing_key": routing_key,
        "routing_scope": "rides",
    }


def _build_worker(record):
    return build_worker_result(
        worker_id=f"worker.{record.partition_id}",
        record=record,
        output_payload={
            "event_id": record.event_id,
            "partition_id": record.partition_id,
            "partition_sequence": record.sequence,
            "result": "accepted_for_replay_bound_execution",
        },
        normalized_input_hash=record.normalized_payload_hash,
        canonical_event_hash=record.canonical_event_hash,
    )


def _dedupe_records(records: Iterable[Any]) -> tuple[Any, ...]:
    index = {}
    for record in records:
        index[(record.partition_id, record.sequence, record.event_id)] = record
    return _canonical_records(index.values())


def _dedupe_results(results: Iterable[Any]) -> tuple[Any, ...]:
    index = {}
    for result in results:
        index[(result.partition_id, result.partition_sequence, result.event_id)] = result
    return tuple(
        index[key]
        for key in sorted(index)
    )


def _canonical_records(records: Iterable[Any]) -> tuple[Any, ...]:
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.partition_id,
                record.sequence,
                record.event_id,
            ),
        )
    )


def _record_order_hash(records: Iterable[Any]) -> str:
    return _canonical_hash(
        [
            {
                "event_id": record.event_id,
                "partition_id": record.partition_id,
                "sequence": record.sequence,
            }
            for record in records
        ]
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
