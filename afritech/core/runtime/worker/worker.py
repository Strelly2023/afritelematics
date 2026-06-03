"""Worker for queue-mediated deterministic MVP pipeline execution."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Dict, Optional

from afritech.core.engine import execute
from afritech.guards.edge_input_guard import validate_edge_pipeline
from afritech.storage.event_log import store_event
from afritech.storage.event_schema import EventRecord
from afritech.execution.worker.types import WorkerResult


def process_event(
    event: Mapping[str, Any],
    partition_id: Optional[int] = None,
    flow_trace: Mapping[str, Any] | None = None,
) -> WorkerResult:
    """
    Execute one normalized event and append a replay ledger record.

    HARD GUARANTEES:
    - Deterministic execution
    - Canonical output boundary (WorkerResult)
    - Replay-safe hashing
    - Full trace observability
    """

    # ---------------------------------------------------------
    # TRACE VALIDATION (CLOSED WORLD ENFORCEMENT)
    # ---------------------------------------------------------
    trace: Dict[str, Any] = dict(
        flow_trace or {"stages": ["adapter", "normalization", "ingestion"]}
    )
    validate_edge_pipeline(trace)

    # ---------------------------------------------------------
    # INPUT NORMALIZATION (IMMUTABLE SNAPSHOT)
    # ---------------------------------------------------------
    normalized_input: Dict[str, Any] = deepcopy(dict(event))

    if "request_id" not in normalized_input:
        raise KeyError("Missing required field: request_id")

    # ---------------------------------------------------------
    # DETERMINISTIC EXECUTION
    # ---------------------------------------------------------
    output = execute(normalized_input)

    if output is None:
        raise RuntimeError("Execution returned None (invalid result state)")

    normalized_output: Dict[str, Any] = deepcopy(output)

    # ---------------------------------------------------------
    # REPLAY HASH GENERATION (CANONICAL)
    # ---------------------------------------------------------
    replay_hash = EventRecord.generate_hash(normalized_output)

    # ---------------------------------------------------------
    # EVENT RECORD (REPLAY LEDGER)
    # ---------------------------------------------------------
    record = EventRecord(
        request_id=str(normalized_input["request_id"]),
        partition_id=partition_id,
        normalized_input=normalized_input,
        output=normalized_output,
        trace=trace,
        replay_hash=replay_hash,
    )

    store_event(record)

    # ---------------------------------------------------------
    # CANONICAL WORKER RESULT (CRITICAL FIX)
    # ---------------------------------------------------------
    return WorkerResult(
        request_id=record.request_id,
        partition_id=partition_id,
        outputs=normalized_output,
        trace=trace,
        replay_hash=replay_hash,
    )