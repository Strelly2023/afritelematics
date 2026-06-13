"""Deterministic event outbox for AfriPay."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.afripay.models import DomainEvent, new_id


class EventOutbox:
    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def emit(self, event_type: str, payload: Mapping[str, Any]) -> DomainEvent:
        event = DomainEvent(new_id("evt"), event_type, _canonicalize(payload))
        self._events.append(event)
        return event

    def all(self) -> tuple[DomainEvent, ...]:
        return tuple(self._events)

    def root_hash(self) -> str:
        return canonical_hash([event_payload(event) for event in self._events])


class EventStore:
    """Append-only immutable event store with aggregate replay."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
        self._hash_chain: list[str] = []

    def append(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        aggregate_id: str | None = None,
    ) -> DomainEvent:
        event = DomainEvent(
            new_id("evt"),
            event_type,
            _canonicalize({**dict(payload), "aggregate_id": aggregate_id}),
        )
        previous = self._hash_chain[-1] if self._hash_chain else "GENESIS"
        event_hash = canonical_hash({"event": event_payload(event), "previous": previous})
        self._events.append(event)
        self._hash_chain.append(event_hash)
        return event

    def replay(self, aggregate_id: str) -> tuple[DomainEvent, ...]:
        return tuple(
            event
            for event in self._events
            if event.payload.get("aggregate_id") == aggregate_id
        )

    def all(self) -> tuple[DomainEvent, ...]:
        return tuple(self._events)

    def root_hash(self) -> str:
        return self._hash_chain[-1] if self._hash_chain else canonical_hash([])


def event_payload(event: DomainEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "payload": _canonicalize(event.payload),
    }


def canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if hasattr(value, "canonical"):
        return value.canonical()
    return value
