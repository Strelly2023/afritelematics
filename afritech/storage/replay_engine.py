"""Replay engine for MVP production pipeline event records."""

from __future__ import annotations

from afritech.core.engine import execute
from afritech.storage.event_schema import EventRecord


def replay_event(event: EventRecord) -> str:
    output = execute(event.normalized_input)
    return EventRecord.generate_hash(output)

