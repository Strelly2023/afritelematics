"""Trace enforcement for GA Elite field-test clients."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any


ACTOR_TYPES = {"rider", "driver", "operator"}
REQUIRED_TRANSITIONS = ("REQUESTED", "DRIVER_ACCEPTED", "STARTED", "COMPLETED")


class TraceEnvelopeError(ValueError):
    """Raised when a client trace envelope is not admissible."""


@dataclass(frozen=True)
class TraceEvent:
    event_id: str
    sequence_id: int
    device_id: str
    actor_type: str
    actor_id: str
    action: str
    payload: Any
    local_timestamp: str
    normalized_timestamp: str
    app_version: str
    test_mode: bool
    ride_id: str | None
    transition: str | None
    event_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "sequence_id": self.sequence_id,
            "device_id": self.device_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "action": self.action,
            "payload": self.payload,
            "local_timestamp": self.local_timestamp,
            "normalized_timestamp": self.normalized_timestamp,
            "app_version": self.app_version,
            "test_mode": self.test_mode,
            "ride_id": self.ride_id,
            "transition": self.transition,
            "hash": self.event_hash,
        }


@dataclass(frozen=True)
class TraceValidationResult:
    ride_id: str
    valid: bool
    ordered: bool
    complete: bool
    duplicate_event_ids: bool
    missing_transitions: tuple[str, ...]
    trace_hash: str
    replay_hash: str
    replay_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "valid": self.valid,
            "ordered": self.ordered,
            "complete": self.complete,
            "duplicate_event_ids": self.duplicate_event_ids,
            "missing_transitions": list(self.missing_transitions),
            "trace_hash": self.trace_hash,
            "replay_hash": self.replay_hash,
            "replay_verified": self.replay_verified,
        }


@dataclass
class TraceEventLog:
    """Append-only in-memory event log for Day 0/Day 1 field-test enforcement."""

    _events: list[TraceEvent] = field(default_factory=list)
    _event_ids: set[str] = field(default_factory=set)
    _sequence: int = 0
    _lock: Lock = field(default_factory=Lock)

    def append(self, envelope: dict[str, Any], ride_id: str | None) -> TraceEvent:
        self._validate_envelope(envelope)
        with self._lock:
            event_id = str(envelope["event_id"])
            if event_id in self._event_ids:
                return self._existing(event_id)

            self._sequence += 1
            normalized_timestamp = normalize_timestamp(str(envelope["local_timestamp"]))
            transition = transition_from_action(str(envelope["action"]))
            event_hash = stable_hash(
                {
                    "event_id": event_id,
                    "sequence_id": self._sequence,
                    "device_id": envelope["device_id"],
                    "actor_type": envelope["actor_type"],
                    "actor_id": envelope["actor_id"],
                    "action": envelope["action"],
                    "payload": envelope.get("payload"),
                    "local_timestamp": envelope["local_timestamp"],
                    "normalized_timestamp": normalized_timestamp,
                    "app_version": envelope["app_version"],
                    "test_mode": envelope.get("test_mode", False),
                    "ride_id": ride_id,
                    "transition": transition,
                }
            )
            event = TraceEvent(
                event_id=event_id,
                sequence_id=self._sequence,
                device_id=str(envelope["device_id"]),
                actor_type=str(envelope["actor_type"]),
                actor_id=str(envelope["actor_id"]),
                action=str(envelope["action"]),
                payload=envelope.get("payload"),
                local_timestamp=str(envelope["local_timestamp"]),
                normalized_timestamp=normalized_timestamp,
                app_version=str(envelope["app_version"]),
                test_mode=bool(envelope.get("test_mode", False)),
                ride_id=ride_id,
                transition=transition,
                event_hash=event_hash,
            )
            self._events.append(event)
            self._event_ids.add(event.event_id)
            return event

    def all_events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._event_ids.clear()
            self._sequence = 0

    def events_for_ride(self, ride_id: str) -> tuple[TraceEvent, ...]:
        return tuple(event for event in self._events if event.ride_id == ride_id)

    def validate_ride(self, ride_id: str) -> TraceValidationResult:
        events = self.events_for_ride(ride_id)
        ordered = all(
            left.sequence_id < right.sequence_id
            for left, right in zip(events, events[1:])
        )
        event_ids = [event.event_id for event in events]
        duplicate_event_ids = len(event_ids) != len(set(event_ids))
        transitions = tuple(event.transition for event in events if event.transition)
        missing = tuple(
            transition for transition in REQUIRED_TRANSITIONS if transition not in transitions
        )
        complete = not missing
        trace_hash = trace_hash_for(events)
        replay_hash = trace_hash_for(tuple(sorted(events, key=lambda item: item.sequence_id)))
        replay_verified = trace_hash == replay_hash
        return TraceValidationResult(
            ride_id=ride_id,
            valid=ordered and complete and not duplicate_event_ids and replay_verified,
            ordered=ordered,
            complete=complete,
            duplicate_event_ids=duplicate_event_ids,
            missing_transitions=missing,
            trace_hash=trace_hash,
            replay_hash=replay_hash,
            replay_verified=replay_verified,
        )

    def integrity_summary(self) -> dict[str, Any]:
        ride_ids = sorted({event.ride_id for event in self._events if event.ride_id})
        validations = [self.validate_ride(ride_id) for ride_id in ride_ids]
        valid_count = sum(1 for result in validations if result.valid)
        invalid = [result for result in validations if not result.valid]
        return {
            "total_rides": len(ride_ids),
            "valid_traces": valid_count,
            "invalid_traces": len(invalid),
            "missing_events": sum(len(result.missing_transitions) for result in invalid),
            "trace_count": len(self._events),
            "replay_success_rate": (
                "100%"
                if not validations
                else f"{int((sum(1 for result in validations if result.replay_verified) / len(validations)) * 100)}%"
            ),
            "replay_failures": sum(1 for result in validations if not result.replay_verified),
            "last_failed_ride_id": invalid[-1].ride_id if invalid else None,
        }

    def _existing(self, event_id: str) -> TraceEvent:
        for event in self._events:
            if event.event_id == event_id:
                return event
        raise TraceEnvelopeError("duplicate event id missing from log")

    def _validate_envelope(self, envelope: dict[str, Any]) -> None:
        required = (
            "event_id",
            "device_id",
            "actor_type",
            "actor_id",
            "action",
            "payload",
            "local_timestamp",
            "app_version",
        )
        missing = [
            field_name
            for field_name in required
            if field_name not in envelope or envelope[field_name] in (None, "")
        ]
        if missing:
            raise TraceEnvelopeError(f"missing envelope fields: {','.join(missing)}")
        if envelope["actor_type"] not in ACTOR_TYPES:
            raise TraceEnvelopeError("invalid actor_type")


TRACE_LOG = TraceEventLog()


def reset_trace_log() -> TraceEventLog:
    TRACE_LOG.clear()
    return TRACE_LOG


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def trace_hash_for(events: tuple[TraceEvent, ...]) -> str:
    return stable_hash([event.canonical_dict() for event in events])


def normalize_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TraceEnvelopeError("invalid local_timestamp") from exc
    parsed = parsed.astimezone(UTC).replace(microsecond=0)
    return parsed.isoformat().replace("+00:00", "Z")


def transition_from_action(action: str) -> str | None:
    normalized = action.upper()
    if "REQUEST" in normalized:
        return "REQUESTED"
    if "ACCEPT" in normalized:
        return "DRIVER_ACCEPTED"
    if "START" in normalized:
        return "STARTED"
    if "COMPLETE" in normalized:
        return "COMPLETED"
    if "REJECT" in normalized:
        return "REJECTED"
    if "CANCEL" in normalized:
        return "CANCELLED"
    return None
