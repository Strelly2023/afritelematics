"""Append-only in-memory event log for MVP replay validation."""

from __future__ import annotations

from afritech.storage.event_schema import EventRecord


EVENT_STORE: list[EventRecord] = []


def store_event(record: EventRecord) -> None:
    EVENT_STORE.append(record)


def get_all_events() -> tuple[EventRecord, ...]:
    return tuple(EVENT_STORE)


def clear_event_log() -> None:
    EVENT_STORE.clear()

