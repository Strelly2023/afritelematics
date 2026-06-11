"""Trace enforcement for GA Elite field-test clients."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
import os
from threading import Lock
from typing import Any

from afriride_system.backend.authority_runtime import (
    DOC_VERSION,
    assert_consistent_authority_hashes,
    authority_envelope,
)
from afriride_system.backend.repositories.trace_repository import TraceRepository
from afriride_system.backend.storage import AfriRideStorage, DEFAULT_DB_PATH


__doc_authority__ = "DOC-ARCH-001"
__doc_version__ = "1.0.0"
__governed_invariants__ = (
    "I3_NO_SILENT_MUTATION",
    "I4_DETERMINISTIC_EXECUTION",
    "I5_REPLAY_REQUIRED",
    "I6_REPLAY_AUTHORITY",
    "I7_TRANSCRIPT_COMPLETENESS",
    "I8_TRANSCRIPT_HASH_STABILITY",
    "I11_AUTHORITY_DECLARATION",
)


ACTOR_TYPES = {"rider", "driver", "operator"}
REQUIRED_TRANSITIONS = ("REQUESTED", "DRIVER_ACCEPTED", "ARRIVED", "STARTED", "COMPLETED")


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
    previous_hash: str | None
    authority_hash: str
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
            "previous_hash": self.previous_hash,
            "authority_hash": self.authority_hash,
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
    hash_chain_verified: bool
    invariant_violations: tuple[str, ...]

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
            "hash_chain_verified": self.hash_chain_verified,
            "invariant_violations": list(self.invariant_violations),
            "authority": authority_envelope(
                doc_id=__doc_authority__,
                doc_version=__doc_version__,
                governed_invariants=__governed_invariants__,
                surface="trace_validation",
            ),
        }


@dataclass
class TraceEventLog:
    """Append-only persistent trace log for field-test enforcement."""

    repository: TraceRepository
    _lock: Lock = field(default_factory=Lock)

    def append(self, envelope: dict[str, Any], ride_id: str | None) -> TraceEvent:
        self._validate_envelope(envelope)
        with self._lock:
            event_id = str(envelope["event_id"])
            existing = self._existing(event_id)
            if existing is not None:
                return existing

            sequence_id, previous_hash = self.repository.next_sequence_and_previous_hash()
            normalized_timestamp = normalize_timestamp(str(envelope["local_timestamp"]))
            transition = transition_from_action(str(envelope["action"]))
            authority_hash = authority_envelope(
                doc_id=__doc_authority__,
                doc_version=__doc_version__,
                governed_invariants=__governed_invariants__,
                surface="trace_event",
            )["authority_hash"]
            event_hash = compute_trace_event_hash(
                event_id=event_id,
                sequence_id=sequence_id,
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
                previous_hash=previous_hash,
                authority_hash=authority_hash,
            )
            event = TraceEvent(
                event_id=event_id,
                sequence_id=sequence_id,
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
                previous_hash=previous_hash,
                authority_hash=authority_hash,
                event_hash=event_hash,
            )
            self.repository.save(
                {
                    "event_id": event.event_id,
                    "sequence_id": event.sequence_id,
                    "device_id": event.device_id,
                    "actor_type": event.actor_type,
                    "actor_id": event.actor_id,
                    "action": event.action,
                    "payload": event.payload,
                    "local_timestamp": event.local_timestamp,
                    "normalized_timestamp": event.normalized_timestamp,
                    "app_version": event.app_version,
                    "test_mode": event.test_mode,
                    "ride_id": event.ride_id,
                    "transition": event.transition,
                    "previous_hash": event.previous_hash,
                    "authority_hash": event.authority_hash,
                    "event_hash": event.event_hash,
                }
            )
            return event

    def all_events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._event_from_row(row) for row in self.repository.all())

    def clear(self) -> None:
        with self._lock:
            self.repository.clear()

    def events_for_ride(self, ride_id: str) -> tuple[TraceEvent, ...]:
        return tuple(self._event_from_row(row) for row in self.repository.events_for_ride(ride_id))

    def validate_ride(self, ride_id: str) -> TraceValidationResult:
        from afriride_system.backend.replay_engine import ReplayEngine

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
        replay = ReplayEngine().replay(ride_id, events)
        invariant_violations = list(replay.invariant_violations)
        hash_chain_verified = replay.hash_chain_verified
        authority_hashes = {event.authority_hash for event in events}
        if len(authority_hashes) > 1:
            invariant_violations.append("authority_hash_mismatch")
            hash_chain_verified = False
        elif events:
            assert_consistent_authority_hashes(
                trace=events[0].authority_hash,
                replay=replay.canonical_dict()["authority"]["authority_hash"],
            )
        return TraceValidationResult(
            ride_id=ride_id,
            valid=ordered and complete and not duplicate_event_ids and replay.replay_verified and len(authority_hashes) <= 1,
            ordered=ordered,
            complete=complete,
            duplicate_event_ids=duplicate_event_ids,
            missing_transitions=missing,
            trace_hash=replay.trace_hash,
            replay_hash=replay.replay_hash,
            replay_verified=replay.replay_verified,
            hash_chain_verified=hash_chain_verified,
            invariant_violations=tuple(invariant_violations),
        )

    def integrity_summary(self) -> dict[str, Any]:
        events = self.all_events()
        ride_ids = sorted({event.ride_id for event in events if event.ride_id})
        validations = [self.validate_ride(ride_id) for ride_id in ride_ids]
        valid_count = sum(1 for result in validations if result.valid)
        invalid = [result for result in validations if not result.valid]
        global_chain_failures = self._global_chain_failures(events)
        return {
            "total_rides": len(ride_ids),
            "valid_traces": valid_count,
            "invalid_traces": len(invalid),
            "missing_events": sum(len(result.missing_transitions) for result in invalid),
            "trace_count": len(events),
            "hash_chain_failures": global_chain_failures,
            "replay_success_rate": (
                "100%"
                if not validations
                else f"{int((sum(1 for result in validations if result.replay_verified) / len(validations)) * 100)}%"
            ),
            "replay_failures": sum(1 for result in validations if not result.replay_verified),
            "last_failed_ride_id": invalid[-1].ride_id if invalid else None,
        }

    def _global_chain_failures(self, events: tuple[TraceEvent, ...]) -> int:
        failures = 0
        previous_hash: str | None = None
        for event in events:
            if event.previous_hash != previous_hash:
                failures += 1
            if event.event_hash != recompute_trace_event_hash(event):
                failures += 1
            previous_hash = event.event_hash
        return failures

    def _existing(self, event_id: str) -> TraceEvent | None:
        payload = self.repository.get_by_event_id(event_id)
        if payload is None:
            return None
        return self._event_from_row(payload)

    def _event_from_row(self, payload: dict[str, Any]) -> TraceEvent:
        return TraceEvent(
            event_id=str(payload["event_id"]),
            sequence_id=int(payload["sequence_id"]),
            device_id=str(payload["device_id"]),
            actor_type=str(payload["actor_type"]),
            actor_id=str(payload["actor_id"]),
            action=str(payload["action"]),
            payload=payload["payload"],
            local_timestamp=str(payload["local_timestamp"]),
            normalized_timestamp=str(payload["normalized_timestamp"]),
            app_version=str(payload["app_version"]),
            test_mode=bool(payload["test_mode"]),
            ride_id=payload["ride_id"],
            transition=payload["transition"],
            previous_hash=payload.get("previous_hash"),
            authority_hash=str(
                payload.get("authority_hash")
                or authority_envelope(
                    doc_id=__doc_authority__,
                    doc_version=__doc_version__,
                    governed_invariants=__governed_invariants__,
                    surface="trace_event",
                )["authority_hash"]
            ),
            event_hash=str(payload["event_hash"]),
        )

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


def build_trace_log(*, db_path: str | None = None) -> TraceEventLog:
    storage = AfriRideStorage(
        db_path
        or os.environ.get("AFRIRIDE_DATABASE_URL")
        or os.environ.get("AFRIRIDE_DB_PATH")
        or DEFAULT_DB_PATH
    )
    return TraceEventLog(repository=TraceRepository(storage))


def trace_event_from_payload(payload: dict[str, Any]) -> TraceEvent:
    event_hash = payload.get("event_hash", payload.get("hash"))
    if event_hash in (None, ""):
        raise KeyError("event_hash")
    return TraceEvent(
        event_id=str(payload["event_id"]),
        sequence_id=int(payload["sequence_id"]),
        device_id=str(payload["device_id"]),
        actor_type=str(payload["actor_type"]),
        actor_id=str(payload["actor_id"]),
        action=str(payload["action"]),
        payload=payload["payload"],
        local_timestamp=str(payload["local_timestamp"]),
        normalized_timestamp=str(payload["normalized_timestamp"]),
        app_version=str(payload["app_version"]),
        test_mode=bool(payload["test_mode"]),
        ride_id=payload["ride_id"],
        transition=payload["transition"],
        previous_hash=payload.get("previous_hash"),
        authority_hash=str(payload["authority_hash"]),
        event_hash=str(event_hash),
    )


TRACE_LOG = build_trace_log()


def reset_trace_log() -> TraceEventLog:
    TRACE_LOG.clear()
    try:
        from afriride_system.api.dependencies.runtime import reset_trace_log as reset_runtime_trace_log

        return reset_runtime_trace_log()
    except Exception:
        pass
    return TRACE_LOG


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def trace_hash_for(events: tuple[TraceEvent, ...]) -> str:
    return stable_hash([event.canonical_dict() for event in events])


def compute_trace_event_hash(
    *,
    event_id: str,
    sequence_id: int,
    device_id: str,
    actor_type: str,
    actor_id: str,
    action: str,
    payload: Any,
    local_timestamp: str,
    normalized_timestamp: str,
    app_version: str,
    test_mode: bool,
    ride_id: str | None,
    transition: str | None,
    previous_hash: str | None,
    authority_hash: str,
) -> str:
    return stable_hash(
        {
            "event_id": event_id,
            "sequence_id": sequence_id,
            "device_id": device_id,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "payload": payload,
            "local_timestamp": local_timestamp,
            "normalized_timestamp": normalized_timestamp,
            "app_version": app_version,
            "test_mode": test_mode,
            "ride_id": ride_id,
            "transition": transition,
            "previous_hash": previous_hash,
            "authority_hash": authority_hash,
        }
    )


def recompute_trace_event_hash(event: TraceEvent) -> str:
    return compute_trace_event_hash(
        event_id=event.event_id,
        sequence_id=event.sequence_id,
        device_id=event.device_id,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        action=event.action,
        payload=event.payload,
        local_timestamp=event.local_timestamp,
        normalized_timestamp=event.normalized_timestamp,
        app_version=event.app_version,
        test_mode=event.test_mode,
        ride_id=event.ride_id,
        transition=event.transition,
        previous_hash=event.previous_hash,
        authority_hash=event.authority_hash,
    )


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
    if "ARRIVE" in normalized:
        return "ARRIVED"
    if "START" in normalized:
        return "STARTED"
    if "COMPLETE" in normalized:
        return "COMPLETED"
    if "REJECT" in normalized:
        return "REJECTED"
    if "CANCEL" in normalized:
        return "CANCELLED"
    return None
