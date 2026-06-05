from __future__ import annotations

from typing import Iterable

from afritech.models import EventRecord
from afritech.trust_kernel.hashing import event_hash, sha256_payload


def replay(events: Iterable[EventRecord]) -> str:
    state: dict[str, object] = {}
    for event in events:
        _verify_event_hash(event)
        apply_event(state, event)
    return hash_state(state)


def replay_all() -> str:
    return replay(EventRecord.objects.order_by("created_at", "event_id"))


def apply_event(state: dict[str, object], event: EventRecord) -> None:
    subject_id = event.subject_id
    subjects = dict(state.get("subjects", {}))
    current = dict(subjects.get(subject_id, {}))
    current["last_event_type"] = event.event_type
    current["last_event_hash"] = event.event_hash
    current["actor_id"] = event.actor_id

    if "status" in event.payload:
        current["status"] = event.payload["status"]
    if "ride_id" in event.payload:
        current["ride_id"] = event.payload["ride_id"]

    subjects[subject_id] = current
    state["subjects"] = subjects


def hash_state(state: dict[str, object]) -> str:
    return sha256_payload(state)


def _verify_event_hash(event: EventRecord) -> None:
    computed = event_hash(
        event_id=str(event.event_id),
        event_type=event.event_type,
        actor_id=event.actor_id,
        subject_id=event.subject_id,
        prev_hash=event.prev_hash,
        payload=event.payload,
        signature=event.signature,
    )
    if computed != event.event_hash:
        raise ValueError("EVENT_HASH_MISMATCH")
