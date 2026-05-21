"""Worker for queue-mediated deterministic MVP pipeline execution."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from afritech.core.engine import execute
from afritech.guards.edge_input_guard import validate_edge_pipeline
from afritech.storage.event_log import store_event
from afritech.storage.event_schema import EventRecord


def process_event(
    event: Mapping[str, Any],
    flow_trace: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one normalized event and append a replay ledger record."""

    trace = dict(flow_trace or {"stages": ["adapter", "normalization", "ingestion"]})
    validate_edge_pipeline(trace)

    normalized_input = deepcopy(dict(event))
    output = execute(normalized_input)

    record = EventRecord(
        request_id=str(normalized_input["request_id"]),
        normalized_input=normalized_input,
        output=deepcopy(output),
        trace=trace,
        replay_hash=EventRecord.generate_hash(output),
    )
    store_event(record)

    return output

